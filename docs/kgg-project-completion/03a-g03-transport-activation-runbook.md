# G03a – Secure-MCP-Transport-Aktivierung

## 1. Ziel

Den vorhandenen lokalen KGG-stdio-MCP genau einmal über einen privaten Secure
MCP Tunnel an die normale ChatGPT-App anbinden und danach genau einen
synthetischen read-only Discovery-Canary ausführen.

## 2. Warum dieses Gate erforderlich ist

Lokales Codex-stdio und die sichtbare ChatGPT-App-Erstellungsoberfläche sind
noch keine reale ChatGPT-Verbindung. Dieses Runbook schließt nur die
Transportlücke; es baut keinen zweiten Server.

## 3. Scope und Nicht-Ziele

Erlaubt: ein privater Tunnel, der vom Repository-Root aus den vorhandenen
Befehl `python kgg-plugin/mcp/server.py`,
read-only Tool-Allowlist und ein Canary. Nicht erlaubt: öffentlicher Endpoint,
neuer Proxy, Patientendaten, Produktionsaktionen, Write-Tools, zweiter Server,
PR/Merge oder eine zweite Canary-Ausführung.

## 4. Abhängigkeiten

- G02 lokales Paket und `.mcp.json`.
- ChatGPT Developer Mode und sichtbare App-Erstellungsoberfläche.
- OpenAI-Platform-Tunnel-Rechte `Read + Manage` zum Erstellen und `Read + Use`
  zum Ausführen/Auswählen.
- Workspace-Bindung und Runtime-Key. Der Key wird niemals dokumentiert.
- `tunnel-client` auf demselben Host/Netz, der den stdio-MCP erreicht.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=TUNNEL_RESOURCE_CREATED_DISCOVERY_CANARY_PASS_CLIENT_STOPPED`
- `LIVE_EVIDENCE_STATUS=PRIVATE_TUNNEL_CLIENT_HEALTH_AND_DISCOVERY_CANARY_PASS`
- `GATE_STATUS=PASS`
- `EVIDENCE_LEVEL=E3_REAL_HOST`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T19:14:04+02:00`

## 6. Bestehende Evidence

- ChatGPT zeigt `App erstellen` und die Verbindung `Tunnel`.
- OpenAI Platform zeigt nach Fresh-Reload genau eine private Tunnelressource.
- Der offizielle Windows-x64-Client wurde gegen das veröffentlichte
  Checksum-Manifest geprüft; `help quickstart` lief erfolgreich.
- Das lokale Repository enthält nur den bestehenden stdio-MCP.

## 7. Lücke und Root Cause

Die Tunnelressource existiert; der offizielle `tunnel-client` lief mit einem
transient eingesetzten Runtime-Key bis zum erfolgreichen Canary und wurde
danach kontrolliert beendet. Die ChatGPT-App ist verbunden. Der
Secret-Wert und die Tunnel-ID werden absichtlich nicht in Repository-Evidence
übernommen. Das Runtime-Key-Gate ist abgeschlossen; G03 bleibt auf genau einen
Discovery-Canary begrenzt.

## 8. Kleinschrittiger Arbeitsplan

1. Das separat autorisierte Runtime-Key-Gate einmalig verwenden.
2. Tunnel-Client nur aus der offiziellen Release-Quelle beziehen; keine
   Abhängigkeit ungefragt installieren.
3. Die bereits erstellte private Tunnelressource und den ausgewählten
   Ziel-Workspace verwenden; keinen zweiten Tunnel anlegen.
4. IDs und Runtime-Key nicht in Evidence
   speichern.
5. Profil auf den vom Repository-Root aus gültigen Befehl
   `python kgg-plugin/mcp/server.py` konfigurieren.
6. `doctor`/Health prüfen und den Client starten.
7. In ChatGPT die private App verbinden, Tools scannen und nur die freigegebene
   read-only Allowlist aktivieren.
8. Genau einen frischen synthetischen Discovery-Canary durchführen.
9. Bei jedem Fehler stoppen, Evidence binden und keinen Redispatch versuchen.
10. Nach erfolgreichem Canary zu G07 wechseln; keinen zweiten identischen Canary
    ausführen.

