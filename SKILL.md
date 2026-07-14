---
name: shape-code-change
description: Classify, investigate, and shape requested software changes into decision-complete, code-routed implementation plans. Use when the user asks to plan, design, scope, investigate, or prepare implementation work for greenfield systems, features, behavior changes, defects, refactors, migrations, quality improvements, operational changes, retirements, verification work, or technical spikes—especially when repository evidence, approach selection, risk analysis, vertical sequencing, or task-graph handoff is needed. Do not use to implement changes, explain code without planning, create task-graph task files, or track implementation progress.
---

# Shape Code Change

Produce a planning artifact only. Do not edit implementation code, create task files, or track execution.

## Workflow

1. Establish the stakeholder outcome, constraints, and observable success criteria.
2. Classify the primary intent, modifiers, scope, uncertainty, and depth. Read [change-routes.md](references/change-routes.md) for the selected intent. Read [risk-overlays.md](references/risk-overlays.md) only for applicable modifiers.
3. Inspect repository instructions, relevant entry points and flow, analogous implementations, consumers, tests, and runnable commands. Label proposed paths and symbols as `proposed` or `candidate`, never `confirmed`.
4. Run the smallest safe, non-destructive, meaningful pre-change baseline when practical. Record the command, result, existing failures, and relevance. Otherwise record why, the slice that establishes it, and how later checks separate regressions.
5. Route the current or intended path as `stimulus → boundary → validation/interpretation → orchestration → core transformation → state/dependency → emission → observation`, adapting it to the system.
6. Identify material decisions and resolve prerequisites first. Compare only genuinely different approaches and select a direction.
7. Define coherent, independently verifiable delivery slices before considering parallelism. Each ship delivery slice must traverse a production-shaped path, advance a success criterion, and leave the repository compatible and buildable.
8. Apply modifier gates, then use [planning-audits.md](references/planning-audits.md) to audit decision completeness, traceability, vertical order, and parallelization.
9. Render the exact grammar in [plan-format.md](references/plan-format.md), then run `python scripts/validate-plan.py <plan>` and `python scripts/validate-plan.py <plan> --handoff` before declaring handoff readiness.

## Select Depth

- `micro`: local scope, low uncertainty, no material modifier, one observable outcome. Inspect the entry point, implementation location, and nearest tests. Keep inline unless persistence is requested.
- `standard`: understood flow, limited scope, reversible implementation. Inspect the affected flow, consumers, analogue, tests, and commands.
- `full`: materially cross-service, uncertain, irreversible, coupled, migratory, or rollout-sensitive. Add contracts, operations, alternatives, rollout, recovery, and observability.

Escalate after inspection when necessary. Record a short evidence-based `depth_rationale`; do not calculate a score.

## Ask Material Questions Only

Resolve repository-answerable questions by inspection. Ask only about choices that affect behavior, scope, risk, contracts, or architecture. Ask dependent questions individually; batch at most three related independent questions. Every question must provide an evidence-backed recommendation, a reasonable default with its consequence, or state that it is a stakeholder preference.

## Lifecycle and Persistence

Use `draft → decision-ready → handoff-ready → superseded`. Handoff-ready implementation content is immutable. A material discovery affecting behavior, scope, contracts, data semantics, architecture, slice dependencies, risk, rollout, recovery, or reversal creates version `N+1`, declares `supersedes`, and marks the old plan `superseded` with `superseded_by`; only those two old-plan fields may change. Delete unfinished drafts instead of superseding when appropriate.

When writes are permitted and `.agent` exists, evolve standard/full plans at `.agent/plans/<plan-id>-v<version>.md`. Ask before creating `.agent`. Honor repository instructions or an explicit location first. Under read-only or planning restrictions, keep the canonical artifact in conversation; later materialize it verbatim before task-graph handoff.

## Handoff Boundaries

A delivery slice is a macro-level, independently verifiable delivery boundary. It preserves architecture, contracts, sequencing, acceptance criteria, rollout, and reversal across handoff; it is not a task file or a complete task decomposition. The canonical schema retains the `# Implementation Slices` heading for compatibility.

Task-graph decomposes each delivery slice into fresh-context implementation tasks. It may discover dependencies and safe parallel work within a delivery slice. Slice-level parallel eligibility describes whether whole delivery slices can proceed concurrently; it does not constrain internal task-level scheduling.

Implementation may choose only localized, reversible details that preserve behavior, contracts, architecture, data semantics, rollout, acceptance criteria, and other delivery slices. A choice outside that discretion stops the slice and requires replanning.

For scouts, follow [plan-format.md](references/plan-format.md). A material scout is terminal for its plan; do not speculate downstream ship delivery slices. A technical spike may end with evidence and a recommendation.

Return an inline micro plan or the persisted plan path. `shape-code-change` never invokes task decomposition; the consumer must validate a handoff-ready schema and preserve delivery-slice provenance.
