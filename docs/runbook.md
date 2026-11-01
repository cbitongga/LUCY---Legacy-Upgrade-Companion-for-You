# Developer and local operations runbook

## Launch and stop

From the repository root run `python3 -m lucy serve`. The service binds only 127.0.0.1:8765. Use `--port` after `serve` to select another local port, and `--data /absolute/directory` before `serve` to select a state directory. Ctrl-C stops the process; restart with the same directory to resume saved interviews and checkpoints. There is no automatic startup service.

If the execution environment blocks local listening sockets, grant only the local launch capability or run the command directly in a user terminal. Never solve this by binding to a public interface.

## State and backups

Local state is in `.lucy/lucy.sqlite3`, with optional fixture workspaces under `.lucy/workspaces/`. The directory is git-ignored. Interview answers and project names are stored in plaintext; do not enter secrets. SQLite is an inspectable prototype store, not encrypted or tamper-resistant storage.

Stop the server before copying the entire data directory as a backup. Restore into a separate directory and launch with `--data` to verify projects, contract versions, evidence hashes and audit records. Do not manually rewrite approval or evidence records. Production requires migrations, an online backup process and regular restoration drills.

## Failure handling

- An interrupted interview retains only explicitly saved answers. Unsaved text is not persisted.
- Requirements changes revoke earlier planning approval. Review the new contract and strategy again.
- Missing mandatory gate evidence leaves acceptance Incomplete. Failed gates produce Blocked. Never edit a gate merely to get an accepted outcome.
- Fixture steps fail into Blocked on worker errors/timeouts. Retry is explicit and bounded to two attempts per step. Pause/cancel acts between steps, not inside a running probe.
- A crash before a fixture checkpoint can rerun the current fixed step; it cannot deploy or modify the original application. The generated fixture file is disposable.
- Browser errors are displayed above the workspace. A server restart rotates the action token; reload the browser before saving.

## Validation

`python3 -m unittest discover -s tests -v` checks interview persistence, contract-version invalidation, strategy approval, forbidden execution, budgets, gate semantics, bounded discovery, differing verifier roles and the optional complete fixture cycle. `node --check lucy/web/app.js` checks browser-script syntax.

The fixture is explicitly synthetic. Its tests exercise deterministic repair and allocation detection; they do not demonstrate an AI performing a real migration. It is not necessary to run the fixture to use the requirements workflow.

### Verification recorded for this implementation

- All 12 automated tests passed on Python 3.13.3.
- Browser JavaScript syntax check passed with Node 25.8.0.
- Local browser inspection confirmed the rendered control plane, specialist registry, project creation without a repository, and unapproved empty requirements contract. A blank `First migration` project was created; no user requirements or approvals were invented.
- HTTP smoke checks returned 200 for the UI and project list, 404 for a missing project, and 403 for missing action credentials and an untrusted Host header.
- Full browser completion of all twelve answers, responsive device testing, real model calls and real application migration were not performed. Backend tests cover interview completion and approval invalidation.

## Before connecting real agents

Choose the provider and retention policy; implement output-schema validation and tool capability enforcement; configure isolated worker environments and egress; establish project identity and scoped credentials; bind approval to contract, source revision and environment; set execution/iteration/cost budgets; protect test artifacts from implementers; validate the adapter on non-sensitive inputs. Do not wire repository text directly into a shell executor.

## Deferred operational guarantees

No production deployment, distributed execution, background jobs, live notification delivery, authentication/tenant enforcement, real workload profiling, cross-project knowledge search, model execution or real application migration has been performed. The UI labels these boundaries explicitly. The roadmap defines the evidence needed to add them.
