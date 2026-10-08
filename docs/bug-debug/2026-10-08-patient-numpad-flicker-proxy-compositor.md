# Patienten-App: kg/Wdh-Flackern beim Feldwechsel – Ursache und Lösung

Datum: 2026-10-08  
Status: RESOLVED  
Betroffener Bereich: KGG Patienten-App, Compact Set View / NumPad / Android Chrome

## Fehlerbild

Auf einem echten Oppo/Android-Chrome trat beim Wechsel zwischen kg und Wdh ein sehr kurzes, aber klar sichtbares Flackern des Hauptbildschirms auf. Das NumPad blieb optisch stehen, während der darunterliegende Dokumentinhalt für ungefähr einen Frame sprang bzw. neu gepaintet wurde.

Einige frühe Fixversuche reduzierten das Problem, beseitigten es aber nicht vollständig.

## Reproduzierbare Kernevidenz

- Physisches Oppo zeigte das Problem zuverlässig beim direkten Feldwechsel.
- Videoanalyse zeigte einen einzelnen falschen Dokumentframe von ungefähr 20–30 ms.
- Der NumPad-Layer blieb dabei stabil; betroffen war der darunterliegende Seiteninhalt.
- CDP-/Paint-Diagnostik konnte die problematischen Root-Paints gezielt nachweisen.
- Reine Desktop-GREEN-Tests waren nicht ausreichend; der physische Oppo-Test blieb das Abnahme-Gate.

## Ursachen

Es waren mehrere Effekte beteiligt:

1. **DOM-Neuaufbau im openPad-Pfad**  
   Beim Feldwechsel wurde unnötig UI neu aufgebaut bzw. paint-relevant verändert.

2. **Asynchroner Media-DOM-Ersatz**  
   Der Media-Renderer ersetzte Bild-/Media-Knoten nachträglich und konnte zusätzliche Paints auslösen.

3. **Paint-relevante Active-State-Markierung**  
   Die aktive kg/Wdh-Markierung wurde ursprünglich direkt über Klassen/Border auf echten Inputs realisiert. Schon diese Änderung konnte wieder einen Full-Document-Paint verursachen.

4. **Native Input-/Focus-/Scroll-Pfade waren für die Compact-UI ungeeignet**  
   Die sichtbare Compact-UI brauchte einen eigenen Touch-Target-Pfad, ohne native Fokus-/Scroll-Nebenwirkungen.

## Endgültige Lösung

Die stabile Lösung war eine Kombination mehrerer Änderungen:

### 1. Draft-State statt DOM-Rebuild

Solange das NumPad offen ist, ist der Draft-State maßgeblich. Beim Wechsel kg ↔ Wdh wird der aktive Zielwert gewechselt, ohne das NumPad zu schließen und ohne den gesamten Pad-/Dokumentzustand neu aufzubauen.

Der Core kann dadurch denselben offenen Pad-Zustand wiederverwenden.

### 2. Compact Tap Proxies

Die echten readonly `input.num` bleiben Daten-/State-Träger, sind im Compact Mode aber nicht mehr das direkte Touch-Ziel.

Stattdessen liegen `.kggCompactTapProxy`-Elemente darüber. Sie:
- repräsentieren das reale Tap-Ziel,
- verweisen auf das zugehörige Backing-Input,
- vermeiden native Fokus-/Scroll-Pfade,
- erlauben direkten Wechsel zwischen kg/Wdh und zwischen Sätzen bei offenem NumPad.

### 3. Compositor-sichere Active-Markierung

Die sichtbare aktive Markierung wird nicht mehr durch paint-relevante Border-Änderungen am echten Input erzeugt.

Stattdessen:
- `.kggCompactSourceRing` markiert das aktive Eingabefeld,
- `.kggPairIndicator` markiert das aktive Feld im NumPad,
- Bewegung/Wechsel erfolgt über compositor-freundliche Eigenschaften wie `transform: translate3d(...)` bzw. Opacity.

Dadurch blieb der Feldwechsel im Trace bei **0 Layout / 0 Paint**.

### 4. Stabiler Media-Renderer

Media-Knoten werden idempotent behandelt und Object URLs wiederverwendet, statt bei jedem Wechsel neue DOM-Knoten einzusetzen.

### 5. Ein interner Scroll-Owner

Die Seite verwendet für den relevanten Patienten-App-Pfad einen klaren internen Main-Scroller. Window-Scroll und konkurrierende Scroll-Owner werden vermieden.

Beim Öffnen des letzten Satzes wird nur der interne Scroller kontrolliert bewegt; kg↔Wdh innerhalb desselben Satzes verursacht keinen neuen Scroll.

## Verifikation

Vor dem Merge wurden unter anderem geprüft:

- kg ↔ Wdh im selben Satz: 0 Layout / 0 Paint
- Wechsel in einen anderen Satz bei offenem NumPad
- kein closePad beim direkten Touch-Wechsel
- 25 kg → 12 Wdh → OK
- letzter Satz mit ausreichendem Abstand zum NumPad
- stabile Media-Nodes
- physischer Oppo-Test

Der Nutzer bestätigte auf dem echten Oppo, dass das Flackern behoben ist.

Produkt-Merge:
- PR #289
- Main-Commit: `e52474373170719e5a146b03c378846d5e0356ec`

## Wichtige Präventionsregel

Bei zukünftigen Compact-UI-Änderungen niemals automatisch davon ausgehen, dass `input.num` das echte Klickziel ist.

Für Compact Mode gilt:
- Interaktion über `.kggCompactTapProxy`
- aktive visuelle Markierung über `.kggCompactSourceRing` / `.kggPairIndicator`
- Tests dürfen nicht wieder auf direkte Input-Klicks oder alte Border-Verträge zurückfallen.

Legacy Mode darf weiterhin mit den echten Inputs arbeiten.

## Follow-up nach dem Merge

Nach PR #289 wurde der restliche Browser-Testbestand systematisch auf alte Annahmen geprüft.

Dabei fand sich noch ein veralteter Test:
`release-pipeline/kgg_patient_compact_transfer_playwright.js`

Er verwendete noch:
- direkte Klicks auf echte Compact-Inputs,
- alte Selektoren wie `#kggPadPair button[data-kgg-key=...]`.

Das war **kein neuer Produktbug**. Es war ein Test-Harness-Drift: Der Test beschrieb die alte UI-Architektur, obwohl die App bereits korrekt auf Proxy-/Compositor-Interaktion umgestellt war.

Follow-up:
- PR #297
- nur Test-Harness-Anpassung
- kein Produkt-Runtime-Code geändert
- Required Gate: GREEN
- Validate/Build: GREEN
- gemergt nach main
- Merge-Commit: `f54a7f8abb27ec8ae2087c8bdb2383944e2e3c22`

## Wiederverwendbar für

Diese Lösung und die Diagnoseprinzipien sind relevant für:
- 1-Frame-Flimmern
- Root-Paints bei UI-State-Wechseln
- mobile readonly Inputs mit eigenen Overlays
- Focus-/Scroll-Jumps in Android Chrome
- Compositor-freundliche Active-State-Indikatoren
- Tests, die nach UI-Architekturänderungen veraltete Klickziele verwenden
