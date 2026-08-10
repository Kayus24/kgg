# KGG Patient GPT Knowledge: Architecture

Generated retrieval pack. Source digest: `5d713c2d71fd686d`.

Live GitHub context and source files override this static Knowledge pack.

---

# Source: docs/kgg-patient-gpt-context.md

# KGG Patient GPT Live Context

Authoritative live repository context for the private KGG Patienten-App Update-Agent.
Reload before every diagnosis involving current code and before every Preview, PR or live request.

## Repository

- Repository: `https://github.com/Kayus24/kgg`, branch `main`.
- Live patient app: `https://kayus24.github.io/kgg/`.
- Current patient PWA version from `service-worker.js`: `v73`.
- Recovery: `https://kayus24.github.io/kgg/update-recovery.html`.
- Isolated preview host: `https://kayus24.github.io/kgg-patient-preview/`.
- Pre-authorized Patient Preview workflow: `.github/workflows/kgg-patient-gpt-preview-only.yml`.
- Consequential Patient PR/live workflow: `.github/workflows/kgg-patient-gpt-preview-gate.yml`.
- Guard implementation: `release-pipeline/kgg_patient_gpt_write_gate.py`.
- Private project memory: `Kayus24/kgg-project-memory`.
- Private cross-agent coordination: `coordination/index.json` and guarded append-only threads.

## Patient Source Files

- `APP_BOUNDARIES.md`
- `index.html`
- `service-worker.js`
- `update-recovery.html`
- `manifest.json`
- `collapse-cards.js`
- `numpad-ui-fix.js`
- `manifest-v64.webmanifest`
- `patient-card-progress.js`
- `patient-card-settings.js`
- `patient-day-history.js`
- `patient-extra-info-display.js`
- `patient-install-guide.js`
- `patient-install-prompt.js`
- `patient-ios-large-pad-force.js`
- `patient-last-value-hints.js`
- `patient-media-retry-cache_v2.js`
- `patient-multiplan-db.js`
- `patient-numpad-card-guard.js`
- `patient-numpad-visibility-fix.js`
- `patient-plan-delete.js`
- `patient-plan-replace-slot-fix.js`
- `patient-qr-fullscreen.js`
- `patient-set-summary-groups.js`
- `patient-start-scan.js`
- `patient-start-values-day1.js`
- `patient-ui-micro-polish.js`
- `patient-version-label.js`

## Hard Rules

- Work in German, make one smallest safe patch and preserve existing hooks.
- Never write directly to `main`; use exact Preview hash, PR and protected live approval.
- Reads, validate_only, publish_preview, evidence checks and safe coordination responses are pre-authorized; do not ask after every step.
- Patient PR/live requires Max' exact phrase `Gut für PAT live`.
- Patient output never exposes raw JSON, Base64, KGGH2/KGGD1 or debug payloads.
- Preview fixtures are synthetic and contain no patient data.
- Version, cache name, Recovery release, version label and changelog are owned by the gate.
- QR/hash/storage changes use `risk_class=interface` and stay backward compatible.
- Breaking interface changes, therapist app, PDF and Android/APK stay outside this agent.
- A Custom GPT supplies the Preview URL but does not claim to control the Codex in-app browser.

## Required Evidence

- `validate_only` before `publish_preview` with identical payload.
- Successful workflow run, jobs, artifact, meta.json, Preview URL and Recovery URL.
- Preview index contains the canonical patient modules exactly once and passes the first-load smoke without a service-worker controller or reload.
- Max accepts the Preview in the in-app browser before PR or live mode.
- Live mode additionally needs Required Checks, patient-live Environment approval, merge and live version verification.

---

# Source: APP_BOUNDARIES.md

# KGG App Boundaries

Diese Datei ist eine Sicherheits- und Orientierungsdatei fuer Max, Codex und spaetere Agenten.

Sie dokumentiert die Grenze zwischen Patienten-App und Therapeuten-App. Sie ist absichtlich nur Dokumentation und veraendert kein Laufzeitverhalten.

## Grundregel

Die KGG-Patienten-App und die KGG-Therapeuten-App duerfen funktional zusammenarbeiten, sollen aber gedanklich und bei Patches klar getrennt bleiben.

Gemeinsame Schnittstelle ist nur das stabile Plan-/QR-/Rueckgabe-QR-Datenformat.

## Patienten-App

### Zielgruppe

Patient:innen.

### Zweck

Die Patienten-App zeigt einen bereits erstellten Trainingsplan an, speichert Trainingswerte lokal und erzeugt Rueckgabe-Daten fuer Therapeut:innen.

### Typische Aufgaben

