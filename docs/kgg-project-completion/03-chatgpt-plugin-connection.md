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
- `LIVE_EVIDENCE_STATUS=FRESH_PLUGIN_DIRECTORY_SEARCH_FOUND_NO_KGG_PLUGIN`
- `GATE_STATUS=BLOCKED`
- `EVIDENCE_LEVEL=E3_REAL_HOST`
- `LAST_VERIFIED_BASE_SHA=efb35ff796235348fd0d620ee58c0e24b0e9fc8d`
- `LAST_VERIFIED_AT=2026-09-21T13:04:52+02:00`

## 6. Bestehende Evidence

Der frische normale ChatGPT-Check auf `https://chatgpt.com/plugins` zeigte bei der Suche nach `KGG` sichtbar „Derzeit passen keine Plugins zu dieser Suche.“ Offizielle Verbindungsschritte sind unter `https://developers.openai.com/plugins/deploy/connect-chatgpt` beschrieben.

## 7. Lücke und Root Cause

Der lokale stdio-MCP ist in ChatGPT nicht automatisch verfügbar. Ein erreichbarer HTTPS-/Secure-MCP-Endpoint und die anschließende Workspace-/Plugin-Installation fehlen.

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
- `NEXT_ON_FAIL=genau ein autorisiertes Transport-Gate; danach G03 erneut ausführen`
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

## 13.1 Aktueller Blocker-Nachweis

`BLOCKER_FINGERPRINT=G03_NO_TRANSPORT_EFB35FF`

`OBSERVED=KGG-Suche im frischen normalen ChatGPT-Plugin-Verzeichnis ohne Treffer; lokale Umgebung ohne tunnel-client/HTTPS-Endpoint.`

`NEXT_ACTION=Autorisierter HTTPS-/Secure-MCP-Endpoint bereitstellen oder die Surface ausdrücklich als NOT_SUPPORTED abschließen.`

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
