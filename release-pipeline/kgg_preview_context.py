#!/usr/bin/env python3
"""Build the deterministic, non-sensitive context embedded in Preview output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


SCHEMA_VERSION = 2
PREVIEW_APP_VERSION = "0.2.14-v404-dual-device-qr-test"
REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PATCH_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SECRET_RE = re.compile(
    r"(?i)(?:gh[pousr]_[a-z0-9_]{20,}|sk-proj-[a-z0-9_-]{20,}|AIza[a-z0-9_-]{20,})"
)

STATION_TEST_IDS = (
    "admin-portrait",
    "admin-landscape",
    "admin-split-screen",
    "admin-package-button",
    "admin-touch-dialog-save",
    "admin-seven-exercises",
    "admin-reorder-save-reload",
    "display-pairing",
    "display-h2-1-baseline",
    "display-h2-7-legacy",
    "display-h2-12-diagnostic",
    "display-h2-20-diagnostic",
    "display-h3-7-normal",
    "display-h3-12-normal",
    "display-h3-20-normal",
    "display-h3-20-far-angle",
    "display-h3-20-low-contrast",
    "display-h3-20-photo",
)


class PreviewContextError(ValueError):
    """Raised when a context would be unsafe or ambiguous."""


def _clean_text(value: Any, label: str, limit: int) -> str:
    if not isinstance(value, str):
        raise PreviewContextError(f"{label} must be a string")
    clean = " ".join(value.replace("\r", " ").replace("\n", " ").replace("\t", " ").split())
    if not clean or len(clean) > limit:
        raise PreviewContextError(f"{label} must contain 1 to {limit} characters")
    if SECRET_RE.search(clean):
        raise PreviewContextError(f"{label} contains a token-shaped secret")
    return clean


def _required_tests(values: Any) -> list[str]:
    if not isinstance(values, list) or not values:
        raise PreviewContextError("requiredTests must be a non-empty list")
    if len(values) > 64:
        raise PreviewContextError("requiredTests contains too many entries")
    clean = [_clean_text(value, "requiredTests item", 240) for value in values]
    if len(set(clean)) != len(clean):
        raise PreviewContextError("requiredTests contains duplicates")
    return clean


def _sha(value: Any, label: str, pattern: re.Pattern[str]) -> str:
    clean = _clean_text(value, label, 64).lower()
    if not pattern.fullmatch(clean):
        raise PreviewContextError(f"{label} has an invalid shape")
    return clean


def _https_url(value: Any, label: str, hosts: set[str]) -> str:
    clean = _clean_text(value, label, 500)
    parsed = urlsplit(clean)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in hosts
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise PreviewContextError(f"{label} is not an allowed HTTPS URL")
    return clean


def build_context(
    *,
    request_id: str,
    patch_hash: str,
    base_sha: str,
    commit_sha: str,
    required_tests: list[str],
    preview_version: str = PREVIEW_APP_VERSION,
    web_version: str = "",
    device_test_session_id: str = "",
    device_test_job_hash: str = "",
    device_test_job_url: str = "",
    patient_pwa_url: str = "",
    device_test_profile: str = "quick",
) -> dict[str, Any]:
    request = _clean_text(request_id, "requestId", 64).lower()
    if not REQUEST_ID_RE.fullmatch(request):
        raise PreviewContextError("requestId has an invalid shape")
    preview = _clean_text(preview_version, "previewVersion", 80)
    web = _clean_text(web_version, "webVersion", 80) if web_version else ""
    clean_commit = _sha(commit_sha, "commitSha", SHA_RE)
    clean_patch = _sha(patch_hash, "patchHash", PATCH_HASH_RE)
    session_id = device_test_session_id or f"kgg-test-{clean_commit[:32]}"
    if not re.fullmatch(r"kgg-test-[a-f0-9]{32}", session_id):
        raise PreviewContextError("deviceTestSessionId has an invalid shape")
    job_hash = _sha(
        device_test_job_hash or clean_patch,
        "deviceTestJobHash",
        PATCH_HASH_RE,
    )
    job_url = _https_url(
        device_test_job_url
        or f"https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/{request}/job.json",
        "deviceTestJobUrl",
        {"raw.githubusercontent.com"},
    )
    pwa_url = _https_url(
        patient_pwa_url
        or "https://kayus24.github.io/kgg-patient-preview/device-test/",
        "patientPwaUrl",
        {"kayus24.github.io"},
    )
    profile = _clean_text(device_test_profile, "deviceTestProfile", 10).lower()
    if profile not in {"quick", "full"}:
        raise PreviewContextError("deviceTestProfile must be quick or full")
    return {
        "kind": "kgg_preview_context",
        "schemaVersion": SCHEMA_VERSION,
        "requestId": request,
        "patchHash": clean_patch,
        "baseSha": _sha(base_sha, "baseSha", SHA_RE),
        "commitSha": clean_commit,
        "previewVersion": preview,
        "webVersion": web,
        "requiredTests": _required_tests(required_tests),
        "stationTestIds": list(STATION_TEST_IDS),
        "deviceTestSessionId": session_id,
        "deviceTestJobHash": job_hash,
        "deviceTestJobUrl": job_url,
        "patientPwaUrl": pwa_url,
        "deviceTestProfile": profile,
    }


def context_script(context: dict[str, Any]) -> str:
    raw = json.dumps(context, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"window.KGGPreviewContext=Object.freeze({raw});\n"


def read_payload_required_tests(payload_file: Path) -> list[str]:
    try:
        payload = json.loads(payload_file.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreviewContextError(f"cannot read payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise PreviewContextError("payload must be an object")
    values = payload.get("required_tests", payload.get("requiredTests"))
    return _required_tests(values)


def write_context(path: Path, context: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(context, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def self_test() -> None:
    context = build_context(
        request_id="tab-s9-context-self-test",
        patch_hash="a" * 64,
        base_sha="b" * 40,
        commit_sha="c" * 40,
        required_tests=["critical", "ui-stability"],
        device_test_session_id="kgg-test-" + "d" * 32,
        device_test_job_hash="e" * 64,
        device_test_job_url="https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/self-test/job.json",
        patient_pwa_url="https://kayus24.github.io/kgg-patient-preview/device-test/",
        device_test_profile="quick",
    )
    script = context_script(context)
    if context["stationTestIds"] != list(STATION_TEST_IDS):
        raise PreviewContextError("station test list changed unexpectedly")
    if "tab-s9-context-self-test" not in script or "a" * 64 not in script:
        raise PreviewContextError("context script lost stable identifiers")
    for bad in [
        {"request_id": "../escape"},
        {"patch_hash": "g" * 64},
        {"base_sha": "d" * 39},
    ]:
        values = {
            "request_id": bad.get("request_id", "tab-s9-context-self-test"),
            "patch_hash": bad.get("patch_hash", "a" * 64),
            "base_sha": bad.get("base_sha", "b" * 40),
            "commit_sha": "c" * 40,
            "required_tests": ["critical"],
        }
        try:
            build_context(**values)
        except PreviewContextError:
            pass
        else:
            raise PreviewContextError("unsafe context value was accepted")
    try:
        build_context(
            request_id="tab-s9-context-self-test",
            patch_hash="a" * 64,
            base_sha="b" * 40,
            commit_sha="c" * 40,
            required_tests=["ghp_" + "x" * 30],
        )
    except PreviewContextError:
        pass
    else:
        raise PreviewContextError("secret-shaped test declaration was accepted")
    print("KGG Preview context self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--request-id")
    parser.add_argument("--patch-hash")
    parser.add_argument("--base-sha")
    parser.add_argument("--commit-sha")
    parser.add_argument("--preview-version", default=PREVIEW_APP_VERSION)
    parser.add_argument("--web-version", default="")
    parser.add_argument("--device-test-session-id", default="")
    parser.add_argument("--device-test-job-hash", default="")
    parser.add_argument("--device-test-job-url", default="")
    parser.add_argument("--patient-pwa-url", default="")
    parser.add_argument("--device-test-profile", default="quick")
    parser.add_argument("--payload-file", type=Path)
    parser.add_argument("--required-test", action="append", dest="required_tests")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    required_tests = args.required_tests
    if args.payload_file:
        required_tests = read_payload_required_tests(args.payload_file)
    if not all([args.request_id, args.patch_hash, args.base_sha, args.commit_sha, required_tests]):
        parser.error(
            "request-id, patch-hash, base-sha, commit-sha and required tests "
            "(--payload-file or --required-test) are required"
        )
    try:
        context = build_context(
            request_id=args.request_id,
            patch_hash=args.patch_hash,
            base_sha=args.base_sha,
            commit_sha=args.commit_sha,
            required_tests=required_tests,
            preview_version=args.preview_version,
            web_version=args.web_version,
            device_test_session_id=args.device_test_session_id,
            device_test_job_hash=args.device_test_job_hash,
            device_test_job_url=args.device_test_job_url,
            patient_pwa_url=args.patient_pwa_url,
            device_test_profile=args.device_test_profile,
        )
        if args.output:
            write_context(args.output, context)
        print(json.dumps(context, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except PreviewContextError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
