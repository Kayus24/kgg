#!/usr/bin/env python3
"""Run the local, non-mutating KGG Plugin Candidate gate."""

from __future__ import annotations

import json
import ast
import argparse
from pathlib import Path
import sys


REQUIRED_SKILLS = {
    "kgg-supervisor",
    "kgg-operations",
    "kgg-testing",
    "kgg-safety",
    "kgg-escalation",
}
REQUIRED_TOOLS = (
    "get_current_state",
    "get_ticket_state",
    "start_ui_session",
    "set_device_profile",
    "run_quick_flow",
    "capture_screenshot",
    "run_width_sweep",
    "get_test_evidence",
    "get_session_status",
)


def _roots() -> tuple[Path, Path, object | None]:
    """Resolve repository mode or an installed package without guessing paths."""

    for package_root in Path(__file__).resolve().parents:
        if not (package_root / ".codex-plugin" / "plugin.json").is_file():
            continue
        repository_root = package_root.parent
        gate = repository_root / "release-pipeline" / "kgg_plugin_candidate_gate.py"
        if gate.is_file():
            sys.path.insert(0, str(repository_root / "release-pipeline"))
            from kgg_plugin_candidate_gate import validate_candidate  # noqa: E402

            return repository_root, package_root, validate_candidate
        return package_root, package_root, None
    raise RuntimeError("candidate package root could not be resolved")


def _installed_package_check(plugin_root: Path) -> dict[str, object]:
    """Validate only bytes shipped in an installed cache package.

    Canonical source hashes and Fresh Main cannot be revalidated after the
    repository checkout is absent.  This result is therefore never marked
    comparison-ready; the repository gate remains the authority for A/B or
    migration decisions.
    """

    try:
        manifest = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        mcp = json.loads((plugin_root / ".mcp.json").read_text(encoding="utf-8"))
        source_hashes = json.loads((plugin_root / "references" / "architecture" / "source-hashes.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"installed package metadata invalid: {exc.__class__.__name__}") from exc

    if manifest.get("name") != "kgg-plugin" or not isinstance(manifest.get("version"), str) or manifest["version"].split("+", 1)[0] != "0.1.0":
        raise RuntimeError("installed package version or name invalid")
    if manifest.get("skills") != "./skills/" or manifest.get("mcpServers") != "./.mcp.json":
        raise RuntimeError("installed package manifest wiring invalid")
    if source_hashes.get("fresh_main_required") is not True:
        raise RuntimeError("installed source map does not require Fresh Main")

    skills_dir = plugin_root / "skills"
    actual_skills = {path.name for path in skills_dir.iterdir() if path.is_dir()} if skills_dir.is_dir() else set()
    if actual_skills != REQUIRED_SKILLS:
        raise RuntimeError("installed skill set invalid")
    for skill in sorted(REQUIRED_SKILLS):
        skill_file = skills_dir / skill / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "description:" not in text or "[TODO:" in text:
            raise RuntimeError(f"installed skill invalid: {skill}")

    server_path = plugin_root / "mcp" / "server.py"
    server_source = server_path.read_text(encoding="utf-8")
    tree = ast.parse(server_source, filename=str(server_path))
    tool_names = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TOOL_NAMES" for target in node.targets):
            tool_names = ast.literal_eval(node.value)
            break
    if tuple(tool_names or ()) != REQUIRED_TOOLS:
        raise RuntimeError("installed MCP tool catalog invalid")
    server_cfg = mcp.get("mcpServers", {}).get("kgg_ui_lab", {})
    if not isinstance(server_cfg, dict) or server_cfg.get("enabled") is not True or server_cfg.get("args") != ["./mcp/server.py"]:
        raise RuntimeError("installed MCP wiring invalid")

    return {
        "schema": "kgg-plugin/candidate-gate/v1",
        "status": "PASS",
        "surface": "installed-package",
        "verification_scope": "package_integrity_only",
        "comparison_ready": False,
        "fresh_main": "not_checked",
        "source_hashes": "declared_not_revalidated",
        "skills": sorted(REQUIRED_SKILLS),
        "tools": list(REQUIRED_TOOLS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-only", action="store_true", help="run package-only checks without repository sources")
    args = parser.parse_args(argv)
    _, plugin_root, repository_gate = _roots()
    if args.installed_only or repository_gate is None:
        result = _installed_package_check(plugin_root)
    else:
        result = repository_gate(
            plugin_root,
            surface_capabilities={"codex": {"mcp"}, "chatgpt": {"mcp"}},
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
