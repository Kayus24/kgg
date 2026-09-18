# Codex Ticket: iOS Home-Screen-App verliert konkreten Patientenplan

## Beobachtung
Wenn ein iOS-User die KGG-Web-App zum Home-Bildschirm hinzufügen will und danach öffnet, erscheint:

> Kein Plan gefunden. Bitte den QR-Code oder Plan-Link einmal öffnen.

Das bedeutet: Die Home-Screen-App startet nur die Basis-App `/kgg/`, aber nicht den konkreten Plan aus dem QR-/Hash-Link.

## Technische Ursache / Vermutung

Aktueller Stand:

- `manifest.json` nutzt `start_url: "./"`.
- Der konkrete Plan hängt aktuell im URL-Hash `#KGGH2:...`.
- Die App lädt einen Plan nur aus:
  1. URL-Hash `KGGH2:...`
  2. `localStorage` Key `kggCurrentPlanV1`

Problem:

- Beim Hinzufügen zum Home-Bildschirm wird auf iOS offenbar nicht zuverlässig der konkrete Hash-Link als Startpunkt gespeichert.
- Stattdessen startet die PWA/Favorit-App auf `/kgg/`.
- In diesem Home-Screen-Kontext ist `localStorage` offenbar leer oder nicht identisch zum vorherigen Safari-Kontext.
- Ergebnis: kein Hash + kein gespeicherter Plan = „Kein Plan gefunden“.

## Wichtig
Das ist kein Bedienfehler der Patient:innen. Die App muss den konkreten Plan installierbar machen oder beim ersten Start aus Home Screen wiederherstellen können.

## Lösungsvorschläge

### Lösung A: QR-/Planlink nicht nur im Hash, sondern auch als Query unterstützen
Aktuell:

```text
/kgg/#KGGH2:...
```

Zusätzlich unterstützen:

```text
/kgg/?plan=KGGH2...
```

oder:

```text
/kgg/?kgg=...
```

Vorteil:
- Query-Parameter werden von iOS/Home-Screen eher als Teil der Start-URL bewahrt als Hash.
- App kann `parseQueryPlan()` vor `parseHash()` prüfen.

Akzeptanz:
- QR-Link mit `?plan=` öffnen.
- Zum Home-Bildschirm hinzufügen.
- Home-Screen-App startet direkt mit Plan.

Risiko:
- Lange URLs bleiben lang, aber nicht schlimmer als Hash.

### Lösung B: Installationsmodus mit kanonischem Plan-Startlink
Wenn Plan geladen ist, zeigt App einen Button:

> Für iPhone installieren

Dieser Button öffnet eine kanonische URL:

```text
/kgg/?installPlan=<encodedPlan>
```

Dann Anleitung: Safari Teilen → Zum Home-Bildschirm.

Vorteil:
- Patient:innen installieren nicht versehentlich `/kgg/`, sondern den konkreten Plan.
- Klarer Flow für iOS.

### Lösung C: Home-Screen-Recovery-Screen
Wenn kein Plan gefunden wurde und iOS/standalone erkannt wird:

- Nicht nur Fehlermeldung zeigen.
- Stattdessen Recovery-Karte:
  - „Dieser Home-Bildschirm-Link enthält noch keinen Plan.“
  - Button „Plan erneut scannen/öffnen“
  - Button „Safari-Anleitung anzeigen“
  - optional „Zuletzt gespeicherten Plan suchen“

Vorteil:
- Patient:innen hängen nicht fest.

### Lösung D: Plan beim ersten Öffnen in IndexedDB + localStorage doppelt speichern
Beim Laden eines QR-Plans:

- `localStorage.kggCurrentPlanV1`
- zusätzlich IndexedDB `kgg_patient_plan_store`
- zusätzlich `sessionStorage` optional

Beim Start:

1. Query prüfen
2. Hash prüfen
3. localStorage prüfen
4. IndexedDB prüfen

Vorteil:
- robuster gegen iOS Storage-Zickigkeiten.

Risiko:
- Home-Screen-Kontext kann trotzdem getrennt sein. Daher nicht allein ausreichend.

### Lösung E: Manifest/Apple Meta verbessern
In `index.html` ergänzen:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="KGG Plan">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
```

Zusätzlich PNG Icon 180x180 bereitstellen.

Vorteil:
- iOS erkennt App sauberer.

Aber:
- Löst allein nicht, dass der konkrete Plan verloren geht.

## Empfohlene Patch-Reihenfolge

1. Query-Plan-Support einbauen: `?plan=` oder `?kgg=`.
2. QR-/Patientenlink künftig auf Query-Link umstellen oder parallel anbieten.
3. iOS-Installationsbutton im geladenen Plan: „iPhone installieren“ öffnet kanonischen Query-Link.
4. Recovery-Screen für Home-Screen ohne Plan.
5. Apple Meta + PNG Icon ergänzen.
6. Danach Tages-Auto-Advance und Auto-Extend separat patchen.

## Nicht anfassen

- PDF-Layout
- Parser
- Scan/OCR
- Übungsdatenbank
- Numpad
- Haupt-UI-Layout

## Akzeptanztest

1. Plan über Query-Link öffnen.
2. Plan wird angezeigt.
3. iOS Safari: Zum Home-Bildschirm hinzufügen.
4. Home-Screen-Icon öffnen.
5. Derselbe Plan erscheint sofort, keine Meldung „Kein Plan gefunden“.
6. Ohne Plan zeigt Home-Screen-App Recovery-Anleitung statt nur Fehler.
