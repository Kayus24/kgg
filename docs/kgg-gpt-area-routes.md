# KGG GPT Area Routes

Generated from `kgg-update/index.html`. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-004.md`, `docs/kgg-gpt-source/chunk-005.md`, `docs/kgg-gpt-source/chunk-007.md`, `docs/kgg-gpt-source/chunk-008.md`, `docs/kgg-gpt-source/chunk-013.md`, `docs/kgg-gpt-source/chunk-055.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-058.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-007.md` line 3125
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-007.md` line 3064
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-007.md` line 3163
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-004.md` line 2094
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-055.md` line 23409
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-056.md` line 23544

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-002.md`, `docs/kgg-gpt-source/chunk-003.md`, `docs/kgg-gpt-source/chunk-005.md`, `docs/kgg-gpt-source/chunk-009.md`, `docs/kgg-gpt-source/chunk-010.md`, `docs/kgg-gpt-source/chunk-011.md`, `docs/kgg-gpt-source/chunk-012.md`, `docs/kgg-gpt-source/chunk-060.md`, `docs/kgg-gpt-source/chunk-061.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-060.md` line 25521
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-060.md` line 25521
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-060.md` line 25555
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-002.md` line 904
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-003.md` line 1278

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-000.md`, `docs/kgg-gpt-source/chunk-047.md`, `docs/kgg-gpt-source/chunk-050.md`, `docs/kgg-gpt-source/chunk-051.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-057.md`, `docs/kgg-gpt-source/chunk-058.md`, `docs/kgg-gpt-source/chunk-062.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-051.md` line 21682
  - `KGGH2`: `docs/kgg-gpt-source/chunk-000.md` line 54
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-047.md` line 20003
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-057.md` line 23950

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-014.md`, `docs/kgg-gpt-source/chunk-049.md`, `docs/kgg-gpt-source/chunk-050.md`, `docs/kgg-gpt-source/chunk-051.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-063.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-051.md` line 21664
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-014.md` line 5983
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-049.md` line 20811

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-042.md`, `docs/kgg-gpt-source/chunk-046.md`, `docs/kgg-gpt-source/chunk-047.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-042.md` line 17812
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-001.md`, `docs/kgg-gpt-source/chunk-040.md`, `docs/kgg-gpt-source/chunk-041.md`, `docs/kgg-gpt-source/chunk-042.md`, `docs/kgg-gpt-source/chunk-046.md`, `docs/kgg-gpt-source/chunk-047.md`, `docs/kgg-gpt-source/chunk-048.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-001.md` line 818
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-047.md` line 20105
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-042.md` line 17812

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-044.md`, `docs/kgg-gpt-source/chunk-045.md`, `docs/kgg-gpt-source/chunk-054.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-044.md` line 18893

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-000.md`, `docs/kgg-gpt-source/chunk-002.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-000.md` line 10
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-000.md` line 138
