#!/usr/bin/env python3
"""
Apply v004 phone-only admin banner cleanup to an existing repo checkout.

Use this if a connector cannot upload the full 600KB HTML payload.
Run from the repository root:

  python3 scripts/apply_v004_phone_hide_admin_banner.py

The script:
- injects a phone-only CSS block into kgg-update/index.html
- updates kgg-update/version.json with the new SHA-256
- does not touch native Android files
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path.cwd()
INDEX = ROOT / "kgg-update" / "index.html"
VERSION = ROOT / "kgg-update" / "version.json"
PATCH_ID = "kgg-mini-patch-v400-08-phone-hide-admin-file-banner"

STYLE = f"""
<style id="{PATCH_ID}">
  /* v400 mini08: Phone-only cleanup.
     Entfernt die gelbe ADMIN-DATEI/Admin-Test-Box nur im Handy-Layout.
     Tablet-Layout ab 760px bleibt unveraendert. */
  @media (max-width:759px){{
    .adminTestBanner{{
      display:none!important;
    }}
  }}
</style>
"""

if not INDEX.exists():
    raise SystemExit(f"Missing {INDEX}. Stop: no patch applied.")

html = INDEX.read_text(encoding="utf-8")
if PATCH_ID not in html:
    if "</head>" not in html:
        raise SystemExit("Missing </head>. Stop: no patch applied.")
    html = html.replace("</head>", STYLE + "\n</head>", 1)
    INDEX.write_text(html, encoding="utf-8", newline="")
else:
    print("Patch already present in index.html")

sha = hashlib.sha256(INDEX.read_bytes()).hexdigest()

if VERSION.exists():
    try:
        data = json.loads(VERSION.read_text(encoding="utf-8"))
    except Exception:
        data = {}
else:
    data = {}

old_code = int(data.get("versionCode") or 0)
data.update({
    "versionCode": max(old_code + 1, 4),
    "versionName": "1.0.3-phone-admin-banner-clean",
    "indexUrl": "index.html",
    "sha256": sha,
    "notes": "GitHub update: phone-only cleanup; hides the yellow ADMIN-DATEI/Admin-Test banner in the handset layout without touching tablet layout or native Android wrapper."
})
VERSION.parent.mkdir(parents=True, exist_ok=True)
VERSION.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("v004 phone admin banner patch applied.")
print(f"SHA-256 kgg-update/index.html: {sha}")
print(f"versionCode: {data['versionCode']}")
