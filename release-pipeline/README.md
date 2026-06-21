# KGG Release Pipeline v2

Eine Release-Logik fuer drei gleichberechtigte Bedienwege:

- Admin-App per GitHub Device Flow
- Codex/GPT per GitHub-Connector oder `gh`
- GitHub Actions im Browser

Alle Schreibaktionen erzeugen einen Branch und Pull Request. `main` wird nicht direkt beschrieben.

## Admin-Beta vorbereiten

Auf dem Release-Branch liegen temporaer:

- `release-inbox/admin.html`
- `release-inbox/release.json` mit `releaseId`, `versionName` und `notes`

Der PR-Workflow validiert die Datei, erzeugt unveraenderliche Admin-/Kolleg:innen-Artefakte und entfernt die Inbox-Dateien vor dem Merge. Bestehende v389-Dateien bilden den konservativen Profil-Transformationsvertrag. Neue Admin-Bloecke muessen zwischen `KGG_ADMIN_ONLY_START` und `KGG_ADMIN_ONLY_END` liegen.

## Freigabe und Rollback

`release-control.yml` erstellt fuer Promotion und Rollback immer einen eigenen PR. Ein Rollback erhoeht den Rollout-Code, zeigt aber auf ein bereits geprueftes unveraenderliches Artefakt.

## Kosten und Geheimnisse

Die Pipeline benoetigt nur GitHub Pages, Actions und eine auf dieses Repository begrenzte GitHub App. Tokens bleiben in GitHub beziehungsweise im Android Keystore. HTML, Manifest und Actions-Logs enthalten keine Tokens oder API-Keys.
