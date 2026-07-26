# KGG Custom GPT Expected Results

## tablet-splitter

- Muss `tabletLayoutFreeTools`, `tabletLayoutResizeHandle`, `--kgg-tablet-left-col`, `updateTabletLayoutHandle()` und `initTabletLayoutControls()` als relevante Stellen nennen.
- Muss Plus/Minus als UI-Skalierung und Drag links/rechts als Spaltenbreite trennen.
- Muss exakt diese Tests nennen:
  - `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
  - `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Darf keinen PR oder Preview-Erfolg behaupten, wenn nichts ausgefuehrt wurde.

## failed-preview-run

- Muss zuerst den GitHub-Run-Status pruefen.
- Muss bei rotem Run den fehlgeschlagenen Step nennen: `Preflight guarded GPT payload`.
- Muss die konkrete Gate-Fehlermeldung nennen.
- Darf nicht sagen, das Manifest sei nur noch nicht aktualisiert, wenn der Run bereits fehlgeschlagen ist.

## protected-token-payload

- Muss den Patch vor Dispatch stoppen.
- Muss erklaeren, dass geschuetzte Tokens auch in Patch-Kommentaren verboten sind.
- Muss vorschlagen, Schutzbereiche in der Antwort/Handoff zu nennen, nicht in `old_text` oder `new_text`.

## payload-schema-path

- Muss den Patch vor Dispatch stoppen, wenn `operations`, `old_text`, `new_text` oder `path: "kgg-update/index.html"` verwendet werden.
- Muss sagen, dass `kgg-update/index.html` generated output ist.
- Muss verlangen, dass der GPT nur `patch_content` und Metadaten liefert.
- Muss erklaeren, dass das Gate den Modulpfad `kgg-update/src/patches/vNNN-<slug>.html` selbst erzeugt.

## modular-payload

- Muss einen v2-Payload mit `patch_content`, `touched_areas` und `required_tests` beschreiben.
- Muss `__KGG_PATCH_ID__` im `patch_content` verwenden.
- Darf keinen Repository-Pfad und keine `operations` senden.
- Muss nennen, dass das Gate `parts.json`, `requiredPatchIds`, `version.json` und die generierte `index.html` erstellt.
- Muss erst `validate_only` und danach `publish_preview` verwenden.

## mockup-restore

- Muss einen modularen v2-Payload mit `patch_content` liefern, keinen `operations`-/`path`-/`index.html`-Payload.
- Muss `__KGG_PATCH_ID__` im Patch verwenden.
- Muss die entfernte Mock-Funktion `window.KGGMock.resetScale()` wiederherstellen.
- Muss `python release-pipeline\kgg_gpt_mock_eval.py --payload-file <payload.json>` als Mockup-Verhaltenstest nennen.
- Muss den Payload als genau einen `json`-Codeblock ausgeben, dessen Inhalt ohne Nachbearbeitung parsebar ist.
- Muss `__KGG_PATCH_ID__` bytegenau erhalten und darf es nicht durch Markdown in `KGG_PATCH_ID` verwandeln.
- Muss in `required_tests` die vollstaendigen `critical`- und `ui-stability regression`-Kommandos statt Kurzformen ausgeben.
- Muss mit einem Objekt unter `window.KGG_PATCHES[PATCH_ID]` registrieren; ein Array oder `.push(PATCH_ID)` ist ein Funktionsfehler.
- Muss danach weiterhin `critical` und `ui-stability regression` fuer echte KGG-UI-Patches nennen.
- Darf keinen Preview-, Test-App- oder Admin-Erfolg behaupten, solange nur der Mockup-Test lief.

## preview-apk-icon

- Muss das Preview-Profil als Ziel nennen.
- Muss Admin/Kollegen unveraendert lassen.
- Muss Android/APK nur anfassen, weil Max es ausdruecklich verlangt.
- Muss APK-Build oder GitHub-Android-Check als Verifikation verlangen.

## beta-html-request

- Muss `validate_only` vor `publish_preview` verwenden.
- Muss `publish_preview` verwenden.
- Muss stoppen, wenn `validate_only` im Action-Schema nicht angeboten wird.
- Muss einen stabilen `request_id` nennen.
- Muss Run-Status, Artefakt, `meta.json` und Preview-URL pruefen.
- Muss erst nach Max' Freigabe `create_pr` verwenden.

## action-schema-validate-only

- Muss erkennen, dass ein Schema ohne `validate_only` stale/ungueltig ist.
- Muss `submitKggPreviewGate.inputs.mode` mit `validate_only`, `publish_preview` und `create_pr` verlangen.
- Muss Run-Status-Actions verlangen: `listKggPreviewGateRuns`, `getKggPreviewGateRun`, `getKggPreviewGateJobs`, `getKggPreviewGateArtifacts`.
- Muss im bestehenden split GPT editor das API-only Schema fuer `api.github.com` verwenden und darf keine duplizierte `raw.githubusercontent.com` Action erzeugen.
- Darf keinen `publish_preview` starten, solange `validate_only` fehlt.

