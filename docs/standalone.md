# Standalone LUCY: first execution slice

LUCY now starts its own background worker. VS Code, Copilot and Claude CLI are not required. This milestone executes **read-only requirements reviews**, not general-purpose migrations.

## Start without downloads or credentials

Python 3.11+ and its standard library are sufficient. No pip install, Node build, Docker image or external service is required for offline operation.

```sh
python3 -m lucy serve
```

Open the loopback URL, open/create a project, save interview answers, then choose **Agent operations → Run offline checklist**. The offline handler identifies unanswered interview questions and emits a deterministic checklist. It is explicitly not AI. Jobs and progress survive browser closure. Stop the server with Ctrl-C; restart against the same data directory to retain the queue and results.

The UI starts one worker subprocess by default. To manage UI and worker independently, use the same **absolute** data directory in both commands:

```sh
python3 -m lucy --data /path/to/lucy-state serve --no-worker
python3 -m lucy --data /path/to/lucy-state worker
```

For a single queued job:

```sh
python3 -m lucy --data /path/to/lucy-state worker --once
```

On a controlled machine, use the organization's approved service manager to keep these processes alive. Closing a browser does not stop jobs; stopping the host or service does. The UI labels separately managed workers as “external worker required”; it does not yet discover their process health.

## Optional direct Claude API

Set `ANTHROPIC_API_KEY` through the environment's approved secret mechanism and set `LUCY_MODEL` to a model identifier your organization permits. Never paste keys into chat, the interview, or tracked files. Start/restart both server and worker with the configuration. An optional `ANTHROPIC_WORKSPACE_ID` is supported for keys requiring a workspace. `LUCY_ANTHROPIC_VERSION` defaults to the compatibility version `2023-06-01` and can be set to the version approved for your API environment.

The UI requires an authorization checkbox before **Send requirements to Claude API**. The request sends only the saved requirements object plus the fixed reviewer instructions, not repository source, project names, paths or local credentials. Requirements may themselves contain sensitive data; only send contracts approved for that provider. The endpoint is fixed to `https://api.anthropic.com/v1/messages`, TLS verification remains enabled, and redirects are blocked. Custom endpoints, enterprise gateways, Bedrock, other providers and CLI adapters are not implemented.

