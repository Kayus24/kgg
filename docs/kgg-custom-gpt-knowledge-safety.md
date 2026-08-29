# Kgg Gpt Safety

Generated production knowledge for protected areas, regression history and safe patch patterns.

Source digest: `c6b736604365cbda`

## Usage Rules

- Reload this pack before KGG patch, Preview/Test-APK, Admin-Beta or run-diagnosis work.
- If this pack conflicts with live GitHub files, trust the live source files and report stale knowledge.
- Read current cycle and run status from GitHub Actions, not from this static pack.
- Do not claim Preview, Test-APK or Admin-Beta success without run/artifact/HTTP evidence.
- Treat `ci_tooling` separately from app patch failures.
- Positive E2E push-test means both `publish_preview` and `publish_admin_beta` succeeded.

## Source Files

- `docs/kgg-custom-gpt-negative-examples.md`
- `docs/kgg-gpt-bug-lessons.md`
- `docs/kgg-gpt-patch-patterns.md`

---

# Source: docs/kgg-custom-gpt-negative-examples.md

# KGG Custom GPT Negative Examples

## JSON als normaler Markdown-Text

Falsch:

```text
{ "patch_content": "<script>var id=\"__KGG_PATCH_ID__\";</script>" }
```

Ausserhalb eines `json`-Codeblocks kann Markdown `__KGG_PATCH_ID__` als Hervorhebung interpretieren und die Unterstriche verlieren. Ein sichtbarer JSON-aehnlicher Text ist zudem kein Nachweis fuer parsebares JSON.

Richtig ist genau ein `json`-Codeblock mit gueltigem JSON, dem bytegenauen Platzhalter und vollstaendigen Testkommandos.

## Patch-ID als Array registriert

Falsch:

```js
window.KGG_PATCHES = window.KGG_PATCHES || [];
window.KGG_PATCHES.push(PATCH_ID);
```

Das verletzt den KGG-Patchvertrag. Richtig ist ein Objekt-Eintrag unter `window.KGG_PATCHES[PATCH_ID]`, damit Gate und Verhaltenstests die Installation eindeutig nachweisen koennen.

## Alter index.html-Payload

```json
{
  "request_id": "tablet-splitter",
  "operations": [
    {
      "path": "kgg-update/index.html",
      "old_text": "...",
      "new_text": "..."
    }
  ]
}
```

Reject: `operations`, `old_text`, `new_text` und `path` sind v1. `kgg-update/index.html` ist generated output. Nutze `patch_content`.

## Alias-Feld file

```json
{
  "request_id": "tablet-splitter",
  "file": "kgg-update/index.html",
  "patch_content": "..."
}
```

Reject: Der GPT darf keinen Datei- oder Repository-Pfad bestimmen. Das Gate erzeugt `kgg-update/src/patches/vNNN-<slug>.html`.

## Geschuetztes Wort im Kommentar

```json
{
  "patch_content": "<script id=\"__KGG_PATCH_ID__\">/* keine API-Key Aenderung */</script>"
}
```

Reject: Guard-Tokens sind auch in Kommentaren verboten. Schutzbereiche in der Antwort beschreiben, nicht im Patch.

## Komplette HTML statt Fragment

```json
{
  "patch_content": "<!doctype html><html><body>...</body></html>"
}
```

Reject: `patch_content` ist nur ein Modulfragment. Das Gate baut die End-HTML.

## Manuelle Versionierung

```json
{
  "patch_content": "<script>const VERSION='KGG_GITHUB_UPDATE_v999_bad';</script>"
}
```

Reject: Version, Build-Info, Changelog und Source-Truth gehoeren dem Gate.

## Brain-Relay-Worker ohne Lead

Falsch: Eine Entwicklungsaufgabe direkt an einen Worker oder an mehrere Lead-
GPTs verteilen, den Relay als Loeser verwenden oder Anforderungen beim
Komprimieren neu formulieren.

Richtig: Genau einen Admin-Lead aus der Task Capsule verwenden, optional bis zu
vier getrennte Unter-Chats synthetisieren lassen und den festen Manager-Lead-
Synthesis-Relay-Worker-Relay-Lead-CI-Weg einhalten. Nur Status-Reads duerfen
GPT ueberspringen; Requirements-Hash und Revision bleiben gleich.

## Brain-Relay-Worker-Limits

