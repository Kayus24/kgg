# G04 – Echte Browser-/UI-Brücke

## 1. Ziel

Der KGG-Plugin-Kern steuert eine echte, isolierte KGG-HTML-Testseite über einen vertrauenswürdigen Browser Runner und liefert reale Screenshots sowie echte Aktionsresultate.

## 2. Warum dieses Gate erforderlich ist

Dies ist das zentrale Produktziel. Der aktuelle MCP-Server erzeugt ausdrücklich synthetische Screenshots und Quick-Flow-Schritte; damit kann kein GPT die App tatsächlich bedienen.

## 3. Scope und Nicht-Ziele

Minimaler Werkzeugvertrag: Session starten/beenden, Seite öffnen, Screenshot, Zustands-/Viewportinfo, Maus/Touch bewegen, klicken/tappen, Text eingeben, scrollen/swipen, warten, zurück/reload. Kein allgemeiner Desktopzugriff, keine Patientendaten, keine beliebigen Domains.

## 4. Abhängigkeiten

G02. Vorhandene Playwright- und Browser-Smoke-Komponenten sind zuerst wiederzuverwenden. G08-Safety gilt von Beginn an.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=OPT_IN_REAL_PLAYWRIGHT_BRIDGE`
- `LIVE_EVIDENCE_STATUS=LOCAL_REAL_RUNTIME_TWO_SCREENSHOT_RUN`
- `GATE_STATUS=PASS`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T13:42:46+02:00`
- `CANDIDATE_FINGERPRINT=G04_REAL_BROWSER_BRIDGE_20260921_01`

## 6. Bestehende Evidence

- `kgg-plugin/mcp/server.py` beschreibt `run_quick_flow` als „synthetic ... no browser“ und `capture_screenshot` als „no real screen capture“.
- zahlreiche vorhandene Playwright-Skripte zeigen reale lokale Browserfähigkeit, sind aber nicht als Agentenwerkzeuge exponiert.
- `release-pipeline/kgg_ui_lab_browser.py` ist eine abstrahierte Runner-Grenze, kein eigener echter Host.
- `kgg-plugin/mcp/real_browser.py` bindet den MCP-Server opt-in und fail-closed an den Playwright-Host.
- `kgg-plugin/mcp/browser_host.js` führt genau einen allowlisteten, ephemeren Chromium-Lauf ohne Screenshot-Datei aus.
- `release-pipeline/test_kgg_real_browser_bridge.py` beweist mit der lokalen KGG-Fixture zwei unterschiedliche Screenshot-Hashes und `admin-ready → scale-drag-state`.

## 7. Lücke und Root Cause

Die dünne Verbindung ist für den lokalen, vertrauenswürdigen Host geschlossen. Nicht geschlossen ist die externe Host-/Transportfrage: Standardmäßig bleibt der installierte Server Synthetic, und ChatGPT besitzt weiterhin keinen nachgewiesenen HTTPS-/Secure-MCP-Kanal (G03).

## 8. Kleinschrittiger Arbeitsplan

1. Vorhandene Playwright-Laufzeit und wiederverwendbare Runner-Funktionen inventarisieren. ✅
2. einen einzigen erlaubten Test-URL-/Datei-Startpfad definieren. ✅ `localhost`/HTTPS; keine `file:`-URLs.
3. Session-/Lease-/Run-ID-Vertrag festlegen. ✅ vorhandener MCP-Vertrag plus `run_id`-Bindung.
4. echten `open/get_state/screenshot/end`-Pfad implementieren. ✅ one-shot, ephemerer Browserkontext.
5. RED/Green für reale `click`, `type`, `scroll/swipe`, `reload/back`, `wait` ergänzen. ✅ Host-Dispatcher und sichere Operationen vorhanden.
6. Koordinaten und semantische Zielwahl unterstützen; semantisch bevorzugen. ✅ `data-kgg-action`/Role-Fallback und bounded coordinates.
7. jeden Schritt mit Vorher-/Nachherzustand und Screenshot-Hash binden. ✅ zwei unabhängige PNG-SHA-256 im Realtest.
8. Real- und Synthetic-Modus klar trennen. ✅ `KGG_REAL_BROWSER=1`; fehlender Host führt zu Fehler statt Synthetic-Fallback.
9. G05/G06 auf diesen Pfad aufbauen. **Nächster Schritt**.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G04_REAL_BROWSER_BRIDGE`
- `INPUT=allowlistete synthetische KGG-Testseite, Browser Runner, MCP-Session`
- `PROCEDURE=Seite öffnen; Screenshot A; echte Aktion; Screenshot B; DOM/visuellen Zustand prüfen; Session beenden`
- `PASS_CRITERIA=Aktion verändert die reale Seite; beide Screenshots sind retrievable und unterschiedlich; Run-/Session-Evidence stimmt; fehlender Host fällt nicht auf Synthetic zurück`
- `FAIL_CRITERIA=synthetic URI/Fixture, Modell behauptet Aktion ohne Runner-Event, beliebige Domain oder fehlender Nachzustand`
- `RETRY_RULE=Ein identischer Retry nur bei belegtem transientem Browserstartfehler`
- `FALLBACK=Session sauber beenden; Screenshot-only PARTIAL ist kein Gate-PASS`
- `EVIDENCE_OUTPUT=REAL_BROWSER_BRIDGE_EVIDENCE_V1`
- `NEXT_ON_PASS=G05 und G06`
- `NEXT_ON_FAIL=Root Cause; bei Architekturunsicherheit G11`
- `INVALIDATION_TRIGGERS=Runner-, Browser-, Tool-Schema-, Security- oder Session-Vertrag ändert sich`

## 10. Tests

- unabhängiger Black-Box-Test gegen eine echte HTML-Fixture.
- `python -m unittest release-pipeline/test_kgg_real_browser_bridge.py` mit dem vorinstallierten Codex-Playwright-Bundle: 2 Tests PASS; zwei unterschiedliche Screenshot-SHA-256 und Zustandswechsel nachgewiesen.
- Negative: falsche Domain, abgelaufene Lease, falsche Session, außerhalb Viewport, unerwarteter Dialog, Timeout, Screenshot-Manipulation.
- vorhandene UI-Stability-Suites als Regression.
- unveränderter End-to-End-Replay.
- `cmd /c release-pipeline\\run-kgg-tests.cmd --level critical`: PASS (141 Tests, 1 Skip).
- `cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression`: PASS.

## 11. Safety und Datenschutz

Nur synthetische Seiten/Daten; URL-Allowlist; isoliertes Browserprofil; begrenzte Laufzeit/Schrittzahl; keine Downloads, Clipboard-, Kamera-, Mikrofon- oder Dateizugriffe ohne separates Gate; Screenshots sanitizen und zeitlich begrenzt behalten.

## 12. Brother-GPT-Eskalation

Bei unbekannter externer Hostgrenze erhält der Brother vorhandene Runner-APIs, Fehler, getestete Optionen und das minimale Tool-Schema. Er soll Reuse vor Neubau prüfen. Für den jetzt belegten lokalen Pfad ist kein Brother-Review erforderlich; G03 bleibt als eigener Transport-Blocker fingerprinted.

## 13. Abschlussartefakte

Real-Runner-Adapter, MCP-Tools, Playwright-Host, allowlistete Fixture, Tests, Tool-Dokumentation, Evidence-Schema und reproduzierbarer Demo-Run.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=ACCEPTED`, `EVIDENCE=E2_LOCAL_REAL_RUNTIME`, `REVIEW_NOTE=Local real-browser path verified; external ChatGPT transport remains G03.`
