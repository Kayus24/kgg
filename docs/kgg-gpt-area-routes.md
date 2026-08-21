# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-2ef360223df0d59a.md`, `docs/kgg-gpt-source/chunk-v2-8d7262cbd622d6b5.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-4e4bba2570e8d879.md`, `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-abda8c72aa216cd7.md`, `docs/kgg-gpt-source/chunk-v2-3a427ee8d016b5fa.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-v2-8d7262cbd622d6b5.md` from `kgg-update/src/document/head-ui.html` line 1768
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-v2-8d7262cbd622d6b5.md` from `kgg-update/src/document/head-ui.html` line 1707
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-v2-8d7262cbd622d6b5.md` from `kgg-update/src/document/head-ui.html` line 1806
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-v2-2ef360223df0d59a.md` from `kgg-update/src/document/head-ui.html` line 737
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6520
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-v2-abda8c72aa216cd7.md` from `kgg-update/src/runtime/app-core.html` line 6656

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-d9785f81054d8643.md`, `docs/kgg-gpt-source/chunk-v2-91cffbc572adb9de.md`, `docs/kgg-gpt-source/chunk-v2-2ef360223df0d59a.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-7148376ffc56b310.md`, `docs/kgg-gpt-source/chunk-v2-f4b2d210c83d4148.md`, `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md`, `docs/kgg-gpt-source/chunk-v2-048facdccb5f36f0.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 45
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md` from `kgg-update/src/document/head-ui.html` line 2663
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-v2-d9785f81054d8643.md` from `kgg-update/src/metadata/patch-rules.html` line 118

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-f3e741f5c3d4453b.md`, `docs/kgg-gpt-source/chunk-v2-64dbbad2f3ff6d2c.md`, `docs/kgg-gpt-source/chunk-v2-cb3ff21a2a089711.md`, `docs/kgg-gpt-source/chunk-v2-35db267aa82f89fb.md`, `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-abda8c72aa216cd7.md`, `docs/kgg-gpt-source/chunk-v2-3a427ee8d016b5fa.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-v2-35db267aa82f89fb.md` from `kgg-update/src/runtime/app-core.html` line 4743
  - `KGGH2`: `docs/kgg-gpt-source/chunk-v2-f3e741f5c3d4453b.md` from `kgg-update/src/metadata/changelog.html` line 469
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-v2-64dbbad2f3ff6d2c.md` from `kgg-update/src/runtime/app-core.html` line 3047
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-v2-3a427ee8d016b5fa.md` from `kgg-update/src/runtime/app-core.html` line 7062
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6383

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6314
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6413
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6383
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md` from `kgg-update/src/patches/v061-cross-app-live-qr-camera.html` line 10
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6414

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md`, `docs/kgg-gpt-source/chunk-v2-a26714eecfe66a44.md`, `docs/kgg-gpt-source/chunk-v2-cb3ff21a2a089711.md`, `docs/kgg-gpt-source/chunk-v2-35db267aa82f89fb.md`, `docs/kgg-gpt-source/chunk-v2-abda8c72aa216cd7.md`, `docs/kgg-gpt-source/chunk-v2-2e9fa891c1ef2855.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-v2-35db267aa82f89fb.md` from `kgg-update/src/runtime/app-core.html` line 4725
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md` from `kgg-update/src/runtime/pdf-offline.html` line 110
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-v2-a26714eecfe66a44.md` from `kgg-update/src/runtime/app-core.html` line 3858

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-7bdad4bb9e8537d6.md`, `docs/kgg-gpt-source/chunk-v2-64dbbad2f3ff6d2c.md`, `docs/kgg-gpt-source/chunk-v2-7a2c828284153289.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-7bdad4bb9e8537d6.md` from `kgg-update/src/runtime/app-core.html` line 771
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-2a7ac00babda8c8e.md`, `docs/kgg-gpt-source/chunk-v2-cf60284ba3246995.md`, `docs/kgg-gpt-source/chunk-v2-7bdad4bb9e8537d6.md`, `docs/kgg-gpt-source/chunk-v2-64dbbad2f3ff6d2c.md`, `docs/kgg-gpt-source/chunk-v2-7a2c828284153289.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-v2-2a7ac00babda8c8e.md` from `kgg-update/src/runtime/app-core.html` line 50
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-v2-7a2c828284153289.md` from `kgg-update/src/runtime/app-core.html` line 3149
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-7bdad4bb9e8537d6.md` from `kgg-update/src/runtime/app-core.html` line 771

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-39e873ccf0bac40b.md`, `docs/kgg-gpt-source/chunk-v2-ebfcc7035772d0ab.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-v2-39e873ccf0bac40b.md` from `kgg-update/src/runtime/app-core.html` line 1937

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-7f177d03ad9951ef.md`, `docs/kgg-gpt-source/chunk-v2-394807ea5bac58a9.md`, `docs/kgg-gpt-source/chunk-v2-f3e741f5c3d4453b.md`, `docs/kgg-gpt-source/chunk-v2-d9785f81054d8643.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-v2-7f177d03ad9951ef.md` from `kgg-update/src/base-head.html` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-v2-f3e741f5c3d4453b.md` from `kgg-update/src/metadata/changelog.html` line 2
