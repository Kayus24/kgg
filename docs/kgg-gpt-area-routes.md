# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-4e4bba2570e8d879.md`, `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md`, `docs/kgg-gpt-source/chunk-v2-3ba34d7ce2c4a75c.md`, `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1775
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1714
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1813
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md` from `kgg-update/src/document/head-ui.html` line 744
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6723
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-v2-3ba34d7ce2c4a75c.md` from `kgg-update/src/runtime/app-core.html` line 6863

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1f705f359e2cd671.md`, `docs/kgg-gpt-source/chunk-v2-ffcaa82769342a15.md`, `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-7148376ffc56b310.md`, `docs/kgg-gpt-source/chunk-v2-f4b2d210c83d4148.md`, `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md`, `docs/kgg-gpt-source/chunk-v2-048facdccb5f36f0.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 45
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md` from `kgg-update/src/document/head-ui.html` line 2670
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-v2-1f705f359e2cd671.md` from `kgg-update/src/metadata/patch-rules.html` line 118

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-a919cbbe18ba7d80.md`, `docs/kgg-gpt-source/chunk-v2-52fc54134ed60677.md`, `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md`, `docs/kgg-gpt-source/chunk-v2-bbfd62268e7bc895.md`, `docs/kgg-gpt-source/chunk-v2-b25b9279c7b0d9b9.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md`, `docs/kgg-gpt-source/chunk-v2-3ba34d7ce2c4a75c.md`, `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 4934
  - `KGGH2`: `docs/kgg-gpt-source/chunk-v2-a919cbbe18ba7d80.md` from `kgg-update/src/metadata/changelog.html` line 18
  - `KGGH3`: `docs/kgg-gpt-source/chunk-v2-a919cbbe18ba7d80.md` from `kgg-update/src/metadata/changelog.html` line 18
  - `makeKggH3ShareUrl`: `docs/kgg-gpt-source/chunk-v2-b25b9279c7b0d9b9.md` from `kgg-update/src/runtime/app-core.html` line 4634
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-v2-bbfd62268e7bc895.md` from `kgg-update/src/runtime/app-core.html` line 3084
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md` from `kgg-update/src/runtime/app-core.html` line 7271
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6586

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6517
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6616
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6586
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md` from `kgg-update/src/patches/v061-cross-app-live-qr-camera.html` line 10
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-v2-3475e9435b333a13.md` from `kgg-update/src/runtime/app-core.html` line 6617

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md`, `docs/kgg-gpt-source/chunk-v2-9e6d2594a0e567f6.md`, `docs/kgg-gpt-source/chunk-v2-b25b9279c7b0d9b9.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-3ba34d7ce2c4a75c.md`, `docs/kgg-gpt-source/chunk-v2-2e9fa891c1ef2855.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 4916
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md` from `kgg-update/src/runtime/pdf-offline.html` line 110
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-v2-9e6d2594a0e567f6.md` from `kgg-update/src/runtime/app-core.html` line 3946

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-c10b65bf601ddfaa.md`, `docs/kgg-gpt-source/chunk-v2-75dd47fe75e6ee4d.md`, `docs/kgg-gpt-source/chunk-v2-bbfd62268e7bc895.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-c10b65bf601ddfaa.md` from `kgg-update/src/runtime/app-core.html` line 779
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-14ecc856340ded54.md`, `docs/kgg-gpt-source/chunk-v2-c399a91bc1a42a84.md`, `docs/kgg-gpt-source/chunk-v2-c10b65bf601ddfaa.md`, `docs/kgg-gpt-source/chunk-v2-75dd47fe75e6ee4d.md`, `docs/kgg-gpt-source/chunk-v2-bbfd62268e7bc895.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-v2-14ecc856340ded54.md` from `kgg-update/src/runtime/app-core.html` line 51
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-v2-bbfd62268e7bc895.md` from `kgg-update/src/runtime/app-core.html` line 3186
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-c10b65bf601ddfaa.md` from `kgg-update/src/runtime/app-core.html` line 779

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-208ab64db2a985ef.md`, `docs/kgg-gpt-source/chunk-v2-c76cf10c62062774.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-v2-208ab64db2a985ef.md` from `kgg-update/src/runtime/app-core.html` line 1955

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-639bfac8ea49cbde.md`, `docs/kgg-gpt-source/chunk-v2-7fed7106b40c946e.md`, `docs/kgg-gpt-source/chunk-v2-a919cbbe18ba7d80.md`, `docs/kgg-gpt-source/chunk-v2-1f705f359e2cd671.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-v2-639bfac8ea49cbde.md` from `kgg-update/src/base-head.html` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-v2-a919cbbe18ba7d80.md` from `kgg-update/src/metadata/changelog.html` line 2
