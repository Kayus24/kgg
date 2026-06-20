# update-inbox

Dieser Ordner ist die Upload-Inbox für kleine KGG-App-Updates.

Künftiger Ablauf für Max:

1. `patch.py` hier hochladen.
2. `release.json` hier hochladen.
3. Beides nach `main` committen.
4. GitHub Action `Apply Update Inbox` erledigt automatisch:
   - `kgg-update/index.html` patchen
   - Doctype auf exakt `<!doctype html>` normalisieren
   - `versionCode` in `kgg-update/version.json` um 1 erhöhen
   - `versionName` aus `release.json` übernehmen
   - SHA-256 von `kgg-update/index.html` berechnen
   - `kgg-update/version.json` aktualisieren
   - nur erlaubte Ziel-Dateien committen

## Erwartetes `release.json`

```json
{
  "versionName": "1.0.4-kurzer-name",
  "notes": "Kurze Beschreibung des Updates."
}
```

## Erwartetes `patch.py`

- wird aus dem Repository-Root ausgeführt
- darf `kgg-update/index.html` verändern
- darf optional `docs/APP_STATE.md` verändern
- darf keine Secrets/API-Keys enthalten
- darf PDF, QR-Erzeugung, Patienten-App, Scan-Kamera, Parser, Android-Wrapper, Tablet-Layout, Plan-State und Storage nicht anfassen

Verfügbare Umgebungsvariablen:

```bash
KGG_INDEX_HTML=kgg-update/index.html
KGG_VERSION_JSON=kgg-update/version.json
KGG_RELEASE_JSON=update-inbox/release.json
```

Die Action blockiert automatisch, wenn der Patch andere Dateien verändert als:

- `kgg-update/index.html`
- `kgg-update/version.json`
- `docs/APP_STATE.md`
