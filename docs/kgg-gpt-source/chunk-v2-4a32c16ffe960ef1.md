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
    "tablet-recent-package-shell-geometry",
    "changelog-archive-window",
    "typed-update-versions",
    "source-control-char-guard",
    "editor-trash-bank-delete"
  ],
  "currentVersion": {
    "versionCode": 66,
    "versionName": "1.0.66-editor-trash-bank-delete",
    "lastPatchId": "kgg-v066-editor-trash-bank-delete",
    "updatedBy": "kgg-module-scaffolder"
  },
  "latestPatchId": "kgg-v066-editor-trash-bank-delete",
  "lastUpdateIntent": {
    "id": "kgg-v066-editor-trash-bank-delete",
    "summary": "Der Mülleimer im Dialog Übung bearbeiten wird immer auf die bestehende bestätigte Datenbank-Löschung geroutet; das separate Entfernen aus dem aktuellen Plan bleibt unverändert.",
    "touched": [
      "Übungsdatenbank",
      "Editor"
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
