#!/usr/bin/env python3
"""Generate chunked KGG source context for the private GPT."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "kgg-update" / "index.html"
INDEX_PATH = ROOT / "docs" / "kgg-gpt-source-index.json"
CHUNK_DIR = ROOT / "docs" / "kgg-gpt-source"
LINES_PER_CHUNK = 420


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip() + "\n"


def read_source() -> str:
    return normalize(SOURCE_PATH.read_text(encoding="utf-8", errors="replace"))


def chunk_text(source: str) -> dict[Path, str]:
    lines = source.splitlines()
    outputs: dict[Path, str] = {}
    for index, start in enumerate(range(0, len(lines), LINES_PER_CHUNK)):
        end = min(start + LINES_PER_CHUNK, len(lines))
        chunk_lines = lines[start:end]
        name = f"chunk-{index:03d}.md"
        body = [
            f"# KGG Source Chunk {index:03d}",
            "",
            f"- Source: `kgg-update/index.html`",
            f"- Lines: {start + 1}-{end}",
            "",
            "```html",
            *chunk_lines,
            "```",
            "",
        ]
        outputs[CHUNK_DIR / name] = "\n".join(body)
    return outputs


def render_outputs() -> dict[Path, str]:
    source = read_source()
    chunks = chunk_text(source)
    index = {
        "kind": "kgg_gpt_source_index",
        "version": 1,
        "sourcePath": "kgg-update/index.html",
        "sourceSha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "linesPerChunk": LINES_PER_CHUNK,
        "chunks": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "name": path.name,
                "startLine": (number * LINES_PER_CHUNK) + 1,
                "endLine": min((number + 1) * LINES_PER_CHUNK, len(source.splitlines())),
            }
            for number, path in enumerate(sorted(chunks))
        ],
    }
    outputs: dict[Path, str] = {
        INDEX_PATH: json.dumps(index, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
    }
    outputs.update({path: normalize(text) for path, text in chunks.items()})
    return outputs


def clean_chunk_dir() -> None:
    if CHUNK_DIR.exists():
        shutil.rmtree(CHUNK_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check KGG GPT source chunks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    outputs = render_outputs()
    if args.write:
        clean_chunk_dir()
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"Wrote {path.relative_to(ROOT)}")
        return 0

    errors: list[str] = []
    expected_paths = set(outputs)
    current_chunks = set(CHUNK_DIR.glob("chunk-*.md")) if CHUNK_DIR.exists() else set()
    stale_extra = current_chunks - {path for path in expected_paths if path.parent == CHUNK_DIR}
    for path in sorted(stale_extra):
        errors.append(f"stale extra chunk: {path.relative_to(ROOT)}")
    for path, expected in outputs.items():
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
            continue
        current = normalize(path.read_text(encoding="utf-8"))
        if current != normalize(expected):
            errors.append(f"stale: {path.relative_to(ROOT)}")
    if errors:
        print("ERROR: KGG GPT source context is stale. Run release-pipeline/kgg_gpt_source_context.py --write.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("KGG GPT source context OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
