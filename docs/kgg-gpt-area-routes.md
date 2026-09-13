# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-4e4bba2570e8d879.md`, `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-6632393d0bf01abd.md`, `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1775
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1714
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1813
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md` from `kgg-update/src/document/head-ui.html` line 744
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6629
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-v2-6632393d0bf01abd.md` from `kgg-update/src/runtime/app-core.html` line 6765

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-aee7655e6abb4889.md`, `docs/kgg-gpt-source/chunk-v2-b43b1beb8073b31e.md`, `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-7148376ffc56b310.md`, `docs/kgg-gpt-source/chunk-v2-f4b2d210c83d4148.md`, `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md`, `docs/kgg-gpt-source/chunk-v2-048facdccb5f36f0.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-v2-b0058ed5b447e425.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 45
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md` from `kgg-update/src/document/head-ui.html` line 2670
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-v2-aee7655e6abb4889.md` from `kgg-update/src/metadata/patch-rules.html` line 118

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-6497790a973d8797.md`, `docs/kgg-gpt-source/chunk-v2-40aa17d0c1fc062c.md`, `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md`, `docs/kgg-gpt-source/chunk-v2-dea245f83f6ea1da.md`, `docs/kgg-gpt-source/chunk-v2-b878f0e5f6c88c8b.md`, `docs/kgg-gpt-source/chunk-v2-f88f6861f96e33ae.md`, `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-6632393d0bf01abd.md`, `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-v2-f88f6861f96e33ae.md` from `kgg-update/src/runtime/app-core.html` line 4840
  - `KGGH2`: `docs/kgg-gpt-source/chunk-v2-6497790a973d8797.md` from `kgg-update/src/metadata/changelog.html` line 337
  - `KGGH3`: `docs/kgg-gpt-source/chunk-v2-6497790a973d8797.md` from `kgg-update/src/metadata/changelog.html` line 333
  - `makeKggH3ShareUrl`: `docs/kgg-gpt-source/chunk-v2-b878f0e5f6c88c8b.md` from `kgg-update/src/runtime/app-core.html` line 4540
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-v2-dea245f83f6ea1da.md` from `kgg-update/src/runtime/app-core.html` line 3063
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-v2-89412742830e5b96.md` from `kgg-update/src/runtime/app-core.html` line 7172
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6492

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6423
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6522
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6492
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md` from `kgg-update/src/patches/v061-cross-app-live-qr-camera.html` line 10
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-v2-897ecd5a4f2ace89.md` from `kgg-update/src/runtime/app-core.html` line 6523

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md`, `docs/kgg-gpt-source/chunk-v2-71fbb6667dad86ff.md`, `docs/kgg-gpt-source/chunk-v2-b878f0e5f6c88c8b.md`, `docs/kgg-gpt-source/chunk-v2-f88f6861f96e33ae.md`, `docs/kgg-gpt-source/chunk-v2-6632393d0bf01abd.md`, `docs/kgg-gpt-source/chunk-v2-2e9fa891c1ef2855.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-v2-f88f6861f96e33ae.md` from `kgg-update/src/runtime/app-core.html` line 4822
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md` from `kgg-update/src/runtime/pdf-offline.html` line 110
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-v2-71fbb6667dad86ff.md` from `kgg-update/src/runtime/app-core.html` line 3880

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-ab206cfda2463fc1.md`, `docs/kgg-gpt-source/chunk-v2-dea245f83f6ea1da.md`, `docs/kgg-gpt-source/chunk-v2-f4bf6424a0c6f26d.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-ab206cfda2463fc1.md` from `kgg-update/src/runtime/app-core.html` line 778
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-002f9bd68c9ccc55.md`, `docs/kgg-gpt-source/chunk-v2-c399a91bc1a42a84.md`, `docs/kgg-gpt-source/chunk-v2-ab206cfda2463fc1.md`, `docs/kgg-gpt-source/chunk-v2-dea245f83f6ea1da.md`, `docs/kgg-gpt-source/chunk-v2-f4bf6424a0c6f26d.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-v2-002f9bd68c9ccc55.md` from `kgg-update/src/runtime/app-core.html` line 50
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-v2-f4bf6424a0c6f26d.md` from `kgg-update/src/runtime/app-core.html` line 3165
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-ab206cfda2463fc1.md` from `kgg-update/src/runtime/app-core.html` line 778

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-c61486f8b5531295.md`, `docs/kgg-gpt-source/chunk-v2-b795156b00755847.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-v2-c61486f8b5531295.md` from `kgg-update/src/runtime/app-core.html` line 1953

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-df3d98f956119563.md`, `docs/kgg-gpt-source/chunk-v2-90d653cb89864dba.md`, `docs/kgg-gpt-source/chunk-v2-6497790a973d8797.md`, `docs/kgg-gpt-source/chunk-v2-aee7655e6abb4889.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-v2-df3d98f956119563.md` from `kgg-update/src/base-head.html` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-v2-6497790a973d8797.md` from `kgg-update/src/metadata/changelog.html` line 2
