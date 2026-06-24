# KGG Release Pipeline v2

Eine Release-Logik fuer drei gleichberechtigte Bedienwege:

- Mobile-Inbox per GitHub-Handy-Webseite
- Admin-App per GitHub Device Flow als Komfortweg
- Codex/GPT per GitHub-Connector oder `gh`
- GitHub Actions im Browser

Alle Schreibaktionen erzeugen einen Branch und Pull Request. `main` wird nicht direkt beschrieben.

## Handy-Standardweg ohne Codex

Die Admin-App speichert die aktuelle HTML lokal. Danach wird die Datei auf dem Branch `mobile-inbox` in den Ordner `mobile-inbox/` hochgeladen. Die Action `KGG Mobile Inbox Release` validiert die HTML gegen die aktuelle KGG-Basis, erzeugt automatisch `releaseId` und Release-Notiz, baut Admin-/Kolleg:innen-Artefakte und merged den geprueften PR.

Die Kolleg:innen-Freigabe passiert bewusst getrennt ueber `Promote latest KGG Admin beta`, damit eine Admin-Beta erst getestet werden kann.

## Mobile-Inbox Smoke automatisieren

Schneller Check ohne GitHub-Schreibaktion:

```powershell
python release-pipeline/mobile_inbox_live_smoke.py --dry-run
```

Der Dry-run nimmt die aktuelle Admin-HTML aus `origin/main`, prueft sie lokal wie ein Mobile-Inbox-Upload und baut die Release-Artefakte in einem temporaeren Clone. Es wird nichts gepusht, kein PR erstellt und `main` bleibt unveraendert.

Echter Live-Test:

```powershell
python release-pipeline/mobile_inbox_live_smoke.py
```

Der Live-Test braucht `gh auth login` mit Schreibrechten fuer `Kayus24/kgg`. Er schreibt absichtlich eine Smoke-HTML nach `mobile-inbox/KGG_MOBILE_INBOX_SMOKE.html`, wartet auf die Action `KGG Mobile Inbox Release` und prueft danach automatisch:

- Workflow ist gruen.
- ein neuer `[admin-beta] rNNNN ...` PR wurde erstellt und gemergt.
- `origin/main` enthaelt `therapist-app/releases/web/rNNNN/admin.html`.
- die GitHub-Pages-URL antwortet mit `200`.
- das Manifest zeigt Admin auf die neue Release, Kolleg:innen bleibt unveraendert.

Wichtig: Jeder Live-Test erzeugt bewusst eine neue Admin-Beta-Release. Er fuehrt keine Kolleg:innen-Freigabe aus.

## Lokale Test-Batterie

Schneller Gesamttest ohne GitHub-Schreibaktion:

```powershell
python release-pipeline/kgg_test_battery.py
```

Einzelne Batterien:

```powershell
python release-pipeline/kgg_test_battery.py --suite mobile-inbox
python release-pipeline/kgg_test_battery.py --suite sync
python release-pipeline/kgg_test_battery.py --suite textblocks
```

`sync` und `textblocks` laden die echte Produktionslogik aus `kgg-update/index.html` in einem lokalen Node-Harness. Damit werden Sync-Safe-Export/Merge, Secret-Blockade und Terminheld-/Satz-Textbloecke ohne Emulator geprueft.

Nur wenn wirklich eine neue Admin-Beta erzeugt werden soll:

```powershell
python release-pipeline/kgg_test_battery.py --suite mobile-inbox --live-mobile-inbox
```

## Admin-Beta per PR vorbereiten

Auf dem Release-Branch liegen temporaer:

- `release-inbox/admin.html`
- `release-inbox/release.json` mit `releaseId`, `versionName` und `notes`

Der PR-Workflow validiert die Datei, erzeugt unveraenderliche Admin-/Kolleg:innen-Artefakte und entfernt die Inbox-Dateien vor dem Merge. Verbindliche UI-Basis ist `kgg-update/index.html` ab v24. Privilegierte DOM-/JavaScript-Bloecke werden beim Kolleg:innen-Build fail-closed entfernt. Neue Admin-Bloecke muessen zwischen `KGG_ADMIN_ONLY_START` und `KGG_ADMIN_ONLY_END` liegen.

## Freigabe und Rollback

`release-control.yml` erstellt fuer Promotion und Rollback immer einen eigenen PR. Ein Rollback erhoeht den Rollout-Code, zeigt aber auf ein bereits geprueftes unveraenderliches Artefakt.

## Kosten und Geheimnisse

Die Pipeline benoetigt nur GitHub Pages, Actions und eine auf dieses Repository begrenzte GitHub App. Tokens bleiben in GitHub beziehungsweise im Android Keystore. HTML, Manifest und Actions-Logs enthalten keine Tokens oder API-Keys.
