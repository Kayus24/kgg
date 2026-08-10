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
HIGHEST_ACTIONS_COMPATIBLE_MODEL = "GPT-5.6 Thinking"

PRODUCTION_KNOWLEDGE = [
    "docs/kgg-custom-gpt-knowledge-architecture.md",
    "docs/kgg-custom-gpt-knowledge-operations.md",
    "docs/kgg-custom-gpt-knowledge-safety.md",
    "docs/kgg-custom-gpt-knowledge-testing.md",
]
PRODUCTION_ACTIONS = [
    "docs/kgg-custom-gpt-action-openapi.yaml",
    "docs/kgg-custom-gpt-action-api-openapi.yaml",
]
PRODUCTION_BOOTSTRAP = "docs/kgg-custom-gpt-editor-bootstrap.md"
PRODUCTION_BOOTSTRAP_VERSION = "admin-v6"
PRODUCTION_EDITOR_SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json"
EVAL_KNOWLEDGE = ["docs/kgg-custom-gpt-eval-knowledge.md"]
PATIENT_KNOWLEDGE = [
    "docs/kgg-patient-custom-gpt-knowledge-architecture.md",
    "docs/kgg-patient-custom-gpt-knowledge-operations.md",
    "docs/kgg-patient-custom-gpt-knowledge-safety.md",
    "docs/kgg-patient-custom-gpt-knowledge-testing.md",
]
PATIENT_ACTIONS = [
    "docs/kgg-patient-custom-gpt-action-openapi.yaml",
    "docs/kgg-patient-custom-gpt-action-api-openapi.yaml",
]
PATIENT_BOOTSTRAP = "docs/kgg-patient-custom-gpt-editor-bootstrap.md"
PATIENT_BOOTSTRAP_VERSION = "patient-v3"
PATIENT_EDITOR_SNAPSHOT = ROOT / "docs" / "kgg-patient-custom-gpt-editor-snapshot.json"
CUSTOM_GPT_ACTION_LIMIT = 30


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


