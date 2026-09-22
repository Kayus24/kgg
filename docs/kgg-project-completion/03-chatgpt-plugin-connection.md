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

### 5.1 Aktuelle Live-Reconciliation (2026-09-22)

Die unten dokumentierte G03-E3-Evidence bleibt der historische, einmalige
Discovery-Canary und wird nicht rückwirkend gelöscht. Ein späterer read-only
Live-Check im aktuellen ChatGPT-Workspace zeigte zunächst `Plugin nicht
verfügbar`; ein weiterer frischer Detail-Read lädt `KGG UI Lab Private` nun
wieder und zeigt die vollständige Tool-Liste.

Für den aktuellen Betriebsstand gilt daher:

- `B_PLUGIN_DISCOVERY=CURRENTLY_VISIBLE_TOOLS`.
- `G03_CURRENT=DISCOVERY_VISIBLE_EXECUTION_UNVERIFIED`.
- Die Tools sind sichtbar, aber es wurde in diesem Reconciliation-Schritt
  bewusst kein Chat und kein Plugin-Tool aufgerufen.
- Ein Tool-Call ist ein separater Kommunikations-/Kosten-Gate und wird nicht
  automatisch gestartet.

Die autoritative laufende Reconciliation steht in
`CURRENT_OPERATIONAL_RECONCILIATION_20260922.json`.

- `IMPLEMENTATION_STATUS=CHATGPT_APP_CONNECTED_READ_ONLY_CANARY_PASS`
- `LIVE_EVIDENCE_STATUS=PRIVATE_TUNNEL_CLIENT_DISCOVERY_PASS_CLIENT_STOPPED`
- `GATE_STATUS=PASS`
- `CONSEQUENCE_GATE_STATUS=COMPLETED_TRANSIENT_RUNTIME_KEY`
- `EVIDENCE_LEVEL=E3_REAL_HOST`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T19:14:04+02:00`

## 6. Bestehende Evidence

Der frische normale ChatGPT-Check auf `https://chatgpt.com/plugins` zeigte bei der Suche nach `KGG` sichtbar „Derzeit passen keine Plugins zu dieser Suche.“ Offizielle Verbindungsschritte sind unter `https://developers.openai.com/plugins/deploy/connect-chatgpt` beschrieben.

### 6.1 Fresh Account-/Workspace-Fähigkeit

Read-only im internen ChatGPT-Browser geprüft:

- Tab `264`, `https://chatgpt.com/#settings/Plugins`: Die installierte Plugin-Liste
  enthält keinen Eintrag `KGG`; der Link `Plugins durchsuchen` ist sichtbar.
- Tab `264`, `https://chatgpt.com/#settings/Security?section=developer-mode`:
  `Entwicklermodus` ist als sichtbarer Schalter `Value=1` aktiviert.
- In den sichtbaren Einstellungen ist kein privater KGG-/MCP-Verbindungs- oder
  Secure-MCP-Tunnel-Eintrag vorhanden. Das beweist nicht, dass die Funktion
  plattformweit fehlt; es beweist nur, dass sie im aktuell beobachteten
  Workspace noch nicht gebunden ist.
- Die aktive KGG-Verbindung wird über die private Tunnelressource außerhalb des
  Repositories hergestellt; `kgg-plugin/.mcp.json` bleibt der lokale stdio-
  Quellpfad `python ./mcp/server.py` und wird nicht umgeschrieben.
- Der frühere lokale Preflight meldete `TUNNEL_CLIENT=NOT_FOUND`. Dieser Zustand
  ist durch den anschließend verifizierten offiziellen Windows-x64-Client
  überholt; die Client-Prüfung und die Runtime-Key-Aktivierung sind mit
  transienter Nutzung abgeschlossen. Der Secret-Wert wurde nicht gespeichert.

Damit sind Ziel-Workspace-Fähigkeit, KGG-Transport-/Installationsbindung und
der read-only Tool-Canary nachgewiesen. Der Canary wurde genau einmal
ausgeführt; keine Statuspromotion über G03 hinaus wird daraus abgeleitet.

### 6.2 Bounded Create-Versuch

Mit der gebundenen G03-Freigabe wurden Name, Beschreibung, Personal-
Organisation und der ausgewählte ChatGPT-Workspace genau einmal im
Tunnel-Formular eingetragen und `Create` einmal ausgelöst. Nach der
Postcondition-Prüfung zeigte die Plattform weiterhin `No tunnels yet`; eine
Tunnel-ID oder ein Runtime-Key wurde daher weder erzeugt noch gespeichert.

