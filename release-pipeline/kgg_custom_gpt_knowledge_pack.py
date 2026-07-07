#!/usr/bin/env python3
"""Generate the uploadable KGG Custom GPT knowledge pack."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "docs" / "kgg-custom-gpt-knowledge-pack.md"

SOURCES = [
    "docs/kgg-gpt-context.md",
    "docs/kgg-custom-gpt-playbook.md",
    "docs/kgg-custom-gpt-action-schema.md",
    "docs/kgg-custom-gpt-preview-runbook.md",
    "docs/kgg-custom-gpt-preview-report-template.md",
    "docs/kgg-custom-gpt-negative-examples.md",
    "docs/kgg-custom-gpt-test-prompts.md",
    "docs/kgg-custom-gpt-expected-results.md",
    "docs/kgg-custom-gpt-test-report.md",
    "docs/kgg-custom-gpt-cycle-report.md",
    "docs/kgg-gpt-bug-lessons.md",
    "docs/kgg-gpt-patch-patterns.md",
    "docs/kgg-gpt-area-routes.md",
]


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip() + "\n"


def read_source(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise RuntimeError(f"missing knowledge source: {path}")
    return normalize(full.read_text(encoding="utf-8"))


def source_digest(items: list[tuple[str, str]]) -> str:
    hasher = hashlib.sha256()
    for path, text in items:
        hasher.update(path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(text.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()[:16]


def render_pack() -> str:
    items = [(path, read_source(path)) for path in SOURCES]
    digest = source_digest(items)
    lines = [
        "# KGG Custom GPT Knowledge Pack",
        "",
        "This file is generated for upload into the Custom GPT Wissen/Knowledge area.",
        "The short GPT editor instructions should stay strict and compact; long context, runbooks, routing, bug lessons and eval fixtures live here.",
        "",
        f"Source digest: `{digest}`",
        "",
        "## Usage Rules",
        "",
        "- Reload this pack before KGG patch, Preview/Test-APK, Admin-Beta or run-diagnosis work.",
        "- If this pack conflicts with live GitHub files, trust the live source files and report stale knowledge.",
        "- Do not claim Preview, Test-APK or Admin-Beta success without run/artifact/HTTP evidence.",
        "- Treat `ci_tooling` separately from app patch failures.",
        "- Positive E2E push-test means both `publish_preview` and `publish_admin_beta` succeeded.",
        "",
        "## Source Files",
        "",
    ]
    for path, _text in items:
        lines.append(f"- `{path}`")
    for path, text in items:
        lines.extend(
            [
                "",
                "---",
                "",
                f"# Source: {path}",
                "",
                text.rstrip(),
            ]
        )
    return normalize("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check the KGG Custom GPT knowledge pack.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write docs/kgg-custom-gpt-knowledge-pack.md.")
    group.add_argument("--check", action="store_true", help="Fail if the knowledge pack is stale.")
    group.add_argument("--print", action="store_true", help="Print generated knowledge pack.")
    args = parser.parse_args()

    try:
        expected = render_pack()
        if args.print:
            print(expected, end="")
            return 0
        if args.write:
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(expected, encoding="utf-8", newline="\n")
            print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
            return 0
        if not OUTPUT_PATH.exists():
            raise RuntimeError("docs/kgg-custom-gpt-knowledge-pack.md is missing. Run release-pipeline/kgg_custom_gpt_knowledge_pack.py --write.")
        current = normalize(OUTPUT_PATH.read_text(encoding="utf-8"))
        if current != expected:
            raise RuntimeError("docs/kgg-custom-gpt-knowledge-pack.md is stale. Run release-pipeline/kgg_custom_gpt_knowledge_pack.py --write.")
        print("KGG Custom GPT knowledge pack OK")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
