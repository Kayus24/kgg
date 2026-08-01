#!/usr/bin/env python3
"""Generate and verify patient Custom GPT context, source chunks and Knowledge."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONTEXT_PATH = DOCS / "kgg-patient-gpt-context.md"
SOURCE_INDEX_PATH = DOCS / "kgg-patient-gpt-source-index.json"
SOURCE_DIR = DOCS / "kgg-patient-gpt-source"
MAX_CHUNK_CHARS = 24_000

MANUAL_SOURCES = {
    "editor": "docs/kgg-patient-custom-gpt-editor-bootstrap.md",
    "playbook": "docs/kgg-patient-custom-gpt-playbook.md",
    "action": "docs/kgg-patient-custom-gpt-action-schema.md",
    "negative": "docs/kgg-patient-custom-gpt-negative-examples.md",
    "tests": "docs/kgg-patient-custom-gpt-test-prompts.md",
}
KNOWLEDGE_PATHS = {
    "architecture": DOCS / "kgg-patient-custom-gpt-knowledge-architecture.md",
    "operations": DOCS / "kgg-patient-custom-gpt-knowledge-operations.md",
    "safety": DOCS / "kgg-patient-custom-gpt-knowledge-safety.md",
    "testing": DOCS / "kgg-patient-custom-gpt-knowledge-testing.md",
}


class ResourceError(RuntimeError):
    """Raised for missing or stale patient GPT resources."""


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise ResourceError(f"missing patient GPT source: {relative}")
    return normalize(path.read_text(encoding="utf-8"))


def patient_source_paths() -> list[str]:
    paths = [
        "APP_BOUNDARIES.md",
        "index.html",
        "service-worker.js",
        "update-recovery.html",
        "manifest.json",
        "collapse-cards.js",
        "numpad-ui-fix.js",
    ]
    paths.extend(path.name for path in sorted(ROOT.glob("manifest-v*.webmanifest")))
    paths.extend(path.name for path in sorted(ROOT.glob("patient-*.js")))
    return list(dict.fromkeys(paths))


def current_version() -> str:
    worker = read("service-worker.js")
    match = re.search(r"const APP_VERSION = '([0-9]+)';", worker)
    if not match:
        raise ResourceError("service-worker.js has no numeric APP_VERSION")
    return match.group(1)


def render_context() -> str:
    version = current_version()
    files = patient_source_paths()
    lines = [
        "# KGG Patient GPT Live Context",
        "",
        "Authoritative live repository context for the private KGG Patienten-App Update-Agent.",
        "Reload before every diagnosis involving current code and before every Preview, PR or live request.",
        "",
        "## Repository",
        "",
        "- Repository: `https://github.com/Kayus24/kgg`, branch `main`.",
        "- Live patient app: `https://kayus24.github.io/kgg/`.",
        f"- Current patient PWA version from `service-worker.js`: `v{version}`.",
        "- Recovery: `https://kayus24.github.io/kgg/update-recovery.html`.",
        "- Isolated preview host: `https://kayus24.github.io/kgg-patient-preview/`.",
        "- Pre-authorized Patient Preview workflow: `.github/workflows/kgg-patient-gpt-preview-only.yml`.",
        "- Consequential Patient PR/live workflow: `.github/workflows/kgg-patient-gpt-preview-gate.yml`.",
        "- Guard implementation: `release-pipeline/kgg_patient_gpt_write_gate.py`.",
        "- Private project memory: `Kayus24/kgg-project-memory`.",
        "- Private cross-agent coordination: `coordination/index.json` and guarded append-only threads.",
        "",
        "## Patient Source Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in files)
    lines.extend(
        [
            "",
            "## Hard Rules",
            "",
            "- Work in German, make one smallest safe patch and preserve existing hooks.",
            "- Never write directly to `main`; use exact Preview hash, PR and protected live approval.",
            "- Reads, validate_only, publish_preview, evidence checks and safe coordination responses are pre-authorized; do not ask after every step.",
            "- Patient PR/live requires Max' exact phrase `Gut für PAT live`.",
            "- Patient output never exposes raw JSON, Base64, KGGH2/KGGD1 or debug payloads.",
            "- Preview fixtures are synthetic and contain no patient data.",
            "- Version, cache name, Recovery release, version label and changelog are owned by the gate.",
            "- QR/hash/storage changes use `risk_class=interface` and stay backward compatible.",
            "- Breaking interface changes, therapist app, PDF and Android/APK stay outside this agent.",
            "- A Custom GPT supplies the Preview URL but does not claim to control the Codex in-app browser.",
            "",
            "## Required Evidence",
            "",
            "- `validate_only` before `publish_preview` with identical payload.",
            "- Successful workflow run, jobs, artifact, meta.json, Preview URL and Recovery URL.",
            "- Max accepts the Preview in the in-app browser before PR or live mode.",
            "- Live mode additionally needs Required Checks, patient-live Environment approval, merge and live version verification.",
            "",
        ]
    )
    return normalize("\n".join(lines))


def split_source() -> tuple[dict[Path, str], list[dict[str, object]]]:
    chunks: dict[Path, str] = {}
    files: list[dict[str, object]] = []
    chunk_number = 0
    for relative in patient_source_paths():
        text = read(relative)
        files.append(
            {
                "path": relative,
                "sha256": sha256(text),
                "characters": len(text),
            }
        )
        for start in range(0, len(text), MAX_CHUNK_CHARS):
            part = text[start : start + MAX_CHUNK_CHARS]
            name = f"chunk-{chunk_number:03d}.md"
            body = normalize(
                "\n".join(
                    [
                        f"# KGG Patient Source Chunk {chunk_number:03d}",
                        "",
                        f"- Source file: `{relative}`",
                        f"- Characters: {start + 1}-{start + len(part)}",
                        f"- Full source SHA-256: `{sha256(text)}`",
                        "",
                        "```",
                        part.rstrip(),
                        "```",
                    ]
                )
            )
            chunks[SOURCE_DIR / name] = body
            chunk_number += 1
    return chunks, files


def render_source_index(chunks: dict[Path, str], files: list[dict[str, object]]) -> str:
    data = {
        "kind": "kgg_patient_gpt_source_index",
        "version": 1,
        "patientVersion": current_version(),
        "chunkSizeCharacters": MAX_CHUNK_CHARS,
        "files": files,
        "chunks": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(text),
                "characters": len(text),
            }
            for path, text in sorted(chunks.items())
        ],
        "routes": {
            "pwa-update": ["service-worker.js", "update-recovery.html", "patient-version-label.js"],
            "patient-ui": ["index.html", "collapse-cards.js", "numpad-ui-fix.js", "patient-*.js"],
            "patient-interface": ["index.html", "patient-start-scan.js", "patient-multiplan-db.js"],
        },
    }
    return json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def render_knowledge(context: str) -> dict[Path, str]:
    sources = {
        "architecture": [
            ("docs/kgg-patient-gpt-context.md", context),
            ("APP_BOUNDARIES.md", read("APP_BOUNDARIES.md")),
        ],
        "operations": [
            (MANUAL_SOURCES["playbook"], read(MANUAL_SOURCES["playbook"])),
            (MANUAL_SOURCES["action"], read(MANUAL_SOURCES["action"])),
        ],
        "safety": [
            (MANUAL_SOURCES["negative"], read(MANUAL_SOURCES["negative"])),
            ("docs/kgg-gpt-bug-lessons.md", read("docs/kgg-gpt-bug-lessons.md")),
            ("APP_BOUNDARIES.md", read("APP_BOUNDARIES.md")),
        ],
        "testing": [
            (MANUAL_SOURCES["tests"], read(MANUAL_SOURCES["tests"])),
            ("release-pipeline/kgg_pwa_contract_smoke.py", read("release-pipeline/kgg_pwa_contract_smoke.py")),
            ("release-pipeline/kgg_update_recovery_smoke.py", read("release-pipeline/kgg_update_recovery_smoke.py")),
        ],
    }
    rendered: dict[Path, str] = {}
    for profile, items in sources.items():
        digest = hashlib.sha256()
        for relative, text in items:
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(text.encode("utf-8"))
            digest.update(b"\0")
        lines = [
            f"# KGG Patient GPT Knowledge: {profile.title()}",
            "",
            f"Generated retrieval pack. Source digest: `{digest.hexdigest()[:16]}`.",
            "",
            "Live GitHub context and source files override this static Knowledge pack.",
            "",
        ]
        for relative, text in items:
            lines.extend(["---", "", f"# Source: {relative}", "", text.rstrip(), ""])
        rendered[KNOWLEDGE_PATHS[profile]] = normalize("\n".join(lines))
    return rendered


def expected_outputs() -> dict[Path, str]:
    context = render_context()
    chunks, files = split_source()
    outputs: dict[Path, str] = {
        CONTEXT_PATH: context,
        SOURCE_INDEX_PATH: render_source_index(chunks, files),
    }
    outputs.update(chunks)
    outputs.update(render_knowledge(context))
    return outputs


def write_outputs(outputs: dict[Path, str]) -> None:
    expected_chunks = {path.resolve() for path in outputs if path.parent == SOURCE_DIR}
    if SOURCE_DIR.exists():
        for path in SOURCE_DIR.glob("chunk-*.md"):
            if path.resolve() not in expected_chunks:
                path.unlink()
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def check_outputs(outputs: dict[Path, str]) -> None:
    for path, expected in outputs.items():
        if not path.is_file():
            raise ResourceError(f"missing generated patient GPT resource: {path.relative_to(ROOT)}")
        current = normalize(path.read_text(encoding="utf-8"))
        if current != normalize(expected):
            raise ResourceError(f"stale generated patient GPT resource: {path.relative_to(ROOT)}")
    expected_chunks = {path.name for path in outputs if path.parent == SOURCE_DIR}
    actual_chunks = {path.name for path in SOURCE_DIR.glob("chunk-*.md")} if SOURCE_DIR.exists() else set()
    if expected_chunks != actual_chunks:
        raise ResourceError("patient GPT source chunk set is stale")


def self_test() -> None:
    outputs = expected_outputs()
    if not outputs or CONTEXT_PATH not in outputs or SOURCE_INDEX_PATH not in outputs:
        raise ResourceError("resource generator produced an incomplete output set")
    index = json.loads(outputs[SOURCE_INDEX_PATH])
    if not index["chunks"] or not index["files"]:
        raise ResourceError("source index has no patient source")
    if len([path for path in outputs if path in KNOWLEDGE_PATHS.values()]) != 4:
        raise ResourceError("resource generator must create exactly four patient Knowledge packs")
    print("KGG patient GPT resource self-test PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        outputs = expected_outputs()
        if args.write:
            write_outputs(outputs)
            print(f"Wrote {len(outputs)} patient GPT resources")
            return 0
        check_outputs(outputs)
        print(f"KGG patient GPT resources OK ({len(outputs)} files)")
        return 0
    except (ResourceError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
