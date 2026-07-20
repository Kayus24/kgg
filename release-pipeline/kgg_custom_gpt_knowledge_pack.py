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
    "docs/kgg-gpt-bug-lessons.md",
    "docs/kgg-gpt-patch-patterns.md",
    "docs/kgg-gpt-area-routes.md",
]

CURATED_PACKS = {
    "docs/kgg-custom-gpt-knowledge-architecture.md": [
        "docs/kgg-gpt-context.md",
        "docs/kgg-gpt-area-routes.md",
    ],
    "docs/kgg-custom-gpt-knowledge-operations.md": [
        "docs/kgg-custom-gpt-playbook.md",
        "docs/kgg-custom-gpt-action-schema.md",
        "docs/kgg-custom-gpt-preview-runbook.md",
        "docs/kgg-custom-gpt-preview-report-template.md",
    ],
    "docs/kgg-custom-gpt-knowledge-safety.md": [
        "docs/kgg-custom-gpt-negative-examples.md",
        "docs/kgg-gpt-bug-lessons.md",
        "docs/kgg-gpt-patch-patterns.md",
    ],
    "docs/kgg-custom-gpt-knowledge-testing.md": [
        "docs/kgg-custom-gpt-test-prompts.md",
        "docs/kgg-custom-gpt-expected-results.md",
        "docs/kgg-custom-gpt-test-report.md",
        "docs/kgg-custom-gpt-cycle-report.md",
    ],
}


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


def render_source_pack(title: str, purpose: str, source_paths: list[str]) -> str:
    items = [(path, read_source(path)) for path in source_paths]
    digest = source_digest(items)
    lines = [
        f"# {title}",
        "",
        purpose,
        "",
        f"Source digest: `{digest}`",
        "",
        "## Usage Rules",
        "",
        "- Reload this pack before KGG patch, Preview/Test-APK, Admin-Beta or run-diagnosis work.",
        "- If this pack conflicts with live GitHub files, trust the live source files and report stale knowledge.",
        "- Read current cycle and run status from GitHub Actions, not from this static pack.",
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


def render_pack() -> str:
    return render_source_pack(
        "KGG Custom GPT Knowledge Pack",
        "This generated compatibility pack contains the complete production knowledge set. Prefer the four smaller curated packs in the GPT editor so retrieval stays focused.",
        SOURCES,
    )


def render_curated_packs() -> dict[Path, str]:
    purposes = {
        "docs/kgg-custom-gpt-knowledge-architecture.md": "Generated production knowledge for live app structure, source routing and current release context.",
        "docs/kgg-custom-gpt-knowledge-operations.md": "Generated production knowledge for modular payloads, Actions, Preview/Test-App and Admin-Beta operations.",
        "docs/kgg-custom-gpt-knowledge-safety.md": "Generated production knowledge for protected areas, regression history and safe patch patterns.",
        "docs/kgg-custom-gpt-knowledge-testing.md": "Generated production regression fixtures and expected operational responses. Never upload this file to the isolated Eval GPT.",
    }
    result = {}
    for filename, source_paths in CURATED_PACKS.items():
        title = Path(filename).stem.replace("kgg-custom-gpt-knowledge-", "KGG GPT ").replace("-", " ").title()
        result[ROOT / filename] = render_source_pack(title, purposes[filename], source_paths)
    return result


def render_eval_pack() -> str:
    lines = [
        "# KGG Isolated Eval GPT Knowledge",
        "",
        "This generated pack is intentionally solution-free. It must be the only Knowledge file uploaded to the isolated Repair-Lab GPT.",
        "",
        "## Isolation",
        "",
        "- Use only the KGG Blind Repair Lab Source and Evaluator Actions.",
        "- Do not use Web Search, production GitHub Actions, the intact main app, golden source, hidden assertions or production test fixtures.",
        "- Read the opaque challenge manifest and only the broken source chunks needed for the observed symptom.",
        "- Return a modular v2 payload with exactly the fields listed by the challenge.",
        "- The patch must contain `__KGG_PATCH_ID__` and must restore behavior through a new patch module; never patch a repository path directly.",
        "- Copy all exact required test commands from the challenge manifest.",
        "- Submit one attempt, inspect the real workflow run and failed step, then make a materially different correction.",
        "- After three consecutive failures in the same failure class, stop and report the repeated class instead of guessing again.",
        "- Never claim PASS without a completed successful evaluator run and its report artifact.",
        "",
        "## Payload Shape",
        "",
        "Required fields: `request_id`, `title`, `summary`, `version_slug`, `touched_areas`, `required_tests`, `patch_content`.",
        "Forbidden fields: `operations`, `replace_exact`, `old_text`, `new_text`, `path`, `file`, `filename`.",
        "",
        "## Test Integrity",
        "",
        "Do not ask for hidden case names, evaluator code, internal manifests, sample payloads or intact source. A repair is valid only when it follows from the symptom and broken full-app source.",
    ]
    return normalize("\n".join(lines))


def expected_outputs() -> dict[Path, str]:
    outputs = {OUTPUT_PATH: render_pack(), ROOT / "docs" / "kgg-custom-gpt-eval-knowledge.md": render_eval_pack()}
    outputs.update(render_curated_packs())
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check the KGG Custom GPT knowledge pack.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write docs/kgg-custom-gpt-knowledge-pack.md.")
    group.add_argument("--check", action="store_true", help="Fail if the knowledge pack is stale.")
    group.add_argument("--print", action="store_true", help="Print generated knowledge pack.")
    args = parser.parse_args()

    try:
        outputs = expected_outputs()
        if args.print:
            print(outputs[OUTPUT_PATH], end="")
            return 0
        if args.write:
            for path, expected in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8", newline="\n")
                print(f"Wrote {path.relative_to(ROOT)}")
            return 0
        for path, expected in outputs.items():
            if not path.exists():
                raise RuntimeError(f"{path.relative_to(ROOT)} is missing. Run release-pipeline/kgg_custom_gpt_knowledge_pack.py --write.")
            current = normalize(path.read_text(encoding="utf-8"))
            if current != expected:
                raise RuntimeError(f"{path.relative_to(ROOT)} is stale. Run release-pipeline/kgg_custom_gpt_knowledge_pack.py --write.")
        print(f"KGG Custom GPT knowledge packs OK ({len(outputs)} files)")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
