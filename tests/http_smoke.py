"""Opt-in loopback integration check: python3 tests/http_smoke.py."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


class HTTPWorkflowTest(unittest.TestCase):
    def test_standalone_service(self):
        with tempfile.TemporaryDirectory() as root:
            log = Path(root) / "server.log"
            env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "LUCY_MODEL"}}
            with log.open("w") as output:
                server = subprocess.Popen([sys.executable, "-m", "lucy", "--data", root, "serve", "--port", "0"], cwd=ROOT, env=env, stdout=output, stderr=output)
                try:
                    deadline = time.monotonic() + 10
                    while "http://" not in log.read_text() and server.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.05)
                    self.assertIn("http://", log.read_text(), log.read_text())
                    base = next(line.split("control plane: ")[1] for line in log.read_text().splitlines() if "control plane: " in line)
                    def request(path, body=None, token=None):
                        headers = {"Content-Type": "application/json"}
                        if token:
                            headers["X-Lucy-Token"] = token
                        req = Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
                        with urlopen(req, timeout=5) as response:
                            return json.load(response)
                    session = request("/api/session")
                    token = session["token"]
                    self.assertFalse(session["providers"][1]["configured"])
                    self.assertEqual(request("/api/runtime")["worker"], "running")
                    with self.assertRaises(HTTPError) as caught:
                        request("/api/projects", {"name": "Unauthorized"})
                    self.assertEqual(caught.exception.code, 403)
                    p = request("/api/projects", {"name": "HTTP standalone test"}, token)
                    detail = request("/api/projects/" + p["id"])
                    body = {"provider": "offline", "contract_hash": detail["contract_hash"], "request_key": "http-review-once"}
                    job = request("/api/projects/" + p["id"] + "/jobs", body, token)
                    again = request("/api/projects/" + p["id"] + "/jobs", body, token)
                    self.assertEqual(job["id"], again["id"])
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        job = request("/api/jobs/" + job["id"])
                        if job["status"] not in {"queued", "running"}:
                            break
                        time.sleep(0.1)
                    self.assertEqual(job["status"], "completed")
                    self.assertEqual(len(job["events"]), 3)
                    final = request("/api/projects/" + p["id"])
                    self.assertEqual(final["gates"], detail["gates"])
                    self.assertEqual(final["requirements"], detail["requirements"])
                    self.assertEqual(final["acceptance"], "Incomplete")
                    self.assertEqual(len(final["evidence"]), 1)
                    self.assertEqual(len(request("/api/projects/" + p["id"] + "/jobs")), 1)
                finally:
                    server.terminate()
                    try:
                        server.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
                self.assertEqual(server.returncode, 0, log.read_text())


if __name__ == "__main__":
    unittest.main()
