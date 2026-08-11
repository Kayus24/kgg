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

Der echte Read-only-Audit am 2026-08-11 erweiterte diese historische Sicht auf
alle registrierten Abhängigkeiten: 21 logische Git-Fundstellen, 36 physische
Worktrees in 7 gemeinsamen Git-Verzeichnissen, davon 28 sauber und 8 unsauber.
Er belegte 196 Dirty-Pfade (0 staged, 58 unstaged, 138 untracked), 0 Konflikte,
13.736 ignored Dateien, 13.970 getrackte Pfade, 106 reguläre Dateien direkt im
Workspace-Root und 432 weitere lose Dateien außerhalb auditierter Git-Wurzeln.
Der Audit endete ohne Warnung; die höheren Zahlen entstehen durch die bewusst
mitinventarisierten extern registrierten Worktrees und ignored/losen Bestände.

## Belegter historischer Objektdefekt

Der erste reale Capture-Lauf am 2026-08-11 stoppte korrekt bei
`KGG_MODULE_SANDBOX\.git`: Commit
`ecf2e61c9579ebfb157e7169f10de1119f7a9ec9` verweist auf den dort fehlenden
Parent `a348c7153884ef161af8aff9dcaa21968b79ed49`. Die vollständige erreichbare
Closure benötigt 265 im Archiv fehlende Objekte (94 Commits, 97 Trees und 74
Blobs; 638.358 Rohbytes). SHA-256 der sortierten OID-Liste einschließlich
Abschluss-Newline ist
`c45474664ff5fd2b88bcbb35df0c1a9114b4e82b213abc2e6b71815de2b9dfce`.

Der aktive Klon `C:\src\kgg` enthält alle diese Objekte, besteht
`git fsck --full --strict` und führt den fehlenden Commit weiterhin erreichbar
über `origin/main`. Er darf deshalb beim Capture ausschließlich lesend als
Recovery-Objektanbieter dienen. Das Archiv selbst wird nicht ergänzt oder
repariert: Seine physische Git-Kopie bleibt bytegenau defekt. Ein separates
Rescue-Overlay enthält die vollständige fehlende Teilmenge; die normalen Refs
werden im Bundle/Mirror und abweichende Worktree-HEADs in eigenen Bundles ohne
Anbieter verifiziert.

## Werkzeug

`release-pipeline/kgg_workspace_preservation.py` hat zwei strikt getrennte
Betriebsarten:

- `audit` liest den angegebenen Workspace und gibt die Inventur ausschließlich
  als JSON auf stdout aus.
- `capture` inventarisiert erneut und schreibt ausschließlich in ein neues
  `run-<UTC>`-Verzeichnis unter dem Rettungsziel. Ein partieller Lauf bleibt als
  verstecktes `.run-....partial-...` mit `CAPTURE_FAILED.txt` erkennbar und wird
  nie als vollständige Rettung ausgegeben.

Wenn ein Quell-`fsck` an fehlenden erreichbaren Objekten scheitert, bleibt
`capture` ohne `--recovery-object-repo` fail-closed. Mit einem angegebenen
fsck-grünen Anbieter werden alle vom Roh-`fsck` gemeldeten fehlenden Wurzeln
samt vollständiger Objekt-Closure ermittelt. Die im Quell-Objektspeicher
tatsächlich fehlende Teilmenge wird als lokales Rescue-Overlay geschrieben und
einzeln durch Git-OID, Typ, Bytezahl und SHA-256 belegt. Repository- und
Worktree-Bundles werden jeweils in einem leeren Bare-Repository ohne den
Anbieter verifiziert; der endgültige Mirror wird ausschließlich aus dem
Repository-Bundle erzeugt, gegen Quell-Refs und HEAD verglichen und besteht
anschließend `fsck` ebenfalls ohne Alternate. Anbieter mit Git-Alternates oder
Partial-/Promisor-Konfiguration werden abgelehnt; `GIT_NO_LAZY_FETCH=1`
verhindert implizite Netz-Nachladungen. `CAPTURE_COMPLETE.txt` trägt in diesem
Fall ausdrücklich `PASS_WITH_RECOVERED_SOURCE_DEFECTS`.

Das Werkzeug dedupliziert physische Worktree-Wurzeln auch bei Junction-/Link-
Aliasen, gruppiert gemeinsame Git-Verzeichnisse und nimmt alle dort
registrierten erreichbaren Worktrees in die Inventur auf. Erfasst werden:

- JSON-Inventur mit Branch/Detached-HEAD, HEAD und getrennten Zählern für
  staged, unstaged, untracked, ignored und Konflikte,
- Git-Bundle und ein ausschließlich daraus erzeugter, selbständiger
  `--mirror`-Klon je gemeinsamem Git-Verzeichnis,
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
  --rescue-root "C:\KGG_RESCUE\2026-08-10" `
  --recovery-object-repo "C:\src\kgg"
```

Wenn nach erfolgreichem Preflight bereits ein partielles Ziel angelegt wurde,
bleibt es als eigener Fehlernachweis bestehen und wird weder überschrieben noch
als Basis eines späteren Laufs verwendet. Audit- oder Provider-Preflight-Fehler
brechen dagegen bewusst ab, bevor überhaupt ein Rescue-Root entsteht.

## Grenzen und manuelle Prüfungen

Die physische Git-Kopie erfasst reguläre Datei-Inhalte, aber keine belastbare
Wiederherstellung von NTFS-ACLs, Alternate Data Streams, Sparse-/Hardlink-
Metadaten oder Zeitstempeln. Links, Reparse Points und Spezialdateien außerhalb
eines deduplizierten Worktree-Alias brechen deshalb ab. Warnungen oder ein
partielles Paket sind kein ausreichendes Backup. Auch ein vollständiges Paket
begründet keine Cleanup-Sicherheit: Es braucht eine zweite physische Kopie,
einen Offline-Hashvergleich und eine manuelle Restore-Probe.

Der Quellbestand und ein angegebener Recovery-Objektanbieter müssen während
Audit und Capture ruhen. Die Filterprüfung wird
unmittelbar vor den relevanten Git-Aufrufen wiederholt und die Quelle am Ende
erneut inventarisiert und gehasht; eine gleichzeitig absichtlich veränderte
Git-Konfiguration oder `.gitattributes` kann jedoch nicht atomar gegen alle
Git-Lesevorgänge verriegelt werden. Ein solcher paralleler Schreibzugriff macht
den Lauf ungültig und erfordert einen neuen Audit- und Capture-Durchlauf.

Recovery setzt voraus, dass der anfängliche Read-only-Audit jeden Worktree und
seinen aktuellen HEAD noch lesen kann. Fehlt bereits das direkte HEAD-Objekt,
kann Git keinen verlässlichen Status- oder Diff-Snapshot mehr liefern; der Audit
bricht dann bewusst vor dem Capture ab. Der Objektanbieter wird nicht benutzt,
um einen nicht auditierbaren Quell-Worktree scheinbar gesund zu machen. Dieser
Fall benötigt eine separate forensische Einzelrettung und darf nicht bereinigt
werden.