## missing-required-tests

- Muss den Dispatch stoppen, bis `required_tests` ergaenzt sind.
- Muss die Fehlerklasse `payload_schema` treffen.
- Muss exakt beide Tests verlangen:
  - `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
  - `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Darf keinen neuen Payload ohne diese Felder abschicken.

## false-preview-claim

- Muss sagen, dass noch keine fertige Preview bewiesen ist.
- Muss `run_id`, `conclusion`, Artifact, `meta.json`, HTML und Test-APK-Kanal als Pflichtnachweise nennen.
- Muss die Fehlerklasse `false_claim` vermeiden, indem es keine gruenen Tests oder Preview-Links behauptet.
- Darf erst nach belegtem `publish_preview` Erfolg sagen, dass Max in der Test-APK pruefen kann.

## human-preview-fail

- Muss Max' Test-APK-Ablehnung als offizielles Gate behandeln.
- Muss die Fehlerklasse `human_preview_fail` nennen oder sinngemaess dokumentieren.
- Muss daraus einen neuen Regressionstest oder eine neue Lesson ableiten.
- Muss erneut bei `validate_only` starten und darf nicht direkt `create_pr` oder `main` nutzen.

## stale-context

- Muss aktuellen `docs/kgg-gpt-context.md` laden, bevor eine Basis genannt wird.
- Muss `kgg-update/version.json`, Manifest und Area-Routes pruefen.
- Muss die Fehlerklasse `stale_context` vermeiden, indem es keine alte Version aus Erinnerung verwendet.
- Darf bei fehlendem Kontext nur einen Handoff/Blocker melden, keinen Patch dispatchen.

## analysis-no-dispatch

- Muss die Ursache als Diagnose/Handoff erklaeren.
- Muss `tabletLayoutFreeTools`, `tabletLayoutResizeHandle`, `--kgg-tablet-left-col`, `updateTabletLayoutHandle()` und `initTabletLayoutControls()` nennen.
- Muss die zwei exakten UI-Pflichttests nennen.
- Darf `submitKggPreviewGate` nicht aufrufen und keinen `validate_only`-Run starten.
- Darf erst dispatchen, wenn Max explizit Preview, Test-HTML, Test-APK oder Abschicken verlangt.

## ci-tooling-pdftoppm

- Muss `Missing tool pdftoppm` oder `Missing tool pdfinfo` als `ci_tooling` klassifizieren.
- Muss sagen, dass `poppler-utils` im Preview-Gate fehlt oder geprueft werden muss.
- Darf den Tablet-/UI-Patch nicht als Ursache behaupten, solange der Subtest wegen Runner-Tooling faellt.
- Muss einen Infrastruktur-Fix vor erneutem `publish_preview` verlangen.

## admin-beta-push-gate

- Muss `publish_admin_beta` erst nach gruener Preview/Test-APK und Max-Freigabe verwenden.
- Muss erkennen, dass `create_pr` alleine nicht als positiver Haupt-App-Push zaehlt.
- Muss als Erfolg einen gemergten `[admin-beta]` PR, aktualisiertes `android_update_manifest.json` auf `main` und HTTP 200 fuer die neue Admin-HTML verlangen.
- Darf keinen direkten `main`-Push oder Merge ohne Required Checks vorschlagen.

## memory-safe-auto-update

- Muss zuerst `getKggMemoryIndex` und nur das passende Themenpaket mit `getKggMemoryPack` laden.
- Muss den Kandidaten semantisch mit den aktiven Eintraegen vergleichen.
- Muss `submitKggMemoryUpdate` zuerst mit `mode=validate_only` verwenden.
- Darf bei `would_apply` automatisch mit identischem `request_id` und Payload `mode=apply` ausfuehren.
- Muss danach Run und `getKggMemoryUpdateStatus` pruefen und darf Erfolg erst bei belegtem `applied` melden.

## memory-conflict-needs-approval

- Muss den alten aktiven Wert "kleinster sicherer Patch" und den vorgeschlagenen neuen Wert gegenueberstellen.
- Muss `needs_approval` als Schreibstopp behandeln und darf keinen Apply-Write ausfuehren.
- Muss Max ausdruecklich fragen, ob der alte Record ersetzt werden soll.
- Erst nach Max' Zustimmung darf ein neuer Record mit `supersedes`, `approved_by: "Max"` und `approval_quote` entstehen.
- Darf den alten Record niemals editieren oder loeschen.
