# Patient App Changelog

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
