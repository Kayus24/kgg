# KGG Therapeuten-App: modulare Quelle

Dieser Ordner ist die editierbare Quelle fuer `../index.html`. Browser und
Android-WebView laden weiterhin genau eine in sich geschlossene HTML-Datei.
Die Fragmente sind reine Build-Module und werden nie einzeln ausgeliefert.

## Befehle

```powershell
python release-pipeline/build_therapist_source.py --check
python release-pipeline/kgg_selftest_build.py --smart
python release-pipeline/kgg_selftest_build.py --certify
python release-pipeline/kgg_selftest_build.py --watch
```

Der Self-Test-Build baut transaktional: Kandidat einsetzen, Tests ausfuehren,
bei Fehler automatisch die letzte funktionierende `index.html` und
`version.json` wiederherstellen. `--smart` waehlt anhand von
`test-impact.json` zusaetzliche Tests; `--certify` startet die volle Batterie.
Berichte und Screenshots landen ausschliesslich unter `tmp/kgg-selftest/`.

Die Reihenfolge in `parts.json` ist laufzeitrelevant. Alle dort gelisteten
Fragmente ergeben byteweise die Laufzeitdatei. `sourceRoles.documentTitle` und
`sourceRoles.runtimeIdentity` zeigen auf die Fragmente, in denen der Scaffolder
Titel beziehungsweise `VERSION`/`KGG_BUILD_INFO` aktualisiert; diese Rollen
muessen immer auf Eintraege aus `parts` zeigen. `index.html` nie direkt
bearbeiten.

Eine groessere Quelldatei darf nur mit einem vorab geprueften Split-Plan
zerlegt werden. Jeder Anchor muss exakt einmal vorkommen, die Anchors muessen in
Quellreihenfolge stehen und die neue Verkettung muss byteidentisch bleiben:

```powershell
python release-pipeline/kgg_split_therapist_source.py --plan <plan.json> --check
python release-pipeline/kgg_split_therapist_source.py --plan <plan.json> --write
```

Der Writer ersetzt einen zusammenhaengenden Bereich aus `sourceParts` durch die
angegebenen `segments`, aktualisiert explizite `sourceRoleUpdates` und rollt bei
jedem Fehler Manifest, Quellteile und neue Dateien vollstaendig zurueck.

## Neuen Patch vorbereiten

```powershell
python release-pipeline/kgg_new_patch.py `
  --slug beispiel-fix `
  --title "Beispiel Fix" `
  --summary "Kleinste beabsichtigte Aenderung." `
  --area "UI"
```

Der Scaffolder erhoeht die Version, erzeugt Marker/Fragment und aktualisiert
Source-Truth, Changelog, Patch-Regeln, Build-Identitaet, Manifest und Hash als
eine validierte Transaktion. Geschuetzte Bereiche brauchen
`--allow-protected` plus `--approval-note`.

Der vollstaendige Changelog-Stand bis v062 liegt unveraendert als versionierter
Snapshot unter `docs/changelog-archive/`. In den Laufzeit-Metadaten bleiben v063
und die 14 neuesten Vorgaenger, damit normale Patches wieder ohne Overflow-
Override scaffoldbar sind. Der Archiv-Contract prueft Snapshot-Hash, Reihenfolge
und die lueckenlose Ueberlappung mit dem eingebetteten Fenster.
