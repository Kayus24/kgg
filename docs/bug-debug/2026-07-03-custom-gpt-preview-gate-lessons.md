# Custom GPT Preview-Gate Lessons

## Problem

Der Custom GPT kann bei Preview-/Beta-Anfragen plausibel antworten, obwohl der GitHub-Run bereits fehlgeschlagen ist.
Ein konkreter Fehler war: Die Antwort deutete einen fehlenden Preview-Manifest-Eintrag als "noch nicht veroeffentlicht", obwohl `Apply guarded GPT payload` rot war.

## Ursache

Das Write-Gate blockt geschuetzte Tokens auch dann, wenn sie nur in einem Patch-Kommentar innerhalb `new_text` stehen.
Ein weiterer Fehler ist, Run-Status, fehlgeschlagenen Step und Artefakte nicht in dieser Reihenfolge zu pruefen.

## Loesung

Der GPT muss vor jeder Erfolgsaussage den GitHub-Run lesen.
Bei rotem Run muss er den fehlgeschlagenen Step und die konkrete Gate-Meldung nennen.
Schutzbereich-Hinweise gehoeren in Antwort oder PR-Handoff, nicht in Patch-`old_text` oder Patch-`new_text`.

## Nicht anfassen

- App-Feature-Code
- PDF
- QR/Patienten-App
- Scan/OCR
- Parser
- Plan-State
- Medien/Upload
- Android/APK, ausser Max fragt explizit danach

## Test / Abnahmekriterien

- Payload mit geschuetztem Token im Patch-Kommentar wird im Preflight geblockt.
- GPT-Eval `failed-preview-run` verlangt den echten roten Step.
- GPT-Eval `protected-token-payload` verlangt Stop vor Dispatch.

## Bereiche

- debug
- tablet-layout
- sync

---

## Problem

Beim Tablet-Layout vermischt der GPT leicht zwei Bedienkonzepte:
das alte Scale-Control im Sidebar-Kontext und den echten Spalten-Splitter zwischen Uebungsdatenbank und Planbereich.

## Ursache

`tabletLayoutFreeTools` ist das alte Skalierungs-Control.
`tabletLayoutResizeHandle` ist der Splitter/Handle.
Der sichtbare Griff kann durch CSS-Schichten und `updateTabletLayoutHandle()` falsch verankert wirken.

## Loesung

Der GPT muss diese Logik getrennt halten:
Plus/Minus veraendert `--kgg-tablet-ui-scale`.
Drag links/rechts veraendert `--kgg-tablet-left-col`.
Der sichtbare Splitter gehoert an die Trennkante zwischen Uebungsdatenbank und Uebungen im Plan.

## Nicht anfassen

- PDF
- QR/Patienten-App
- Scan/OCR
- Parser
- Plan-State
- Medien/Upload
- Android/APK
- GitHub Manifest
- Handy-Layout

## Test / Abnahmekriterien

- UI-Stability-Probe `tablet-splitter-scale-drag` prueft die konkrete Bedienlogik.
- GPT-Eval `tablet-splitter` muss die richtigen Klassen, Variablen und Funktionen nennen.
- UI/Layout-Patches muessen `critical` plus `ui-stability regression` verlangen.

## Bereiche

- tablet-layout
- drag-reorder
