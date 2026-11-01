# Agent prompts, tools and permission model

The executable source of truth is `lucy/agents.py`. The control plane exposes all definitions and full prompts. There are seventeen roles from the original specification plus a Requirements Interviewer, which is useful before any application is supplied. Each project records its registry assignments. Specialists are definitions, not live model processes.

## Common prompt contract

Every role receives its objective, approved project/contract version, allowed capabilities, relevant immutable evidence and remaining budget. Repository text, retrieved knowledge and tool output are untrusted data. Output must separate verified/inferred/unknown claims, list evidence references, propose actions with capability/arguments/version, disclose risks and identify approval needs. Instructions cannot grant permissions. The broker must reject unlisted actions even when the model requests them.

## Topology

The orchestrator schedules work; specialists communicate through tasks, artifacts and findings rather than free-form broadcasts. Interviewer and architect participate in planning; intelligence activates after repository intake. Implementation and remediation may write only isolated workspaces. Test engineering owns tests; differential verification compares runs; critic challenges results; guardian evaluates gates. Assurance aggregates evidence without overriding gates. Runtime, stability, cloud and adversarial roles are activated by the contract's risk profile. Knowledge, forecasting and observability consume project events.

No implementation/remediation role may certify its own work. A verifier cannot modify the candidate or its expected results. Current fixture checks enforce distinct actor labels but do not establish independent credentials; production must enforce identity and write boundaries outside prompts.

## Implemented tool contracts

| Operation | Inputs | Result | Boundary |
|---|---|---|---|
| Start interview | Project name, 1–120 characters | Persistent project with role assignments | No repository required |
| Save requirements | Allowlisted question IDs and string answers ≤5,000 characters | New contract version; approval revoked | User-supplied assertions only |
| Propose strategies | Completed interview | Two provisional rule-based options | No factual feasibility claim |
| Approve plan | Strategy ID and current contract hash | Local operator planning approval | No code execution grant |
| Inspect repository | Explicit CLI directory | Bounded metadata facts/inferences/unknowns | No source execution, symlink traversal, or secret content ingestion |
| Fixture worker | Bundled fixed source and controlled workspace | Scenario outputs and allocation samples | Trusted fixture only; 10-second timeout |
| Guardian | Named gate results | Blocked / Incomplete / Needs Review / Accepted | Missing mandatory gate fails closed |
| Read evidence | Existing project ID | Artifact content and SHA-256 | Single local operator; no tenant isolation |

Other capability names in the registry are design contracts only. There is no generic dispatcher that executes them, so an unconfigured role cannot acquire shell or cloud access.

## Future model adapter boundary

Implement an `AgentProvider.run(role, approved_context, output_schema, budget)` adapter behind the capability broker. Require structured output validation; reject missing evidence links, unknown capabilities, stale contracts and budget excess. Record model identifier/version, prompt/template hashes, redacted tool input/output, usage and stop reason. Model output is a proposal, never a direct tool invocation. Configure credentials in a secret broker or environment at process startup; do not send credentials to the browser or persist them in project JSON.

A provider has deliberately not been selected or connected. This avoids assuming a vendor, sending proprietary data, or claiming live autonomous agents before execution policy and isolation exist.

## API

GET `/api/session` returns the local action token, roles and questionnaire. GET `/api/projects` lists projects; GET `/api/projects/{id}` returns detail and evidence. All POST calls require the same-origin `X-Lucy-Token` header.

- POST `/api/projects`: `{name}`
- POST `/api/projects/{id}/interview`: `{answers: {question_id: text}}`
- POST `/api/projects/{id}/strategy`: `{strategy, contract_hash}`
- Optional fixture: POST `/api/demo`, then project `/approve`, `/step`, `/pause`, `/resume`, `/cancel`, `/retry`.

The server is loopback-only and single-threaded. Tokens protect browser-origin mutations, not access by other local processes. External authentication and authorization are future milestones.
