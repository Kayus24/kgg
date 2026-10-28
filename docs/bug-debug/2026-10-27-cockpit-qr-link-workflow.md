# Patienten-QR: Scantext und Cockpit-Link ohne Auto-Oeffnung

## Auftrag und Ausgangsstand
Ausgang: `main` `96a82f08ca674ec3195c20ec3d16bb45f9965b16`, Admin-Web r0437 / Quelle v129.
Bei QR-Scans wird das Cockpit bislang durch `importPatientPlan()` aktiviert und
eine separate Cockpit-Link-Ausgabe angezeigt. Der urspruengliche Scantext wird verdeckt.

## v130-Kandidat (isolierter Branch)
- Scan verarbeitet QR-Daten weiterhin im bisherigen Job/Inbox-Workflow.
- `importPatientPlan(payload,{background:true})` aktualisiert nur den Cockpit-Slot;
  die aktuelle Ansicht und das Ausgabemodal werden nicht umgeschaltet.
- `scanResultToCopyText` haengt den Link NACH dem bisherigen Patiententext an.
- `makeLink()` nutzt standardmaessig die feste oeffentliche URL
  `https://kayus24.github.io/kgg/kgg-update/index.html` statt der gerade
  aufgerufenen Release-/Browseradresse; explizite Test-Base-URLs bleiben erlaubt.
- Cockpit-Code bleibt `KGGTC1:`. Komprimierte neue Links haben den Payloadmarker
  `z` und nutzen das bereits eingebundene `fflate.deflateSync`.
  Lesbarkeit alter unkomprimierter `KGGTC1:`-Codes bleibt erhalten.
  Aufblaehen beim Lesen ist durch ein oberes Ausgabelimit begrenzt.

## Native Android-App-Links: noch offene externe Bedingung
Die vorhandene Android-App akzeptiert nach Codevertrag nur Links auf dem Pfad
`/kgg/kgg-update/index.html`. Das ist nun der Standardpfad der neuen Links.
Eine automatische Oeffnung installierter Apps ist damit alleine nicht bewiesen:
`https://kayus24.github.io/.well-known/assetlinks.json` lieferte am
27.10.2026 HTTP 404. Android 12+ bevorzugt ohne verifizierte Domain einen Browser.

Fuer eine verlaessliche automatische native Linkzuordnung sind vor Release
notwendig: Zugriff auf die Domainwurzel, Digital-Asset-Links-Datei mit dem
tatsaechlichen SHA-256-Fingerprint des signierten Admin-APK (`de.kgg.admin`),
`android:autoVerify` am passenden Android-Intent-Filter, gepruefte Verifikation
auf einem echten Geraet und Freigabe eines neuen APK-/Web-Releases.
NICHT eine JSON-Datei unter `/kgg/.well-known/` erstellen: Android sucht
die Datei am DOMAINROOT, nicht unter dem GitHub-Pages-Projektpfad.

## Schutzgrenzen und Nachweise
- Keine Cloud-Shortener und kein neues Backend: ein Cockpit-Link enthaelt
  patientenbezogene Werte und ist keine Verschluesselung.
- Nicht laengere Links durch Abschneiden kuerzen.
- Gezielter synthetischer `kgg_cockpit_qr_resume_smoke.js`:
  normale Ansicht, kein Scanmodal, Scantext + Link, Android-Pfad,
  Komprimierung/Legacy-Decoder, Wiederaufnahme und Notizen.
- `kgg_therapy_cockpit_native_contract.py`: statischer Android-Vertrag.
- Physische App-Oeffnung und Domainverifikation sind **NOT_RUN/UNVERIFIED**.
- Kein Push/Merge/Release aus diesem isolierten Stand.

## 27.10.2026: kopierbare Cockpit-Abschlussdokumentation
Nach Feedback zur ausgegebenen Patienten-Dokumentation wurde `documentationFor`
auf **Übungsname -> S1/S2/... -> weitere Übungen -> optionale vorhandene
Therapienotizen -> Neuer Cockpit-Link** beschränkt. Keine Kopfzeile,
kein Dummy-Patientenname, kein Datum und kein redundanter Abschlussvorspann.
`showOutput` kopiert den technischen Ergebnisstatus nicht länger als Text;
bei `plan_mismatch`, `exercise_mismatch`, `hook_unavailable`,
`hook_failed` wird die entsprechende Warnung stattdessen getrennt im
Cockpit-Ausgabemodal angezeigt. Ein fehlgeschlagener Plan-Import ist damit
nicht unbemerkt erfolgreich und wird auch nicht als Patientenbefund kopiert.

Gezielter `kgg_cockpit_qr_resume_smoke.js` PASS am isolierten lokalen
v130-Kandidaten (23.43s / exit 0), mit Assertions für sauberen Beginn,
gesonderte Warnung, Notizen, URL als letzte Zeile, Link-Kodierung,
alte/neue Links und unabhängige Browserkontexte.

Ein **wirklich kurzer**, geräteübergreifend verwendbarer URL-Token
ist OHNE zusätzlichen autorisierten, datenschutzgerechten Speicher-
und Lookup-Dienst nicht erreichbar: der bestehende Offline-Link enthält
den vollständigen Trainingsstand. Die v130-Deflate-Kodierung aus dem
vorherigen Arbeitsabschnitt verkürzt die URL nur relativ, bleibt aber
selbstenthaltend. Die ältere, lange Beispiel-URL stammt aus dem
veröffentlichten v129-Stand; v130 ist nicht veröffentlicht.

