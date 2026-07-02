#!/usr/bin/env python3
"""Generate compact bug-history knowledge for the private KGG Custom GPT."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "kgg-gpt-bug-index.json"
LESSONS_PATH = ROOT / "docs" / "kgg-gpt-bug-lessons.md"
PATTERNS_PATH = ROOT / "docs" / "kgg-gpt-patch-patterns.md"

SOURCE_DIRS = [
    ROOT / "docs" / "bug-debug",
    ROOT / "docs" / "bugfixes",
    ROOT / "docs" / "release-handoffs",
]
SOURCE_FILES = [
    ROOT / "docs" / "CHANGELOG_THERAPIST_APP.md",
    ROOT / "docs" / "VERSIONSLOG.md",
]

SECTION_ALIASES = {
    "problem": ["problem", "kurzfassung"],
    "cause": ["ursache", "fehlerursache"],
    "fix": ["loesung/fix", "loesung", "fix", "empfohlener mini-patch", "aenderung"],
    "tests": ["test", "test / abnahmekriterien", "akzeptanztests", "testregel", "abnahmekriterien"],
    "do_not_touch": ["nicht anfassen", "safety"],
    "risks": ["folge-risiken", "risiken", "risk", "kaputt/auffaellig"],
}

AREA_KEYWORDS = {
    "phone-layout": ["handy", "phone", "390", "759", "mobile"],
    "tablet-layout": ["tablet", "760", "split", "layout"],
    "modal": ["modal", "dialog", "overlay", "share"],
    "drag-reorder": ["drag", "reorder", "verschieben", "hitbox", "touch-action", "swipe"],
    "qr-patient": ["qr", "patient", "patienten"],
    "scan-camera": ["scan", "kamera", "galerie", "ocr"],
    "parser-textblocks": ["parser", "textblock", "satz"],
    "sync": ["sync", "peer", "paket", "bank"],
    "pdf": ["pdf"],
    "debug": ["debug", "json", "diagnose"],
}

FORBIDDEN_PATTERNS = [
    {
        "id": "global-touch-action",
        "risk": "Global touch or pointer rules can break swipe, scroll and drag/reorder flows.",
        "avoid": "Do not add broad `touch-action`, `pointer-events` or gesture rules on app-wide containers.",
        "prefer": "Limit gesture rules to the exact handle/control and run UI stability regression.",
    },
    {
        "id": "modal-scoped-only-to-tablet",
        "risk": "Closed modals can leak into the phone document flow when hiding rules are scoped only to tablet classes.",
        "avoid": "Do not hide modal overlays only below `body.tabletLayoutCustom`.",
        "prefer": "Give the modal a global hidden base rule and then layer tablet-specific presentation separately.",
    },
    {
        "id": "breakpoint-drift",
        "risk": "Phone and tablet UI can both become active if the 759/760 px split drifts.",
        "avoid": "Do not test breakpoints with browser zoom or change phone/tablet media queries incidentally.",
        "prefer": "Use real viewports: phone <=759 px, tablet >=760 px.",
    },
    {
        "id": "debug-output-to-patient",
        "risk": "Patient-facing output must never expose raw JSON, Base64 or debug payloads.",
        "avoid": "Do not route debug pages or payload dumps into normal patient flows.",
        "prefer": "Keep debug output internal and preserve patient-safe rendering.",
    },
    {
        "id": "side-effect-feature-touch",
        "risk": "Small UI fixes often become unsafe when they also touch QR, PDF, parser, scan or plan state.",
        "avoid": "Do not edit protected feature blocks unless Max explicitly asked for that area.",
        "prefer": "Make one scoped patch and list all untouched protected areas in the PR.",
    },
]


def normalize_text(text: str) -> str:
    replacements = {
        "\r\n": "\n",
        "\r": "\n",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ã„": "Ae",
        "Ã–": "Oe",
        "Ãœ": "Ue",
        "Ã¤": "ae",
        "Ã¶": "oe",
        "Ã¼": "ue",
        "ÃŸ": "ss",
        "â€“": "-",
        "â€”": "-",
        "â€ž": '"',
        "â€œ": '"',
        "â€": '"',
        "â€˜": "'",
        "â€™": "'",
        "Ã—": "x",
        "Â": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def ascii_clean(text: str) -> str:
    text = normalize_text(text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def first_nonempty(lines: list[str], limit: int = 360) -> str:
    collected: list[str] = []
    in_code = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line or line.startswith("#"):
            continue
        collected.append(line)
        if sum(len(item) for item in collected) >= limit:
            break
    text = ascii_clean(" ".join(collected))
    return text[:limit].rstrip()


def slugify(text: str) -> str:
    text = ascii_clean(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "entry"


def source_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in SOURCE_DIRS:
        if directory.exists():
            paths.extend(sorted(path for path in directory.rglob("*.md") if path.is_file()))
    for path in SOURCE_FILES:
        if path.exists():
            paths.append(path)
    return sorted(set(paths), key=lambda item: item.as_posix())


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def read_source(path: Path) -> str:
    return normalize_text(path.read_text(encoding="utf-8", errors="replace"))


def title_from_text(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.M)
    return ascii_clean(match.group(1)) if match else ascii_clean(fallback)


def split_readme_topics(path: Path, text: str) -> list[tuple[str, str]]:
    if path.name.lower() != "readme.md":
        return [(title_from_text(text, path.stem), text)]
    text = strip_fenced_code(text)
    matches = list(re.finditer(r"^##\s+(.+)$", text, re.M))
    topics: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        title = ascii_clean(match.group(1))
        lower_title = title.lower()
        if lower_title.startswith("standardformat") or lower_title in {"problem", "ursache", "nicht anfassen", "folge-risiken"}:
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            topics.append((title, body))
    return topics or [(title_from_text(text, path.stem), text)]


def sections(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = "summary"
    result[current] = []
    for raw in text.splitlines():
        match = re.match(r"^#{2,4}\s+(.+?)\s*$", raw)
        if match:
            current = ascii_clean(match.group(1)).lower()
            result.setdefault(current, [])
            continue
        result.setdefault(current, []).append(raw)
    return result


def section_value(section_map: dict[str, list[str]], aliases: list[str]) -> str:
    for alias in aliases:
        for name, lines in section_map.items():
            if name == alias or alias in name:
                value = first_nonempty(lines)
                if value:
                    return value
    return ""


def markers(text: str) -> list[str]:
    found: set[str] = set()
    for match in re.finditer(r"`([^`\n]{2,120})`", text):
        token = ascii_clean(match.group(1))
        if token:
            found.add(token)
    for match in re.finditer(r"(\.[A-Za-z][A-Za-z0-9_-]{2,}|#[A-Za-z][A-Za-z0-9_-]{2,})", text):
        found.add(ascii_clean(match.group(1)))
    for match in re.finditer(r"([A-Za-z0-9_./-]+\.(?:html|js|json|md|py|cmd|yml))", text):
        found.add(ascii_clean(match.group(1)))
    return sorted(found)[:24]


def classify(text: str) -> list[str]:
    lowered = ascii_clean(text).lower()
    areas = [area for area, words in AREA_KEYWORDS.items() if any(word in lowered for word in words)]
    return sorted(set(areas)) or ["general"]


def summarize_record(path: Path, title: str, body: str) -> dict[str, Any]:
    section_map = sections(body)
    body_text = ascii_clean(body)
    source = path.relative_to(ROOT).as_posix()
    record = {
        "id": slugify(source + "-" + title),
        "source_path": source,
        "title": title,
        "areas": classify(title + "\n" + body),
        "symptom": section_value(section_map, SECTION_ALIASES["problem"]) or first_nonempty(body.splitlines()),
        "cause": section_value(section_map, SECTION_ALIASES["cause"]),
        "fix_pattern": section_value(section_map, SECTION_ALIASES["fix"]),
        "tests": section_value(section_map, SECTION_ALIASES["tests"]),
        "do_not_touch": section_value(section_map, SECTION_ALIASES["do_not_touch"]),
        "risks": section_value(section_map, SECTION_ALIASES["risks"]),
        "markers": markers(body),
        "keywords": sorted(set(classify(body_text) + [slugify(title)])),
    }
    return record


def build_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in source_paths():
        text = read_source(path)
        if path.name in {"CHANGELOG_THERAPIST_APP.md", "VERSIONSLOG.md"} and "## 2026-" not in text and "Version:" not in text:
            continue
        for title, body in split_readme_topics(path, text):
            record = summarize_record(path, title, body)
            if record["symptom"] or record["fix_pattern"] or record["do_not_touch"]:
                records.append(record)
    return sorted(records, key=lambda item: (item["source_path"], item["title"]))


def render_index(records: list[dict[str, Any]]) -> str:
    data = {
        "kind": "kgg_gpt_bug_knowledge",
        "version": 1,
        "sources": [path.relative_to(ROOT).as_posix() for path in source_paths()],
        "records": records,
        "forbidden_patterns": FORBIDDEN_PATTERNS,
    }
    return json.dumps(data, indent=2, ensure_ascii=True, sort_keys=True) + "\n"


def render_lessons(records: list[dict[str, Any]]) -> str:
    lesson_records = [
        record
        for record in records
        if record["source_path"] not in {"docs/CHANGELOG_THERAPIST_APP.md", "docs/VERSIONSLOG.md"}
    ]
    lines = [
        "# KGG GPT Bug Lessons",
        "",
        "Generated from the KGG bug/debug history. Load this before proposing or dispatching a patch.",
        "",
        "## Always Apply",
        "",
        "- Search this file and `kgg-gpt-bug-index.json` for similar symptoms before patching.",
        "- Reuse the matching `do_not_touch` rules and add the matching tests to the PR plan.",
        "- If a proposed patch resembles a forbidden pattern, stop and route to Codex.",
        "- Keep patient-facing flows free of raw JSON, Base64 and debug output.",
        "",
        "## Known Lessons",
        "",
    ]
    for record in lesson_records:
        summary = record.get("symptom") or record.get("fix_pattern") or "See source."
        caution = record.get("do_not_touch") or record.get("risks") or "Keep patch scoped to the requested area."
        tests = record.get("tests") or "Run the risk-matched KGG battery."
        areas = ", ".join(record.get("areas", []))
        lines.extend(
            [
                f"### {record['title']}",
                "",
                f"- Source: `{record['source_path']}`",
                f"- Areas: {areas}",
                f"- Lesson: {summary}",
                f"- Caution: {caution}",
                f"- Tests: {tests}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_patterns(records: list[dict[str, Any]]) -> str:
    lines = [
        "# KGG GPT Patch Patterns",
        "",
        "Use these patterns to avoid repeating known KGG regressions.",
        "",
        "## Forbidden Patterns",
        "",
    ]
    for pattern in FORBIDDEN_PATTERNS:
        lines.extend(
            [
                f"### {pattern['id']}",
                "",
                f"- Risk: {pattern['risk']}",
                f"- Avoid: {pattern['avoid']}",
                f"- Prefer: {pattern['prefer']}",
                "",
            ]
        )

    area_tests = {
        "phone-layout": "Use real phone viewport <=759 px and run ui-stability regression.",
        "tablet-layout": "Use real tablet viewport >=760 px and run ui-stability regression.",
        "modal": "Verify closed modal is not in normal flow; verify explicit open/close.",
        "drag-reorder": "Test drag/reorder and swipe/delete separately on phone and tablet.",
        "qr-patient": "Do not touch QR/patient flow unless explicitly requested; run patient-qr critical when touched.",
        "parser-textblocks": "Run textblocks regression when parser/text-block behavior is touched.",
        "sync": "Run sync regression when sync, bank, package or peer behavior is touched.",
        "debug": "Debug output must stay internal and never become patient-facing output.",
    }
    seen_areas = sorted({area for record in records for area in record.get("areas", [])})
    lines.extend(["## Area Test Hints", ""])
    for area in seen_areas:
        hint = area_tests.get(area, "Use the risk-matched KGG test battery and keep unrelated features unchanged.")
        lines.append(f"- `{area}`: {hint}")
    lines.append("")
    lines.extend(
        [
            "## PR Reminder",
            "",
            "- Include `base file used`, `changed file`, `changes`, `smoke test` and `risks`.",
            "- Mention the matching bug-history lesson when one exists.",
            "- Do not mark tests green unless GitHub or local output proves it.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip() + "\n"


def outputs() -> dict[Path, str]:
    records = build_records()
    return {
        INDEX_PATH: render_index(records),
        LESSONS_PATH: render_lessons(records),
        PATTERNS_PATH: render_patterns(records),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check KGG GPT bug-history knowledge.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write generated bug-history knowledge files.")
    group.add_argument("--check", action="store_true", help="Fail if generated bug-history knowledge is stale.")
    group.add_argument("--print", action="store_true", help="Print generated file contents.")
    args = parser.parse_args()

    try:
        rendered = {path: normalize(text) for path, text in outputs().items()}
        if args.print:
            for path, text in rendered.items():
                print(f"--- {path.relative_to(ROOT)} ---")
                print(text, end="")
            return 0
        if args.write:
            for path, text in rendered.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
                print(f"Wrote {path.relative_to(ROOT)}")
            return 0
        for path, expected in rendered.items():
            if not path.exists():
                raise RuntimeError(f"{path.relative_to(ROOT)} is missing. Run release-pipeline/kgg_bug_knowledge.py --write.")
            current = normalize(path.read_text(encoding="utf-8"))
            if current != expected:
                raise RuntimeError(f"{path.relative_to(ROOT)} is stale. Run release-pipeline/kgg_bug_knowledge.py --write.")
        print("KGG bug knowledge OK")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
