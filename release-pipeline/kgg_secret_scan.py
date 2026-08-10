#!/usr/bin/env python3
"""Scan every tracked text file for token-shaped secrets without leaking values."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Keep prefixes split in source so this scanner and its tests cannot become
# self-matching fixtures. Patterns stay compatible with both Git ERE and Python.
SECRET_PATTERNS = (
    ("GitHub classic token", "gh" + r"[pousr]_[A-Za-z0-9_]{20,}"),
    ("GitHub fine-grained token", "github" + r"_pat_[A-Za-z0-9_]{20,}"),
    ("OpenAI project key", "s" + r"k-proj-[A-Za-z0-9_-]{20,}"),
    ("OpenAI key", "s" + r"k-[A-Za-z0-9_-]{20,}"),
    ("Google API key", "AI" + r"za[0-9A-Za-z_-]{25,}"),
    ("AWS access key ID", "A" + r"(KIA|SIA)[0-9A-Z]{16}"),
    ("Slack token", "xo" + r"x[baprs]-[0-9A-Za-z-]{10,}"),
    ("Stripe live secret key", "(s" + r"k|rk)_live_[0-9A-Za-z]{16,}"),
    (
        "private key header",
        "-" * 5 + r"BEGIN[ \t]+([A-Z0-9]+[ \t]+)*PRIVATE[ \t]+KEY" + "-" * 5,
    ),
)


class SecretScanError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecretFinding:
    path: str


def _redact(text: str) -> str:
    redacted = text
    for _label, pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.ASCII)
    return "".join(char if char.isprintable() else "?" for char in redacted)


def _git_grep_paths(root: Path, *, cached: bool) -> set[str]:
    args = ["git", "grep", "-I", "-l", "-z", "-E"]
    if cached:
        args.append("--cached")
    for _label, pattern in SECRET_PATTERNS:
        args.extend(["-e", pattern])
    args.append("--")

    proc = subprocess.run(
        args,
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode == 1:
        return set()
    if proc.returncode != 0:
        detail = _redact(proc.stderr.decode("utf-8", errors="replace").strip())
        suffix = f": {detail}" if detail else ""
        source = "index" if cached else "worktree"
        raise SecretScanError(
            f"git grep failed for {source} with exit code {proc.returncode}{suffix}"
        )

    return {
        raw_path.decode("utf-8", errors="replace")
        for raw_path in proc.stdout.split(b"\0")
        if raw_path
    }


def scan_tracked_text(root: Path = ROOT) -> list[SecretFinding]:
    """Return matches from tracked worktree files and the staged index snapshot."""

    paths = _git_grep_paths(root, cached=False)
    paths.update(_git_grep_paths(root, cached=True))
    return [SecretFinding(path=path) for path in sorted(paths)]


def redacted_report(findings: list[SecretFinding]) -> list[str]:
    return [f"{_redact(finding.path)}: potential secret [REDACTED]" for finding in findings]


def main(root: Path = ROOT) -> int:
    try:
        findings = scan_tracked_text(root)
    except SecretScanError as exc:
        print(f"Secret scan ERROR: {_redact(str(exc))}", file=sys.stderr)
        return 2

    if findings:
        for line in redacted_report(findings):
            print(line, file=sys.stderr)
        print(
            f"Secret scan FAILED: {len(findings)} tracked text file(s) contain token-shaped data; values redacted.",
            file=sys.stderr,
        )
        return 1

    print("Secret scan OK: tracked worktree and index text checked; binary files ignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
