# G02 – Universelles KGG-Plugin-Paket

## 1. Ziel

Ein versioniertes KGG-Plugin bündelt Skills, MCP und optionale UI so, dass derselbe Kern in Codex und normalem ChatGPT installiert werden kann.

## 2. Warum dieses Gate erforderlich ist

Der aktuelle lokale stdio-MCP beweist Codex-Nähe, aber keine ChatGPT-Verfügbarkeit. Ein universelles Paket benötigt eine transportfähige MCP-Grenze und reproduzierbare Installation.

## 3. Scope und Nicht-Ziele

In Scope: `kgg-plugin/**`, Manifest, Skills, MCP-Beschreibung, Distribution und Health/Version. Nicht in Scope: eine zweite Produktarchitektur oder hosted Telemetrieplattform.

## 4. Abhängigkeiten

G01. Für ChatGPT ist ein öffentlich per HTTPS erreichbarer MCP-Endpunkt oder ein Secure MCP Tunnel erforderlich; lokales stdio allein genügt nicht.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=LOCAL_CODEX_PLUGIN_CANDIDATE`
- `LIVE_EVIDENCE_STATUS=LOCAL_ONLY`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=fe62c8be2b48fbe7ba3f40313f2d016b5e07c69a`
- `LAST_VERIFIED_AT=2026-09-21T10:12:30+02:00`

## 6. Bestehende Evidence

- `kgg-plugin/.codex-plugin/plugin.json`
- `kgg-plugin/.mcp.json` startet `python ./mcp/server.py`.
- Skills und MCP-Evalskripte existieren.
- Offizielle Plugin-Dokumentation: `https://developers.openai.com/plugins/concepts/plugins` und `https://developers.openai.com/plugins/deploy/connect-chatgpt`.

## 7. Lücke und Root Cause

Das Paket setzt derzeit eine lokale Python-/Pfadumgebung voraus. Es gibt noch keinen nachgewiesenen ChatGPT-kompatiblen HTTPS-/Tunnel-Endpunkt und keine normale ChatGPT-Installation.

## 8. Kleinschrittiger Arbeitsplan

1. Plugin-Manifest und Paketlayout gegen aktuelle offizielle Anforderungen prüfen.
2. Runtime-Abhängigkeiten und relative Pfade vollständig erfassen.
3. einen minimalen read-only `health/version/capabilities`-Pfad definieren.
4. Transportwahl treffen: HTTPS-Deployment oder Secure MCP Tunnel; keine doppelte Serverlogik.
5. Paket lokal validieren und für persönliche Installation paketieren.
6. Installations- und Deinstallationsweg dokumentieren.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G02_DISTRIBUTABLE_PLUGIN`
- `INPUT=Plugin-Verzeichnis, offizielle aktuelle Plugin-Spezifikation, Runtime-Abhängigkeiten`
- `PROCEDURE=lint/package; frische Installation; Health-Tool; Capability-Liste; Deinstallation`
- `PASS_CRITERIA=Ein einziges versioniertes Paket ist in beiden Zielhosts installierbar und meldet dieselbe Identität`
- `FAIL_CRITERIA=lokaler absoluter Pfad, ungebundene Abhängigkeit, separater ChatGPT-Servercode oder nicht reproduzierbare Installation`
- `RETRY_RULE=Ein Neuinstallationsversuch nach belegtem transientem Packagingfehler`
- `FALLBACK=Codex lokal bleibt PARTIAL; ChatGPT bleibt BLOCKED`
- `EVIDENCE_OUTPUT=PLUGIN_PACKAGE_REPORT mit Hash, Version und Hostresultaten`
- `NEXT_ON_PASS=G03 und G04`
- `NEXT_ON_FAIL=G11 bei Transport-/Packaging-Architekturfrage`
- `INVALIDATION_TRIGGERS=Manifest, MCP-Protokoll, Runtime oder Paketversion ändert sich`

## 10. Tests

- vorhandene Candidate-Validation.
- Manifest-/Schema-Tests.
- frische lokale Codex-Installation.
- frische ChatGPT-Installation/Discovery in G03.
- Negativ: falsche Version, fehlende Runtime, nicht erlaubter Host.

## 11. Safety und Datenschutz

Keine Secrets im Paket. Remote MCP authentifiziert minimal, protokolliert keine sensitiven Payloads und nutzt nur synthetische Testdaten.

## 12. Brother-GPT-Eskalation

Bei unklarer Transportwahl soll der Brother offizielle Lösungen vergleichen und den kleinsten Pfad wählen; kein eigener Backend-Stack ohne Nachweis.

## 12.1 G02-Preflight-Checkpoint

- `CHECKPOINT_ID=CP_G02_PREFLIGHT_START`
- `BASE_SHA=fe62c8be2b48fbe7ba3f40313f2d016b5e07c69a`
- `DECISION=CONTINUE_INSIDE_EXISTING_SCOPE`
- `LOCAL_MCP_BOUNDARY=present`
- `CHATGPT_DISTRIBUTION_BOUNDARY=not_yet_proven`
- `REAL_BROWSER_BOUNDARY=not_part_of_G02`
- `NEXT_STEP=G02.1 manifest/runtime/transport audit`

G02 darf die lokale stdio-Fähigkeit als Candidate-Evidence verwenden, aber nicht als Beweis für eine installierbare ChatGPT-Verbindung. Ein fehlender HTTPS-/Tunnel-Endpunkt wird als konkrete externe Voraussetzung klassifiziert, nicht durch synthetische Health- oder Screenshot-Daten überdeckt.

## 13. Abschlussartefakte

Installierbares Paket, Versionsmanifest, Capability-Health, Installationsanleitung und Rollback.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
