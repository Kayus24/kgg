#!/usr/bin/env python3
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("brain", HERE / "kgg_brain_relay_worker.py")
brain = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(brain)

def expect_fail(fn, needle: str) -> None:
    try:
        fn()
    except brain.ContractError as exc:
        assert needle in str(exc), (needle, str(exc))
        return
    raise AssertionError(f"expected failure containing {needle!r}")

def reasoning_capsule():
    c = brain.synthetic_capsule(with_sub_chats=True)
    c["entry_mode"] = "BOSS_FIRST"
    c["work_mode"] = "reasoning"
    c["workers"] = []
    c["route"] = [
        "luna-manager", "lead-gpt", "gpt-subchat",
        "lead-synthesis", "lead-gpt", "ci-acceptance",
    ]
    return c

def implementation_capsule():
    c = brain.synthetic_capsule()
    c["entry_mode"] = "SUPERVISOR_FIRST"
    c["work_mode"] = "implementation"
    return c

def mixed_capsule():
    c = brain.synthetic_capsule(with_sub_chats=True)
    c["entry_mode"] = "SUPERVISOR_FIRST"
    c["work_mode"] = "mixed"
    return c

def main():
    assert brain.DEFAULT_ENTRY_MODE == "SUPERVISOR_FIRST"
    assert brain.ENTRY_MODES == {"BOSS_FIRST", "SUPERVISOR_FIRST"}
    assert brain.WORK_MODES == {"reasoning", "implementation", "mixed"}
    assert brain.MAX_SUB_CHATS == 4
    assert brain.MAX_LUNA_WORKERS == 3
    assert brain.MAX_VERIFIERS == 1
    assert len(brain.BRIDGE_FIELDS) == 9
    assert "strategic-lead" not in brain.ROLE_MODELS
    assert brain.ROLE_MODELS["sol-endboss"] == ("gpt-5.6-sol", "ultra")

    # Existing v2 contract stays structurally identical.
    legacy = brain.synthetic_capsule()
    validated = brain.validate_task_capsule(legacy)
    assert validated == legacy
    assert "entry_mode" not in validated
    assert "work_mode" not in validated

    legacy_sub = brain.synthetic_capsule(with_sub_chats=True)
    assert brain.validate_task_capsule(legacy_sub) == legacy_sub

    incomplete = copy.deepcopy(legacy)
    incomplete["route"] = ["luna-manager", "lead-gpt", "luna-relay"]
    expect_fail(lambda: brain.validate_task_capsule(incomplete), "complete")

    # Entry mode alone does not force a new route or mutate the object.
    boss_legacy = copy.deepcopy(legacy)
    boss_legacy["entry_mode"] = "BOSS_FIRST"
    assert brain.validate_task_capsule(boss_legacy) == boss_legacy

    # Explicit work_mode opts into Rev1 behavior.
    brain.validate_task_capsule(reasoning_capsule())
    brain.validate_task_capsule(implementation_capsule())
    brain.validate_task_capsule(mixed_capsule())

    bad = copy.deepcopy(legacy)
    bad["entry_mode"] = "UNKNOWN"
    expect_fail(lambda: brain.validate_task_capsule(bad), "entry_mode")

    bad = copy.deepcopy(legacy)
    bad["work_mode"] = "UNKNOWN"
    expect_fail(lambda: brain.validate_task_capsule(bad), "work_mode")

    bad = reasoning_capsule()
    bad["workers"] = copy.deepcopy(implementation_capsule()["workers"])
    expect_fail(lambda: brain.validate_task_capsule(bad), "must not allocate implementation workers")

    bad = implementation_capsule()
    bad["sub_chats"] = copy.deepcopy(mixed_capsule()["sub_chats"])
    bad["route"] = copy.deepcopy(mixed_capsule()["route"])
    expect_fail(lambda: brain.validate_task_capsule(bad), "must not allocate GPT sub-chats")

    bad = mixed_capsule()
    bad["workers"] = []
    expect_fail(lambda: brain.validate_task_capsule(bad), "requires GPT sub-chats and at least one")

    bad = mixed_capsule()
    template = copy.deepcopy(bad["sub_chats"][0])
    while len(bad["sub_chats"]) < 5:
        i = len(bad["sub_chats"]) + 1
        item = copy.deepcopy(template)
        item["chat_id"] = f"kgg-sub-extra-{i}"
        item["scope"] = f"extra-scope-{i}"
        bad["sub_chats"].append(item)
    expect_fail(lambda: brain.validate_task_capsule(bad), "at most four GPT sub-chats")

    bad = implementation_capsule()
    base_worker = copy.deepcopy(next(w for w in bad["workers"] if w["role"] == "luna-max-worker"))
    verifier = [copy.deepcopy(w) for w in bad["workers"] if w["role"] == "verifier"]
    workers = []
    for i in range(4):
        item = copy.deepcopy(base_worker)
        item["worker_id"] = f"worker-{i+1}"
        item["scope"] = f"scope-{i+1}"
        workers.append(item)
    bad["workers"] = workers + verifier
    expect_fail(lambda: brain.validate_task_capsule(bad), "three Luna-Max workers plus one verifier")

    assert brain.route_chat_message({"request": "diagnose only"})["mode"] == brain.STANDALONE_MODE
    c = implementation_capsule()
    active = brain.synthetic_workflow_start(c)
    routed = brain.route_chat_message(active, capsule=c, bridge=active["bridge"])
    assert routed["mode"] == brain.WORKFLOW_MODE

    h = brain.synthetic_handoff(c)
    b = brain.build_bridge_from_local(c, h, role="lead-gpt", status="PASS", next_action="continue-workflow")
    assert len(b) == 9

    bad_bridge = copy.deepcopy(b)
    bad_bridge["extra"] = "x"
    expect_fail(
        lambda: brain.validate_bridge(bad_bridge, c["requirements"]["text"], h, capsule=c),
        "fields must be exact",
    )

    bad_h = copy.deepcopy(h)
    bad_h["transport_only"] = False
    bad_h["handoff_sha256"] = brain.handoff_sha256_for(bad_h)
    expect_fail(lambda: brain.validate_handoff_event(bad_h, c), "transport_only=true")

    bad_h = copy.deepcopy(h)
    bad_h["requirements_sha256"] = "a" * 64
    bad_h["handoff_sha256"] = brain.handoff_sha256_for(bad_h)
    expect_fail(lambda: brain.validate_handoff_event(bad_h, c), "requirements_changed")

    brain.validate_sol_request({
        "role": "sol-endboss", "state": "SLEEPING",
        "requested_action": "observe", "internal_sol_agents": False,
    })
    expect_fail(
        lambda: brain.validate_sol_request({
            "role": "sol-endboss", "state": "SLEEPING", "requested_action": "code",
        }),
        "may not code",
    )

    idle_snapshot = {
        "plan_ready": True, "acceptance_met": False, "blocked": False,
        "waiting_max": False, "child_running": False, "result_pending": False,
        "dispatch_ready": False, "lead_review_pending": False, "verifying": False,
    }
    idle = brain.supervisor_state_for(idle_snapshot)
    assert idle == "IDLE_NEEDS_LEAD"
    first = brain.supervisor_poll_decision("CHILD_RUNNING", idle)
    assert first["poll_interval_seconds"] == 60
    assert first["read_only"] is True
    assert first["chat_messages"] == 0
    assert first["meaningful_events"] == 1
    assert first["action"] == "emit-needs-lead"

    repeat = brain.supervisor_poll_decision(idle, idle)
    assert repeat["action"] == "none"
    assert repeat["meaningful_events"] == 0

    waiting = copy.deepcopy(idle_snapshot)
    waiting["waiting_max"] = True
    state = brain.supervisor_state_for(waiting)
    assert state == "WAITING_MAX"
    assert brain.supervisor_poll_decision(state, state)["action"] == "none"

    running = copy.deepcopy(idle_snapshot)
    running["child_running"] = True
    state = brain.supervisor_state_for(running)
    for _ in range(10):
        d = brain.supervisor_poll_decision(state, state)
        assert d["chat_messages"] == 0
        assert d["meaningful_events"] == 0
        assert d["action"] == "none"

    assert brain.ROTATION_PREPARE_AT == 35
    assert brain.ROTATION_HARD_AT == 40
    print("PASS: KGG Brain-Relay Rev1 legacy compatibility + explicit routing tests")

if __name__ == "__main__":
    main()
