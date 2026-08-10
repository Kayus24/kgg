#!/usr/bin/env python3
"""Track blind Repair-Lab attempts and enforce stop/two-round acceptance rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FAILURE_CLASSES = {
    "payload_schema",
    "workflow_dispatch",
    "ci_tooling",
    "browser_runtime",
    "repair_logic",
    "false_claim",
    "isolation_breach",
    "source_drift",
}
REQUIRED_PER_ROUND = 10
REQUIRED_GREEN_ROUNDS = 2
MAX_SAME_FAILURE = 3


class StabilizeError(RuntimeError):
    pass


def empty_state() -> dict[str, Any]:
    return {"schema": 1, "model": "", "resource_manifest_sha256": "", "attempts": [], "rounds": {}}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise StabilizeError(f"cannot read state: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise StabilizeError("invalid Repair-Lab state schema")
    return value


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def failure_streak(state: dict[str, Any], challenge_id: str, failure_class: str) -> int:
    streak = 0
    for attempt in reversed(state.get("attempts", [])):
        if attempt.get("challenge_id") != challenge_id:
            continue
        if attempt.get("status") == "PASS":
            break
        if attempt.get("failure_class") != failure_class:
            break
        streak += 1
    return streak


def record_attempt(
    state: dict[str, Any],
    *,
    round_id: str,
    challenge_id: str,
    status: str,
    failure_class: str,
    run_id: str,
    model: str,
    resource_hash: str,
    notes: str,
) -> dict[str, Any]:
    status = status.upper()
    if status not in {"PASS", "FAIL"}:
        raise StabilizeError("status must be PASS or FAIL")
    if status == "FAIL" and failure_class not in FAILURE_CLASSES:
        raise StabilizeError(f"unknown failure class: {failure_class}")
    if status == "PASS" and failure_class:
        raise StabilizeError("PASS must not have a failure class")
    if state.get("model") and state["model"] != model:
        raise StabilizeError("model changed inside the two-round acceptance window")
    if state.get("resource_manifest_sha256") and state["resource_manifest_sha256"] != resource_hash:
        raise StabilizeError("resource manifest changed; restart acceptance rounds from zero")
    state["model"] = model
    state["resource_manifest_sha256"] = resource_hash
    attempt = {
        "round_id": round_id,
        "challenge_id": challenge_id,
        "status": status,
        "failure_class": failure_class,
        "run_id": run_id,
        "notes": notes[:500],
    }
    state.setdefault("attempts", []).append(attempt)
    round_state = state.setdefault("rounds", {}).setdefault(round_id, {"passed": [], "failed": [], "complete": False})
    if status == "PASS":
        if challenge_id not in round_state["passed"]:
            round_state["passed"].append(challenge_id)
        round_state["failed"] = [item for item in round_state["failed"] if item.get("challenge_id") != challenge_id]
    else:
        round_state["failed"].append({"challenge_id": challenge_id, "failure_class": failure_class, "run_id": run_id})
    round_state["complete"] = len(set(round_state["passed"])) == REQUIRED_PER_ROUND and not round_state["failed"]
    streak = failure_streak(state, challenge_id, failure_class) if status == "FAIL" else 0
    return {
        "status": "STOP_ALTERNATIVE_REQUIRED" if streak >= MAX_SAME_FAILURE else "RECORDED",
        "failure_streak": streak,
        "round_complete": round_state["complete"],
    }


def acceptance(state: dict[str, Any]) -> dict[str, Any]:
    complete = [round_id for round_id, value in state.get("rounds", {}).items() if value.get("complete")]
    stopped = []
    for attempt in state.get("attempts", []):
        if attempt.get("status") != "FAIL":
            continue
        streak = failure_streak(state, str(attempt.get("challenge_id")), str(attempt.get("failure_class")))
        if streak >= MAX_SAME_FAILURE:
            stopped.append({"challenge_id": attempt.get("challenge_id"), "failure_class": attempt.get("failure_class"), "streak": streak})
    accepted = len(complete) >= REQUIRED_GREEN_ROUNDS and not stopped
    return {
        "status": "PASS" if accepted else ("STOP_ALTERNATIVE_REQUIRED" if stopped else "PENDING"),
        "green_rounds": len(complete),
        "required_green_rounds": REQUIRED_GREEN_ROUNDS,
        "complete_round_ids": complete,
        "stopped": stopped,
        "model": state.get("model", ""),
        "resource_manifest_sha256": state.get("resource_manifest_sha256", ""),
    }


def self_test() -> None:
    state = empty_state()
    for round_number in (1, 2):
        round_id = f"self-round-{round_number}"
        for index in range(REQUIRED_PER_ROUND):
            result = record_attempt(
                state,
                round_id=round_id,
                challenge_id=f"repair-{round_number:02d}{index:014d}"[-23:],
                status="PASS",
                failure_class="",
                run_id=str(round_number * 100 + index),
                model="GPT-5.6 Thinking",
                resource_hash="a" * 64,
                notes="control",
            )
        if not result["round_complete"]:
            raise StabilizeError("self-test round did not complete")
    if acceptance(state)["status"] != "PASS":
        raise StabilizeError("two complete rounds must pass")
    failing = empty_state()
    for index in range(3):
        result = record_attempt(
            failing,
            round_id="self-fail",
            challenge_id="repair-0123456789abcdef",
            status="FAIL",
            failure_class="repair_logic",
            run_id=str(index),
            model="GPT-5.6 Thinking",
            resource_hash="b" * 64,
            notes="same failure",
        )
    if result["status"] != "STOP_ALTERNATIVE_REQUIRED":
        raise StabilizeError("third identical failure must stop the cycle")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--record", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--round-id")
    parser.add_argument("--challenge-id")
    parser.add_argument("--status", choices=["PASS", "FAIL"])
    parser.add_argument("--failure-class", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--model", default="GPT-5.6 Thinking")
    parser.add_argument("--resource-hash", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print(json.dumps({"status": "PASS", "test": "kgg_gpt_repair_stabilize"}))
            return 0
        if not args.state:
            raise StabilizeError("--state is required")
        state = load_state(args.state)
        if args.record:
            if not all([args.round_id, args.challenge_id, args.status, args.run_id, args.resource_hash]):
                raise StabilizeError("record requires round, challenge, status, run, model and resource hash")
            result = record_attempt(
                state,
                round_id=args.round_id,
                challenge_id=args.challenge_id,
                status=args.status,
                failure_class=args.failure_class,
                run_id=args.run_id,
                model=args.model,
                resource_hash=args.resource_hash,
                notes=args.notes,
            )
            write_state(args.state, state)
            print(json.dumps({**result, "acceptance": acceptance(state)}, ensure_ascii=False, indent=2))
            return 2 if result["status"] == "STOP_ALTERNATIVE_REQUIRED" else 0
        result = acceptance(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
