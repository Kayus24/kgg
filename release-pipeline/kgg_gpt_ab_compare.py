#!/usr/bin/env python3
"""Compare bounded Production/Candidate Custom GPT pilot metrics safely.

The comparator deliberately fails closed.  It never treats missing Candidate
evidence as a replacement decision and it emits only coarse metrics, not
prompts, browser output, selectors or traces.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Mapping


REQUIRED = (
    "scenario_id",
    "base_sha",
    "status",
    "reads",
    "context_items",
    "clarifying_questions",
    "action_calls",
    "dispatches",
    "duplicate_dispatches",
    "runtime_ms",
    "result_quality",
    "root_cause_quality",
    "repository_writes",
    "secret_leaks",
    "patient_data_leaks",
    "source_regressions",
    "gate_regressions",
    "action_regressions",
)
SURFACE_NAMES = ("production", "candidate", "codex_plugin")
NON_NEGATIVE = {
    "reads",
    "context_items",
    "clarifying_questions",
    "action_calls",
    "dispatches",
    "duplicate_dispatches",
    "runtime_ms",
    "result_quality",
    "root_cause_quality",
    "repository_writes",
    "secret_leaks",
    "patient_data_leaks",
    "source_regressions",
    "gate_regressions",
    "action_regressions",
}
FAILURE_ONLY_CLASSES = frozenset(
    {
        "NUMERIC_METRICS_NOT_VERIFIABLE",
        "REQUIRED_READ_NOT_VERIFIABLE",
        "FRESH_SHA_NOT_VERIFIABLE",
        "VERIFIABLE_COMPLETION_MISSING",
    }
)


class CompareError(ValueError):
    """Raised for malformed or unsafe comparison input."""


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompareError(f"cannot read metrics file: {path}") from exc
    if not isinstance(value, dict):
        raise CompareError("metrics file must contain one JSON object")
    return value


def _failure_only(label: str, value: Any) -> dict[str, Any] | None:
    """Accept the bounded fail-closed envelope without treating it as metrics."""

    if not isinstance(value, dict) or set(value) != {"status", "error_class"}:
        return None
    if value.get("status") != "FAIL" or value.get("error_class") not in FAILURE_ONLY_CLASSES:
        raise CompareError(f"{label} failure envelope is invalid")
    return {"status": "FAIL", "error_class": value["error_class"]}


def _normalize(label: str, value: Any) -> tuple[dict[str, Any], bool]:
    failure = _failure_only(label, value)
    if failure is not None:
        return failure, True
    return _validate(label, value), False


def _validate(label: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CompareError(f"{label} metrics are missing")
    missing = [key for key in REQUIRED if key not in value]
    if missing:
        raise CompareError(f"{label} metrics are incomplete")
    extra = sorted(set(value) - set(REQUIRED))
    if extra:
        raise CompareError(f"{label} metrics contain unexpected fields")
    status = str(value["status"]).upper()
    if status not in {"PASS", "FAIL"}:
        raise CompareError(f"{label} status must be PASS or FAIL")
    if not isinstance(value["scenario_id"], str) or not value["scenario_id"]:
        raise CompareError(f"{label} scenario_id must be non-empty")
    if not isinstance(value["base_sha"], str) or not re.fullmatch(r"[0-9a-fA-F]{40}", value["base_sha"]):
        raise CompareError(f"{label} base_sha must be a 40-character SHA")
    for key in NON_NEGATIVE:
        number = value[key]
        if not isinstance(number, int) or isinstance(number, bool) or number < 0:
            raise CompareError(f"{label} {key} must be a non-negative integer")
    for quality_key in ("result_quality", "root_cause_quality"):
        if value[quality_key] > 100:
            raise CompareError(f"{label} {quality_key} must be at most 100")
    return value


def compare(production: Any, candidate: Any) -> dict[str, Any]:
    """Return a safe comparison result; no replacement on incomplete evidence."""

    if not isinstance(production, dict) or not isinstance(candidate, dict):
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "stale_context",
            "safe_message": "Both Production and Candidate metrics are required.",
        }
    try:
        prod, prod_failure = _normalize("production", production)
        cand, cand_failure = _normalize("candidate", candidate)
    except CompareError as exc:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "payload_schema",
            "safe_message": str(exc),
        }

    if prod_failure or cand_failure:
        failures = {
            label: item["error_class"]
            for label, item, is_failure in (
                ("production", prod, prod_failure),
                ("candidate", cand, cand_failure),
            )
            if is_failure
        }
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "pilot_incomplete",
            "safe_message": "A surface returned a bounded failure envelope; complete numeric metrics are required.",
            "failure_classes": failures,
            "replacement_eligible": False,
        }

    if prod["scenario_id"] != cand["scenario_id"]:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "stale_context",
            "safe_message": "Production and Candidate do not use the same synthetic scenario.",
        }
    if prod["base_sha"] != cand["base_sha"]:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "stale_context",
            "safe_message": "Production and Candidate do not use the same Fresh-Main SHA.",
            "replacement_eligible": False,
        }

    safety_fields = (
        "duplicate_dispatches",
        "repository_writes",
        "secret_leaks",
        "patient_data_leaks",
        "source_regressions",
        "gate_regressions",
        "action_regressions",
    )
    if any(prod[key] or cand[key] for key in safety_fields):
        status = "FAIL"
        error_class = "safety_regression"
        safe_message = "A safety invariant failed; replacement is forbidden."
    elif prod["status"] != "PASS" or cand["status"] != "PASS":
        status = "NOT_COMPARABLE"
        error_class = "pilot_incomplete"
        safe_message = "Both sides must complete successfully before comparison."
    else:
        status = "COMPARABLE"
        error_class = ""
        safe_message = "Production and Candidate are comparable for this synthetic scenario."

    deltas = {key: cand[key] - prod[key] for key in NON_NEGATIVE}
    result = {
        "status": status,
        "error_class": error_class,
        "safe_message": safe_message,
        "scenario_id": prod["scenario_id"],
        "production_base_sha": prod["base_sha"],
        "candidate_base_sha": cand["base_sha"],
        "production": {key: prod[key] for key in NON_NEGATIVE},
        "candidate": {key: cand[key] for key in NON_NEGATIVE},
        "deltas_candidate_minus_production": deltas,
        "replacement_eligible": False,
    }
    if status == "COMPARABLE":
        # Replacement is intentionally stricter than comparability: the
        # Candidate must not regress quality, dispatch count or runtime.
        result["replacement_eligible"] = (
            cand["result_quality"] >= prod["result_quality"]
            and cand["root_cause_quality"] >= prod["root_cause_quality"]
            and cand["dispatches"] <= prod["dispatches"]
            and cand["runtime_ms"] <= prod["runtime_ms"]
        )
    return result


def compare_surfaces(
    surfaces: Mapping[str, Any],
    *,
    required_surfaces: tuple[str, ...] = SURFACE_NAMES,
) -> dict[str, Any]:
    """Compare two or three identical synthetic runs without replacement writes.

    The third surface is intentionally optional at the CLI boundary so existing
    two-sided reports remain readable.  When requested, every required surface
    must provide the complete metric contract; missing or unsafe evidence is
    never treated as a passing comparison.
    """

    if not isinstance(surfaces, Mapping) or not required_surfaces or len(set(required_surfaces)) != len(required_surfaces):
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "payload_schema",
            "safe_message": "Surface comparison definition is invalid.",
            "replacement_eligible": False,
        }
    missing = [name for name in required_surfaces if name not in surfaces]
    if missing:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "pilot_incomplete",
            "missing_surfaces": missing,
            "safe_message": "Every requested surface must complete the same synthetic pilot.",
            "replacement_eligible": False,
        }
    normalized: dict[str, dict[str, Any]] = {}
    failure_classes: dict[str, str] = {}
    try:
        for name in required_surfaces:
            normalized[name], is_failure = _normalize(name, surfaces[name])
            if is_failure:
                failure_classes[name] = normalized[name]["error_class"]
    except CompareError as exc:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "payload_schema",
            "safe_message": str(exc),
            "replacement_eligible": False,
        }

    if failure_classes:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "pilot_incomplete",
            "safe_message": "A surface returned a bounded failure envelope; complete numeric metrics are required.",
            "failure_classes": failure_classes,
            "replacement_eligible": False,
        }

    production = normalized.get("production")
    if production is None:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "payload_schema",
            "safe_message": "A production control surface is required.",
            "replacement_eligible": False,
        }
    scenario_ids = {item["scenario_id"] for item in normalized.values()}
    if len(scenario_ids) != 1:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "stale_context",
            "safe_message": "All surfaces must use the same synthetic scenario.",
            "replacement_eligible": False,
        }
    base_shas = {item["base_sha"] for item in normalized.values()}
    if len(base_shas) != 1:
        return {
            "status": "NOT_COMPARABLE",
            "error_class": "stale_context",
            "safe_message": "All surfaces must use the same Fresh-Main SHA.",
            "replacement_eligible": False,
        }

    safety_fields = (
        "duplicate_dispatches",
        "repository_writes",
        "secret_leaks",
        "patient_data_leaks",
        "source_regressions",
        "gate_regressions",
        "action_regressions",
    )
    safe_metrics = {
        name: {key: normalized[name][key] for key in NON_NEGATIVE}
        for name in required_surfaces
    }
    if any(normalized[name][key] for name in required_surfaces for key in safety_fields):
        status = "FAIL"
        error_class = "safety_regression"
        safe_message = "A safety invariant failed; replacement is forbidden."
    elif any(normalized[name]["status"] != "PASS" for name in required_surfaces):
        status = "NOT_COMPARABLE"
        error_class = "pilot_incomplete"
        safe_message = "Every surface must complete successfully before comparison."
    else:
        status = "COMPARABLE"
        error_class = ""
        safe_message = "All requested surfaces are comparable for this synthetic scenario."

    production_metrics = safe_metrics["production"]
    deltas = {
        name: {key: safe_metrics[name][key] - production_metrics[key] for key in NON_NEGATIVE}
        for name in required_surfaces
        if name != "production"
    }
    replacement_eligible = status == "COMPARABLE" and all(
        safe_metrics[name]["result_quality"] >= production_metrics["result_quality"]
        and safe_metrics[name]["root_cause_quality"] >= production_metrics["root_cause_quality"]
        and safe_metrics[name]["dispatches"] <= production_metrics["dispatches"]
        and safe_metrics[name]["runtime_ms"] <= production_metrics["runtime_ms"]
        for name in required_surfaces
        if name != "production"
    )
    return {
        "status": status,
        "error_class": error_class,
        "safe_message": safe_message,
        "scenario_id": production["scenario_id"],
        "surfaces": safe_metrics,
        "deltas_vs_production": deltas,
        "replacement_eligible": replacement_eligible,
    }


def self_test() -> None:
    base = {
        "scenario_id": "ticket-180-tablet-splitter",
        "base_sha": "a" * 40,
        "status": "PASS",
        "reads": 8,
        "context_items": 4,
        "clarifying_questions": 0,
        "action_calls": 2,
        "dispatches": 1,
        "duplicate_dispatches": 0,
        "runtime_ms": 900,
        "result_quality": 90,
        "root_cause_quality": 88,
        "repository_writes": 0,
        "secret_leaks": 0,
        "patient_data_leaks": 0,
        "source_regressions": 0,
        "gate_regressions": 0,
        "action_regressions": 0,
    }
    candidate = dict(base, reads=6, runtime_ms=700, result_quality=95, root_cause_quality=92)
    result = compare(base, candidate)
    assert result["status"] == "COMPARABLE"
    assert result["replacement_eligible"] is True
    assert result["deltas_candidate_minus_production"]["reads"] == -2
    root_quality_regression = compare(base, dict(candidate, root_cause_quality=87))
    assert root_quality_regression["status"] == "COMPARABLE"
    assert root_quality_regression["replacement_eligible"] is False
    unsafe = compare(dict(base, duplicate_dispatches=1), candidate)
    assert unsafe["status"] == "FAIL"
    assert unsafe["replacement_eligible"] is False
    source_unsafe = compare(dict(base, source_regressions=1), candidate)
    assert source_unsafe["status"] == "FAIL"
    assert source_unsafe["replacement_eligible"] is False
    missing = compare(base, {"scenario_id": "ticket-180-tablet-splitter"})
    assert missing["status"] == "NOT_COMPARABLE"
    assert "prompt" not in json.dumps(result).casefold()
    codex_plugin = dict(base, reads=5, runtime_ms=650, result_quality=96, root_cause_quality=93)
    three_way = compare_surfaces({"production": base, "candidate": candidate, "codex_plugin": codex_plugin})
    assert three_way["status"] == "COMPARABLE"
    assert three_way["replacement_eligible"] is True
    assert three_way["deltas_vs_production"]["codex_plugin"]["runtime_ms"] == -250
    root_quality_regression_three = compare_surfaces(
        {"production": base, "candidate": dict(candidate, root_cause_quality=87), "codex_plugin": codex_plugin}
    )
    assert root_quality_regression_three["status"] == "COMPARABLE"
    assert root_quality_regression_three["replacement_eligible"] is False
    incomplete = compare_surfaces({"production": base, "candidate": candidate})
    assert incomplete["status"] == "NOT_COMPARABLE"
    assert incomplete["error_class"] == "pilot_incomplete"
    assert "codex_plugin" in incomplete["missing_surfaces"]
    unsafe_three = compare_surfaces({"production": dict(base, action_regressions=1), "candidate": candidate, "codex_plugin": codex_plugin})
    assert unsafe_three["status"] == "FAIL"
    assert unsafe_three["replacement_eligible"] is False
    assert "prompt" not in json.dumps(three_way).casefold()
    mismatched_sha = compare(base, dict(candidate, base_sha="b" * 40))
    assert mismatched_sha["status"] == "NOT_COMPARABLE"
    assert mismatched_sha["error_class"] == "stale_context"
    mismatched_sha_three = compare_surfaces(
        {"production": base, "candidate": candidate, "codex_plugin": dict(codex_plugin, base_sha="b" * 40)}
    )
    assert mismatched_sha_three["status"] == "NOT_COMPARABLE"
    assert mismatched_sha_three["error_class"] == "stale_context"
    extra = compare(base, dict(candidate, raw_transcript="synthetic-only fixture"))
    assert extra["status"] == "NOT_COMPARABLE"
    assert extra["error_class"] == "payload_schema"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--production", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--codex-plugin", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"status": "PASS", "test": "kgg_gpt_ab_compare"}))
        return 0
    if not args.production or not args.candidate:
        parser.error("--production and --candidate are required unless --self-test is used")
    production = _read(args.production)
    candidate = _read(args.candidate)
    if args.codex_plugin:
        result = compare_surfaces(
            {"production": production, "candidate": candidate, "codex_plugin": _read(args.codex_plugin)}
        )
    else:
        result = compare(production, candidate)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 0 if result["status"] in {"COMPARABLE", "NOT_COMPARABLE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
