#!/usr/bin/env python3
"""Build the deterministic, non-sensitive context embedded in Preview output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PREVIEW_APP_VERSION = "0.2.13-v403-tab-s9-test-station"
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
    "patient-first-start",
    "patient-add-plan",
    "patient-replace-cancel",
    "patient-switch-plan",
    "patient-rename",
    "patient-values-reload",
    "patient-offline-restore",
    "qr-oppo-display",
    "qr-scan-7",
    "qr-scan-12",
    "qr-scan-20",
    "qr-angle-distance",
    "qr-weak-photo-fallback",
    "qr-camera-stop",
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


def build_context(
    *,
    request_id: str,
    patch_hash: str,
    base_sha: str,
    commit_sha: str,
    required_tests: list[str],
    preview_version: str = PREVIEW_APP_VERSION,
    web_version: str = "",
) -> dict[str, Any]:
    request = _clean_text(request_id, "requestId", 64).lower()
    if not REQUEST_ID_RE.fullmatch(request):
        raise PreviewContextError("requestId has an invalid shape")
    preview = _clean_text(preview_version, "previewVersion", 80)
    web = _clean_text(web_version, "webVersion", 80) if web_version else ""
    station_ids = list(STATION_TEST_IDS)
    return {
        "kind": "kgg_preview_context",
        "schemaVersion": SCHEMA_VERSION,
        "requestId": request,
        "patchHash": _sha(patch_hash, "patchHash", PATCH_HASH_RE),
        "baseSha": _sha(base_sha, "baseSha", SHA_RE),
        "commitSha": _sha(commit_sha, "commitSha", SHA_RE),
        "previewVersion": preview,
        "webVersion": web,
        "requiredTests": _required_tests(required_tests),
        "stationTestIds": station_ids,
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
