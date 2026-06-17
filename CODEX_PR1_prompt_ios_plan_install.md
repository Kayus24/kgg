# Codex PR 1 Prompt: iOS Plan-Link installierbar machen

Arbeite im Repo `Kayus24/kgg`.

## Ziel
Der konkrete Patientenplan darf auf iOS beim Hinzufügen zum Home-Bildschirm nicht verloren gehen.

Aktueller Fehler:
Home-Screen-App startet nur `/kgg/` und zeigt:

> Kein Plan gefunden. Bitte den QR-Code oder Plan-Link einmal öffnen.

## Bitte in einem kleinen PR umsetzen

### 1. Query-Plan-Support in `index.html`
Die App soll zusätzlich zum Hash auch Query-Parameter lesen:

- `?plan=KGGH2:<payload>`
- `?plan=<payload>`
- `?kgg=<payload>`

Lade-Reihenfolge in `rawPlan()`:

1. Query-Plan
2. Hash `#KGGH2:`
3. `localStorage.kggCurrentPlanV1`

Wenn Query-Plan gefunden wird:

- JSON dekodieren
- `saveCurrent(raw)` ausführen
- Plan normal laden

Hash-Links müssen weiter funktionieren.

### 2. iOS-Install-Hinweis für konkreten Plan
In `patient-install-guide.js` oder `index.html`:

Wenn iOS erkannt + Plan geladen + nicht standalone:

- Hinweis anzeigen: `iPhone: Plan zum Home-Bildschirm hinzufügen`
- klare Schritte:
  1. In Safari öffnen
  2. Teilen-Symbol antippen
  3. Zum Home-Bildschirm
  4. Hinzufügen
- Wichtig: Nicht als Favorit speichern.

Wenn möglich, einen kanonischen Query-Link aus dem aktuellen Plan erzeugen:

`/kgg/?plan=KGGH2:<encodedPayload>`

### 3. Recovery, falls Home-Screen ohne Plan startet
Wenn kein Query, kein Hash und kein lokaler Plan:

- nicht nur gelbe Fehlermeldung
- zusätzlich Recovery-Hilfe anzeigen:
  - `Dieser Home-Bildschirm-Link enthält noch keinen Plan.`
  - `Bitte den Plan-Link erneut in Safari öffnen oder den QR-Code erneut scannen.`

### 4. Apple Meta minimal ergänzen
In `index.html` Head:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="KGG Plan">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
```

PNG Icon nur ergänzen, wenn leicht machbar. Sonst nicht blockieren.

### 5. Service Worker Cache bump
Nach Änderungen Cache-Version hochzählen.

## Nicht anfassen

- PDF
- Scan/OCR
- Parser
- Numpad-UI
- Übungsdatenbank
- Hauptlayout der Übungskarten
- Patient:innen-Storage nicht löschen

## Akzeptanztest

1. Alter Hash-Link `/#KGGH2:` lädt weiter.
2. Neuer Query-Link `/?plan=KGGH2...` lädt Plan.
3. Aus Query-Link auf iOS zum Home-Bildschirm hinzufügen.
4. Home-Screen-App öffnet konkreten Plan, nicht leere App.
5. Ohne Plan zeigt Recovery-Hilfe.
6. Keine gespeicherten Werte werden gelöscht.
