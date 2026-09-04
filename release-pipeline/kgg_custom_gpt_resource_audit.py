#!/usr/bin/env python3
"""Generate and verify the KGG Custom GPT model, capability and resource contract."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
import re
import sys
import tempfile
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
PRODUCTION_BOOTSTRAP_VERSION = "admin-v8"
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
PATIENT_BOOTSTRAP_VERSION = "patient-v5"
PATIENT_EDITOR_SNAPSHOT = ROOT / "docs" / "kgg-patient-custom-gpt-editor-snapshot.json"
CUSTOM_GPT_ACTION_LIMIT = 30
TARGET_PENDING_SYNC_STATUS = "target-pending-live-editor-sync"
LIVE_SYNC_STATUS = "live-synced"
TARGET_PASS = "TARGET_PASS"
LIVE_PASS = "LIVE_PASS"
_RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_MAIN_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


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
            "profileVersion": "4.2.0",
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


def atomic_write_text(path: Path, content: str) -> None:
    """Replace one text artifact without exposing a partial write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def read_snapshot(path: Path) -> dict[str, Any]:
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise AuditError(f"cannot read editor snapshot: {exc}") from exc
    if not isinstance(snapshot, dict):
        raise AuditError("editor snapshot must be a JSON object")
    return snapshot


def validate_snapshot_identity(
    snapshot: dict[str, Any], profile: str, expected: dict[str, Any]
) -> None:
    if snapshot.get("name") != expected.get("name"):
        raise AuditError(f"{profile} GPT name mismatch")
    if expected.get("visibility") and snapshot.get("visibility") != expected["visibility"]:
        raise AuditError(f"{profile} visibility mismatch")
    if profile in {"production", "patientProduction"} and not re.fullmatch(
        r"g-[a-z0-9]{16,64}", str(snapshot.get("gptId") or "")
    ):
        raise AuditError(f"{profile} GPT id is missing or invalid")
    if snapshot.get("model") != HIGHEST_ACTIONS_COMPATIBLE_MODEL:
        raise AuditError(f"{profile} GPT model is not {HIGHEST_ACTIONS_COMPATIBLE_MODEL}")
    capabilities = snapshot.get("capabilities")
    if not isinstance(capabilities, dict):
        raise AuditError(f"{profile} capabilities must be an object")
    for key, wanted in expected["capabilities"].items():
        if capabilities.get(key) is not wanted:
            raise AuditError(f"{profile} capability mismatch: {key} must be {wanted}")


def target_snapshot_fields(expected: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "profileVersion": expected["profileVersion"],
        "knowledgeSha256": [item["sha256"] for item in expected["knowledge"]],
        "actionSha256": [item["sha256"] for item in expected["actions"]],
    }
    if expected.get("editorBootstrap"):
        fields["bootstrapVersion"] = expected["editorBootstrap"]["version"]
        fields["instructionsSha256"] = expected["editorBootstrap"]["sha256"]
    return fields


def refresh_target_snapshot(path: Path, profile: str) -> None:
    if profile not in {"production", "patientProduction"}:
        raise AuditError("target refresh is supported only for production profiles")
    snapshot = read_snapshot(path)
    expected = expected_manifest()[profile]
    validate_snapshot_identity(snapshot, profile, expected)
    target_fields = target_snapshot_fields(expected)
    target_changed = any(snapshot.get(key) != value for key, value in target_fields.items())

    if profile == "production" and not target_changed:
        return

    for key, value in target_fields.items():
        snapshot[key] = value
    snapshot["syncStatus"] = TARGET_PENDING_SYNC_STATUS
    snapshot.pop("lastVerifiedAt", None)
    snapshot.pop("lastVerifiedMainCommit", None)
    atomic_write_text(path, normalize(snapshot))


def validate_live_verification(snapshot: dict[str, Any], profile: str) -> None:
    verified_at = snapshot.get("lastVerifiedAt")
    if not isinstance(verified_at, str) or not _RFC3339_UTC_RE.fullmatch(verified_at):
        raise AuditError(
            f"{profile} live snapshot requires RFC3339 UTC lastVerifiedAt"
        )
    try:
        datetime.fromisoformat(verified_at[:-1] + "+00:00")
    except ValueError as exc:
        raise AuditError(
            f"{profile} live snapshot requires RFC3339 UTC lastVerifiedAt"
        ) from exc
    verified_commit = snapshot.get("lastVerifiedMainCommit")
    if not isinstance(verified_commit, str) or not _MAIN_COMMIT_RE.fullmatch(
        verified_commit
    ):
        raise AuditError(
            f"{profile} live snapshot requires a 40-character lowercase "
            "lastVerifiedMainCommit"
        )


