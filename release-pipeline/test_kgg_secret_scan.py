import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_secret_scan as secret_scan


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="kgg-secret-scan-")
        self.root = Path(self.temp_dir.name)
        self._git("init", "--quiet")
        self._git("config", "user.email", "scan-test@example.invalid")
        self._git("config", "user.name", "KGG Secret Scan Test")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _track_text(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._git("add", "-f", "--", relative)
        return path

    def test_supported_secret_shapes_are_detected(self):
        fixture = self._track_text("fixture.txt", "safe\n")
        examples = {
            "github-classic": "gh" + "p_" + "A" * 36,
            "github-fine-grained": "github" + "_pat_" + "A" * 30,
            "openai": "s" + "k-" + "A" * 32,
            "openai-project": "s" + "k-proj-" + "A" * 32,
            "google": "AI" + "za" + "A" * 35,
            "aws": "A" + "KIA" + "A" * 16,
            "slack": "xo" + "xb-" + "1234567890-ABCDEFGHIJ",
            "stripe": "s" + "k_live_" + "A" * 24,
            "private-key": "-" * 5 + "BEGIN RSA " + "PRIVATE " + "KEY" + "-" * 5,
        }

        for name, value in examples.items():
            with self.subTest(name=name):
                fixture.write_text(value + "\n", encoding="utf-8")
                findings = secret_scan.scan_tracked_text(self.root)
                self.assertEqual([secret_scan.SecretFinding("fixture.txt")], findings)

    def test_rgignore_cannot_hide_tracked_text_and_untracked_files_are_excluded(self):
        self._track_text(".rgignore", "ignored.txt\nuntracked.txt\n")
        token = "AI" + "za" + "B" * 35
        self._track_text("ignored.txt", token + "\n")
        (self.root / "untracked.txt").write_text(token + "\n", encoding="utf-8")

        findings = secret_scan.scan_tracked_text(self.root)

        self.assertEqual([secret_scan.SecretFinding("ignored.txt")], findings)

    def test_binary_tracked_file_is_ignored(self):
        token = ("gh" + "p_" + "C" * 36).encode("ascii")
        (self.root / "fixture.bin").write_bytes(b"\x89PNG\r\n\x1a\n\x00" + token)
        self._git("add", "-f", "--", "fixture.bin")

        self.assertEqual([], secret_scan.scan_tracked_text(self.root))

    def test_staged_secret_cannot_be_hidden_by_safe_worktree_content(self):
        token = "xo" + "xb-" + "1234567890-ZYXWVUTSRQ"
        fixture = self._track_text("staged.txt", token + "\n")
        fixture.write_text("safe worktree content\n", encoding="utf-8")

        findings = secret_scan.scan_tracked_text(self.root)

        self.assertEqual([secret_scan.SecretFinding("staged.txt")], findings)

    def test_scanner_and_fixtures_are_not_self_matching(self):
        self._track_text("scanner.py", Path(secret_scan.__file__).read_text(encoding="utf-8"))
        self._track_text("scanner_test.py", Path(__file__).read_text(encoding="utf-8"))

        self.assertEqual([], secret_scan.scan_tracked_text(self.root))

    def test_report_redacts_token_shaped_filename(self):
        token = "s" + "k-proj-" + "D" * 32
        lines = secret_scan.redacted_report(
            [secret_scan.SecretFinding(f"fixtures/{token}.txt")]
        )

        self.assertNotIn(token, lines[0])
        self.assertIn("[REDACTED]", lines[0])

    def test_cli_failure_output_never_echoes_token_shaped_filename(self):
        token = "github" + "_pat_" + "E" * 30
        self._track_text(token + ".txt", token + "\n")
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = secret_scan.main(self.root)

        output = stderr.getvalue()
        self.assertEqual(1, exit_code)
        self.assertNotIn(token, output)
        self.assertIn("[REDACTED]", output)

    def test_pre_commit_always_runs_secret_scan_before_path_filter(self):
        hook = (HERE.parent / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        changed_offset = hook.index('changed="$(git diff --cached')
        early_exit_offset = hook.index("exit 0", changed_offset)

        for command in (
            "python release-pipeline/kgg_secret_scan.py",
            "py -3 release-pipeline/kgg_secret_scan.py",
        ):
            with self.subTest(command=command):
                self.assertLess(hook.index(command), changed_offset)
                self.assertLess(hook.index(command), early_exit_offset)


if __name__ == "__main__":
    unittest.main(verbosity=2)
