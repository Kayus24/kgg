"""Capture and independently verify an outer ``codex exec --json`` stream.

This module is deliberately separate from the JSONL adapter.  It owns the
process boundary, retains the exact stdout bytes, records outer timing and
identity, and exposes a fail-closed verification step.  It does not interpret
model content, score quality, or build a measurement envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import signal
import subprocess
import time
from collections.abc import Sequence
from typing import Any


class CaptureError(ValueError):
    """Raised when raw evidence or its binding cannot be trusted."""


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    """Terminate the bounded command and descendants without an unbounded wait."""

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.0,
            )
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, ProcessLookupError):
        process.kill()


def _bounded_collect(
    process: subprocess.Popen[bytes],
    timeout_error: subprocess.TimeoutExpired,
) -> tuple[bytes, bytes]:
    """Collect after tree termination, with a final bounded cleanup window."""

    try:
        return process.communicate(timeout=1.0)
    except subprocess.TimeoutExpired as cleanup_error:
        process.kill()
        stdout = cleanup_error.output or timeout_error.output or b""
        stderr = cleanup_error.stderr or timeout_error.stderr or b""
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        return stdout, stderr


@dataclass(frozen=True)
class CaptureRecord:
    """Immutable metadata plus the exact captured stdout bytes."""

    raw_stdout: bytes
    raw_stderr: bytes
    raw_stdout_sha256: str
    stdout_bytes: int
    event_lines: int
    outer_runtime_ms: int
    exit_code: int | None
    terminal_state: str
    command: tuple[str, ...]
    codex_version: str
    run_id: str
    surface: str
    scenario_id: str
    base_sha: str
    candidate_fingerprint: str

    def metadata(self) -> dict[str, Any]:
        """Return JSON-safe metadata; raw bytes remain a separate evidence blob."""

        return {
            "raw_stdout_sha256": self.raw_stdout_sha256,
            "stdout_bytes": self.stdout_bytes,
            "event_lines": self.event_lines,
            "outer_runtime_ms": self.outer_runtime_ms,
            "exit_code": self.exit_code,
            "terminal_state": self.terminal_state,
            "command": list(self.command),
            "codex_version": self.codex_version,
            "run_id": self.run_id,
            "surface": self.surface,
            "scenario_id": self.scenario_id,
            "base_sha": self.base_sha,
            "candidate_fingerprint": self.candidate_fingerprint,
        }


_TERMINAL_STATES = frozenset({"completed", "failed", "timed_out"})


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaptureError(f"{label}_missing")
    if "\x00" in value:
        raise CaptureError(f"{label}_invalid")
    return value


def _base_sha(value: Any) -> str:
    text = _required_text(value, "base_sha").lower()
    if len(text) != 40 or any(char not in "0123456789abcdef" for char in text):
        raise CaptureError("base_sha_invalid")
    return text


def _command(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not value:
        raise CaptureError("command_invalid")
    result = tuple(_required_text(item, "command_arg") for item in value)
    return result


def _event_line_count(raw_stdout: bytes) -> int:
    return sum(1 for line in raw_stdout.splitlines() if line.strip())


def capture_from_completed_process(
    *,
    raw_stdout: bytes,
    raw_stderr: bytes = b"",
    started_ns: int,
    finished_ns: int,
    exit_code: int | None,
    terminal_state: str,
    command: Sequence[str],
    codex_version: str,
    run_id: str,
    surface: str,
    scenario_id: str,
    base_sha: str,
    candidate_fingerprint: str,
) -> CaptureRecord:
    """Create a capture record without decoding or interpreting stdout."""

    if not isinstance(raw_stdout, bytes) or not raw_stdout:
        raise CaptureError("raw_stdout_missing")
    if not isinstance(raw_stderr, bytes):
        raise CaptureError("raw_stderr_invalid")
    if not isinstance(started_ns, int) or not isinstance(finished_ns, int) or finished_ns < started_ns:
        raise CaptureError("outer_timing_invalid")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        raise CaptureError("exit_code_invalid")
    if terminal_state not in _TERMINAL_STATES:
        raise CaptureError("terminal_state_invalid")
    if terminal_state == "completed" and exit_code != 0:
        raise CaptureError("terminal_exit_mismatch")
    if terminal_state == "failed" and exit_code in (None, 0):
        raise CaptureError("terminal_exit_mismatch")
    if terminal_state == "timed_out" and exit_code is not None:
        raise CaptureError("terminal_timeout_exit_mismatch")

    raw_hash = hashlib.sha256(raw_stdout).hexdigest()
    return CaptureRecord(
        raw_stdout=raw_stdout,
        raw_stderr=raw_stderr,
        raw_stdout_sha256=raw_hash,
        stdout_bytes=len(raw_stdout),
        event_lines=_event_line_count(raw_stdout),
        outer_runtime_ms=(finished_ns - started_ns) // 1_000_000,
        exit_code=exit_code,
        terminal_state=terminal_state,
        command=_command(command),
        codex_version=_required_text(codex_version, "codex_version"),
        run_id=_required_text(run_id, "run_id"),
        surface=_required_text(surface, "surface"),
        scenario_id=_required_text(scenario_id, "scenario_id"),
        base_sha=_base_sha(base_sha),
        candidate_fingerprint=_required_text(candidate_fingerprint, "candidate_fingerprint"),
    )


def verify_record(record: CaptureRecord, raw_stdout: bytes | None = None) -> dict[str, Any]:
    """Re-hash and re-count retained bytes independently of capture metadata."""

    if not isinstance(record, CaptureRecord):
        raise CaptureError("record_invalid")
    retained = record.raw_stdout if raw_stdout is None else raw_stdout
    if not isinstance(retained, bytes) or not retained:
        raise CaptureError("retained_raw_stdout_missing")
    digest = hashlib.sha256(retained).hexdigest()
    if digest != record.raw_stdout_sha256:
        raise CaptureError("raw_stdout_digest_mismatch")
    if len(retained) != record.stdout_bytes:
        raise CaptureError("raw_stdout_size_mismatch")
    lines = _event_line_count(retained)
    if lines != record.event_lines:
        raise CaptureError("event_line_count_mismatch")
    if record.terminal_state == "completed" and record.exit_code != 0:
        raise CaptureError("terminal_exit_mismatch")
    return {
        "status": "RAW_CAPTURE_VERIFIED",
        "raw_stdout_sha256": digest,
        "stdout_bytes": len(retained),
        "event_lines": lines,
        "run_id": record.run_id,
        "surface": record.surface,
        "scenario_id": record.scenario_id,
        "base_sha": record.base_sha,
        "candidate_fingerprint": record.candidate_fingerprint,
    }


def capture_command(
    command: Sequence[str],
    *,
    cwd: str,
    stdin_bytes: bytes,
    codex_version: str,
    run_id: str,
    surface: str,
    scenario_id: str,
    base_sha: str,
    candidate_fingerprint: str,
    timeout_seconds: float | None = None,
) -> CaptureRecord:
    """Run a bounded command and retain stdout before any decoding."""

    argv = _command(command)
    if not isinstance(stdin_bytes, bytes):
        raise CaptureError("stdin_bytes_invalid")
    started_ns = time.monotonic_ns()
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name != "nt",
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        ),
    )
    try:
        stdout, stderr = process.communicate(input=stdin_bytes, timeout=timeout_seconds)
        terminal_state = "completed" if process.returncode == 0 else "failed"
        exit_code = process.returncode
    except subprocess.TimeoutExpired as error:
        _terminate_process_tree(process)
        stdout, stderr = _bounded_collect(process, error)
        terminal_state = "timed_out"
        exit_code = None
        if not stdout and error.output:
            stdout = error.output
        if not stderr and error.stderr:
            stderr = error.stderr
    finished_ns = time.monotonic_ns()
    return capture_from_completed_process(
        raw_stdout=stdout,
        raw_stderr=stderr,
        started_ns=started_ns,
        finished_ns=finished_ns,
        exit_code=exit_code,
        terminal_state=terminal_state,
        command=argv,
        codex_version=codex_version,
        run_id=run_id,
        surface=surface,
        scenario_id=scenario_id,
        base_sha=base_sha,
        candidate_fingerprint=candidate_fingerprint,
    )
