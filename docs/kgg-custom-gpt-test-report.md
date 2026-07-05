# KGG Custom GPT Test Report

Status: PASS

Testdatum: 2026-07-05
Testziel: Custom GPT `KGG Update-Agent` im Browser-Editor `g-6a45fba0f3408191ac1fb2c987a2e960`
Instruction-Laenge nach Haertung: 7908 Zeichen, unter dem 8000-Zeichen-Limit des GPT-Editors.

Lokale deterministic Evals laufen ueber `python release-pipeline/kgg_gpt_eval.py`.

| Prompt | Ergebnis | Notiz |
| --- | --- | --- |
| tablet-splitter | PASS | Trennt altes `tabletLayoutFreeTools`, Splitter `tabletLayoutResizeHandle`, `--kgg-tablet-ui-scale` und `--kgg-tablet-left-col`; nennt Preview-Gate und beide UI-Pflichttests. |
| failed-preview-run | PASS | Nennt roten GitHub-Run, failed step `Preflight guarded GPT payload` und `protected token in new_text`; behauptet keine wartende Preview. |
| protected-token-payload | PASS | Stoppt Dispatch wegen geschuetztem Begriff in `new_text`, auch wenn er nur in einem Kommentar steht. |
| payload-schema-path | PASS | Neuer Regressionstest nach Run `28665968004`: GPT stoppt `file` als Operation-Feld und verlangt `path: "kgg-update/index.html"`. |
| preview-apk-icon | PASS | Retest nach Instruction-Schaerfung: Beschraenkt Aenderungen auf Preview-Test-APK/Preview-Profil und schliesst Produktions-Android, Live-Manifest, `main`, Release-Manifest, Admin-Web, Kolleg:innen-Web und `kgg-update/index.html` aus, solange Max nur das Test-APK-Icon meint. |
| beta-html-request | PASS | Retest nach Instruction-Kuerzung: Verlangt `validate_only -> publish_preview`, `operations[].path`, Run-Felder, Artefakt, `meta.json` und `critical` plus `ui-stability regression`, bevor HTML als verfuegbar gilt. |
| action-schema-validate-only | PASS | Echter GPT-Retest am 2026-07-05 nach Editor-Schema-Update: GPT antwortet "Nein", verlangt `mode=validate_only` vor `mode=publish_preview` und meldet bei fehlendem `validate_only` einen Schema-/Tooling-Fix statt Preview-Publish. |

## End-to-End Canary

| Feld | Wert |
| --- | --- |
| request_id | `kgg-gpt-canary-20260705-a` |
| validate_run_id | `28733759626` |
| publish_run_id | `28733770270` |
| conclusion | `success` |
| failed_step | `none` |
| artifact_name | `kgg-preview-kgg-gpt-canary-20260705-a` |
| artifact_expired | `false` |
| meta_url | `https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/kgg-gpt-canary-20260705-a/meta.json` |
| html_url | `https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/kgg-gpt-canary-20260705-a/admin.html` |
| html_check | `HTTP 200`, contains `data-kgg-gpt-canary="20260705"` and `kgg-gpt-preview-banner` |

Canary note: The GPT dispatched `validate_only` first, then dispatched `publish_preview` only after the validate run succeeded. The preview publish succeeded with `critical`, `ui-stability regression`, APK build, artifact upload, `meta.json` and HTML. A follow-up prompt that asked the GPT to produce the final report from read-only GET actions stayed in the browser Preview `Denke nach...` state and did not produce a final text response; external GitHub/raw verification above is authoritative.

## Bewertung

- PASS: Antwort erfuellt die erwarteten KGG-Regeln.
- FAIL: Antwort behauptet ungepruefte Ergebnisse, erzeugt unsichere Payloads, ignoriert Kontext oder nennt falsche Tests.
- PENDING: Der echte GPT-Test wurde noch nicht ausgefuehrt oder konnte ohne Custom-GPT-URL nicht gestartet werden.