Falsch: Fuenf Unter-Chats, vier Implementierungs-Worker mit ueberlappenden
Scopes, rekursive Worker oder mehr als zwei Luna-Retries starten.

Richtig: Hoechstens vier Unter-Chats, drei Luna-Max-Worker plus einen
Verifier, disjunkte Scopes und zwei substantiell unterschiedliche Versuche.
Danach folgt Lead-Review; `NEEDS_SOL` braucht Cricket.

## Sol als Schein-Loeser

Falsch: Sol aus `SLEEPING` wecken, Code/Debug/Test/Repair oder
Repo-Grossanalyse ausfuehren lassen oder unsichtbare Sol-Agenten ohne eine
einmalige Cricket-Eskalation behaupten.

Richtig: Sol bleibt Endboss fuer eine sichtbare, einmalige Entscheidung.
Cricket dokumentiert L0-L3 und unterscheidet technisches Enforcement,
Policy-only und Proxy. Hidden CoT, unsichtbare Agenten, exakte Token-/Credit-
Werte und nicht vorhandene Stop-Funktionen werden nicht als kontrollierbar
ausgegeben.

## Fehlende Tests

```json
{
  "request_id": "tablet-splitter",
  "title": "Tablet Splitter",
  "summary": "Layout",
  "version_slug": "tablet-splitter",
  "touched_areas": ["Tablet-Layout"],
  "required_tests": [],
  "patch_content": "<script id=\"__KGG_PATCH_ID__\"></script>"
}
```

Reject: UI-Payload braucht `critical` plus `ui-stability regression`.

## Roter Run plus meta 404

Wenn der GitHub-Run rot ist und `meta.json` 404 liefert, ist das kein “wartet noch”.
Erst failed step und Log melden, dann keinen Preview-Erfolg behaupten.

## Test-App-Fail

Wenn Max in der Test-App sagt “sieht falsch aus”, ist das `human_preview_fail`.
Kein PR, kein Admin-Beta, kein Main. Lesson/Regression ergaenzen und wieder `validate_only`.

---

# Source: docs/kgg-gpt-bug-lessons.md

# KGG GPT Bug Lessons

Generated from the KGG bug/debug history. Load this before proposing or dispatching a patch.

## Always Apply

- Search this file and `kgg-gpt-bug-index.json` for similar symptoms before patching.
- Reuse the matching `do_not_touch` rules and add the matching tests to the PR plan.
- If a proposed patch resembles a forbidden pattern, stop and route to Codex.
- Keep patient-facing flows free of raw JSON, Base64 and debug output.

## Known Lessons

### 2026-06-18 Phone-Gesten-Fix + mini07 Identitaets-Fix + Auto-Update-Handoff

- Source: `docs/bug-debug/2026-06-18-phone-gesture-identity-autoupdate.md`
- Areas: debug, drag-reorder, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, sync, tablet-layout
- Lesson: Im Handy-Layout waren die Gesten der Uebungskarten im aktuellen Plan fehlerhaft: - Swipe links/rechts lief nicht sichtbar oder sprang zurueck. - Die Swipe-Animation wurde durch Phone-Scroll-CSS ueberschrieben. - Drag/Reorder per Griff `` war optisch unzuverlaessig. - Tablet war nicht betroffen. Zusaetzlich war nach dem Funktionsfix die interne Build-Identita
- Caution: - PDF - QR - Patient-App - Scan - Parser - Plan-State - Storage - Tablet-Layout - Uebungsdatenbank-Logik
- Tests: - [ ] Handy-Viewport 390844 oder 400844 testen. - [ ] `matchMedia('(max-width:759px)').matches === true`. - [ ] Mindestens zwei Uebungen in den Plan legen. - [ ] Karte links/rechts swipen: Karte muss sichtbar mitlaufen. - [ ] Ueber Loeschschwelle swipen: Karte muss entfernt werden. - [ ] Griff `` halten und Karte verschieben. - [ ] Tablet-Viewport ab 760 px

### Buglog Phone Admin-Datei Banner ausblenden

