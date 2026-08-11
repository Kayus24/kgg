#!/usr/bin/env python3
"""Generate chunked modular KGG source context for the private GPT."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "kgg-update" / "src"
PARTS_PATH = SRC_ROOT / "parts.json"
INDEX_PATH = ROOT / "docs" / "kgg-gpt-source-index.json"
CHUNK_DIR = ROOT / "docs" / "kgg-gpt-source"
ROUTES_JSON_PATH = ROOT / "docs" / "kgg-gpt-area-routes.json"
ROUTES_MD_PATH = ROOT / "docs" / "kgg-gpt-area-routes.md"
MIN_PAYLOAD_BYTES = 12_000
MAX_PAYLOAD_BYTES = 32_768
ROLLING_LINE_WINDOW = 8
BOUNDARY_MASK = 0x01FF
HASH_PREFIX_LENGTH = 16
CHUNK_FILENAME_RE = re.compile(r"^chunk-(?:[0-9]{3}|v2-[0-9a-f]{16})\.md$")
V2_CHUNK_FILENAME_RE = re.compile(r"^chunk-v2-([0-9a-f]{16})\.md$")

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
        "markers": ["finishWithPatientApp", "KGGH2", "tryApplyKggSetupFromHash", "openKggTherapistAppOnlyQr", "handleQrRaw"],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite patient-scan --level regression",
        ],
        "notes": "Patient output must not expose raw JSON, Base64 or debug payloads.",
    },
    {
        "id": "camera-qr",
        "triggers": ["kamera", "camera", "automatischer qr", "zoom", "webview", "barcode detector"],
        "markers": ["KGGNativeCamera", "getCameraCapabilities", "handleQrRaw", "LIVE_VARIANTS", "getUserMedia"],
        "tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite camera-qr --level regression",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite patient-scan --level regression",
        ],
        "notes": "Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.",
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


@dataclass(frozen=True)
class SourceDocument:
    path: str
    payload: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()

    @property
    def lines(self) -> list[bytes]:
        return self.payload.splitlines(keepends=True)


@dataclass(frozen=True)
class SourceChunk:
    source: SourceDocument
    payload: bytes
    start_line: int
    end_line: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()

    @property
    def name(self) -> str:
        return f"chunk-v2-{self.sha256[:HASH_PREFIX_LENGTH]}.md"

    @property
    def path(self) -> str:
        return f"docs/kgg-gpt-source/{self.name}"

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


def normalize_lf_bytes(raw: bytes) -> bytes:
    """Return strict UTF-8 source bytes using LF line endings."""
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    normalized.decode("utf-8", errors="strict")
    if normalized and not normalized.endswith(b"\n"):
        normalized += b"\n"
    return normalized


def read_source_documents(
    src_root: Path = SRC_ROOT,
    parts_path: Path = PARTS_PATH,
) -> list[SourceDocument]:
    manifest_bytes = normalize_lf_bytes(parts_path.read_bytes())
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    parts = manifest.get("parts")
    if not isinstance(parts, list):
        raise RuntimeError("kgg-update/src/parts.json must contain a parts list")

    resolved_root = src_root.resolve()
    documents = [SourceDocument("kgg-update/src/parts.json", manifest_bytes)]
    seen = {parts_path.resolve()}
    for relative in parts:
        if not isinstance(relative, str) or not relative:
            raise RuntimeError("kgg-update/src/parts.json parts must be non-empty POSIX paths")
        relative_path = Path(relative)
        if relative_path.is_absolute():
            raise RuntimeError(f"source part must stay relative: {relative}")
        if "\\" in relative:
            raise RuntimeError("kgg-update/src/parts.json parts must use POSIX paths")
        if ".." in relative_path.parts:
            raise RuntimeError(f"source part escapes kgg-update/src: {relative}")
        candidate = (src_root / relative_path).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError as exc:
            raise RuntimeError(f"source part escapes kgg-update/src: {relative}") from exc
        if candidate in seen:
            raise RuntimeError(f"duplicate source part: {relative}")
        if not candidate.is_file():
            raise RuntimeError(f"missing source part: {relative}")
        seen.add(candidate)
        documents.append(
            SourceDocument(
                f"kgg-update/src/{Path(relative).as_posix()}",
                normalize_lf_bytes(candidate.read_bytes()),
            )
        )
    return documents


def is_natural_boundary(window: Iterable[bytes], *, mask: int = BOUNDARY_MASK) -> bool:
    lines = tuple(window)
    if len(lines) != ROLLING_LINE_WINDOW:
        return False
    first_16_bits = int.from_bytes(hashlib.sha256(b"".join(lines)).digest()[:2], "big")
    return first_16_bits & mask == 0


def chunk_source(
    source: SourceDocument,
    *,
    min_payload_bytes: int = MIN_PAYLOAD_BYTES,
    max_payload_bytes: int = MAX_PAYLOAD_BYTES,
    boundary_mask: int = BOUNDARY_MASK,
) -> list[SourceChunk]:
    if min_payload_bytes <= 0 or max_payload_bytes < min_payload_bytes:
        raise ValueError("invalid source chunk byte limits")
    lines = source.lines
    if not lines:
        return []

    chunks: list[SourceChunk] = []
    window: deque[bytes] = deque(maxlen=ROLLING_LINE_WINDOW)
    current: list[bytes] = []
    current_bytes = 0
    current_start = 1

    def emit(end_line: int) -> None:
        nonlocal current, current_bytes, current_start
        if not current:
            return
        chunks.append(SourceChunk(source, b"".join(current), current_start, end_line))
        current = []
        current_bytes = 0
        current_start = end_line + 1

    for line_number, line in enumerate(lines, start=1):
        if len(line) > max_payload_bytes:
            raise RuntimeError(
                f"source line exceeds {max_payload_bytes} bytes: {source.path}:{line_number}"
            )
        if current and current_bytes + len(line) > max_payload_bytes:
            emit(line_number - 1)
        current.append(line)
        current_bytes += len(line)
        window.append(line)
        if current_bytes >= min_payload_bytes and is_natural_boundary(window, mask=boundary_mask):
            emit(line_number)

    emit(len(lines))
    return chunks


def register_hash_prefix(registry: dict[str, str], full_hash: str) -> str:
    prefix = full_hash[:HASH_PREFIX_LENGTH]
    previous = registry.get(prefix)
    if previous is not None and previous != full_hash:
        raise RuntimeError(f"source chunk hash-prefix collision: {prefix}")
    registry[prefix] = full_hash
    return prefix


def chunk_reference(chunk: SourceChunk) -> dict[str, object]:
    return {
        "sourcePath": chunk.source.path,
        "sourceSha256": chunk.source.sha256,
        "name": chunk.name,
        "path": chunk.path,
        "payloadSha256": chunk.sha256,
        "payloadBytes": len(chunk.payload),
        "payloadLines": chunk.line_count,
    }


def marker_locations(
    documents: list[SourceDocument],
    chunks_by_source: dict[str, list[SourceChunk]],
    marker: str,
) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for source in documents:
        for line_number, line in enumerate(source.lines, start=1):
            if marker not in line.decode("utf-8"):
                continue
            chunk = next(
                item
                for item in chunks_by_source[source.path]
                if item.start_line <= line_number <= item.end_line
            )
            matches.append(
                {
                    "marker": marker,
                    "sourcePath": source.path,
                    "sourceSha256": source.sha256,
                    "sourceLine": line_number,
                    "chunk": chunk.name,
                    "path": chunk.path,
                    "payloadSha256": chunk.sha256,
                    "payloadBytes": len(chunk.payload),
                    "payloadLines": chunk.line_count,
                }
            )
            if len(matches) == 8:
                return matches
    return matches


def render_area_routes(
    documents: list[SourceDocument],
    chunks_by_source: dict[str, list[SourceChunk]],
) -> tuple[bytes, bytes]:
    chunk_order = {
        (chunk.source.path, chunk.path): order
        for order, chunk in enumerate(
            chunk
            for source in documents
            for chunk in chunks_by_source[source.path]
        )
    }
    chunks_by_key = {
        (chunk.source.path, chunk.path): chunk
        for source in documents
        for chunk in chunks_by_source[source.path]
    }
    routes = []
    for route in AREA_ROUTES:
        marker_entries = []
        chunk_keys: set[tuple[str, str]] = set()
        for marker in route["markers"]:
            locations = marker_locations(documents, chunks_by_source, marker)
            if locations:
                marker_entries.append(locations[0])
                chunk_keys.update(
                    (str(item["sourcePath"]), str(item["path"])) for item in locations
                )
            else:
                marker_entries.append(
                    {
                        "marker": marker,
                        "sourcePath": None,
                        "sourceSha256": None,
                        "sourceLine": None,
                        "chunk": None,
                        "path": None,
                        "payloadSha256": None,
                        "payloadBytes": None,
                        "payloadLines": None,
                    }
                )
        routes.append(
            {
                "id": route["id"],
                "triggers": route["triggers"],
                "markers": marker_entries,
                "sourceChunks": [
                    chunk_reference(chunks_by_key[key])
                    for key in sorted(chunk_keys, key=chunk_order.__getitem__)
                ],
                "tests": route["tests"],
                "notes": route["notes"],
            }
        )
    route_json = {
        "kind": "kgg_gpt_area_routes",
        "version": 2,
        "sourceIndex": "docs/kgg-gpt-source-index.json",
        "routes": routes,
    }
    md_lines = [
        "# KGG GPT Area Routes",
        "",
        "Generated from `kgg-update/src` modular source. Use this before loading source chunks.",
        "",
    ]
    for route in routes:
        md_lines.extend(
            [
                f"## {route['id']}",
                "",
                "- Triggers: " + ", ".join(f"`{item}`" for item in route["triggers"]),
                "- Source chunks: "
                + (
                    ", ".join(f"`{item['path']}`" for item in route["sourceChunks"])
                    or "none found"
                ),
                "- Tests: " + "; ".join(f"`{item}`" for item in route["tests"]),
                f"- Notes: {route['notes']}",
                "- Markers:",
            ]
        )
        for marker in route["markers"]:
            if marker["path"]:
                md_lines.append(
                    f"  - `{marker['marker']}`: `{marker['path']}` from "
                    f"`{marker['sourcePath']}` line {marker['sourceLine']}"
                )
            else:
                md_lines.append(f"  - `{marker['marker']}`: not found")
        md_lines.append("")
    return (
        (json.dumps(route_json, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"),
        ("\n".join(md_lines).rstrip() + "\n").encode("utf-8"),
    )


def render_outputs() -> dict[Path, bytes]:
    documents = read_source_documents()
    chunks_by_source = {source.path: chunk_source(source) for source in documents}
    hash_registry: dict[str, str] = {}
    chunk_outputs: dict[Path, bytes] = {}
    for source in documents:
        for chunk in chunks_by_source[source.path]:
            register_hash_prefix(hash_registry, chunk.sha256)
            path = ROOT / chunk.path
            previous = chunk_outputs.get(path)
            if previous is not None and previous != chunk.payload:
                raise RuntimeError(f"source chunk path collision: {chunk.path}")
            chunk_outputs[path] = chunk.payload

    routes_json, routes_md = render_area_routes(documents, chunks_by_source)
    index = {
        "kind": "kgg_gpt_source_index",
        "version": 2,
        "chunking": {
            "algorithm": "sha256-rolling-8-lines-v1",
            "lineEndings": "LF",
            "minPayloadBytes": MIN_PAYLOAD_BYTES,
            "maxPayloadBytes": MAX_PAYLOAD_BYTES,
            "rollingLineWindow": ROLLING_LINE_WINDOW,
            "naturalBoundaryMask": "0x01ff",
            "naturalBoundaryValue": "0x0000",
            "filenameHashPrefixHexChars": HASH_PREFIX_LENGTH,
        },
        "areaRoutes": {
            "json": "docs/kgg-gpt-area-routes.json",
            "markdown": "docs/kgg-gpt-area-routes.md",
        },
        "sources": [
            {
                "path": source.path,
                "sha256": source.sha256,
                "bytes": len(source.payload),
                "lines": len(source.lines),
                "chunks": [
                    {
                        "name": chunk.name,
                        "path": chunk.path,
                        "payloadSha256": chunk.sha256,
                        "payloadBytes": len(chunk.payload),
                        "payloadLines": chunk.line_count,
                    }
                    for chunk in chunks_by_source[source.path]
                ],
            }
            for source in documents
        ],
    }
    outputs: dict[Path, bytes] = {
        INDEX_PATH: (json.dumps(index, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"),
        ROUTES_JSON_PATH: routes_json,
        ROUTES_MD_PATH: routes_md,
    }
    outputs.update(chunk_outputs)
    return outputs


def current_generated_chunks() -> set[Path]:
    if not CHUNK_DIR.exists():
        return set()
    candidates = set(CHUNK_DIR.glob("chunk-*.md"))
    unexpected = sorted(path for path in candidates if not CHUNK_FILENAME_RE.fullmatch(path.name))
    if unexpected:
        names = ", ".join(path.name for path in unexpected)
        raise RuntimeError(f"refusing to replace unexpected source chunk files: {names}")
    return candidates


def payload_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def reject_existing_v2_mismatches(
    current_chunks: set[Path], outputs: dict[Path, bytes]
) -> None:
    """Keep content-addressed names immutable, including across generations."""
    for path in sorted(current_chunks.intersection(outputs)):
        match = V2_CHUNK_FILENAME_RE.fullmatch(path.name)
        if match is None:
            continue
        existing_hash = payload_sha256(path.read_bytes())
        expected_hash = payload_sha256(outputs[path])
        if existing_hash == expected_hash:
            continue
        prefix = match.group(1)
        if existing_hash.startswith(prefix) and expected_hash.startswith(prefix):
            raise RuntimeError(
                f"existing source chunk hash-prefix collision: {display_path(path)}"
            )
        raise RuntimeError(
            f"refusing to overwrite corrupt content-addressed source chunk: "
            f"{display_path(path)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check KGG GPT source chunks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    outputs = render_outputs()
    if args.write:
        old_chunks = current_generated_chunks()
        reject_existing_v2_mismatches(old_chunks, outputs)
        for path, payload in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            print(f"Wrote {path.relative_to(ROOT)}")
        expected_chunks = {path for path in outputs if path.parent == CHUNK_DIR}
        for path in sorted(old_chunks - expected_chunks):
            path.unlink()
            print(f"Removed stale {path.relative_to(ROOT)}")
        return 0

    errors: list[str] = []
    expected_paths = set(outputs)
    current_chunks = current_generated_chunks()
    stale_extra = current_chunks - {path for path in expected_paths if path.parent == CHUNK_DIR}
    for path in sorted(stale_extra):
        errors.append(f"stale extra chunk: {path.relative_to(ROOT)}")
    for path, expected in outputs.items():
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
            continue
        current = path.read_bytes()
        if current != expected:
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
