#!/usr/bin/env python3
"""Validate shape-code-change Markdown plans without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = [
    "Outcome",
    "Success Criteria",
    "Repository Evidence",
    "Current and Target Flow",
    "Decisions",
    "Scope",
    "Baseline",
    "Implementation Slices",
    "Risk and Operational Gates",
    "Planning Audits",
    "Pre-Handoff Discovery Log",
]
STATUSES = {"draft", "decision-ready", "handoff-ready", "superseded"}
DECISION_DISPOSITIONS = {"resolved", "out-of-scope", "decision-rule"}
LOCATION_EVIDENCE = {"confirmed", "proposed", "candidate"}
AUDIT_NAMES = {
    "decision_completeness",
    "traceability",
    "vertical_order",
    "parallelization",
}
MODIFIER_FIELDS = {
    "public-contract": {"consumers", "compatibility", "versioning_or_deprecation"},
    "persistent-data": {
        "compatibility",
        "migration",
        "failure_recovery",
        "rollback_or_forward_repair",
    },
    "security-privacy-compliance": {
        "trust_boundaries",
        "authorization",
        "sensitive_data",
        "auditability",
    },
    "distributed-async-concurrency": {"ordering", "retries", "idempotency", "races"},
    "performance-cost": {"baseline", "target", "workload", "measurement_method"},
    "deployment-migration": {
        "staged_exposure",
        "compatibility_window",
        "recovery",
        "drift_detection",
    },
    "user-interface-accessibility": {
        "interaction_states",
        "supported_surfaces",
        "accessibility_verification",
    },
}
MATERIAL_SCOUT_FIELDS = {
    "falsifiable_question",
    "timebox",
    "required_evidence",
    "success_threshold",
    "failure_threshold",
    "decision_rule",
    "replanning_condition",
}


class PlanError(Exception):
    pass


def split_top_level(value: str, delimiter: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for index, char in enumerate(value):
        if quote:
            if char == quote and (index == 0 or value[index - 1] != "\\"):
                quote = None
        elif char in "'\"":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == delimiter and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]


def split_key_value(value: str) -> tuple[str, str] | None:
    depth = 0
    quote: str | None = None
    for index, char in enumerate(value):
        if quote:
            if char == quote and value[index - 1 : index] != "\\":
                quote = None
        elif char in "'\"":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == ":" and depth == 0:
            return value[:index].strip(), value[index + 1 :].strip()
    return None


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        return [parse_scalar(part) for part in split_top_level(value[1:-1])]
    if value.startswith("{") and value.endswith("}"):
        result: dict[str, Any] = {}
        for part in split_top_level(value[1:-1]):
            pair = split_key_value(part)
            if not pair:
                raise PlanError(f"invalid inline mapping item: {part}")
            result[pair[0].strip("'\"")] = parse_scalar(pair[1])
        return result
    lowered = value.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


class MiniYaml:
    """Parser for the conservative YAML subset defined by the plan format."""

    def __init__(self, text: str):
        self.lines: list[tuple[int, str, int]] = []
        for number, raw in enumerate(text.splitlines(), 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if "\t" in raw[: len(raw) - len(raw.lstrip())]:
                raise PlanError(f"YAML line {number}: tabs are not allowed for indentation")
            indent = len(raw) - len(raw.lstrip(" "))
            self.lines.append((indent, raw.strip(), number))

    def parse(self) -> Any:
        if not self.lines:
            return {}
        value, index = self._block(0, self.lines[0][0])
        if index != len(self.lines):
            _, _, number = self.lines[index]
            raise PlanError(f"YAML line {number}: unexpected indentation")
        return value

    def _block(self, index: int, indent: int) -> tuple[Any, int]:
        if self.lines[index][0] != indent:
            raise PlanError(f"YAML line {self.lines[index][2]}: inconsistent indentation")
        if self.lines[index][1].startswith("- ") or self.lines[index][1] == "-":
            return self._list(index, indent)
        return self._mapping(index, indent)

    def _nested_or_empty(self, index: int, indent: int) -> tuple[Any, int]:
        if index < len(self.lines) and self.lines[index][0] > indent:
            return self._block(index, self.lines[index][0])
        return {}, index

    def _mapping(self, index: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(self.lines):
            current_indent, content, number = self.lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise PlanError(f"YAML line {number}: unexpected indentation")
            if content.startswith("- "):
                break
            pair = split_key_value(content)
            if not pair or not pair[0]:
                raise PlanError(f"YAML line {number}: expected key: value")
            key, raw_value = pair
            if key in result:
                raise PlanError(f"YAML line {number}: duplicate key {key}")
            index += 1
            if raw_value in {"|", ">"}:
                chunks = []
                while index < len(self.lines) and self.lines[index][0] > indent:
                    chunks.append(self.lines[index][1])
                    index += 1
                result[key] = "\n".join(chunks)
            elif raw_value:
                result[key] = parse_scalar(raw_value)
            else:
                result[key], index = self._nested_or_empty(index, indent)
        return result, index

    def _list(self, index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(self.lines):
            current_indent, content, number = self.lines[index]
            if current_indent < indent:
                break
            if current_indent != indent or not (content.startswith("- ") or content == "-"):
                break
            item = content[1:].strip()
            index += 1
            if not item:
                value, index = self._nested_or_empty(index, indent)
                result.append(value)
                continue
            pair = split_key_value(item)
            if pair:
                key, raw_value = pair
                value: dict[str, Any] = {}
                if raw_value:
                    value[key] = parse_scalar(raw_value)
                else:
                    value[key], index = self._nested_or_empty(index, indent)
                if index < len(self.lines) and self.lines[index][0] > indent:
                    extra_indent = self.lines[index][0]
                    extra, index = self._mapping(index, extra_indent)
                    for extra_key, extra_value in extra.items():
                        if extra_key in value:
                            raise PlanError(f"YAML line {number}: duplicate key {extra_key}")
                        value[extra_key] = extra_value
                result.append(value)
            else:
                result.append(parse_scalar(item))
        return result, index


def parse_yaml(text: str, context: str) -> Any:
    try:
        return MiniYaml(text).parse()
    except PlanError as error:
        raise PlanError(f"{context}: {error}") from error


def parse_plan(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PlanError(str(error)) from error
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    if not frontmatter:
        raise PlanError("plan must begin with YAML frontmatter delimited by ---")
    metadata = parse_yaml(frontmatter.group(1), "frontmatter")
    if not isinstance(metadata, dict):
        raise PlanError("frontmatter must be a mapping")
    body = text[frontmatter.end() :]
    matches = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        if name in sections:
            raise PlanError(f"duplicate section: {name}")
        sections[name] = body[match.end() : end].strip()
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        raise PlanError(f"missing required section(s): {', '.join(missing)}")

    def descriptors(section: str) -> list[dict[str, Any]]:
        blocks = re.findall(r"```ya?ml\s*\n(.*?)\n```", sections[section], re.DOTALL)
        parsed = [parse_yaml(block, f"{section} descriptor") for block in blocks]
        for value in parsed:
            if not isinstance(value, dict):
                raise PlanError(f"{section} descriptors must be mappings")
        return parsed

    gates = descriptors("Risk and Operational Gates")
    return {
        "metadata": metadata,
        "sections": sections,
        "success_criteria": descriptors("Success Criteria"),
        "decisions": descriptors("Decisions"),
        "slices": descriptors("Implementation Slices"),
        "gates": gates[0] if gates else {},
    }


def populated(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def require_fields(item: dict[str, Any], fields: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(field for field in fields if not populated(item.get(field)))
    if missing:
        errors.append(f"{label} is missing populated field(s): {', '.join(missing)}")


def collect_ids(items: list[dict[str, Any]], kind: str, prefix: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for item in items:
        identifier = item.get("id")
        if not identifier:
            errors.append(f"{kind} is missing id")
            continue
        if not isinstance(identifier, str) or not re.fullmatch(prefix + r"-\d+", identifier):
            errors.append(f"invalid {kind} id: {identifier}")
        if identifier in ids:
            errors.append(f"duplicate {kind} id: {identifier}")
        ids.add(identifier)
    return ids


def find_cycle(slices: list[dict[str, Any]], known: set[str]) -> bool:
    graph = {
        item.get("id"): [dep for dep in item.get("depends_on", []) if dep in known]
        for item in slices
        if item.get("id") in known
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(dependency) for dependency in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def validate(plan: dict[str, Any], handoff: bool) -> list[str]:
    errors: list[str] = []
    meta = plan["metadata"]
    required_meta = {
        "schema_version",
        "plan_id",
        "plan_version",
        "status",
        "artifact_mode",
        "primary_intent",
        "risk_modifiers",
        "scope",
        "uncertainty",
        "plan_depth",
        "depth_rationale",
        "handoff_target",
        "repository_state",
        "unresolved_material_decisions",
        "audits",
    }
    missing_meta = sorted(required_meta - set(meta))
    if missing_meta:
        errors.append(f"frontmatter missing field(s): {', '.join(missing_meta)}")
    if meta.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(meta.get("plan_version"), int) or meta.get("plan_version", 0) < 1:
        errors.append("plan_version must be a positive integer")
    if populated(meta.get("supersedes")) and meta.get("plan_version") == 1:
        errors.append("superseding plan_version must be greater than 1")
    status = meta.get("status")
    if status not in STATUSES:
        errors.append(f"invalid status: {status}")
    if status == "superseded" and not populated(meta.get("superseded_by")):
        errors.append("superseded plans must declare superseded_by")
    if status != "superseded" and populated(meta.get("superseded_by")):
        errors.append("only superseded plans may declare superseded_by")

    repository = meta.get("repository_state")
    if not isinstance(repository, dict):
        errors.append("repository_state must be a mapping")
    else:
        require_fields(
            repository,
            {"vcs", "working_tree"},
            "repository_state",
            errors,
        )
        vcs = repository.get("vcs")
        if vcs not in {"git", "none"}:
            errors.append("repository_state.vcs must be git or none")
        if vcs == "git" and not populated(repository.get("base_revision")):
            errors.append("Git repository_state requires base_revision")
        if vcs == "none" and repository.get("base_revision") is not None:
            errors.append("non-Git repository_state requires base_revision: null")
        if repository.get("working_tree") == "dirty":
            if repository.get("includes_uncommitted_evidence") is not True:
                errors.append("dirty repository_state must flag includes_uncommitted_evidence")
            if not repository.get("observed_changed_paths"):
                errors.append("dirty repository_state must list observed_changed_paths")

    success = plan["success_criteria"]
    decisions = plan["decisions"]
    slices = plan["slices"]
    sc_ids = collect_ids(success, "success criterion", "SC", errors)
    collect_ids(decisions, "decision", "DEC", errors)
    slice_ids = collect_ids(slices, "slice", "SLICE", errors)
    for decision in decisions:
        disposition = decision.get("status")
        if disposition is not None and disposition not in DECISION_DISPOSITIONS:
            errors.append(f"decision {decision.get('id', '?')} has invalid disposition: {disposition}")
    acceptance_ids: set[str] = set()
    for item in slices:
        identifier = item.get("id", "?")
        criteria = item.get("success_criteria", [])
        dependencies = item.get("depends_on", [])
        if not isinstance(criteria, list):
            errors.append(f"slice {identifier} success_criteria must be a list")
            criteria = []
        if not isinstance(dependencies, list):
            errors.append(f"slice {identifier} depends_on must be a list")
            dependencies = []
        for criterion in criteria:
            if criterion not in sc_ids:
                errors.append(f"slice {identifier} references unknown success criterion {criterion}")
        for dependency in dependencies:
            if dependency not in slice_ids:
                errors.append(f"slice {identifier} references unknown dependency {dependency}")
        for location in item.get("code_locations", []):
            if not isinstance(location, dict) or location.get("evidence") not in LOCATION_EVIDENCE:
                errors.append(f"slice {identifier} has invalid code location evidence")
        acceptance = item.get("acceptance_criteria", [])
        if acceptance and not isinstance(acceptance, list):
            errors.append(f"slice {identifier} acceptance_criteria must be a list")
            acceptance = []
        for criterion in acceptance:
            if not isinstance(criterion, dict):
                errors.append(f"slice {identifier} has invalid acceptance criterion")
                continue
            ac_id = criterion.get("id")
            if not ac_id:
                errors.append(f"slice {identifier} has acceptance criterion without id")
            elif ac_id in acceptance_ids:
                errors.append(f"duplicate acceptance criterion id: {ac_id}")
            else:
                acceptance_ids.add(ac_id)
        if item.get("type") == "scout" and item.get("material") is True:
            dependants = [
                other.get("id")
                for other in slices
                if identifier in other.get("depends_on", []) and other.get("type") == "ship"
            ]
            if dependants:
                errors.append(f"material scout {identifier} must be terminal; downstream ship slices: {', '.join(dependants)}")
    if find_cycle(slices, slice_ids):
        errors.append("slice dependency cycle detected")

    if not handoff:
        return errors
    if status != "handoff-ready":
        errors.append("status must be handoff-ready for --handoff validation")
    if meta.get("unresolved_material_decisions"):
        errors.append("unresolved_material_decisions must be empty for handoff")
    for criterion in success:
        require_fields(criterion, {"outcome", "verification"}, f"success criterion {criterion.get('id', '?')}", errors)
    for decision in decisions:
        require_fields(decision, {"status", "decision", "rationale"}, f"decision {decision.get('id', '?')}", errors)
    audits = meta.get("audits", {})
    if not isinstance(audits, dict):
        errors.append("audits must be a mapping")
    else:
        for name in sorted(AUDIT_NAMES):
            audit = audits.get(name)
            if not isinstance(audit, dict) or audit.get("status") != "complete" or audit.get("result") != "pass":
                errors.append(f"audit {name} must be complete with result pass")
    coverage: set[str] = set()
    for item in slices:
        identifier = item.get("id", "?")
        if item.get("type") == "scout" and item.get("material") is True:
            require_fields(item, MATERIAL_SCOUT_FIELDS, f"material scout {identifier}", errors)
        criteria = item.get("success_criteria", [])
        coverage.update(criteria if isinstance(criteria, list) else [])
        if item.get("type") == "ship" and not criteria:
            errors.append(f"ship slice {identifier} does not advance a success criterion")
        acceptance = item.get("acceptance_criteria", [])
        if not acceptance:
            errors.append(f"slice {identifier} must define acceptance criteria")
        elif isinstance(acceptance, list):
            for criterion in acceptance:
                if isinstance(criterion, dict):
                    require_fields(
                        criterion,
                        {"statement", "verification"},
                        f"acceptance criterion {criterion.get('id', '?')}",
                        errors,
                    )
    for identifier in sorted(sc_ids - coverage):
        errors.append(f"success criterion {identifier} is not covered by a slice")
    declared_modifiers = meta.get("risk_modifiers", [])
    if not isinstance(declared_modifiers, list):
        errors.append("risk_modifiers must be a list")
        declared_modifiers = []
    gate_map = plan["gates"].get("modifiers", {}) if isinstance(plan["gates"], dict) else {}
    if not isinstance(gate_map, dict):
        errors.append("Risk and Operational Gates modifiers must be a mapping")
        gate_map = {}
    for modifier in declared_modifiers:
        required = MODIFIER_FIELDS.get(modifier)
        if not required:
            continue
        gate = gate_map.get(modifier)
        if not isinstance(gate, dict):
            errors.append(f"{modifier} gate is missing")
        else:
            require_fields(gate, required, f"{modifier} gate", errors)
    return errors


def summary(plan: dict[str, Any], valid_for_handoff: bool) -> dict[str, Any]:
    meta = plan["metadata"]
    return {
        "schema_version": meta.get("schema_version"),
        "plan_id": meta.get("plan_id"),
        "plan_version": meta.get("plan_version"),
        "status": meta.get("status"),
        "repository_state": meta.get("repository_state"),
        "success_criteria": plan["success_criteria"],
        "decisions": plan["decisions"],
        "slices": plan["slices"],
        "risk_modifiers": meta.get("risk_modifiers", []),
        "valid_for_handoff": valid_for_handoff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--handoff", action="store_true", help="enforce handoff-ready requirements")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the parsed consumer summary")
    args = parser.parse_args()
    try:
        plan = parse_plan(args.plan)
        errors = validate(plan, args.handoff)
    except PlanError as error:
        errors = [str(error)]
        plan = None
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps(summary(plan, args.handoff), indent=2, ensure_ascii=False))
    else:
        mode = "handoff" if args.handoff else "draft"
        print(f"valid {mode} plan: {args.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
