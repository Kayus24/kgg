# Patient App Changelog

## 2026-06-18 – No-plan QR rescue scanner

### Changed
- If the installed web app opens without a plan and shows `Kein Plan gefunden`, a large rescue panel is shown directly below the warning.
- The rescue panel contains a big `Plan-QR scannen` button.
- Patients can also paste a plan link if camera/BarcodeDetector is unavailable.
- This lets patients recover a lost plan link from inside the installed web app.

### Files
- `patient-start-scan.js`
- `service-worker.js`

### Commits
- `a2f2be9b11be33c65e430c7759607d25dabcc90b`
- `19cca01527f028cda5fa9065052227aa0c67aa49`

### Safety
- No changes to PDF.
- No changes to parser, scan/OCR pipeline, Numpad, storage, or exercise database logic.

## 2026-06-18 – Closed exercise card media thumbnails

### Changed
- Closed exercise cards now show a small thumbnail on the right side when the exercise has a real image/media item.
- The thumbnail is hidden again when the card is opened.
- Existing full media display inside opened exercise cards remains unchanged.

### Files
- `patient-media-retry-cache_v2.js`

### Commit
- `58f43b9dafa1f13d56758c0510ca018836e02767`

### Safety
- No changes to PDF.
- No changes to QR generation.
- No changes to parser, scan/OCR, Numpad, storage, or exercise database logic.