Uses the [Messages API](https://platform.claude.com/docs/en/api/messages) and [documented authentication headers](https://platform.claude.com/docs/en/api/overview). Transport and response parsing are covered by mocked tests. **No live API call has been made or validated in this implementation session.** Model access, version compatibility, network policy and actual billing must be verified in the target environment. “Configured” in the UI indicates environment variables are present, not successful connectivity.

## Execution and evidence guarantees

- Jobs pin the contract hash/version, provider configuration and local consent record.
- A per-project idempotency key prevents duplicate enqueue after a retried request; only one active review is permitted per project.
- SQLite transactions atomically claim jobs. Each worker uses its own connection. WAL and a busy timeout allow concurrent UI and worker access on one machine.
- Worker ownership and a 90-second lease prevent late results from overwriting another attempt. Heartbeats refresh every five seconds.
- A spawned provider child has a 60-second task deadline; the HTTP socket timeout is 30 seconds. Input is capped at 64 KB including prompt overhead; responses at 100 KB; maximum output is 1,800 tokens.
- Exactly one provider request per attempt, at most two attempts for one job. No automatic API retry or provider fallback. These are per-job limits, **not a project dollar budget**; enforce account spending caps externally until that is implemented.
- Expired leases become `interrupted`, never silently requeued. Manual retry can incur another charge if the original request reached the provider.
- Pause applies to queued jobs; resume rechecks the contract and configuration. Cancel applies to queued/paused/running jobs. It discards late output and stops local provider work; it cannot undo an already-sent remote request or guarantee billing cancellation.
- Provider output must be JSON with exactly `summary`, `questions`, `risks`, `next_steps`. Unexpected fields, tool requests, truncation and malformed output fail closed.
- Reports are stored as **unverified planning advice** with hash-linked artifacts. They cannot modify project requirements, approvals, findings or gates. Results are marked stale if requirements changed; later edits are also shown as an outdated contract in the UI.
- Worker errors retain safe categories, not raw HTTP bodies, headers, credentials or prompts. Local requirements and reports remain plaintext in the data directory, as before.

## Progress and endpoints

The UI polls every two seconds **only on Agent operations**, updating the job list without replacing interview fields or the external-provider consent checkbox. This is persisted progress polling, not token streaming or SSE. A reconnect reads the saved job events.

- GET `/api/runtime`: worker process status and provider availability.
- GET `/api/projects/{id}/jobs`: latest 50 jobs with event histories.
- GET `/api/jobs/{id}`: persisted job and ordered progress events.
- POST `/api/projects/{id}/jobs`: `provider`, `contract_hash`, `request_key`, optional `consent: true` for Anthropic.
- POST `/api/jobs/{id}/{pause|resume|cancel|retry}`: operator control.

All mutations use the existing same-origin action-token protection. This is still a single local operator service, not organization authentication.

## Storage and recovery

Startup adds `jobs`, `job_events` and a status index using `CREATE TABLE IF NOT EXISTS`; it does not rewrite existing project/evidence rows. SQLite schema migration versioning remains future work. With WAL enabled, use SQLite's online backup API or stop **all** writers before copying the whole data directory, including any WAL files. Never copy only a live `.sqlite3` file.

Graceful shutdown terminates the managed worker and its active provider child. Hard crashes may leave an uncertain in-flight API request; lease expiry makes the job visible as interrupted on the next worker/control recovery pass. A stopped managed worker is shown as stopped; this prototype does not automatically restart crashed workers. Use an approved service supervisor for that.

## Verification

```sh
python3 -m unittest discover -s tests -v
node --check lucy/web/app.js
python3 tests/http_smoke.py
```

Node is optional for a developer syntax check; it is not a runtime dependency. The HTTP smoke test needs permission to bind loopback sockets and uses only temporary local state and offline review. The unit tests include a real spawned worker, atomic claims, cancellation, lease expiry, bounded retries, stale contracts, schema rejection and mocked provider requests. No external network or credentials are needed for tests.

Verification in this implementation: 27 unit/worker tests passed, the separate loopback HTTP smoke test passed, and JavaScript syntax validation passed. Browser QA queued an offline checklist from Agent operations and observed it complete through automatic progress polling, with missing questions and an explicitly unverified report. External API controls were disabled without configuration. See [UI verification screenshot](standalone-operations-preview.png).

## Next milestone

Expand supported agents through an enforced capability broker, approved repository intake, isolated workspaces and protected verifier artifacts. Add enterprise authentication, endpoint adapters, calibrated spending budgets, worker supervision and event streaming as needed. Do not describe this slice as autonomous coding or completed migration execution.

## Agent activity and remaining steps

Mission control includes a compact activity board; Agent operations shows all 18 specialists with distinct local SVG icons. Open a project's **Progress** button to select its board. The page polls `GET /api/projects/{id}/activity` every two seconds. Active steps animate, with reduced-motion support; paused, failed, interrupted, outdated, idle, and unconfigured states have explicit labels. A failed refresh warns that the displayed state is old and stops animation.

Requirements reviews persist four checkpoints: check/claim contract, review requirements, validate report format, save report/evidence. The queue records `running`, `validating`, `saving`, then the terminal event. Step transitions require the live worker's ownership and lease. A failed or cancelled step remains unfinished; retry starts a new attempt at zero. Expired leases never display as working. Offline reviews may finish between polls; their durable events remain available in review history.

The count applies only to the displayed review, three planning milestones, or eight synthetic fixture steps. A full application migration has no defined remaining-step count yet. Local role handlers are labeled separately from model calls; registering a specialist does not create an autonomous executor.

## Delegated reviews and robot mission map

**Launch offline crew** creates three bounded requirements assignments (mission/architecture, behavior/compatibility, permissions/constraints). Supplied security or runtime requirements split out dedicated reviews, up to five children. This is an explicit deterministic decomposition policy, not model-generated arbitrary task scheduling. All twelve questionnaire areas are covered once; each child receives the entire immutable requirements contract plus its own objective and focus keys. Child outputs remain individually inspectable and are combined into one bounded report. They do not establish repository-wide understanding or execute migration code.

POST the existing jobs endpoint with `delegate: true` (default false for compatibility). Child records are stored within the durable job, with parent ID, role, rationale, status and report; owner/lease-checked transitions produce child events. One child runs at a time, in an isolated provider process, with a 60-second deadline per child. Depth is one, maximum five children and two explicit attempts; no recursive spawning or automatic retries. Failure/cancellation stops further dispatch, rejects late output, and unfinished children are visibly blocked/cancelled. Retry resets all children and may repeat paid calls. Model configuration, consent and contract pinning apply to every child. Claude mode therefore permits up to five requests per attempt (ten across both attempts), not the original one-request single review budget. No paid calls were made during implementation validation.

The activity endpoint adds `subagents` and `subagent_count`; totals include children and shared prepare/validate/save checkpoints (6–8 steps). The glossy mission map displays 18 registered role robots, a central orchestrator and actual child assignments. Select a robot for its task, mode and context. Connections to specialist groups show organization, not a claim that unconfigured executors are running. Reduced motion and disconnected-state handling remain supported. Mobile layout reflows the map into connected branches.
