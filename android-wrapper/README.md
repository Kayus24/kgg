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
