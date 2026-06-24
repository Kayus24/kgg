#!/usr/bin/env python3
"""Run local/static KGG smoke-test batteries.

Default mode is intentionally non-mutating: no push, no PR, no live GitHub
write. Use --live-mobile-inbox only when a real Admin beta release should be
created as part of the smoke test.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BatteryError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def run(args: list[str], *, cwd: Path = ROOT) -> None:
    log("+ " + " ".join(args))
    proc = subprocess.run(args, cwd=str(cwd))
    if proc.returncode != 0:
        raise BatteryError(f"Command failed ({proc.returncode}): {' '.join(args)}")


def node_executable() -> str:
    configured = os.environ.get("KGG_NODE") or os.environ.get("NODE")
    if configured and Path(configured).exists():
        return configured

    found = shutil.which("node")
    if found:
        return found

    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / ("node.exe" if os.name == "nt" else "node")
    )
    if bundled.exists():
        return str(bundled)

    raise BatteryError("Node.js not found. Install node or set KGG_NODE to the node executable.")


def run_mobile_inbox(live: bool) -> None:
    log("== Mobile-Inbox battery ==")
    args = [sys.executable, "release-pipeline/mobile_inbox_live_smoke.py"]
    if not live:
        args.append("--dry-run")
    run(args)


def run_html_logic(suite: str) -> None:
    log(f"== HTML logic battery: {suite} ==")
    run([node_executable(), "release-pipeline/kgg_html_logic_smoke.js", "--suite", suite])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KGG local/static test batteries")
    parser.add_argument("--suite", choices=["all", "mobile-inbox", "sync", "textblocks"], default="all")
    parser.add_argument(
        "--live-mobile-inbox",
        action="store_true",
        help="Run the real Mobile-Inbox live smoke; this intentionally creates a new Admin beta release.",
    )
    args = parser.parse_args()

    try:
      if args.suite in ("all", "mobile-inbox"):
          run_mobile_inbox(args.live_mobile_inbox)
      if args.suite == "all":
          run_html_logic("all")
      elif args.suite in ("sync", "textblocks"):
          run_html_logic(args.suite)
      log("KGG test battery OK")
      return 0
    except BatteryError as exc:
      print(f"ERROR: {exc}", file=sys.stderr)
      return 1


if __name__ == "__main__":
    raise SystemExit(main())
