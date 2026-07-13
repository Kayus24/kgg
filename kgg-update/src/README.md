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

Die Reihenfolge in `parts.json` ist laufzeitrelevant. `base-head.html`, die
Fragmente unter `metadata/`, `base-app.html`, die versionierten Patches und
`footer.html` ergeben byteweise die Laufzeitdatei. `index.html` nie direkt
bearbeiten.

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

Der eingebettete Changelog liegt in der aktuellen Basis bereits ueber seinem
konfigurierten Limit (31 statt 30 Eintraege). Darum blockiert der Scaffolder
standardmaessig. Keine Historie wird automatisch geloescht; bis zu einer
freigegebenen Archivierung ist ein bewusster Override mit
`--allow-changelog-overflow --approval-note "..."` erforderlich.
