import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from lucy.agents import QUESTIONNAIRE, registry
from lucy.assurance import DIMENSIONS, compare, critic, decide
from lucy.discovery import inspect_repository
from lucy.engine import Engine, digest
from lucy.store import Store


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.engine = Engine(self.store)

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def test_interview_needs_no_repository(self):
        p = self.engine.start_interview("Customer platform")
        self.assertEqual(p["status"], "interviewing")
        self.assertEqual(len(p["agents"]), 18)
        self.assertIsNone(p["forecast_history"][-1]["remaining_active_seconds"])
        with self.assertRaises(ValueError):
            self.engine.step(p["id"])

    def test_versioned_contract_and_stale_approval(self):
        p = self.engine.start_interview("Platform")
        p = self.engine.interview(p["id"], {key: "Undecided; requires investigation" for key, _, _ in QUESTIONNAIRE})
        self.assertEqual(p["status"], "strategy_review")
        first_hash = digest(p["requirements"])
        p = self.engine.approve_strategy(p["id"], "incremental", first_hash)
        self.assertEqual(p["status"], "planned")
        with self.assertRaises(ValueError):
            self.engine.step(p["id"])
        p = self.engine.interview(p["id"], {"target": "Python"})
        self.assertIsNone(p["approval"])
        with self.assertRaises(ValueError):
            self.engine.approve_strategy(p["id"], "parallel", first_hash)
        self.assertEqual(len(self.store.evidence(p["id"])), 2)

    def test_partial_and_invalid_answers(self):
        p = self.engine.start_interview("Partial")
        p = self.engine.interview(p["id"], {"motivation": "Reduce maintenance"})
        self.assertEqual(p["status"], "interviewing")
        self.assertFalse(p["strategies"])
        with self.assertRaises(ValueError):
            self.engine.interview(p["id"], {"shell": "anything"})
        with self.assertRaises(ValueError):
            self.engine.approve_strategy(p["id"], "incremental", digest(p["requirements"]))

    def test_restart_preserves_interview(self):
        p = self.engine.start_interview("Persistent")
        self.engine.interview(p["id"], {"target": "Java"})
        self.store.db.close()
        self.store = Store(self.temp.name)
        self.assertEqual(self.store.get(p["id"])["requirements"]["answers"]["target"], "Java")

    def test_demo_requires_exact_approval_and_obeys_pause_cancel(self):
        p = self.engine.create()
        with self.assertRaises(ValueError):
            self.engine.step(p["id"])
        with self.assertRaises(ValueError):
            self.engine.approve(p["id"], "stale")
        self.engine.approve(p["id"], digest(p["requirements"]))
        self.engine.control(p["id"], "pause")
        with self.assertRaises(ValueError):
            self.engine.step(p["id"])
        self.engine.control(p["id"], "resume")
        self.engine.control(p["id"], "cancel")
        with self.assertRaises(ValueError):
            self.engine.step(p["id"])

    def test_fixture_detects_and_revalidates_without_false_acceptance(self):
        p = self.engine.create()
        self.engine.approve(p["id"], digest(p["requirements"]))
        for _ in range(4):
            p = self.engine.step(p["id"])
        self.assertEqual(p["acceptance"], "Blocked")
        self.assertEqual({f["kind"] for f in p["findings"]}, {"functional", "memory"})
        self.store.db.close()
        self.store = Store(self.temp.name)
        self.engine = Engine(self.store)
        for _ in range(4):
            p = self.engine.step(p["id"])
        self.assertEqual(p["status"], "review_required")
        self.assertEqual(p["acceptance"], "Incomplete")
        self.assertTrue(all(f["status"] == "resolved" for f in p["findings"]))
        self.assertEqual(p["knowledge"][0]["status"], "verified")
        for artifact in self.store.evidence(p["id"]):
            self.assertEqual(artifact["sha256"], hashlib.sha256(json.dumps(artifact["body"], sort_keys=True).encode()).hexdigest())

    def test_failure_budget(self):
        from unittest.mock import patch
        p = self.engine.create()
        self.engine.approve(p["id"], digest(p["requirements"]))
        with patch.object(self.engine, "run_worker", side_effect=ValueError("Worker unavailable")):
            p = self.engine.step(p["id"])
            self.assertEqual(p["status"], "blocked")
            self.engine.control(p["id"], "retry")
            self.engine.step(p["id"])
        with self.assertRaises(ValueError):
            self.engine.control(p["id"], "retry")


class SafetyTests(unittest.TestCase):
    def test_gate_missing_failed_and_review(self):
        self.assertEqual(decide([]), "Incomplete")
        gates = [{"name": n, "status": "passed"} for n in DIMENSIONS]
        self.assertEqual(decide(gates), "Accepted")
        gates[-1]["status"] = "unverified"
        self.assertEqual(decide(gates), "Needs Review")
        gates[0]["status"] = "failed"
        self.assertEqual(decide(gates), "Blocked")

    def test_different_verifier_required(self):
        with self.assertRaises(ValueError):
            critic({}, {}, author="same", reviewer="same")

    def test_missing_scenario_is_mismatch(self):
        self.assertTrue(compare({"cases": [{"id": "one", "output": 1}]}, {"cases": []}))

    def test_discovery_skips_symlinks_hidden_files_and_caps_work(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            (path / "main.py").write_text("raise Exception('never execute')")
            (path / ".env").write_text("SECRET=must-not-read")
            (path / "linked.py").symlink_to(path / ".env")
            report = inspect_repository(path)
            self.assertEqual(report["verified"]["files_scanned"], 1)
            self.assertNotIn("SECRET", json.dumps(report))
            self.assertTrue(inspect_repository(path, limit=0)["truncated"])

    def test_roles_have_explicit_permissions_and_no_live_model_claim(self):
        roles = registry()
        self.assertEqual(len({a["id"] for a in roles}), 18)
        for role in roles:
            self.assertIn("arbitrary shell", role["denied"])
            self.assertTrue(role["capabilities"])


if __name__ == "__main__":
    unittest.main()
