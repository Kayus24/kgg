#!/usr/bin/env python3
"""Contract tests for the semantic UI-Lab browser runner."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

import kgg_ui_lab_browser as browser
import kgg_ui_lab_contract as contract


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 14, 8, 5, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


def runner(*capabilities: str) -> dict:
    return {
        "runner_id": "runner-browser-001",
        "version": "1.0.0",
        "browser_revision": "chromium-140",
        "capabilities": list(capabilities),
    }


def flow() -> dict:
    return {
        "name": "admin-start-state",
        "version": "1.0.0",
        "steps": [
            {"operation": "read_state", "label": "admin-ready"},
            {"operation": "capture_screenshot", "label": "baseline-screen"},
        ],
    }


def observation(step: dict) -> dict:
    if step["operation"] == "capture_screenshot":
        return {
            "expected": "baseline-visible",
            "actual": "baseline-visible",
            "status": "pass",
            "artifacts": [{"id": "shot-001", "kind": "screenshot", "ref": "artifacts/baseline.png", "sha256": "c" * 64}],
        }
    return {"expected": "admin-ready", "actual": "admin-ready", "status": "pass", "artifacts": []}


class KggUiLabBrowserTests(unittest.TestCase):
    def test_semantic_flow_passes_and_captures_artifact(self) -> None:
        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows", "capture"), observation, now=Clock())
        result = run.run(flow())
        self.assertEqual(result["schema"], browser.BROWSER_RUN_SCHEMA)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["steps"][1]["artifact_refs"], ["shot-001"])

    def test_selector_or_raw_qr_content_is_rejected(self) -> None:
        unsafe = dict(flow(), steps=[{"operation": "click", "label": "secret-selector"}])
        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows"), observation, now=Clock())
        with self.assertRaisesRegex(browser.BrowserContractError, "sensitive"):
            run.run(unsafe)

    def test_capture_requires_capture_capability_and_artifact(self) -> None:
        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows"), observation, now=Clock())
        with self.assertRaisesRegex(contract.ContractError, "capability_missing"):
            run.run(flow())

        no_artifact = lambda step: {"expected": "screen", "actual": "screen", "status": "pass", "artifacts": []}
        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows", "capture"), no_artifact, now=Clock())
        result = run.run(flow())
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error_class"], "runner_unavailable")

    def test_tap_and_wait_are_semantic_and_wait_is_bounded(self) -> None:
        seen: list[dict] = []

        def observe(step: dict) -> dict:
            seen.append(dict(step))
            return {"expected": "ready", "actual": "ready", "status": "pass", "artifacts": []}

        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows"), observe, now=Clock())
        result = run.run(
            {
                "name": "tap-wait-flow",
                "version": "1.0.0",
                "steps": [
                    {"operation": "tap", "label": "tablet-control"},
                    {"operation": "wait", "label": "wait-short", "timeout_ms": 1500},
                ],
            }
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(seen[1]["timeout_ms"], 1500)

        with self.assertRaisesRegex(browser.BrowserContractError, "wait_timeout"):
            run.run(
                {
                    "name": "tap-wait-flow",
                    "version": "1.0.1",
                    "steps": [{"operation": "wait", "label": "wait-too-long", "timeout_ms": 5001}],
                }
            )

    def test_runner_exception_is_bounded_without_raw_error(self) -> None:
        def fail(_: dict) -> dict:
            raise TimeoutError("private browser details must not escape")

        run = browser.SemanticBrowserRunner(runner("browser", "quick_flows"), fail, now=Clock())
        result = run.run({"name": "read-state", "version": "1.0.0", "steps": [{"operation": "read_state", "label": "admin-ready"}]})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error_class"], "network_timeout")
        self.assertNotIn("private", str(result))


if __name__ == "__main__":
    unittest.main()
