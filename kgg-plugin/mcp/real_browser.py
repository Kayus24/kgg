"""Fail-closed, policy-driven bridge from the bounded Python server to Playwright.

The stdio launcher creates an explicit ``BrowserBootstrap`` from its host
configuration. Embedded callers default to a synthetic, disabled bootstrap.
The bridge executes one policy-allowlisted run in an ephemeral browser
context, retains screenshots only in memory, validates helper responses, and
never falls back to synthetic evidence when the real host is unavailable.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
from typing import Any, Mapping
from urllib.parse import urlparse


MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
_ATTRIBUTE_RE = re.compile(r"^data-[a-z0-9-]{1,63}$")
_NAMESPACE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


@dataclass(frozen=True)
class BrowserPolicy:
    """Host-neutral browser policy with KGG defaults supplied by the adapter."""

    allowed_https_hosts: frozenset[str] = frozenset({"kayus24.github.io"})
    allowed_https_path_prefixes: tuple[str, ...] = ("/kgg", "/kgg-patient-preview")
    state_attribute: str = "data-kgg-state"
    action_attribute: str = "data-kgg-action"
    input_attribute: str = "data-kgg-input"
    language_toggle_id: str | None = "kggLangSwitch"
    evidence_namespace: str = "kgg-ui-lab"

    def __post_init__(self) -> None:
        if any(not isinstance(host, str) or not host or "/" in host for host in self.allowed_https_hosts):
            raise ValueError("browser_policy_host_invalid")
        if any(not isinstance(prefix, str) or not prefix.startswith("/") for prefix in self.allowed_https_path_prefixes):
            raise ValueError("browser_policy_path_invalid")
        for attribute in (self.state_attribute, self.action_attribute, self.input_attribute):
            if not isinstance(attribute, str) or not _ATTRIBUTE_RE.fullmatch(attribute):
                raise ValueError("browser_policy_attribute_invalid")
        if self.language_toggle_id is not None and (not isinstance(self.language_toggle_id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", self.language_toggle_id)):
            raise ValueError("browser_policy_language_toggle_invalid")
        if not isinstance(self.evidence_namespace, str) or not _NAMESPACE_RE.fullmatch(self.evidence_namespace):
            raise ValueError("browser_policy_namespace_invalid")

    @classmethod
    def kgg(cls) -> "BrowserPolicy":
        return cls()

    @classmethod
    def generic(cls) -> "BrowserPolicy":
        return cls(
            allowed_https_hosts=frozenset(),
            allowed_https_path_prefixes=(),
            state_attribute="data-ui-state",
            action_attribute="data-ui-action",
            input_attribute="data-ui-input",
            language_toggle_id=None,
            evidence_namespace="generic-ui-lab",
        )

    def allows_url(self, value: str) -> bool:
        parsed = urlparse(value)
        local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"} and bool(parsed.netloc)
        if local_http:
            return True
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_https_hosts or not bool(parsed.netloc):
            return False
        path = parsed.path or "/"
        return any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in self.allowed_https_path_prefixes)

    def to_payload(self) -> dict[str, Any]:
        return {
            "allowed_https_hosts": sorted(self.allowed_https_hosts),
            "allowed_https_path_prefixes": list(self.allowed_https_path_prefixes),
            "state_attribute": self.state_attribute,
            "action_attribute": self.action_attribute,
            "input_attribute": self.input_attribute,
            "language_toggle_id": self.language_toggle_id,
            "evidence_namespace": self.evidence_namespace,
        }


@dataclass(frozen=True)
class BrowserBootstrap:
    """Explicit per-host activation and already-provisioned runtime selection."""

    enabled: bool = False
    node_command: str | None = None
    playwright_module_path: str | None = None
    policy: BrowserPolicy = field(default_factory=BrowserPolicy.kgg)

    @classmethod
    def synthetic(cls) -> "BrowserBootstrap":
        return cls(enabled=False)

    @classmethod
    def from_environment(cls) -> "BrowserBootstrap":
        """Read launcher variables only at an explicit host bootstrap boundary."""

        enabled = os.environ.get("KGG_REAL_BROWSER", "").casefold() in {"1", "true", "yes"}
        return cls(
            enabled=enabled,
            node_command=os.environ.get("KGG_BROWSER_NODE"),
            playwright_module_path=os.environ.get("KGG_PLAYWRIGHT_NODE_PATH"),
        )


class RealBrowserError(RuntimeError):
    """Safe, stable error emitted by the real browser boundary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _safe_url(value: Any, policy: BrowserPolicy | None = None) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise RealBrowserError("real_browser_url_invalid")
    selected_policy = policy or BrowserPolicy.kgg()
    parsed = urlparse(value)
    if parsed.username or parsed.password or parsed.fragment:
        raise RealBrowserError("real_browser_url_invalid")
    if not selected_policy.allows_url(value):
        raise RealBrowserError("real_browser_url_invalid")
    return value


