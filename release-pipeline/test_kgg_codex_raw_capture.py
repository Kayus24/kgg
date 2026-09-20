from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

PIPELINE = Path(__file__).resolve().parent
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

import kgg_codex_raw_capture as capture


BASE = "439742c89de6eac298dd8aa11c2a775feb0c4ae6"
FINGERPRINT = "candidate-fingerprint-fixture"
RAW = b'{"type":"thread.started"}\n{"type":"turn.completed"}\n'


def record(**overrides: object) -> capture.CaptureRecord:
    values: dict[str, object] = {
        "raw_stdout": RAW,
        "raw_stderr": b"",
        "started_ns": 1_000_000_000,
        "finished_ns": 1_037_000_000,
        "exit_code": 0,
        "terminal_state": "completed",
        "command": ("codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only", "-"),
        "codex_version": "codex-fixture-version",
        "run_id": "run-fixture-1",
        "surface": "C",
        "scenario_id": "scenario-fixture-1",
        "base_sha": BASE,
        "candidate_fingerprint": FINGERPRINT,
    }
    values.update(overrides)
    return capture.capture_from_completed_process(**values)  # type: ignore[arg-type]


class RawCaptureTests(unittest.TestCase):
    def test_retains_exact_bytes_and_records_outer_metadata(self) -> None:
        item = record()
        self.assertIs(item.raw_stdout, RAW)
        self.assertEqual(item.raw_stdout_sha256, hashlib.sha256(RAW).hexdigest())
        self.assertEqual(item.stdout_bytes, len(RAW))
        self.assertEqual(item.event_lines, 2)
        self.assertEqual(item.outer_runtime_ms, 37)
        self.assertEqual(item.terminal_state, "completed")

    def test_independent_rehash_and_recount_pass(self) -> None:
        item = record()
        result = capture.verify_record(item, bytes(RAW))
        self.assertEqual(result["status"], "RAW_CAPTURE_VERIFIED")
        self.assertEqual(result["event_lines"], 2)

    def test_tampered_bytes_fail_closed(self) -> None:
        item = record()
        with self.assertRaisesRegex(capture.CaptureError, "digest_mismatch"):
            capture.verify_record(item, RAW + b"tampered")

    def test_missing_binding_and_empty_raw_fail_closed(self) -> None:
        with self.assertRaisesRegex(capture.CaptureError, "raw_stdout_missing"):
            record(raw_stdout=b"")
        with self.assertRaisesRegex(capture.CaptureError, "scenario_id_missing"):
            record(scenario_id="")

    def test_terminal_state_cannot_fabricate_success(self) -> None:
        with self.assertRaisesRegex(capture.CaptureError, "terminal_exit_mismatch"):
            record(exit_code=1, terminal_state="completed")
        with self.assertRaisesRegex(capture.CaptureError, "terminal_exit_mismatch"):
            record(exit_code=0, terminal_state="failed")

    def test_metadata_excludes_raw_blob(self) -> None:
        metadata = record().metadata()
        self.assertNotIn("raw_stdout", metadata)
        self.assertEqual(metadata["raw_stdout_sha256"], hashlib.sha256(RAW).hexdigest())

    def test_process_boundary_captures_stdout_before_decoding(self) -> None:
        command = (
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'{\\\"type\\\":\\\"thread.started\\\"}\\n')",
        )
        item = capture.capture_command(
            command,
            cwd=str(Path(__file__).resolve().parents[1]),
            stdin_bytes=b"",
            codex_version="python-fixture",
            run_id="run-process-boundary",
            surface="C",
            scenario_id="scenario-process-boundary",
            base_sha=BASE,
            candidate_fingerprint=FINGERPRINT,
        )
        self.assertEqual(item.terminal_state, "completed")
        self.assertEqual(item.raw_stdout, b'{"type":"thread.started"}\n')
        self.assertEqual(capture.verify_record(item)["status"], "RAW_CAPTURE_VERIFIED")


if __name__ == "__main__":
    unittest.main()
