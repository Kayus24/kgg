# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-4e4bba2570e8d879.md`, `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1775
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1714
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1813
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md` from `kgg-update/src/document/head-ui.html` line 744
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 7049
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md` from `kgg-update/src/runtime/app-core.html` line 7189

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-3f0661d3bfe74555.md`, `docs/kgg-gpt-source/chunk-v2-e8caed52c244518b.md`, `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-7148376ffc56b310.md`, `docs/kgg-gpt-source/chunk-v2-f4b2d210c83d4148.md`, `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md`, `docs/kgg-gpt-source/chunk-v2-ff09e6b1ba093e76.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 45
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md` from `kgg-update/src/document/head-ui.html` line 2670
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-v2-3f0661d3bfe74555.md` from `kgg-update/src/metadata/patch-rules.html` line 118

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-91a70596533f4f5f.md`, `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`, `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-56f504b12af65b0f.md`, `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 5247
  - `KGGH2`: `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md` from `kgg-update/src/runtime/kgg-plan-format.html` line 7
  - `KGGH3`: `docs/kgg-gpt-source/chunk-v2-91a70596533f4f5f.md` from `kgg-update/src/document/body-shell.html` line 223
  - `makeKggH3ShareUrl`: `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md` from `kgg-update/src/runtime/app-core.html` line 4947
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md` from `kgg-update/src/runtime/app-core.html` line 3272
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md` from `kgg-update/src/runtime/app-core.html` line 7604
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 6912

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md`, `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 6842
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 6942
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 6912
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-v2-d3cb2b3eb0e8e619.md` from `kgg-update/src/patches/v061-cross-app-live-qr-camera.html` line 10
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-v2-f0a80bda6e162045.md` from `kgg-update/src/runtime/app-core.html` line 6943

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md`, `docs/kgg-gpt-source/chunk-v2-10ab656515746c5a.md`, `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-2e9fa891c1ef2855.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 5229
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md` from `kgg-update/src/runtime/pdf-offline.html` line 110
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-v2-10ab656515746c5a.md` from `kgg-update/src/runtime/app-core.html` line 4234

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md`, `docs/kgg-gpt-source/chunk-v2-b47845ac4342135d.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md` from `kgg-update/src/runtime/app-core.html` line 779
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-f00cb05d8160bac5.md`, `docs/kgg-gpt-source/chunk-v2-c399a91bc1a42a84.md`, `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md`, `docs/kgg-gpt-source/chunk-v2-b47845ac4342135d.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`, `docs/kgg-gpt-source/chunk-v2-d4ae4133b4e424b4.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-v2-f00cb05d8160bac5.md` from `kgg-update/src/runtime/app-core.html` line 51
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md` from `kgg-update/src/runtime/app-core.html` line 3374
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md` from `kgg-update/src/runtime/app-core.html` line 779

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-def07cc9ee7bbca6.md`, `docs/kgg-gpt-source/chunk-v2-552835ad2bd758be.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-v2-def07cc9ee7bbca6.md` from `kgg-update/src/runtime/app-core.html` line 1968

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-51231f0ef9d6bc25.md`, `docs/kgg-gpt-source/chunk-v2-3c54f3cb3206cb42.md`, `docs/kgg-gpt-source/chunk-v2-e3661427f3a53574.md`, `docs/kgg-gpt-source/chunk-v2-3f0661d3bfe74555.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-v2-51231f0ef9d6bc25.md` from `kgg-update/src/base-head.html` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-v2-e3661427f3a53574.md` from `kgg-update/src/metadata/changelog.html` line 2