```text
ATTEMPT_ID=G03_TUNNEL_CREATE_20260921_01
RESULT=NO_RESOURCE_OBSERVED
ERROR_CLASS=PLATFORM_CREATE_UNCONFIRMED
RETRY_POLICY=NO_AUTOMATIC_RETRY
```

Die verzögerte Postcondition-Prüfung nach einem frischen Reload zeigt jetzt
genau eine Tunnelzeile. Damit ist die Ressource erstellt; die Tunnel-ID wird
nicht in KGG-Dokumentation oder Chat-Ausgaben übernommen. Der offizielle
Windows-x64-Client `v0.0.14` wurde aus dem Latest-Release geladen, gegen
`SHA256SUMS.txt` geprüft und `tunnel-client help quickstart` lief erfolgreich.

Das separate Runtime-Key-Gate wurde ausdrücklich autorisiert. Genau ein
Runtime-Key wurde transient im laufenden Client-Prozess verwendet; sein Secret
wurde weder ausgegeben noch in Repository, Logs oder Evidence gespeichert.

Ein frischer read-only Abruf der Platform-Key-Seite zeigt zusätzlich die
Schaltfläche `Create new secret key` und genau einen maskierten bestehenden
Schlüssel. Der Secret-Wert ist nicht verfügbar, wird nicht extrahiert und
nicht wiederverwendet.

## 7. Aufgelöste Lücke und Root Cause

Der lokale stdio-MCP ist an eine private Tunnelressource gebunden; der offizielle
Client lief bis zum Ende des Canary und wurde danach kontrolliert beendet. Die
ChatGPT-App ist verbunden und der Discovery-Canary hat
`get_current_state(actor=system)` mit `status=ready` geliefert. Der
Runtime-Key bleibt ausschließlich transient und wird nicht als Evidence
behalten.

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

## 13.1 Aufgelöster Blocker-Nachweis

`BLOCKER_FINGERPRINT=G03_NO_TRANSPORT_1E6C6E3`

`OBSERVED=Private Tunnelressource erstellt; offizieller Client v0.0.14 verifiziert und live; ChatGPT-App KGG UI Lab Private verbunden; get_current_state(actor=system) genau einmal erfolgreich ausgeführt.`

`NEXT_ACTION=Weiter mit G07 Surface-Matrix; keinen zweiten G03-Discovery-Canary und kein erneutes Runtime-Key-Gate.`

### 13.2 Brother-Advisory, geprüft und übernommen

Der Brother-GPT hat nach eigener Gegenprüfung bestätigt, dass der bestehende
lokale stdio-MCP direkt wiederverwendet werden soll. Der kleinste unterstützte
Pfad ist ein Secure MCP Tunnel; ein zweiter Server, Proxy, Fake-HTTPS-Endpunkt
oder eine öffentliche Bereitstellung wäre Aufgaben-Drift. Vor jeder Aktivierung
ist jedoch ein neues Consequence Gate erforderlich. Die read-only
Workspace-Prüfung ist abgeschlossen: Developer Mode ist sichtbar aktiv, aber
keine KGG-Installation und keine aktive Tunnel-Nutzung ist belegt. Diese
historische Blocker-Einschätzung ist durch den anschließenden Transport- und
Canary-Nachweis aufgelöst; G03 ist nun `PASS`.

Übernommene Entscheidung:

```text
SUPPORTED_PATH_EXISTS=true
 AUTHORIZED_CHATGPT_REACHABLE_TRANSPORT_PRESENT=true
CHATGPT_KGG_INSTALLATION_PROVEN=true
PREFERRED_TRANSPORT=SECURE_MCP_TUNNEL
PUBLIC_HTTPS_ENDPOINT_REQUIRED_FOR_CURRENT_PRIVATE_PROOF=false
NEXT_GATE=G07_SURFACE_MATRIX
```

### 13.3 Offizielle Transportvoraussetzungen

Der aktuelle OpenAI-Stand bestätigt für einen privaten lokalen MCP-Server:

- `tunnel_id` aus den Platform-Tunnel-Einstellungen;
- ein Runtime-API-Key für `tunnel-client` (wird niemals in Repository,
  Checkpoint oder Chat protokolliert);
- `Tunnels Read + Use` zum Ausführen bzw. Auswählen des Tunnels und getrennte
  ChatGPT-Developer-Mode-/Workspace-Berechtigung;
