# KGG UI Lab – Host-Runtime-Zeiger und Rollback

Bezug: GitHub-Issue #352. Kein Plugin-Tool-Schema-, Produkt- oder Runtime-Starttask-Umbau.

## Bestehenden Schutz beibehalten

Der Host-Windows-Task nutzt bereits den stabilen Launcher kgg_ui_lab_mcp_real.py. Dieser liest C:\src\kgg-runtime\ui-lab\current.json und prüft Release-Dateihash, SemVer, Pfad und fixierten Tool-Vertrag. Der vorhandene ChatGPT-Katalog und Tunnel bleiben unverändert.

Der ergänzende manage_runtime.py verwaltet ausschließlich das bestehende Pointer-Format:
- status verifiziert die aktuell adressierte Serverdatei, Version und Tool-Liste.
- verify-candidate prüft eine separat vorbereitete Runtime samt unabhängig gepinntem SHA-256.
- promote verlangt außerdem den erwarteten aktuellen Zeiger-SHA und schützt gegen parallele Updates mit begrenztem Dateilock. Schreibt previous.json und current.json per temp plus os.replace. Bei lokaler Nachprüfung mit Fehler wird der Pointer zurückgestellt.
- rollback schaltet nur auf einen zuvor validierten previous.json-Pointer zurück.

Vergleich Desktop-Commander-Klon: Hash-/Dependency-Pinning, fail-closed bei Drift, getrenntes Staging, keine blinde Wiederholung unklarer Writes. Der separate Klon-Worktree und sein Startweg wurden nicht geändert.

## Host-Rollout (nur in einem autorisierten Wartungsfenster)

1. Neue freigegebene vollständige Runtime als eigenes unveränderliches Verzeichnis unter C:\src\kgg-runtime\ui-lab\<RELEASE>\mcp\server.py vorbereiten. Quell-SHA-256 aus dem überprüften Release/Repo erhalten und separat angeben. Nie die aktive Runtime in-place bearbeiten.
2. Mit dem Python-Host-Interpreter und manage_runtime.py den Befehl status aufrufen, current active_sha sichern. Dann verify-candidate --release RELEASE --server-sha256 SHA aufrufen.
3. Nur nach bestandenem Check den Befehl promote --release RELEASE --server-sha256 SHA --expect-active-sha256 CURRENT_SHA aufrufen. Ein abweichender Tool-Katalog blockiert den Vorgang.
4. Erst nach Prozess-/User-Abstimmung genau den verwalteten KGG-Tunnel kontrolliert neu starten. Die Zeigerumschaltung aktualisiert den bereits laufenden Prozess NICHT von selbst.
5. Neu prüfen: Windows-Aufgabe, Singleton-Tunnel, ready/healthy, frischer ChatGPT-Aufruf get_current_state, bei UI-Änderungen realer Browser-Canary. Wenn Live-Check fehlschlägt, Pointer zuerst unabhängig lesen, dann rollback --expect-active-sha256 ACTUAL_CURRENT_SHA und nach kontrolliertem Restart erneut prüfen.
6. Bei UNKNOWN Write-Zustand niemals denselben Promote/Rollback blind wiederholen. Zunächst status, Pointer und Prozesse unabhängig abfragen. Vorherige Release-Dateien bis zur verifizierten Abnahme behalten.

Keine erhöhte Berechtigung, kein GitHub-Merge/Release, keine Änderung an den ChatGPT-Tool-Kontrakten. Anders als ein automatisches Live-Health-Rollback testet dieser Code zunächst nur die lokale Dateikonsistenz und die Tool-Kompatibilität. Für Live-Ausfall braucht es einen expliziten Host-Rollback und erneute Health-Verifikation.

## Abnahme

Unit-Tests mit temporären, synthetischen Runtime-Verzeichnissen:
python -m unittest discover -s kgg-plugin/host-runtime -p test_manage_runtime.py -v

Read-only Abgleich mit aktueller installierter Runtime:
python kgg-plugin/host-runtime/manage_runtime.py status

Ein neuer produktiver Versionswechsel, Android-QR-Kamera, installierte PWA-Links und die dynamische Recovery nach fehlerhaftem Live-Restart sind damit ausdrücklich NOT_RUN.
