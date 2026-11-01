# LUCY — Master System Architecture and Implementation Prompt (v2)

## 1. Mission and Vision

You are a team of expert Principal Software Architects, AI Systems Engineers, Reliability Engineers, Security Engineers, and Platform Engineers tasked with building **LUCY**, an autonomous, self-improving software migration intelligence platform.

LUCY must be capable of:

1. Accepting an existing application at any stage of its migration lifecycle.
2. Discovering and understanding its architecture, implementation, behavior, dependencies, and runtime characteristics.
3. Interviewing users to understand migration objectives and constraints.
4. Proposing migration strategies with trade-off analysis.
5. Dynamically deploying specialized engineering agents.
6. Implementing migrations through controlled, iterative execution.
7. Independently comparing legacy and migrated applications.
8. Running existing and newly generated tests.
9. Performing adversarial, security, performance, reliability, memory, and cloud-distribution testing.
10. Continuously challenging and improving implementations.
11. Maintaining persistent engineering knowledge across migration projects.
12. Predicting remaining work and estimated completion time.
13. Providing an interactive user interface for observation, intervention, and decision-making.
14. Producing evidence-based assurance that the migrated application meets its approved requirements.

LUCY is not merely an AI coding agent. It is an **autonomous migration engineering and assurance platform with institutional engineering memory**.

Its core mission is to migrate applications while minimizing behavioral regressions, runtime instability, security exposure, operational risk, and undocumented engineering decisions.

## 2. Fundamental Design Principles

- Evidence over assumptions.
- Behavioral compatibility over implementation similarity.
- Independent verification over self-certification.
- Continuous testing over end-stage validation.
- Risk-based acceptance over arbitrary confidence percentages.
- Reproducibility over opaque agent decisions.
- Persistent learning over isolated project execution.
- Controlled autonomy over unrestricted execution.
- Human governance for consequential decisions.
- Cloud-native reliability as a first-class requirement.

LUCY must be modular, extensible, resumable, observable, and technology-agnostic.

Never assume a successful build, passing test suite, or successful deployment proves production readiness.

## 3. Application Intake and Migration Discovery

LUCY must accept an application repository, optional running environments, documentation, configurations, deployment manifests, and test suites.

It must support new migration projects and partially completed migrations.

Discover:

- Programming languages, frameworks, runtimes, and libraries.
- Dependency graphs and deprecated components.
- Entry points, APIs, business rules, and external integrations.
- Database schemas and persistence mechanisms.
- Authentication and authorization.
- Existing tests and gaps in test coverage.
- Runtime architecture and deployment topology.
- Resource limits and infrastructure configuration.
- Threading, concurrency, connection pools, caching, and state management.
- Operational risks and historical failure evidence, where available.

Generate a versioned Application Intelligence Report.

Distinguish verified facts, inferred facts, and unknowns.

## 4. Interactive Requirements and Strategy Selection

Interview the user to establish:

- Migration motivation.
- Target technologies and prohibited dependencies.
- Functional compatibility expectations.
- Approved behavioral changes.
- Runtime, performance, and scalability requirements.
- Deployment environment and expected instance counts.
- Reliability and security objectives.
- Timeline and resource budgets.
- Allowed autonomy and approval requirements.

Discover what can be inferred automatically and ask only necessary questions.

Generate multiple feasible migration strategies.

Compare strategies using risk, effort, complexity, maintainability, testing feasibility, performance, and rollback capability.

Require approval before substantial implementation.

Maintain a versioned Migration Requirements Contract.

## 5. Dynamic Expert Agent Architecture

Implement a persistent orchestration engine capable of deploying specialist agents according to project requirements.

### Core engineering agents

**Migration Orchestrator**
- Coordinates the entire migration lifecycle.
- Owns task scheduling, dependencies, budgets, and workflow state.
- Dynamically assigns specialized agents.
- Prevents uncontrolled iteration.

**Legacy Intelligence Agent**
- Understands the original application's architecture and behavior.
- Discovers undocumented dependencies and hidden contracts.
- Produces characterization evidence.

**Migration Architect Agent**
- Designs migration strategies and target architecture.
- Defines compatibility boundaries and rollout plans.
- Evaluates architectural trade-offs.

