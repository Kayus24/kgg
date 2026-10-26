#!/usr/bin/env python3
"""Exercise real battery subprocesses, including bounded failure and child cleanup."""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kgg_test_battery as battery


def process_state(pid: int) -> tuple[str, str] | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return fields[19], fields[0]  # Start time identifies the process; Z/X are no longer running.


def is_running(identity: tuple[int, int, str]) -> bool:
    state = process_state(identity[1])
    return bool(state and state[0] == identity[2] and state[1] not in {"Z", "X"})


def fixture(code: str, ready: Path) -> str:
    # /proc may be mounted outside our PID namespace: report both PIDs and the start time.
    return (
        "import os, time; from pathlib import Path; stat=Path('/proc/self/stat').read_text(); "
        f"Path({str(ready)!r}).write_text(' '.join([str(os.getpid()), stat.split()[0], "
        "stat.rsplit(')', 1)[1].split()[19]])); " + code
    )


class CommandLifetimeTests(unittest.TestCase):
    def run_python(self, code: str, *, cwd: Path | None = None) -> None:
        battery.run([sys.executable, "-c", code], cwd=cwd or battery.ROOT)

    def wait_ready(self, ready: Path, proc: subprocess.Popen, owned: list[tuple[int, int, str]]) -> tuple[int, int, str]:
        deadline = time.monotonic() + 5
        while proc.poll() is None and time.monotonic() < deadline:
            try:
                pid, proc_pid, started = ready.read_text().split()
                identity = (int(pid), int(proc_pid), started)
            except (FileNotFoundError, ValueError):
                time.sleep(0.01)
                continue
            owned.append(identity)
            self.assertTrue(is_running(identity), "fixture child exited before its handshake")
            return identity
        self.fail("child handshake missing")

    def assert_stopped(self, identity: tuple[int, int, str]) -> None:
        deadline = time.monotonic() + 2
        while is_running(identity) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(is_running(identity), "battery left its owned child running")

    @staticmethod
    def cleanup(owned: list[tuple[int, int, str]], proc: subprocess.Popen | None) -> None:
        for identity in reversed(owned):
            if is_running(identity):
                try:
                    pid = identity[0]
                    if os.getpgid(pid) == pid:
                        os.killpg(pid, signal.SIGKILL)
                    else:
                        os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if proc is not None:
            if proc.poll() is None:  # Also cover failure before the fixture handshake.
                try:
                    if os.getpgid(proc.pid) == proc.pid:
                        os.killpg(proc.pid, signal.SIGKILL)
                    else:
                        proc.kill()
                except ProcessLookupError:
                    pass
            proc.communicate(timeout=5)

    def test_success_and_working_directory_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_python("from pathlib import Path; Path('result').write_text('ok')", cwd=root)
            self.assertEqual((root / "result").read_text(), "ok")

    def test_nonzero_exit_is_still_a_failure(self) -> None:
        with self.assertRaisesRegex(battery.BatteryError, r"Command failed \(7\)"):
            self.run_python("raise SystemExit(7)")

    def test_configured_timeout_rejects_a_slow_command(self) -> None:
        with patch.dict(os.environ, {"KGG_TEST_COMMAND_TIMEOUT_SECONDS": "0.15"}):
            began = time.monotonic()
            with self.assertRaisesRegex(battery.BatteryError, "TIMEOUT"):
                self.run_python("import time; time.sleep(0.7)")
            self.assertLess(time.monotonic() - began, 3)

    def test_invalid_timeout_does_not_launch_a_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for value in ["0", "-1", "nan", "inf", "invalid", ""]:
                with self.subTest(value=value):
                    with patch.dict(os.environ, {"KGG_TEST_COMMAND_TIMEOUT_SECONDS": value}):
                        with self.assertRaisesRegex(battery.BatteryError, "positive finite"):
                            self.run_python("from pathlib import Path; Path('launched').write_text('yes')", cwd=root)
                    self.assertFalse((root / "launched").exists())

    @unittest.skipUnless(sys.platform == "linux", "real process-tree liveness uses Linux /proc")
    def test_timeout_stops_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = fixture("time.sleep(30)", root / "ready")
            parent = fixture(
                "import subprocess, sys; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}]).wait()", root / "parent-ready"
            )
            owned = []
            proc = None
            real_popen = subprocess.Popen

            def ready_popen(*args, **kwargs):
                nonlocal proc
                proc = real_popen(*args, **kwargs)
                self.wait_ready(root / "parent-ready", proc, owned)
                self.wait_ready(root / "ready", proc, owned)
                return proc  # Start the short command timeout only after the real child is ready.

            try:
                with patch.dict(os.environ, {"KGG_TEST_COMMAND_TIMEOUT_SECONDS": "0.15"}):
                    with patch.object(battery.subprocess, "Popen", side_effect=ready_popen):
                        with self.assertRaisesRegex(battery.BatteryError, "TIMEOUT"):
                            self.run_python(parent, cwd=root)
                self.assert_stopped(owned[-1])
            finally:
                self.cleanup(owned, proc)

    @unittest.skipUnless(sys.platform == "linux", "real SIGINT/process-tree liveness uses Linux /proc")
    def test_interrupt_stops_owned_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = fixture("time.sleep(30)", root / "ready")
            caller = fixture(
                f"import sys; sys.path.insert(0, {str(Path(battery.__file__).parent)!r}); "
                "import kgg_test_battery as battery; "
                f"battery.run([sys.executable, '-c', {child!r}], cwd=__import__('pathlib').Path({str(root)!r}))", root / "parent-ready"
            )
            owned = []
            proc = subprocess.Popen([sys.executable, "-c", caller], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            try:
                self.wait_ready(root / "parent-ready", proc, owned)
                child_identity = self.wait_ready(root / "ready", proc, owned)
                proc.send_signal(signal.SIGINT)
                _, error = proc.communicate(timeout=5)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(b"KeyboardInterrupt", error)
                self.assert_stopped(child_identity)
            finally:
                self.cleanup(owned, proc)

    def test_interrupt_is_preserved_when_cleanup_fails(self) -> None:
        command = [sys.executable, "-c", "raise SystemExit(0)"]
        with patch.object(battery.subprocess, "Popen") as popen:
            popen.return_value.wait.side_effect = KeyboardInterrupt
            with patch.object(battery, "stop_command_tree", side_effect=OSError("synthetic cleanup failure")):
                with self.assertRaises(KeyboardInterrupt):
                    battery.run(command)


if __name__ == "__main__":
    unittest.main()