def _node_command(bootstrap: BrowserBootstrap | None = None) -> str:
    configured = bootstrap.node_command if bootstrap is not None else None
    if configured and not Path(configured).is_file():
        raise RealBrowserError("real_browser_node_unavailable")
    command = configured or shutil.which("node")
    if not command:
        raise RealBrowserError("real_browser_node_unavailable")
    return command


def _playwright_module_path(bootstrap: BrowserBootstrap | None = None) -> str | None:
    """Resolve an already provisioned Playwright runtime for the child host.

    The MCP server is launched from ``kgg-plugin/mcp`` while the bundled Codex
    runtime keeps its Node modules outside the repository.  Without an
    explicit ``NODE_PATH`` the child process exits before it can emit a JSON
    response, which the persistent bridge can only observe as a generic
    timeout.  Prefer an explicit operator-provided path, then use the
    pre-provisioned Codex runtime, and finally the repository test runtime.
    This never installs or downloads a dependency.
    """

    configured = bootstrap.playwright_module_path if bootstrap is not None else None
    if configured:
        return configured

    repo_root = Path(__file__).resolve().parents[2]
    candidates = (
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules",
        repo_root / "release-pipeline" / "node_modules",
    )
    for candidate in candidates:
        if (candidate / "playwright").is_dir():
            return str(candidate)
    return None


def _helper_path() -> Path:
    path = Path(__file__).with_name("browser_host.js")
    if not path.is_file():
        raise RealBrowserError("real_browser_helper_missing")
    return path


def _session_helper_path() -> Path:
    path = Path(__file__).with_name("browser_session_host.js")
    if not path.is_file():
        raise RealBrowserError("real_browser_session_helper_missing")
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


