# Workspace-Beweissicherung

Dieses Runbook beschreibt ausschließlich Inventur und beweissichere Erfassung.
Es erlaubt keine Bereinigung, Löschung, Verschiebung und kein
`git worktree prune`. Der aktive Arbeitsklon bleibt `C:\src\kgg`; der historische
Transferordner ist nur eine Quelle für eine spätere, ausdrücklich gestartete
Erfassung.

## Korrigierter belegter Altbestand vom 2026-08-10

Die historische Inventur nennt 40 unstaged geänderte Pfade und 39 untracked,
nicht ignorierte Einzeldateien. Das sind **79 zu erhaltende Statuspfade**, nicht
69. Zusätzlich wurden 0 staged Pfade und 0 Konflikte berichtet. Die fünf
unsauberen Worktrees dürfen vor einem abgeschlossenen Rettungslauf nicht
bereinigt werden.

Die nachfolgende Präzisierung unterscheidet 21 logische `.git`-Fundstellen von
20 physischen Git-Wurzeln; eine Fundstelle ist ein Junction-Alias. Sie gruppieren
sich in 7 gemeinsame Git-Verzeichnisse. Von den 20 physischen Worktrees wurden
15 als sauber und 5 als unsauber gemeldet.

Der ergänzende Audit weist außerdem drei **externe, unsaubere Abhängigkeiten**
gemeinsamer Git-Verzeichnisse aus: `therapist_live_scanner` mit 15 unstaged und
7 untracked Pfaden, den externen v360-Worktree mit 0 unstaged und 91 untracked
Pfaden sowie den Layout-Parser mit 3 unstaged und 1 untracked Pfad. Diese
Bestände sind ein Fail-closed-Stoppsignal: Sie müssen beim echten Audit
erreichbar und im Rettungspaket enthalten sein. Aus der Inventur folgt
ausdrücklich **keine Cleanup-Sicherheit**.

## Werkzeug

`release-pipeline/kgg_workspace_preservation.py` hat zwei strikt getrennte
Betriebsarten:

- `audit` liest den angegebenen Workspace und gibt die Inventur ausschließlich
  als JSON auf stdout aus.
- `capture` inventarisiert erneut und schreibt ausschließlich in ein neues
  `run-<UTC>`-Verzeichnis unter dem Rettungsziel. Ein partieller Lauf bleibt als
  verstecktes `.run-....partial-...` mit `CAPTURE_FAILED.txt` erkennbar und wird
  nie als vollständige Rettung ausgegeben.

Das Werkzeug dedupliziert physische Worktree-Wurzeln auch bei Junction-/Link-
Aliasen, gruppiert gemeinsame Git-Verzeichnisse und nimmt alle dort
registrierten erreichbaren Worktrees in die Inventur auf. Erfasst werden:

- JSON-Inventur mit Branch/Detached-HEAD, HEAD und getrennten Zählern für
  staged, unstaged, untracked, ignored und Konflikte,
- Git-Bundle und unabhängiger `--mirror`-Klon je gemeinsamem Git-Verzeichnis,
- byteweise physische Kopie jedes gemeinsamen Git-Verzeichnisses einschließlich
  Config, Hooks, Reflogs, unerreichbarer Objekte und lokaler LFS-Daten,
- byteweise physische Kopien externer Git-Alternates/Object-Stores und absolut
  konfigurierter externer LFS-Speicher,
- physische Kopien konfigurierter Hook-Verzeichnisse außerhalb bereits
  erfasster Common-Git- und Worktree-Wurzeln,
- `git fsck --full --strict` für Quelle und Mirror sowie Bundle-Verifikation,
- eigenes HEAD-Bundle je Worktree, damit detached HEADs erhalten bleiben,
- roher Index, `.git`-Marker und separater Worktree-Adminzustand, damit auch
  Intent-to-add, Index-Flags und laufende Adminzustände beweisbar bleiben,
- rohe, hashverifizierte Bytes aller vorhandenen regulären getrackten
  Worktree-Dateien; damit bleiben auch Assume-unchanged, Skip-worktree sowie
  Clean-/EOL-Filterzustände unabhängig vom Patch sichtbar,