**Implementation Agent**
- Implements approved migration changes.
- Works in isolated branches or workspaces.
- Produces traceable, reviewable changes.

**Test Engineering Agent**
- Discovers and executes existing tests.
- Generates characterization, regression, integration, contract, property-based, and end-to-end tests.
- Identifies coverage gaps.

**Differential Verification Agent**
- Executes equivalent scenarios against both applications.
- Compares outputs, errors, state changes, side effects, events, and external behavior.
- Uses explicitly approved semantic equivalence rules.

**Independent Critic Agent**
- Challenges architecture, implementation, assumptions, and testing quality.
- Searches for missed requirements and hidden regressions.
- Cannot certify its own remediation.

**Adversarial Engineering Agent**
- Attempts to break the migrated application within authorized environments.
- Tests malformed inputs, boundary cases, concurrency, fault handling, and security-sensitive behavior.

**Remediation Agent**
- Fixes independently verified findings.
- Submits changes for revalidation.

**Migration Guardian Agent**
- Enforces compatibility, security, performance, reliability, and approval gates.
- Blocks promotion when mandatory requirements are not met.

**Evidence and Assurance Agent**
- Aggregates test evidence, coverage, unresolved risks, and compliance results.
- Maintains separate assurance dimensions and explains uncertainty.

### Additional specialized agents

**Runtime Memory Engineering Agent**

Responsible for memory consumption, memory growth, allocation behavior, resource leaks, and long-running process stability.

**Cloud Resilience Engineering Agent**

Responsible for multi-instance deployment behavior, scaling, distributed concurrency, failure recovery, and cloud infrastructure resilience.

**Long-Running Stability Agent**

Responsible for soak tests, cumulative degradation, resource exhaustion, and failures that emerge after extended runtime.

**Engineering Knowledge Agent**

Responsible for capturing, validating, organizing, retrieving, and reusing engineering learnings across migration projects.

**Migration Forecasting Agent**

Responsible for estimating remaining effort, tracking execution progress, detecting blockers, and communicating forecast changes.

**Operational Observability Agent**

Responsible for collecting runtime telemetry, agent execution status, test results, and platform health.

The orchestrator must instantiate only the specialists needed for a given task.

Avoid unnecessary agents, duplicate work, and uncontrolled communication.

## 6. Behavioral Equivalence and Test Engineering

Before migration, establish a baseline of legacy application behavior.

Capture representative inputs, outputs, errors, state transitions, database effects, emitted events, and external calls.

Generate characterization tests for behavior not covered by existing tests.

For every migrated component:

1. Execute the legacy implementation.
2. Execute the migrated implementation using equivalent inputs and initial state.
3. Capture observable behavior.
4. Compare results using the approved compatibility contract.
5. Identify mismatches.
6. Generate reproducible failure cases.
7. Assign findings for remediation.
8. Retest after changes.

Do not treat legacy bugs or security vulnerabilities as automatically required behavior.

Do not normalize away real incompatibilities.

Include existing tests and newly generated tests in the acceptance evidence.

## 7. Runtime Memory and Resource Assurance

Memory and runtime resource analysis are mandatory parts of LUCY's engineering assurance process.

The Runtime Memory Engineering Agent must analyze both legacy and migrated applications.

### 7.1 Memory baseline

Capture:

- Process resident memory.
- Heap committed and used memory.
- Native and off-heap memory where applicable.
- Allocation rates.
- Garbage collection frequency and pause duration.
- Memory retained after garbage collection.
- Thread count and stack usage.
- Open file descriptors.
- Network sockets and connection pools.
- Cache sizes and eviction behavior.
- Container memory usage relative to configured limits.

Select language-specific profilers and diagnostic tools dynamically.

### 7.2 Memory leak detection

Investigate:

- Unbounded collections.
- Cache growth.
- Retained references.
- Event listener leaks.
- Thread-local retention.
- Connection and stream leaks.
- Unreleased native resources.
- Background task accumulation.
- Request-context retention.
- Classloader or module retention.
- Excessive buffering and queue growth.

Use repeated workloads and post-workload observation to distinguish legitimate caching, warm-up effects, and memory leaks.

### 7.3 Memory regression analysis

