# KGG Android Wrapper v2

Quellprojekt fuer die einmalig neu zu installierenden Admin- und Kolleg:innen-APKs. Danach werden HTML-Releases ueber die getrennten Kanaele in `therapist-app/android_update_manifest.json` geladen.

Der Admin-Flavor enthaelt zusaetzlich die native Release-Zentrale. GitHub-Tokens werden nur im Android Keystore gespeichert und niemals an die WebView weitergereicht. Der Kolleg:innen-Flavor kann keine Release-Aktionen aufrufen.

Ab v395 ist die GitHub-Verbindung nur noch der Komfortweg. Der stabile Handy-Standard ist:

1. Aktuelle HTML in der Admin-App speichern.
2. GitHub-Mobile-Inbox oeffnen.
3. HTML auf den Branch `mobile-inbox` hochladen.
4. GitHub Actions erzeugt den geprueften Admin-Beta-Release.

Buildvarianten:

- `assembleAdminDebug`
- `assembleKollegenDebug`

## Schnelle Preview-Test-APK (ohne Beta- oder App-Merge)

Die einmal auf `main` registrierte GitHub Action `Android wrapper check` hat
einen separaten manuellen Modus: **Actions → Android wrapper check → Run workflow**,
Branch `main` belassen und bei `source_pr` die Nummer des offenen KGG-PRs
eingeben (z. B. `366`). Nach dem Lauf unter `Artifacts` das ZIP
`unapproved-quick-pr-...` herunterladen und `app-preview-debug.apk`
auf dem Android-Testgerät installieren.

Die Action pinnt den SHA des PRs. Ein eigener, unprivilegierter Runner baut
ausschließlich `assemblePreviewDebug` und prüft Signatur, Paketkennung
`de.kgg.preview` und eingebetteten Source-SHA. Die APK ist ausdrücklich
**UNAPPROVED** und liegt höchstens sieben Tage als Actions-Artefakt vor.
Weder `kgg-preview-approved` noch ein Merge des PR-Produktcodes nach `main`
sind dafür nötig. Sie hat keine Beta-/Release-/Main-/Patienten-Publish-Rechte.

**Grenzen:** Kein vollständiger Critical-/UI-/Geräte-PASS, keine vertrauenswürdige
Quell-Reproduzierbarkeit. Debug-Signaturschlüssel können je GitHub-Runner
abweichen; ein Update über eine frühere Preview-Installation kann deshalb
scheitern und eine Deinstallation erfordern (lokale Testdaten gehen verloren).
Nur mit synthetischen Testdaten nutzen. Für einen offiziell freigegebenen
APK-Kandidaten weiterhin `kgg-approved-pr-test-apk.yml` und dessen
Review-/Provenienzprüfungen verwenden.
