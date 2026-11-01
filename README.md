# LUCY

Local, requirements-first foundation for an evidence-based migration platform. No application or migration demonstration is needed to start.

## Start

Requires Python 3.11+; uses only the standard library.

```sh
python3 -m lucy serve
```

Open http://127.0.0.1:8765. Create a project, complete the requirements interview, inspect specialist definitions, and review a provisional strategy. State persists in `.lucy/lucy.sqlite3`. Stop with Ctrl-C; restart with the same data directory to continue.

```sh
python3 -m unittest discover -s tests -v
python3 -m lucy inspect /absolute/path/to/application
```

The inspection command reads filenames and metadata only, never executes repository code, skips hidden directories and symlinks, and reports unknowns explicitly.

## Available now

- Eighteen specialist definitions with prompts, activation conditions, output contracts, capabilities, and denied actions.
- Twelve-question interview; partial answers saved across restarts; immutable contract versions.
- Two rule-based, provisional strategy options covering risk, effort, complexity, maintainability, testability, performance, and rollback.
- Human planning approval bound to a contract hash; requirement edits revoke approval.
- Local web control plane for projects, interviews, agents, strategies, gates, evidence, and knowledge.
- Transactional project checkpoints, event history, hashed artifacts, fail-closed acceptance and explicitly unestimated forecasts.

**Not implemented:** live model agents, general-purpose code migration, repository sandboxing, production access, organization authentication, distributed scheduling, real application profiling, soak/cloud/security testing, or cross-project knowledge retrieval. Registered agents are not running AI models. Planning approval never starts migration. Unknown answers can support planning but cannot establish executable acceptance criteria.

## Optional developer fixture

The synthetic invoice application tests the evidence plumbing. It is not a real customer application and does not meet the original requirement for a real migration demonstration. It is deliberately absent from the main onboarding flow.

```sh
python3 -m lucy --data /tmp/lucy-fixture demo --approve-demo
```

This explicitly approves a bounded fixture: baseline, seeded faulty refactor, comparison, critic, deterministic repair, separate verification, scoped learning and report. It finds a rounding mismatch and retained allocation growth. The final decision remains **Incomplete**, because security, data integrity, performance, soak, cloud, operations and final human acceptance have no evidence. The test suite exercises this fixture in temporary directories.

## Documentation

- [Architecture and critical review](docs/architecture.md)
- [Agent and tool contracts](docs/agents-and-tools.md)
- [Milestones and acceptance criteria](docs/roadmap.md)
- [Operational runbook](docs/runbook.md)
- [Original specification](docs/original-request.md)

This is a single-user localhost prototype. Do not bind it to a public interface or route untrusted source code to the fixture executor. Process separation is not a security sandbox. See the architecture for the production isolation boundary.
