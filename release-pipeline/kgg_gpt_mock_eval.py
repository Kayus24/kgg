#!/usr/bin/env python3
"""Mock-app evaluator for modular KGG Custom GPT payloads.

The mock deliberately removes one harmless app function. A GPT payload passes
only if it uses the modular v2 contract and restores the missing behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))
import kgg_gpt_write_gate as write_gate  # noqa: E402


PATCH_ID = "mock-v001-restore-scale-reset"
MOCK_TEST = "python release-pipeline\\kgg_gpt_mock_eval.py --payload-file <payload.json>"
CRITICAL_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical"
UI_REGRESSION_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"


class MockEvalError(RuntimeError):
    pass


def sample_good_payload() -> dict[str, Any]:
    return {
        "request_id": "mockup-restore-scale-reset",
        "title": "Mockup scaler reset restore",
        "summary": "Restore the removed resetScale behavior in the mock app.",
        "version_slug": "mockup-restore-scale-reset",
        "touched_areas": ["Admin-Web UI"],
        "required_tests": [
            MOCK_TEST,
            CRITICAL_TEST,
            UI_REGRESSION_TEST,
        ],
        "patch_content": (
            "<script id=\"__KGG_PATCH_ID__\">\n"
            "(function(){\n"
            "  \"use strict\";\n"
            "  const PATCH_ID=\"__KGG_PATCH_ID__\";\n"
            "  window.KGGMock=window.KGGMock||{};\n"
            "  window.KGGMock.resetScale=function(){\n"
            "    this.scale=1;\n"
            "    if(typeof this.updateLabel===\"function\") this.updateLabel();\n"
            "  };\n"
            "  window.KGG_PATCHES=window.KGG_PATCHES||{};\n"
            "  window.KGG_PATCHES[PATCH_ID]={installed:true, restores:\"mock-reset-scale\"};\n"
            "})();\n"
            "</script>\n"
        ),
    }


def sample_bad_payload() -> dict[str, Any]:
    payload = sample_good_payload()
    payload["request_id"] = "mockup-bad-no-reset"
    payload["patch_content"] = (
        "<script id=\"__KGG_PATCH_ID__\">\n"
        "(function(){\"use strict\";window.KGG_PATCHES=window.KGG_PATCHES||{};})();\n"
        "</script>\n"
    )
    return payload


def load_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        parsed = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        raise MockEvalError(f"cannot read payload JSON: {exc}") from exc
    validated = write_gate.validate_payload(json.dumps(parsed, ensure_ascii=False))
    return validated


def script_bodies(patch_content: str) -> list[str]:
    bodies = re.findall(r"<script\b[^>]*>(.*?)</script>", patch_content, flags=re.IGNORECASE | re.DOTALL)
    if not bodies:
        raise MockEvalError("mock payload must provide executable script content")
    return [body.replace("__KGG_PATCH_ID__", PATCH_ID) for body in bodies]


def run_node_probe(script_parts: list[str]) -> dict[str, Any]:
    probe = {
        "base": (
            "global.window={};\n"
            "const elements={};\n"
            "function element(id){\n"
            "  if(!elements[id]){\n"
            "    elements[id]={id, textContent:'', listeners:{}, addEventListener(type,fn){this.listeners[type]=fn;}, click(){if(this.listeners.click)this.listeners.click({type:'click'});}};\n"
            "  }\n"
            "  return elements[id];\n"
            "}\n"
            "global.document={getElementById:element};\n"
            "window.KGGMock={\n"
            "  scale:1,\n"
            "  updateLabel(){document.getElementById('scaleLabel').textContent=Math.round(this.scale*100)+'%';},\n"
            "  setScale(value){this.scale=value;this.updateLabel();}\n"
            "};\n"
            "document.getElementById('scalePlus').addEventListener('click',()=>window.KGGMock.setScale(1.25));\n"
            "document.getElementById('scaleMinus').addEventListener('click',()=>window.KGGMock.setScale(0.75));\n"
            "document.getElementById('scaleReset').addEventListener('click',()=>{\n"
            "  if(typeof window.KGGMock.resetScale!=='function') throw new Error('resetScale missing');\n"
            "  window.KGGMock.resetScale();\n"
            "});\n"
            "window.KGGMock.updateLabel();\n"
        ),
        "patches": script_parts,
        "assertions": (
            "document.getElementById('scalePlus').click();\n"
            "if(window.KGGMock.scale!==1.25) throw new Error('plus no longer changes scale');\n"
            "document.getElementById('scaleReset').click();\n"
            "if(window.KGGMock.scale!==1) throw new Error('reset did not restore scale=1');\n"
            "if(document.getElementById('scaleLabel').textContent!=='100%') throw new Error('reset label not restored');\n"
            f"if(!window.KGG_PATCHES||!window.KGG_PATCHES['{PATCH_ID}']) throw new Error('patch registration missing');\n"
            "console.log(JSON.stringify({status:'PASS', scale:window.KGGMock.scale, label:document.getElementById('scaleLabel').textContent}));\n"
        ),
    }
    node_program = (
        "const probe=JSON.parse(process.argv[1]);\n"
        "eval(probe.base);\n"
        "for(const part of probe.patches) eval(part);\n"
        "eval(probe.assertions);\n"
    )
    proc = subprocess.run(
        ["node", "-e", node_program, json.dumps(probe)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        raise MockEvalError(output or "node mock probe failed")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        raise MockEvalError(f"mock probe did not return JSON: {proc.stdout}") from exc


def evaluate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    tests = {str(item).strip() for item in payload.get("required_tests", [])}
    missing_tests = [command for command in (MOCK_TEST, CRITICAL_TEST, UI_REGRESSION_TEST) if command not in tests]
    if missing_tests:
        raise MockEvalError(f"mock payload is missing exact required_tests command(s): {missing_tests}")
    content = str(payload.get("patch_content") or "")
    scripts = script_bodies(content)
    result = run_node_probe(scripts)
    return {
        "status": "PASS",
        "request_id": payload.get("request_id"),
        "patch_id": PATCH_ID,
        "visible_marker": result.get("label"),
        "restored_behavior": "scale reset",
    }


def run_self_test() -> None:
    good = evaluate_payload(write_gate.validate_payload(json.dumps(sample_good_payload(), ensure_ascii=False)))
    if good.get("status") != "PASS":
        raise MockEvalError("good mock payload did not pass")
    try:
        evaluate_payload(write_gate.validate_payload(json.dumps(sample_bad_payload(), ensure_ascii=False)))
    except MockEvalError:
        pass
    else:
        raise MockEvalError("bad mock payload unexpectedly passed")
    shorthand = sample_good_payload()
    shorthand["required_tests"] = ["critical", "ui-stability regression", MOCK_TEST]
    try:
        evaluate_payload(write_gate.validate_payload(json.dumps(shorthand, ensure_ascii=False)))
    except MockEvalError:
        return
    raise MockEvalError("mock payload with shorthand tests unexpectedly passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a modular GPT payload against a broken mock KGG app.")
    parser.add_argument("--payload-file", type=Path, help="JSON file with a modular v2 GPT payload.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in good/bad mock payload checks.")
    parser.add_argument("--print-sample", action="store_true", help="Print a sample passing payload.")
    args = parser.parse_args()

    try:
        if args.print_sample:
            print(json.dumps(sample_good_payload(), ensure_ascii=False, indent=2))
            return 0
        if args.self_test:
            run_self_test()
            print(json.dumps({"status": "PASS", "test": "kgg_gpt_mock_eval_self_test"}, ensure_ascii=False))
            return 0
        if not args.payload_file:
            raise MockEvalError("--payload-file or --self-test is required")
        payload = load_payload(args.payload_file)
        print(json.dumps(evaluate_payload(payload), ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
