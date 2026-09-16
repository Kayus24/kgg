#!/usr/bin/env python3
"""Semantic, side-effect-injected browser runner for the UI Lab.

The runner knows Quick-Flow operations and evidence shape, but it never owns
browser selectors, shell access, or network credentials. A trusted host may
inject a semantic observer; tests use a synthetic observer.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable, Mapping

import kgg_ui_lab_contract as contract
import kgg_ui_lab_runtime as runtime


BROWSER_RUN_SCHEMA = "kgg-ui-lab/browser-run/v1"
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$")
_ARTIFACT_KINDS = frozenset({"screenshot", "capture", "result", "metadata", "dom-snapshot"})
_SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "browser_output")


class BrowserContractError(ValueError):
    """Raised when a semantic browser runner result is unsafe or malformed."""


def _fail(code: str, detail: str = "") -> None:
    raise BrowserContractError(code if not detail else f"{code}: {detail}")


def _safe_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 200 or not _TEXT_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    lowered = value.casefold()
    if any(token in lowered for token in _SENSITIVE) or re.search(r"\btoken\b", lowered):
        _fail("sensitive_field", label)
    return value


def _artifact(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"id", "kind", "ref", "sha256"}:
        _fail("artifact_invalid")
    artifact_id = value["id"]
    if not isinstance(artifact_id, str) or not _ID_RE.fullmatch(artifact_id):
        _fail("artifact_id_invalid")
    kind = value["kind"]
    if not isinstance(kind, str) or kind not in _ARTIFACT_KINDS:
        _fail("artifact_kind_invalid")
    ref = value["ref"]
    if not isinstance(ref, str) or not 1 <= len(ref) <= 512 or any(token in ref.casefold() for token in _SENSITIVE):
        _fail("sensitive_field", "artifact.ref")
    digest = value["sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        _fail("artifact_sha256_invalid")
    return {"id": artifact_id, "kind": kind, "ref": ref, "sha256": digest}


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class SemanticBrowserRunner:
    """Execute a registered semantic flow through an injected observer."""

    def __init__(
        self,
        runner: Mapping[str, Any],
        observer: Callable[[Mapping[str, str]], Mapping[str, Any]],
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.runner = contract.validate_runner(runner)
        if not callable(observer):
            raise BrowserContractError("observer_invalid")
        self.observer = observer
        self.now = now or (lambda: datetime.now(timezone.utc))

    def run(self, flow: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(flow, Mapping) or set(flow) != {"name", "version", "steps"}:
            _fail("quick_flow_invalid")
        if not isinstance(flow["name"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", flow["name"]):
            _fail("quick_flow_invalid", "name")
        if not isinstance(flow["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", flow["version"]):
            _fail("quick_flow_invalid", "version")
        steps = flow["steps"]
        if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
            _fail("quick_flow_invalid", "steps")
        contract.require_capability({"runner": self.runner}, "browser")
        contract.require_capability({"runner": self.runner}, "quick_flows")
        if any(isinstance(step, Mapping) and step.get("operation") == "capture_screenshot" for step in steps):
            contract.require_capability({"runner": self.runner}, "capture")

        started = self.now()
        normalized_steps: list[dict[str, Any]] = []
        artifacts: list[dict[str, str]] = []
        seen_artifacts: set[str] = set()
        failure_class = ""
        result_status = "PASS"
        for sequence, raw_step in enumerate(steps, start=1):
            if not isinstance(raw_step, Mapping) or not {"operation", "label"}.issubset(set(raw_step)):
                _fail("quick_flow_step_invalid")
            operation, label = raw_step["operation"], raw_step["label"]
            if not isinstance(operation, str) or operation not in {
                "read_state",
                "click",
                "tap",
                "type",
                "scroll",
                "reload",
                "back",
                "wait",
                "capture_screenshot",
            }:
                _fail("quick_flow_step_invalid", "operation")
            allowed_keys = {"operation", "label", "timeout_ms"} if operation == "wait" else {"operation", "label"}
            if set(raw_step) - allowed_keys:
                _fail("quick_flow_step_invalid", "fields")
            label = _safe_text(label, "step_label")
            wait_timeout_ms = 1000
            if operation == "wait" and "timeout_ms" in raw_step:
                wait_timeout_ms = raw_step["timeout_ms"]
                if (
                    not isinstance(wait_timeout_ms, int)
                    or isinstance(wait_timeout_ms, bool)
                    or not 1 <= wait_timeout_ms <= contract.MAX_WAIT_MS
                ):
                    _fail("quick_flow_step_invalid", "wait_timeout")
            try:
                observer_step: dict[str, Any] = {"operation": operation, "label": label}
                if operation == "wait":
                    # The host receives an explicit ceiling; the runner itself
                    # does not sleep or expose an unbounded wait primitive.
                    observer_step["timeout_ms"] = wait_timeout_ms
                observation = self.observer(observer_step)
                if not isinstance(observation, Mapping) or set(observation) != {"expected", "actual", "status", "artifacts"}:
                    _fail("observation_invalid")
                expected = _safe_text(observation["expected"], "expected")
                actual = _safe_text(observation["actual"], "actual")
                status = observation["status"]
                if status not in {"pass", "fail", "blocked"}:
                    _fail("observation_status_invalid")
                raw_artifacts = observation["artifacts"]
                if not isinstance(raw_artifacts, list) or len(raw_artifacts) > 10:
                    _fail("observation_artifacts_invalid")
                step_artifacts = [_artifact(item) for item in raw_artifacts]
            except BrowserContractError:
                raise
            except Exception as exc:  # noqa: BLE001 - public result is deliberately generic
                expected, actual, status, step_artifacts = label, "runner-error", "blocked", []
                failure_class = runtime.classify_failure("runner", exc.__class__.__name__.replace("Error", " error"))
                if failure_class == "unknown":
                    failure_class = "runner_unavailable"

            if any(item["id"] in seen_artifacts for item in step_artifacts):
                _fail("artifact_duplicate")
            seen_artifacts.update(item["id"] for item in step_artifacts)
            artifacts.extend(step_artifacts)
            refs = [item["id"] for item in step_artifacts]
            normalized_steps.append(
                {
                    "sequence": sequence,
                    "label": label,
                    "expected": expected,
                    "actual": actual,
                    "status": status,
                    "artifact_refs": refs,
                }
            )
            if operation == "capture_screenshot" and not step_artifacts:
                status = "blocked"
                normalized_steps[-1]["status"] = status
                failure_class = "runner_unavailable"
            if status != "pass":
                result_status = "BLOCKED" if status == "blocked" else "FAIL"
                if not failure_class:
                    failure_class = runtime.classify_failure(operation, actual)
                break

        ended = self.now()
        return {
            "schema": BROWSER_RUN_SCHEMA,
            "runner_id": self.runner["runner_id"],
            "runner_version": self.runner["version"],
            "flow_name": flow["name"],
            "flow_version": flow["version"],
            "started_at": _timestamp(started),
            "ended_at": _timestamp(ended),
            "status": result_status,
            "error_class": failure_class,
            "steps": normalized_steps,
            "artifacts": artifacts,
        }