def run_real_flow(
    *,
    url: str,
    viewport: Mapping[str, Any],
    steps: list[Mapping[str, Any]],
    run_id: str,
    timeout_ms: int,
    bootstrap: BrowserBootstrap | None = None,
) -> dict[str, Any]:
    """Run one real browser flow; never substitutes synthetic evidence."""

    selected_bootstrap = bootstrap or BrowserBootstrap.synthetic()
    if not selected_bootstrap.enabled:
        raise RealBrowserError("real_browser_not_enabled")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 128:
        raise RealBrowserError("real_browser_run_id_invalid")
    if not isinstance(timeout_ms, int) or not 1000 <= timeout_ms <= 1_800_000:
        raise RealBrowserError("real_browser_timeout_invalid")
    request = {
        "command": "run",
        "run_id": run_id,
        "url": _safe_url(url, selected_bootstrap.policy),
        "viewport": dict(viewport),
        "steps": [dict(step) for step in steps],
        "policy": selected_bootstrap.policy.to_payload(),
    }
    env = os.environ.copy()
    module_path = _playwright_module_path(selected_bootstrap)
    if module_path:
        env["NODE_PATH"] = module_path + os.pathsep + env.get("NODE_PATH", "")
    try:
        completed = subprocess.run(
            [_node_command(selected_bootstrap), str(_helper_path())],
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


def _validate_session_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RealBrowserError("real_browser_session_response_invalid")
    if value.get("status") not in {"PASS", "FAIL"} or not isinstance(value.get("error_class", ""), str):
        raise RealBrowserError("real_browser_session_response_invalid")
    if not isinstance(value.get("state", "unknown"), str):
        raise RealBrowserError("real_browser_session_response_invalid")
    artifacts: list[dict[str, str]] = []
    images: list[dict[str, str]] = []
    for raw in value.get("artifacts") or []:
        if not isinstance(raw, Mapping):
            raise RealBrowserError("real_browser_artifact_invalid")
        public, image = _validate_artifact(raw)
        artifacts.append(public)
        if image:
            images.append(image)
    result = {
        "status": value["status"],
        "error_class": str(value.get("error_class", ""))[:120],
        "state": str(value.get("state", "unknown"))[:200],
        "artifacts": artifacts,
        "images": images,
    }
    action = value.get("action")
    if action is not None:
        if not isinstance(action, Mapping) or not {"expected", "actual", "status", "before_state", "after_state"}.issubset(action):
            raise RealBrowserError("real_browser_action_invalid")
        if action["status"] not in {"pass", "fail", "blocked"}:
            raise RealBrowserError("real_browser_action_invalid")
        result["action"] = {
            "expected": str(action["expected"])[:200],
            "actual": str(action["actual"])[:200],
            "status": action["status"],
            "before_state": str(action["before_state"])[:200],
            "after_state": str(action["after_state"])[:200],
        }
    return result


class PersistentRealBrowser:
    """One bounded in-memory page for an observe/decide/act/verify loop."""

    def __init__(
        self,
        *,
        url: str,
        viewport: Mapping[str, Any],
        run_id: str,
        timeout_ms: int,
        bootstrap: BrowserBootstrap | None = None,
    ) -> None:
        selected_bootstrap = bootstrap or BrowserBootstrap.synthetic()
        if not selected_bootstrap.enabled:
            raise RealBrowserError("real_browser_not_enabled")
        if not isinstance(run_id, str) or not run_id or len(run_id) > 128:
            raise RealBrowserError("real_browser_run_id_invalid")
        if not isinstance(timeout_ms, int) or not 1000 <= timeout_ms <= 1_800_000:
            raise RealBrowserError("real_browser_timeout_invalid")
        env = os.environ.copy()
        module_path = _playwright_module_path(selected_bootstrap)
        if module_path:
            env["NODE_PATH"] = module_path + os.pathsep + env.get("NODE_PATH", "")
        try:
            self._process = subprocess.Popen(
                [_node_command(selected_bootstrap), str(_session_helper_path())],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                env=env,
                bufsize=1,
            )
        except OSError as exc:
            raise RealBrowserError("real_browser_process_failed") from exc
        self._responses: queue.Queue[str] = queue.Queue()
        self._reader = threading.Thread(target=self._read_responses, daemon=True)
        self._reader.start()
        self._timeout_seconds = (timeout_ms / 1000) + 15
        try:
            self._send({
                "command": "init",
                "run_id": run_id,
                "url": _safe_url(url, selected_bootstrap.policy),
                "viewport": dict(viewport),
                "policy": selected_bootstrap.policy.to_payload(),
            })
        except Exception:
            self.close()
            raise

    def _read_responses(self) -> None:
        stdout = self._process.stdout
        if stdout is None:
            return
        for line in stdout:
            self._responses.put(line)

    def _send(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if self._process.poll() is not None or self._process.stdin is None:
            raise RealBrowserError("real_browser_session_closed")
        try:
            self._process.stdin.write(json.dumps(dict(request), ensure_ascii=False, separators=(",", ":")) + "\n")
            self._process.stdin.flush()
            line = self._responses.get(timeout=self._timeout_seconds)
        except queue.Empty as exc:
            self.close()
            raise RealBrowserError("real_browser_timeout") from exc
        except (BrokenPipeError, OSError) as exc:
            self.close()
            raise RealBrowserError("real_browser_process_failed") from exc
        try:
            raw = json.loads(line.strip())
        except json.JSONDecodeError as exc:
            self.close()
            raise RealBrowserError("real_browser_session_response_invalid") from exc
        return _validate_session_response(raw)

    def observe(self) -> dict[str, Any]:
        response = self._send({"command": "observe"})
        if response["status"] != "PASS":
            raise RealBrowserError(response["error_class"] or "real_browser_observe_failed")
        return response

    def act(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        response = self._send({"command": "act", "step": dict(decision)})
        if response["status"] != "PASS":
            raise RealBrowserError(response["error_class"] or "real_browser_action_failed")
        return response

    def close(self) -> None:
        process = getattr(self, "_process", None)
        if process is None:
            return
        try:
            if process.poll() is None and process.stdin is not None:
                process.stdin.write('{"command":"close"}\n')
                process.stdin.flush()
                process.wait(timeout=5)
        except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
        finally:
            if process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    pass
            try:
                if process.stdin is not None:
                    process.stdin.close()
                if process.stdout is not None:
                    process.stdout.close()
            except OSError:
                pass
            reader = getattr(self, "_reader", None)
            if reader is not None:
                reader.join(timeout=1)
