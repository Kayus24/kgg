# KGG Source Chunk 000

- Source: `kgg-update/src` modular source
- Lines: 1-420

```html
<!-- SOURCE FILE: kgg-update/src/parts.json -->
{
  "schema": 1,
  "output": "../index.html",
  "versionManifest": "../version.json",
  "requiredPatchIds": [
    "kgg-v041-ui-mini-series",
    "kgg-v042-phone-dock-anchored-correction",
    "kgg-v044-phone-liquid-actions",
    "kgg-v045-phone-drawer-bank-align",
    "kgg-v046-tablet-runtime-viewport-guard",
    "kgg-v050-phone-ui-mini-fix",
    "kgg-v051-android-qr-pdf-bridge",
    "kgg-v052-pdf-plan-thumbnails",
    "kgg-v053-ui-tablet-stability",
    "kgg-v060-tablet-html-release-label",
    "kgg-v061-cross-app-live-qr-camera",
    "kgg-v062-tablet-recent-package-shell-geometry"
  ],
  "parts": [
    "base-head.html",
    "metadata/source-truth.html",
    "metadata/changelog.html",
    "metadata/patch-rules.html",
    "metadata/changelog-guard.html",
    "base-app.html",
    "patches/v041-ui-mini-series.html",
    "patches/v042-phone-dock-anchored-correction.html",
    "patches/v044-phone-liquid-actions.html",
    "patches/v045-phone-drawer-bank-align.html",
    "patches/v046-tablet-runtime-viewport-guard.html",
    "patches/v050-phone-ui-mini-fix.html",
    "patches/v051-android-qr-pdf-bridge.html",
    "patches/v052-pdf-plan-thumbnails.html",
    "patches/v053-ui-tablet-stability.html",
    "patches/v060-tablet-html-release-label.html",
    "patches/v061-cross-app-live-qr-camera.html",
    "patches/v062-tablet-recent-package-shell-geometry.html",
    "footer.html"
  ]
}

<!-- SOURCE FILE: kgg-update/src/base-head.html -->
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<!--
KGG INTERNAL SOURCE TRUTH — READ THIS FIRST

Machine-readable app state, patch rules, and changelog are embedded near the top of this HTML.
Before editing this app, any LLM/agent/human should read these blocks:
1. <script type="application/json" id="kgg-source-truth">
{
  "schema": 1,
  "app": "KGG Plan",
  "activeFixes": [
    "embedded-source-truth",
    "patch-retention-guard",
    "rollback-v023-debug-breakage",
    "phone-viewport-state-leak-guard",
    "phone-plan-local-list-drag",
    "local-content-no-auto-redirect",
    "no-auto-release-navigation",
    "release-center-local-fallback",
    "structured-textblock-parser",
    "free-textfield-units",
    "schmerz-tag-textblocks",
    "native-sync-diagnostics",
    "device-sync-menu-separation",
    "ui-mini-series",
    "phone-dock-anchored-correction",
    "tablet-card-reorder",
    "phone-liquid-actions",
    "phone-drawer-bank-align",
    "tablet-runtime-viewport-guard",
    "phone-landscape-tablet-menu",
    "encoding-guard-repair",
    "symbol-encoding-hotfix",
    "phone-ui-mini-fix",
    "android-qr-pdf-bridge",
    "pdf-plan-thumbnails",
    "ui-tablet-stability",
    "patient-qr-latest-base",
    "colleague-share-apk-update-fix",
    "patient-qr-root-query",
    "grossdruck-pdf-readable-images",
    "grossdruck-readability-beta",
    "059-ui-scaler-push-canary",
    "tablet-html-release-label",
    "cross-app-live-qr-camera",
    "tablet-recent-package-shell-geometry"
  ],
  "currentVersion": {
    "versionCode": 62,
    "versionName": "1.0.62-tablet-recent-package-shell-geometry",
    "lastPatchId": "kgg-v062-tablet-recent-package-shell-geometry",
    "updatedBy": "kgg-module-scaffolder"
  },
  "latestPatchId": "kgg-v062-tablet-recent-package-shell-geometry",
  "lastUpdateIntent": {
    "id": "kgg-v062-tablet-recent-package-shell-geometry",
    "summary": "Die bereits bestätigte Tablet-Historien-Shell bleibt unverändert; zusätzlich übernimmt sie exakt die grüne Arbeitsflächen-Geometrie des Übungspakete-Overlays, damit der Hintergrund beim Öffnen nicht mehr verspringt.",
    "touched": [
      "Tablet-Layout",
      "Historien-Overlay",
      "Übungspakete-Overlay-Shell"
    ],
    "notTouched": [
      "PDF",
      "QR/Patienten-App",
      "Scan/OCR",
      "Parser",
      "Plan-State",
      "Medien/Upload",
      "API-Key-Logik",
      "Android/APK",
      "GitHub Manifest",
      "Handy-Layout"
    ]
  }
}
</script>
<!-- END kgg-source-truth -->

<!-- SOURCE FILE: kgg-update/src/metadata/source-truth.html -->
<script type="application/json" id="kgg-source-truth">
{
  "schema": 1,
  "app": "KGG Plan",
  "activeFixes": [
    "embedded-source-truth",
    "patch-retention-guard",
    "rollback-v023-debug-breakage",
    "phone-viewport-state-leak-guard",
    "phone-plan-local-list-drag",
    "local-content-no-auto-redirect",
    "no-auto-release-navigation",
    "release-center-local-fallback",
    "structured-textblock-parser",
    "free-textfield-units",
    "schmerz-tag-textblocks",
    "native-sync-diagnostics",
    "device-sync-menu-separation",
    "ui-mini-series",
    "phone-dock-anchored-correction",
    "tablet-card-reorder",
    "phone-liquid-actions",
    "phone-drawer-bank-align",
    "tablet-runtime-viewport-guard",
    "phone-landscape-tablet-menu",
    "encoding-guard-repair",
    "symbol-encoding-hotfix",
    "phone-ui-mini-fix",
    "android-qr-pdf-bridge",
    "pdf-plan-thumbnails",
    "ui-tablet-stability",
    "patient-qr-latest-base",
    "colleague-share-apk-update-fix",
    "patient-qr-root-query",
    "grossdruck-pdf-readable-images",
    "grossdruck-readability-beta",
    "059-ui-scaler-push-canary",
    "tablet-html-release-label",
    "cross-app-live-qr-camera",
    "tablet-recent-package-shell-geometry"
  ],
  "currentVersion": {
    "versionCode": 62,
    "versionName": "1.0.62-tablet-recent-package-shell-geometry",
    "lastPatchId": "kgg-v062-tablet-recent-package-shell-geometry",
    "updatedBy": "kgg-module-scaffolder"
  },
  "latestPatchId": "kgg-v062-tablet-recent-package-shell-geometry",
  "lastUpdateIntent": {
    "id": "kgg-v062-tablet-recent-package-shell-geometry",
    "summary": "Die bereits bestätigte Tablet-Historien-Shell bleibt unverändert; zusätzlich übernimmt sie exakt die grüne Arbeitsflächen-Geometrie des Übungspakete-Overlays, damit der Hintergrund beim Öffnen nicht mehr verspringt.",
    "touched": [
      "Tablet-Layout",
      "Historien-Overlay",
      "Übungspakete-Overlay-Shell"
    ],
    "notTouched": [
      "PDF",
      "QR/Patienten-App",
      "Scan/OCR",
      "Parser",
      "Plan-State",
      "Medien/Upload",
      "API-Key-Logik",
      "Android/APK",
      "GitHub Manifest",
      "Handy-Layout"
    ]
  }
}
</script>

<!-- SOURCE FILE: kgg-update/src/metadata/changelog.html -->

<!-- BEGIN kgg-changelog: embedded Changelog; READ THIS BEFORE PATCHING -->
<script type="application/json" id="kgg-changelog">
{
  "schema": 1,
  "latestVersionCode": 62,
  "entries": [
    {
      "versionCode": 62,
      "versionName": "1.0.62-tablet-recent-package-shell-geometry",
      "patchId": "kgg-v062-tablet-recent-package-shell-geometry",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Plan-Historie mit stabiler Hintergrund-Geometrie",
      "reason": "Die bereits bestätigte Tablet-Historien-Shell bleibt unverändert; zusätzlich übernimmt sie exakt die grüne Arbeitsflächen-Geometrie des Übungspakete-Overlays, damit der Hintergrund beim Öffnen nicht mehr verspringt.",
      "whatChanged": [
        "Die bereits bestätigte Tablet-Historien-Shell bleibt unverändert; zusätzlich übernimmt sie exakt die grüne Arbeitsflächen-Geometrie des Übungspakete-Overlays, damit der Hintergrund beim Öffnen nicht mehr verspringt."
      ],
      "touchedAreas": [
        "Tablet-Layout",
        "Historien-Overlay",
        "Übungspakete-Overlay-Shell"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Gate-managed Custom GPT module patch; Max approved modular GPT migration with existing embedded changelog overflow."
    },
    {
      "versionCode": 61,
      "versionName": "1.0.61-cross-app-live-qr-camera",
      "patchId": "kgg-v061-cross-app-live-qr-camera",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "PAT Live-QR-Kamera fuer Admin",
      "reason": "Uebernimmt den bewaehrten kontinuierlichen Patienten-QR-Scan mit lokalem jsQR-Fallback und manueller Papieraufnahme in die Admin-Test-App.",
      "whatChanged": [
        "Uebernimmt den bewaehrten kontinuierlichen Patienten-QR-Scan mit lokalem jsQR-Fallback und manueller Papieraufnahme in die Admin-Test-App."
      ],
      "touchedAreas": [
        "Scan/OCR",
        "QR/Patienten-App",
        "Android/APK"
      ],
      "notTouched": [
        "PDF",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Max hat den PAT-Scanner-Port und den begrenzten Cross-App-Kamerazugriff am 2026-08-01 ausdruecklich beauftragt."
    },
    {
      "versionCode": 60,
      "versionName": "1.0.60-tablet-html-release-label",
      "patchId": "kgg-v060-tablet-html-release-label",
      "status": "certified",
      "type": "module-patch",
      "title": "Tablet HTML Release Label",
      "reason": "Zeigt den Namen der aktuell geladenen HTML-Version unten rechts im ausgefahrenen Tablet-Menue.",
      "whatChanged": [
        "Zeigt den Namen der aktuell geladenen HTML-Version unten rechts im ausgefahrenen Tablet-Menue."
      ],
      "touchedAreas": [
        "Tablet-Menue"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "passed",
        "certification": "passed",
        "notes": "Vollstaendige Regression plus dynamischer APK-/Web-Identitaets- und Bottom-Right-Positionstest."
      },
      "approvalNote": "Max hat den sichtbaren Tablet-Menue-Patch ausdruecklich beauftragt; die Changelog-Archivierung bleibt ein separater Folgepatch."
    },
    {
      "versionCode": 59,
      "versionName": "1.0.59-ui-scaler-push-canary",
      "patchId": "kgg-v059-ui-scaler-push-canary",
      "status": "active",
      "type": "kgg-gpt-write-gate",
      "title": "Visible harmless UI scaler label change for end-to-end Test-App and Admin-Beta push verification.",
      "reason": "Custom GPT preview was accepted by Max and routed through the guarded write gate.",
      "whatChanged": [
        "Visible harmless UI scaler label change for end-to-end Test-App and Admin-Beta push verification."
      ],
      "touchedAreas": [
        "kgg-update/index.html"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "github": "pending",
        "notes": "Required Gate and release-pr validate-build must pass before merge."
      }
    },
    {
      "versionCode": 58,
      "versionName": "1.0.58-grossdruck-readability-beta",
      "patchId": "kgg-v058-grossdruck-readability-beta",
      "status": "active",
      "type": "local-html-patch",
      "title": "Grossdruck-PDF mit Kurzsichtigkeits-Test",
      "reason": "Die Grossdruck-PDF soll fuer kurzsichtige Leser:innen bei Uebungsname, Satz, Wdh, kg/Gewicht und Schmerzskala messbar lesbarer sein, bevor eine Admin-Beta gebaut wird.",
      "whatChanged": [
        "Grossdruck-Titel, Meta-Zeilen und Tabellenlabels werden auf 14pt, 8.6pt und 7pt Mindestgroessen angehoben.",
        "Die Grossdruck-Vorlage bleibt bei 3 Uebungen pro A4-Seite, nutzt aber groessere Abstaende und ein L3-v3 Template.",
        "Eine lokale PDF-Readability-Testengine erzeugt Test-PDFs, Poppler-Renderings und Kurzsichtigkeits-Simulationen."
      ],
      "touchedAreas": [
        "PDF generation",
        "Grossdruck PDF layout",
        "PDF readability test engine",
        "Release test battery",
        "Source Truth",
        "version.json"
      ],
      "notTouched": [
        "QR/Patienten-App",
        "Scan/OCR parser",
        "Gemini API pipeline",
        "Parser",
        "Plan-State",
        "Android/APK",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "notes": "node release-pipeline/kgg_pdf_readability_smoke.js plus PDF critical und critical suite vor Admin-Beta."
      }
    },
    {
      "versionCode": 57,
      "versionName": "1.0.57-grossdruck-pdf-readable-images",
      "patchId": "kgg-v057-grossdruck-pdf-readable-images",
      "status": "active",
      "type": "local-html-patch",
      "title": "Grossdruck-PDF mit Bildern und groesserer Schrift",
      "reason": "Die vergroesserte PDF-Version soll vorhandene Uebungsbilder zeigen und auf A4 lesbarer sein, ohne Scan/OCR, QR oder Plan-State zu aendern.",
      "whatChanged": [
        "Grossdruck-PDF wird als echtes A4-Portrait mit 3 Uebungen pro Seite erzeugt.",
        "Lokale PDF-Uebungsbilder werden auch im Grossdruck-Snapshot geladen.",
        "Grossdruck-Tabellen, Kopfzeilen und Karten nutzen groessere Fontgroessen und Abstaende."
      ],
      "touchedAreas": [
        "PDF generation",
        "Grossdruck PDF layout",
        "PDF exercise thumbnails",
        "Source Truth",
        "version.json"
      ],
      "notTouched": [
        "QR/Patienten-App",
        "Scan/OCR parser",
        "Gemini API pipeline",
        "Parser",
        "Plan-State",
        "Android/APK",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "notes": "Critical plus PDF render smoke; Gemini-Live-Smoke nur mit lokal vorhandener Admin-Konfig/API-Key."
      }
    },
    {
      "versionCode": 56,
      "versionName": "1.0.56-patient-qr-root-query",
      "patchId": "kgg-v056-patient-qr-root-query",
      "status": "active",
      "type": "local-html-patch",
      "title": "Patienten-QR nutzt Root-App mit Query-Payload",
      "reason": "Der Trainingsplan-QR soll die aktuelle Patienten-App oeffnen und den Plan direkt ueber ?plan=KGGH2:... uebergeben, statt auf den alten Renderer-Pfad oder gespeicherte Altplaene zu fallen.",
      "whatChanged": [
        "Default-Patienten-App-Basis zeigt auf https://kayus24.github.io/kgg/.",
        "Neue Patienten-QRs verwenden ?plan=KGGH2:<payload>.",
        "Tests blockieren kgg-update/index.html, releases und media-inline-bundle-7 als Standard-Patientenlink."
      ],
      "touchedAreas": [
```