## Android App Links – Umsetzung 27.10.2026
- Manifest `android-wrapper/app/src/main/AndroidManifest.xml`: bestehender **exakter** HTTPS-Pfad blieb unverändert; `android:autoVerify="true"` ergänzt. Natives `MainActivity.java`-Handoff war bereits vorhanden und wurde nicht erweitert oder umgebaut.
- `release-pipeline/kgg_therapy_cockpit_native_contract.py`: Regression gegen fehlendes `autoVerify` eingefügt. PASS.
- Derzeitiger Link `https://kayus24.github.io/kgg/kgg-update/index.html?cockpit=...` wird von Android nur automatisch an `de.kgg.admin` übergeben, wenn die Domain-Asset-Links-Deklaration **öffentlich am Domain-Root** vorliegt und Android den **installierten** Cert-Fingerprint verifiziert.
- Fingerprint anhand `apksigner verify --print-certs` für Admin v386, v400, v401 und v406 identisch; lokal gebaute Admin-APK ebenfalls identisch: `FA:E0:EE:E0:21:92:F3:27:F6:E9:48:96:53:58:E7:70:C5:9C:8B:3B:24:2D:77:E5:90:F1:E7:B5:1A:B4:E8:C6`. Verbindliche Gegenprobe: Site-PR #1 mit `apksigner`-Fingerabdruck vergleichen.
- GitHub root repo `Kayus24/Kayus24.github.io` neu; Datei `.well-known/assetlinks.json` mit **vollständiger** Signatur und leere `.nojekyll` in Branch `feat/kgg-android-assetlinks-20261027`, Commit `4d90c73`, [Draft-PR #1](https://github.com/Kayus24/Kayus24.github.io/pull/1). **Nicht gemergt, nicht live**. `https://kayus24.github.io/.well-known/assetlinks.json` bisher HTTP 404.
- Offline-Android-Build mit lokal vorhandenem Gradle 8.14.3/JBR erfolgreich (`:app:assembleAdminDebug`, 33 Tasks). APK `android-wrapper/app/build/outputs/apk/admin/debug/app-admin-debug.apk`, SHA256 `C71DDBA0DF53FB5971A6FABAA9F7DA99F8F737E0C7905AC168FA62D7021AA375`. Binary manifest per `aapt dump xmltree` geprüft: `autoVerify=true`, exakt erwartete URL. `apksigner` Fingerprint passt.
- Die Android-Version im lokalen Build ist noch `versionCode 38 / 0.2.16-v406`; der Build ist **kein** update-sicher freigegebenes v130-APK. Live-Versionierung/Release-Bindung steht aus.
- ADB-Geräte: **keine** verbunden. Echtes `pm verify-app-links`, `pm get-app-links`, Link-Tap: **NOT_RUN**.
- Für dieses ausdrücklich **nicht veröffentlichte** KGG-PR kann die bestehende Hygieneprüfung **nur zu Entwicklungszwecken** `KGG_ALLOW_RELEASE_DRIFT=1` verwenden (source v130 / manifest Admin v129); die korrekte Release-Zuordnung bleibt zwingende Sperre für Merge/Release. Kein dauerhaftes Abschalten von Schutzprüfungen.

## Changelog-Fortschritt und Commit-Hook-Checkpoint
Der erste normale `git commit`-Versuch wurde vom installierten Hook zurecht
zurückgewiesen (2/141 Python-Release-Contract-Fälle: eingebetteter Changelog
v129 gegen `version.json` v130). Kein Hook wurde umgangen und kein Commit
durchgedrückt. Reparatur mittels bestehendem `kgg_changelog_archive.py
--compact-current`: separater v130-Changelog-Eintrag,
`docs/changelog-archive/kgg-therapist-changelog-through-v130.json`
mit 71 gesicherten Versionseinträgen, eingebettetes 15-Einträge-Fenster.
`test_kgg_changelog_archive.py` erwartete Snapshot-Zahlen an v130 angepasst;
6/6 PASS, Archiv-Validator PASS, Quellgeneratorabgleich PASS.
Ein zweiter normaler Commit-Hook-Lauf steht aus.

## Fortsetzung nach Chat-Haenger – Linux-CI-Handy-Layout
GitHub PR #345 hatte mit HEAD `90bb318` in Actions Run `40540368777` im
`core-gate` **FAIL**, nachdem die release-, Android- und sonstigen
Vertraege erfolgreich durchlaufen waren. Der gezielte Cockpit-Browserfall
`phone activation selects newly scanned patient` meldete auf Linux
`viewport=390, documentWidth=390, bodyWidth=390, card.right=394.16`:
die einzelne sichtbare Karte ragte kurzfristig um 4.16px nach rechts,
waehrend das Dokument selbst nicht horizontal scrollte. Windows lokal PASS.

Der Browser-Regressionsfall wartet nun nach dem Blur der Handy-Notizen
ueber requestAnimationFrame-basiertes Playwright `waitForFunction`
maximal 4 Sekunden auf eine **real** im Viewport befindliche aktive Karte.
Der strenge geometrische End-Assert bleibt unveraendert. Ein anhaltender
Ueberlauf bleibt ein FAIL; es wurden **keine** Produkt-CSS-Regeln,
Breakpoints oder Test-Toleranzen geloest bzw. vergroessert.
Gezielter Node-Cockpit-QR-Smoke unter Windows: PASS. Linux-CI gegen die
Aenderung bis zur Rueckmeldung **NOT_RUN/IN_PROGRESS**; keine Behauptung,
dass der Fehler dort bereits behoben ist.