### 8.1 Offizielle Client-Sequenz (Windows, erst nach Gate)

Die aktuelle OpenAI-Anleitung verlangt einen `tunnel_id`, einen Runtime-Key
und einen erreichbaren stdio-/HTTP-MCP. Für diesen Windows-Host ist die
äquivalente, nicht automatisch auszuführende Sequenz:

```powershell
# Nur interaktiv setzen; niemals in Datei, Chat oder Evidence speichern.
$env:CONTROL_PLANE_API_KEY = '<RUNTIME_KEY_NUR_FUER_DIESE_SESSION>'

tunnel-client init `
  --sample sample_mcp_stdio_local `
  --profile kgg-ui-lab-local-stdio `
  --tunnel-id '<TUNNEL_ID_AUS_PLATFORM>' `
  --mcp-command 'python kgg-plugin/mcp/server.py'

tunnel-client doctor --profile kgg-ui-lab-local-stdio --explain
tunnel-client run --profile kgg-ui-lab-local-stdio
```

Quelle und Versionsregel: [Secure MCP Tunnel – Set up
`tunnel-client`](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels#how-to-set-up-tunnel-client).
Immer die dort verlinkte Latest-Release verwenden, das passende Windows-Asset
für die tatsächliche Hostarchitektur wählen und vor dem Start das veröffentlichte
Checksum-/Provenance-Asset prüfen. Keine Versionsnummer oder Runtime-Secret in
den Projektdateien festschreiben.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G03_TRANSPORT_ACTIVATION`
- `INPUT=Tunnel-Formular, vorhandener stdio-MCP, Workspace-Bindung, bounded Gate`
- `PROCEDURE=Create → bind workspace → configure stdio profile → doctor → run → connect app → one read-only canary`
- `PASS_CRITERIA=Tunnel healthy; ChatGPT-App sichtbar; erlaubtes read-only Tool liefert gebundene Antwort`
- `FAIL_CRITERIA=fehlende Rechte, fehlende Tunnel-ID, Client unhealthy, falscher MCP, Write-/Produktionsfähigkeit oder ungebundene Toolantwort`
- `RETRY_RULE=kein identischer Retry bei deterministischem Fehler; höchstens ein Retry bei belegtem transientem Transportfehler`
- `FALLBACK=G03 BLOCKED; lokale Codex-/Custom-GPT-Fallbacks unverändert weiterführen`
- `EVIDENCE_OUTPUT=G03_TRANSPORT_ACTIVATION_CHECKPOINT und G03_DISCOVERY_REPORT`
- `NEXT_ON_PASS=G07 Surface-Matrix; G03-Canary nicht wiederholen`
- `NEXT_ON_FAIL=BLOCKER_PACKAGE mit genau einer Root-Cause und ohne Redispatch`
- `INVALIDATION_TRIGGERS=Main-, MCP-, Manifest-, Workspace-, Tunnel- oder Tool-Schema-Drift`

### 9.1 Getrennter Real-Host-Diagnoseschritt (G04/G05, nicht G03-Retry)

Der normale ChatGPT-Anschluss darf nicht dadurch als Real-Host gelten, dass
die synthetische Tool-Liste sichtbar ist. Für einen späteren, separat
gebundenen `POST_FIX_DIAGNOSTIC` müssen vor dem ersten Session-Aufruf alle
folgenden Punkte read-only nachgewiesen werden:

1. Das verbundene Bundle veröffentlicht eine überprüfbare Source-/Build-
   Revision oder ist nachweislich mit dem geprüften Fresh-Main-Code gebunden.
2. Die Plugin-Beschreibung und der Tool-Contract kennzeichnen den Pfad nicht
   mehr nur als synthetisch; andernfalls bleibt der Lauf `SYNTHETIC_ONLY`.
3. Der gestartete MCP-Prozess erbt `KGG_REAL_BROWSER=1`. Der Default-
   `kgg-plugin/mcp/server.py` bleibt unverändert synthetisch; die Aktivierung
   darf nur über eine explizite, gebundene Runner-/Profilvariante erfolgen.
4. `KGG_BROWSER_NODE`, `KGG_PLAYWRIGHT_NODE_PATH` beziehungsweise die im
   aktuellen `real_browser.py` vorgesehenen Fallbacks sind im selben Prozess
   auflösbar. Fehlende Dependencies werden nicht automatisch installiert.
5. Der `app.url`-Wert wird als nackte JSON-String-Primitive übertragen, nie als
   Markdown-Link oder Link-Objekt.

Danach gilt genau diese Reihenfolge:

```text
POST_FIX_BRIDGE_BINDING
→ PLAYWRIGHT_RESOLUTION
→ CHROMIUM_LAUNCH
→ ALLOWLISTED_FIXTURE_NAVIGATION
→ ONE_OBSERVE_SCREENSHOT
→ OPTIONAL_ONE_SAFE_ACTION
→ SECOND_SCREENSHOT_STATE_CHECK
→ RECONCILE_OR_STOP
```

`SESSION_START_REJECTED_PRE_BROWSER` beendet den Diagnoseschritt. Es gibt
keinen weiteren identischen `start_ui_session`-Retry. Ein erfolgreicher
synthetischer Screenshot oder Quick Flow bleibt `SYNTHETIC_ONLY` und darf
G05/G06 nicht auf `PASS` heben. Der bestehende Tunnel wird wiederverwendet;
kein neuer Tunnel, kein neuer Runtime-Key und keine automatische Installation
werden aus diesem Runbook abgeleitet.

## 10. Tests

- Tunnel-Health/Readiness und MCP-Tool-Scan.
- Negative Prüfung: falscher Workspace, fehlende Berechtigung, ungesunder
  Client, nicht erlaubtes Write-Tool.
- Genau ein read-only Discovery-Canary.
- Keine Browser-, Patienten- oder Produktionsaktion in G03.
- Der Real-Host-Diagnoseschritt ist kein G03-Discovery-Canary und benötigt ein
  eigenes, einmaliges Run-/Consequence-Gate. Ohne Bundle-Bindung oder ohne
  `KGG_REAL_BROWSER=1` bleibt der Endzustand `B_PARTIAL / UI_PARITY_NOT_OBSERVABLE`.

## 11. Safety und Datenschutz

Nur synthetische Namen und IDs. Keine API-Keys, Tunnel-IDs mit sensiblen
Metadaten, Patienteninformationen oder Rohlogs speichern. Write-Tools müssen
vor dem Canary ausgeschlossen werden.

## 12. Brother-GPT-Eskalation

Nur bei einem neuen kausalen Fehler-Fingerprint. Der Brother erhält Status,
Health-/Schema-Evidence und die kleinste Entscheidungsfrage; er darf weder
Tunnel noch App erstellen und keine Rechte empfehlen, die über dieses Gate
hinausgehen.

## 13. Abschlussartefakte

Tunnel-Health-Evidence ohne Secrets, gebundene App-/Tool-Discovery, ein
Canary-Checkpoint, Rollback-/Disable-Anweisung und aktualisiertes G03-Register.

## 14. Beitragsherkunft

```text
CONTRIBUTION_SOURCE=BROTHER_GPT_AND_KGG_LEAD
CONTRIBUTION_DATE=2026-09-21
HANDOFF_ID=G03_CHATGPT_DISCOVERY_20260921_01
REVIEW_STATUS=ACCEPTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=Secure MCP Tunnel statt zweitem Server; Eligibility vor Aktivierung; ein Canary.
DECISION_SUMMARY=Runbook macht die einzige verbleibende externe Konsequenz reproduzierbar und fail-closed.
```

Die Ergänzung des Real-Host-Diagnoseschritts wurde am 2026-09-23 aus der
Brother-GPT-Prüfung des Blockers
`SESSION_START_REJECTED_PRE_BROWSER; CURRENT_BUNDLE_OR_ARGUMENT_BINDING_UNPROVEN`
übernommen. Sie ändert weder G03-Status noch Measurement-Contract und erteilt
keine Tunnel-, Key- oder Produktionsfreigabe.
