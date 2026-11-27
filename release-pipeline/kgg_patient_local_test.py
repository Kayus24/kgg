#!/usr/bin/env python3
"""Run the fixed synthetic patient settings test through the local KGG write gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import shutil
import subprocess
from subprocess import Popen
import sys

import kgg_brain_relay_worker as relay
import kgg_patient_gpt_write_gate as gate


SCHEMA = "kgg.patient-local-test/v1"
PROFILE = "playwright-card-settings-accessible-name"
HARNESS = Path(__file__).with_name("kgg_patient_card_settings_accessibility_playwright.cjs")
PATIENT_FILE = "patient-card-settings.js"
PHASES = ("red", "green", "replay")
MAX_ATTEMPTS = 3
RUN_SECONDS = 110
TERMINAL = {"PASS", "FAIL", "BLOCKED", "TIMEOUT", "UNKNOWN"}


class TestStopped(gate.GateError):
    pass


def now():
    return datetime.now(timezone.utc)


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notice_content(directory, result):
    return (f"KGG {result['run_id']} {result['status']}\n"
            f"Base SHA {result['base_sha']}\n"
            f"Evidence SHA-256 {fingerprint(directory / 'result.json')}\n"
            "ENDE notice\n")


def run_dir(root, sha, attempt):
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or attempt not in range(1, MAX_ATTEMPTS + 1):
        gate.fail("exact base SHA and repair attempt 1–3 required")
    path = root.resolve() / "tmp" / "kgg-patient-local-test" / sha / f"card-settings-{attempt}"
    if path.resolve() != path:
        gate.fail("local test path escaped its canonical directory")
    return path


def write_notice(directory, result):
    # PDC gptflow owns authorization, the verified destination, delivery and ACK.
    # The file is a wake-up signal. The receiver independently reads evidence.
    path = directory / "notice.md"
    pending = directory / "notice.pending"
    with pending.open("x", encoding="utf-8", newline="\n") as output:
        output.write(notice_content(directory, result))
        output.flush()
        os.fsync(output.fileno())
    os.replace(pending, path)


def evidence(directory, root=gate.ROOT):
    if not directory.exists():
        return {"status": "NOT_RUN"}
    result_path = directory / "result.json"
    path = result_path if result_path.is_file() else directory / "request.json"
    try:
        if path.resolve() != path:
            gate.fail("unsafe test receipt")
        record = json.loads(path.read_text(encoding="utf-8"))
        if (record["schema"], record["run_id"], record["base_sha"]) != (
            SCHEMA, f"{directory.parent.name}-{directory.name}", directory.parent.name,
        ):
            gate.fail("stale test receipt")
        if path == result_path:
            if record["status"] not in TERMINAL or gate.local_byte_hashes(directory / "proof") != record["proof_sha256"]:
                gate.fail("test evidence mismatch")
            if record["status"] == "PASS":
                candidate = gate.local_candidate_evidence(record["job_id"], root)
                authoring_receipt = gate.local_candidate_job(root, record["job_id"]) / "result.json"
                if (candidate["status"] != "COMPLETE" or candidate["patch_sha256"] != record["patch_sha256"]
                        or fingerprint(authoring_receipt) != record["authoring_receipt_sha256"]):
                    gate.fail("authoring evidence mismatch")
            notice = directory / "notice.md"
            record["notice_ready"] = (notice.resolve() == notice and notice.is_file()
                                      and notice.read_bytes() == notice_content(directory, record).encode("utf-8"))
        else:
            # A PID can be reused. Only a matching receipt proves completion.
            start = directory / "start.json"
            if start.is_file() and start.resolve() == start:
                worker = json.loads(start.read_text(encoding="utf-8"))
                if worker["run_id"] == record["run_id"]:
                    record["pid"] = worker["pid"]
            if now() >= datetime.fromisoformat(record["deadline"]):
                record.update(status="UNKNOWN", reason="deadline_without_terminal_receipt")
            record = {key: value for key, value in record.items() if key not in {"payload", "approval"}}
        return record
    except (gate.GateError, OSError, ValueError, KeyError, TypeError):
        return {"status": "UNKNOWN", "reason": "test_receipt_unavailable_or_invalid"}


def preflight(payload, schema, attempt, root=gate.ROOT):
    confirmation = gate.local_candidate_preflight(payload, root)
    if schema != SCHEMA:
        gate.fail("current test schema required")
    if payload.get("required_tests") != [PROFILE] or {op["path"] for op in payload["operations"]} != {PATIENT_FILE}:
        gate.fail("the fixed settings profile cannot certify other patient changes")
    directory = run_dir(root, confirmation["base_sha"], attempt)
    return {
        "schema": SCHEMA, "profile": PROFILE, "status": "PREFLIGHT", "confirmation": confirmation,
        "run_id": f"{directory.parent.name}-{directory.name}",
        "result_file": str(directory / "notice.md"),
        "preview_status": "NOT_RUN",
    }


def start(payload, approval, schema, attempt, root=gate.ROOT):
    plan = preflight(payload, schema, attempt, root)
    confirmation = plan["confirmation"]
    if approval != {**confirmation, "approval_phrase": gate.PATIENT_APPROVAL_PHRASE}:
        gate.fail("exact authorized patch required")
    sha, job_id, patch = (confirmation[key] for key in ("base_sha", "request_id", "patch_sha256"))
    directory = run_dir(root, sha, attempt)
    operations = json.dumps(payload["operations"], sort_keys=True, separators=(",", ":"))
    approach_sha = gate.sha256_text(operations)
    harness_sha = fingerprint(HARNESS)

    if not directory.exists():
        for previous in range(1, attempt):
            result = evidence(run_dir(root, sha, previous), root)
            if (result["status"] != "FAIL" or result.get("reason") != "candidate_assertion_failed"
                    or result.get("harness_sha256") != harness_sha):
                gate.fail("repair requires the previous verified candidate assertion failure and unchanged test")
            if result.get("approach_sha256") == approach_sha:
                gate.fail("repair duplicates a previous patch")
        if gate.local_candidate_job(root, job_id).exists():
            gate.fail("test start requires a fresh authoring request ID for RED before patch")

    directory.parent.mkdir(parents=True, exist_ok=True)
    try:
        directory.mkdir()
    except FileExistsError:
        existing = evidence(directory, root)
        if existing.get("patch_sha256", patch) != patch:
            gate.fail("repair attempt is already reserved for a different patch")
        return existing

    started = now()
    record = {
        "schema": SCHEMA, "job_id": job_id, "run_id": plan["run_id"], "base_sha": sha,
        "patch_sha256": patch, "approach_sha256": approach_sha, "harness_sha256": harness_sha,
        "profile": PROFILE, "attempt": attempt, "status": "RUNNING", "preview_status": "NOT_RUN",
        "started_at": started.isoformat(), "deadline": (started + timedelta(seconds=RUN_SECONDS)).isoformat(),
        "result_file": plan["result_file"],
    }
    gate.write_local_receipt(directory / "request.json", {**record, "payload": payload, "approval": approval})
    try:
        worker = Popen(
            [sys.executable, str(Path(__file__).resolve()), "worker", "--base-sha", sha, "--attempt", str(attempt)],
            cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except OSError:
        (directory / "proof").mkdir()
        result = finish(directory, record, "BLOCKED", "worker_start_unavailable", {})
        return result
    return {**record, "pid": worker.pid}


def browser_phase(directory, phase, source, record, exits, deadline):
    if fingerprint(HARNESS) != record["harness_sha256"]:
        raise TestStopped("test_harness_changed")
    remaining = (deadline - now()).total_seconds()
    if remaining <= 0:
        raise subprocess.TimeoutExpired(phase, RUN_SECONDS)
    destination = directory / "proof" / phase
    destination.mkdir()
    env = os.environ.copy()
    env.pop("NODE_OPTIONS", None)
    env.pop("NODE_PATH", None)
    with (destination / "browser.log").open("xb") as output:
        completed = subprocess.run(
            ["node", str(HARNESS), str(source), str(destination)], cwd=destination, env=env,
            timeout=remaining, stdout=output, stderr=subprocess.STDOUT,
        )
    exits[phase] = completed.returncode
    result_path = destination / "result.json"
    if not result_path.is_file():
        raise TestStopped("browser_evidence_unavailable")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    screenshots = {label: fingerprint(destination / name) for label, name in
                   (("initial", "initial.png"), ("postTap", "post-tap.png"))}
    if (result.get("servedSha256") != fingerprint(source / PATIENT_FILE)
            or result.get("screenshotSha256") != screenshots
            or screenshots["initial"] == screenshots["postTap"]
            or result.get("settingsSheetVisibleAfterTap") is not True):
        raise TestStopped("browser_evidence_mismatch")
    observed = completed.returncode, result.get("status"), result.get("matchedButtons")
    if observed == (1, "FAIL", 0):
        if phase != "red":
            raise TestStopped("candidate_assertion_failed")
    elif observed == (0, "PASS", 1):
        if phase == "red":
            raise TestStopped("baseline_did_not_reproduce")
    else:
        raise TestStopped("browser_outcome_inconsistent")


def finish(directory, record, status, reason, exits):
    result = {**record, "status": status, "reason": reason, "exit_codes": exits, "finished_at": now().isoformat(),
              "proof_sha256": gate.local_byte_hashes(directory / "proof")}
    gate.write_local_receipt(directory / "result.json", result)
    write_notice(directory, result)
    return result


def worker(directory, root=gate.ROOT):
    request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    # The exclusive receipt also prevents duplicate workers after a lost start response.
    with (directory / "worker.lock").open("x", encoding="utf-8"):
        pass
    payload, approval = request.pop("payload"), request.pop("approval")
    record = {**request, "pid": os.getpid()}
    gate.write_local_receipt(directory / "start.json", record)
    (directory / "proof").mkdir()
    exits = {}
    deadline = datetime.fromisoformat(record["deadline"])
    try:
        if gate.git_sha(root) != record["base_sha"] or gate.payload_hash(payload) != record["patch_sha256"]:
            raise TestStopped("stale_source_or_patch")
        if not shutil.which("node"):
            raise FileNotFoundError("node")

        def reproduce(source):
            browser_phase(directory, "red", source, record, exits, deadline)

        authored = gate.prepare_local_candidate(payload, approval, root, before_patch=reproduce)
        if authored["status"] != "COMPLETE":
            reason = authored.get("reason", "authoring_receipt_incomplete")
            status = authored["status"]
            if reason in {"browser_evidence_unavailable", "browser_evidence_mismatch", "browser_outcome_inconsistent"}:
                status = "UNKNOWN"
            if status == "COMPLETE":
                status = "UNKNOWN"
        elif exits.get("red") != 1:
            status, reason = "UNKNOWN", "missing_red_before_authoring"
        else:
            for phase in PHASES[1:]:
                browser_phase(directory, phase, root / authored["candidate"], record, exits, deadline)
            if gate.local_candidate_evidence(record["job_id"], root) != authored or gate.git_sha(root) != record["base_sha"]:
                raise TestStopped("source_or_candidate_changed_during_test")
            record["authoring_receipt_sha256"] = fingerprint(gate.local_candidate_job(root, record["job_id"]) / "result.json")
            status, reason = "PASS", "red_green_unchanged_replay"
    except subprocess.TimeoutExpired:
        status, reason = "TIMEOUT", "test_deadline"
    except (FileNotFoundError, PermissionError):
        status, reason = "BLOCKED", "test_dependency_or_permission"
    except TestStopped as exc:
        reason = str(exc)
        status = "FAIL" if reason == "candidate_assertion_failed" else "UNKNOWN"
    except (gate.GateError, OSError, subprocess.SubprocessError, ValueError, KeyError):
        status, reason = "UNKNOWN", "test_execution_unconfirmed"
    return finish(directory, record, status if status in TERMINAL else "UNKNOWN", reason, exits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["preflight", "start", "status", "evidence", "worker"])
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--schema")
    parser.add_argument("--payload-file", type=Path)
    parser.add_argument("--approval-file", type=Path)
    args = parser.parse_args()
    try:
        directory = run_dir(gate.ROOT, args.base_sha, args.attempt)
        if args.mode in {"preflight", "start"}:
            payload = gate.local_json_input(args.payload_file)
            if not isinstance(payload, dict) or payload.get("base_sha") != args.base_sha:
                gate.fail("test base SHA does not match payload")
            record = (preflight(payload, args.schema, args.attempt) if args.mode == "preflight"
                      else start(payload, gate.local_json_input(args.approval_file), args.schema, args.attempt))
        elif args.mode == "worker":
            record = worker(directory)
        else:
            record = evidence(directory)
        status = record["status"]
        if args.mode != "evidence":
            record = {key: value for key, value in record.items() if key != "proof_sha256"}
        record["supervisor_state"] = relay.supervisor_state_for({
            "plan_ready": status != "NOT_RUN", "child_running": status == "RUNNING",
            "result_pending": status in {"PASS", "FAIL"}, "blocked": status in {"BLOCKED", "UNKNOWN", "TIMEOUT"},
        })
        print(json.dumps(record, sort_keys=True))
        return 0 if status in {"PREFLIGHT", "RUNNING", "PASS"} else 1
    except (gate.GateError, OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"status": "BLOCKED", "reason": "test_start_or_input_rejected"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
