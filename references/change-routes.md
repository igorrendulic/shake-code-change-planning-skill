# Change Routes

Select one primary intent and add modifiers separately. Use repository evidence to tailor the generalized route; do not force every node into every system.

## Primary intents

| Intent | Investigation emphasis | Planning emphasis |
|---|---|---|
| `greenfield-system` | Intended users, host constraints, adjacent systems, deployment conventions | First walking skeleton, architecture decisions, operational bootstrap |
| `capability-add` | Existing entry point, nearest analogue, consumers, extension seams | End-to-end additive behavior and compatibility |
| `behavior-change` | Current contract, callers, tests encoding old behavior | Explicit old-to-new semantics, transition and communication |
| `defect-correction` | Reproduction, failing path, invariant, blast radius | Characterization first when needed, root-cause fix, regression proof |
| `refactor` | Current responsibilities, dependency graph, behavior-preserving tests | Seam creation and incremental migration with unchanged behavior |
| `migration` | Source/target semantics, data or traffic ownership, mixed-version states | Compatibility window, sequencing, backfill/cutover, recovery |
| `quality-improvement` | Measured quality gap, affected workflow, existing signals | Target metric, bounded intervention, before/after verification |
| `operational-change` | Deployment/runtime path, operators, alerts, failure modes | Safe exposure, observability, runbook and reversal |
| `retirement` | Consumers, usage evidence, retained data/contracts | Deprecation, drain, removal, cleanup and proof of absence |
| `verification` | Claim under test, representative environment, current evidence | Reproducible evidence and explicit pass/fail thresholds |
| `technical-spike` | Falsifiable uncertainty, cheapest representative experiment | Timebox, evidence, thresholds, decision rule, replanning condition |

## Route adaptations

### API or interactive application

User/event → transport or UI boundary → input/auth validation → handler/controller → domain behavior → storage/dependency → response/render → logs, metrics, analytics.

### Library or SDK

Caller → public API → argument interpretation → coordinator → core algorithm → platform/dependency → return/error/event → tests and compatibility signals.

### Event-driven system

Producer stimulus → topic/queue boundary → schema/auth validation → consumer orchestration → domain transformation → state/downstream dependency → ack/event → lag, retry and dead-letter observation.

### Batch job or data pipeline

Schedule/input → ingestion boundary → schema/quality checks → stage orchestration → transformation → checkpoint/store → output publication → freshness, quality and cost signals.

### Infrastructure or operations

Change trigger → config/control-plane boundary → policy validation → rollout controller → runtime effect → managed resource → exposed service/state → health, drift and audit signals.

### Greenfield

Use intended paths as proposed evidence. Route one thin production-shaped walking skeleton through boundary, core behavior, dependency, emission, and observation before broader capability slices.

## Horizontal exceptions

Allow a non-vertical prerequisite only for characterization, a bounded PoC, additive compatibility, release-safety infrastructure, or a seam-establishing refactor. State which vertical slice it rejoins and why the exception is necessary. Do not split layers merely to manufacture parallel work.
