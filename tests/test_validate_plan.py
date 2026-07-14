import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-plan.py"


def plan_text(
    *,
    status="handoff-ready",
    modifiers="[]",
    repository_state=None,
    unresolved="[]",
    audits=None,
    success_blocks=None,
    decision_blocks=None,
    slice_blocks=None,
    gate_block="modifiers: {}",
):
    repository_state = repository_state or """repository_state:
  vcs: git
  base_revision: abc123
  working_tree: clean
  includes_uncommitted_evidence: false
  observed_changed_paths: []"""
    audits = audits or """audits:
  decision_completeness: {status: complete, result: pass, exceptions: []}
  traceability: {status: complete, result: pass, exceptions: []}
  vertical_order: {status: complete, result: pass, exceptions: []}
  parallelization: {status: complete, result: pass, exceptions: []}"""
    success_blocks = success_blocks or ["""id: SC-001
outcome: Authorized users can export completed orders.
verification: The integration test returns the expected CSV rows."""]
    decision_blocks = decision_blocks or ["""id: DEC-001
status: resolved
decision: Generate exports synchronously.
rationale: Equivalent exports fit the request limit.
alternatives_rejected: [Background job]"""]
    slice_blocks = slice_blocks or ["""id: SLICE-001
type: ship
goal: Export completed orders through the existing API.
success_criteria: [SC-001]
depends_on: []
scope: [Add the export route and service behavior.]
out_of_scope: [Scheduled exports.]
code_locations:
  - path: src/orders/routes.py
    symbol: export_orders
    evidence: proposed
contracts_changed: [Additive authenticated HTTP endpoint.]
acceptance_criteria:
  - id: AC-001
    statement: Completed orders are returned as valid CSV.
    verification: Run the targeted integration test.
test_commands: [pytest tests/orders/test_export.py -v]
parallel:
  eligible: false
  reason: First end-to-end tracer slice.
rollout: Release with the existing deployment.
reversal: Remove the additive route before external adoption."""]

    def blocks(values):
        return "\n\n".join(f"```yaml\n{value}\n```" for value in values)

    return f"""---
schema_version: 1
plan_id: add-order-export
plan_version: 1
status: {status}
artifact_mode: file
supersedes: null
superseded_by: null
primary_intent: capability-add
risk_modifiers: {modifiers}
scope: cross-module
uncertainty: medium
plan_depth: standard
depth_rationale: Touches an existing cross-module flow with a reversible API addition.
handoff_target: task-graph
{repository_state}
unresolved_material_decisions: {unresolved}
{audits}
---

# Outcome

Allow authorized users to export completed orders.

# Success Criteria

{blocks(success_blocks)}

# Repository Evidence

The existing route and integration test establish the flow.

# Current and Target Flow

Request to route to service to CSV response.

# Decisions

{blocks(decision_blocks)}

# Scope

Add the export endpoint; exclude scheduled exports.

# Baseline

```yaml
commands:
  - command: pytest tests/orders/test_export.py -v
    result: pass
    relevance: Covers the nearest existing export flow.
```

# Implementation Slices

{blocks(slice_blocks)}

# Risk and Operational Gates

```yaml
{gate_block}
```

# Planning Audits

All four audits are represented in metadata.

# Pre-Handoff Discovery Log

No material discoveries after decision resolution.
"""


