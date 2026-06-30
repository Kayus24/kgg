#!/usr/bin/env python3
"""Guard KGG HTML releases against late charset and mojibake regressions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "therapist-app" / "android_update_manifest.json"
SOURCE_HTML = ROOT / "kgg-update" / "index.html"
RELEASE_INBOX_HTML = ROOT / "release-inbox" / "admin.html"
MAX_CHARSET_BYTE_OFFSET = 512
MOJIBAKE_MARKERS = ("Ã", "Â", "â€", "âœ", "âž", "ðŸ", "\ufffd")


class EncodingGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class EncodingFinding:
    label: str
    path: Path
    message: str


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _charset_byte_offset(raw: bytes) -> int:
    lowered = raw[:4096].lower()
    match = re.search(br'<meta\s+charset=["\']?utf-8["\']?\s*/?>', lowered)
    return -1 if match is None else match.start()


def _first_non_ascii_byte(raw: bytes) -> int:
    return next((index for index, value in enumerate(raw) if value >= 128), -1)


def validate_html_encoding(raw: bytes, label: str, path: Path | None = None) -> list[EncodingFinding]:
    """Return encoding findings for one HTML document.

    This deliberately checks raw bytes before decoding, because the dangerous
    failure mode is a WebView/browser deciding the document encoding before it
    sees a late charset declaration.
    """
    path = path or Path(label)
    findings: list[EncodingFinding] = []

    if not raw.startswith(b"<!doctype html>"):
        findings.append(EncodingFinding(label, path, "HTML must start exactly with <!doctype html> and no BOM/prefix bytes."))

    if not re.match(br"<!doctype html>\s*<html\b[^>]*>\s*<head\b[^>]*>", raw[:256], re.I):
        findings.append(EncodingFinding(label, path, "<head> must appear immediately after <!doctype html> / <html>."))

    charset_at = _charset_byte_offset(raw)
    if charset_at < 0:
        findings.append(EncodingFinding(label, path, 'Missing early <meta charset="utf-8">.'))
    else:
        if charset_at > MAX_CHARSET_BYTE_OFFSET:
            findings.append(
                EncodingFinding(
                    label,
                    path,
                    f'<meta charset="utf-8"> is too late at byte {charset_at}; must be within first {MAX_CHARSET_BYTE_OFFSET} bytes.',
                )
            )
        first_non_ascii = _first_non_ascii_byte(raw)
        if first_non_ascii >= 0 and first_non_ascii < charset_at:
            findings.append(
                EncodingFinding(
                    label,
                    path,
                    f"First non-ASCII byte appears at byte {first_non_ascii}, before charset at byte {charset_at}.",
                )
            )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        findings.append(EncodingFinding(label, path, f"HTML is not valid UTF-8: {exc}."))
        return findings

    for marker in MOJIBAKE_MARKERS:
        index = text.find(marker)
        if index >= 0:
            snippet = text[max(0, index - 24) : index + 48].replace("\n", "\\n")
            findings.append(EncodingFinding(label, path, f"Mojibake marker {marker!r} found near: {snippet!r}."))
            break

    return findings


def manifest_admin_path(manifest_path: Path = MANIFEST) -> Path:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    admin_url = str(data.get("channels", {}).get("admin", {}).get("url") or data.get("adminHtmlUrl") or "")
    match = re.search(r"/therapist-app/releases/web/(r[0-9]{4,})/admin\.html(?:$|\?)", admin_url)
    if not match:
        raise EncodingGuardError(f"Cannot derive active Admin HTML path from manifest URL: {admin_url}")
    return ROOT / "therapist-app" / "releases" / "web" / match.group(1) / "admin.html"


def guard_targets() -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = [("source", SOURCE_HTML)]
    if RELEASE_INBOX_HTML.exists():
        targets.append(("release-inbox", RELEASE_INBOX_HTML))
    targets.append(("manifest-admin", manifest_admin_path()))
    return targets


def run_guard(targets: list[tuple[str, Path]] | None = None) -> None:
    all_findings: list[EncodingFinding] = []
    for label, path in targets or guard_targets():
        if not path.exists():
            all_findings.append(EncodingFinding(label, path, "Expected HTML file does not exist."))
            continue
        all_findings.extend(validate_html_encoding(path.read_bytes(), label, path))

    if all_findings:
        details = "\n".join(
            f"- {finding.label} ({_display_path(finding.path)}): {finding.message}" for finding in all_findings
        )
        raise EncodingGuardError("KGG encoding guard failed:\n" + details)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action="append", type=Path, help="Check an explicit HTML path instead of default KGG targets.")
    args = parser.parse_args(argv)
    try:
        if args.path:
            run_guard([(path.name, (ROOT / path).resolve() if not path.is_absolute() else path) for path in args.path])
        else:
            run_guard()
        print("Encoding guard OK")
        return 0
    except EncodingGuardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
