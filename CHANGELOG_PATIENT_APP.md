# Patient App Changelog

## 2026-06-18 – Numpad input morph polish

### Changed
- The large numpad value field now starts visually from the tapped kg/Wdh input before expanding into the popup value field.
- The tapped source input stays highlighted while the numpad is open.
- The transition uses a short shared-element style morph so the popup feels more like an enlarged input field.
- Service worker cache bumped to `kgg-handyplan-v38-input-morph-polish`.

### Files
- `patient-numpad-visibility-fix.js`
- `service-worker.js`

### Commits
- `5f268f5326135cc46bdb171233a73f6f8e0b8715`
- `ed121485ec11bfaa1e3def86c041ed930b443d91`

### Safety
- No changes to PDF, QR, parser, scan/OCR, media/image logic, storage, exercise database, card collapse behavior, or numpad value logic.

## 2026-06-18 – Numpad outside-tap card guard

### Changed
- Closing the patient numpad by tapping outside should no longer collapse the opened exercise card.
- Added a small guard module and injected it through the service worker.
- Service worker cache bumped to `kgg-handyplan-v37-numpad-card-close-fix`.

### Files
- `patient-numpad-card-guard.js`
- `service-worker.js`

### Commits
- `140601d8e26b114665682b1a93204aa9006cc6e9`
- `39cbad37897ae2aa3949bd220fa68c765b527e1e`

### Safety
- No changes to PDF, QR, parser, scan/OCR, media/image logic, storage, exercise database, or main exercise layout.

## 2026-06-18 – QR fullscreen high-contrast display

### Changed
- Tapping a generated patient QR code now opens it in a fullscreen high-contrast view.
- The fullscreen QR view uses a white background and scales the QR as large as possible for therapist camera scanning.
- The fullscreen view can be closed with the close button, tapping the white backdrop, or Escape on desktop.
- A screen wake lock is requested when supported, so the QR screen is less likely to dim while being scanned.

### Files
- `patient-qr-fullscreen.js`
- `service-worker.js`

### Commits
- `452a3e6769626d4bae8ea099b83c37ef542f5be7`
- `231c29717fe9433797338caed4f3baf0c86ad340`

### Safety
- QR payload/generation unchanged.
- No changes to PDF, parser, scan/OCR, storage, Numpad, exercise database logic, or main exercise layout.

## 2026-06-18 – Open-card image lightbox

### Changed
- Images inside opened exercise cards can now be tapped to open a larger full-screen view.
- The lightbox closes with the close button, tapping the dark backdrop, or Escape on desktop.
- Closed-card thumbnails stay preview-only and do not open the lightbox.

### Files
- `patient-media-retry-cache_v2.js`
- `service-worker.js`

### Commits
- `4696df02e690e1df87d142d327a5a04f32962f2c`
- `a19c536430c5aa48c5dd6c25ac39dc2931326d3e`

### Safety
- No changes to PDF.
- No changes to QR generation.
- No changes to parser, scan/OCR, storage, Numpad, or exercise database logic.

## 2026-06-18 – Light KGG web app icon

### Changed
- Web app icon updated to the light KGG logo style: cream rounded background, olive figure, yellow motion arc and dumbbell.
- Manifest theme color adjusted to match the yellow KGG accent.

### Files
- `icon.svg`
- `manifest.json`

### Commits
- `6968c653330f416dc34522a29072854d06baba96`
- `7ca07e582dac9f4dc0a57b48e49847dc939e05ab`

### Follow-up
- Add a real binary `apple-touch-icon.png` from the provided PNG logo in a local Git/Codex commit, because the chat GitHub tool can safely write text/SVG but not binary PNG assets.

## 2026-06-18 – No-plan QR rescue scanner

### Changed
- If the installed web app opens without a plan and shows `Kein Plan gefunden`, a large rescue panel is shown directly below the warning.
- The rescue panel contains a big `Plan-QR scannen` button.
- Patients can also paste a plan link if camera scanning is unavailable.
- QR image decoding now has a jsQR fallback for browsers where `BarcodeDetector` is unavailable.
- This lets patients recover a lost plan link from inside the installed web app.

### Files
- `patient-start-scan.js`
- `service-worker.js`

### Commits
- `a2f2be9b11be33c65e430c7759607d25dabcc90b`
- `19cca01527f028cda5fa9065052227aa0c67aa49`
- `3733bef2b86548bfab509b93f134c295310fd6a5`

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
