#!/usr/bin/env python3
"""Generate and verify the KGG Custom GPT model, capability and resource contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "kgg-custom-gpt-resource-manifest.json"
HIGHEST_ACTIONS_COMPATIBLE_MODEL = "GPT-5.6 Thinking"

PRODUCTION_KNOWLEDGE = [
    "docs/kgg-custom-gpt-knowledge-architecture.md",
    "docs/kgg-custom-gpt-knowledge-operations.md",
    "docs/kgg-custom-gpt-knowledge-safety.md",
    "docs/kgg-custom-gpt-knowledge-testing.md",
]
EVAL_KNOWLEDGE = ["docs/kgg-custom-gpt-eval-knowledge.md"]


class AuditError(RuntimeError):
    pass


def digest(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise AuditError(f"missing GPT resource: {path}")
    return hashlib.sha256(full.read_bytes()).hexdigest()


def resource(path: str) -> dict[str, str]:
    return {"path": path, "sha256": digest(path)}


def expected_manifest() -> dict[str, Any]:
    return {
        "schema": 1,
        "modelPolicy": {
            "rule": "Use the highest model currently offered by the GPT editor that still supports Custom Actions.",
            "verifiedEditorModel": HIGHEST_ACTIONS_COMPATIBLE_MODEL,
            "verifyBeforeEveryBlindRound": True,
            "disallowedModes": ["Pro mode when Actions are unavailable"],
        },
        "production": {
            "name": "KGG Update-Agent",
            "capabilities": {
                "webSearch": True,
                "codeInterpreter": True,
                "imageGeneration": True,
                "canvas": False,
                "apps": False,
                "actions": True,
            },
            "knowledge": [resource(path) for path in PRODUCTION_KNOWLEDGE],
            "actions": [
                resource("docs/kgg-custom-gpt-action-openapi.yaml"),
                resource("docs/kgg-custom-gpt-action-api-openapi.yaml"),
            ],
            "freshness": "GitHub live context and source chunks are authoritative; generated Knowledge is a retrieval accelerator and must pass --check.",
        },
        "eval": {
            "name": "KGG Repair-Lab Eval",
            "sameModelAsProduction": True,
            "capabilities": {
                "webSearch": False,
                "codeInterpreter": True,
                "imageGeneration": False,
                "canvas": False,
                "apps": False,
                "actions": True,
            },
            "knowledge": [resource(path) for path in EVAL_KNOWLEDGE],
            "actions": [
                resource("docs/kgg-custom-gpt-repair-lab-raw-openapi.yaml"),
                resource("docs/kgg-custom-gpt-repair-lab-api-openapi.yaml"),
            ],
            "forbiddenResources": [
                "production source Actions",
                "intact main HTML",
                "Web Search",
                "golden source",
                "internal challenge manifest",
                "sample repair payloads",
                "hidden evaluator assertions",
            ],
        },
        "officialReferences": [
            "https://help.openai.com/en/articles/8554397-creating-a-gpt",
            "https://help.openai.com/en/articles/8843948-knowledge-in-gpts",
            "https://help.openai.com/en/articles/20001049-apps-in-custom-gpts-beta",
            "https://help.openai.com/en/articles/8770868-gpt-actions",
        ],
    }


def normalize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def validate_snapshot(path: Path, profile: str) -> None:
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise AuditError(f"cannot read editor snapshot: {exc}") from exc
    expected = expected_manifest()[profile]
    if snapshot.get("model") != HIGHEST_ACTIONS_COMPATIBLE_MODEL:
        raise AuditError(f"{profile} GPT model is not {HIGHEST_ACTIONS_COMPATIBLE_MODEL}")
    for key, wanted in expected["capabilities"].items():
        if bool(snapshot.get("capabilities", {}).get(key)) is not wanted:
            raise AuditError(f"{profile} capability mismatch: {key} must be {wanted}")
    expected_hashes = {item["sha256"] for item in expected["knowledge"]}
    actual_hashes = set(snapshot.get("knowledgeSha256", []))
    if expected_hashes != actual_hashes:
        raise AuditError(f"{profile} Knowledge digest mismatch")


def self_test() -> None:
    manifest = expected_manifest()
    if manifest["production"]["capabilities"]["apps"]:
        raise AuditError("production Apps must stay disabled because Custom Actions are required")
    if manifest["production"]["capabilities"]["canvas"]:
        raise AuditError("Canvas must stay disabled for the selected GPT model")
    if manifest["eval"]["capabilities"]["webSearch"]:
        raise AuditError("Eval GPT Web Search would compromise blind testing")
    production = {item["sha256"] for item in manifest["production"]["knowledge"]}
    evaluation = {item["sha256"] for item in manifest["eval"]["knowledge"]}
    if production.intersection(evaluation):
        raise AuditError("Eval and production Knowledge must be separated")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--editor-snapshot", type=Path)
    parser.add_argument("--profile", choices=["production", "eval"])
    args = parser.parse_args()
    try:
        self_test()
        expected = normalize(expected_manifest())
        if args.self_test:
            print(json.dumps({"status": "PASS", "test": "kgg_custom_gpt_resource_audit"}))
            return 0
        if args.write:
            OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
        else:
            if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
                raise AuditError("resource manifest is missing or stale; run --write")
        if args.editor_snapshot:
            if not args.profile:
                raise AuditError("--profile is required with --editor-snapshot")
            validate_snapshot(args.editor_snapshot, args.profile)
        print(json.dumps({"status": "PASS", "manifest": str(OUTPUT.relative_to(ROOT))}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
