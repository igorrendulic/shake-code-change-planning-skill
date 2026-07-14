# Canonical Plan Format

## Contents

1. [Document grammar](#document-grammar)
2. [Frontmatter](#frontmatter)
3. [Required sections](#required-sections)
4. [Repeated descriptors](#repeated-descriptors)
5. [Baseline and gates](#baseline-and-gates)
6. [Lifecycle](#lifecycle)
7. [Task-graph contract](#task-graph-contract)
8. [Validator](#validator)

## Document grammar

Use UTF-8 Markdown. Start with YAML frontmatter. Use each fixed H1 heading exactly once and in the specified order. Put every repeated success criterion, decision, and slice in its own fenced `yaml` mapping. Use conservative YAML: spaces for indentation, mappings, sequences, inline lists/maps, quoted or plain scalars, booleans, integers, and null. Avoid anchors, tags, and custom types.

Plan filenames are `.agent/plans/<plan-id>-v<plan_version>.md` unless repository instructions or the user specify another location. `plan_id` is stable kebab-case; versions are positive integers.

## Frontmatter

```yaml
---
schema_version: 1
plan_id: add-order-export
plan_version: 1
status: handoff-ready
artifact_mode: file
supersedes: null
superseded_by: null

primary_intent: capability-add
risk_modifiers: [public-contract]
scope: cross-module
uncertainty: medium
plan_depth: standard
depth_rationale: "Touches an existing cross-module flow with a reversible API addition."
handoff_target: task-graph

repository_state:
  vcs: git
  base_revision: "<git-sha>"
  working_tree: clean
  includes_uncommitted_evidence: false
  observed_changed_paths: []

unresolved_material_decisions: []

audits:
  decision_completeness:
    status: complete
    result: pass
    exceptions: []
  traceability:
    status: complete
    result: pass
    exceptions: []
  vertical_order:
    status: complete
    result: pass
    exceptions: []
  parallelization:
    status: complete
    result: pass
    exceptions: []
---
```

Allowed lifecycle states are `draft`, `decision-ready`, `handoff-ready`, and `superseded`. `artifact_mode` is `inline` or `file`. Use the primary intents from change-routes.md. Modifiers are additive risk labels from risk-overlays.md. Scope and uncertainty are concise categorical judgments; they are not validator-controlled enums.

For a non-Git directory use:

```yaml
repository_state:
  vcs: none
  base_revision: null
  working_tree: unavailable
  includes_uncommitted_evidence: false
  observed_changed_paths: []
```

For a dirty Git worktree use `working_tree: dirty`, set `includes_uncommitted_evidence` accurately, and list all observed relevant changed paths. This is a freshness warning, not a reproducible snapshot.

## Required sections

Use these headings in order:

1. `# Outcome` — stakeholder result, not implementation activity.
2. `# Success Criteria` — one descriptor per observable criterion.
3. `# Repository Evidence` — instruction files, confirmed paths/symbols, analogues, consumers, tests, commands, and uncertainty.
4. `# Current and Target Flow` — routed execution path before and after the change.
5. `# Decisions` — one descriptor for each material choice.
6. `# Scope` — included and excluded work plus boundaries.
7. `# Baseline` — executed checks or explicit deferral.
8. `# Implementation Slices` — vertically ordered descriptors.
9. `# Risk and Operational Gates` — declared modifier descriptors and cross-cutting gates.
10. `# Planning Audits` — audit conclusions and justified exceptions.
11. `# Pre-Handoff Discovery Log` — discoveries after initial investigation and whether they changed material assumptions.

## Repeated descriptors

### Success criterion

Use stable `SC-*` IDs. Every stakeholder-visible criterion has an observable outcome and reproducible verification.

```yaml
id: SC-001
outcome: "An authorized user can export completed orders as CSV."
verification: "The integration test produces a CSV containing the expected order rows."
```

### Decision

Use stable `DEC-*` IDs. Allowed dispositions are `resolved`, `out-of-scope`, and `decision-rule`.

```yaml
id: DEC-001
status: resolved
decision: "Generate exports synchronously within the existing request limit."
rationale: "Equivalent repository exports complete below the limit."
alternatives_rejected:
  - "Background export job"
```

A decision rule states the observable predicate and resulting choice. `unresolved_material_decisions` may refer to open decision IDs in drafts but must be empty at handoff.

### Implementation slice

Use globally stable `SLICE-*` and `AC-*` IDs.

```yaml
id: SLICE-001
type: ship
goal: "Export completed orders through the existing API."
success_criteria: [SC-001]
depends_on: []
scope:
  - "Add the export route and service behavior."
out_of_scope:
  - "Scheduled exports."
code_locations:
  - path: src/orders/routes.py
    symbol: export_orders
    evidence: proposed
contracts_changed:
  - "Additive authenticated HTTP endpoint."
acceptance_criteria:
  - id: AC-001
    statement: "Completed orders are returned as valid CSV."
    verification: "Run the targeted integration test."
test_commands:
  - "pytest tests/orders/test_export.py -v"
parallel:
  eligible: false
  reason: "This is the first end-to-end tracer slice."
rollout: "Release with the existing service deployment."
reversal: "Remove the additive route before external adoption."
```

`type` is `ship`, `prerequisite`, or `scout`. Code-location evidence is `confirmed`, `proposed`, or `candidate`. `confirmed` means inspection found that exact path/symbol. A proposed location is a selected future location. A candidate requires implementation-time localized confirmation without opening a material decision.

Every ship slice advances at least one success criterion, follows a production-shaped path, is independently verifiable, and leaves the repository compatible and buildable. A prerequisite names the vertical slice it rejoins in its goal, scope, or an optional `rejoins` field.

### Scout

A non-material scout may block already-defined slices. Set `material: false`, state its bounded question and acceptance evidence, and let dependent slices name it in `depends_on`.

A scout that could change architecture, scope, risk, or delivery structure is terminal. Do not define speculative downstream ship slices. Include:

```yaml
id: SLICE-001
type: scout
material: true
goal: "Determine whether the event store can enforce atomic deduplication."
success_criteria: [SC-001]
depends_on: []
falsifiable_question: "Can one atomic write enforce the idempotency key?"
timebox: "Four hours."
required_evidence: "A concurrency test against the production-shaped adapter."
success_threshold: "All duplicate writes collapse to one record."
failure_threshold: "Any duplicate record is observed."
decision_rule: "Use the store primitive on success; replan on failure."
replanning_condition: "The store cannot enforce atomic deduplication."
acceptance_criteria:
  - id: AC-001
    statement: "The scout records a reproducible conclusion."
    verification: "Run the probe and attach its output."
```

For `technical-spike`, the scout evidence and recommendation may satisfy the final stakeholder outcome.

## Baseline and gates

Record an executed baseline as structured YAML:

```yaml
commands:
  - command: "pytest tests/orders/test_export.py -v"
    result: pass
    existing_failures: []
    relevance: "Covers the nearest existing export flow."
```

If no baseline is safe or practical:

```yaml
not_run:
  reason: "The available command writes to the shared production queue."
  establishing_slice: SLICE-001
  regression_differentiation: "First capture the isolated adapter result, then compare all later slices to it."
```

Risk gates use one mapping keyed by declared modifier:

```yaml
modifiers:
  public-contract:
    consumers: [Web client, external API clients]
    compatibility: "The endpoint is additive; existing routes are unchanged."
    versioning_or_deprecation: "No version bump; removal requires the normal deprecation policy."
```

Read risk-overlays.md for every required field. The validator checks populated structure only; it cannot prove adequacy.

## Lifecycle

- `draft`: inspection, questions, and approach selection may modify any content.
- `decision-ready`: all known material decisions are resolved; slicing and audits may continue.
- `handoff-ready`: all handoff checks pass; implementation content is immutable.
- `superseded`: a replacement plan owns future work.

Material discoveries create `<plan-id>-v<N+1>.md`, increment `plan_version`, and set `supersedes` to the prior artifact. On the old artifact only change `status: superseded` and `superseded_by`. Unfinished drafts may instead be deleted.

Supersede for changes to stakeholder behavior/success, scope, contracts or persistent-data semantics, architecture or dependencies, risk classification, rollout, recovery, or reversal. Do not supersede for mechanical task decomposition, internal naming, or localized reversible implementation choices.

## Task-graph contract

The intended future command is: `I will update the task-graph to decompose .agent/plans/<plan>.md`.

The consumer must:

1. Require `status: handoff-ready` and a supported `schema_version`.
2. Parse or validate before decomposition.
3. Check repository-state freshness and re-inspect relevant paths on drift.
4. Convert slices into fresh-context tasks while preserving success criteria, scope, dependencies, acceptance criteria, and tests.
5. Avoid new product or architectural decisions and stop on material gaps.
6. Record this provenance in each task:

```yaml
source_plan: .agent/plans/add-order-export-v1.md
source_slice: SLICE-001
success_criteria: [SC-001]
```

Task decomposition does not modify the source plan.

## Validator

From the skill directory run:

```text
python scripts/validate-plan.py <plan>
python scripts/validate-plan.py <plan> --handoff
python scripts/validate-plan.py <plan> --handoff --json
```

Default validation checks parseability, lifecycle metadata, IDs, references, dependency cycles, repository metadata, location labels, and scout shape while allowing an incomplete draft. Handoff validation additionally requires handoff-ready status, no unresolved material decisions, complete decisions/audits, success traceability, acceptance verification, and declared modifier gates.

JSON output is a stable parsed summary for a task-graph consumer. Structural validation does not prove all decisions were discovered, architecture is correct, slices are semantically vertical, or risk analysis is adequate.
