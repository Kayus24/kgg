# G03 – Plugin-Verbindung im normalen ChatGPT

## 1. Ziel

Ein normaler ChatGPT-Chat kann das persönliche KGG-Plugin erkennen, seine freigegebenen Tools sehen und einen bounded read-only Aufruf ausführen.

## 2. Warum dieses Gate erforderlich ist

Der Hauptnutzen der Migration entsteht erst, wenn die Funktionen außerhalb des Custom GPT erreichbar sind. Lokale Codex-Funktionalität beweist dieses Ziel nicht.

## 3. Scope und Nicht-Ziele

Nur Installation, Discovery, Auth und read-only Canary. Keine Browseraktion und kein Repo-Write in diesem Gate.

## 4. Abhängigkeiten

G02, ChatGPT-Account/Workspace mit Plugin-Unterstützung, erreichbarer MCP-Endpunkt und ggf. Developer Mode.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=NO_VERIFIED_CHATGPT_INSTALLATION`
- `LIVE_EVIDENCE_STATUS=LIVE_TEST_FOUND_NO_KGG_PLUGIN`
- `GATE_STATUS=FAIL`
- `EVIDENCE_LEVEL=E3_REAL_HOST`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

Der normale ChatGPT-Live-Test stellte keine KGG-Tools bereit. Offizielle Verbindungsschritte sind unter `https://developers.openai.com/plugins/deploy/connect-chatgpt` beschrieben.

## 7. Lücke und Root Cause

Der lokale stdio-MCP ist in ChatGPT nicht automatisch verfügbar. Deployment/Tunnel, Installation oder Workspace-Freigabe fehlen.

## 8. Kleinschrittiger Arbeitsplan

1. Host-/Workspace-Pluginfähigkeit read-only prüfen.
2. G02-Endpunkt bereitstellen.
3. persönliches Plugin installieren und exakte Plugin-Version notieren.
4. in einem frischen normalen Chat Tool Discovery ausführen.
5. read-only `health/version/capabilities` aufrufen.
6. Ergebnis mit Tool-Name, Version, Request-ID und sichtbarer Antwort dokumentieren.
7. Deinstallations-/Disable-Fallback prüfen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G03_CHATGPT_DISCOVERY`
- `INPUT=installiertes Paket, erreichbarer Endpoint, frischer normaler Chat`
- `PROCEDURE=Plugin auswählen; Capability abfragen; genau einen read-only Canary ausführen`
- `PASS_CRITERIA=ChatGPT zeigt das KGG-Plugin und liefert eine run-gebundene Antwort des richtigen Tools/Servers`
- `FAIL_CRITERIA=kein Plugin, falscher Server, Antwort nur aus Modellwissen oder fehlende Tool-Evidence`
- `RETRY_RULE=Ein frischer Chat nach belegtem UI-/Cacheproblem, keine wiederholten Tool-Calls ins Blaue`
- `FALLBACK=Workspace-/Accountgrenze dokumentieren und NOT_SUPPORTED prüfen`
- `EVIDENCE_OUTPUT=CHATGPT_PLUGIN_DISCOVERY_REPORT`
- `NEXT_ON_PASS=G07 und nach G04 echter UI-Canary`
- `NEXT_ON_FAIL=G02 oder G11`
- `INVALIDATION_TRIGGERS=Plugin-Version, Endpoint, Auth oder Workspace-Policy ändert sich`

## 10. Tests

- positiver Tool-Discovery-Canary.
- Negativ: Plugin deaktiviert oder falsche Auth muss fail-closed sein.
- frischer Chat als unveränderter Replay.

## 11. Safety und Datenschutz

Canary enthält nur synthetische IDs. Keine Repo-, Patienten- oder Produktionswrites.

## 12. Brother-GPT-Eskalation

Bei fehlender Discovery erhält der Brother Screenshots, Endpoint-/Manifeststatus und offizielle Fehlermeldung; keine Zugangsdaten.

## 13. Abschlussartefakte

Installationsnachweis, Tool-Discovery, Canary-Transcript, Version und Disable-/Rollback-Nachweis.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

