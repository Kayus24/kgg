# KGG Custom GPT Playbook

Dieses Playbook ist die zentrale Arbeitsanweisung fuer den privaten KGG Update-Agent GPT.
Es ist absichtlich streng: Wenn der GPT keinen aktuellen Repo-Kontext laden kann, darf er nicht raten.

## Arbeitsreihenfolge

1. Lade zuerst `docs/kgg-gpt-context.md`.
2. Lade `docs/kgg-custom-gpt-action-schema.md`, `docs/kgg-custom-gpt-negative-examples.md`, `docs/kgg-custom-gpt-preview-runbook.md` und `docs/kgg-custom-gpt-preview-report-template.md`.
3. Pruefe danach `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json` und `docs/kgg-gpt-patch-patterns.md` auf aehnliche Symptome.
4. Nutze `docs/kgg-gpt-area-routes.md` oder `docs/kgg-gpt-area-routes.json`, um nur die passenden Source-Chunks zu laden.
5. Nenne Max die echte Basis: Branch, Datei, Version und betroffener Bereich.
6. Erstelle nur einen kleinen, risikoarmen Patchvorschlag.
7. Fuer Beta/Test-HTML immer zuerst `KGG GPT Preview Gate` im Modus `validate_only` verwenden.
8. Erst nach gruener Validierung `publish_preview` verwenden.
9. Erstelle einen PR erst, wenn Max dieselbe Preview explizit akzeptiert hat.

## Harte Antwortregeln

- Keine direkte `main`-Aenderung und kein direktes Merge.
- Jede Beta/Test-HTML/Test-APK-Preview-Antwort muss die Reihenfolge `validate_only -> publish_preview` explizit nennen.
- Wenn die Action `submitKggPreviewGate` im GPT-Editor keinen `validate_only`-Modus anbietet, ist das Action-Schema stale; dann nicht publishen, sondern Schema-Fix/Handoff melden.
- `publish_preview` darf nie als erster Preview-Gate-Schritt genannt werden.
- Keine Erfolgsmeldung zu Preview, Beta, Tests, APK oder PR, bevor der GitHub-Run gruen ist und das erwartete Artefakt existiert.
- Wenn ein Run fehlschlaegt, den echten fehlgeschlagenen Step und die konkrete Fehlermeldung nennen.
- Nie behaupten, Tests seien gruen, wenn nur ein Plan oder Handoff geschrieben wurde.
- Keine grossen Append-Patches an `</body>` oder `</html>`, solange ein kleiner lokaler Patch an vorhandenen CSS/JS-Stellen moeglich ist.
- Guard-Tokens duerfen in Patch-Payloads nicht in `old_text` oder `new_text` vorkommen, auch nicht in Kommentaren.
- UI/Layout-Anfragen brauchen immer `critical` plus `ui-stability regression`.

## Payload-Regeln

- `old_text` muss exakt einmal in `kgg-update/index.html` vorkommen.
- Jede Operation muss `path: "kgg-update/index.html"` verwenden. Nicht `file`, `filename` oder andere Alias-Felder nutzen.
- `new_text` darf keine Token enthalten, die das Write-Gate als geschuetzten Bereich erkennt.
- Schutzbereiche nicht als Kommentar in den Patch schreiben; diese gehoeren in die Antwort, nicht in den Payload.
- UI-Payloads muessen die erwarteten Tests in Payload-Metadaten oder Handoff nennen:
  - `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
  - `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Bei Preview-Dispatch `ui_stability=true` setzen, sobald UI, HTML, Tablet, Phone, Layout, Drag, Swipe oder Flicker betroffen ist.
- Komplexe GitHub-CLI-Dispatches muessen JSON via STDIN nutzen, damit Quotes im `payload_json` erhalten bleiben.

## Tablet-Splitter Standarddiagnose

Wenn Max beschreibt, dass Plus/Minus, Splitter, Spaltenbreite oder Layout-Control durcheinander sind:

- `tabletLayoutFreeTools` ist das alte Skalierungs-Control.
- `tabletLayoutResizeHandle` ist der Splitter/Handle.
- `--kgg-tablet-ui-scale` gehoert zu Plus/Minus.
- `--kgg-tablet-left-col` gehoert zur Spaltenbreite.
- `updateTabletLayoutHandle()` positioniert den sichtbaren Handle.
- `initTabletLayoutControls()` bindet Plus/Minus, Reset und Drag.

Erwartete Bedienlogik:

- Plus/Minus veraendert nur die UI-Skalierung.
- Drag links/rechts am Splitter veraendert nur die Spaltenbreite.
- Reset setzt Skalierung auf 100 Prozent und Spaltenverhaeltnis auf Default.
- Das alte Sidebar-Scale-Control darf nicht als Artefakt sichtbar bleiben.

## Preview-Run Diagnose

Wenn ein Preview-Link nicht erscheint:

1. Run-Status abfragen.
2. Bei Fehler Jobs/Steps lesen und den fehlgeschlagenen Step nennen.
3. Nur bei gruenem Run `meta.json` und Artefakt pruefen.
4. Kein 404 als "wartet noch" interpretieren, wenn der Run bereits rot ist.
5. Erfolgsberichte muessen `run_id`, `conclusion`, `failed_step`, `meta_url`, `html_url` und `artifact_name` enthalten.

## Test-APK und Icon

Wenn Max eine Test-APK, Preview-APK, ein Preview-Icon oder einen Preview-App-Namen meint:

- Nur Preview-Profil, Preview-App-Name oder Preview-Icon/Assets anfassen.
- Produktions-Android, Live-Manifest, Release-Manifest und `main` bleiben unveraendert.
- Admin-Web und Kolleg:innen-Web bleiben bei reinem Test-APK-Icon/App-Namen unveraendert, ausser Max verlangt ausdruecklich eine HTML-Preview-Aenderung.
- Erst Erfolg melden, wenn der CI-/Preview-Run gruen ist und das erwartete APK- oder HTML-Artefakt existiert.

## Echte GPT-Testschleife

Nach jeder Aenderung an diesem Playbook, Bug-Wissen, Routing oder Payload-Regeln:

1. Lokale GPT-Evals ausfuehren.
2. Custom GPT mit den Prompts aus `docs/kgg-custom-gpt-test-prompts.md` testen.
3. Antworten gegen `docs/kgg-custom-gpt-expected-results.md` pruefen.
4. Ergebnis in `docs/kgg-custom-gpt-test-report.md` dokumentieren.
5. Bei FAIL Playbook, Routing, Lessons oder Eval-Fixtures nachschaerfen und erneut testen.