def resource(path: str, *, version: str | None = None) -> dict[str, str]:
    result = {"path": path, "sha256": digest(path)}
    if version is not None:
        result["version"] = version
    return result


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
            "profileVersion": "4.1.0",
            "editorBootstrap": resource(
                PRODUCTION_BOOTSTRAP, version=PRODUCTION_BOOTSTRAP_VERSION
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
            "actions": [resource(path) for path in PRODUCTION_ACTIONS],
            "freshness": "GitHub live context and source chunks are authoritative; generated Knowledge is a retrieval accelerator and must pass --check.",
            "visibility": "private",
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
        "patientProduction": {
            "name": "KGG Patienten-App Update-Agent",
            "profileVersion": "1.2.0",
            "editorBootstrap": resource(
                PATIENT_BOOTSTRAP, version=PATIENT_BOOTSTRAP_VERSION
            ),
            "capabilities": {
                "webSearch": True,
                "codeInterpreter": True,
                "imageGeneration": False,
                "canvas": False,
                "apps": False,
                "actions": True,
            },
            "knowledge": [resource(path) for path in PATIENT_KNOWLEDGE],
            "actions": [resource(path) for path in PATIENT_ACTIONS],
            "freshness": "Live patient context, current source chunks and Preview evidence override static Knowledge.",
            "visibility": "private",
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
        raise AuditError(f"{profile} profileVersion mismatch")
    if expected.get("visibility") and snapshot.get("visibility") != expected["visibility"]:
        raise AuditError(f"{profile} visibility mismatch")
    if profile in {"production", "patientProduction"} and not re.fullmatch(
        r"g-[a-z0-9]{16,64}", str(snapshot.get("gptId") or "")
    ):
        raise AuditError(f"{profile} GPT id is missing or invalid")
    if snapshot.get("model") != HIGHEST_ACTIONS_COMPATIBLE_MODEL:
        raise AuditError(f"{profile} GPT model is not {HIGHEST_ACTIONS_COMPATIBLE_MODEL}")
    for key, wanted in expected["capabilities"].items():
        if bool(snapshot.get("capabilities", {}).get(key)) is not wanted:
            raise AuditError(f"{profile} capability mismatch: {key} must be {wanted}")
    expected_hashes = {item["sha256"] for item in expected["knowledge"]}
    actual_hashes = set(snapshot.get("knowledgeSha256", []))
    if expected_hashes != actual_hashes:
        raise AuditError(f"{profile} Knowledge digest mismatch")
    expected_action_hashes = {item["sha256"] for item in expected["actions"]}
    actual_action_hashes = set(snapshot.get("actionSha256", []))
    if expected_action_hashes != actual_action_hashes:
        raise AuditError(f"{profile} Action digest mismatch")
    if expected.get("editorBootstrap"):
        if snapshot.get("bootstrapVersion") != expected["editorBootstrap"]["version"]:
            raise AuditError(f"{profile} editor Bootstrap version mismatch")
        if snapshot.get("instructionsSha256") != expected["editorBootstrap"]["sha256"]:
            raise AuditError(f"{profile} editor Instructions digest mismatch")


def self_test() -> None:
    if normalized_text_digest(b"first\r\nsecond\r\n") != normalized_text_digest(b"first\nsecond\n"):
        raise AuditError("resource digests must be independent of CRLF or LF line endings")
    manifest = expected_manifest()
    if manifest["production"]["capabilities"]["apps"]:
        raise AuditError("production Apps must stay disabled because Custom Actions are required")
    if manifest["production"]["capabilities"]["canvas"]:
        raise AuditError("Canvas must stay disabled for the selected GPT model")
    if manifest["production"]["visibility"] != "private":
        raise AuditError("production GPT must remain private")
    if manifest["production"]["editorBootstrap"]["version"] == manifest["production"]["profileVersion"]:
        raise AuditError("production bootstrap and profile versions must remain separate contracts")
    if manifest["eval"]["capabilities"]["webSearch"]:
        raise AuditError("Eval GPT Web Search would compromise blind testing")
    if manifest["patientProduction"]["capabilities"]["apps"]:
        raise AuditError("patientProduction Apps must stay disabled because Custom Actions are required")
    if manifest["patientProduction"]["capabilities"]["imageGeneration"]:
        raise AuditError("patientProduction does not need Image Generation")
    if manifest["patientProduction"]["visibility"] != "private":
        raise AuditError("patientProduction must remain private")
    if manifest["patientProduction"]["editorBootstrap"]["version"] == manifest["patientProduction"]["profileVersion"]:
        raise AuditError("patient bootstrap and profile versions must remain separate contracts")
    for label, path in [
        ("admin raw", PRODUCTION_ACTIONS[0]),
        ("admin api", PRODUCTION_ACTIONS[1]),
        ("patient raw", PATIENT_ACTIONS[0]),
        ("patient api", PATIENT_ACTIONS[1]),
    ]:
        schema = (ROOT / path).read_text(encoding="utf-8")
        operations = len(re.findall(r"^\s+operationId:\s+\S+\s*$", schema, re.MULTILINE))
        if operations > CUSTOM_GPT_ACTION_LIMIT:
            raise AuditError(
                f"{label} Action exposes {operations} operations; limit is {CUSTOM_GPT_ACTION_LIMIT}"
            )
    production = {item["sha256"] for item in manifest["production"]["knowledge"]}
    evaluation = {item["sha256"] for item in manifest["eval"]["knowledge"]}
    if production.intersection(evaluation):
        raise AuditError("Eval and production Knowledge must be separated")
    patient = {item["sha256"] for item in manifest["patientProduction"]["knowledge"]}
    if patient.intersection(evaluation):
        raise AuditError("Patient and Eval Knowledge must be separated")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--editor-snapshot", type=Path)
    parser.add_argument("--profile", choices=["production", "eval", "patientProduction"])
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
        elif PRODUCTION_EDITOR_SNAPSHOT.exists() or PATIENT_EDITOR_SNAPSHOT.exists():
            if PRODUCTION_EDITOR_SNAPSHOT.exists():
                validate_snapshot(PRODUCTION_EDITOR_SNAPSHOT, "production")
            if PATIENT_EDITOR_SNAPSHOT.exists():
                validate_snapshot(PATIENT_EDITOR_SNAPSHOT, "patientProduction")
        print(json.dumps({"status": "PASS", "manifest": str(OUTPUT.relative_to(ROOT))}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
