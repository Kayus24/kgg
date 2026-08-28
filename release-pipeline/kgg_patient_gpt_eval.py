#!/usr/bin/env python3
"""Static acceptance evaluation for the KGG patient Custom GPT profile."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvalError(RuntimeError):
    pass


def require(text: str, label: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise EvalError(f"{label} is missing: {', '.join(missing)}")


def main() -> int:
    try:
        bootstrap = (ROOT / "docs/kgg-patient-custom-gpt-editor-bootstrap.md").read_text(encoding="utf-8")
        playbook = (ROOT / "docs/kgg-patient-custom-gpt-playbook.md").read_text(encoding="utf-8")
        prompts = (ROOT / "docs/kgg-patient-custom-gpt-test-prompts.md").read_text(encoding="utf-8")
        brain_relay = (ROOT / "docs/kgg-brain-relay-worker-workflow.md").read_text(encoding="utf-8")
        raw_action = (ROOT / "docs/kgg-patient-custom-gpt-action-openapi.yaml").read_text(encoding="utf-8")
        api_action = (ROOT / "docs/kgg-patient-custom-gpt-action-api-openapi.yaml").read_text(encoding="utf-8")
        snapshot = json.loads(
            (ROOT / "docs/kgg-patient-custom-gpt-editor-snapshot.json").read_text(encoding="utf-8")
        )

        require(
            bootstrap,
            "patient editor bootstrap",
            (
                "getKggPatientResourceManifest",
                "getKggPatientContext",
                "getKggPatientPlaybook",
                "validate_only",
                "publish_preview",
                "publish_patient_live",
                "stale_base",
                "human_preview_fail",
                "risk_class=interface",
                '"type": "replace_exact"',
                "exakte Fuenf-Felder-Form",
                "vollstaendige ausgeschriebene `https://`-Klartext-URLs",
                "Leere oder nur beschriftete Markdown-Links sind kein Nachweis",
                "patient-v5",
                "Gut für PAT live",
                "getKggAgentCoordinationIndex",
                "submitKggAgentCoordinationEvent",
                "coordination_unavailable",
                "isolierten visuellen Patient-UI-Patch",
                "patient-start-scan.js",
                "patient-camera",
                "patient-scan",
                "STANDALONE",
                "WORKFLOW",
                "WORKFLOW_BLOCKED",
                "kgg-custom-gpt-workflow-start/v1",
            ),
        )
        require(
            playbook,
            "patient playbook",
            (
                "base_sha",
                "old_sha256",
                "replace_exact",
                "synthet",
                "Environment",
                "service-worker.js",
                "Coordination-v2",
                "getKggAgentCoordinationBridgeTask",
                "coordination-bridge/tasks/{task_id}.json",
            ),
        )
        require(
            brain_relay,
            "Brain-Relay-Worker workflow",
            (
                "Luna Manager",
                "Lead-GPT",
                "Luna-Max-Worker",
                "hoechstens vier",
                "L0-L3",
                "coordination-v2",
                "Neuer Chat",
                "RETIRED",
                "SLEEPING",
                "Abschluss- und Blockerbericht",
            ),
        )
        require(
            prompts,
            "patient prompt suite",
            (
                "Nur analysieren",
                "direkt live",
                "APP_VERSION",
                "echten Patientenlink",
                "Main hat sich",
                "Browser-Test ist fehlgeschlagen",
                "Scanner zoomt die Kamera",
                "Koordinationsqueue liefert 404",
                "lass patient-scan aus den Tests weg",
                "dual-mode-activation",
                "STANDALONE",
                "WORKFLOW_BLOCKED",
                "kgg-custom-gpt-workflow-start/v1",
            ),
        )
        require(
            raw_action,
            "patient raw Action",
            (
                "getKggPatientResourceManifest",
                "getKggPatientSourceChunk",
                "getKggPatientPreviewMeta",
            ),
        )
        require(
            api_action,
            "patient API Action",
            (
                "submitKggPatientPreviewGate",
                "submitKggPatientMainGate",
                "getKggPatientMainCommit",
                "getKggPatientPreviewGateJobs",
                "getKggMemoryIndex",
                "submitKggMemoryUpdate",
                "getKggAgentCoordinationIndex",
                "submitKggAgentCoordinationEvent",
                "getKggAgentCoordinationBridgeTask",
                "coordination-bridge/tasks/{task_id}.json",
            ),
        )
        for label, schema in (("raw", raw_action), ("api", api_action)):
            count = len(re.findall(r"^\s+operationId:\s+\S+\s*$", schema, re.MULTILINE))
            if count > 30:
                raise EvalError(f"{label} patient Action exceeds 30 operations")
        if snapshot.get("visibility") != "private":
            raise EvalError("patient GPT snapshot must remain private")
        if snapshot.get("capabilities", {}).get("apps"):
            raise EvalError("patient GPT Apps must be disabled while Actions are enabled")
        if snapshot.get("capabilities", {}).get("imageGeneration"):
            raise EvalError("patient GPT Image Generation must remain disabled")

        print(
            json.dumps(
                {
                    "status": "PASS",
                    "profile": "patientProduction",
                    "promptCases": 23,
                    "rawOperations": len(re.findall(r"^\s+operationId:", raw_action, re.MULTILINE)),
                    "apiOperations": len(re.findall(r"^\s+operationId:", api_action, re.MULTILINE)),
                }
            )
        )
        return 0
    except (OSError, json.JSONDecodeError, EvalError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