def validate_snapshot(
    path: Path, profile: str, *, require_live_synced: bool = False
) -> str:
    snapshot = read_snapshot(path)
    expected = expected_manifest()[profile]
    validate_snapshot_identity(snapshot, profile, expected)
    if snapshot.get("profileVersion") != expected.get(
        "profileVersion", snapshot.get("profileVersion")
    ):
        raise AuditError(f"{profile} profileVersion mismatch")
    expected_hashes = [item["sha256"] for item in expected["knowledge"]]
    actual_hashes = snapshot.get("knowledgeSha256")
    if (
        not isinstance(actual_hashes, list)
        or len(actual_hashes) != len(expected_hashes)
        or set(expected_hashes) != set(actual_hashes)
    ):
        raise AuditError(f"{profile} Knowledge digest mismatch")
    expected_action_hashes = [item["sha256"] for item in expected["actions"]]
    actual_action_hashes = snapshot.get("actionSha256")
    if (
        not isinstance(actual_action_hashes, list)
        or len(actual_action_hashes) != len(expected_action_hashes)
        or set(expected_action_hashes) != set(actual_action_hashes)
    ):
        raise AuditError(f"{profile} Action digest mismatch")
    if expected.get("editorBootstrap"):
        if snapshot.get("bootstrapVersion") != expected["editorBootstrap"]["version"]:
            raise AuditError(f"{profile} editor Bootstrap version mismatch")
        if snapshot.get("instructionsSha256") != expected["editorBootstrap"]["sha256"]:
            raise AuditError(f"{profile} editor Instructions digest mismatch")
    sync_status = snapshot.get("syncStatus")
    if sync_status == TARGET_PENDING_SYNC_STATUS:
        if require_live_synced:
            raise AuditError(
                f"{profile} editor snapshot is only a validated target; live sync is required"
            )
        return TARGET_PASS
    if sync_status == LIVE_SYNC_STATUS:
        validate_live_verification(snapshot, profile)
        return LIVE_PASS
    raise AuditError(
        f"{profile} syncStatus must be {TARGET_PENDING_SYNC_STATUS!r} or "
        f"{LIVE_SYNC_STATUS!r}"
    )


def combined_snapshot_status(statuses: list[str]) -> str:
    if not statuses:
        return "PASS"
    if TARGET_PASS in statuses:
        return TARGET_PASS
    return LIVE_PASS


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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
    mode.add_argument(
        "--refresh-target-profile",
        choices=["production", "patientProduction"],
        help="refresh one editor target snapshot and mark it pending without claiming live sync",
    )
    parser.add_argument("--editor-snapshot", type=Path)
    parser.add_argument("--profile", choices=["production", "eval", "patientProduction"])
    parser.add_argument(
        "--require-live-synced",
        action="store_true",
        help="reject target-only editor snapshots and require verified live-editor evidence",
    )
    args = parser.parse_args()
    try:
        if args.self_test and (
            args.editor_snapshot or args.profile or args.require_live_synced
        ):
            raise AuditError(
                "--self-test cannot be combined with editor snapshot validation flags"
            )
        selected_snapshot = args.editor_snapshot
        selected_profile = args.profile
        if args.refresh_target_profile:
            if args.profile:
                raise AuditError(
                    "--profile is derived from --refresh-target-profile"
                )
            if args.require_live_synced:
                raise AuditError(
                    "target refresh cannot be combined with --require-live-synced"
                )
            selected_profile = args.refresh_target_profile
            selected_snapshot = selected_snapshot or (
                PRODUCTION_EDITOR_SNAPSHOT
                if selected_profile == "production"
                else PATIENT_EDITOR_SNAPSHOT
            )
        elif args.profile and not args.editor_snapshot:
            raise AuditError("--profile requires --editor-snapshot")
        elif args.editor_snapshot and not args.profile:
            raise AuditError("--editor-snapshot requires --profile")
        if args.require_live_synced and (
            not selected_snapshot or not selected_profile
        ):
            raise AuditError(
                "--require-live-synced requires --editor-snapshot and --profile"
            )
        self_test()
        expected = normalize(expected_manifest())
        if args.self_test:
            print(json.dumps({"status": "PASS", "test": "kgg_custom_gpt_resource_audit"}))
            return 0
        if args.refresh_target_profile:
            refresh_target_snapshot(selected_snapshot, selected_profile)
            atomic_write_text(OUTPUT, expected)
        elif args.write:
            atomic_write_text(OUTPUT, expected)
        else:
            if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
                raise AuditError("resource manifest is missing or stale; run --write")
        snapshot_statuses: list[str] = []
        if selected_snapshot:
            snapshot_statuses.append(
                validate_snapshot(
                    selected_snapshot,
                    selected_profile,
                    require_live_synced=args.require_live_synced,
                )
            )
        elif PRODUCTION_EDITOR_SNAPSHOT.exists() or PATIENT_EDITOR_SNAPSHOT.exists():
            if PRODUCTION_EDITOR_SNAPSHOT.exists():
                snapshot_statuses.append(
                    validate_snapshot(
                        PRODUCTION_EDITOR_SNAPSHOT,
                        "production",
                        require_live_synced=args.require_live_synced,
                    )
                )
            if PATIENT_EDITOR_SNAPSHOT.exists():
                snapshot_statuses.append(
                    validate_snapshot(
                        PATIENT_EDITOR_SNAPSHOT,
                        "patientProduction",
                        require_live_synced=args.require_live_synced,
                    )
                )
        print(
            json.dumps(
                {
                    "status": combined_snapshot_status(snapshot_statuses),
                    "manifest": display_path(OUTPUT),
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
