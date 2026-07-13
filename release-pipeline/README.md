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

Windows-PC-Standardweg ohne GitHub-Schreibaktion:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --level critical
```

Der Wrapper sucht zuerst das Codex-Bundled-Python/Node und faellt danach auf System-Tools zurueck. Damit bleibt die Testbatterie auch dann startbar, wenn Windows `python` nur auf den Microsoft-Store-Alias zeigt.

Test-Hierarchie:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --level critical
cmd /c release-pipeline\run-kgg-tests.cmd --level regression
cmd /c release-pipeline\run-kgg-tests.cmd --level all
```

- `critical`: blockiert PRs; App-Start/Syntax, Version-Hash, Secret-Scan, Mobile-Inbox-Dry-run, Sync-Safety und Satz-Karten-Schutz.
- `regression`: critical plus groessere Sync-/Parser-Abdeckung und echte Browser-Gestenpruefung fuer riskante Aenderungen.
- `all`: alle nicht-live Tests plus optionale Comfort-Tests; mutierende Live-Tests bleiben extra geschuetzt.

Einzelne Batterien bleiben moeglich. Ohne `--level` laufen sie aus Kompatibilitaet wie bisher vollstaendig, aber ohne Live-GitHub-Schreibaktion:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --suite mobile-inbox
cmd /c release-pipeline\run-kgg-tests.cmd --suite sync
cmd /c release-pipeline\run-kgg-tests.cmd --suite native-sync
cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks
cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability
```

Registrierte Tests mit Kategorie und Begruendung anzeigen:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --level all --list
```

CI/Linux kann die Batterie weiterhin direkt mit Python starten:

```bash
python release-pipeline/kgg_test_battery.py --level critical
```

## Patch-Hygiene

### Modulare Therapeuten-Quelle

In der isolierten Modul-Sandbox wird `kgg-update/index.html` deterministisch aus
`kgg-update/src/parts.json` gebaut. Vor jedem Test oder Patch:

```powershell
python release-pipeline/build_therapist_source.py --check
```

Nach einer beabsichtigten Änderung an einem Fragment:

```powershell
python release-pipeline/build_therapist_source.py --write
```

Die Critical-Batterie führt `--check` automatisch aus. Die Patch-Hygiene
blockiert direkte Änderungen an der erzeugten `index.html`, wenn kein passendes
Quellfragment geändert wurde. Browser und Android laden weiterhin nur die eine
zusammengebaute HTML-Datei.

### Transaktionaler Self-Test-Build (nur Modul-Sandbox)

```powershell
cmd /c release-pipeline\run-kgg-selftest.cmd --smart
cmd /c release-pipeline\run-kgg-selftest.cmd --certify
cmd /c release-pipeline\run-kgg-selftest.cmd --watch
```

- `--smart`: Critical-Tests plus anhand `kgg-update/src/test-impact.json`
  ausgewaehlte Regressionstests.
- `--certify`: komplette lokale Critical-/Regression-Batterie inklusive echtem
  UI-/Funktionsvertrag auf Phone, Phone Landscape, Tablet Portrait, Tablet
  Landscape und Tablet Split-Screen.
- `--watch`: beobachtet die Quellfragmente und startet nach dem Speichern den
  Smart-Build.

Der Kandidat wird nur transaktional eingesetzt. Bei einem Testfehler stellt die
Pipeline die vorherige `index.html` und `version.json` wieder her. JSON-,
Markdown- und HTML-Berichte sowie Screenshots liegen unter
`tmp/kgg-selftest/`; dieser Ordner ist nicht versioniert.

Der lokale Hook unter `.githooks/pre-commit` blockiert Commits an Modulen und
Buildwerkzeugen, bis `--certify` gruen ist. Aktivierung in dieser Sandbox:

```powershell
git config core.hooksPath .githooks
```

Ein neuer Patch wird mit `release-pipeline/kgg_new_patch.py` vorbereitet. Das
Tool erhoeht die Zielversion, aktualisiert Metadaten und Manifest, baut die
HTML und berechnet den Hash. Geschuetzte Bereiche und das bereits erreichte
Changelog-Limit sind fail-closed und brauchen eine explizite Approval-Notiz.

Nach einem sauberen, zertifizierten Sandbox-Commit erzeugt
`release-pipeline/kgg_export_handoff.py` ein Review-Buendel unter
`tmp/kgg-selftest/handoff/`. Der Export blockiert Release-/Android-/Manifest-
Aenderungen, verlangt ein Repo ohne Remote und fuehrt weder Push noch
Produktionsfreigabe aus.

Vor den Release-Contracts laeuft ein schneller Hygiene-Check:

```powershell
python release-pipeline/kgg_test_battery.py --suite hygiene --level critical
```

Er blockiert typische schmutzige Chat-Patches:

- Branch basiert nicht auf aktuellem `origin/main` (`KGG_ALLOW_STALE_BRANCH=1` nur fuer bewusste Rettungsarbeiten).
- `therapist-app/test-lab/**` landet in einem normalen App-/Release-PR.
- `release-inbox/admin.html` und `release-inbox/release.json` sind nur halb vorhanden.
- `kgg-update/index.html` wurde geaendert, aber `kgg-update/version.json` fehlt oder der LF-normalisierte Hash passt nicht.
- Die Source-HTML ist neuer als die vorbereitete oder live Admin-Beta (`KGG_ALLOW_RELEASE_DRIFT=1` nur fuer explizite No-Release-PRs).

