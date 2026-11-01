"""Persistent sequential workflow for a trusted, explicitly approved demonstration."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .assurance import DIMENSIONS, critic, decide
from .discovery import inspect_repository
from .store import now
from .agents import QUESTIONNAIRE, registry, strategies

ROOT = Path(__file__).resolve().parent.parent
STEPS = ["baseline", "implement", "verify", "critic", "remediate", "revalidate", "learn", "report"]
ROLES = ["Legacy Intelligence", "Implementation", "Differential Verification", "Independent Critic", "Remediation", "Migration Guardian", "Engineering Knowledge", "Evidence and Assurance"]
BAD_SOURCE = '''"""Deliberately defective migration candidate for the bounded demo."""
_history = []
def invoice(items):
    _history.append(bytearray(1024))
    if not items:
        return {"error": "empty_invoice"}
    if any(i["quantity"] < 0 or float(i["price"]) < 0 for i in items):
        return {"error": "negative_value"}
    return {"total": format(sum(float(i["price"]) * i["quantity"] for i in items), ".2f"), "currency": "USD"}
'''
FIXED_SOURCE = '''"""Migrated invoice implementation: isolated decimal line-item calculation."""
from decimal import Decimal, ROUND_HALF_UP
def line_total(item):
    return Decimal(str(item["price"])) * item["quantity"]
def invoice(items):
    if not items:
        return {"error": "empty_invoice"}
    if any(i["quantity"] < 0 or Decimal(str(i["price"])) < 0 for i in items):
        return {"error": "negative_value"}
    amount = sum((line_total(i) for i in items), Decimal("0"))
    return {"total": str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "currency": "USD"}
'''


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Engine:
    def __init__(self, store):
        self.store = store

    def start_interview(self, name):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("Enter a project name of 1–120 characters")
        project = {"id": uuid.uuid4().hex, "name": name.strip(), "demo": False, "created_at": now(), "status": "interviewing", "cursor": 0,
                   "requirements": {"version": 1, "answers": {}}, "approval": None, "strategies": [], "discovery": None,
                   "tasks": [], "gates": [{"name": n, "status": "unverified", "reason": "No migration evidence"} for n in DIMENSIONS],
                   "findings": [], "knowledge": [], "forecast_history": [], "acceptance": "Incomplete",
                   "agents": [{"id": a["id"], "status": "ready" if a["id"] in {"interviewer", "orchestrator"} else "registered"} for a in registry()]}
        self.forecast(project, "Requirements interview opened; migration scope unknown")
        self.store.save(project, {"action": "interview_started", "actor": "requirements-interviewer"})
        return project

    def interview(self, project_id, answers):
        project = self.store.get(project_id)
        if project["demo"] or project["status"] not in {"interviewing", "strategy_review", "planned"}:
            raise ValueError("Project does not support requirements interview")
        keys = {q[0] for q in QUESTIONNAIRE}
        if not isinstance(answers, dict) or any(k not in keys or not isinstance(v, str) or len(v) > 5000 for k, v in answers.items()):
            raise ValueError("Invalid requirement answer")
        previous = project["requirements"]
        merged = {**previous["answers"], **{k: v.strip() for k, v in answers.items()}}
        if merged == previous["answers"]:
            return project
        project["requirements"] = {"version": previous["version"] + 1, "answers": merged}
        project["approval"] = None
        complete = all(merged.get(key) for key in keys)
        project["status"] = "strategy_review" if complete else "interviewing"
        project["strategies"] = strategies(merged) if complete else []
        self.forecast(project, "Requirements revised; any earlier strategy approval invalidated")
        self.store.save(project, {"action": "requirements_updated", "actor": "requirements-interviewer", "version": project["requirements"]["version"]},
                        {f"{project_id}:contract-v{project['requirements']['version']}": project["requirements"]})
        return project

    def approve_strategy(self, project_id, strategy, contract_hash):
        project = self.store.get(project_id)
        if project["demo"] or project["status"] != "strategy_review" or strategy not in {s["id"] for s in project["strategies"]}:
            raise ValueError("Complete the interview and choose a proposed strategy")
        if contract_hash != digest(project["requirements"]):
            raise ValueError("Requirements changed; review the new contract")
        project["approval"] = {"contract_hash": contract_hash, "version": project["requirements"]["version"], "strategy": strategy, "at": now(), "actor": "local-operator", "scope": "planning only; execution requires repository, measurable gates and configured sandbox"}
        project["status"] = "planned"
        self.store.save(project, {"action": "strategy_approved", **project["approval"]})
        return project

    def create(self, path=None):
        demo = path is None
        report = inspect_repository(path or ROOT / "examples/invoice")
        project = {"id": uuid.uuid4().hex, "name": "Invoice migration · demonstration" if demo else Path(path).name,
                   "demo": demo, "created_at": now(), "status": "awaiting_approval" if demo else "discovered", "cursor": 0,
                   "requirements": {"version": 1, "target": "Refactor Python invoice calculation into a line-item module", "compatibility": "Exact JSON output for six disclosed fixture scenarios; no normalization", "memory_growth_limit_bytes": 65536,
                                    "execution": "Bundled trusted fixture only; no production access", "max_steps": 8, "max_attempts_per_step": 2, "worker_timeout_seconds": 10},
                   "strategies": [{"id": "incremental", "name": "Incremental extraction", "risk": "low for this fixture", "effort": "small", "rollback": "restore source snapshot", "tradeoff": "Small compatibility boundary; limited modernization"},
                                  {"id": "rewrite", "name": "Full runtime rewrite", "risk": "high", "effort": "unknown", "rollback": "parallel legacy service", "tradeoff": "More modernization; larger verification surface; not executable in prototype"}],
                   "discovery": report, "approval": None, "tasks": [{"name": step, "role": role, "status": "pending", "attempts": 0} for step, role in zip(STEPS, ROLES)],
                   "gates": [{"name": name, "status": "unverified", "reason": "No applicable evidence"} for name in DIMENSIONS], "findings": [], "knowledge": [], "forecast_history": [], "acceptance": "Incomplete"}
        self.forecast(project, "Initial intake; no duration history")
        self.store.save(project, {"action": "discovered", "actor": "legacy-intelligence"})
        return project

    def approve(self, project_id, contract_hash):
        project = self.store.get(project_id)
        if not project["demo"] or project["status"] != "awaiting_approval":
            raise ValueError("Only a waiting bundled demonstration can be approved")
        if contract_hash != digest(project["requirements"]):
            raise ValueError("Stale requirements; review the current contract")
        project["approval"] = {"contract_hash": contract_hash, "version": 1, "strategy": "incremental", "at": now(), "actor": "local-operator", "scope": "execute bounded demo; not production acceptance"}
        project["status"] = "ready"
        self.store.save(project, {"action": "approved", **project["approval"]})
        return project

    def control(self, project_id, action):
        project = self.store.get(project_id)
        allowed = {"pause": ({"ready"}, "paused"), "resume": ({"paused"}, "ready"), "cancel": ({"ready", "paused", "blocked", "awaiting_approval"}, "cancelled"), "retry": ({"blocked"}, "ready")}
        if action not in allowed or project["status"] not in allowed[action][0]:
            raise ValueError("Invalid workflow transition")
        if action == "retry" and project["tasks"][project["cursor"]]["attempts"] >= 2:
            raise ValueError("Attempt budget exhausted")
        project["status"] = allowed[action][1]
        self.forecast(project, action)
        self.store.save(project, {"action": action, "actor": "local-operator"})
        return project

    def forecast(self, project, reason):
        durations = [t["seconds"] for t in project["tasks"] if t.get("seconds") is not None]
        pending = [t["name"] for t in project["tasks"] if t["status"] != "completed"]
        # Heterogeneous tasks cannot be credibly extrapolated from the same run.
        project["forecast_history"].append({"at": now(), "reason": reason, "remaining_tasks": len(pending), "critical_path": pending,
            "observed_active_seconds": sum(durations), "remaining_active_seconds": 0 if project["demo"] and not pending else None,
            "completion_range": None, "confidence": "insufficient evidence", "uncertainty": "No comparable migration history; human delay, real integration, soak and cloud work are unestimated"})

    def run_worker(self, source, workspace):
        # Only constants from this module / bundled fixture reach this execution path.
        target = workspace / "application.py"
        target.write_text(source)
        started = time.monotonic()
        result = subprocess.run([sys.executable, "-I", str(ROOT / "lucy/worker.py"), str(target)], cwd=workspace,
            env={"PATH": os.defpath, "PYTHONIOENCODING": "utf-8"}, capture_output=True, text=True, timeout=10, check=True)
        if len(result.stdout) > 200000:
            raise ValueError("Worker output budget exceeded")
        return {**json.loads(result.stdout), "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "wall_seconds": time.monotonic() - started}

    def step(self, project_id):
        project = self.store.get(project_id)
        if project["status"] != "ready" or not project["demo"]:
            raise ValueError("Workflow must be approved and ready")
        if not project["approval"] or project["approval"]["contract_hash"] != digest(project["requirements"]):
            raise ValueError("Approval does not match requirements")
        task = project["tasks"][project["cursor"]]
        if task["attempts"] >= 2:
            raise ValueError("Attempt budget exhausted")
        task["attempts"] += 1
        start = time.monotonic()
        artifacts = {}
        workspace = self.store.root / "workspaces" / project_id
        workspace.mkdir(parents=True, exist_ok=True)
        evidence = {e["id"].split(":", 1)[1]: e["body"] for e in self.store.evidence(project_id)}
        name = task["name"]
        try:
            if name == "baseline":
                source = (ROOT / "examples/invoice/legacy.py").read_text()
                artifacts["baseline"] = {**self.run_worker(source, workspace), "source": source}
            elif name == "implement":
                artifacts["candidate_source"] = {"source": BAD_SOURCE, "sha256": hashlib.sha256(BAD_SOURCE.encode()).hexdigest(), "note": "Intentional rounding regression and retained-request allocation"}
            elif name == "verify":
                artifacts["candidate"] = self.run_worker(evidence["candidate_source"]["source"], workspace)
            elif name == "critic":
                review = critic(evidence["baseline"], evidence["candidate"])
                artifacts["initial_review"] = review
                project["findings"] = [{**f, "status": "open", "evidence": f"{project_id}:initial_review"} for f in review["findings"]]
                self.set_gate(project, "functional", "failed" if any(f["kind"] == "functional" for f in review["findings"]) else "passed", "Initial differential review")
                self.set_gate(project, "memory", "failed" if any(f["kind"] == "memory" for f in review["findings"]) else "passed", "Initial allocation probe")
            elif name == "remediate":
                artifacts["remediated_source"] = {"source": FIXED_SOURCE, "sha256": hashlib.sha256(FIXED_SOURCE.encode()).hexdigest(), "note": "Decimal HALF_UP contract restored; unbounded history removed"}
            elif name == "revalidate":
                run = self.run_worker(evidence["remediated_source"]["source"], workspace)
                review = critic(evidence["baseline"], run, author="remediation", reviewer="guardian-checks")
                artifacts.update({"revalidation": run, "final_review": review})
                for finding in project["findings"]:
                    finding["status"] = "open" if any(f["kind"] == finding["kind"] for f in review["findings"]) else "resolved"
                    finding["revalidation_evidence"] = f"{project_id}:final_review"
                for dimension in ("functional", "memory"):
                    self.set_gate(project, dimension, "failed" if any(f["kind"] == dimension for f in review["findings"]) else "passed", "Bundled scenario scope only", f"{project_id}:revalidation")
                self.set_gate(project, "required_tests", "passed", "Six demo scenarios executed; real application tests unavailable", f"{project_id}:revalidation")
            elif name == "learn":
                if evidence["final_review"]["findings"]:
                    raise ValueError("Cannot verify learning while final findings remain")
                project["knowledge"] = [{"id": uuid.uuid4().hex, "version": 1, "source_project": project_id, "technology": "Python / Decimal", "status": "verified", "date": now(),
                    "problem": "Float rewrite changed rounding; request history retained allocations", "root_cause": "Binary float formatting and unbounded retained bytearrays", "solution": "Explicit Decimal HALF_UP and stateless processing", "evidence": [f"{project_id}:initial_review", f"{project_id}:final_review"],
                    "scope": "This synthetic fixture and this Python runtime only", "reuse_conditions": "Validate rounding contract and workload in destination project", "limitations": "No cross-project authorization or external validation"}]
                artifacts["knowledge"] = project["knowledge"]
            elif name == "report":
                project["status"] = "review_required"
                artifacts["assurance_report"] = {"project_id": project_id, "decision": decide(project["gates"]), "gates": project["gates"], "findings": project["findings"],
                    "scope": "Synthetic invoice migration demonstration", "production_ready": False, "limitations": ["No real legacy repository supplied", "No AI-generated migration or independent human review", "No security, persistence, performance, soak, cloud or operational evidence"],
                    "evidence_manifest": [{"id": e["id"], "sha256": e["sha256"]} for e in self.store.evidence(project_id)]}
            task.update(status="completed", seconds=time.monotonic() - start)
            project["cursor"] += 1
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            task.update(status="failed", error=type(exc).__name__ + ": " + str(exc)[:300], seconds=time.monotonic() - start)
            project["status"] = "blocked"
            artifacts = {}
        project["acceptance"] = decide(project["gates"])
        self.forecast(project, name + ": " + task["status"])
        self.store.save(project, {"action": name, "actor": task["role"], "status": task["status"], "seconds": task["seconds"]}, {f"{project_id}:{key}": body for key, body in artifacts.items()})
        return project

    @staticmethod
    def set_gate(project, name, status, reason, evidence=None):
        gate = next(g for g in project["gates"] if g["name"] == name)
        gate.update(status=status, reason=reason, evidence=evidence)

    def detail(self, project_id):
        project = self.store.get(project_id)
        return {**project, "contract_hash": digest(project["requirements"]), "events": self.store.events(project_id), "evidence": self.store.evidence(project_id)}