- Source: `docs/bug-debug/2026-06-19-phone-admin-banner-hide.md`
- Areas: debug, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, tablet-layout
- Lesson: Im Handy-Layout ist eine gelbe interne Admin-/Testbox sichtbar: Diese Box gehoert nicht in den normalen Handy-Flow.
- Caution: - PDF - QR - Patienten-App - Scan - Parser - Android Wrapper - Tablet-Layout - Plan-State - Storage
- Tests: 1. Clean State: `localStorage.clear(); sessionStorage.clear(); location.reload();` 2. Handy-Viewport: 390 x 844. 3. Pruefen: - `window.innerWidth <= 759` - `matchMedia('(max-width:759px)').matches === true` - Gelbe `ADMIN-DATEI`-Box nicht sichtbar. 4. Tablet-Viewport: 820 x 1180. 5. Pruefen: - `window.innerWidth >= 760` - Tablet-Layout unveraendert.

### PATCHLOG v007 QR-Scan aus Fotodatenbank reparieren

- Source: `docs/bug-debug/2026-06-19-qr-photo-upload-decode.md`
- Areas: debug, parser-textblocks, pdf, qr-patient, scan-camera, sync, tablet-layout
- Lesson: Der QR-Scan ueber die Kamera funktioniert, aber QR-Codes aus hochgeladenen Bildern/Fotos aus der Fotodatenbank werden nicht zuverlaessig erkannt. Der bestehende Datei-Pfad `scanQrFromImageFile(file)` laedt Bilder nur ueber `URL.createObjectURL(file)` in ein `Image`-Element und scannt anschliessend eine 1800px-Canvas-Version mit wenigen Crops/Filtern. Auf And
- Caution: Keep patch scoped to the requested area.
- Tests: 1. App oeffnen. 2. QR-Scan ueber Kamera testen. 3. Foto-/Datei-Upload oeffnen. 4. Ein gespeichertes QR-Bild aus der Galerie auswaehlen. 5. Erwartung: App erkennt den QR und verarbeitet ihn wie beim Kamera-Scan. 6. Negativtest: normales Papierplan-Foto ohne QR soll weiterhin in den Papierplan-/OCR-Pfad gehen.

### 2026-06-20 v011 Tablet-Layout nach Rollback weiter kaputt wegen versionCode/Cache

- Source: `docs/bug-debug/2026-06-20-v011-tablet-layout-cache-rollback.md`
- Areas: debug, parser-textblocks, pdf, qr-patient, scan-camera, tablet-layout
- Lesson: Nach dem v011-Update war das Tablet-Layout sichtbar kaputt. Der direkte Rollback auf den Stand vor v011 stellte `kgg-update/index.html` und `kgg-update/version.json` zwar im Repository wieder her, die installierte App zeigte aber weiter den kaputten v011-Stand. Sichtbar in der App: - Toast: `KGG Update: aktuell (1.0.9-restore-lkg-qr-gallery-decode)` - Tablet
- Caution: - PDF - QR-Erzeugung - Patienten-App - Scan-Kamera - Parser - Android-Wrapper - Tablet-Layout - Plan-State - Storage
- Tests: - [x] Tablet-App komplett schliessen. - [x] App neu oeffnen. - [x] App laedt nicht mehr den kaputten v011-Stand. - [x] Tablet-Layout funktioniert wieder laut Max-Screenshot/Rueckmeldung. - [x] Max hat bestaetigt: `Hat geklappt`. - [ ] Galerie-QR separat neu testen, wenn ein neuer QR-Fix vorbereitet wird. - [ ] Kamera-Scan separat neu testen, wenn ein neuer Q

### Custom GPT Payload Schema: alter v1-Pfad statt modularer v2-Payload

