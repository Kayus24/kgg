# Release Handoff v007 — QR Photo Upload Decode

## Status

Bereit als GitHub-Update-Patchscript. Keine große HTML-Datei muss über den Connector hochgeladen werden.

## Ausführen

```bash
python3 scripts/apply_v007_qr_photo_upload_decode.py
```

## Erwartete geänderte Dateien

```txt
kgg-update/index.html
kgg-update/version.json
```

## Guard

Wenn andere Dateien geändert werden: stoppen.

## Commit Message

```txt
Improve QR recognition from uploaded photo-library images
```

## Nicht anfassen

PDF, QR-Erzeugung, Patienten-App, Scan-Kamera, Parser, Android-Wrapper, Tablet-Layout, Plan-State, Storage.
