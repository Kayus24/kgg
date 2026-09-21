"""Fail-closed bridge from the bounded Python MCP server to Playwright.

The bridge is opt-in through ``KGG_REAL_BROWSER=1`` and executes one
allowlisted run in an ephemeral browser context.  It retains screenshots only
in memory, validates the helper response, and never falls back to synthetic
evidence when the real host is unavailable.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping
from urllib.parse import urlparse


MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class RealBrowserError(RuntimeError):
    """Safe, stable error emitted by the real browser boundary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _safe_url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise RealBrowserError("real_browser_url_invalid")
    parsed = urlparse(value)
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"} and bool(parsed.netloc)
    https = parsed.scheme == "https" and bool(parsed.netloc)
    if not local_http and not https:
        raise RealBrowserError("real_browser_url_invalid")
    return value


def _node_command() -> str:
    configured = os.environ.get("KGG_BROWSER_NODE")
    if configured and not Path(configured).is_file():
        raise RealBrowserError("real_browser_node_unavailable")
    command = configured or shutil.which("node")
    if not command:
        raise RealBrowserError("real_browser_node_unavailable")
    return command


def _helper_path() -> Path:
    path = Path(__file__).with_name("browser_host.js")
    if not path.is_file():
        raise RealBrowserError("real_browser_helper_missing")
    return path


def _validate_artifact(value: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, Any] | None]:
    required = {"id", "kind", "ref", "sha256", "content_type", "data_base64"}
    if set(value) != required or value.get("kind") != "screenshot" or value.get("content_type") != "image/png":
        raise RealBrowserError("real_browser_artifact_invalid")
    encoded = value.get("data_base64")
    if not isinstance(encoded, str) or len(encoded) > MAX_IMAGE_BYTES * 2:
        raise RealBrowserError("real_browser_artifact_too_large")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise RealBrowserError("real_browser_artifact_invalid") from None
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise RealBrowserError("real_browser_artifact_too_large")
    digest = hashlib.sha256(raw).hexdigest()
    if value.get("sha256") != digest:
        raise RealBrowserError("real_browser_artifact_hash_mismatch")
    public = {key: str(value[key]) for key in ("id", "kind", "ref", "sha256")}
    image = {"data_base64": encoded, "mime_type": "image/png", "sha256": digest}
    return public, image


def _validate_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RealBrowserError("real_browser_response_invalid")
    if value.get("status") not in {"PASS", "FAIL"} or not isinstance(value.get("steps"), list) or not isinstance(value.get("artifacts"), list):
        raise RealBrowserError("real_browser_response_invalid")
    if not isinstance(value.get("error_class"), str) or not isinstance(value.get("final_state"), str):
        raise RealBrowserError("real_browser_response_invalid")
    artifacts: list[dict[str, str]] = []
    images: list[dict[str, str]] = []
    for raw in value["artifacts"]:
        if not isinstance(raw, Mapping):
            raise RealBrowserError("real_browser_artifact_invalid")
        public, image = _validate_artifact(raw)
        artifacts.append(public)
        if image:
            images.append(image)
    steps: list[dict[str, Any]] = []
    for step in value["steps"]:
        if not isinstance(step, Mapping) or not {"expected", "actual", "status", "artifacts"}.issubset(step):
            raise RealBrowserError("real_browser_step_invalid")
        if step["status"] not in {"pass", "fail", "blocked"} or not isinstance(step["expected"], str) or not isinstance(step["actual"], str):
            raise RealBrowserError("real_browser_step_invalid")
        step_refs = []
        for ref in step.get("artifacts") or []:
            if isinstance(ref, Mapping):
                if isinstance(ref.get("id"), str):
                    step_refs.append(ref["id"])
            elif isinstance(ref, str):
                step_refs.append(ref)
        steps.append({
            "expected": step["expected"][:200],
            "actual": step["actual"][:200],
            "status": step["status"],
            "artifact_refs": [item["id"] for item in artifacts if item["id"] in set(step_refs)],
        })
    return {
        "status": value["status"],
        "error_class": value["error_class"][:120],
        "steps": steps,
        "artifacts": artifacts,
        "images": images,
        "final_state": value["final_state"][:200],
        "runtime_ms": value.get("runtime_ms") if isinstance(value.get("runtime_ms"), int) and value["runtime_ms"] >= 0 else 0,
    }


def run_real_flow(*, url: str, viewport: Mapping[str, Any], steps: list[Mapping[str, Any]], run_id: str, timeout_ms: int) -> dict[str, Any]:
    """Run one real browser flow; never substitutes synthetic evidence."""

    if os.environ.get("KGG_REAL_BROWSER", "").casefold() not in {"1", "true", "yes"}:
        raise RealBrowserError("real_browser_not_enabled")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 128:
        raise RealBrowserError("real_browser_run_id_invalid")
    if not isinstance(timeout_ms, int) or not 1000 <= timeout_ms <= 1_800_000:
        raise RealBrowserError("real_browser_timeout_invalid")
    request = {
        "command": "run",
        "run_id": run_id,
        "url": _safe_url(url),
        "viewport": dict(viewport),
        "steps": [dict(step) for step in steps],
    }
    env = os.environ.copy()
    module_path = env.get("KGG_PLAYWRIGHT_NODE_PATH")
    if module_path:
        env["NODE_PATH"] = module_path + os.pathsep + env.get("NODE_PATH", "")
    try:
        completed = subprocess.run(
            [_node_command(), str(_helper_path())],
            input=json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n",
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 15,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RealBrowserError("real_browser_timeout") from exc
    except OSError as exc:
        raise RealBrowserError("real_browser_process_failed") from exc
    if len(completed.stdout.encode("utf-8", errors="ignore")) > MAX_RESPONSE_BYTES:
        raise RealBrowserError("real_browser_response_too_large")
    try:
        raw = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise RealBrowserError("real_browser_response_invalid") from None
    response = _validate_response(raw)
    if completed.returncode != 0 and response["status"] == "PASS":
        raise RealBrowserError("real_browser_process_failed")
    return response
