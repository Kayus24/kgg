# Bug-Debug-Log

Zweck: Wiederkehrende KGG-App-Probleme so dokumentieren, dass Codex/GitHub später nicht dieselben Fehler neu suchen muss.

## Standardformat für jeden Eintrag

```md
# YYYY-MM-DD – Kurztitel

## Problem
Was ist sichtbar kaputt?

## Betroffene Version/Datei
- Version:
- Datei(en):

## Reproduktion
1.
2.
3.

## Ursache
Technische Ursache, soweit bekannt.

## Lösung/Fix
Was wurde geändert?

## Test / Abnahmekriterien
- [ ] Handy-Viewport getestet
- [ ] Tablet-Viewport getestet
- [ ] Relevante Funktion getestet
- [ ] Keine Nebenbereiche verändert

## Nicht anfassen
Welche Bereiche dürfen durch diesen Fix nicht verändert werden?

## Folge-Risiken
Was könnte später wieder brechen?
```

---

# Bekannte Themen / Startindex

## Patient-App iOS/PWA startet leere Basis-App

### Problem
Home-Screen-Installation oder Favoriten öffnen teilweise nur die leere Basis-App. Konkreter Patient:innenplan kann beim Start fehlen oder alte Versionen werden zuerst geöffnet.

### Status
Als GitHub-Issue dokumentiert. Gehört primär zur Patient:innen-App, ist aber relevant für QR-/Übergabe-Flow.

### Nicht anfassen
Therapeuten-App-Layout, PDF, Parser und Scan nur ändern, wenn explizit nötig.

---

## v389 Textfeld-Jitter-Diagnostik

### Problem
Textfeld-/Render-Jitter musste isoliert messbar gemacht werden.

### Bekannte Datei
- `therapist-app/test-lab/textfield-jitter/KGG_APP_KOLLEGEN_v389_textfield_jitter_INSTRUMENTED.html`

### Bekannte Lösung
Diagnose-Frame-Pfad korrigiert und geladenen App-Pfad im Diagnose-JSON mitgeführt.

### Nicht anfassen
Haupt-App bleibt im Diagnose-Test möglichst unverändert.

---

## Tablet/Handy Layout-Grenze 759/760 px

### Problem
Handy-UI und Tablet-UI dürfen nicht gleichzeitig aktiv sein. Handy: `max-width:759px`. Tablet: `min-width:760px`.

### Testregel
Nicht mit Browser-Zoom testen, sondern mit echten Viewports:
- Handy z. B. 390 × 844 oder 400 × 844
- Tablet z. B. 820 × 1180

### Akzeptanz
- Handy: `innerWidth <= 759`, `max-width` true, `min-width` false.
- Tablet: `innerWidth >= 760`, `min-width` true.
- Handy darf keine Tablet-Weitergabe-/API-Key-Blöcke im normalen Flow zeigen.

### Nicht anfassen
Tablet-Funktionen nicht durch Handy-Cleanup zerstören.

---

## Drag-Drop / Reorder-Hitbox

### Problem
Verschieben von Übungskarten kann je nach Layout/Viewport anders reagieren. Tablet und Handy getrennt testen.

### Bekannte Richtung
Reorder-Handle-Hitbox und Touch-Action-Regeln gezielt prüfen. Keine globale Touch-Regel setzen, die Swipe/Delete oder Scroll kaputt macht.

### Testregel
- Nach oben/unten verschieben testen.
- Links/rechts Swipe/Delete-Animation separat testen.
- Handy und Tablet getrennt prüfen.

### Nicht anfassen
Keine Layout-Änderungen nebenbei.

---

## Debug JSON Seite

### Problem
Bei PWA-/Storage-/Service-Worker-Problemen braucht es eine einfache Diagnoseausgabe.

### Bekannte Datei
- `debug.html`

### Zweck
Liefert JSON zu URL, Hash, localStorage, Service Worker, Cache und Display-Mode.

### Sicherheitsregel
Patient:innen dürfen JSON/Base64 nie als normale Ausgabe sehen. Debug-Seiten sind intern.

---

# Arbeitsregel

Für jeden neuen Bugfix bitte zuerst entscheiden:

1. Mini-Patch?
2. Codex-Ticket?
3. UI-Flow?
4. Source-of-Truth-Entscheidung?

Danach erst patchen. Pro Patch nur eine Sache ändern.