- ein laufender `tunnel-client`, der vom Repository-Root aus den vorhandenen
  stdio-Befehl `python kgg-plugin/mcp/server.py` erreichen kann;
- eine ChatGPT-App-Verbindung, bei der im Developer-Mode `Tunnel` ausgewählt
  und anschließend genau ein read-only Discovery-Canary ausgeführt wird.

Diese Voraussetzungen waren die Evidence für die Gate-Planung. Sie sind nun
durch den laufenden Client, die verbundene ChatGPT-App und den einmaligen
read-only Discovery-Canary erfüllt. Die Tunnel-ID und das Runtime-Secret
werden weiterhin absichtlich nicht in Repository-Evidence übernommen.
Der sichere Endzustand ist `G03=PASS`.

Quellen: [OpenAI Secure MCP Tunnel Guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
und [OpenAI Help Center zu Developer Mode/MCP-Apps](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt),
zuletzt read-only geprüft am 2026-09-21.

### 13.4 Fresh Transport-UI-Evidence

Im internen Browser wurde die Erstellungs- und Transportvorbereitung verifiziert:

- `https://chatgpt.com/plugins?search=KGG#settings/Connectors?create-connector=true&redirectAfter=%2Fplugins`
  zeigt `Neues Plugin`, `App erstellen` und die Verbindungsarten `Server URL`
  und `Tunnel`.
- Der sichtbare Link `Tunnel erstellen` führt zu
  `https://platform.openai.com/settings/organization/tunnels`.
- Dort sind im persönlichen Workspace `Tunnels` und der Button `Create tunnel`
  sichtbar. Nach einem einmaligen Create-Versuch und verzögerter Fresh-Prüfung
  ist genau eine Tunnelressource sichtbar; die Tunnel-ID wird nicht in KGG-
  Evidence übernommen. Es wurde kein Cookie-/Berechtigungsdialog bestätigt.

Damit ist `CHATGPT_PRIVATE_APP_CREATION_UI=PRESENT`,
`TUNNEL_CREATION_UI=PRESENT`, `AUTHORIZED_TUNNEL_RESOURCE=CREATED`,
`TUNNEL_CLIENT=STOPPED_AFTER_CANARY`, `CHATGPT_APP=CONNECTED` und
`DISCOVERY_CANARY=PASS`. Der G03-Transportpfad ist abgeschlossen; der nächste
Schritt ist G07.

Das read-only geöffnete Platform-Formular bestätigt außerdem die nötigen
Eingabeklassen `Name`, `Description`, `Organizations` und
`ChatGPT workspaces`; der Button `Create` bleibt vor vollständiger Eingabe
deaktiviert. Workspace-IDs und Organisationskennungen werden nicht in KGG-
Evidence übernommen.

## 14. Beitragsherkunft

```text
CONTRIBUTION_SOURCE=BROTHER_GPT
CONTRIBUTION_DATE=2026-09-21
HANDOFF_ID=G03_CHATGPT_DISCOVERY_20260921_01
REVIEW_STATUS=ACCEPTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=Bestehenden stdio-MCP über Secure MCP Tunnel wiederverwenden; keinen zweiten Server bauen; zuerst Workspace-Eignung read-only prüfen.
DECISION_SUMMARY=G03 PASS: Bestehenden stdio-MCP über Secure MCP Tunnel wiederverwenden; transienter Runtime-Key, verbundene ChatGPT-App und genau ein read-only Discovery-Canary sind nachgewiesen.
```

Ausführbares Aktivierungspaket: [03a-g03-transport-activation-runbook.md](03a-g03-transport-activation-runbook.md).

```text
ACTIVATION_RUNBOOK_SHA256=288bf00880e54f14a43aa662645fbc40515a575bd9f8fd24b97bd9afb9524243
```

Das einmalige, begrenzte Konsequenz-Gate ist als
[G03_HUMAN_GATE_REQUEST_20260921.json](G03_HUMAN_GATE_REQUEST_20260921.json)
maschinenlesbar gebunden:

```text
HUMAN_GATE_REQUEST_SHA256=fa4f958a25560a9ec5f1853b8eda0801dff130a95a1693b3de1269806162ec2c
```

Das abgeschlossene, separat geschützte Runtime-Key-Gate ist
[G03_RUNTIME_KEY_GATE_20260921.json](G03_RUNTIME_KEY_GATE_20260921.json):

```text
RUNTIME_KEY_GATE_SHA256=2f71734dc523ea62652f97f521d76e47b659093720f4ca5c6ec5f5c7492dc95f
```
