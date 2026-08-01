#!/usr/bin/env python3
"""Write the public, non-sensitive KGG Preview workflow status channel."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
PHASES = {"validating", "publishing", "success", "failure"}


class StatusError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_status(
    request_id: str,
    run_id: str,
    run_url: str,
    phase: str,
    message: str,
    updated_at: str | None = None,
) -> dict[str, object]:
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise StatusError("request_id must match ^[a-z0-9][a-z0-9-]{5,63}$")
    if phase not in PHASES:
        raise StatusError("phase must be validating, publishing, success or failure")
    if not run_id.isdigit():
        raise StatusError("run_id must contain digits only")
    if not run_url.startswith("https://github.com/"):
        raise StatusError("run_url must be a GitHub HTTPS URL")
    clean_message = " ".join(message.split()).strip()
    if not clean_message or len(clean_message) > 240:
        raise StatusError("message must contain 1 to 240 characters")
    terminal = phase in {"success", "failure"}
    return {
        "kind": "kgg_preview_run_status",
        "schema": 1,
        "requestId": request_id,
        "runId": run_id,
        "runUrl": run_url,
        "phase": phase,
        "status": "completed" if terminal else "in_progress",
        "conclusion": phase if terminal else None,
        "updatedAt": updated_at or utc_now(),
        "message": clean_message,
    }


def write_json_atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        handle.write(raw)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def write_status(preview_root: Path, status: dict[str, object]) -> tuple[Path, Path]:
    root = preview_root.resolve()
    request_id = str(status["requestId"])
    request_path = (root / "status" / "requests" / f"{request_id}.json").resolve()
    latest_path = (root / "status" / "latest.json").resolve()
    if root not in request_path.parents or root not in latest_path.parents:
        raise StatusError("status path escaped preview root")
    write_json_atomic(request_path, status)
    write_json_atomic(latest_path, status)
    return request_path, latest_path


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="kgg-preview-status-") as directory:
        root = Path(directory)
        first = build_status(
            "preview-status-self-test",
            "123456",
            "https://github.com/Kayus24/kgg/actions/runs/123456",
            "validating",
            "Preview wird validiert.",
            "2026-08-01T10:00:00Z",
        )
        request_path, latest_path = write_status(root, first)
        loaded = json.loads(latest_path.read_text(encoding="utf-8"))
        if loaded != first or request_path.read_bytes() != latest_path.read_bytes():
            raise StatusError("status files differ after initial write")
        final = build_status(
            "preview-status-self-test",
            "123456",
            "https://github.com/Kayus24/kgg/actions/runs/123456",
            "success",
            "Test-App-Preview ist bereit.",
            "2026-08-01T10:05:00Z",
        )
        write_status(root, final)
        loaded = json.loads(latest_path.read_text(encoding="utf-8"))
        if loaded["status"] != "completed" or loaded["conclusion"] != "success":
            raise StatusError("terminal status was not persisted")
        try:
            build_status(
                "../escape",
                "1",
                "https://github.com/Kayus24/kgg/actions/runs/1",
                "failure",
                "blocked",
            )
        except StatusError:
            pass
        else:
            raise StatusError("unsafe request id was accepted")
    print("KGG Preview status self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-root", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--run-id")
    parser.add_argument("--run-url")
    parser.add_argument("--phase", choices=sorted(PHASES))
    parser.add_argument("--message")
    parser.add_argument("--updated-at")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    required = [args.preview_root, args.request_id, args.run_id, args.run_url, args.phase, args.message]
    if any(value is None for value in required):
        parser.error("status writes require preview-root, request-id, run-id, run-url, phase and message")
    status = build_status(
        args.request_id,
        args.run_id,
        args.run_url,
        args.phase,
        args.message,
        args.updated_at,
    )
    request_path, latest_path = write_status(args.preview_root, status)
    print(json.dumps({"request": str(request_path), "latest": str(latest_path)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
