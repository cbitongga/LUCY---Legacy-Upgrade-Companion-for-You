# Copy-paste prompt for another model in the controlled environment

You are continuing development of **LUCY — Legacy Upgrade Companion for You**, an evidence-based software migration platform. Work in the existing local clone. It may be behind GitHub, and downloading updates, dependencies, SDKs or container images may be prohibited. **Do not assume internet access, ask me to download updates as the first step, or bypass environment restrictions.** Inspect what is present and implement the missing pieces locally using approved capabilities. Prefer Python 3.11+ standard library and existing dependencies. Do not overwrite local changes.

Repository identity: `https://github.com/cbitongga/LUCY---Legacy-Upgrade-Companion-for-You.git`. The earlier baseline commit is `af5046854e0c8e4c564a0c007be579d4d96b7521`; the standalone work is newer. You do not need to fetch that commit to carry out this prompt. If a permitted local copy already includes the new modules below, extend and verify them rather than implementing duplicates.

## Product direction and user decisions

LUCY must be a standalone service that owns its workflow, approvals, agent assignments, state, evidence and progress. It must run without an open VS Code Copilot or Claude CLI session. The browser is an observation/control interface; closing it must not stop background work. Copilot/Claude CLI may become optional execution adapters, not mandatory infrastructure. A running host/service is still required.

Start with agent definitions and the requirements interview. The user will supply a real application migration later. **Do not require or invent a sample migration to begin.** There is an optional synthetic invoice fixture for internal developer tests; never call it proof of a real migration or production readiness.

The visual identity is already approved: dark interface, a simplified programmer cat inside the U of LUCY, sage-green U, full laptop mascot on the welcome screen, and “Legacy Upgrade Companion for You” beneath the wordmark. Preserve branding and existing workflows.

## Baseline repository to inspect

Read any applicable AGENTS.md, README.md and project documentation. Expected layout:

- `lucy/server.py`: loopback HTTP server with fixed static routes, same-origin action-token checks and project APIs.
- `lucy/__main__.py`: CLI commands `serve`, `inspect`, `demo`, `report`.
- `lucy/store.py`: SQLite `projects(id, body)`, `events(seq, project_id, at, body)` and immutable `evidence(id, project_id, sha256, body)`.
- `lucy/engine.py`: interview projects, versioned requirements, provisional strategies, contract-hash-bound planning approval, fail-closed gates and optional bounded fixture workflow.
- `lucy/agents.py`: 18 specialist definitions, capability names, prompts and a 12-question interview. Definitions do not imply live model execution.
- `lucy/assurance.py`: gate evaluation and fixture comparisons.
- `lucy/discovery.py`: metadata-only inspection; no repository code execution.
- `lucy/worker.py`: **existing trusted synthetic fixture runner**. Do not repurpose it for arbitrary repository execution.
- `lucy/web/index.html`, `app.js`, `style.css`: buildless UI with projects, interview, agents, strategy approvals, assurance and knowledge.
- `tests/test_lucy.py`: 12 baseline tests.
- `docs/original-request.md`, `architecture.md`, `agents-and-tools.md`, `roadmap.md`, `runbook.md`.

Baseline interview states: `interviewing → strategy_review → planned`. Editing answers increments the contract version and clears approval. Planning approval must never authorize source changes or deployment. A pending/failed mandatory gate prevents acceptance. Forecast dates remain unknown without evidence.

## Standalone slice implemented in the other environment

The other environment has started the following implementation. Reproduce missing functionality here if you cannot pull it. This is a first standalone **read-only requirements-review slice**, not a complete migration agent platform.

### 1. Durable queue (`lucy/jobs.py`)

Add tables non-destructively in the existing SQLite store:

```sql
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  status TEXT NOT NULL,
  body TEXT NOT NULL,
  owner TEXT,
  lease_until REAL,
  request_key TEXT NOT NULL,
  UNIQUE(project_id, request_key)
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);
CREATE TABLE IF NOT EXISTS job_events (
  seq INTEGER PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  at TEXT NOT NULL,
  action TEXT NOT NULL
);
```

Use a separate SQLite connection per process, foreign keys, a ten-second busy timeout and WAL on a local filesystem. Do not share a connection across threads/processes. Back up existing state before schema changes when appropriate. WAL backups must use SQLite backup or stop all writers and copy the whole data directory.

Job JSON includes ID, project, kind=`requirements_review`, role=`interviewer`, status, provider, pinned provider configuration, requirements snapshot, contract hash/version, attempts, timestamps, result/error, owner, lease deadline, consent and read-only scope. No credentials in job records.

Implement enqueue, list/detail, atomic claim, heartbeat, finish, recovery and controls. Use `BEGIN IMMEDIATE` for claim/state transitions. Enqueue must validate the project, current contract hash, provider, input size, consent and idempotency key. Permit one active job per project. Repeated same-key/same-input requests return the original job; conflicting reuse fails.

States: `queued → running → completed|failed|stale`; `queued ↔ paused`; active jobs can become `cancelled`; expired running leases become `interrupted`. Resume/retry recheck current contract and pinned configuration. Maximum two attempts. Interrupted jobs require explicit retry, since the previous paid request may have reached the provider. Never automatically replay an uncertain paid request.

Use a 90-second lease, refreshed every five seconds. Owner/lease checks must reject late output from cancelled, expired or superseded work. If the contract changed before claim, mark stale without sending data. If it changes during execution, retain a stale report without overwriting the newer project. Later contract edits must make older reports visibly outdated.

Completion atomically writes the result, progress event and hashed evidence classified as **unverified planning advice**. Do not replace the whole project snapshot from the worker. Do not change requirements, approvals, gates, acceptance, findings or knowledge verification status.

### 2. Provider interface (`lucy/providers.py`)

