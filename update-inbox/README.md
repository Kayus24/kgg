# update-inbox (stillgelegt)

Dieser Ordner ist ein historisches Archiv und kein aktiver Update-Eingang.
Die vorhandenen Dateien bleiben nur zur Nachvollziehbarkeit erhalten und dürfen
nicht als Release-Werkzeuge ausgeführt werden.

## Nicht verwenden

- Niemals `patch.py` oder `release.json` in diesen Ordner hochladen.
- Niemals Inhalte aus diesem Ordner direkt nach `main` committen.
- Niemals die historischen Skripte verwenden, um `kgg-update/index.html` direkt
  zu verändern.

## Aktueller Handy-Upload

1. Einen Branch namens `mobile-inbox` verwenden.
2. Genau eine neue oder geänderte Admin-HTML unter `mobile-inbox/` ablegen.
3. Diese eine HTML-Datei committen und den Branch pushen.
4. `.github/workflows/mobile-inbox-release.yml` validiert die Datei, erzeugt
   unveränderliche Release-Artefakte und öffnet einen Draft-Pull-Request.
5. Den Draft extern auf `Ready for review` setzen, den normalen Required Gate
   abwarten und nur bei grünen Checks manuell mergen.

Der Workflow startet oder bewertet aufgrund des `GITHUB_TOKEN` keine PR-Checks,
merged nicht selbst und veröffentlicht nichts durch einen direkten Commit auf
`main`.

## Normale Quellpatches

Quelländerungen entstehen auf einem eigenen Arbeitsbranch unter
`kgg-update/src/**`. `kgg-update/index.html` ist nur das erzeugte Ergebnis und
wird nicht direkt bearbeitet. Danach den Builder beziehungsweise das passende
Self-Test-Gate ausführen, den Branch pushen und die Änderung per Pull Request
integrieren:

```powershell
python release-pipeline/build_therapist_source.py --check
python release-pipeline/kgg_selftest_build.py --smart
```
