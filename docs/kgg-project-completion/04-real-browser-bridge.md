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

- `IMPLEMENTATION_STATUS=SYNTHETIC_ADAPTER_ONLY`
- `LIVE_EVIDENCE_STATUS=NO_REAL_BROWSER_CHANNEL`
- `GATE_STATUS=FAIL`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

- `kgg-plugin/mcp/server.py` beschreibt `run_quick_flow` als „synthetic ... no browser“ und `capture_screenshot` als „no real screen capture“.
- zahlreiche vorhandene Playwright-Skripte zeigen reale lokale Browserfähigkeit, sind aber nicht als Agentenwerkzeuge exponiert.
- `release-pipeline/kgg_ui_lab_browser.py` ist eine abstrahierte Runner-Grenze, kein eigener echter Host.

## 7. Lücke und Root Cause

Es fehlt die dünne, kontrollierte Verbindung zwischen MCP-Aufrufen und einem echten Browserkontext. Die bisherigen Contract- und Synthetic-Arbeiten validierten Formate, nicht die Realfunktion.

## 8. Kleinschrittiger Arbeitsplan

1. Vorhandene Playwright-Laufzeit und wiederverwendbare Runner-Funktionen inventarisieren.
2. einen einzigen erlaubten Test-URL-/Datei-Startpfad definieren.
3. Session-/Lease-/Run-ID-Vertrag festlegen.
4. zunächst echten `open/get_state/screenshot/end`-Pfad implementieren.
5. RED/Green für reale `click`, `type`, `scroll/swipe`, `reload/back`, `wait` ergänzen.
6. Koordinaten und semantische Zielwahl beide unterstützen; semantisch bevorzugen, Koordinaten als echte Fallbackfähigkeit behalten.
7. jeden Schritt mit Vorher-/Nachherzustand und Screenshot-Hash binden.
8. MCP-Toolbeschreibungen klar in `real` und `synthetic_fixture` trennen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G04_REAL_BROWSER_BRIDGE`
- `INPUT=allowlistete synthetische KGG-Testseite, Browser Runner, MCP-Session`
- `PROCEDURE=Seite öffnen; Screenshot A; echte Aktion; Screenshot B; DOM/visuellen Zustand prüfen; Session beenden`
- `PASS_CRITERIA=Aktion verändert die reale Seite; beide Screenshots sind retrievable und unterschiedlich; Run-/Session-Evidence stimmt`
- `FAIL_CRITERIA=synthetic URI/Fixture, Modell behauptet Aktion ohne Runner-Event, beliebige Domain oder fehlender Nachzustand`
- `RETRY_RULE=Ein identischer Retry nur bei belegtem transientem Browserstartfehler`
- `FALLBACK=Session sauber beenden; Screenshot-only PARTIAL ist kein Gate-PASS`
- `EVIDENCE_OUTPUT=REAL_BROWSER_BRIDGE_EVIDENCE_V1`
- `NEXT_ON_PASS=G05 und G06`
- `NEXT_ON_FAIL=Root Cause; bei Architekturunsicherheit G11`
- `INVALIDATION_TRIGGERS=Runner-, Browser-, Tool-Schema-, Security- oder Session-Vertrag ändert sich`

## 10. Tests

- unabhängiger Black-Box-Test gegen eine echte HTML-Fixture.
- Negative: falsche Domain, abgelaufene Lease, falsche Session, außerhalb Viewport, unerwarteter Dialog, Timeout, Screenshot-Manipulation.
- vorhandene UI-Stability-Suites als Regression.
- unveränderter End-to-End-Replay.

## 11. Safety und Datenschutz

Nur synthetische Seiten/Daten; URL-Allowlist; isoliertes Browserprofil; begrenzte Laufzeit/Schrittzahl; keine Downloads, Clipboard-, Kamera-, Mikrofon- oder Dateizugriffe ohne separates Gate; Screenshots sanitizen und zeitlich begrenzt behalten.

## 12. Brother-GPT-Eskalation

Bei unbekannter Hostgrenze erhält der Brother vorhandene Runner-APIs, Fehler, getestete Optionen und das minimale Tool-Schema. Er soll Reuse vor Neubau prüfen.

## 13. Abschlussartefakte

Real-Runner-Adapter, MCP-Tools, Tests, Tool-Dokumentation, Evidence-Schema und reproduzierbarer Demo-Run.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

