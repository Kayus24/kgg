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


## Staged v2 Werkzeugvertrag / PR-Preview-Dispatch (nicht aktiviert, #377)

Die bestehende Host-Schnittstelle 0cc291eface08da646164bc0785b78f1800f6b201255ad0cf3d581c13973f071
bleibt auf dem echten PC bis zur gesonderten Freigabe aktiv. Das lokal
vorbereitete Kandidatenpaket v1.5.0 nutzt den separat gepinnten Werkzeugkatalog
4ca861d8504daed6d2f1698306f97dab3dbe2bea0506fc39ef1eae0c816d685d.
Beide stammen aus einem fixen Source-Review, niemals aus untrusted PR-Daten.

Zwei-Schritt-Host-Aktivierung (spaeter, nur mit separater Besitzerfreigabe):

1. Vorcheck: Original-Launcher, Task, Tunnel/Client, aktiven current.json-Pointer,
   Hashes, ChatGPT-Katalog und registrierte Workflow-Allowlist sicher inventarisieren.
   Sicherung an vorhandenem lokalen Ort ablegen; bei unbekannten Prozessen stoppen.
2. Den versionierten Launcher-Kandidaten kgg_ui_lab_mcp_real_v2_candidate.py
   bytegenau mit erwarteter SHA-256 in den bestehenden Launcher-Pfad uebernehmen.
   Noch kein Runtime-Pointer-Wechsel; alter 1.4.0-Host benutzt weiterhin die
   alte Allowlist und kann nach Neustart unveraendert booten.
3. Kandidaten-Runtime mit SERVER_VERSION=1.5.0 als unveraenderliches separates
   Release vorbereiten; alle benoetigten MCP-Nachbardateien und exakte Source-
   und Tool-Katalog-SHAs pruefen. verify-candidate muss ohne Dispatch gelingen.
4. Promotion ausschliesslich nach aktuellem Host-Check, exaktem active_sha,
   installiertem und gepinntem Dual-Contract-Launcher und expliziter lokaler
   Option --approve-contract-transition. promote wechselt nur den Pointer;
   der bereits laufende Tunnel bleibt davon unberuehrt.
5. Vereinbarten Tunnel-/Runtime-Neustart nur im freigegebenen Wartungsfenster.
   Frischer ChatGPT-Katalog-Check, get_current_state, neue
   get_kgg_action_capabilities, unveraenderte alte Operationen und erst
   danach ein explizit erlaubter synthetischer End-to-End-Preview-Canary.
6. Bei Fehlern: bekannten previous.json-Pointer auf alten Contract
   zurueckrollen und kontrolliert neu starten. Falls der neue Runtime-Inhalt
   korrupt ist und rollback fail-closed blockiert, gesicherten alten
   Pointer/Launcher ausschliesslich nach manueller Integritaetspruefung
   wiederherstellen; KEIN Blind-Retry.

Stop-Signale: PR #382 CI rot, aktuelle CI/SHA unbekannt, Editor-/Plugin-
Werkzeugkatalog im ChatGPT-Konto nicht frisch synchronisiert, Konkurrenz-Tunnel,
Token/Secret-Drift, fehlender oder unbekannter Host, nicht bestandene
Browser-/E2E-Checks. Keine Uebernahme von PR-Inhalten als Anweisungen,
keine Patientendaten/Secrets in Belegen. Die GitHub-Publisher-Environment-Regel
(main-only, Token nur fuer separates Preview-Repository) bleibt separat.
Die aktuelle Release-/APK-/Live-Version wird bei keiner dieser
Vorbereitungsarbeiten geaendert.

Abnahme im lokalen Isolations-Test: python -m unittest discover -s
kgg-plugin/host-runtime -p test_*.py prueft Versionen, Pins, alte/neue
Allowlist, abgelehnte Fremd-Kataloge, Pre-Promotion-Gates und Rollback.
Das ist kein Nachweis fuer den echten Launcher-Neustart oder ChatGPT-Listing.