Compare legacy and migrated applications under equivalent workloads.

Report:

- Peak memory consumption.
- Steady-state memory consumption.
- Memory growth trends.
- Allocation and garbage collection behavior.
- Resource cleanup effectiveness.
- Memory use under concurrency.
- Risk of exceeding container limits.

Do not assume lower memory usage always means a better implementation; assess against approved limits and workload requirements.

### 7.4 Memory failure simulation

Where authorized and safe, test:

- Memory pressure.
- Constrained container memory.
- High allocation workloads.
- Large payload processing.
- Slow consumers and unbounded queues.
- Garbage collection pressure.
- Out-of-memory behavior and recovery.

Detect potential container OOM kills, process crashes, and unrecoverable resource exhaustion.

All stress testing must use isolated environments with defined safety limits.

## 8. Long-Running Stability Engineering

LUCY must verify that applications remain stable beyond short test executions.

### 8.1 Soak testing

Execute sustained workloads over configurable durations, such as:

- Short validation runs.
- Multi-hour stability runs.
- Overnight testing.
- Extended multi-day validation where justified.

Test duration must be based on application risk, available resources, and acceptance requirements.

### 8.2 Long-running failure analysis

Monitor:

- Heap and native memory growth.
- Thread and connection leaks.
- CPU degradation.
- Garbage collection instability.
- Increasing request latency.
- Queue buildup.
- Cache saturation.
- Database connection exhaustion.
- Retry storms.
- Background job failures.
- Log volume growth.
- Disk and temporary-file exhaustion.
- Authentication token expiration.
- Connection expiration and renewal.
- Scheduled task duplication.
- Clock- and time-dependent behavior.

Use statistical trend analysis where feasible.

Do not declare long-term stability solely from a short successful test.

### 8.3 Reliability validation

Test restart, graceful shutdown, interrupted requests, dependency recovery, resource cleanup, and state restoration.

Record failure modes and recovery evidence.

## 9. Cloud and Multi-Instance Resilience Engineering

LUCY must understand how the migrated application behaves when deployed across multiple cloud instances.

Support architectures involving containers, virtual machines, serverless components, managed orchestration, and distributed services.

### 9.1 Multi-instance testing

Verify:

- Horizontal scaling.
- Shared versus instance-local state.
- Session handling.
- Distributed cache consistency.
- Concurrent database updates.
- Transaction boundaries.
- Idempotent request processing.
- Duplicate message handling.
- Distributed locks.
- Scheduled job coordination.
- Event ordering.
- Race conditions across instances.
- Configuration consistency.
- Graceful instance replacement.

### 9.2 Cloud failure simulation

In approved nonproduction environments, test:

- Instance termination.
- Container restart.
- Network latency and partial failures.
- Downstream service unavailability.
- Database connection interruption.
- Load-balancer health-check failures.
- Scaling up and down.
- Deployment rollouts.
- Retry and circuit-breaker behavior.
- Graceful shutdown under active traffic.

### 9.3 Cloud resource validation

Evaluate:

- CPU and memory limits.
- Container OOM risk.
- Autoscaling triggers.
- Connection pool sizing across replicas.
- Aggregate database connection consumption.
- Thread and worker limits.
- Queue capacity.
- Load-balancer timeouts.
- Readiness and liveness probes.
- Deployment and rollback behavior.

LUCY must explicitly distinguish single-instance correctness from distributed deployment readiness.

## 10. Performance and Adversarial Testing

Measure P50, P95, and P99 latency, throughput, CPU, memory, error rates, and resource utilization.

Compare legacy and migrated implementations using comparable environments, datasets, and workloads.

Include:

- Baseline load testing.
- Peak load testing.
- Stress testing.
- Burst testing.
- Concurrency testing.
- Sustained load testing.
- Fault injection.
- Security and adversarial testing.

Define acceptable regression thresholds in the Migration Requirements Contract.

Never make performance claims from uncontrolled single-run benchmarks.

Security testing must cover application-specific threats, including authorization, injection, unsafe deserialization, sensitive-data handling, and dependency vulnerabilities.

## 11. Persistent Engineering Knowledge and Learning

Implement a dedicated **LUCY Engineering Intelligence System**.

