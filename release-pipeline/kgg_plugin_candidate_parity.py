#!/usr/bin/env python3
"""Read-only parity fixtures for the first KGG Plugin Candidate slice.

The three names in the integrated goal are deliberately represented as local
evaluation fixtures, not as extra MCP tools.  This keeps the Phase 2 parity
check explicit while the Phase 3 tool catalog remains the fixed, preview-safe
surface.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


PARITY_SCHEMA = "kgg-plugin/parity-fixture/v1"
FIXTURE_NAMES = frozenset({"current_state", "ticket_plan", "safe_canary"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = (
    "raw_qr",
    "base64",
    "password",
    "api_key",
    "secret",
    "patient_data",
    "selector",
    "stack_trace",
    "browser_output",
)
_WRITE_KEYS = frozenset({"dispatch", "dispatches", "repository_writes", "editor_write", "merge", "release", "external_send"})


class ParityFixtureError(ValueError):
    """A stable, fail-closed parity-fixture error."""


def _fail(code: str, detail: str = "") -> None:
    raise ParityFixtureError(code if not detail else f"{code}: {detail}")


def _safe_tree(value: Any, path: str = "payload") -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 80:
                _fail("fixture_field_invalid", path)
            lowered = key.casefold()
            if any(token in lowered for token in _SENSITIVE) or lowered in _WRITE_KEYS:
                _fail("fixture_forbidden_field", f"{path}.{key}")
            result[key] = _safe_tree(item, f"{path}.{key}")
        return result
    if isinstance(value, list):
        if len(value) > 50:
            _fail("fixture_payload_too_large", path)
        return [_safe_tree(item, f"{path}[]") for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str) and len(value) > 500:
            _fail("fixture_value_too_large", path)
        return value
    _fail("fixture_value_invalid", path)


def validate_fixture(name: str, fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one named, synthetic, read-only parity fixture."""

    if name not in FIXTURE_NAMES:
        _fail("fixture_name_invalid")
    if not isinstance(fixture, Mapping) or set(fixture) != {"schema", "name", "mode", "source_sha256", "payload"}:
        _fail("fixture_fields_invalid", name)
    if fixture["schema"] != PARITY_SCHEMA or fixture["name"] != name:
        _fail("fixture_schema_invalid", name)
    if fixture["mode"] != "read_only":
        _fail("fixture_mode_invalid", name)
    digest = fixture["source_sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        _fail("fixture_source_hash_invalid", name)
    if not isinstance(fixture["payload"], Mapping):
        _fail("fixture_payload_invalid", name)
    return {
        "schema": PARITY_SCHEMA,
        "name": name,
        "mode": "read_only",
        "source_sha256": digest,
        "payload": _safe_tree(fixture["payload"]),
    }


def validate_bundle(bundle: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Require exactly the three Phase 2 fixtures, with no hidden extras."""

    if not isinstance(bundle, Mapping) or set(bundle) != set(FIXTURE_NAMES):
        _fail("fixture_bundle_incomplete")
    return {name: validate_fixture(name, bundle[name]) for name in sorted(FIXTURE_NAMES)}


def sample_bundle() -> dict[str, dict[str, Any]]:
    """Return deterministic synthetic fixtures used by the candidate eval."""

    digest = "a" * 64
    payloads = {
        "current_state": {"status": "ready", "branch": "codex/kgg-next-level-infrastructure", "head": "synthetic-head", "synthetic": True},
        "ticket_plan": {"ticket_id": "#180", "status": "selected", "title": "tablet-splitter-scale-drag", "steps": ["read", "reproduce", "report"], "synthetic": True},
        "safe_canary": {"scenario_id": "ticket-180-tablet-splitter", "status": "PASS", "synthetic": True},
    }
    return {
        name: {
            "schema": PARITY_SCHEMA,
            "name": name,
            "mode": "read_only",
            "source_sha256": digest,
            "payload": payloads[name],
        }
        for name in sorted(FIXTURE_NAMES)
    }


def self_test() -> None:
    """Exercise the positive bundle and the fail-closed negative cases."""

    bundle = validate_bundle(sample_bundle())
    assert set(bundle) == set(FIXTURE_NAMES)
    assert bundle["safe_canary"]["mode"] == "read_only"
    missing = dict(sample_bundle())
    missing.pop("ticket_plan")
    try:
        validate_bundle(missing)
    except ParityFixtureError as exc:
        assert str(exc).startswith("fixture_bundle_incomplete")
    else:
        raise AssertionError("missing parity fixture accepted")
    unsafe = sample_bundle()
    unsafe["safe_canary"]["payload"] = {"dispatches": 1}
    try:
        validate_bundle(unsafe)
    except ParityFixtureError as exc:
        assert str(exc).startswith("fixture_forbidden_field")
    else:
        raise AssertionError("write field accepted in parity fixture")


if __name__ == "__main__":
    self_test()
    print({"schema": PARITY_SCHEMA, "status": "PASS", "fixtures": sorted(FIXTURE_NAMES)})