- binäre staged/unstaged Patches,
- untracked und ignored Dateien als verifizierte Kopien mit SHA-256 und Bytezahl,
- reguläre Dateien direkt im Workspace-Root als zweite verifizierte Kopie,
- sämtliche verschachtelten losen Dateien außerhalb auditierter Git-Wurzeln,
- eine abschließende `CAPTURE_SHA256.json` über alle Paketdateien einschließlich
  des vollständigen Git-Mirrors,
- eine Restore-Anleitung, die ausschließlich in neue Zielpfade restauriert.

Lange Windows-Pfade werden für direkte Dateioperationen mit Extended-Length-
Pfaden und für Git mit `core.longpaths=true` verarbeitet. Symlinks,
Reparse-Sonderdateien, nicht abgedeckte Links, Pfadfluchten, überschneidende Rettungsziele,
unzugängliche registrierte Worktrees, Konflikte mit nicht verlustfrei als Patch
rekonstruierbaren Index-Stufen, Quelländerungen während des Laufs sowie
fehlgeschlagene Hash-, Bundle- oder fsck-Prüfungen brechen `capture` ab.
Geerbte `GIT_*`-Variablen dürfen die explizit geprüften Quellpfade nicht auf
das Repository oder den Index eines aufrufenden Hooks umleiten und werden vor
jedem Git-Unterprozess bereinigt.

Vor jedem Git-Status- oder Diff-Aufruf prüft das Werkzeug die tatsächlich für
getrackte, untracked und ignored Pfade gesetzten `filter`-Attribute. Sobald für
einen verwendeten Treiber `clean`, `smudge` oder `process` konfiguriert ist,
bricht der Lauf ab, bevor der Treiber gestartet werden kann. Nur global
konfigurierte, im jeweiligen Worktree aber nicht aktivierte Treiber (zum
Beispiel Git LFS ohne passende Attribute) sind zulässig. Eltern-Worktrees
fragen den Submodule-Status nicht rekursiv ab; jedes entdeckte Submodule oder
verschachtelte Repository wird stattdessen als eigene Quelle vorgeprüft und
erfasst.

`CAPTURE_COMPLETE.txt` entsteht erst im bereits final benannten
`run-<UTC>`-Verzeichnis und wird dort atomar aus einem Pending-Marker
veröffentlicht. Scheitert die Verzeichnispromotion oder die Marker-Promotion,
bleibt ausschließlich ein Fehlernachweis zurück; der Lauf darf dann nicht als
vollständig behandelt werden.

## Aufruf

Nur lesende Inventur:

```powershell
python release-pipeline\kgg_workspace_preservation.py audit `
  --workspace "<historischer Transferordner>"
```

Späterer Rettungslauf nach manueller Prüfung des Audit-JSON:

```powershell
python release-pipeline\kgg_workspace_preservation.py capture `
  --workspace "<historischer Transferordner>" `
  --rescue-root "C:\KGG_RESCUE\2026-08-10"
```

Für den Implementierungs- und Testschritt wird der zweite Befehl ausdrücklich
nicht gegen das echte Archiv ausgeführt.

## Grenzen und manuelle Prüfungen

Die physische Git-Kopie erfasst reguläre Datei-Inhalte, aber keine belastbare
Wiederherstellung von NTFS-ACLs, Alternate Data Streams, Sparse-/Hardlink-
Metadaten oder Zeitstempeln. Links, Reparse Points und Spezialdateien außerhalb
eines deduplizierten Worktree-Alias brechen deshalb ab. Warnungen oder ein
partielles Paket sind kein ausreichendes Backup. Auch ein vollständiges Paket
begründet keine Cleanup-Sicherheit: Es braucht eine zweite physische Kopie,
einen Offline-Hashvergleich und eine manuelle Restore-Probe.

Der Quellbestand muss während Audit und Capture ruhen. Die Filterprüfung wird
unmittelbar vor den relevanten Git-Aufrufen wiederholt und die Quelle am Ende
erneut inventarisiert und gehasht; eine gleichzeitig absichtlich veränderte
Git-Konfiguration oder `.gitattributes` kann jedoch nicht atomar gegen alle
Git-Lesevorgänge verriegelt werden. Ein solcher paralleler Schreibzugriff macht
den Lauf ungültig und erfordert einen neuen Audit- und Capture-Durchlauf.
