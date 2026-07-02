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
