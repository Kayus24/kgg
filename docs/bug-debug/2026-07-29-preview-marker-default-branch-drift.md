# 2026-07-29 - Preview-Marker und Default-Branch-Drift

## Problem

Die KGG Test-App zeigte erneut einen schwarzen, vollhohen Balken mit kompletter
Preview-Beschreibung. Der Balken verschob die eigentliche App und schnitt
Bedienelemente am linken Rand an, obwohl ein kompakter Marker bereits auf einem
offenen Arbeitsbranch implementiert und getestet war.

## Betroffene Version/Datei

- Preview: `kgg-ocr-camera-wide-preview`
- Run: `30397801575`
- Run-`headSha` und Preview-`baseSha`: `15e39b2e23a7acf65588939fecacfaae971ab514`
- Datei: `release-pipeline/kgg_gpt_write_gate.py`

## Ursache

Der kompakte Marker war nur in PR #110 vorhanden. Der produktive
`workflow_dispatch` lief weiterhin aus dem Default-Branch `main`, dessen
`inject_preview_banner()` noch ein `position:sticky`-Element mit der kompletten
Request-Beschreibung erzeugte. Ein gruener Branch-Test beweist nicht, dass ein
Fix bereits fuer produktive GPT-Actions aktiv ist.

## Loesung/Fix

- Der produktive Marker ist ein kleines, fixed positioniertes Overlay und nimmt
  nicht am App-Layout teil.
- Die eingeklappte Kennung zeigt nur `TEST` plus Hash-Kurzform.
- Details mit Titel, Request-ID und vollem Hash werden nur auf Anforderung
  eingeblendet.
- Das Gate entfernt eigene alte Marker vor jeder Injektion, statt vorhandene
  Marker ungeprueft zu uebernehmen.
- Vor einer Erfolgsmeldung werden Workflow-`headSha`, Preview-`baseSha` und der
  aktuelle Default-Branch miteinander verglichen.

## Test / Abnahmekriterien

- Ein altes Sticky-Banner wird ersetzt und nicht dupliziert.
- Der eingeklappte Marker ist hoechstens 92 x 24 CSS-Pixel gross.
- App-Geometrie und horizontaler Overflow bleiben mit und ohne Marker identisch.
- Menue, Scanner und Dock bleiben bei geschlossenem Marker anklickbar.
- Details oeffnen und schliessen per Toggle, Aussenklick und Escape.
- Viewports: 360 x 800, 390 x 844, 720 x 1280 und 1180 x 820.
- Ein neuer Preview-Run muss auf einem `baseSha` nach dem Marker-Hotfix laufen.

## Nicht anfassen

- Admin- und Kolleg:innen-HTML
- PDF
- QR/Patienten-App
- Scan/OCR
- Parser
- Plan-State
- Medien/Upload
- Android- und Admin-Manifest

## Folge-Risiken

- Ein offener PR darf nie als produktiver Stand beschrieben werden.
- Eine erneute Preview aus einem alten Workflow-Ref kann alte Gate-Logik
  wiederverwenden.
- Sichtbare Request-Beschreibungen duerfen nicht erneut in einen permanenten
  Marker gepackt werden.

## Bereiche

- debug
- phone-layout
- tablet-layout