- Source: `docs/bug-debug/2026-07-03-custom-gpt-payload-schema-path.md`
- Areas: debug, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, tablet-layout
- Lesson: Ein Custom-GPT-Preview-Dispatch kann formal plausibel aussehen, aber im Write-Gate scheitern, wenn er ein altes v1-Operationsschema verwendet. Historischer Run: `28665968004` scheiterte im Step `Apply guarded GPT payload` mit `ERROR: v1 only allows kgg-update/index.html`. Seit der modularen Quelle ist auch `path: "kgg-update/index.html"` falsch, weil `index.
- Caution: - App-Feature-Code - PDF - QR/Patienten-App - Scan/OCR - Parser - Plan-State - Medien/Upload - Android/APK - GitHub Manifest - Handy-Layout
- Tests: - `release-pipeline/kgg_gpt_payload_preflight.py --self-test` blockt einen Payload mit `file`. - GPT-Eval `payload-schema-path` blockt alte `operations` gegen `kgg-update/index.html`. - GPT-Eval `modular-payload` verlangt `patch_content` mit `__KGG_PATCH_ID__`. - Der GPT darf bei rotem Run nicht nur `meta.json 404` melden, sondern muss den fehlgeschlagenen S

### Custom GPT Preview-Gate Lessons

- Source: `docs/bug-debug/2026-07-03-custom-gpt-preview-gate-lessons.md`
- Areas: debug, drag-reorder, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, sync, tablet-layout
- Lesson: Der Custom GPT kann bei Preview-/Beta-Anfragen plausibel antworten, obwohl der GitHub-Run bereits fehlgeschlagen ist. Ein konkreter Fehler war: Die Antwort deutete einen fehlenden Preview-Manifest-Eintrag als "noch nicht veroeffentlicht", obwohl `Apply guarded GPT payload` rot war. Beim Tablet-Layout vermischt der GPT leicht zwei Bedienkonzepte: das alte Sca
- Caution: - App-Feature-Code - PDF - QR/Patienten-App - Scan/OCR - Parser - Plan-State - Medien/Upload - Android/APK, ausser Max fragt explizit danach - PDF - QR/Patienten-App - Scan/OCR - Parser - Plan-State - Medien/Upload - Android/APK - GitHub Manifest - Handy-Layout
- Tests: - Payload mit geschuetztem Token im Patch-Kommentar wird im Preflight geblockt. - GPT-Eval `failed-preview-run` verlangt den echten roten Step. - GPT-Eval `protected-token-payload` verlangt Stop vor Dispatch. - UI-Stability-Probe `tablet-splitter-scale-drag` prueft die konkrete Bedienlogik. - GPT-Eval `tablet-splitter` muss die richtigen Klassen, Variablen u

### 2026-07-29 - Preview-Marker und Default-Branch-Drift

- Source: `docs/bug-debug/2026-07-29-preview-marker-default-branch-drift.md`
- Areas: debug, modal, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, tablet-layout
- Lesson: Die KGG Test-App zeigte erneut einen schwarzen, vollhohen Balken mit kompletter Preview-Beschreibung. Der Balken verschob die eigentliche App und schnitt Bedienelemente am linken Rand an, obwohl ein kompakter Marker bereits auf einem offenen Arbeitsbranch implementiert und getestet war.
- Caution: - Admin- und Kolleg:innen-HTML - PDF - QR/Patienten-App - Scan/OCR - Parser - Plan-State - Medien/Upload - Android- und Admin-Manifest
- Tests: - Ein altes Sticky-Banner wird ersetzt und nicht dupliziert. - Der eingeklappte Marker ist hoechstens 92 x 24 CSS-Pixel gross. - App-Geometrie und horizontaler Overflow bleiben mit und ohne Marker identisch. - Menue, Scanner und Dock bleiben bei geschlossenem Marker anklickbar. - Details oeffnen und schliessen per Toggle, Aussenklick und Escape. - Viewports:

### WebView-Kamera und Cross-App-QR brauchen reale Vertragsbelege

- Source: `docs/bug-debug/2026-08-01-webview-camera-cross-app-qr.md`
- Areas: parser-textblocks, phone-layout, qr-patient, scan-camera
- Lesson: Eine gruen gebaute HTML-Preview behauptete automatische QR-Uebernahme, auf dem Android-Geraet erschien aber weiter die alte stark gezoomte Systemkamera.
- Caution: Kein Mikrofonzugriff, kein erzwungener Zoom, keine echten Patientendaten oder echten QR-Payloads in Tests, Memory oder Agent-Koordination.
- Tests: Pflicht sind Critical, UI-Stability, Admin `camera-qr`, Patient `patient-scan`, Android-Wrapper-Vertrag und Preview-APK-Build. Browser-Smoke prueft Auto-QR, jsQR-Fallback, Permission-Fallback, manuelles Foto und Track-Cleanup getrennt. Ein Emulator ersetzt den abschliessenden Handytest nicht.

### Patient-Kamera wirkt gezoomt und GPT stoppt an Koordinations-404

- Source: `docs/bug-debug/2026-08-02-patient-camera-crop-coordination-404.md`
- Areas: debug, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera
- Lesson: Der mobile Live-Scanner der Patient:innen-App zeigt nur einen Ausschnitt des Kamerabilds und wirkt dadurch stark gezoomt. Der Update-GPT diagnostiziert die Ursache, startet aber keinen Patient-Preview-Write, weil der private Koordinationsindex HTTP 404 liefert.
- Caution: - QR-/KGGH2-/KGGD1-Vertrag - Parser und Plan-State - Patientenspeicher und Trainingswerte - Admin-App, PDF und Android-Wrapper
- Tests: - Breiter Stream `1280x720` und hoher Stream `720x1280` bleiben im mobilen Kamerarahmen vollstaendig sichtbar. - `getComputedStyle(video).objectFit` ist `contain`. - Kein horizontaler Overflow; Schliessen und Fallbacks bleiben bedienbar. - QR-Erkennung, Track-Cleanup, Plan und Trainingswerte bleiben unveraendert. - Koordinationsindex liefert keinen 404 und e

### Patient First-Load Modules

- Source: `docs/bug-debug/2026-08-02-patient-preview-first-load-modules.md`
- Areas: qr-patient, scan-camera
- Lesson: Ein Patient-Preview-Run konnte vollstaendig gruen sein, obwohl die erste im Browser oder in der Test-App geoeffnete `index.html` den Scanner und weitere Patient-Module noch nicht geladen hatte. Das gleiche Risiko bestand fuer den echten ersten QR-Aufruf: Die Dateien waren im Artefakt vorhanden, wurden aber erst durch `service-worker.js` in einen spaeteren, b
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### 2026-08-13 - Custom-GPT Antwortzug-Reaktivierung und Editor-/Action-Drift

- Source: `docs/bug-debug/2026-08-13-custom-gpt-answer-turn-editor-drift.md`
- Areas: debug, modal, parser-textblocks, pdf, qr-patient, scan-camera, sync
- Lesson: Ein KGG Custom GPT kann nach dem Ende seines ChatGPT-Antwortzugs nicht selbst einen neuen Antwortzug starten. Ein laufender GitHub-Workflow kann zwar weiter arbeiten, aber Run-, Job- und Artifact-Status werden danach nicht von selbst erneut gelesen. Wenn Codex den GPT erneut aktiviert, kann ohne klare Uebergabe ein doppelter Preview-Dispatch, eine falsche Fo
- Caution: - App-Feature-Code, PDF, QR-/Patienten-App-Vertrag, Scan/OCR, Parser, Plan-State, Medien/Upload, Android/APK, Manifest und Geheimnisse. - Keine Patientendaten, echte Plan-/QR-Payloads, Chats, Tokens oder Rohdaten im Bug-Debug-Log, in der Koordination oder im Project Memory speichern.
- Tests: - `python release-pipeline/kgg_bug_knowledge.py --check` ist gruen. - `python release-pipeline/kgg_custom_gpt_knowledge_pack.py --check` ist gruen. - `python release-pipeline/kgg_patient_gpt_resources.py --check` ist gruen. - Der Resource-Audit akzeptiert nur passende Hashes; nach einer kanonischen Knowledge-Aenderung bleibt ein Profil bis zur echten Editor-

### KGG Ticket-Queue Reihe 1 Testuebergabe

- Source: `docs/bug-debug/2026-08-20-ticket-queue-row1-handoff.md`
- Areas: modal, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, sync, tablet-layout
- Lesson: Stand: 2026-08-20 Zweck: Uebergabe der noch offenen Nachweise an Custom GPT + Max. Wichtig: Diese Datei aendert keinen Ticketstatus und schliesst kein Ticket. - KGG-Main: `5d0f9395e6d493f84731fd8980d363c305531553`. - Admin-Main: v070 (`1.0.70-tablet-package-save`). - Patient-Main/PWA: v77. - Automatische lokale Smokes der Reihe 1: gruen. - Admin-live und Pat
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### Kurze Startprompts fuer neue Codex-Chats

- Source: `docs/bug-debug/2026-08-21-codex-chat-start-prompts.md`
- Areas: debug, pdf, qr-patient, sync
- Lesson: Weiter mit KGG. Lies `C:\src\kgg\docs\bug-debug\2026-08-21-codex-continuation-pdf.md`. Pruefe die lokale PR-Vorbereitung fuer Ticket 012. Keine Pushes, Merges oder Releases ohne ausdrueckliche Freigabe. Weiter mit KGG. Lies `C:\src\kgg\docs\bug-debug\2026-08-21-codex-continuation-gpt-sync.md`. Arbeite zunaechst read-only; kein Preview, kein Dispatch und kein
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### Codex-Fortsetzung Custom-GPT-Synchronisierung

- Source: `docs/bug-debug/2026-08-21-codex-continuation-gpt-sync.md`
- Areas: qr-patient, sync
- Lesson: Stand: 2026-08-21 - Admin-GPT: `g-6a45fba0f3408191ac1fb2c987a2e960`, privat, vier kanonische Knowledge-Dateien und beide Actions sichtbar. - Lokaler Produktionsaudit: `TARGET_PASS`; Snapshot steht bewusst auf `target-pending-live-editor-sync`, weil die Operations-Knowledge-Datei nach der letzten Aenderung extern erneut hochgeladen/verifiziert werden muss. -
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### Codex-Fortsetzung PDF / Ticket 012

- Source: `docs/bug-debug/2026-08-21-codex-continuation-pdf.md`
- Areas: pdf
- Lesson: Stand: 2026-08-21 - Main: `5d0f9395e6d493f84731fd8980d363c305531553`, Admin v070. - Kandidat: `C:\src\kgg-ticket-session-1`, Branch `codex/ticket-session-1`, Commit `a136bdf07298e9926d6cf7c239655c35719c5b77`, v071. - Der Kandidat basiert direkt auf Main, ist sauber und nicht gepusht. - Fix: klassische PDF-Uebungsnummern laufen seitenuebergreifend global weit
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### Codex-Fortsetzung QR / Device-Variance / Ticket 032

- Source: `docs/bug-debug/2026-08-21-codex-continuation-qr-device.md`
- Areas: phone-layout, qr-patient, scan-camera
- Lesson: Stand: 2026-08-21 - Admin-Kamera-Smoke gruen: BarcodeDetector, jsQR-Fallback, Berechtigungsfallback und manuelles Foto. - Patient-Scanner-Suite laeuft mit Multi-Plan-Erhalt, Track-Cleanup und vielen synthetischen Perspektiv-/Distanz-/Rotations-/Lichtfaellen. - Extreme Klein-/Dunkel-, Trapez-, Asymmetrie- und starke Yaw/Pitch-Faelle melden weiterhin `WARN` bz
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### KGG Realgeraete-Abnahme Ticket-Session 1

- Source: `docs/bug-debug/2026-08-21-real-device-acceptance-handoff.md`
- Areas: drag-reorder, modal, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, sync, tablet-layout
- Lesson: **Status:** `pending-real-device` **Erstellt:** 2026-08-21 **Lokaler Stand:** `codex/ticket-session-1` / `d898b423ee324a8f8f4f4115a8dd015e2ed34afc` **Bereich:** Admin-/Patient-App, QR, PWA, Tablet, Planverwaltung Diese Uebergabe enthaelt nur Tests, die lokale Browser-, Parser- und PDF-Pruefungen nicht vollstaendig ersetzen koennen. Es werden keine Patientend
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### 2026-08-22 KGG Ticket-Backlog und Live-Test-Merkliste

- Source: `docs/bug-debug/2026-08-22-ticket-backlog-and-live-tests.md`
- Areas: modal, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, sync, tablet-layout
- Lesson: Diese Datei ist die dauerhafte Uebergabe fuer noch offene Live-/Realgeraet-Tests und bekannte Ticketbloecke. Sie enthaelt nur synthetische Testfaelle und keine Patientendaten. - Kanonischer Remote-Stand: `origin/main` / `ad6433a`. - Therapeut:innen-Quelle: v071, `1.0.71-pdf-global-exercise-numbering`. - Veroeffentlichtes Therapeut:innen-Web: r0426 / v1.0.65.
- Caution: Keine Patientendaten, keine Secrets, kein Preview-/Dispatch-/Memory-Write und keine automatische Aenderung von Ticket- oder GPT-Live-Status ohne belegten Nachweis.
- Tests: Statuswerte: `pending-real-device`, `blocked-remote-access`, `scope-open`, `passed` oder `failed`. Ein Test wird erst nach dokumentiertem Geraet, Browser, Version, Beobachtung und anonymisiertem Screenshot als `passed` markiert. | Prioritaet | Test/Ticket | Geraet/Kanal | Abnahme | |---|---|---|---| | P0 | RD-001 / Ticket 001 | Admin-Browser | Sieben Uebunge

### Debug JSON Seite

- Source: `docs/bug-debug/README.md`
- Areas: debug, qr-patient
- Lesson: Bei PWA-/Storage-/Service-Worker-Problemen braucht es eine einfache Diagnoseausgabe.
- Caution: Keep patch scoped to the requested area.
- Tests: Run the risk-matched KGG battery.

### Drag-Drop / Reorder-Hitbox

- Source: `docs/bug-debug/README.md`
- Areas: drag-reorder, phone-layout, tablet-layout
- Lesson: Verschieben von Uebungskarten kann je nach Layout/Viewport anders reagieren. Tablet und Handy getrennt testen.
- Caution: Keine Layout-Aenderungen nebenbei. ---
- Tests: - Nach oben/unten verschieben testen. - Links/rechts Swipe/Delete-Animation separat testen. - Handy und Tablet getrennt pruefen.

### Patient-App iOS/PWA startet leere Basis-App

- Source: `docs/bug-debug/README.md`
- Areas: parser-textblocks, pdf, qr-patient, scan-camera, tablet-layout
- Lesson: Home-Screen-Installation oder Favoriten oeffnen teilweise nur die leere Basis-App. Konkreter Patient:innenplan kann beim Start fehlen oder alte Versionen werden zuerst geoeffnet.
- Caution: Therapeuten-App-Layout, PDF, Parser und Scan nur aendern, wenn explizit noetig. ---
- Tests: Run the risk-matched KGG battery.

### Tablet/Handy Layout-Grenze 759/760 px

- Source: `docs/bug-debug/README.md`
- Areas: phone-layout, tablet-layout
- Lesson: Handy-UI und Tablet-UI duerfen nicht gleichzeitig aktiv sein. Handy: `max-width:759px`. Tablet: `min-width:760px`.
- Caution: Tablet-Funktionen nicht durch Handy-Cleanup zerstoeren. ---
- Tests: Nicht mit Browser-Zoom testen, sondern mit echten Viewports: - Handy z. B. 390 844 oder 400 844 - Tablet z. B. 820 1180

### v389 Textfeld-Jitter-Diagnostik

- Source: `docs/bug-debug/README.md`
- Areas: debug
- Lesson: Textfeld-/Render-Jitter musste isoliert messbar gemacht werden.
- Caution: Haupt-App bleibt im Diagnose-Test moeglichst unveraendert. ---
- Tests: Run the risk-matched KGG battery.

### Bugfix-Doku: Mobile Share-Modal faellt in den normalen Handy-Flow

- Source: `docs/bugfixes/mobile-share-modal-css-regression.md`
- Areas: modal, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, tablet-layout
- Lesson: Im Handy-Layout (< 760 px) werden die Elemente des Dialogs Therapeuten-App weitergeben sichtbar im normalen Seitenfluss angezeigt: - Ueberschrift Therapeuten-App weitergeben - Hinweis Waehle, was der QR-Code enthalten soll. - Auswahlbuttons Nur App, App + API-Key, Nur API-Key Diese Elemente gehoeren nicht in den normalen Handy-Flow. Sie sollen nur erscheinen
- Caution: - QR-Core - API-Key-Transfer-Logik - PDF-Core - Parser - Scan-Core - Patient-App-Payload - Plan-State - `.scanHub` / obere Scanbox, da das ein separater UI-Flow-Punkt ist
- Tests: 1. Viewport 390 x 844 px oeffnen. 2. Pruefen: Therapeuten-App weitergeben und die drei Optionen sind nicht im normalen Handy-Flow sichtbar. 3. Viewport 390 x 844 px: `document.getElementById('kggTherapistShareModal').getBoundingClientRect().height` soll im geschlossenen Zustand 0 oder das Element `display:none` haben. 4. Modal gezielt oeffnen: `openKggTherap

