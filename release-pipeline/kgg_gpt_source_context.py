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
ROUTES_JSON_PATH = ROOT / "docs" / "kgg-gpt-area-routes.json"
ROUTES_MD_PATH = ROOT / "docs" / "kgg-gpt-area-routes.md"
LINES_PER_CHUNK = 420

AREA_ROUTES = [
    {
        "id": "tablet-layout",
        "triggers": ["tablet", "layout", "splitter", "spaltenbreite", "uebungsdatenbank", "planbereich"],
        "markers": [
            "tabletLayoutFreeTools",
            "tabletLayoutResizeHandle",
            "--kgg-tablet-left-col",
            "--kgg-tablet-ui-scale",
            "updateTabletLayoutHandle",
            "initTabletLayoutControls",
        ],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "notes": "Plus/Minus controls scale; horizontal drag controls the left column width.",
    },
    {
        "id": "phone-layout",
        "triggers": ["phone", "handy", "dock", "drawer", "scan button", "759"],
        "markers": [
            "kggPhoneAdminMenu",
            "phonePhotoMenuToggle",
            "kggPhoneHasPlan",
            "phoneTextFocus",
            "max-width:759px",
        ],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "notes": "Do not change the 759/760 px breakpoint incidentally.",
    },
    {
        "id": "qr-patient",
        "triggers": ["qr", "patient", "patienten-app", "plan qr"],
        "markers": ["finishWithPatientApp", "KGGH2", "tryApplyKggSetupFromHash", "openKggTherapistAppOnlyQr"],
        "tests": ["cmd /c release-pipeline\\run-kgg-tests.cmd --level critical"],
        "notes": "Patient output must not expose raw JSON, Base64 or debug payloads.",
    },
    {
        "id": "pdf",
        "triggers": ["pdf", "druck", "trainingsplan"],
        "markers": ["finishWithPdf", "KGGOfflineJsPDF", "attachKggPdfExerciseThumbnails"],
        "tests": ["cmd /c release-pipeline\\run-kgg-tests.cmd --level critical"],
        "notes": "PDF changes need bounded thumbnail/card behavior.",
    },
    {
        "id": "android-apk",
        "triggers": ["apk", "android", "preview app", "icon"],
        "markers": ["KGGAndroidPdf", "KGGNativeSync", "PREVIEW_MANIFEST_URL"],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.",
        ],
        "notes": "Android/APK is protected unless Max explicitly asks for it.",
    },
    {
        "id": "sync",
        "triggers": ["sync", "paket", "uebungsbank", "peer", "kollegen"],
        "markers": ["KGGDataStore", "kgg_sync_bundle", "nativeExerciseBankSync", "KGGNativeSync"],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite sync --level regression",
        ],
        "notes": "Sync export must exclude patients and secrets.",
    },
    {
        "id": "parser-textblocks",
        "triggers": ["parser", "textblock", "satz", "ocr"],
        "markers": ["parseExerciseText", "textBlocks", "scanState"],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite textblocks --level regression",
        ],
        "notes": "Parser and text-block behavior must not create bogus Satz cards.",
    },
    {
        "id": "preview-gate",
        "triggers": ["preview", "beta", "test-html", "custom gpt", "write gate"],
        "markers": ["kgg-gpt-preview-banner", "kgg-source-truth", "kgg-changelog"],
        "tests": [
            "python release-pipeline\\kgg_gpt_payload_preflight.py --self-test",
            "python release-pipeline\\kgg_gpt_eval.py",
        ],
        "notes": "A missing preview URL is not success; inspect the GitHub run first.",
    },
]


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


def marker_locations(lines: list[str], marker: str) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for index, line in enumerate(lines, start=1):
        if marker in line:
            chunk_number = (index - 1) // LINES_PER_CHUNK
            matches.append(
                {
                    "marker": marker,
                    "line": index,
                    "chunk": f"chunk-{chunk_number:03d}.md",
                    "path": f"docs/kgg-gpt-source/chunk-{chunk_number:03d}.md",
                }
            )
    return matches[:8]


def render_area_routes(source: str) -> tuple[str, str]:
    lines = source.splitlines()
    routes = []
    for route in AREA_ROUTES:
        marker_entries = []
        chunks = set()
        for marker in route["markers"]:
            locations = marker_locations(lines, marker)
            if locations:
                marker_entries.append(locations[0])
                chunks.update(item["path"] for item in locations)
            else:
                marker_entries.append({"marker": marker, "line": None, "chunk": None, "path": None})
        routes.append(
            {
                "id": route["id"],
                "triggers": route["triggers"],
                "markers": marker_entries,
                "sourceChunks": sorted(chunks),
                "tests": route["tests"],
                "notes": route["notes"],
            }
        )
    route_json = {
        "kind": "kgg_gpt_area_routes",
        "version": 1,
        "sourcePath": "kgg-update/index.html",
        "linesPerChunk": LINES_PER_CHUNK,
        "routes": routes,
    }
    md_lines = [
        "# KGG GPT Area Routes",
        "",
        "Generated from `kgg-update/index.html`. Use this before loading source chunks.",
        "",
    ]
    for route in routes:
        md_lines.extend(
            [
                f"## {route['id']}",
                "",
                "- Triggers: " + ", ".join(f"`{item}`" for item in route["triggers"]),
                "- Source chunks: " + (", ".join(f"`{item}`" for item in route["sourceChunks"]) or "none found"),
                "- Tests: " + "; ".join(f"`{item}`" for item in route["tests"]),
                f"- Notes: {route['notes']}",
                "- Markers:",
            ]
        )
        for marker in route["markers"]:
            if marker["path"]:
                md_lines.append(f"  - `{marker['marker']}`: `{marker['path']}` line {marker['line']}")
            else:
                md_lines.append(f"  - `{marker['marker']}`: not found")
        md_lines.append("")
    return (
        json.dumps(route_json, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        "\n".join(md_lines).rstrip() + "\n",
    )


def render_outputs() -> dict[Path, str]:
    source = read_source()
    chunks = chunk_text(source)
    routes_json, routes_md = render_area_routes(source)
    index = {
        "kind": "kgg_gpt_source_index",
        "version": 1,
        "sourcePath": "kgg-update/index.html",
        "sourceSha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "linesPerChunk": LINES_PER_CHUNK,
        "areaRoutes": {
            "json": "docs/kgg-gpt-area-routes.json",
            "markdown": "docs/kgg-gpt-area-routes.md",
        },
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
        ROUTES_JSON_PATH: routes_json,
        ROUTES_MD_PATH: routes_md,
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
