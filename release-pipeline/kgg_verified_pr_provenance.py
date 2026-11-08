#!/usr/bin/env python3
"""Strict, offline PR provenance validation for a future generic KGG Preview gate.

This module never publishes, downloads, executes PR code or acquires credentials.
The existing v133-specific publisher stays unchanged. A separate trusted workflow
must verify source checkout, run all test gates, and hold publishing privileges.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Mapping

CONTRACT = "kgg-verified-pr-provenance/v1"
REPO = "Kayus24/kgg"
WORKFLOW_NAME = "Validate and build KGG admin beta"
WORKFLOW_PATH = ".github/workflows/release-pr.yml"
WORKFLOW_ID = 299714308
APPROVAL_LABEL = "kgg-preview-approved"
NO_RELEASE_LABEL = "kgg-no-release"
REQUIRED_TESTS = ["critical", "ui-stability regression", "phone-cockpit-entry-390"]
EXPECTED_APPLICATION_ID = "de.kgg.preview"
_EMBEDDED_ASSET = "assets/android/kgg_preview_context.js"
_MAX_APK_BYTES = 128 * 1024 * 1024
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_BRANCH_RE = re.compile(r"[A-Za-z0-9._/-]{1,160}\Z")


class ProvenanceError(ValueError):
    """A non-sensitive code identifying failed provenance verification."""


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ProvenanceError(code)


def _obj(value: Any, name: str) -> Mapping[str, Any]:
    _require(isinstance(value, dict), name + "_not_object")
    return value


def _eq_number(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _branch(value: str) -> bool:
    return isinstance(value, str) and bool(_BRANCH_RE.fullmatch(value)) and not (
        value.startswith("/") or value.endswith("/") or ".." in value or "//" in value
    )


def validate(
    pr: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    pr_number: int,
    sha: str,
    branch: str,
    base_branch: str,
    base_sha: str,
    run_id: int,
) -> dict[str, Any]:
    """Validate already-fetched GitHub API PR/run JSON against immutable inputs.

    The caller MUST get this data from the authenticated GitHub REST API, not from
    an untrusted PR fixture, and MUST verify source checkout, code diffs, test
    results, permissions, and branch drift again immediately before publishing.
    """
    _require(type(pr_number) is int and pr_number > 0, "pr_number_invalid")
    _require(type(run_id) is int and run_id > 0, "run_id_invalid")
    _require(isinstance(sha, str) and bool(_SHA_RE.fullmatch(sha)), "sha_invalid")
    _require(_branch(branch), "branch_invalid")
    _require(_branch(base_branch), "base_branch_invalid")
    _require(isinstance(base_sha, str) and bool(_SHA_RE.fullmatch(base_sha)), "base_sha_invalid")
    pr = _obj(pr, "pr")
    run = _obj(run, "run")
    _require(_eq_number(pr.get("number"), pr_number), "pr_number_mismatch")
    _require(pr.get("state") == "open" and pr.get("draft") is True, "pr_not_open_draft")
    head = _obj(pr.get("head"), "pr_head")
    base = _obj(pr.get("base"), "pr_base")
    _require(head.get("sha") == sha, "pr_sha_drift")
    _require(head.get("ref") == branch, "pr_branch_drift")
    _require(base.get("ref") == base_branch, "pr_base_drift")
    _require(base.get("sha") == base_sha, "pr_base_sha_drift")
    _require(_obj(head.get("repo"), "head_repo").get("full_name") == REPO, "pr_fork_denied")
    _require(_obj(base.get("repo"), "base_repo").get("full_name") == REPO, "pr_base_repo_invalid")
    _require(pr.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}, "pr_author_untrusted")
    labels = pr.get("labels")
    _require(isinstance(labels, list), "pr_labels_invalid")
    label_names = []
    for label in labels:
        label_names.append(_obj(label, "pr_label").get("name"))
    _require(NO_RELEASE_LABEL in label_names, "no_release_label_missing")
    _require(APPROVAL_LABEL in label_names, "preview_approval_missing")
    _require(_eq_number(run.get("id"), run_id), "run_id_mismatch")
    _require(run.get("status") == "completed" and run.get("conclusion") == "success", "run_not_green")
    _require(run.get("event") == "pull_request", "run_event_invalid")
    _require(run.get("name") == WORKFLOW_NAME, "run_workflow_name_mismatch")
    _require(run.get("path") == WORKFLOW_PATH, "run_workflow_path_mismatch")
    _require(_eq_number(run.get("workflow_id"), WORKFLOW_ID), "run_workflow_id_mismatch")
    _require(run.get("head_sha") == sha, "run_sha_mismatch")
    _require(run.get("head_branch") == branch, "run_branch_mismatch")
    _require(_obj(run.get("repository"), "run_repo").get("full_name") == REPO, "run_repo_mismatch")
    _require(_obj(run.get("head_repository"), "run_head_repo").get("full_name") == REPO, "run_head_repo_mismatch")
    associated_prs = run.get("pull_requests")
    _require(isinstance(associated_prs, list), "run_pr_associations_invalid")
    match = [
        x for x in associated_prs
        if isinstance(x, dict) and _eq_number(x.get("number"), pr_number)
    ]
    _require(len(match) == 1, "run_pr_not_bound")
    run_pr_head = _obj(match[0].get("head"), "run_pr_head")
    run_pr_base = _obj(match[0].get("base"), "run_pr_base")
    _require(run_pr_head.get("sha") == sha and run_pr_head.get("ref") == branch,
             "run_pr_head_drift")
    _require(run_pr_base.get("sha") == base_sha and run_pr_base.get("ref") == base_branch,
             "run_pr_base_drift")
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "repo": REPO,
        "pr": pr_number,
        "sha": sha,
        "branch": branch,
        "baseBranch": base_branch,
        "baseSha": base_sha,
        "verificationRunId": run_id,
        "approval": APPROVAL_LABEL,
        "publishingAuthorized": False,
    }


def _json_object(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ProvenanceError(code) from None
    return _obj(parsed, code)


def _pinned_source_version(api: Mapping[str, Any]) -> bytes:
    """Decode only GitHub's authenticated Contents API file response."""
    api = _obj(api, "source_version_api")
    _require(api.get("type") == "file" and
             api.get("path") == "kgg-update/version.json" and
             api.get("encoding") == "base64", "source_version_api_invalid")
    encoded = api.get("content")
    size = api.get("size")
    _require(isinstance(encoded, str) and type(size) is int and
             0 < size <= 16384 and len(encoded) <= 24000, "source_version_api_size")
    try:
        raw = base64.b64decode("".join(encoded.split()), validate=True)
    except (ValueError, binascii.Error):
        raise ProvenanceError("source_version_api_base64") from None
    _require(len(raw) == size, "source_version_api_size_mismatch")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    _require(api.get("sha") == blob, "source_version_api_blob_mismatch")
    return raw