### 2026-06-18 v003a Plan UI Stability Handoff

- Source: `docs/release-handoffs/2026-06-18-v003a-plan-ui-stability.md`
- Areas: debug, drag-reorder, parser-textblocks, pdf, phone-layout, qr-patient, scan-camera, tablet-layout
- Lesson: Nicht die originale `KGG_GitHub_Update_v003_plan_ui_stability.zip` deployen. Grund: Die originale v003 enthaelt zwar den funktionalen Plan-UI-Stability-Patch, traegt intern aber alte Build-Identitaet: - `<title>` zeigt noch `mini03` - `VERSION` zeigt noch `v399` - `KGG_BUILD_INFO.release` zeigt noch `v399` Das wuerde den vorherigen mini07-Identitaets-Fix zur
- Caution: - PDF - QR - Patient-App - Scan - Parser - Plan-State - Storage - Tablet-Layout
- Tests: Phone: - Viewport 390844 oder 400844. - Mindestens zwei Uebungen in den Plan legen. - Uebungskarte antippen: Nur Karte/Planbereich darf reagieren, darunterliegende UI darf nicht nach unten creepen. - Uebung per Griff `` verschieben: Nur Karten im Plan sollen sich bewegen. - Vertikal scrollen: Plan-Karten duerfen nicht flackern. - Swipe links/rechts muss weit

