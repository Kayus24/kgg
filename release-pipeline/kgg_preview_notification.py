#!/usr/bin/env python3
"""Verify a published KGG preview and send one redacted FCM topic message."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


WORKFLOW_PATH = ".github/workflows/kgg-gpt-preview-gate.yml"
RUN_TITLE = re.compile(r"^KGG GPT Preview Gate \| publish_preview \| ([a-z0-9][a-z0-9-]{2,119})$")
REQUEST_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,119}$")
TOPIC = "kgg-preview"
CHANNEL_ID = "kgg_preview_updates"
NOTIFICATION_TAG = "kgg-preview-latest"
RAW_PREVIEW_PREFIX = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/"


class NotificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class VerifiedPreview:
    request_id: str
    title: str
    rollout_code: int
    html_url: str
    artifact_name: str


def _request_json(url: str, token: str = "") -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "kgg-preview-notifier",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        raise NotificationError(f"JSON request failed for {url}: {error}") from error


def _request_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "kgg-preview-notifier"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            if response.status != 200:
                raise NotificationError(f"Expected HTTP 200 for {url}, got {response.status}")
            return response.read()
    except urllib.error.URLError as error:
        raise NotificationError(f"HTTP request failed for {url}: {error}") from error


def _github_content(repo: str, path: str, ref: str, token: str) -> bytes:
    encoded_path = urllib.parse.quote(path, safe="/")
    encoded_ref = urllib.parse.quote(ref, safe="")
    payload = _request_json(
        f"https://api.github.com/repos/{repo}/contents/{encoded_path}?ref={encoded_ref}",
        token,
    )
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise NotificationError(f"GitHub content response is invalid for {path}")
    return base64.b64decode(payload["content"])


def _clean_title(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return "Eine neue Testversion ist bereit."
    return text[:160]


def parse_request_id(display_title: str) -> str:
    match = RUN_TITLE.fullmatch(display_title)
    if not match:
        raise NotificationError("Source run is not a publish_preview run with a safe request id.")
    return match.group(1)


def build_fcm_payload(preview: VerifiedPreview) -> dict[str, Any]:
    return {
        "message": {
            "topic": TOPIC,
            "notification": {
                "title": "Neue KGG Preview",
                "body": _clean_title(preview.title),
            },
            "data": {
                "request_id": preview.request_id,
                "title": _clean_title(preview.title),
                "rollout_code": str(preview.rollout_code),
                "html_url": preview.html_url,
            },
            "android": {
                "priority": "HIGH",
                "notification": {
                    "channel_id": CHANNEL_ID,
                    "icon": "ic_kgg_preview_notification",
                    "tag": NOTIFICATION_TAG,
                },
            },
        }
    }


def verify_preview(repo: str, run_id: int, github_token: str) -> VerifiedPreview:
    api_root = f"https://api.github.com/repos/{repo}"
    run = _request_json(f"{api_root}/actions/runs/{run_id}", github_token)
    if run.get("conclusion") != "success":
        raise NotificationError("Source preview run did not conclude successfully.")
    if run.get("event") != "workflow_dispatch" or run.get("path") != WORKFLOW_PATH:
        raise NotificationError("Source run is not the guarded KGG Preview workflow.")
    request_id = parse_request_id(str(run.get("display_title", "")))

    artifacts = _request_json(f"{api_root}/actions/runs/{run_id}/artifacts", github_token)
    expected_artifact = f"kgg-preview-{request_id}"
    matching = [
        artifact
        for artifact in artifacts.get("artifacts", [])
        if artifact.get("name") == expected_artifact and not artifact.get("expired", True)
    ]
    if len(matching) != 1:
        raise NotificationError("Expected one non-expired Preview APK/HTML artifact.")

    index_bytes = _github_content(repo, "previews/index.json", "gpt-preview", github_token)
    index = json.loads(index_bytes)
    latest = index.get("latest")
    if index.get("kind") != "kgg_gpt_preview_manifest" or not isinstance(latest, dict):
        raise NotificationError("Preview index has an invalid contract.")
    if latest.get("requestId") != request_id:
        raise NotificationError("Published preview is not the latest preview index entry.")

    meta_path = f"previews/{request_id}/meta.json"
    meta = json.loads(_github_content(repo, meta_path, "gpt-preview", github_token))
    if meta.get("kind") != "kgg_gpt_preview" or meta.get("requestId") != request_id:
        raise NotificationError("Preview metadata does not match the source run.")
    html_url = str(meta.get("url", ""))
    expected_prefix = f"{RAW_PREVIEW_PREFIX}{request_id}/"
    if not html_url.startswith(expected_prefix) or not html_url.endswith("/admin.html"):
        raise NotificationError("Preview HTML URL is outside the trusted request directory.")
    html = _request_bytes(f"{html_url}?run_id={run_id}")
    if hashlib.sha256(html).hexdigest() != str(meta.get("sha256", "")).lower():
        raise NotificationError("Preview HTML hash does not match meta.json.")
    rollout_code = meta.get("rolloutCode")
    if not isinstance(rollout_code, int) or rollout_code <= 0:
        raise NotificationError("Preview rolloutCode is invalid.")

    return VerifiedPreview(
        request_id=request_id,
        title=_clean_title(meta.get("title")),
        rollout_code=rollout_code,
        html_url=html_url,
        artifact_name=expected_artifact,
    )


def send_fcm(project_id: str, access_token: str, payload: dict[str, Any]) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project_id):
        raise NotificationError("Firebase project id is missing or invalid.")
    if not access_token:
        raise NotificationError("Firebase access token is missing.")
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        raise NotificationError(f"FCM send failed: {error}") from error
    message_name = str(result.get("name", ""))
    if not message_name.startswith(f"projects/{project_id}/messages/"):
        raise NotificationError("FCM response did not contain a valid message id.")
    return message_name


def self_test() -> None:
    request_id = parse_request_id("KGG GPT Preview Gate | publish_preview | test-preview-123")
    assert request_id == "test-preview-123"
    for invalid in [
        "KGG GPT Preview Gate | validate_only | test-preview-123",
        "KGG GPT Preview Gate | publish_preview | ../escape",
        "KGG GPT Preview Gate | publish_preview | Test_UPPER",
    ]:
        try:
            parse_request_id(invalid)
        except NotificationError:
            pass
        else:
            raise AssertionError(f"Unsafe run title accepted: {invalid}")
    preview = VerifiedPreview(
        request_id=request_id,
        title="  Test   Preview  ",
        rollout_code=123,
        html_url=f"{RAW_PREVIEW_PREFIX}{request_id}/admin.html",
        artifact_name=f"kgg-preview-{request_id}",
    )
    payload = build_fcm_payload(preview)
    assert payload["message"]["topic"] == TOPIC
    assert payload["message"]["notification"]["body"] == "Test Preview"
    assert payload["message"]["android"]["notification"]["tag"] == NOTIFICATION_TAG
    assert payload["message"]["data"]["rollout_code"] == "123"
    serialized = json.dumps(payload)
    for forbidden in ["access_token", "github_token", "patient", "patch_content"]:
        assert forbidden not in serialized.lower()
    print("KGG preview notification self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "Kayus24/kgg"))
    parser.add_argument("--run-id", type=int, default=int(os.environ.get("KGG_SOURCE_RUN_ID", "0")))
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.run_id <= 0:
        raise NotificationError("A positive --run-id is required.")

    preview = verify_preview(args.repo, args.run_id, os.environ.get("GITHUB_TOKEN", ""))
    payload = build_fcm_payload(preview)
    result: dict[str, Any] = {
        "status": "verified",
        "request_id": preview.request_id,
        "artifact_name": preview.artifact_name,
        "topic": TOPIC,
    }
    if not args.dry_run:
        result["message_id"] = send_fcm(
            os.environ.get("KGG_FIREBASE_PROJECT_ID", ""),
            os.environ.get("KGG_FIREBASE_ACCESS_TOKEN", ""),
            payload,
        )
        result["status"] = "sent"
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotificationError as error:
        print(json.dumps({"status": "notification_delivery_failed", "error": str(error)}))
        raise SystemExit(1)
