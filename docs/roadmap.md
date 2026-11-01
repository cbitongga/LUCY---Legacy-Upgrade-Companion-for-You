# Phased implementation and acceptance criteria

> Standalone update: background requirements reviews, direct provider adapter, durable jobs and progress polling are now implemented. See [standalone.md](standalone.md) for current behavior and limitations. The original design and initial-slice descriptions below remain historical where they describe these features as future work.

## Current slice: agent definitions and requirements-first planning

Implemented: local control plane, specialist registry, explicit interview, persistent contract versions, provisional strategy comparison, human planning approvals and evidence scaffolding. Optional synthetic developer fixture validates mismatch/resource detection and remediation plumbing. A real sample application is deferred at the user's direction.

Acceptance checks: create a project without a repository; save and resume partial interviews; inspect role prompts and boundaries; complete the interview; compare two options; approve a plan bound to the displayed contract; edit a requirement and observe approval revocation; confirm migration cannot execute from planning approval. Automated tests cover these behaviors and the fixture checks. UI verification is recorded separately in the runbook.

## Milestone 1 — Migration intelligence

Remaining: connect a chosen model provider through the capability broker; select first supported stack; ingest a real repository with safe parser adapters; discover manifests/dependencies/entry points/schema/tests; distinguish user assertions from observed facts; link intake to the interview and avoid questions already answered by verified context. Add target-specific strategies with cited evidence. Define numeric acceptance thresholds and resolve unknowns before execution approval.

Acceptance: a real application produces a versioned intelligence report with reproducible facts; user approves a measurable contract and one feasible strategy; provider calls are budgeted and audited; no arbitrary repository instructions gain tool access.

## Milestone 2 — Closed-loop migration

Implement disposable workspaces, model-driven changes, protected test artifacts, independent verification identities, bounded task graph, pause/cancel/retry, reviewable diffs and source-revision-bound gates. Add real legacy/new harness adapters for output, errors, data and events. Keep final human acceptance separate.

Acceptance: migrate one user-supplied component, detect deliberately injected regressions with protected tests, remediate and independently revalidate, reproduce the evidence on fresh workers, and stop at budget or unresolved critical failures. Crash/retry cannot duplicate external effects.

## Milestone 3 — Runtime assurance

Implement one language's profiler integration, controlled workload artifacts, repeated performance measurements, resource cleanup checks and configurable soak schedules. Store raw samples and derived statistics separately.

Acceptance: distinguish warm-up/caching from a reproducible leak; detect a real memory regression; report RSS/native/heap coverage and profiler overhead; required duration cannot be satisfied by a short probe. Provide runtime comparison charts with run/revision/workload filters.

## Milestone 4 — Cloud resilience

Implement one supported nonproduction topology and scoped fault runner. Track replica count, aggregate connections, idempotency, job/message duplication, scaling and recovery. Require explicit environment/fault budgets and stop conditions.

Acceptance: single-instance success does not pass distributed gates; duplicate processing, instance loss and dependency disruption produce traceable results; cleanup is confirmed even on failure.

## Milestone 5 — Persistent engineering intelligence

Add knowledge versions, evidence-linked validation, contradictions, deduplication, correction, supersession/retraction and access-filtered retrieval. Require project-specific evidence before marking a reused pattern verified.

Acceptance: cross-project isolation tests pass; hypotheses cannot become verified without evidence; contradictory versions remain explainable; users can search and correct learnings; reuse benefit is measured rather than assumed.

## Milestone 6 — Forecasting and full control plane

Add task DAG/resource scheduling, historical duration cohorts, Monte Carlo completion intervals, critical-path frequency, conditional approval delays, forecast-change reasons, live telemetry, side-by-side runtime/behavior comparisons and meaningful notifications.

Acceptance: cold-start estimates remain explicitly uncertain; interval calibration is backtested; mandatory soak time appears on the wall-clock path; notifications occur only on meaningful changes and respect user preferences.

## Milestone 7 — Hardening

Introduce identity/RBAC, multi-tenant storage enforcement, encrypted artifacts, audited secret brokerage, hardened worker isolation, restricted egress, quotas, signed evidence, leased workers, backups/migrations, recovery drills and operational monitoring.

Acceptance: adversarial boundary tests prove blocked filesystem/network/credential access; tenant isolation holds; restored projects retain evidence links and approval state; deployment and recovery meet explicit objectives. No claim of production readiness until the relevant independent security and operational evidence exists.

## Deliverable map

Critical review, architecture, state machine, storage, differential/runtime/cloud/knowledge/forecast/control-plane/security designs: `architecture.md`. Agent topology, prompts and tools: `agents-and-tools.md` plus executable registry. Backlog and milestone acceptance: this file. Working local slice: `lucy/`. Tests: `tests/`. Developer instructions: `README.md`. Operations: `runbook.md`. These design documents do not imply future modules are implemented.