Ideen-Chats duerfen weiterhin lokal in `test-lab` experimentieren. Vor einem Release-PR werden diese Experimente aber auf einen frischen Branch uebernommen; `test-lab` wird nicht mitveroeffentlicht.

`sync`, `native-sync` und `textblocks` laden die echte Produktionslogik aus `kgg-update/index.html` in einem lokalen Node-Harness. Damit werden Sync-Safe-Export/Merge, Secret-Blockade, Native-Peer-Mesh-Regeln und Terminheld-/Satz-Textbloecke ohne Emulator geprueft.

## Native Sync Diagnose

Die Update-/Sync-Dialoge sollen sichtbar machen, ob die App wirklich ueber die Android-Bridge in einen gemeinsamen Sync-Raum schreibt oder nur im privaten Browser-Fallback arbeitet. Fuer schnelle Rueckmeldung gibt es:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --suite native-sync --level regression
```

Diese Batterie prueft:

- Safe-Sync-Dokumente bleiben `kgg_cross_data_safe_sync` und markieren `patients:false`, `secrets:false`.
- eigene Geraete werden beim Peer-Merge uebersprungen.
- nicht abonnierte Peers werden standardmaessig ignoriert und nur mit explizitem Import uebernommen.
- Tombstones loeschen entfernte Uebungen.
- verbotene Felder wie Tokens, API-Keys, Rohdaten oder Base64-Payloads werden blockiert.
- die vorhandene Android-Bridge bietet die erwarteten Methoden fuer Status, Lesen, Schreiben, Peer-Liste und Follow-Konfig.

In der Admin-App bleibt die sichere manuelle Uebergabe als Fallback: `Sync-Datei speichern` auf Geraet A, Datei auf Geraet B auswaehlen, `Sync-Datei importieren`. Das ersetzt keine spaetere Komfort-Automatik, macht den Datenuebergang aber testbar und ohne Secrets.

`ui-stability` ist der Schutz gegen Layout-/Flicker-Rueckschritte:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level critical
cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression
```

- `critical` prueft schnell und CI-sicher, ob die aktuellen Phone-Swipe-/Drag-Guards noch in der HTML stehen.
- `regression` startet die echte Admin-HTML im Phone-Viewport mit 30 Uebungskarten und testet danach per Browser-PointerEvents:
  - keine Auto-Navigation / kein Popup beim Boot,
  - Swipe bewegt eine Karte sichtbar und raeumt danach Klassen/Styles auf,
  - Scrollen vor dem Drag-Hold startet keinen Drag,
  - Drag/Drop ueber den Griff aendert die Karten-Reihenfolge und raeumt danach auf.

Nach jedem UI-Flicker-, Handy-Layout- oder Kartenanimations-Patch ist `ui-stability --level regression` Pflicht. Wenn Web/HTML gruen ist, die APK aber trotzdem haengt, ist der naechste Befund APK/WebView-spezifisch und nicht mehr Parser/Layout allgemein.

Nur wenn wirklich eine neue Admin-Beta erzeugt werden soll:

```powershell
cmd /c release-pipeline\run-kgg-tests.cmd --suite mobile-inbox --live-mobile-inbox
```

Wenn ein PR nur Test-/Pipeline-Dateien veraendert und bewusst keinen neuen Admin-Release vorbereitet, darf der Release-Drift-Guard explizit uebersprungen werden:

```powershell
$env:KGG_ALLOW_RELEASE_DRIFT='1'
cmd /c release-pipeline\run-kgg-tests.cmd --level critical --suite release
Remove-Item Env:\KGG_ALLOW_RELEASE_DRIFT
```

Ohne diesen Override blockiert `admin-release-drift`, sobald `kgg-update/index.html` neuer ist als der vorbereitete oder live referenzierte Admin-Release. Das ist bei App-Aenderungen beabsichtigt.

## Admin-Beta per PR vorbereiten

Auf dem Release-Branch liegen temporaer:

- `release-inbox/admin.html`
- `release-inbox/release.json` mit `releaseId`, `versionName` und `notes`

Der PR-Workflow validiert die Datei, erzeugt unveraenderliche Admin-/Kolleg:innen-Artefakte und entfernt die Inbox-Dateien vor dem Merge. Verbindliche UI-Basis ist `kgg-update/index.html` ab v24. Privilegierte DOM-/JavaScript-Bloecke werden beim Kolleg:innen-Build fail-closed entfernt. Neue Admin-Bloecke muessen zwischen `KGG_ADMIN_ONLY_START` und `KGG_ADMIN_ONLY_END` liegen.

## Freigabe und Rollback

`release-control.yml` erstellt fuer Promotion und Rollback immer einen eigenen PR. Ein Rollback erhoeht den Rollout-Code, zeigt aber auf ein bereits geprueftes unveraenderliches Artefakt.

## Kosten und Geheimnisse

Die Pipeline benoetigt nur GitHub Pages, Actions und eine auf dieses Repository begrenzte GitHub App. Tokens bleiben in GitHub beziehungsweise im Android Keystore. HTML, Manifest und Actions-Logs enthalten keine Tokens oder API-Keys.
