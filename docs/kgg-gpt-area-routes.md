# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-4e4bba2570e8d879.md`, `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1775
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1714
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-v2-6312112f51263fc5.md` from `kgg-update/src/document/head-ui.html` line 1813
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md` from `kgg-update/src/document/head-ui.html` line 744
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 7071
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md` from `kgg-update/src/runtime/app-core.html` line 7211

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-a2cff5731b444a25.md`, `docs/kgg-gpt-source/chunk-v2-830142c250300581.md`, `docs/kgg-gpt-source/chunk-v2-22071abd1ef89599.md`, `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md`, `docs/kgg-gpt-source/chunk-v2-7148376ffc56b310.md`, `docs/kgg-gpt-source/chunk-v2-f4b2d210c83d4148.md`, `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md`, `docs/kgg-gpt-source/chunk-v2-ff09e6b1ba093e76.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 11
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-v2-ef0b58c6b5b2bf0a.md` from `kgg-update/src/patches/v041-ui-mini-series.html` line 45
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-v2-48801c41482633dd.md` from `kgg-update/src/document/head-ui.html` line 2670
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-v2-a2cff5731b444a25.md` from `kgg-update/src/metadata/patch-rules.html` line 118

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-91a70596533f4f5f.md`, `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`, `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-56f504b12af65b0f.md`, `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md`, `docs/kgg-gpt-source/chunk-v2-45550afade9ceee6.md`, `docs/kgg-gpt-source/chunk-v2-1af68ff5a323a7ae.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 5249
  - `KGGH2`: `docs/kgg-gpt-source/chunk-v2-149070a0516344a4.md` from `kgg-update/src/runtime/kgg-plan-format.html` line 7
  - `KGGH3`: `docs/kgg-gpt-source/chunk-v2-91a70596533f4f5f.md` from `kgg-update/src/document/body-shell.html` line 223
  - `makeKggH3ShareUrl`: `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md` from `kgg-update/src/runtime/app-core.html` line 4949
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md` from `kgg-update/src/runtime/app-core.html` line 3274
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-v2-6f72c87927a47a34.md` from `kgg-update/src/runtime/app-core.html` line 7626
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 6934

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md`, `docs/kgg-gpt-source/chunk-v2-1af68ff5a323a7ae.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 6847
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 6964
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 6934
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-v2-1af68ff5a323a7ae.md` from `kgg-update/src/patches/v061-cross-app-live-qr-camera.html` line 10
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-v2-dcbb0725a95735b8.md` from `kgg-update/src/runtime/app-core.html` line 6965

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md`, `docs/kgg-gpt-source/chunk-v2-10ab656515746c5a.md`, `docs/kgg-gpt-source/chunk-v2-66e77f020a460bad.md`, `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md`, `docs/kgg-gpt-source/chunk-v2-8b9415d4864a23cd.md`, `docs/kgg-gpt-source/chunk-v2-2e9fa891c1ef2855.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-v2-e3eeee1a8a0275be.md` from `kgg-update/src/runtime/app-core.html` line 5231
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-v2-1c7d66f373a9e683.md` from `kgg-update/src/runtime/pdf-offline.html` line 110
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-v2-10ab656515746c5a.md` from `kgg-update/src/runtime/app-core.html` line 4236

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md`, `docs/kgg-gpt-source/chunk-v2-3d1532733516ff26.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md` from `kgg-update/src/runtime/app-core.html` line 779
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-248052c990ccba20.md`, `docs/kgg-gpt-source/chunk-v2-c399a91bc1a42a84.md`, `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md`, `docs/kgg-gpt-source/chunk-v2-3d1532733516ff26.md`, `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md`, `docs/kgg-gpt-source/chunk-v2-d4ae4133b4e424b4.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-v2-248052c990ccba20.md` from `kgg-update/src/runtime/app-core.html` line 51
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-v2-1546593b84682cc2.md` from `kgg-update/src/runtime/app-core.html` line 3376
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-v2-57fb9722c411a800.md` from `kgg-update/src/runtime/app-core.html` line 779

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-37e369501c6c89c9.md`, `docs/kgg-gpt-source/chunk-v2-6e2d852ba7b6b32b.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-v2-37e369501c6c89c9.md` from `kgg-update/src/runtime/app-core.html` line 1968

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-v2-409ec81c9acb4b81.md`, `docs/kgg-gpt-source/chunk-v2-93158d962fca8108.md`, `docs/kgg-gpt-source/chunk-v2-0c6d0541f8b5e1b5.md`, `docs/kgg-gpt-source/chunk-v2-14f199bfb754911c.md`, `docs/kgg-gpt-source/chunk-v2-a2cff5731b444a25.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-v2-409ec81c9acb4b81.md` from `kgg-update/src/base-head.html` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-v2-0c6d0541f8b5e1b5.md` from `kgg-update/src/metadata/changelog.html` line 2
