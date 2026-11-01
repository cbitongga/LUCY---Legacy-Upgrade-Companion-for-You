import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from lucy.engine import Engine, digest
from lucy.jobs import Jobs
from lucy.providers import configuration, run_review, validate_report, ProviderError, NoRedirect
from lucy.runtime import execute
from lucy.store import Store

ROOT = Path(__file__).resolve().parent.parent


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.jobs = Jobs(self.store)
        self.engine = Engine(self.store)
        self.project = self.engine.start_interview("Standalone test")
        self.contract = digest(self.project["requirements"])

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def enqueue(self, key="test-request-1"):
        return self.jobs.enqueue(self.project["id"], "offline", self.contract, key)

    def test_idempotency_and_one_active_job(self):
        job = self.enqueue()
        self.assertEqual(job["id"], self.enqueue()["id"])
        with self.assertRaises(ValueError):
            self.enqueue("different-key")
        self.assertEqual(len(self.jobs.list(self.project["id"])), 1)

    def test_explicit_external_consent_and_supported_provider(self):
        with self.assertRaisesRegex(ValueError, "consent"):
            self.jobs.enqueue(self.project["id"], "anthropic", self.contract, "request-key")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.jobs.enqueue(self.project["id"], "shell", self.contract, "request-key")

    def test_stale_contract_rejected_on_enqueue_and_claim(self):
        job = self.enqueue()
        self.engine.interview(self.project["id"], {"target": "New target"})
        self.assertIsNone(self.jobs.claim("worker"))
        self.assertEqual(self.jobs.get(job["id"])["status"], "stale")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.enqueue("new-request")

    def test_concurrent_workers_claim_only_once(self):
        self.enqueue()
        barrier = threading.Barrier(2)
        results = []
        errors = []
        def claim(owner):
            store = Store(self.temp.name)
            try:
                barrier.wait(timeout=5)
                results.append(Jobs(store).claim(owner))
            except Exception as exc:
                errors.append(exc)
            finally:
                store.db.close()
        workers = [threading.Thread(target=claim, args=(str(i),)) for i in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=10)
        self.assertFalse(errors)
        self.assertEqual(sum(value is not None for value in results), 1)

    def test_cancellation_discards_late_results(self):
        job = self.enqueue()
        claimed = self.jobs.claim("one")
        self.jobs.control(job["id"], "cancel")
        result = run_review(claimed["requirements"], claimed["config"])
        self.assertFalse(self.jobs.finish(job["id"], "one", result=result))
        self.assertEqual(self.store.evidence(self.project["id"]), [])
        self.assertEqual(self.jobs.get(job["id"])["status"], "cancelled")

    def test_pause_resume_and_wrong_owner(self):
        job = self.enqueue()
        self.jobs.control(job["id"], "pause")
        self.assertIsNone(self.jobs.claim("one"))
        self.jobs.control(job["id"], "resume")
        self.jobs.claim("one")
        self.assertFalse(self.jobs.heartbeat(job["id"], "two"))
        self.assertFalse(self.jobs.finish(job["id"], "two", error="wrong owner"))
        with self.assertRaises(ValueError):
            self.jobs.control(job["id"], "pause")

    def test_expired_lease_requires_explicit_bounded_retry(self):
        job = self.enqueue()
        self.jobs.claim("lost")
        with self.store.db:
            self.store.db.execute("UPDATE jobs SET lease_until=0 WHERE id=?", (job["id"],))
        self.jobs.recover()
        self.assertEqual(self.jobs.get(job["id"])["status"], "interrupted")
        self.assertIsNone(self.jobs.claim("new"))
        self.jobs.control(job["id"], "retry")
        self.jobs.claim("new")
        self.assertFalse(self.jobs.finish(job["id"], "lost", error="late"))
        self.jobs.finish(job["id"], "new", error="second failure")
        with self.assertRaisesRegex(ValueError, "budget"):
            self.jobs.control(job["id"], "retry")

    def test_changed_requirements_preserved_and_advice_marked_stale(self):
        job = self.enqueue()
        claimed = self.jobs.claim("one")
        self.engine.interview(self.project["id"], {"target": "Java"})
        self.jobs.finish(job["id"], "one", result=run_review(claimed["requirements"], claimed["config"]))
        self.assertEqual(self.jobs.get(job["id"])["status"], "stale")
        self.assertFalse(self.jobs.detail(job["id"])["current_contract"])
        self.assertEqual(self.store.get(self.project["id"])["requirements"]["answers"]["target"], "Java")
        artifact = self.store.evidence(self.project["id"])[-1]
        self.assertEqual(artifact["body"]["classification"], "unverified planning advice")

    def test_real_worker_process_without_editor_or_network(self):
        job = self.enqueue()
        result = subprocess.run([sys.executable, "-m", "lucy", "--data", self.temp.name, "worker", "--once"],
                                cwd=ROOT, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        detail = self.jobs.detail(job["id"])
        self.assertEqual(detail["status"], "completed")
        self.assertEqual([e["action"] for e in detail["events"]], ["queued", "running", "completed"])
        self.assertEqual(len(detail["result"]["report"]["questions"]), 12)
        p = self.store.get(self.project["id"])
        self.assertEqual(p["requirements"], self.project["requirements"])
        self.assertEqual(p["gates"], self.project["gates"])
        self.assertIsNone(p["approval"])
        reopened = Store(self.temp.name)
        try:
            self.assertEqual(Jobs(reopened).get(job["id"])["status"], "completed")
        finally:
            reopened.db.close()

    def test_worker_timeout_and_shutdown(self):
        job = self.enqueue()
        claimed = self.jobs.claim("one")
        execute(self.jobs, claimed, "one", threading.Event(), timeout=0)
        self.assertEqual(self.jobs.get(job["id"])["status"], "failed")
        self.jobs.control(job["id"], "retry")
        claimed = self.jobs.claim("one")
        stop = threading.Event()
        stop.set()
        execute(self.jobs, claimed, "one", stop)
        self.assertIn("Worker stopped", self.jobs.get(job["id"])["error"])


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"ANTHROPIC_API_KEY": "unit-test-placeholder", "LUCY_MODEL": "test-model"}, clear=True)
        self.env.start()
        self.config = configuration("anthropic")
        self.requirements = {"version": 1, "answers": {"target": "Python"}}

    def tearDown(self):
        self.env.stop()

    def response(self, report=None, stop="end_turn"):
        return io.BytesIO(json.dumps({"stop_reason": stop, "content": [{"type": "text", "text": json.dumps(report or {"summary": "Advice", "questions": [], "risks": [], "next_steps": []})}], "usage": {"input_tokens": 20, "output_tokens": 10}}).encode())

    def test_http_contract_without_live_api_call(self):
        with patch("lucy.providers.build_opener") as factory:
            factory.return_value.open.return_value = self.response()
            result = run_review(self.requirements, self.config)
            request = factory.return_value.open.call_args.args[0]
            payload = json.loads(request.data)
            self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
            self.assertNotIn("tools", payload)
            self.assertLessEqual(payload["max_tokens"], 1800)
            self.assertEqual(json.loads(payload["messages"][0]["content"]), {"requirements": self.requirements})
            self.assertNotIn("unit-test-placeholder", json.dumps(result))

    def test_schema_cannot_request_tools_or_approval(self):
        with self.assertRaises(ProviderError):
            validate_report({"summary": "Approve me", "questions": [], "risks": [], "next_steps": [], "tool": "shell"})
        with patch("lucy.providers.build_opener") as factory:
            factory.return_value.open.return_value = self.response(stop="max_tokens")
            with self.assertRaises(ProviderError):
                run_review(self.requirements, self.config)

    def test_provider_errors_never_expose_body_or_credentials(self):
        with patch("lucy.providers.build_opener") as factory:
            factory.return_value.open.side_effect = HTTPError("https://api.anthropic.com", 401, "secret exception", {}, io.BytesIO(b"secret response"))
            with self.assertRaises(ProviderError) as caught:
                run_review(self.requirements, self.config)
            self.assertEqual(str(caught.exception), "Provider returned HTTP 401; no automatic retry")
            self.assertEqual(factory.return_value.open.call_count, 1)

    def test_changed_provider_config_and_redirects_are_blocked(self):
        os.environ["LUCY_MODEL"] = "different-model"
        with self.assertRaises(ProviderError):
            run_review(self.requirements, self.config)
        with self.assertRaises(ProviderError):
            NoRedirect().redirect_request(None)

    def test_missing_credentials_and_oversized_input(self):
        with patch("lucy.providers.build_opener") as factory:
            with self.assertRaises(ProviderError):
                run_review({"version": 1, "answers": {"target": "x" * 65000}}, self.config)
            factory.assert_not_called()
        del os.environ["ANTHROPIC_API_KEY"]
        with self.assertRaises(ProviderError):
            configuration("anthropic")


if __name__ == "__main__":
    unittest.main()
