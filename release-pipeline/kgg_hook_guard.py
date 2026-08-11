#!/usr/bin/env python3
"""Install or verify the repository-local KGG Git hooks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from kgg_git_environment import sanitized_git_environment


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HOOKS_PATH = ".githooks"


class HookGuardError(RuntimeError):
    pass


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        env=sanitized_git_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and process.returncode != 0:
        detail = (process.stderr or process.stdout).strip() or "unknown git error"
        raise HookGuardError(detail)
    return process


def repository_root(root: Path) -> Path:
    process = run_git(root, "rev-parse", "--show-toplevel")
    return Path(process.stdout.strip()).resolve()


def configured_hooks_path(root: Path) -> str | None:
    process = run_git(
        root,
        "config",
        "--local",
        "--get",
        "core.hooksPath",
        check=False,
    )
    if process.returncode == 1:
        return None
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip() or "cannot read core.hooksPath"
        raise HookGuardError(detail)
    return process.stdout.strip() or None


def resolved_hooks_path(root: Path, configured: str) -> Path:
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def check_hooks(root: Path) -> None:
    root = root.resolve()
    if repository_root(root) != root:
        raise HookGuardError(f"not the repository root: {root}")
    hook = root / EXPECTED_HOOKS_PATH / "pre-commit"
    if not hook.is_file():
        raise HookGuardError(f"missing tracked pre-commit hook: {hook}")
    configured = configured_hooks_path(root)
    if configured is None:
        raise HookGuardError(
            "core.hooksPath is not configured; run kgg_hook_guard.py --install"
        )
    if resolved_hooks_path(root, configured) != (root / EXPECTED_HOOKS_PATH).resolve():
        raise HookGuardError(
            f"core.hooksPath points to {configured!r}, expected {EXPECTED_HOOKS_PATH!r}"
        )


def install_hooks(root: Path) -> None:
    root = root.resolve()
    if repository_root(root) != root:
        raise HookGuardError(f"not the repository root: {root}")
    if not (root / EXPECTED_HOOKS_PATH / "pre-commit").is_file():
        raise HookGuardError("tracked .githooks/pre-commit is missing")
    run_git(root, "config", "--local", "core.hooksPath", EXPECTED_HOOKS_PATH)
    check_hooks(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        if args.install:
            install_hooks(ROOT)
        else:
            check_hooks(ROOT)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "hooksPath": EXPECTED_HOOKS_PATH,
                    "mode": "install" if args.install else "check",
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
