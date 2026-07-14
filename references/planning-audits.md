# Planning Audits

Run audits in this order. Record each as `complete/pass` only after inspecting the plan; use `exceptions` for explicit, justified deviations. Validation proves structure, not substantive quality.

## 1. Decision completeness

- Every known material product, contract, data, architecture, risk, rollout, recovery, and reversal choice has a `DEC-*` descriptor.
- Decisions use `resolved`, `out-of-scope`, or `decision-rule` and contain rationale.
- No affected delivery slice relies on implementation to choose outside localized reversible discretion.
- A material scout ends the plan and defines its replanning gate.

## 2. Traceability

- Every stakeholder-visible outcome has an observable `SC-*` criterion and verification.
- Every success criterion is advanced by at least one delivery slice.
- Every delivery slice advances a criterion or is an explicitly justified horizontal prerequisite that names where it rejoins delivery.
- Evidence supports decisions and routing; proposed locations are not described as confirmed.

## 3. Vertical order

- Delivery slices were formed before parallelization was considered.
- The first ship delivery slice is a production-shaped tracer when practical.
- Each ship delivery slice crosses a real boundary, produces observable behavior, is independently verifiable, and leaves compatibility/build health intact.
- Dependencies reflect delivery order, compatibility windows, and operational gates.

## 4. Parallelization

- Delivery-slice parallel eligibility applies only to scheduling whole delivery slices; it does not constrain task-graph's safe task-level scheduling within a slice.
- No delivery slice was split solely for concurrency.
- Parallel delivery slices have no shared sequencing, contract, migration, or state dependency.
- Shared-file collision risk is noted when relevant.
- Ineligible delivery slices state the concrete macro-level dependency.

## Replanning audit

Before handoff, check discoveries since the last plan edit. Supersede the plan if any discovery changes stakeholder behavior or success, scope, public contracts or persistent-data meaning, architecture or slice dependencies, risk classification, rollout, recovery, or reversal. Mechanical decomposition, internal names, and localized reversible details do not require a new version.
