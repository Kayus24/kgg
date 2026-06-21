# KGG Android Wrapper v2

Quellprojekt fuer die einmalig neu zu installierenden Admin- und Kolleg:innen-APKs. Danach werden HTML-Releases ueber die getrennten Kanaele in `therapist-app/android_update_manifest.json` geladen.

Der Admin-Flavor enthaelt zusaetzlich die native Release-Zentrale. GitHub-Tokens werden nur im Android Keystore gespeichert und niemals an die WebView weitergereicht. Der Kolleg:innen-Flavor kann keine Release-Aktionen aufrufen.

Buildvarianten:

- `assembleAdminDebug`
- `assembleKollegenDebug`