### Release Handoff v007 QR Photo Upload Decode

- Source: `docs/release-handoffs/2026-06-19-v007-qr-photo-upload-decode.md`
- Areas: debug, parser-textblocks, pdf, qr-patient, scan-camera, tablet-layout
- Lesson: Bereit als GitHub-Update-Patchscript. Keine grosse HTML-Datei muss ueber den Connector hochgeladen werden. Wenn andere Dateien geaendert werden: stoppen. PDF, QR-Erzeugung, Patienten-App, Scan-Kamera, Parser, Android-Wrapper, Tablet-Layout, Plan-State, Storage.
- Caution: PDF, QR-Erzeugung, Patienten-App, Scan-Kamera, Parser, Android-Wrapper, Tablet-Layout, Plan-State, Storage.
- Tests: Run the risk-matched KGG battery.

---

# Source: docs/kgg-gpt-patch-patterns.md

# KGG GPT Patch Patterns

Use these patterns to avoid repeating known KGG regressions.

## Forbidden Patterns

### global-touch-action

- Risk: Global touch or pointer rules can break swipe, scroll and drag/reorder flows.
- Avoid: Do not add broad `touch-action`, `pointer-events` or gesture rules on app-wide containers.
- Prefer: Limit gesture rules to the exact handle/control and run UI stability regression.

