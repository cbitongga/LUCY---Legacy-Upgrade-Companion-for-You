"""Loopback-only single-operator control plane. Not a hosted authentication layer."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import sys
import signal
import threading
from urllib.parse import urlsplit

from .agents import QUESTIONNAIRE, registry
from .engine import Engine
from .store import Store
from .jobs import Jobs
from .providers import provider_status
from .activity import project_activity

WEB = Path(__file__).parent / "web"


def serve(root, port=8765, with_worker=True):
    engine = Engine(Store(root))
    jobs = Jobs(engine.store)
    token = secrets.token_urlsafe(32)
    child = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, body, content_type="application/json"):
            data = json.dumps(body).encode() if content_type == "application/json" else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def trusted(self):
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            return self.headers.get("Host") in allowed

        def do_GET(self):
            if not self.trusted():
                return self.send(403, {"error": "Untrusted host"})
            path = urlsplit(self.path).path
            if path in {"/", "/app.js", "/activity.js", "/style.css", "/lucy-logo.png", "/lucy-programmer.png"}:
                name = "index.html" if path == "/" else path[1:]
                mime = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8", "activity.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8", "lucy-logo.png": "image/png", "lucy-programmer.png": "image/png"}[name]
                return self.send(200, (WEB / name).read_bytes(), mime)
            if path == "/api/session":
                return self.send(200, {"token": token, "agents": registry(), "providers": provider_status(), "questions": [{"id": k, "question": q, "hint": h} for k, q, h in QUESTIONNAIRE]})
            if path == "/api/runtime":
                return self.send(200, {"worker": ("running" if child.poll() is None else "stopped") if child else "external worker required", "providers": provider_status()})
            if path == "/api/projects":
                return self.send(200, engine.store.projects())
            if path.startswith("/api/jobs/"):
                try:
                    return self.send(200, jobs.detail(path.split("/")[3]))
                except KeyError:
                    return self.send(404, {"error": "Job not found"})
            if path.startswith("/api/projects/"):
                try:
                    if path.endswith("/activity"):
                        project_id = path.split("/")[3]
                        return self.send(200, project_activity(engine.store.get(project_id), jobs.list(project_id)))
                    if path.endswith("/jobs"):
                        return self.send(200, jobs.list(path.split("/")[3]))
                    return self.send(200, engine.detail(path.split("/")[3]))
                except KeyError:
                    return self.send(404, {"error": "Project not found"})
            self.send(404, {"error": "Not found"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            if not self.trusted() or (origin and origin != "http://" + self.headers.get("Host", "")) or not secrets.compare_digest(self.headers.get("X-Lucy-Token", ""), token):
                return self.send(403, {"error": "Same-origin operator token required"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 100000:
                    raise ValueError("Request too large")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("JSON object required")
                parts = urlsplit(self.path).path.strip("/").split("/")
                if parts == ["api", "projects"]:
                    result = engine.start_interview(body.get("name", ""))
                elif parts == ["api", "demo"]:
                    result = engine.create()
                elif len(parts) == 4 and parts[:2] == ["api", "jobs"]:
                    result = jobs.control(parts[2], parts[3])
                elif len(parts) == 4 and parts[:2] == ["api", "projects"]:
                    project_id, action = parts[2:]
                    if action == "jobs":
                        result = jobs.enqueue(project_id, body.get("provider"), body.get("contract_hash"), body.get("request_key"), body.get("consent", False))
                    elif action == "interview":
                        result = engine.interview(project_id, body.get("answers", {}))
                    elif action == "strategy":
                        result = engine.approve_strategy(project_id, body.get("strategy"), body.get("contract_hash"))
                    elif action == "approve":
                        result = engine.approve(project_id, body.get("contract_hash"))
                    elif action == "step":
                        result = engine.step(project_id)
                    else:
                        result = engine.control(project_id, action)
                else:
                    return self.send(404, {"error": "Not found"})
                self.send(200, result)
            except KeyError:
                self.send(404, {"error": "Project not found"})
            except (ValueError, TypeError) as exc:
                self.send(400, {"error": str(exc)})

    server = HTTPServer(("127.0.0.1", port), Handler)
    previous_term = None
    def stop_server(*_):
        raise KeyboardInterrupt
    if threading.current_thread() is threading.main_thread():
        previous_term = signal.signal(signal.SIGTERM, stop_server)
    try:
        if with_worker:
            child = subprocess.Popen([sys.executable, "-m", "lucy", "--data", str(engine.store.root), "worker"], cwd=WEB.parent.parent)
        print(f"LUCY control plane: http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        server.server_close()
        engine.store.db.close()
        if previous_term is not None:
            signal.signal(signal.SIGTERM, previous_term)
