#!/usr/bin/env python3
"""Track two six-case natural UI rounds and enforce KGG acceptance rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FAILURE_CLASSES = {
    "natural_language",
    "payload_schema",
    "workflow_dispatch",
    "ci_tooling",
    "ui_logic",
    "false_claim",
    "isolation_breach",
    "challenge_integrity",
    "evaluator_failure",
}
REQUIRED_PER_ROUND = 6
REQUIRED_GREEN_ROUNDS = 2
MIN_FIRST_ATTEMPT_PASSES = 10
MAX_ATTEMPTS_TO_PASS = 2
MAX_SAME_FAILURE = 3


class NaturalStabilizeError(RuntimeError):
    pass


def empty_state() -> dict[str, Any]:
    return {
        "schema": 1,
        "model": "",
        "resource_manifest_sha256": "",
        "attempts": [],
        "rounds": {},
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise NaturalStabilizeError(f"cannot read state: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise NaturalStabilizeError("invalid natural UI state schema")
    return value


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def challenge_attempts(state: dict[str, Any], challenge_id: str) -> list[dict[str, Any]]:
    return [
        attempt
        for attempt in state.get("attempts", [])
        if attempt.get("challenge_id") == challenge_id
    ]


def failure_streak(state: dict[str, Any], challenge_id: str, failure_class: str) -> int:
    streak = 0
    for attempt in reversed(challenge_attempts(state, challenge_id)):
        if attempt.get("status") == "PASS":
            break
        if attempt.get("failure_class") != failure_class:
            break
        streak += 1
    return streak


def refresh_round(state: dict[str, Any], round_id: str) -> None:
    round_state = state.setdefault("rounds", {}).setdefault(
        round_id,
        {"challenges": {}, "complete": False},
    )
    passed = [
        challenge
        for challenge in round_state["challenges"].values()
        if challenge.get("status") == "PASS"
    ]
    round_state["complete"] = (
        len(passed) == REQUIRED_PER_ROUND
        and all(int(challenge.get("attempts", 0)) <= MAX_ATTEMPTS_TO_PASS for challenge in passed)
    )


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
        raise NaturalStabilizeError("status must be PASS or FAIL")
    if status == "FAIL" and failure_class not in FAILURE_CLASSES:
        raise NaturalStabilizeError(f"unknown failure class: {failure_class}")
    if status == "PASS" and failure_class:
        raise NaturalStabilizeError("PASS must not have a failure class")
    if state.get("model") and state["model"] != model:
        raise NaturalStabilizeError("model changed inside the acceptance window")
    if (
        state.get("resource_manifest_sha256")
        and state["resource_manifest_sha256"] != resource_hash
    ):
        raise NaturalStabilizeError(
            "resource manifest changed; restart both natural UI rounds"
        )
    state["model"] = model
    state["resource_manifest_sha256"] = resource_hash
    attempt_number = len(challenge_attempts(state, challenge_id)) + 1
    attempt = {
        "round_id": round_id,
        "challenge_id": challenge_id,
        "attempt": attempt_number,
        "status": status,
        "failure_class": failure_class,
        "run_id": run_id,
        "notes": notes[:500],
    }
    state.setdefault("attempts", []).append(attempt)
    round_state = state.setdefault("rounds", {}).setdefault(
        round_id,
        {"challenges": {}, "complete": False},
    )
    round_state["challenges"][challenge_id] = {
        "status": status,
        "attempts": attempt_number,
        "run_id": run_id,
        "failure_class": failure_class,
    }
    refresh_round(state, round_id)
    streak = failure_streak(state, challenge_id, failure_class) if status == "FAIL" else 0
    if streak >= MAX_SAME_FAILURE:
        result_status = "STOP_ALTERNATIVE_REQUIRED"
    elif status == "PASS" and attempt_number > MAX_ATTEMPTS_TO_PASS:
        result_status = "ROUND_RESTART_REQUIRED"
    else:
        result_status = "RECORDED"
    return {
        "status": result_status,
        "attempt_number": attempt_number,
        "failure_streak": streak,
        "round_complete": round_state["complete"],
    }


def acceptance(state: dict[str, Any]) -> dict[str, Any]:
    complete = [
        round_id
        for round_id, value in state.get("rounds", {}).items()
        if value.get("complete")
    ]
    stopped = []
    late_passes = []
    for attempt in state.get("attempts", []):
        if attempt.get("status") == "FAIL":
            streak = failure_streak(
                state,
                str(attempt.get("challenge_id")),
                str(attempt.get("failure_class")),
            )
            if streak >= MAX_SAME_FAILURE:
                marker = {
                    "challenge_id": attempt.get("challenge_id"),
                    "failure_class": attempt.get("failure_class"),
                    "streak": streak,
                }
                if marker not in stopped:
                    stopped.append(marker)
        if attempt.get("status") == "PASS" and int(attempt.get("attempt", 0)) > MAX_ATTEMPTS_TO_PASS:
            late_passes.append(
                {
                    "challenge_id": attempt.get("challenge_id"),
                    "attempt": attempt.get("attempt"),
                }
            )
    first_attempt_passes = sum(
        1
        for attempt in state.get("attempts", [])
        if attempt.get("status") == "PASS" and attempt.get("attempt") == 1
    )
    accepted = (
        len(complete) >= REQUIRED_GREEN_ROUNDS
        and first_attempt_passes >= MIN_FIRST_ATTEMPT_PASSES
        and not stopped
        and not late_passes
    )
    if stopped:
        status = "STOP_ALTERNATIVE_REQUIRED"
    elif late_passes or (
        len(complete) >= REQUIRED_GREEN_ROUNDS
        and first_attempt_passes < MIN_FIRST_ATTEMPT_PASSES
    ):
        status = "ROUND_RESTART_REQUIRED"
    else:
        status = "PASS" if accepted else "PENDING"
    return {
        "status": status,
        "green_rounds": len(complete),
        "required_green_rounds": REQUIRED_GREEN_ROUNDS,
        "complete_round_ids": complete,
        "first_attempt_passes": first_attempt_passes,
        "required_first_attempt_passes": MIN_FIRST_ATTEMPT_PASSES,
        "late_passes": late_passes,
        "stopped": stopped,
        "model": state.get("model", ""),
        "resource_manifest_sha256": state.get("resource_manifest_sha256", ""),
    }


def self_test() -> None:
    state = empty_state()
    for round_number in (1, 2):
        for index in range(REQUIRED_PER_ROUND):
            record_attempt(
                state,
                round_id=f"natural-round-{round_number}",
                challenge_id=f"natural-{round_number:02d}{index:014d}"[-24:],
                status="PASS",
                failure_class="",
                run_id=str(round_number * 100 + index),
                model="GPT-5.6 Thinking",
                resource_hash="a" * 64,
                notes="control",
            )
    if acceptance(state)["status"] != "PASS":
        raise NaturalStabilizeError("two six-case first-attempt rounds must pass")
    retry_state = empty_state()
    for round_number in (1, 2):
        for index in range(REQUIRED_PER_ROUND):
            challenge = f"natural-{round_number:02d}{index:014d}"[-24:]
            if round_number == 1 and index < 2:
                record_attempt(
                    retry_state,
                    round_id=f"natural-retry-{round_number}",
                    challenge_id=challenge,
                    status="FAIL",
                    failure_class="natural_language",
                    run_id=f"f-{round_number}-{index}",
                    model="GPT-5.6 Thinking",
                    resource_hash="b" * 64,
                    notes="retry",
                )
            record_attempt(
                retry_state,
                round_id=f"natural-retry-{round_number}",
                challenge_id=challenge,
                status="PASS",
                failure_class="",
                run_id=f"p-{round_number}-{index}",
                model="GPT-5.6 Thinking",
                resource_hash="b" * 64,
                notes="control",
            )
    if acceptance(retry_state)["status"] != "PASS":
        raise NaturalStabilizeError("exactly ten first-attempt passes must be accepted")
    stopped_state = empty_state()
    for index in range(3):
        result = record_attempt(
            stopped_state,
            round_id="natural-stop",
            challenge_id="natural-0123456789abcdef",
            status="FAIL",
            failure_class="ui_logic",
            run_id=str(index),
            model="GPT-5.6 Thinking",
            resource_hash="c" * 64,
            notes="same failure",
        )
    if result["status"] != "STOP_ALTERNATIVE_REQUIRED":
        raise NaturalStabilizeError("third equal failure must require an alternative")


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
            print(json.dumps({"status": "PASS", "test": "kgg_gpt_natural_ui_stabilize"}))
            return 0
        if not args.state:
            raise NaturalStabilizeError("--state is required")
        state = load_state(args.state)
        if args.record:
            if not all(
                [
                    args.round_id,
                    args.challenge_id,
                    args.status,
                    args.run_id,
                    args.resource_hash,
                ]
            ):
                raise NaturalStabilizeError(
                    "record requires round, challenge, status, run, model and resource hash"
                )
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
            print(
                json.dumps(
                    {**result, "acceptance": acceptance(state)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2 if result["status"] != "RECORDED" else 0
        result = acceptance(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
