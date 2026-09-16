#!/usr/bin/env python3
"""Fail-closed evaluator for the five KGG migration gates.

This module only evaluates evidence.  It never migrates a Custom GPT, changes
an editor, dispatches a workflow, or releases an artifact.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


MIGRATION_SCHEMA = "kgg-ui-lab/migration-gates/v1"
GATE_NAMES = (
    "PARITY_PASS",
    "SAFETY_PASS",
    "EFFICIENCY_PASS",
    "CROSS_SURFACE_PASS",
    "STABILITY_PASS",
)
GATE_CHECKS = {
    "PARITY_PASS": frozenset({"required_fixtures", "required_tools", "skills"}),
    "SAFETY_PASS": frozenset({"no_gate_regression", "no_writes", "no_leaks", "fresh_main"}),
    "EFFICIENCY_PASS": frozenset({"candidate_quality", "candidate_dispatches", "candidate_runtime"}),
    "CROSS_SURFACE_PASS": frozenset({"chatgpt", "codex"}),
    "STABILITY_PASS": frozenset({"fault_injection", "round1", "round2"}),
}
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_KIND_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
_PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$")
_SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "browser_output")


class MigrationGateError(ValueError):
    """A stable, non-sensitive migration-gate error."""


def _fail(code: str, detail: str = "") -> None:
    raise MigrationGateError(code if not detail else f"{code}: {detail}")


def _evidence_refs(value: Any, gate: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        _fail("evidence_refs_invalid", gate)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or not {"id", "kind", "sha256"}.issubset(item) or set(item) - {"id", "kind", "sha256", "path"}:
            _fail("evidence_ref_invalid", f"{gate}[{index}]")
        identifier, kind, digest = item["id"], item["kind"], item["sha256"]
        if not isinstance(identifier, str) or not _ID_RE.fullmatch(identifier) or identifier in seen:
            _fail("evidence_ref_invalid", f"{gate}[{index}].id")
        if not isinstance(kind, str) or not _KIND_RE.fullmatch(kind) or any(token in kind.casefold() for token in _SENSITIVE):
            _fail("evidence_ref_invalid", f"{gate}[{index}].kind")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            _fail("evidence_ref_invalid", f"{gate}[{index}].sha256")
        seen.add(identifier)
        normalized = {"id": identifier, "kind": kind, "sha256": digest}
        if "path" in item:
            path = item["path"]
            if not isinstance(path, str) or not _PATH_RE.fullmatch(path) or path.startswith(".") or ".." in path.split("/"):
                _fail("evidence_ref_invalid", f"{gate}[{index}].path")
            normalized["path"] = path
        result.append(normalized)
    return result


def _gate(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"status", "checks", "evidence_refs"}:
        _fail("gate_fields_invalid", name)
    status = value["status"]
    if status not in {"PASS", "FAIL", "PENDING"}:
        _fail("gate_status_invalid", name)
    checks = value["checks"]
    expected = GATE_CHECKS[name]
    if not isinstance(checks, Mapping) or set(checks) != set(expected) or any(not isinstance(item, bool) for item in checks.values()):
        _fail("gate_checks_invalid", name)
    if status == "PASS" and not all(checks.values()):
        _fail("gate_conflict", name)
    return {"status": status, "checks": {key: bool(checks[key]) for key in sorted(expected)}, "evidence_refs": _evidence_refs(value["evidence_refs"], name)}


def _verify_file_hashes(report: Mapping[str, Any], evidence_root: Path) -> None:
    """Verify optional repository-relative evidence paths before eligibility."""

    for gate in report["gates"].values():
        for item in gate["evidence_refs"]:
            path = item.get("path")
            if not path:
                continue
            evidence_path = (evidence_root / path).resolve()
            try:
                evidence_path.relative_to(evidence_root.resolve())
            except ValueError:
                _fail("evidence_path_invalid", item["id"])
            if not evidence_path.is_file():
                _fail("evidence_file_missing", item["id"])
            actual = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            if actual != item["sha256"]:
                _fail("evidence_hash_mismatch", item["id"])


def evaluate(report: Mapping[str, Any], *, evidence_root: Path | None = None) -> dict[str, Any]:
    """Validate a gate report and derive a non-mutating eligibility result."""

    if not isinstance(report, Mapping) or set(report) != {"schema", "scenario_id", "fresh_main_sha", "gates"}:
        _fail("migration_report_fields_invalid")
    if report["schema"] != MIGRATION_SCHEMA:
        _fail("migration_schema_invalid")
    scenario_id = report["scenario_id"]
    if not isinstance(scenario_id, str) or not _ID_RE.fullmatch(scenario_id):
        _fail("scenario_id_invalid")
    fresh_main_sha = report["fresh_main_sha"]
    if not isinstance(fresh_main_sha, str) or not _SHA1_RE.fullmatch(fresh_main_sha):
        _fail("fresh_main_sha_invalid")
    gates = report["gates"]
    if not isinstance(gates, Mapping) or set(gates) != set(GATE_NAMES):
        _fail("migration_gates_incomplete")
    normalized = {name: _gate(name, gates[name]) for name in GATE_NAMES}
    _verify_file_hashes({"gates": normalized}, evidence_root or Path(__file__).resolve().parents[1])
    all_pass = all(item["status"] == "PASS" for item in normalized.values())
    return {
        "schema": MIGRATION_SCHEMA,
        "scenario_id": scenario_id,
        "fresh_main_sha": fresh_main_sha,
        "gates": deepcopy(normalized),
        "status": "MIGRATION_ELIGIBLE" if all_pass else "NOT_ELIGIBLE",
        # This evaluator can never authorize an external write or release.
        "release_allowed": False,
    }


def synthetic_pass_report() -> dict[str, Any]:
    """Return deterministic all-green evidence for contract tests only."""

    ref = {"id": "gate-ref-001", "kind": "result", "sha256": "a" * 64}
    return {
        "schema": MIGRATION_SCHEMA,
        "scenario_id": "ticket-180-gates",
        "fresh_main_sha": "b" * 40,
        "gates": {
            name: {"status": "PASS", "checks": {key: True for key in sorted(GATE_CHECKS[name])}, "evidence_refs": [dict(ref, id=f"{name.casefold().replace('_', '-')}-ref")]}
            for name in GATE_NAMES
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a KGG UI-Lab migration-gate report.")
    parser.add_argument(
        "--report",
        type=Path,
        help="JSON report to evaluate; without it, run the synthetic contract fixture.",
    )
    args = parser.parse_args()
    if args.report is None:
        report = synthetic_pass_report()
    else:
        try:
            report = json.loads(args.report.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            parser.error(f"cannot read report: {exc}")
    result = evaluate(report)
    print(json.dumps({"schema": MIGRATION_SCHEMA, "status": result["status"], "release_allowed": result["release_allowed"]}, sort_keys=True))
