# G01 – Custom-GPT-Funktionsinventur und Migration

## 1. Ziel

Jede dauerhaft benötigte Fähigkeit der KGG Custom GPTs besitzt eine explizite Zielkomponente im Plugin, einen Akzeptanztest und eine finale Disposition.

## 2. Warum dieses Gate erforderlich ist

„Custom GPT in Plugin übertragen“ ist mehr als ein MCP-Server. Instructions, Knowledge, Actions, Safety, Memory, Koordination und UI-Lab müssen vollständig inventarisiert werden, sonst entsteht unbemerkter Funktionsverlust.

## 3. Scope und Nicht-Ziele

In Scope: produktiv benötigte Custom-GPT-Fähigkeiten. Nicht in Scope: ungeprüfte Altfeatures nur wegen historischer Existenz oder das Kopieren statischer Knowledge-Dateien ohne Fresh-Source-Mechanismus.

## 4. Abhängigkeiten

G00. Kanonische Quellen: Custom-GPT-Goal, Bootstrap, Resource Manifest, Action-Schemas, Knowledge-Packs, Expected Results und Plugin-Skills.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=PARTIAL_MAPPING_EXISTS`
- `LIVE_EVIDENCE_STATUS=CUSTOM_GPT_TESTS_EXIST_PLUGIN_PARITY_NOT_PROVEN`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `LAST_VERIFIED_BASE_SHA=15f1782bafbd3bc358bb08e5e4fc1d9b4592242a`
- `LAST_VERIFIED_AT=2026-09-21T09:56:20+02:00`

## 6. Bestehende Evidence

- Vier Plugin-Skills für Supervisor, Operations, Testing, Safety plus Escalation.
- lokaler MCP-Kandidat mit UI-Lab-Toolnamen.
- umfangreiche Custom-GPT-Prompt-/Action-Expected-Results.
- Resource Manifest und zwei Action-Schemas.
- Vorbereitete Arbeitsmatrix: [01a-capability-migration-matrix.md](01a-capability-migration-matrix.md).

## 7. Lücke und Root Cause

Es fehlt eine abschließende Capability-Matrix „Quelle → Plugin-Baustein → Surface → Test“. Der bisherige Fokus behandelte UI Lab zeitweise als deferierte Zusatzfähigkeit, obwohl es Kernziel ist.

## 8. Kleinschrittiger Arbeitsplan

1. Fähigkeiten aus Instructions, Knowledge, Actions und Live-Testfällen deduplizieren.
2. Jede Fähigkeit als `SKILL`, `MCP_TOOL`, `CHATGPT_UI`, `ACTION`, `DOC_ONLY` oder `REJECTED` klassifizieren.
3. Für jede Fähigkeit A/B/C-Support und minimale Berechtigung bestimmen.
4. Je Fähigkeit einen positiven und mindestens einen Negativtest zuordnen.
5. UI-Lab-Einträge ausdrücklich auf „real“ versus „synthetic“ prüfen.
6. Unnötige oder doppelte Funktionen begründet verwerfen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G01_CAPABILITY_PARITY`
- `INPUT=kanonische Custom-GPT-Ressourcen, Plugin-Manifest, Skills, MCP-Tools, Expected Results`
- `PROCEDURE=vollständige Matrix erzeugen; jede Zeile auf Zielbaustein, Surface und Test prüfen`
- `PASS_CRITERIA=Keine benötigte Fähigkeit ohne Disposition, Besitzer, Test und Zielkomponente`
- `FAIL_CRITERIA=UI-Lab fehlt, Fähigkeit nur aus Modellgedächtnis oder nicht testbare „Parity“-Behauptung`
- `RETRY_RULE=Ein gezielter Read der Quelle einer unklaren Fähigkeit`
- `FALLBACK=UNKNOWN oder DEFER_WITH_REASON, niemals stillschweigend löschen`
- `EVIDENCE_OUTPUT=CAPABILITY_MIGRATION_MATRIX_V1`
- `NEXT_ON_PASS=G02`
- `NEXT_ON_FAIL=G11 bei Architekturunklarheit`
- `INVALIDATION_TRIGGERS=Custom-GPT-Instructions, Manifest, Action-Schema oder Plugin-Capabilities ändern sich`

## 10. Tests

- Matrix-Vollständigkeit gegen Resource Manifest und operationIds.
- Jede Pflichtfähigkeit hat Expected Result.
- Negativtest: synthetische UI-Lab-Tools dürfen nicht als reale Migration zählen.

## 11. Safety und Datenschutz

Keine Knowledge-Rohdaten mit Secrets oder Patientendaten migrieren. Live-Datenzugriff bleibt an vertrauenswürdigen Actions/MCP-Grenzen.

## 12. Brother-GPT-Eskalation

Wenn unklar ist, ob eine Fähigkeit Skill, Tool oder Host-UI braucht, erhält der Brother genau die Capability-Zeile, Hostgrenzen und Alternativen.

## 13. Abschlussartefakte

Versionierte Capability-Matrix, Testzuordnung, abgelehnte Fähigkeiten mit Begründung und aktualisiertes Statusregister.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