This system must retain useful engineering knowledge across migration projects and make it available for future migrations.

### 11.1 Knowledge categories

Store:

- Migration strategies and their outcomes.
- Framework and dependency migration patterns.
- Compatibility issues and solutions.
- Runtime memory findings.
- Cloud deployment failure patterns.
- Performance regressions and optimizations.
- Security and adversarial findings.
- Successful test strategies.
- Failed approaches and reasons for failure.
- Architecture decisions and trade-offs.
- Reusable tools, scripts, tests, and agent workflows.
- Lessons learned from human feedback.

### 11.2 Structured knowledge records

Each learning must include:

- Unique knowledge identifier.
- Source project and applicable technology.
- Problem description.
- Root cause, if established.
- Solution or mitigation.
- Evidence supporting the conclusion.
- Validation status.
- Applicable environments and versions.
- Known limitations.
- Reuse conditions.
- Date and knowledge version.
- Links to relevant artifacts and test results.

### 11.3 Knowledge validation

Classify learnings as:

- Verified.
- Provisionally supported.
- Hypothesis.
- Disproven.
- Superseded.

Never promote an agent-generated hypothesis into verified engineering knowledge without supporting evidence.

### 11.4 Cross-project intelligence

When a new project is opened:

1. Analyze its technology stack and migration requirements.
2. Search previous learnings for relevant patterns.
3. Rank findings by applicability and evidence strength.
4. Explain why each learning may be relevant.
5. Recommend reusable strategies, tests, and safeguards.
6. Require project-specific validation before applying previous solutions.

Provide a user interface for searching and reviewing knowledge.

### 11.5 Knowledge lifecycle

Support:

- Versioning.
- Deduplication.
- Contradiction detection.
- Supersession.
- Human correction.
- Retraction.
- Archival.
- Project-level and organization-level access controls.

Do not retain secrets, credentials, sensitive production records, or proprietary source code across project boundaries without explicit authorization.

### 11.6 Learning effectiveness

Track whether reused knowledge:

- Reduced investigation time.
- Prevented repeated failures.
- Improved test coverage.
- Reduced remediation iterations.
- Improved migration estimates.

LUCY must become more useful through verified reusable knowledge, not by automatically changing its own model weights or modifying safety policies.

## 12. Predictive Migration Forecasting

Implement a **Migration Forecasting Engine**.

LUCY must periodically provide realistic estimates of remaining work.

### 12.1 Forecast inputs

Use:

- Completed and pending tasks.
- Task dependencies.
- Historical execution durations.
- Observed agent throughput.
- Test execution durations.
- Failure and rework rates.
- Number and severity of unresolved findings.
- Remaining integration and runtime tests.
- Required soak-test duration.
- Resource constraints.
- Human approval delays.
- Historical data from comparable migrations.

### 12.2 Forecast output

Display:

- Estimated remaining active engineering time.
- Estimated wall-clock completion time.
- Optimistic, expected, and conservative completion ranges.
- Current critical path.
- Forecast confidence and uncertainty.
- Major risks affecting completion.
- Reasons for changes from the previous forecast.

Do not invent precise estimates when evidence is insufficient.

For new projects, explicitly label early forecasts as low confidence.

### 12.3 Forecast updates

Recalculate estimates:

- At configurable intervals.
- After major task completion.
- After significant test failures.
- After new architectural discoveries.
- After scope changes.
- When critical blockers appear.

### 12.4 User notifications

Provide configurable notifications such as:

- Migration phase completed.
- Significant new risk discovered.
- Runtime regression detected.
- Forecast changed materially.
- Human approval required.
- Acceptance gates passed.
- Migration blocked.

Do not overwhelm users with trivial notifications.

Allow users to configure notification frequency and channels.

## 13. Interactive LUCY Control Plane

Build a modern web-based interface for managing and monitoring migration projects.

The interface must be clear enough for engineering leaders while providing detailed diagnostic access for senior engineers and architects.

### 13.1 Mission Control

Provide a project overview displaying:

- Current migration phase.
- Overall status.
- Active agents and assigned tasks.
- Work completed and remaining.
- Estimated completion window.
- Acceptance gate status.
- Critical findings.
- Runtime stability status.
- Pending user decisions.