- Plan per QR-/Hash-Link oeffnen.
- Uebungen anzeigen.
- Trainingswerte pro Tag eintragen.
- Schmerz 0-10 dokumentieren.
- Werte lokal/offline speichern.
- Rueckgabe-QR fuer Therapeut:innen erzeugen.
- Auf dem Handy als PWA / Startbildschirm-App laufen.

### Typische Dateien in diesem Repo

- `index.html` - Patienten-Handy-App / Live-Einstieg.
- `manifest.json` - PWA-Manifest.
- `service-worker.js` - Offline-Cache und Modul-Ladeverhalten.
- `icon.svg` - App-Icon.
- `patient-*.js` - Patienten-App-Zusatzmodule.
- `collapse-cards.js` - UI-Zusatzverhalten fuer Patienten-App.

### Darf die Patienten-App nicht tun

- Keine Patientenverwaltung.
- Keine Diagnosen oder Verordnungsdaten im normalen QR-Link.
- Keine PDF-Erzeugung fuer Therapeut:innen.
- Keine Admin-/Therapeuten-UI anzeigen.
- Kein JSON/Base64 als normale Patient:innen-Ausgabe anzeigen.
- Keine API-Keys oder geheimen Daten enthalten.

## Therapeuten-App

### Zielgruppe

Therapeut:innen / Kolleg:innen.

### Zweck

Die Therapeuten-App erstellt und bearbeitet KGG-Plaene, nutzt Parser/Scanner/Uebungsbank, erzeugt PDF/QR und kann Rueckgabe-Daten aus der Patienten-App einlesen.

### Typische Aufgaben

- Trainingsplan erstellen und bearbeiten.
- Uebungen aus Datenbank/Bank/Textfeld uebernehmen.
- Textfeld-Parser verwenden.
- Plan-State pflegen.
- PDF erzeugen.
- QR/Patientenlink erzeugen.
- Rueckgabe-QR scannen/importieren.
- Android/APK/WebView-Variante bereitstellen.

### Typische Dateien ausserhalb oder neben diesem Patienten-Repo

- Admin-/Therapeuten-HTML.
- Kolleg:innen-HTML.
- Android WebView / APK-Projektdateien.
- Scanner-Modul.
- PDF-Modul.
- Textfeld-Parser.
- Uebungsbank.
- Export-/Import-Core.
- QR-Core.

### Darf die Therapeuten-App nicht nebenbei tun

- Patienten-App-Service-Worker ohne klaren Auftrag aendern.
- Patienten-App-Offline-Cache nebenbei aendern.
- QR-Datenformat ohne Source-of-Truth-Entscheidung aendern.
- Patient:innen-Ausgabe mit JSON/Base64 verwechseln.
- Layout der Patienten-App nebenbei umbauen.

## Gemeinsame Schnittstelle

Diese Bereiche muessen stabil bleiben:

- Plan-State.
- QR-/Hash-Link-Format.
- Rueckgabe-QR-Format.
- Lokale Speicherlogik der Patienten-App.
- Bedeutungen von Uebungen, Saetzen, Seiten, Gewicht, Wiederholungen und Schmerzskala.

Aenderungen an dieser Schnittstelle brauchen ausdrueckliche Freigabe von Max.

## Risiko-Kategorien fuer Patches

### Sicher anfassen

- Neue Dokumentationsdateien.
- README-Ergaenzungen ohne Aenderung technischer Aussagen.
- Repo-Map / Moduluebersicht.
- Changelog / Patch-Log.
- Kommentare in separaten Doku-Dateien.

### Nur mit Max-Freigabe anfassen

- `service-worker.js`.
- `index.html`.
- `patient-*.js`.
- `collapse-cards.js`.
- QR-/Hash-Parsing.
- Rueckgabe-QR.
- LocalStorage-Keys.
- PWA-Installationslogik.
- Offline-Cache.

### Niemals nebenbei anfassen

- QR-Datenformat.
- Patienten-Ausgabe-Regeln.
- PDF/QR/Parser/Scan-Logik.
- API-Key-Handling.
- Android/APK-Build-Konfiguration.
- Layout oder UI-Flow, wenn der Auftrag nicht genau dazu passt.

## Codex-Regel

Vor jedem Patch muss Codex zuerst einordnen:

1. Patienten-App?
2. Therapeuten-App?
3. Gemeinsame Schnittstelle?
4. Reine Dokumentation?
5. Source-of-Truth-Entscheidung noetig?

Wenn die Antwort unklar ist, darf Codex keinen Code-Patch machen.

## Aktuelle Arbeitsregel

Dieses Repo dient aktuell vor allem der Patienten-App/PWA-Bereitstellung.

Die Therapeuten-App darf hier nur dokumentiert oder angebunden werden, solange Max nicht ausdruecklich einen Code-Patch fuer diesen Bereich freigibt.
