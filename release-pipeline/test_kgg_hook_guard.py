#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kgg_hook_guard as hook_guard  # noqa: E402
from kgg_git_environment import sanitized_git_environment  # noqa: E402


class HookGuardTests(unittest.TestCase):
    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=sanitized_git_environment(),
            check=True,
        )

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-hook-guard-")
        self.root = Path(self.temp.name)
        self._git("init", "--quiet")
        hook_dir = self.root / ".githooks"
        hook_dir.mkdir()
        (hook_dir / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_install_sets_and_verifies_repository_local_hooks(self) -> None:
        self.assertIsNone(hook_guard.configured_hooks_path(self.root))
        hook_guard.install_hooks(self.root)
        self.assertEqual(
            hook_guard.EXPECTED_HOOKS_PATH,
            hook_guard.configured_hooks_path(self.root),
        )
        hook_guard.check_hooks(self.root)

    def test_check_rejects_missing_configuration(self) -> None:
        with self.assertRaisesRegex(hook_guard.HookGuardError, "--install"):
            hook_guard.check_hooks(self.root)

    def test_check_rejects_wrong_hooks_directory(self) -> None:
        self._git("config", "--local", "core.hooksPath", ".other-hooks")
        with self.assertRaisesRegex(hook_guard.HookGuardError, "expected"):
            hook_guard.check_hooks(self.root)

    def test_check_accepts_absolute_repository_hook_path(self) -> None:
        self._git(
            "config",
            "--local",
            "core.hooksPath",
            str((self.root / ".githooks").resolve()),
        )
        hook_guard.check_hooks(self.root)

    def test_sanitized_environment_removes_parent_repository_routing(self) -> None:
        clean = sanitized_git_environment(
            {
                "PATH": "kept",
                "GIT_DIR": "parent/.git",
                "GIT_INDEX_FILE": "parent/index",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": ".other-hooks",
            }
        )
        self.assertEqual({"PATH": "kept"}, clean)


if __name__ == "__main__":
    unittest.main(verbosity=2)
