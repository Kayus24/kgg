# Codex Ticket: iOS Large-UI Numpad Zoom greift nicht

## Beobachtung
Auf dem iPhone einer Patientin/Kollegin mit sehr großer UI sieht das Numpad weiterhin alt aus:

- oben steht noch `kg eingegeben`
- großes Pad-Wertfeld ist noch sichtbar
- kein Active-Input-Zoom über dem Zahlenblock
- `Vorwert übernehmen` bleibt unten unter der Zahlenkolonne bzw. im alten Layout

Das zeigt: `patient-numpad-visibility-fix.js` v5 ist zwar im Repo, aber die Large-UI-Erkennung springt auf diesem iPhone nicht an oder die neue Datei wird nicht zuverlässig geladen.

## Ziel
Nur bei großer UI / iOS / wenig sichtbarer Höhe:

- Haupt-UI nicht verändern.
- echtes Eingabefeld bleibt im Plan.
- eine visuelle Zoom-Kopie des aktiven Eingabefeldes entsteht aus dem echten Feld.
- Zoom-Kopie sitzt direkt über dem unten angedockten Ziffernblock.
- altes extra Pad-Wertfeld (`.padVal`) und `padTitle` werden in diesem Modus ausgeblendet.
- `Vorwert übernehmen` steht über der Zahlenkolonne.
- bei normaler UI bleibt das aktuelle Verhalten unverändert.

## Large-UI-Erkennung robuster machen
Aktuell ist die Erkennung vermutlich zu streng.

Empfohlene Bedingung:

```js
function isiOS(){
  const ua = navigator.userAgent || '';
  return /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}

function largeUi(){
  const b = box();
  if(!b || !open()) return false;
  const vv = window.visualViewport;
  const vh = vv ? vv.height : window.innerHeight;
  const r = b.getBoundingClientRect();
  const fs = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
  return fs >= 18 ||
    vh < 690 ||
    r.height > vh * 0.68 ||
    r.top < vh * 0.54 ||
    (isiOS() && (vh < 820 || r.top < vh * 0.62 || r.height > vh * 0.46));
}
```

## Dateien
- `patient-numpad-visibility-fix.js`
- danach `service-worker.js` Cache-Bump

## Nicht anfassen
- Haupt-UI
- Übungskarten-Renderer
- PDF
- QR
- Scan/OCR
- Parser
- Storage
- Übungsdatenbank

## Akzeptanztest
1. Auf normalem Handy bleibt Numpad wie bisher.
2. Auf iPhone mit großer Anzeige:
   - `kg eingegeben` ist weg.
   - großes extra Pad-Wertfeld ist weg.
   - aktive Feld-Kopie erscheint über dem Zahlenblock.
   - Ziffernblock startet unten.
   - `Vorwert übernehmen` steht direkt über den Zahlen.
3. Tap außerhalb schließt weiterhin.
4. Wechsel auf anderes Eingabefeld speichert/übernimmt vorherigen Wert korrekt.
