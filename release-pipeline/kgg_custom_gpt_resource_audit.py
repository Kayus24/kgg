#!/usr/bin/env python3
"""Generate and verify the KGG Custom GPT model, capability and resource contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "kgg-custom-gpt-resource-manifest.json"
EDITOR_SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json"
EVAL_EDITOR_SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-eval-editor-snapshot.json"
HIGHEST_ACTIONS_COMPATIBLE_MODEL = "GPT-5.6 Thinking"
PRODUCTION_PROFILE_VERSION = "2.5.0"
EVAL_PROFILE_VERSION = "2.1.0"
EDITOR_BOOTSTRAP_VERSION = "v2"
EDITOR_BOOTSTRAP_PATH = "docs/kgg-custom-gpt-editor-bootstrap.md"
EVAL_EDITOR_BOOTSTRAP_VERSION = "v8"
EVAL_EDITOR_BOOTSTRAP_PATH = "docs/kgg-custom-gpt-eval-editor-bootstrap.md"
EDITOR_BOOTSTRAP_MAX_CHARS = 4000
CUSTOM_GPT_ACTION_LIMIT = 30

PRODUCTION_KNOWLEDGE = [
    "docs/kgg-custom-gpt-knowledge-architecture.md",
    "docs/kgg-custom-gpt-knowledge-operations.md",
    "docs/kgg-custom-gpt-knowledge-safety.md",
    "docs/kgg-custom-gpt-knowledge-testing.md",
]
EVAL_KNOWLEDGE = ["docs/kgg-custom-gpt-eval-knowledge.md"]


class AuditError(RuntimeError):
    pass


def normalized_text_digest(content: bytes) -> str:
    normalized = content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def digest(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise AuditError(f"missing GPT resource: {path}")
    return normalized_text_digest(full.read_bytes())


def resource(path: str) -> dict[str, str]:
    return {"path": path, "sha256": digest(path)}


def editor_bootstrap_resource(
    path_name: str, version: str, *, strip_final_newline: bool
) -> dict[str, Any]:
    path = ROOT / path_name
    # The GPT editor preserves the content but removes a final textarea newline.
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if strip_final_newline:
        text = text.rstrip("\n")
    return {
        "path": path_name,
        "version": version,
        "characters": len(text),
        "sha256": normalized_text_digest(text.encode("utf-8")),
    }


def expected_manifest() -> dict[str, Any]:
    return {
        "schema": 2,
        "modelPolicy": {
            "rule": "Use the highest model currently offered by the GPT editor that still supports Custom Actions.",
            "verifiedEditorModel": HIGHEST_ACTIONS_COMPATIBLE_MODEL,
            "verifyBeforeEveryBlindRound": True,
            "disallowedModes": ["Pro mode when Actions are unavailable"],
        },
        "production": {
            "name": "KGG Update-Agent",
            "gptId": "g-6a45fba0f3408191ac1fb2c987a2e960",
            "profileVersion": PRODUCTION_PROFILE_VERSION,
            "editorBootstrap": editor_bootstrap_resource(
                EDITOR_BOOTSTRAP_PATH,
                EDITOR_BOOTSTRAP_VERSION,
                strip_final_newline=True,
            ),
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
            "gptId": "g-6a5e3483c98c81919e6f8a7939d5c072",
            "profileVersion": EVAL_PROFILE_VERSION,
            "editorBootstrap": editor_bootstrap_resource(
                EVAL_EDITOR_BOOTSTRAP_PATH,
                EVAL_EDITOR_BOOTSTRAP_VERSION,
                strip_final_newline=False,
            ),
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
                "canonical natural-language intent",
                "private clarification answer",
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
    if snapshot.get("profileVersion") != expected.get("profileVersion", snapshot.get("profileVersion")):
        raise AuditError(f"{profile} GPT profile version mismatch")
    if snapshot.get("model") != HIGHEST_ACTIONS_COMPATIBLE_MODEL:
        raise AuditError(f"{profile} GPT model is not {HIGHEST_ACTIONS_COMPATIBLE_MODEL}")
    for key, wanted in expected["capabilities"].items():
        if bool(snapshot.get("capabilities", {}).get(key)) is not wanted:
            raise AuditError(f"{profile} capability mismatch: {key} must be {wanted}")
    expected_hashes = {item["sha256"] for item in expected["knowledge"]}
    actual_hashes = set(snapshot.get("knowledgeSha256", []))
    if expected_hashes != actual_hashes:
        raise AuditError(f"{profile} Knowledge digest mismatch")
    expected_names = {Path(item["path"]).name for item in expected["knowledge"]}
    actual_names = set(snapshot.get("knowledgeNames", []))
    if expected_names != actual_names:
        raise AuditError(f"{profile} Knowledge filename mismatch")
    expected_action_hashes = {item["sha256"] for item in expected["actions"]}
    actual_action_hashes = set(snapshot.get("actionSha256", []))
    if expected_action_hashes != actual_action_hashes:
        raise AuditError(f"{profile} Action schema digest mismatch")
    bootstrap = expected.get("editorBootstrap")
    if bootstrap and snapshot.get("instructionsSha256") != bootstrap["sha256"]:
        raise AuditError(f"{profile} editor Instructions digest mismatch")
    if snapshot.get("gptId") and expected.get("gptId") and snapshot["gptId"] != expected["gptId"]:
        raise AuditError(f"{profile} GPT id mismatch")


def self_test() -> None:
    if normalized_text_digest(b"first\r\nsecond\r\n") != normalized_text_digest(b"first\nsecond\n"):
        raise AuditError("resource digests must be independent of CRLF or LF line endings")
    manifest = expected_manifest()
    for profile in ["production", "eval"]:
        bootstrap = manifest[profile]["editorBootstrap"]
        if bootstrap["characters"] > EDITOR_BOOTSTRAP_MAX_CHARS:
            raise AuditError(
                f"{profile} editor bootstrap exceeds {EDITOR_BOOTSTRAP_MAX_CHARS} characters"
            )
    bootstrap_text = (ROOT / EDITOR_BOOTSTRAP_PATH).read_text(encoding="utf-8")
    for marker in [
        "getKggCustomGptResourceManifest",
        "getKggProjectContext",
        "getKggCustomGptPlaybook",
        "getKggMemoryIndex",
        "GitHub Pages ist weder Memory-Quelle noch Fallback",
        "ausdruecklich writefreie Patchplanung",
        "Vor aktuellem Repo-/Versions-/Runstatus",
        "Erst nach drei erfolgreichen Reads darfst du Live-Status melden",
        "hoechstens fuenf getrennte Denkschritte",
    ]:
        if marker not in bootstrap_text:
            raise AuditError(f"production editor bootstrap missing marker: {marker}")
    eval_bootstrap_text = (ROOT / EVAL_EDITOR_BOOTSTRAP_PATH).read_text(encoding="utf-8")
    for marker in [
        "getKggRepairResult",
        "getKggNaturalUiResult",
        "evaluate_natural_attempt",
        "interpretation.confidence",
        "ausfuehrbares HTML-Fragment",
        "Nacktes CSS oder JavaScript",
        "finale Kaskade",
        "Selektor-/Eigenschaftspaar",
        "Repariere niemals eigenmaechtig beide",
        "clarification_count=1",
        "<!-- KGG PATCH START",
        "Nach drei aufeinanderfolgenden FAILs",
        "Fuehre niemals Preview-",
    ]:
        if marker not in eval_bootstrap_text:
            raise AuditError(f"eval editor bootstrap missing marker: {marker}")
    if manifest["production"]["capabilities"]["apps"]:
        raise AuditError("production Apps must stay disabled because Custom Actions are required")
    if manifest["production"]["capabilities"]["canvas"]:
        raise AuditError("Canvas must stay disabled for the selected GPT model")
    if manifest["eval"]["capabilities"]["webSearch"]:
        raise AuditError("Eval GPT Web Search would compromise blind testing")
    raw_action = (ROOT / "docs/kgg-custom-gpt-action-openapi.yaml").read_text(
        encoding="utf-8"
    )
    api_action = (ROOT / "docs/kgg-custom-gpt-action-api-openapi.yaml").read_text(
        encoding="utf-8"
    )
    eval_raw_action = (
        ROOT / "docs/kgg-custom-gpt-repair-lab-raw-openapi.yaml"
    ).read_text(encoding="utf-8")
    eval_api_action = (
        ROOT / "docs/kgg-custom-gpt-repair-lab-api-openapi.yaml"
    ).read_text(encoding="utf-8")
    for label, schema in [
        ("raw", raw_action),
        ("api", api_action),
        ("eval-raw", eval_raw_action),
        ("eval-api", eval_api_action),
    ]:
        operation_count = len(re.findall(r"^\s+operationId:\s+\S+\s*$", schema, re.MULTILINE))
        if operation_count > CUSTOM_GPT_ACTION_LIMIT:
            raise AuditError(
                f"{label} Action exposes {operation_count} operations; "
                f"Custom GPT limit is {CUSTOM_GPT_ACTION_LIMIT}"
            )
    if "\n  /repos/" in raw_action or "api.github.com" in raw_action:
        raise AuditError("raw Action must not duplicate authenticated GitHub API operations")
    if "getKggCustomGptResourceManifest" not in raw_action:
        raise AuditError("raw Action is missing the resource-manifest operation")
    if "submitKggPreviewGate" not in api_action or "getKggMemoryIndex" not in api_action:
        raise AuditError("API Action must provide Preview and private Memory operations")
    for marker in [
        "getKggNaturalUiLabIndex",
        "getKggNaturalUiScreenshot",
        "getKggNaturalUiResult",
    ]:
        if marker not in eval_raw_action:
            raise AuditError(f"Eval raw Action is missing {marker}")
    if (
        "evaluate_natural_attempt" not in eval_api_action
        or "submission_json" not in eval_api_action
        or "patch_content" not in eval_api_action
        or "never JSON-encode" not in eval_api_action
    ):
        raise AuditError("Eval API Action is missing natural UI submission support")
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
        snapshot_path = args.editor_snapshot
        snapshot_profile = args.profile
        if snapshot_path:
            if not snapshot_profile:
                raise AuditError("--profile is required with --editor-snapshot")
            validate_snapshot(snapshot_path, snapshot_profile)
        elif args.check:
            if EDITOR_SNAPSHOT.exists():
                validate_snapshot(EDITOR_SNAPSHOT, "production")
            if EVAL_EDITOR_SNAPSHOT.exists():
                validate_snapshot(EVAL_EDITOR_SNAPSHOT, "eval")
        print(json.dumps({"status": "PASS", "manifest": str(OUTPUT.relative_to(ROOT))}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