Implement `run_review(requirements, config)` behind a provider boundary. First support:

- `offline`: deterministic checklist of missing interview answers and generic review risks. No network, credentials or model. Label it rules-based, not AI.
- `anthropic`: optional direct HTTPS Messages API adapter with Python standard-library HTTP transport. No Claude CLI or SDK installation required. Configuration uses `ANTHROPIC_API_KEY`, explicit `LUCY_MODEL`, optional `ANTHROPIC_WORKSPACE_ID`, and configurable `LUCY_ANTHROPIC_VERSION`. The reference implementation defaults to compatibility version `2023-06-01`; validate the version allowed by this environment before live use. Do not guess a model identifier or assume a subscription covers API charges.

The reference adapter pins `https://api.anthropic.com/v1/messages`; sends `x-api-key`, `anthropic-version`, JSON content type and optional workspace header; sends only fixed reviewer instructions plus the saved requirements object. The provider receives no repository files or local paths. Explicit user consent is required to transmit the current contract. Do not use external providers where environment policy prohibits transmission. No live API call has yet been verified in the other environment.

Keep TLS validation enabled, block redirects, never log raw headers/error bodies or secrets, cap input at 64 KB including prompt overhead, response at 100 KB and generated output at 1,800 tokens. One request per attempt; no automatic retry/fallback. Set a 30-second socket timeout and enforce a 60-second parent task deadline. These are per-job limits, not a monetary project budget.

Only accept JSON with exactly:

```json
{"summary":"text","questions":["text"],"risks":["text"],"next_steps":["text"]}
```

Validate types, lengths and list counts. Reject extra tool/action fields, malformed output and truncated responses. Store provider/model and sanitized token counts separately. Model text is advice; it is never dispatched to a shell or treated as permission. If this environment requires another approved endpoint, design a separate adapter with its explicit authentication/data rules rather than silently rerouting credentials.

### 3. Independent worker (`lucy/runtime.py`)

Add CLI commands:

```sh
python3 -m lucy serve
python3 -m lucy --data /absolute/state/path serve --no-worker
python3 -m lucy --data /absolute/state/path worker
python3 -m lucy --data /absolute/state/path worker --once
```

Default `serve` launches one worker subprocess using the current Python interpreter and absolute state path. `--no-worker` permits separate service supervision. A worker claims jobs and runs the provider in a bounded spawned child process, not in the HTTP request handler. Poll cancellation, heartbeat ownership, enforce the task deadline, terminate/clean up children and handle graceful shutdown. Closing the UI must not stop work. Stopping the default service stops its managed worker; separately supervised workers can continue. Do not claim automatic crash restart unless implemented.

Process separation is not a sandbox for arbitrary code. No general filesystem/network/shell agent tools are enabled in this slice.

### 4. UI/API integration

Add “Agent operations” navigation. Show worker health, available providers, saved contract version, explicit external-transmission consent, Run offline checklist, Send requirements to Claude API, jobs, statuses, attempts, safe errors, stale-contract warning, reports and ordered progress events. Support pause/resume/cancel and bounded manual retry, with a possible-charge notice for external retries.

API routes:

- GET `/api/runtime`
- GET `/api/projects/{id}/jobs`
- GET `/api/jobs/{id}`
- POST `/api/projects/{id}/jobs` with provider, contract_hash, request_key, consent
- POST `/api/jobs/{id}/{pause|resume|cancel|retry}`

Reuse same-origin action-token protection for mutations. Keep server loopback-only. Return no API keys to the browser. Update misleading “provider not configured” copy dynamically; presence of variables is not proof of connectivity. Other registered specialists must not be labeled as executing AI agents.

Poll persisted progress every two seconds only while Agent operations is open. Refresh only the job list and health so that unsaved interview fields and consent checkboxes are not reset. Preserve opened evidence details. This is polling, not SSE or token streaming. Reopening the UI must reconstruct progress from the database.

### 5. Tests and documentation

Keep the 12 baseline tests. Add tests for idempotency, conflicting keys, explicit transmission consent, unsupported providers, atomic competing claims, pause/resume/cancel, expired leases/manual bounded retries, late-result rejection, stale contracts before/during/after work, a real spawned offline worker, persistence across restart, unchanged requirements/approvals/gates, input/output caps, schema validation, provider HTTP contract and safe error handling. Mock external HTTP; no live API access in tests.

The other environment has 27 passing unit/worker tests plus one separate loopback HTTP integration smoke test as of this handoff. Re-run and report your own results; do not inherit that claim as proof of this checkout.

Use `python3 -m unittest discover -s tests -v`. If Node is available, `node --check lucy/web/app.js`; do not require Node to run LUCY. An opt-in `python3 tests/http_smoke.py` starts a temporary loopback service, checks missing-token rejection, creates a project, queues offline review, checks idempotency and completion/evidence, and verifies clean shutdown.

Document launch, configuration, what data leaves the machine, provider limitations, backup/recovery, cancellation semantics and remaining work. Preserve `.lucy/`, credentials and caches outside Git. Do not install software, enable remote exposure or change security policy to make a test pass.

## Next work after this slice

After verifying the standalone queue and planning reviews, extend one approved capability at a time: repository intake, model-backed strategy planning, capability broker, isolated implementation workspaces, protected tests, independent verification, project cost budgets and supervised worker recovery. Only later add true migration execution. Preserve the original seven-milestone roadmap. Never weaken gate criteria to obtain a successful outcome.

First report which of these features already exist in this clone, then implement missing pieces in small reviewable increments. If the environment forbids a network action, continue offline work and identify the exact remaining boundary. Finish with changed files, test evidence, implemented behavior, limitations and next steps. Commit/push only if authorized in this environment; never overwrite unrelated local changes or force-push.
