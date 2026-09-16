#!/usr/bin/env python3
"""Fail-closed Candidate/host capability checks for the KGG Plugin."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


PLUGIN_GATE_SCHEMA = "kgg-plugin/candidate-gate/v1"
REQUIRED_SKILLS = frozenset({"kgg-supervisor", "kgg-operations", "kgg-testing", "kgg-safety", "kgg-escalation"})
REQUIRED_TOOLS = frozenset({"get_current_state", "get_ticket_state", "start_ui_session", "set_device_profile", "run_quick_flow", "capture_screenshot", "run_width_sweep", "get_test_evidence", "get_session_status"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CandidateGateError(ValueError):
    """Stable failure code suitable for a surface-comparison report."""


def _fail(code: str, detail: str = "") -> None:
    raise CandidateGateError(code if not detail else f"{code}: {detail}")


def validate_candidate(
    plugin_root: Path,
    *,
    expected_version: str = "0.1.0",
    mcp_available: bool = True,
    mcp_authorized: bool = True,
    fresh_main: bool = True,
    hook_accepted: bool = True,
    available_tools: set[str] | None = None,
    surface: str = "codex",
    surface_capabilities: Mapping[str, set[str]] | None = None,
    requested_tool_request_id: str | None = None,
    seen_request_ids: set[str] | None = None,
    skill_names: set[str] | None = None,
    hash_overrides: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate the static candidate and host gates without performing writes."""

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    hashes_path = plugin_root / "references" / "architecture" / "source-hashes.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hash_manifest = json.loads(hashes_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail("candidate_manifest_invalid", exc.__class__.__name__)
    # Codex installs may add a ``+codex.<cachebuster>`` build suffix.  The
    # candidate contract compares the semantic base version while the
    # cachebuster remains part of the installed manifest for reload safety.
    manifest_version = manifest.get("version")
    if not isinstance(manifest_version, str) or manifest_version.split("+", 1)[0] != expected_version:
        _fail("version_hash_drift", "plugin version")
    actual_skills = skill_names if skill_names is not None else {path.name for path in (plugin_root / "skills").iterdir() if path.is_dir()}
    missing = REQUIRED_SKILLS - actual_skills
    if missing:
        _fail("skill_missing", ", ".join(sorted(missing)))
    for entry in hash_manifest.get("sources", []):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str) or not _SHA256_RE.fullmatch(entry["sha256"]):
            _fail("version_hash_drift", "source manifest")
        path = str(entry["path"])
        source = plugin_root.parent / path
        if not source.is_file():
            _fail("version_hash_drift", path)
        actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        expected_hash = (hash_overrides or {}).get(path, entry["sha256"])
        if actual_hash != expected_hash:
            _fail("version_hash_drift", path)
    if not mcp_available:
        _fail("mcp_unavailable")
    if not mcp_authorized:
        _fail("mcp_auth_denied")
    if not fresh_main:
        _fail("mcp_stale_main")
    if not hook_accepted:
        _fail("hook_reject")
    if requested_tool_request_id and requested_tool_request_id in (seen_request_ids or set()):
        _fail("duplicate_tool_request", requested_tool_request_id)
    tools = available_tools if available_tools is not None else set(REQUIRED_TOOLS)
    missing_tools = REQUIRED_TOOLS - tools
    if missing_tools:
        _fail("capability_drift", ", ".join(sorted(missing_tools)))
    capabilities = surface_capabilities or {surface: {"mcp"}}
    if surface not in capabilities:
        _fail("surface_unavailable", surface)
    if "mcp" not in capabilities[surface]:
        _fail("surface_unavailable", f"{surface}:mcp")
    return {
        "schema": PLUGIN_GATE_SCHEMA,
        "status": "PASS",
        "surface": surface,
        "skills": sorted(REQUIRED_SKILLS),
        "tools": sorted(REQUIRED_TOOLS),
        "fresh_main": fresh_main,
    }
