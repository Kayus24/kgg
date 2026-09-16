#!/usr/bin/env python3
"""Fail-closed preflight for KGG Production-Control read-only pilots.

The preflight is local and non-mutating.  It checks that a declared pilot
profile can be executed by the synchronized Action schemas and that the real
editor state is supplied as a separate, dated UI-evidence precondition.  It
does not call a GPT, GitHub, the editor, or a validation workflow.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "docs" / "kgg-ui-lab-v1-production-control-readonly-contract.json"
DEFAULT_RAW_SCHEMA = ROOT / "docs" / "kgg-custom-gpt-action-openapi.yaml"
DEFAULT_API_SCHEMA = ROOT / "docs" / "kgg-custom-gpt-action-api-openapi.yaml"
CONTRACT_SCHEMA = "kgg-ui-lab/production-control-contract/v1"
_OPERATION_RE = re.compile(r"^\s+operationId:\s+([A-Za-z0-9_]+)\s*$", re.MULTILINE)
_PROFILE_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EDITOR_EVIDENCE_FIELDS = {
    "schema",
    "observed_at",
    "source",
    "gpt_status",
    "knowledge_count",
    "action_domains",
    "writes_performed",
    "manifest_context_reads",
}
_EDITOR_EVIDENCE_SCHEMA = "kgg-ui-lab/editor-live-observation/v1"


class PreflightError(ValueError):
    """Stable local preflight error."""


def _operations(schema_text: str, label: str) -> set[str]:
    if not isinstance(schema_text, str) or not schema_text.strip():
        raise PreflightError(f"{label}_schema_empty")
    values = _OPERATION_RE.findall(schema_text)
    if not values:
        raise PreflightError(f"{label}_operations_missing")
    if len(values) != len(set(values)):
        raise PreflightError(f"{label}_operation_duplicate")
    return set(values)


def _editor_evidence_is_valid(path: Path | None) -> bool:
    """Validate the structured, dated UI attestation required by the contract."""

    if not path or path.suffix.casefold() != ".json" or not path.is_file():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(value, dict) or set(value) != _EDITOR_EVIDENCE_FIELDS:
        return False
    if value.get("schema") != _EDITOR_EVIDENCE_SCHEMA:
        return False
    observed_at = value.get("observed_at")
    if not isinstance(observed_at, str) or not _DATE_RE.fullmatch(observed_at):
        return False
    try:
        observed_date = date.fromisoformat(observed_at)
    except ValueError:
        return False
    if (date.today() - observed_date).days > 1 or observed_date > date.today():
        return False
    if value.get("source") != "codex_internal_browser":
        return False
    if value.get("gpt_status") != "Live" or value.get("knowledge_count") != 4:
        return False
    if value.get("action_domains") != ["raw.githubusercontent.com", "api.github.com"]:
        return False
    if value.get("writes_performed") is not False:
        return False
    reads = value.get("manifest_context_reads")
    return reads == ["getKggCustomGptResourceManifest", "getKggProjectContext"]


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    """Load and minimally validate the declarative pilot contract."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError("contract_unreadable") from exc
    if not isinstance(value, dict) or set(value) != {"schema", "scenario_id", "profiles"}:
        raise PreflightError("contract_fields_invalid")
    if value["schema"] != CONTRACT_SCHEMA or not isinstance(value["scenario_id"], str) or not value["scenario_id"]:
        raise PreflightError("contract_identity_invalid")
    profiles = value["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise PreflightError("contract_profiles_invalid")
    for name, profile in profiles.items():
        if not isinstance(name, str) or not _PROFILE_RE.fullmatch(name):
            raise PreflightError("contract_profile_name_invalid")
        if not isinstance(profile, dict) or set(profile) != {"required_actions", "forbidden_actions", "external_preconditions"}:
            raise PreflightError(f"contract_profile_fields_invalid:{name}")
        for field in ("required_actions", "forbidden_actions", "external_preconditions"):
            values = profile[field]
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
                raise PreflightError(f"contract_profile_values_invalid:{name}:{field}")
            if len(values) != len(set(values)):
                raise PreflightError(f"contract_profile_duplicates:{name}:{field}")
        if set(profile["required_actions"]) & set(profile["forbidden_actions"]):
            raise PreflightError(f"contract_profile_conflict:{name}")
        if "editor_status_verified" not in profile["external_preconditions"]:
            raise PreflightError(f"contract_editor_precondition_missing:{name}")
    return value


def evaluate(
    contract: Mapping[str, Any],
    *,
    raw_schema: str,
    api_schema: str,
    profile: str,
    editor_evidence: Path | None,
) -> dict[str, Any]:
    """Evaluate one profile without performing any external operation."""

    if not isinstance(contract, Mapping) or contract.get("schema") != CONTRACT_SCHEMA:
        raise PreflightError("contract_identity_invalid")
    profiles = contract.get("profiles")
    if not isinstance(profiles, Mapping) or profile not in profiles:
        raise PreflightError("profile_unknown")
    selected = profiles[profile]
    if not isinstance(selected, Mapping):
        raise PreflightError("profile_invalid")
    raw_operations = _operations(raw_schema, "raw")
    api_operations = _operations(api_schema, "api")
    evidence_ok = _editor_evidence_is_valid(editor_evidence)
    overlap = raw_operations & api_operations
    if overlap:
        return {
            "status": "BLOCKED",
            "profile": profile,
            "error_class": "CAPABILITY_SCHEMA_INVALID",
            "missing_actions": [],
            "overlapping_actions": sorted(overlap),
            "editor_evidence": evidence_ok,
            "dispatch_policy": "forbidden" if profile == "baseline_no_dispatch" else "exactly_one_allowlisted",
            "safe_message": "Action operation ids must belong to exactly one synchronized domain.",
        }

    available = raw_operations | api_operations
    required = set(selected["required_actions"])
    missing = sorted(required - available)
    dispatch_policy = "forbidden" if profile == "baseline_no_dispatch" else "exactly_one_allowlisted"
    if missing:
        return {
            "status": "BLOCKED",
            "profile": profile,
            "error_class": "CAPABILITY_MISMATCH",
            "missing_actions": missing,
            "overlapping_actions": [],
            "editor_evidence": evidence_ok,
            "dispatch_policy": dispatch_policy,
            "safe_message": "The synchronized Action schemas cannot execute the declared pilot profile.",
        }

    if not evidence_ok:
        return {
            "status": "BLOCKED",
            "profile": profile,
            "error_class": "EXTERNAL_PRECONDITION_INVALID" if editor_evidence else "EXTERNAL_PRECONDITION_MISSING",
            "missing_actions": [],
            "overlapping_actions": [],
            "editor_evidence": False,
            "dispatch_policy": dispatch_policy,
            "safe_message": "A dated read-only observation of the real editor status is required before model execution.",
        }

    return {
        "status": "READY",
        "profile": profile,
        "error_class": "",
        "missing_actions": [],
        "overlapping_actions": [],
        "editor_evidence": True,
        "dispatch_policy": dispatch_policy,
        "safe_message": "Pilot capabilities and the external editor-status precondition are present.",
    }


def self_test() -> None:
    contract = {
        "schema": CONTRACT_SCHEMA,
        "scenario_id": "synthetic",
        "profiles": {
            "baseline_no_dispatch": {
                "required_actions": ["readManifest"],
                "forbidden_actions": ["writePreview"],
                "external_preconditions": ["editor_status_verified"],
            }
        },
    }
    import tempfile

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as evidence:
        json.dump(
            {
                "schema": _EDITOR_EVIDENCE_SCHEMA,
                "observed_at": date.today().isoformat(),
                "source": "codex_internal_browser",
                "gpt_status": "Live",
                "knowledge_count": 4,
                "action_domains": ["raw.githubusercontent.com", "api.github.com"],
                "writes_performed": False,
                "manifest_context_reads": ["getKggCustomGptResourceManifest", "getKggProjectContext"],
            },
            evidence,
        )
        evidence_path = Path(evidence.name)
    try:
        ready = evaluate(
            contract,
            raw_schema="  operationId: readManifest\n",
            api_schema="  operationId: readMain\n",
            profile="baseline_no_dispatch",
            editor_evidence=evidence_path,
        )
    finally:
        evidence_path.unlink(missing_ok=True)
    assert ready["status"] == "READY"
    blocked = evaluate(
        contract,
        raw_schema="  operationId: readOther\n",
        api_schema="  operationId: readMain\n",
        profile="baseline_no_dispatch",
        editor_evidence=None,
    )
    assert blocked["error_class"] == "CAPABILITY_MISMATCH"
    no_evidence = evaluate(
        contract,
        raw_schema="  operationId: readManifest\n",
        api_schema="  operationId: readMain\n",
        profile="baseline_no_dispatch",
        editor_evidence=None,
    )
    assert no_evidence["error_class"] == "EXTERNAL_PRECONDITION_MISSING"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--raw-schema", type=Path, default=DEFAULT_RAW_SCHEMA)
    parser.add_argument("--api-schema", type=Path, default=DEFAULT_API_SCHEMA)
    parser.add_argument("--profile", choices=("baseline_no_dispatch", "read_only_validation_runner"))
    parser.add_argument("--editor-evidence", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"status": "PASS", "test": "kgg_production_control_preflight"}))
        return 0
    if not args.profile:
        parser.error("--profile is required unless --self-test is used")
    try:
        result = evaluate(
            load_contract(args.contract),
            raw_schema=args.raw_schema.read_text(encoding="utf-8"),
            api_schema=args.api_schema.read_text(encoding="utf-8"),
            profile=args.profile,
            editor_evidence=args.editor_evidence,
        )
    except (OSError, UnicodeError, PreflightError) as exc:
        result = {
            "status": "BLOCKED",
            "profile": args.profile,
            "error_class": str(exc).split(":", 1)[0],
            "missing_actions": [],
            "overlapping_actions": [],
            "editor_evidence": False,
            "dispatch_policy": "forbidden" if args.profile == "baseline_no_dispatch" else "exactly_one_allowlisted",
            "safe_message": "Production-Control preflight could not prove the declared contract.",
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