class ValidatorCliTests(unittest.TestCase):
    def run_validator(self, text, *args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.md"
            path.write_text(text)
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(path), *args],
                text=True,
                capture_output=True,
                check=False,
            )

    def assert_invalid(self, text, expected, *args):
        result = self.run_validator(text, *args)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def test_valid_draft_decision_ready_and_handoff(self):
        for status in ("draft", "decision-ready"):
            result = self.run_validator(plan_text(status=status))
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_validator(plan_text(), "--handoff")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_draft_can_validate_normally_but_not_for_handoff(self):
        draft = plan_text(status="draft", unresolved="[DEC-002]")
        self.assertEqual(self.run_validator(draft).returncode, 0)
        self.assert_invalid(draft, "status must be handoff-ready", "--handoff")

    def test_default_validation_allows_incomplete_draft_descriptors(self):
        draft = plan_text(
            status="draft",
            success_blocks=["id: SC-001"],
            decision_blocks=["id: DEC-001"],
            slice_blocks=["id: SLICE-001\ntype: scout\nmaterial: true\nsuccess_criteria: [SC-001]\ndepends_on: []"],
        )
        result = self.run_validator(draft)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(self.run_validator(draft, "--handoff").returncode, 0)

    def test_rejects_invalid_lifecycle_metadata(self):
        self.assert_invalid(plan_text(status="complete"), "invalid status")
        superseded = plan_text(status="superseded").replace(
            "superseded_by: null", "superseded_by: null"
        )
        self.assert_invalid(superseded, "superseded_by")
        invalid_replacement = plan_text().replace("supersedes: null", "supersedes: old-v1.md")
        self.assert_invalid(invalid_replacement, "plan_version must be greater than 1")

    def test_rejects_duplicate_and_missing_ids(self):
        duplicate = plan_text(
            success_blocks=[
                "id: SC-001\noutcome: One.\nverification: Check one.",
                "id: SC-001\noutcome: Two.\nverification: Check two.",
            ]
        )
        self.assert_invalid(duplicate, "duplicate success criterion id")
        missing = plan_text(slice_blocks=["type: ship\ngoal: Missing ID\nsuccess_criteria: [SC-001]"])
        self.assert_invalid(missing, "slice is missing id")

    def test_rejects_cyclic_slice_dependencies(self):
        first = """id: SLICE-001
type: ship
goal: First.
success_criteria: [SC-001]
depends_on: [SLICE-002]
acceptance_criteria: [{id: AC-001, statement: Works., verification: Test it.}]"""
        second = """id: SLICE-002
type: ship
goal: Second.
success_criteria: [SC-001]
depends_on: [SLICE-001]
acceptance_criteria: [{id: AC-002, statement: Works., verification: Test it.}]"""
        self.assert_invalid(plan_text(slice_blocks=[first, second]), "dependency cycle")

    def test_rejects_missing_coverage_and_unrelated_slices(self):
        uncovered = plan_text(
            success_blocks=[
                "id: SC-001\noutcome: One.\nverification: Test one.",
                "id: SC-002\noutcome: Two.\nverification: Test two.",
            ]
        )
        self.assert_invalid(uncovered, "SC-002 is not covered", "--handoff")
        unrelated = plan_text(
            slice_blocks=["""id: SLICE-001
type: ship
goal: Orphan work.
success_criteria: []
depends_on: []
acceptance_criteria: [{id: AC-001, statement: Works., verification: Test it.}]"""]
        )
        self.assert_invalid(unrelated, "does not advance a success criterion", "--handoff")

    def test_rejects_acceptance_without_verification(self):
        broken = plan_text().replace(
            "verification: Run the targeted integration test.\n", ""
        )
        self.assert_invalid(broken, "acceptance criterion AC-001", "--handoff")

    def test_requires_declared_modifier_gates(self):
        self.assert_invalid(
            plan_text(modifiers="[public-contract]"),
            "public-contract gate",
            "--handoff",
        )
        gates = """modifiers:
  public-contract:
    consumers: [API clients]
    compatibility: Additive change.
    versioning_or_deprecation: No version change required."""
        result = self.run_validator(
            plan_text(modifiers="[public-contract]", gate_block=gates), "--handoff"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_dirty_git_and_non_git_repository_metadata(self):
        dirty = """repository_state:
  vcs: git
  base_revision: abc123
  working_tree: dirty
  includes_uncommitted_evidence: true
  observed_changed_paths: [src/orders/routes.py]"""
        self.assertEqual(self.run_validator(plan_text(repository_state=dirty)).returncode, 0)
        no_git = """repository_state:
  vcs: none
  base_revision: null
  working_tree: unavailable
  includes_uncommitted_evidence: false
  observed_changed_paths: []"""
        self.assertEqual(self.run_validator(plan_text(repository_state=no_git)).returncode, 0)

    def test_validates_material_scout_gate(self):
        scout = """id: SLICE-001
type: scout
goal: Determine whether the event store supports atomic deduplication.
success_criteria: [SC-001]
depends_on: []
material: true
falsifiable_question: Can one atomic write enforce the idempotency key?
timebox: Four hours.
required_evidence: A concurrency test against the production-shaped adapter.
success_threshold: All duplicate writes collapse to one record.
failure_threshold: Any duplicate record is observed.
decision_rule: Use the store primitive on success; replan on failure.
replanning_condition: The store cannot enforce atomic deduplication.
acceptance_criteria:
  - id: AC-001
    statement: The scout records a reproducible conclusion.
    verification: Run the concurrency probe and attach its output."""
        self.assertEqual(self.run_validator(plan_text(slice_blocks=[scout]), "--handoff").returncode, 0)
        self.assert_invalid(
            plan_text(slice_blocks=[scout.replace("timebox: Four hours.\n", "")]),
            "material scout",
            "--handoff",
        )

    def test_json_output_is_stable_and_consumer_oriented(self):
        result = self.run_validator(plan_text(), "--handoff", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            list(payload),
            [
                "schema_version",
                "plan_id",
                "plan_version",
                "status",
                "repository_state",
                "success_criteria",
                "decisions",
                "slices",
                "risk_modifiers",
                "valid_for_handoff",
            ],
        )
        self.assertEqual(payload["slices"][0]["id"], "SLICE-001")
        self.assertTrue(payload["valid_for_handoff"])


class BehavioralCaseCoverageTests(unittest.TestCase):
    def test_cases_cover_intents_depths_modifiers_and_non_triggers(self):
        cases = json.loads((ROOT / "evals" / "cases.json").read_text())
        expectations = [case["expect"] for case in cases]
        intents = {item.get("primary_intent") for item in expectations}
        self.assertTrue(
            {
                "greenfield-system",
                "capability-add",
                "behavior-change",
                "defect-correction",
                "refactor",
                "migration",
                "quality-improvement",
                "operational-change",
                "retirement",
                "verification",
                "technical-spike",
            }.issubset(intents)
        )
        self.assertTrue({"micro", "standard", "full"}.issubset({item.get("plan_depth") for item in expectations}))
        modifiers = {modifier for item in expectations for modifier in item.get("risk_modifiers", [])}
        self.assertEqual(modifiers, set(MODIFIER_FIELDS_FOR_TEST))
        self.assertGreaterEqual(sum(item.get("trigger") is False for item in expectations), 3)


MODIFIER_FIELDS_FOR_TEST = [
    "public-contract",
    "persistent-data",
    "security-privacy-compliance",
    "distributed-async-concurrency",
    "performance-cost",
    "deployment-migration",
    "user-interface-accessibility",
]


if __name__ == "__main__":
    unittest.main()
