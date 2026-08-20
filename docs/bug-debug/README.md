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

## Custom-GPT-Workflow-Hindernis (gleicher Bug-Debug-Log, kein zweites System)

Jede manuelle Wiederaufnahme oder erneute Aufforderung wird in **diesem** Ordner
erfasst, wenn ein KGG Custom GPT nach einem abgeschlossenen, leeren,
abgebrochenen oder zeitlimitierten Antwortzug nicht selbst weiterpollen oder
weiterarbeiten kann. Dasselbe gilt fuer Editor-/Knowledge-/Action-Drift, wenn
sie einen sicheren Ablauf blockiert. Kein separates Chat-Protokoll, kein
zweites Incident-System und keine Patientendaten anlegen.

Der Eintrag verwendet weiter das Standardformat und enthaelt zusaetzlich diese
strukturierten Felder:

- `Zeit`: RFC3339-UTC-Zeitpunkt der Beobachtung oder Reaktivierung.
- `GPT`: exakter Profilname, bei Bedarf GPT-ID ohne Secrets.
- `Auftrag/Ziel`: begrenzter Auftrag oder `request_id`.
- `Vorheriger sichtbarer Zustand/Run-ID`: z. B. `empty_response`,
  `aborted_response`, `answer_timeout`, `response_turn_ended`,
  `action_window_ended`, `editor_drift`, `action_drift`, `stale_context` oder
  `manual_reactivation`, plus Run-ID/Editor-Pruefung sofern vorhanden.
- `Beleg`: nicht sensible Run-/Artifact-Antwort, Resource-Audit oder sichtbare
  Editor-Pruefung; keine erinnerte Chat-Aussage.
- `monitoring_ambiguous` oder `model_ui_ambiguous`: sichtbare UI-Signale sind
  widerspruechlich und duerfen nicht als automatischer Fortschritts- oder
  Modellnachweis behandelt werden.
- `Auswirkung`: was dadurch nicht automatisch weiterlief oder sicher nicht
  ausgefuehrt werden durfte.
- `Reaktivierungsaktion`: der tatsaechliche begrenzte neue Auftrag oder
  Read-Schritt; niemals ein verdeckter neuer Preview-/Main-Dispatch.
- `Ergebnis`: belegtes Ergebnis der Wiederaufnahme, auch wenn es nur ein
  weiter bestehender Blocker ist.
- `Folgeaktion`: kleinster sichere naechste Schritt.

Der Custom GPT liefert diese neun Werte als kompakten Handoff. Codex legt den
Eintrag ab. Nur eine wiederkehrende oder dauerhaft relevante Regel wird danach
ueber das bestehende KGG Project Memory Gate kuratiert; normale einzelne
Laufzeitereignisse bleiben im Bug-Debug-Log. Ein Ereignis aendert niemals
automatisch GPT-Instructions, Knowledge, Actions, Tests oder Project-Memory-
Regeln: erst dokumentieren, dann spaeter gezielt pruefen, aendern und testen.

Für jeden neuen Bugfix bitte zuerst entscheiden:

1. Mini-Patch?
2. Codex-Ticket?
3. UI-Flow?
4. Source-of-Truth-Entscheidung?

Danach erst patchen. Pro Patch nur eine Sache ändern.