### modal-scoped-only-to-tablet

- Risk: Closed modals can leak into the phone document flow when hiding rules are scoped only to tablet classes.
- Avoid: Do not hide modal overlays only below `body.tabletLayoutCustom`.
- Prefer: Give the modal a global hidden base rule and then layer tablet-specific presentation separately.

### breakpoint-drift

- Risk: Phone and tablet UI can both become active if the 759/760 px split drifts.
- Avoid: Do not test breakpoints with browser zoom or change phone/tablet media queries incidentally.
- Prefer: Use real viewports: phone <=759 px, tablet >=760 px.

### debug-output-to-patient

- Risk: Patient-facing output must never expose raw JSON, Base64 or debug payloads.
- Avoid: Do not route debug pages or payload dumps into normal patient flows.
- Prefer: Keep debug output internal and preserve patient-safe rendering.

### side-effect-feature-touch

- Risk: Small UI fixes often become unsafe when they also touch QR, PDF, parser, scan or plan state.
- Avoid: Do not edit protected feature blocks unless Max explicitly asked for that area.
- Prefer: Make one scoped patch and list all untouched protected areas in the PR.

## Area Test Hints

- `debug`: Debug output must stay internal and never become patient-facing output.
- `drag-reorder`: Test drag/reorder and swipe/delete separately on phone and tablet.
- `general`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `modal`: Verify closed modal is not in normal flow; verify explicit open/close.
- `parser-textblocks`: Run textblocks regression when parser/text-block behavior is touched.
- `pdf`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `phone-layout`: Use real phone viewport <=759 px and run ui-stability regression.
- `qr-patient`: Do not touch QR/patient flow unless explicitly requested; run patient-qr critical when touched.
- `scan-camera`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `sync`: Run sync regression when sync, bank, package or peer behavior is touched.
- `tablet-layout`: Use real tablet viewport >=760 px and run ui-stability regression.

## PR Reminder

- Include `base file used`, `changed file`, `changes`, `smoke test` and `risks`.
- Mention the matching bug-history lesson when one exists.
- Do not mark tests green unless GitHub or local output proves it.
