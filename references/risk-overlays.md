# Risk Overlays

Read only the sections for declared `risk_modifiers`. Put each applicable descriptor under `modifiers` in the Risk and Operational Gates section. Fields must contain plan-specific substance, not placeholders.

## `public-contract`

- `consumers`: known and unknown callers, surfaces, ownership.
- `compatibility`: additive/breaking behavior and mixed-version behavior.
- `versioning_or_deprecation`: version decision or deprecation timeline and exit criteria.

## `persistent-data`

- `compatibility`: old/new readers, writers, and data meaning.
- `migration`: ordering, backfill, validation, cutover.
- `failure_recovery`: partial-failure detection and restart behavior.
- `rollback_or_forward_repair`: safe reversal or why forward repair is required.

## `security-privacy-compliance`

- `trust_boundaries`: identities, systems, and boundary crossings.
- `authorization`: decision point, policy, denial behavior.
- `sensitive_data`: collection, minimization, storage, transmission, retention.
- `auditability`: events, attribution, access, and evidence retention.

## `distributed-async-concurrency`

- `ordering`: required and non-required ordering guarantees.
- `retries`: retry ownership, budget, backoff, terminal handling.
- `idempotency`: key, scope, lifetime, atomic enforcement.
- `races`: concurrent actors, invariants, conflict behavior and tests.

## `performance-cost`

- `baseline`: measured current value and environment.
- `target`: threshold and acceptable regression budget.
- `workload`: representative shape, scale and distribution.
- `measurement_method`: command/tool, repetitions, statistics and comparison.

## `deployment-migration`

- `staged_exposure`: stage order, gates and promotion criteria.
- `compatibility_window`: versions or states that coexist and for how long.
- `recovery`: rollback/repair trigger, owner and steps.
- `drift_detection`: how partial rollout or configuration drift is detected.

## `user-interface-accessibility`

- `interaction_states`: loading, empty, error, success, disabled and recovery states.
- `supported_surfaces`: device, input, viewport, theme and locale commitments.
- `accessibility_verification`: keyboard/focus, semantics, contrast, screen reader and automated/manual checks.

## Combined modifiers

Merge requirements; do not duplicate them. When gates conflict, resolve the more constraining decision explicitly. Typical combinations:

- Public contract + deployment migration: specify client compatibility through the staged window.
- Persistent data + distributed concurrency: define atomicity, idempotent backfill, and mixed-reader/writer races.
- Security + UI: trace authorization and sensitive-data exposure through every interaction state.
- Performance + rollout: make the performance target a promotion and reversal gate.