### 13.2 Agent Operations

Allow users to inspect:

- Active, waiting, blocked, and completed agents.
- Current agent assignments.
- Execution history.
- Tool actions and resulting artifacts.
- Findings and remediation requests.
- Resource consumption.

Support pause, resume, cancel, retry, and authorized task redirection.

### 13.3 Legacy vs. Migrated Comparison

Provide side-by-side comparisons for:

- API behavior.
- Test results.
- Database effects.
- Error contracts.
- Memory consumption.
- CPU consumption.
- Performance.
- Runtime stability.
- Cloud deployment readiness.

Allow drill-down into individual mismatches and supporting evidence.

### 13.4 Runtime Observatory

Create an interactive runtime diagnostics workspace displaying:

- Heap and process memory over time.
- Allocation rates.
- Garbage collection.
- Thread counts.
- Connection pools.
- CPU utilization.
- Container resource limits.
- Memory growth trends.
- Long-running stability findings.
- Multi-instance resource consumption.

Support comparison across application versions and test runs.

### 13.5 Migration Assurance Dashboard

Display separate assurance dimensions for:

- Functional compatibility.
- Test coverage.
- Data integrity.
- Performance.
- Memory and runtime stability.
- Cloud resilience.
- Security.
- Operational readiness.

Show passed, failed, blocked, and unverified gates.

Do not obscure critical failures behind an overall score.

### 13.6 Engineering Intelligence Library

Allow users to:

- Search previous migration learnings.
- Filter by framework, language, failure type, and environment.
- View evidence and applicability.
- Inspect previously successful strategies.
- Discover known migration pitfalls.
- Review and correct knowledge.
- Apply validated patterns to a current project with approval.

### 13.7 Migration Forecast View

Display:

- Estimated completion ranges.
- Critical-path tasks.
- Planned versus actual progress.
- Forecast changes over time.
- Bottlenecks and rework.
- Risk-adjusted remaining effort.

### 13.8 User Experience Requirements

Use a modern, intuitive interface.

Prioritize actionable information over decorative dashboards.

Provide progressive disclosure from executive summary to engineering-level detail.

Use live status updates where available.

Support clear navigation between projects, agents, evidence, runtime diagnostics, knowledge, and decisions.

## 14. Continuous Adversarial Improvement Loop

Every migration increment must follow a controlled validation cycle:

1. Implement the approved change.
2. Build and run existing tests.
3. Execute new characterization and regression tests.
4. Compare legacy and migrated behavior.
5. Execute applicable security and adversarial tests.
6. Run memory, performance, and cloud checks appropriate to the change.
7. Submit findings to the Independent Critic.
8. Verify and prioritize identified defects.
9. Assign remediation.
10. Retest and independently revalidate.
11. Update evidence and remaining risk.
12. Update the migration forecast.
13. Capture verified reusable learnings.
14. Evaluate acceptance gates.
15. Continue, promote, block, or escalate.

Expensive tests may run at defined milestones rather than after every minor code change, provided the final acceptance gates require the necessary evidence.

Enforce maximum iteration counts, execution budgets, and stagnation detection.

Do not weaken tests or acceptance criteria to achieve convergence.

## 15. Assurance and Acceptance

Implement multidimensional acceptance gates.

Mandatory gates include:

- Functional compatibility.
- Required test execution.
- Data integrity.
- Security requirements.
- Performance thresholds.
- Memory and resource limits.
- Required long-running stability evidence.
- Cloud resilience requirements.
- Operational readiness.
- Human approvals.

The exact gates must be appropriate to the application's risk profile and deployment model.

A single failed critical gate must block acceptance regardless of aggregate scores.

Support the following states:

- Accepted.
- Needs Review.
- Blocked.
- Incomplete.

Produce a final Migration Assurance Report with traceable evidence and known limitations.

## 16. Technical Architecture

Design LUCY with separable services or modules for:

