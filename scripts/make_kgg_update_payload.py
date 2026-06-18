#!/usr/bin/env python3
"""Create/update the KGG WebView auto-update payload.

Usage from repo root:
  python3 scripts/make_kgg_update_payload.py /path/to/KGG_APP_ADMIN_v400_mini07_identity_fix.html v400-mini07-identity-fix 1

This copies the given HTML to kgg-update/index.html and writes kgg-update/version.json
with the correct SHA-256 for the Android WebView wrapper auto-updater.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

REPO_RAW_BASE = "https://raw.githubusercontent.com/Kayus24/kgg/main"


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python3 scripts/make_kgg_update_payload.py "
            "<source-html> <versionName> <versionCode>",
            file=sys.stderr,
        )
        return 2

    source = pathlib.Path(sys.argv[1]).expanduser().resolve()
    version_name = sys.argv[2]
    try:
        version_code = int(sys.argv[3])
    except ValueError:
        print("versionCode must be an integer", file=sys.stderr)
        return 2

    if not source.exists() or not source.is_file():
        print(f"Source HTML not found: {source}", file=sys.stderr)
        return 1

    root = pathlib.Path(__file__).resolve().parents[1]
    target_dir = root / "kgg-update"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_html = target_dir / "index.html"
    data = source.read_bytes()
    target_html.write_bytes(data)

    sha256 = hashlib.sha256(data).hexdigest()
    manifest = {
        "versionCode": version_code,
        "versionName": version_name,
        "url": f"{REPO_RAW_BASE}/kgg-update/index.html",
        "sha256": sha256,
    }
    (target_dir / "version.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {target_html}")
    print(f"Wrote {target_dir / 'version.json'}")
    print(f"sha256={sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
