"""Read-only activity projections: known steps, not estimated completion times."""
import time

from .agents import QUESTIONNAIRE, registry
from .store import now

REVIEW_STEPS = [
    ("prepare", "Check contract & claim work", "orchestrator"),
    ("review", "Review requirements", "interviewer"),
    ("validate", "Validate report format", "guardian"),
    ("save", "Save report & evidence", "assurance"),
]
HANDLERS = {"orchestrator", "intelligence", "architect", "guardian", "assurance", "forecast", "interviewer"}
FIXTURE_ROLES = {"baseline": "intelligence", "implement": "implementation", "verify": "differential",
                 "critic": "critic", "remediate": "remediation", "revalidate": "guardian", "learn": "knowledge", "report": "assurance"}


def review_progress(job, timestamp=None):
    timestamp = time.time() if timestamp is None else timestamp
    status = job["status"]
    if status == "running" and (job.get("lease_until") or 0) < timestamp:
        status = "interrupted"
    # Compatibility with jobs completed before explicit stage events were introduced.
    stage = job.get("stage") or ("finished" if job.get("result") else "reviewing" if job.get("attempts") else "queued")
    cursor = {"queued": 0, "reviewing": 1, "validating": 2, "saving": 3, "finished": 4}.get(stage, 0)
    if status in {"queued", "paused"}:
        cursor = 0
    steps = []
    for index, (key, label, role) in enumerate(REVIEW_STEPS):
        step_status = "completed" if index < cursor else "pending"
        if index == cursor:
            step_status = {"running": "working", "failed": "failed", "interrupted": "interrupted",
                           "cancelled": "cancelled", "paused": "paused", "stale": "stale"}.get(status, "waiting")
        steps.append({"id": key, "label": label, "agent_id": role, "status": step_status})
    if job.get('delegate'):
        children = []
        for child in job['children']:
            child_status = child['status']
            if child_status == 'running':
                child_status = 'working' if status == 'running' else status
            if child_status == 'pending' and status in {'cancelled', 'failed', 'interrupted', 'stale', 'paused'}:
                child_status = 'blocked' if status in {'failed', 'interrupted'} else status
            children.append({'id': 'child-' + child['id'], 'label': child['name'], 'agent_id': 'child-' + child['id'], 'status': child_status})
        steps = [steps[0], *children, *steps[2:]]
    return {"title": "Delegated requirements review" if job.get('delegate') else "Requirements review", "kind": "review", "status": status, "steps": steps,
            "job_id": job["id"], "provider": job["provider"], "current_contract": job.get("current_contract", True),
            "contract_version": job["requirements"]["version"], "attempt": job.get("attempts", 0),
            "detail": "Recorded execution steps for this review only. Completing them does not mean the application migration is complete."}


def project_activity(project, jobs, timestamp=None):
    if project["demo"]:
        steps = [{"id": t["name"], "label": t["name"].replace('_', ' ').capitalize(),
                  "agent_id": FIXTURE_ROLES.get(t["name"], "orchestrator"), "status": t["status"]} for t in project["tasks"]]
        first = next((s for s in steps if s["status"] != "completed"), None)
        if first and first["status"] != "failed":
            first["status"] = "paused" if project["status"] == "paused" else "cancelled" if project["status"] == "cancelled" else "waiting"
        workflow = {"title": "Synthetic migration fixture", "kind": "fixture", "steps": steps, "status": project["status"],
                    "current_contract": True, "detail": "Fixture checkpoints only; synchronous work is not reported as a live agent session."}
    elif jobs:
        # Prefer real current work over history; list is newest-first from SQLite.
        job = next((j for j in jobs if j["status"] in {"running", "queued", "paused"}), jobs[0])
        workflow = review_progress(job, timestamp)
    else:
        answers = project["requirements"].get("answers", {})
        answered = sum(bool(answers.get(key)) for key, _, _ in QUESTIONNAIRE)
        complete = answered == len(QUESTIONNAIRE)
        workflow = {"title": "Requirements & planning", "kind": "planning", "status": project["status"], "current_contract": True,
                    "steps": [
                        {"id": "interview", "label": f"Complete interview ({answered}/{len(QUESTIONNAIRE)} answers)", "agent_id": "interviewer", "status": "completed" if complete else "waiting"},
                        {"id": "strategy", "label": "Prepare strategy options", "agent_id": "architect", "status": "completed" if project["strategies"] else "pending"},
                        {"id": "approval", "label": "Approve planning strategy", "agent_id": None, "status": "completed" if project["approval"] else "waiting" if complete else "pending"}],
                    "detail": "These are planning milestones. Interview answers and strategy approval need you; they are not autonomous agent activity."}
    completed = sum(step["status"] == "completed" for step in workflow["steps"])
    workflow.update(completed=completed, total=len(workflow["steps"]), remaining=len(workflow["steps"]) - completed)
    workflow["next_step"] = next((s["label"] for s in workflow["steps"] if s["status"] != "completed"), "All steps in this workflow are recorded")
    if not workflow["current_contract"]:
        workflow["next_step"] = "Start a review of the current contract; this report is outdated"
    agents = []
    children = job.get("children", []) if not project["demo"] and jobs else []
    for definition in registry():
        agent_id = definition["id"]
        assignment = next((s for s in workflow["steps"] if s["agent_id"] == agent_id), None)
        status = "idle" if agent_id in HANDLERS else "not_configured"
        task = "Available when assigned" if status == "idle" else "Executor not connected"
        if assignment:
            status = assignment["status"]
            status = "waiting" if status == "pending" else status
            task = assignment["label"]
            if not workflow["current_contract"] and status == "completed":
                status = "stale"
        if workflow["kind"] == "fixture" and assignment:
            mode = "Fixture handler"
        elif agent_id == "interviewer":
            mode = "Claude API" if workflow.get("provider") == "anthropic" else "Local checklist" if workflow["kind"] == "review" else "User-guided interview"
        else:
            mode = "Local handler" if agent_id in HANDLERS else "Registered definition"
        agents.append({"id": agent_id, "name": definition["name"], "status": status, "task": task, "mode": mode, "category": definition["activation"]})
    subagents = []
    for child in children:
        step = next(s for s in workflow['steps'] if s['id'] == 'child-' + child['id'])
        status = 'waiting' if step['status'] == 'pending' else step['status']
        if not workflow['current_contract'] and status == 'completed':
            status = 'stale'
        subagents.append({'id': step['id'], 'name': child['name'], 'role': child['role'],
                          'parent_id': child['parent_id'], 'status': status, 'task': child['objective'],
                          'mode': 'Claude API child' if workflow.get('provider') == 'anthropic' else 'Local checklist child',
                          'reason': child['reason'], 'context': 'Full contract v' + str(workflow['contract_version'])})
    counts = {key: sum(a["status"] == key for a in agents + subagents) for key in {"working", "waiting", "completed", "failed", "paused", "interrupted", "cancelled", "stale", "idle", "not_configured"}}
    return {"project_id": project["id"], "project_name": project["name"], "updated_at": now(), "workflow": workflow,
            "agents": agents, "subagents": subagents, "subagent_count": len(subagents), "counts": counts, "migration_remaining_steps": None,
            "migration_note": "Full migration step count is not yet defined. This view shows the current bounded workflow."}