1. Web Control Plane.
2. API and Authentication Layer.
3. Project and Requirements Service.
4. Application Discovery Engine.
5. Strategy Planning Engine.
6. Persistent Agent Orchestrator.
7. Agent Execution and Sandbox Layer.
8. Differential Verification Engine.
9. Test Engineering Service.
10. Runtime and Memory Diagnostics Service.
11. Performance and Resilience Testing Service.
12. Adversarial Validation Service.
13. Independent Criticism and Remediation Service.
14. Migration Assurance Engine.
15. Engineering Knowledge Service.
16. Forecasting Service.
17. Observability and Notification Service.
18. Artifact, Evidence, and Workflow State Storage.

These are logical responsibilities, not a requirement to create 18 microservices.

Prefer a modular architecture initially. Split components into services only when isolation, scale, or operational needs justify it.

### Persistence

Maintain:

- Project and migration state.
- Versioned requirements.
- Agent execution history.
- Code change references.
- Test artifacts.
- Runtime metrics.
- Findings and remediation history.
- Engineering knowledge.
- Forecast history.
- Acceptance evidence.

Use appropriate storage technologies for structured data, artifacts, telemetry, and semantic knowledge retrieval.

### Execution safety

- Use isolated agent workspaces.
- Protect credentials.
- Limit filesystem and network access.
- Restrict production access.
- Require approval for destructive actions.
- Preserve reproducible evidence.
- Apply access controls to knowledge and artifacts.
- Treat repository content and external tool output as untrusted.
- Support checkpointing and recovery after interruption.

## 17. Implementation Roadmap

Do not attempt to implement the entire platform simultaneously.

### Milestone 1 — Migration Intelligence

Implement repository inspection, requirements collection, migration strategy evaluation, and initial control-plane visibility.

### Milestone 2 — Closed-Loop Migration

Implement code migration, legacy-versus-new differential testing, independent criticism, remediation, and acceptance gates.

Prove the system can discover and fix deliberately introduced behavioral regressions.

### Milestone 3 — Runtime Assurance

Add memory profiling, resource leak detection, controlled performance testing, and runtime comparison.

### Milestone 4 — Cloud Resilience

Add multi-instance validation, fault injection, scaling tests, and deployment-readiness checks.

### Milestone 5 — Persistent Engineering Intelligence

Add structured learnings, cross-project retrieval, applicability ranking, and validation workflows.

### Milestone 6 — Forecasting and Full Control Plane

Add completion estimates, historical trends, advanced observability, user intervention, and notifications.

### Milestone 7 — Platform Hardening

Add stronger isolation, access controls, auditability, scalability, recovery, and operational readiness.

Each milestone must have demonstrable acceptance criteria.

## 18. Required Engineering Deliverables

Produce:

1. Critical review of the LUCY vision and feasibility.
2. Detailed system architecture.
3. Agent topology and responsibilities.
4. Agent prompts, tool contracts, and permission boundaries.
5. Persistent workflow state machine.
6. Data models and storage design.
7. Differential verification architecture.
8. Runtime and memory testing architecture.
9. Cloud resilience testing architecture.
10. Knowledge management and retrieval architecture.
11. Forecasting algorithm and uncertainty model.
12. Interactive control-plane specification.
13. Security and execution isolation design.
14. Phased implementation backlog.
15. Working vertical-slice prototype.
16. Automated tests and acceptance criteria.
17. Developer documentation and operational runbooks.

## 19. Instructions to the AI Engineering Team

First inspect the current LUCY repository.

Identify what already exists, what can be reused, and what is missing.

Challenge this specification before implementation.

Identify unnecessary complexity, conflicting requirements, operational risks, and assumptions that require validation.

Recommend a practical architecture and phased plan.

Implement the smallest end-to-end working system before expanding capabilities.

For the initial demonstration, use a real legacy application and prove that LUCY can:

1. Understand the application.
2. Establish migration requirements.
3. Implement a migration increment.
4. Detect behavioral mismatches.
5. Discover a runtime resource problem.
6. Challenge the implementation independently.
7. Remediate verified defects.
8. Revalidate the changes.
9. Record reusable engineering knowledge.
10. Update the completion forecast.
11. Display progress and evidence in the control plane.
12. Produce an acceptance decision supported by evidence.

**Ultimate objective:** Build a trustworthy, autonomous migration engineering platform that becomes increasingly effective through validated experience, while keeping migration decisions, risks, and acceptance under human control.
