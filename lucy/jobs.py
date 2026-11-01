"""Durable, leased read-only planning queue. No project snapshot writes here."""
from contextlib import contextmanager
import hashlib
import json
import time
import uuid

from .engine import digest
from .providers import configuration, MAX_INPUT_BYTES
from .store import now
from .delegation import plan

ACTIVE = ("queued", "running", "paused")
LEASE_SECONDS = 90
MAX_ATTEMPTS = 2


class Jobs:
    def __init__(self, store):
        self.store = store
        self.db = store.db

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def event(self, job, action):
        self.db.execute("INSERT INTO job_events(job_id,at,action) VALUES(?,?,?)", (job["id"], now(), action))

    def write(self, job):
        job["updated_at"] = now()
        self.db.execute("UPDATE jobs SET status=?,body=?,owner=?,lease_until=? WHERE id=?",
                        (job["status"], json.dumps(job), job.get("owner"), job.get("lease_until"), job["id"]))

    def get(self, job_id):
        row = self.db.execute("SELECT body FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError("Job not found")
        return json.loads(row[0])

    def detail(self, job_id):
        job = self.get(job_id)
        job["events"] = [{"sequence": seq, "at": at, "action": action} for seq, at, action in self.db.execute(
            "SELECT seq,at,action FROM job_events WHERE job_id=? ORDER BY seq", (job_id,))]
        job["current_contract"] = digest(self.store.get(job["project_id"])["requirements"]) == job["contract_hash"]
        return job

    def list(self, project_id):
        self.store.get(project_id)
        return [self.detail(row[0]) for row in self.db.execute("SELECT id FROM jobs WHERE project_id=? ORDER BY rowid DESC LIMIT 50", (project_id,)).fetchall()]

    def enqueue(self, project_id, provider, contract_hash, request_key, consent=False, delegate=False):
        if type(delegate) is not bool:
            raise ValueError("delegate must be a boolean")
        if not isinstance(request_key, str) or not 8 <= len(request_key) <= 100:
            raise ValueError("An idempotency key of 8–100 characters is required")
        if provider not in ("offline", "anthropic"):
            raise ValueError("Unsupported provider")
        if provider == "anthropic" and consent is not True:
            raise ValueError("Explicit consent to send this contract to Anthropic is required")
        with self.transaction():
            project = self.store.get(project_id)
            if project["demo"] or project["status"] not in {"interviewing", "strategy_review", "planned"}:
                raise ValueError("Only interview projects support background review")
            if digest(project["requirements"]) != contract_hash:
                raise ValueError("Requirements changed; refresh before starting a review")
            existing = self.db.execute("SELECT body FROM jobs WHERE project_id=? AND request_key=?", (project_id, request_key)).fetchone()
            if existing:
                job = json.loads(existing[0])
                if job["provider"] != provider or job["contract_hash"] != contract_hash or job.get("delegate", False) != delegate:
                    raise ValueError("Idempotency key already used for different inputs")
                return job
            if self.db.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','paused')", (project_id,)).fetchone():
                raise ValueError("A review is already active for this project")
            if len(json.dumps(project["requirements"]).encode()) > MAX_INPUT_BYTES - 2000:
                raise ValueError("Requirements exceed the review input budget")
            job = {"id": uuid.uuid4().hex, "project_id": project_id, "kind": "requirements_review", "role": "interviewer",
                   "delegate": delegate, "children": plan(project["requirements"]) if delegate else [],
                   "status": "queued", "stage": "queued", "provider": provider, "config": configuration(provider), "requirements": project["requirements"],
                   "contract_hash": contract_hash, "attempts": 0, "created_at": now(), "updated_at": now(), "result": None,
                   "error": None, "owner": None, "lease_until": None, "consent": consent is True,
                   "scope": "Read-only advice. No tools, repository execution, approvals or gate changes."}
            self.db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?)", (job["id"], project_id, "queued", json.dumps(job), None, None, request_key))
            self.event(job, "queued")
            return job

    def recover(self):
        # Never repeat an uncertain paid request automatically after a crash.
        with self.transaction():
            rows = self.db.execute("SELECT body FROM jobs WHERE status='running' AND lease_until<?", (time.time(),)).fetchall()
            for row in rows:
                job = json.loads(row[0])
                job.update(status="interrupted", owner=None, lease_until=None, error="Worker lease expired; review before retrying. A previous provider call may have been billed.")
                self.write(job)
                self.event(job, "interrupted")

    def claim(self, owner):
        self.recover()
        with self.transaction():
            row = self.db.execute("SELECT body FROM jobs WHERE status='queued' ORDER BY rowid LIMIT 1").fetchone()
            if not row:
                return None
            job = json.loads(row[0])
            if digest(self.store.get(job["project_id"])["requirements"]) != job["contract_hash"]:
                job.update(status="stale", error="Contract changed before execution")
                self.write(job)
                self.event(job, "stale")
                return None
            job.update(status="running", stage="reviewing", owner=owner, lease_until=time.time() + LEASE_SECONDS, attempts=job["attempts"] + 1, error=None)
            self.write(job)
            self.event(job, "running")
            return job

    def heartbeat(self, job_id, owner):
        with self.transaction():
            job = self.get(job_id)
            if job["status"] != "running" or job["owner"] != owner or job["lease_until"] < time.time():
                return False
            job["lease_until"] = time.time() + LEASE_SECONDS
            self.write(job)
            return True

    def child_update(self, job_id, owner, child_id, result=None):
        with self.transaction():
            job = self.get(job_id)
            if job['status'] != 'running' or job['owner'] != owner or job['lease_until'] < time.time():
                return False
            child = next(c for c in job['children'] if c['id'] == child_id)
            if result is None:
                if child['status'] != 'pending' or any(c['status'] == 'running' for c in job['children']):
                    raise ValueError('Child cannot be started')
                child['status'] = 'running'
            else:
                if child['status'] != 'running':
                    raise ValueError('Child is not running')
                child.update(status='completed', result=result)
            self.write(job)
            self.event(job, 'child:' + child_id + ':' + child['status'])
            return True

    def advance(self, job_id, owner, stage):
        """Persist actual worker milestones; never advance by a timer."""
        previous = {"validating": "reviewing", "saving": "validating"}
        if stage not in previous:
            raise ValueError("Unknown execution stage")
        with self.transaction():
            job = self.get(job_id)
            if job["status"] != "running" or job["owner"] != owner or job["lease_until"] < time.time():
                return False
            if job.get("stage", "reviewing") != previous[stage]:
                raise ValueError("Execution stages must advance in order")
            job["stage"] = stage
            self.write(job)
            self.event(job, stage)
            return True

    def finish(self, job_id, owner, result=None, error=None):
        with self.transaction():
            job = self.get(job_id)
            if job["status"] != "running" or job["owner"] != owner or job["lease_until"] < time.time():
                return False
            current = digest(self.store.get(job["project_id"])["requirements"]) == job["contract_hash"]
            job.update(status="failed" if error else ("completed" if current else "stale"), result=result,
                       error=error, owner=None, lease_until=None)
            if result is not None:
                job["stage"] = "finished"
                body = {"job_id": job_id, "contract_hash": job["contract_hash"], "contract_version": job["requirements"]["version"],
                        "classification": "unverified planning advice", "current_at_completion": current, **result}
                raw = json.dumps(body, sort_keys=True)
                key = f"{job['project_id']}:review-{job_id}-attempt-{job['attempts']}"
                self.db.execute("INSERT INTO evidence VALUES(?,?,?,?)", (key, job["project_id"], hashlib.sha256(raw.encode()).hexdigest(), raw))
                job["evidence_id"] = key
            self.write(job)
            self.event(job, job["status"])
            self.db.execute("INSERT INTO events(project_id,at,body) VALUES(?,?,?)", (job["project_id"], now(), json.dumps({"action": "background_review_" + job["status"], "actor": "requirements-reviewer", "job_id": job_id})))
            return True

    def control(self, job_id, action):
        self.recover()
        with self.transaction():
            job = self.get(job_id)
            transitions = {"pause": ({"queued"}, "paused"), "resume": ({"paused"}, "queued"),
                           "cancel": ({"queued", "paused", "running"}, "cancelled"), "retry": ({"failed", "interrupted"}, "queued")}
            if action not in transitions or job["status"] not in transitions[action][0]:
                raise ValueError("Invalid job transition; running jobs can only be cancelled")
            if action in {"retry", "resume"}:
                if digest(self.store.get(job["project_id"])["requirements"]) != job["contract_hash"]:
                    raise ValueError("Contract changed; start a new review")
                if job["attempts"] >= MAX_ATTEMPTS:
                    raise ValueError("Two-attempt budget exhausted")
                if configuration(job["provider"]) != job["config"]:
                    raise ValueError("Provider configuration changed; start a new review")
                if self.db.execute("SELECT 1 FROM jobs WHERE project_id=? AND id!=? AND status IN ('queued','running','paused')", (job["project_id"], job_id)).fetchone():
                    raise ValueError("Another review is active")
            job.update(status=transitions[action][1], owner=None, lease_until=None)
            if action == "retry":
                job["stage"] = "queued"
                for child in job.get("children", []):
                    child.update(status="pending", result=None)
            self.write(job)
            self.event(job, action)
            return job