def _android_sdk_tool(android_home: Path | None, tool_name: str) -> Path:
    """Choose a preinstalled Android SDK binary, never execute an APK asset."""
    home = android_home if android_home is not None else os.environ.get("ANDROID_HOME")
    _require(bool(home), "android_sdk_unavailable")
    tools_dir = Path(home) / "build-tools"
    _require(tools_dir.is_dir(), "android_build_tools_unavailable")
    candidates = [p / tool_name for p in tools_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", p.name)
                  and (p / tool_name).is_file()]
    _require(bool(candidates), tool_name + "_unavailable")
    return sorted(candidates, key=lambda p: tuple(map(int, p.parent.name.split("."))))[-1]


def _verify_apk_signature(apk: Path, *, android_home: Path | None = None,
                          signature_runner: Any = None) -> None:
    """Only trusted Android SDK build-tools may inspect the untrusted APK."""
    signer = _android_sdk_tool(android_home, "apksigner")
    execute = signature_runner if signature_runner is not None else subprocess.run
    try:
        result = execute([str(signer), "verify", "--verbose", str(apk)],
                         capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ProvenanceError("apksigner_failed") from None
    _require(result.returncode == 0, "apk_signature_invalid")


def _embedded_context(raw: bytes) -> Mapping[str, Any]:
    """Parse only the exact Gradle Object.freeze(JSON) wrapper; never eval JS."""
    prefix = b"window.KGGPreviewContext=Object.freeze("
    suffix = b");\n"
    _require(0 < len(raw) <= 65536 and raw.startswith(prefix)
             and raw.endswith(suffix), "apk_context_wrapper_invalid")
    return _json_object(raw[len(prefix):-len(suffix)], "apk_context_json_invalid")


def _verify_apk_application_id(apk: Path, *, android_home: Path | None = None,
                               package_runner: Any = None) -> None:
    """Inspect the signed manifest using the trusted, installed Android SDK AAPT2."""
    home = android_home if android_home is not None else os.environ.get("ANDROID_HOME")
    _require(bool(home), "android_sdk_unavailable")
    tools_dir = Path(home) / "build-tools"
    _require(tools_dir.is_dir(), "android_build_tools_unavailable")
    candidates = [p / "aapt2" for p in tools_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", p.name)
                  and (p / "aapt2").is_file()]
    _require(bool(candidates), "aapt2_unavailable")
    aapt2 = sorted(candidates, key=lambda p: tuple(map(int, p.parent.name.split("."))))[-1]
    execute = package_runner if package_runner is not None else subprocess.run
    try:
        result = execute([str(aapt2), "dump", "packagename", str(apk)],
                         capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ProvenanceError("aapt2_failed") from None
    _require(result.returncode == 0, "aapt2_failed")
    _require(isinstance(result.stdout, str) and
             result.stdout.strip() == EXPECTED_APPLICATION_ID,
             "apk_application_id_mismatch")


def verify_staged_artifact(
    stage: Path, github_version: Mapping[str, Any], *,
    pr_number: int, sha: str, base_sha: str, run_id: int, request_id: str,
    android_home: Path | None = None, signature_runner: Any = None,
    package_runner: Any = None,
) -> dict[str, Any]:
    """Fail closed on untrusted data; independent inputs come from workflow dispatch."""
    _require(type(pr_number) is int and pr_number > 0, "artifact_pr_invalid")
    _require(type(run_id) is int and run_id > 0, "artifact_run_invalid")
    _require(isinstance(sha, str) and bool(_SHA_RE.fullmatch(sha)), "artifact_sha_invalid")
    _require(isinstance(base_sha, str) and bool(_SHA_RE.fullmatch(base_sha)), "artifact_base_invalid")
    _require(isinstance(request_id, str) and
             bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{5,63}", request_id)),
             "artifact_request_invalid")
    _require(stage.is_dir() and not stage.is_symlink(), "artifact_stage_invalid")
    names = {"app-preview-debug.apk", "version.json", "kgg-preview-context.json"}
    children = list(stage.iterdir())
    _require({p.name for p in children} == names and len(children) == 3
             and all(p.is_file() and not p.is_symlink() for p in children),
             "artifact_stage_shape_invalid")
    apk, version, context = (stage / x for x in
                             ("app-preview-debug.apk", "version.json",
                              "kgg-preview-context.json"))
    _require(1024 < apk.stat().st_size <= _MAX_APK_BYTES, "apk_size_invalid")
    _require(0 < version.stat().st_size <= 16384 and
             0 < context.stat().st_size <= 65536, "artifact_json_size_invalid")
    original = _pinned_source_version(github_version)
    _require(version.read_bytes() == original, "artifact_version_mismatch")
    version_data = _json_object(original, "source_version_json_invalid")
    _require(type(version_data.get("versionCode")) is int and
             version_data["versionCode"] > 0 and
             isinstance(version_data.get("versionName"), str) and
             bool(version_data["versionName"]), "source_version_fields_invalid")
    context_data = _json_object(context.read_bytes(), "context_json_invalid")
    patch_hash = hashlib.sha256(
        f"approved-pr|{pr_number}|{sha}|{run_id}".encode("ascii")
    ).hexdigest()
    _require(type(context_data.get("schemaVersion")) is int and
             context_data["schemaVersion"] == 2 and
             context_data.get("kind") == "kgg_preview_context",
             "context_schema_invalid")
    for key, expected in (
        ("commitSha", sha), ("baseSha", base_sha), ("requestId", request_id),
        ("patchHash", patch_hash), ("webVersion", version_data["versionName"])
    ):
        _require(context_data.get(key) == expected, "context_" + key + "_mismatch")
    _require(context_data.get("requiredTests") == REQUIRED_TESTS,
             "context_required_tests_invalid")
    try:
        with zipfile.ZipFile(apk) as archive:
            entries = archive.infolist()
            _require(0 < len(entries) <= 15000 and
                     sum(x.file_size for x in entries) <= 512 * 1024 * 1024,
                     "apk_zip_limits")
            manifest = [x for x in entries if x.filename == "AndroidManifest.xml"]
            _require(len(manifest) == 1 and
                     0 < manifest[0].file_size <= 1024 * 1024,
                     "apk_manifest_missing")
            embedded_files = [x for x in entries if x.filename == _EMBEDDED_ASSET]
            _require(len(embedded_files) == 1 and
                     0 < embedded_files[0].file_size <= 65536 and
                     not embedded_files[0].is_dir(), "apk_context_asset_missing")
            _require(archive.testzip() is None, "apk_zip_corrupt")
            embedded = _embedded_context(archive.read(embedded_files[0]))
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError):
        raise ProvenanceError("apk_zip_invalid") from None
    # Gradle's embedded context omits webVersion; all other fields must agree.
    expected_keys = {
        "kind", "schemaVersion", "requestId", "patchHash", "baseSha", "commitSha",
        "previewVersion", "requiredTests", "stationTestIds", "deviceTestSessionId",
        "deviceTestJobHash", "deviceTestJobUrl", "patientPwaUrl", "deviceTestProfile",
    }
    _require(set(context_data) == expected_keys | {"webVersion"},
             "context_fields_invalid")
    _require(set(embedded) == expected_keys, "apk_context_fields_invalid")
    _require(embedded == {key: context_data[key] for key in expected_keys},
             "apk_embedded_context_mismatch")
    _verify_apk_signature(apk, android_home=android_home,
                          signature_runner=signature_runner)
    _verify_apk_application_id(apk, android_home=android_home,
                               package_runner=package_runner)
    with apk.open("rb") as apk_stream:
        apk_digest = hashlib.file_digest(apk_stream, "sha256").hexdigest()
    return {
        "status": "PASS", "artifactSignatureVerified": True,
        "apkApplicationId": "de.kgg.preview", "embeddedPreviewContextVerified": True,
        "apkSha256": apk_digest,
        "sourceSha": sha, "baseSha": base_sha, "requestId": request_id,
        "publishingAuthorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-file", type=Path)
    parser.add_argument("--run-file", type=Path)
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--sha")
    parser.add_argument("--branch")
    parser.add_argument("--base-branch")
    parser.add_argument("--base-sha")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--verify-artifact", action="store_true")
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--github-version-file", type=Path)
    parser.add_argument("--request-id")
    args = parser.parse_args()
    if args.verify_artifact:
        if not all((args.artifact_dir, args.github_version_file, args.pr_number,
                    args.sha, args.base_sha, args.run_id, args.request_id)):
            parser.error("artifact-dir, github-version-file, pr-number, sha, base-sha, run-id and request-id required")
    elif not all((args.pr_file, args.run_file, args.pr_number, args.sha, args.branch, args.base_branch, args.base_sha, args.run_id)):
        parser.error("pr-file, run-file, pr-number, sha, branch, base-branch, base-sha and run-id are required")
    try:
        if args.verify_artifact:
            api = json.loads(args.github_version_file.read_text(encoding="utf-8"))
            result = verify_staged_artifact(
                args.artifact_dir, api, pr_number=args.pr_number,
                sha=args.sha, base_sha=args.base_sha, run_id=args.run_id,
                request_id=args.request_id)
        else:
            pr = json.loads(args.pr_file.read_text(encoding="utf-8"))
            run = json.loads(args.run_file.read_text(encoding="utf-8"))
            result = validate(pr, run, pr_number=args.pr_number, sha=args.sha,
                              branch=args.branch, base_branch=args.base_branch,
                              base_sha=args.base_sha, run_id=args.run_id)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ProvenanceError) as error:
        print(json.dumps({"status": "FAIL", "code": str(error) if isinstance(error, ProvenanceError) else "invalid_input"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
