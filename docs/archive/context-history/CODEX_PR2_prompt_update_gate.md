# Codex PR 2 Prompt: Update-Gate sichtbar machen

Arbeite im Repo `Kayus24/kgg`.

## Ziel
Patient:innen sollen nicht minutenlang auf einer alten App-Version hängen.

Aktueller Stand:
`service-worker.js` sendet bereits `APP_UPDATE_READY`, aber die App zeigt keinen klaren Reload-Banner.

## Umsetzung

### Neues Modul
Erstelle `patient-update-gate.js`.

Funktion:

- Hört auf `navigator.serviceWorker.addEventListener('message', ...)`.
- Wenn `event.data.type === 'APP_UPDATE_READY'`:
  - Banner unten/oben anzeigen:
    `Neue Version verfügbar`
    `Bitte jetzt aktualisieren, damit der Plan richtig funktioniert.`
  - Button: `Jetzt aktualisieren`
  - Button macht `location.reload()`.

### Sicherheitsregeln

- Nicht automatisch neu laden, wenn Numpad offen ist.
- Keine Werte löschen.
- Kein `localStorage.clear()`.
- Banner darf Patient:innen nicht blockieren.

### Service Worker

- Modul injizieren.
- Cache-Version hochzählen.

## Nicht anfassen

- PDF
- QR
- Parser
- Scan/OCR
- Numpad-UI
- Übungsdatenbank

## Akzeptanztest

1. Neue Service-Worker-Version wird aktiviert.
2. Banner erscheint.
3. Button aktualisiert die App.
4. Keine Endlosschleife.
5. Eingabewerte bleiben erhalten.
