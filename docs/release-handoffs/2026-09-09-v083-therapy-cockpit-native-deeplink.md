# KGG Therapie-Cockpit v083 – nativer Deep-Link-Handoff

## Stand

- Main-Basis für diesen aktuellen Lauf: `ef625b87f321b0e8f4cec4980c99a42fa58da0d8` (ursprünglicher Startstand: `58ede321b2896522a660a0c184d7a83ea817e6e4`)
- Arbeitsbranch: `codex/therapy-cockpit-v2`
- Web-Patches: `kgg-v082-therapy-cockpit`, `kgg-v083-therapy-cockpit-id-guard`
- Web-Quelle: `kgg-update/src/patches/v082-therapy-cockpit.html`
- ID-Guard: `kgg-update/src/patches/v083-therapy-cockpit-id-guard.html`
- Generierter Kandidat: `kgg-update/index.html`
- Kandidatenhash: `d647eadb6e7c691a6a846133f0447a15adc2b44a3fcd04a498fc1a015d482719`

## Web-Vertrag ist fertig

Der Web-Patch importiert selbsttragende `KGGTC1:`-Links aus URL oder Text, validiert Integrität, Name-Decoding, Satzstruktur, Wertebereiche und stabile zweistellige Base62-Übungs-IDs. Er hält bis zu drei Slots nur im Speicher, trennt graue Vorwerte von weißen Tageswerten, bietet die Inline-Tastatur, unabhängige Karten und Scrollbereiche, vollständige Ansichtsschalter und Abschlussdokumentation. Bei einem lokalen `file://`-WebView erzeugt `Plan fertig` einen öffentlichen Link unter `https://kayus24.github.io/kgg/kgg-update/index.html?cockpit=...`.

Der v083-ID-Guard behandelt ein vorhandenes `cockpitId` als verbindlichen kanonischen Schlüssel: ungültige oder unbekannte IDs werden vor Bank-/Sync-Übernahme mit `exercise_id_invalid` bzw. `unknown_exercise_id` abgewiesen; eine Namensabweichung liefert `exercise_id_collision`. Eine fehlende explizite ID darf weiterhin deterministisch aus dem kanonischen Übungsnamen abgeleitet werden.

## Beleg

- `therapy-cockpit-critical`: grün, inklusive 5/10/20/40-Übungsgrößenproben, Integritätsfehlern, unbekannten IDs, Slotgrenze, Vorwert-Roundtrip und sicherem Plan-Adapter.
- Explizite unbekannte/ungültige Übungsbank-IDs: grün mit fail-closed Guard.
- `therapy-cockpit-browser-regression`: grün bei 820×1180, 1024×768 und 1280×800; 1/2/3 Slots, kein Overflow, Numpad, Außen-Tipp, Ansichtswechsel, vierter Import, mittlere Entfernung, Abschluss-Roundtrip, Null-Slot-Rückkehr und Reload-Grenze.
- Vollständiger kritischer Lauf: 139 Tests, `OK (skipped=1)`; danach alle weiteren kritischen Verträge grün.
- Remote-Gates auf Kandidat `78faefb`: Android-Wrapper `34313935264`, Validate/Build `34313935271`, Required Gate `34313935266` — alle grün.
- Die lokale vollständige Pre-Commit-Zertifizierung stoppt zusätzlich am bestehenden `patient-qr-v81-device-ladder-regression`: der Test überschreitet unter dieser Windows-Umgebung sein 300.000-ms-Watchdog; ein isolierter Lauf mit verlängertem Diagnose-Timeout reproduziert Recognition-/Lifecycle-Fehler in diesen alten Geräteprofilen. Die Cockpit-kritischen und nativen Verträge bleiben grün; der Fehler liegt außerhalb des Cockpit-Patches.
- Der separate `release-pr`-Runner hatte bei `origin/main...HEAD` keinen Merge-Base, weil sein `git fetch origin main` keinen Remote-Tracking-Ref anlegte. Der Workflow verwendet nun einen expliziten Ref-Fetch (`main:refs/remotes/origin/main`); der zugehörige Admin-Editor-Sync-Vertrag ist lokal grün und Validate/Build `34313935271` ist nach dem Push grün.

## Nativer Source-Patch

Der kleinste Wrapper-Patch ist im Arbeitsbaum umgesetzt:

- `MainActivity` hat zusätzlich einen exakten `https`/`VIEW`/`DEFAULT`/`BROWSABLE`-Filter für `kayus24.github.io/kgg/kgg-update/index.html` und `singleTop` für die Wiederverwendung des laufenden Tasks.
- `onCreate` übernimmt einen validierten Link in die lokale HTML-URL.
- `onNewIntent` übergibt einen zweiten validierten Link direkt an `window.KGGTherapyCockpit.importCode(...)`, ohne die WebView neu zu laden; vorhandene RAM-Slots bleiben damit erhalten.
- Host, Pfad, Schema, Port, Fragment, doppelte Parameter, `KGGTC1:`-Prefix, Base64URL-Zeichen und 30.000-Zeichen-Limit werden vor der Übergabe geprüft. Die Codec-Integrität und Übungs-ID-Prüfung bleibt im Web-Core.
- JavaScript-Quoting erfolgt über `JSONObject.quote`; der rohe Link wird nicht geloggt. Fehlende Web-API wird nur begrenzt wiederholt und danach generisch gemeldet.

Der statische Vertrag `release-pipeline/kgg_therapy_cockpit_native_contract.py` ist grün. Ein Android-APK-/Gerätetest ist noch nicht belegt, weil auf dieser Maschine Java, Gradle, Android SDK und `adb` fehlen.

## Sichere Anschlussprüfung

1. Im vorhandenen Android-CI `assembleAdminDebug assembleKollegenDebug assemblePreviewDebug` bauen.
2. Die Preview/Test-App installieren und einen gültigen Link aus der offiziellen öffentlichen Basis öffnen.
3. Im laufenden Task zwei weitere gültige Links öffnen, danach einen vierten Link sowie falschen Host/Pfad, manipulierte Integrität und überlange Payload prüfen.
4. Android-Shell-/Manifestversion erst im vorgesehenen Releaseprozess erhöhen und die gebauten Artefakte mit dem aktuellen Web-Kandidaten verknüpfen.

Die APK ist in diesem Lauf weder installiert noch auf einem Gerät akzeptiert. Der Remote-Preview-Dispatch wurde nicht ausgeführt, weil die Sitzung keine callable `submitKggPreviewAuto`-Operation anbietet; ein direkter CLI-Dispatch würde den vorgeschriebenen Gate umgehen. Keine Main-/Live-Freigabe wurde vorweggenommen. Ein Main-/Live-Schritt bleibt bis zu Max' exakter Phrase `Gut für Main` gesperrt.
