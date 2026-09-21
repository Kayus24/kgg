# KGG Project Completion – Master-Gates

Stand dieses Kandidaten: 2026-09-21

Fresh Remote Main nach G00-Merge: `8d1193cbb19e5ec63f597aa8a2e29fd22687369f`

Lokaler HEAD nach G00-Merge: `8d1193cbb19e5ec63f597aa8a2e29fd22687369f`

Dieses Verzeichnis ist die Arbeits- und Abschlusssteuerung für das KGG-Agentenprojekt. Es ersetzt keine Fach-, Safety-, Measurement- oder Release-Verträge. Bei Widerspruch gilt die jeweils fachlich kanonische Quelle; der Widerspruch wird als Gate-Blocker erfasst und nicht stillschweigend aufgelöst.

## 1. Unveränderliches Oberziel

Das Projekt besitzt zwei gleichrangige Produktziele:

1. Die benötigten Funktionen der KGG Custom GPTs werden in ein universell nutzbares KGG-Plugin überführt, das im normalen ChatGPT und – soweit die Host-Fähigkeiten reichen – in Codex verwendet werden kann.
2. Dieses Plugin stellt einen echten UI-Lab-Kanal für die KGG-HTML-App bereit:
   - visueller Regelkreis: Screenshot → GPT-Auswertung → Maus-/Touch-Aktion → neuer Screenshot → Zustandsprüfung;
   - Quick Flows: vorgefertigte, versionierte Navigations- und Bedienfolgen mit visueller Rückfallebene.

Measurement, Provenance und Telemetrie sichern diese Funktionen ab. Sie sind kein Ersatz für eine funktionierende Browser-Brücke.

## 2. Was „fertig“ bedeutet

`PROJECT_COMPLETE` ist nur zulässig, wenn alle Pflicht-Gates `PASS` oder ein ausdrücklich erlaubter finaler Grenzstatus sind, keine ungeklärten Pflichtpunkte verbleiben und der reale End-to-End-Pfad nachgewiesen ist.

Mindestens muss nachgewiesen sein:

- Ein normales ChatGPT kann das installierte KGG-Plugin erkennen und mindestens ein read-only KGG-Tool ausführen.
- Ein autorisierter KGG-Agent kann eine echte KGG-Testseite öffnen, einen echten Screenshot erhalten, eine echte Aktion ausführen und den veränderten Zustand mit einem zweiten Screenshot prüfen.
- Mindestens drei kanonische Quick Flows laufen auf der echten Testseite mit Schritt-Evidence und visueller Rückfallebene.
- Custom GPT, normales ChatGPT mit Plugin und Codex+Plugin sind je Surface ehrlich als `READY`, `PARTIAL` oder `NOT_SUPPORTED` klassifiziert.
- Safety, Datenschutz, Raw-Evidence, Tests, Installation, Rollback und Betriebsdokumentation sind abgeschlossen.

Nicht zugängliche Host-Interna dürfen als `NOT_OBSERVABLE` abgeschlossen werden. Eine fehlende Kernfunktion wie echte Screenshots oder echte Browseraktionen darf dagegen nicht als „nur nicht beobachtbar“ umetikettiert werden.

## 3. Status- und Evidence-Regeln

Erlaubte Gate-Statuswerte:

- `PASS`: Abnahmekriterium mit der geforderten Evidence-Stufe erfüllt.
- `PARTIAL`: verwertbare Teile vorhanden, mindestens ein Pflichtkriterium fehlt.
- `FAIL`: vorhandene Implementierung widerspricht dem Kriterium.
- `BLOCKED`: nächster erlaubter Schritt benötigt eine echte externe Voraussetzung oder ein Consequence Gate.
- `UNKNOWN`: autoritative Prüfung fehlt; niemals als Erfolg behandeln.
- `NOT_APPLICABLE`: nachgewiesen nicht relevant; Begründung erforderlich.

Evidence-Stufen:

1. `E0_DOCUMENTED`: Behauptung oder Spezifikation.
2. `E1_SYNTHETIC`: Fixture/Mock/Unit-Test.
3. `E2_LOCAL_REAL_RUNTIME`: reale lokale Browser-/MCP-Ausführung.
4. `E3_REAL_HOST`: echte Ausführung in ChatGPT, Custom GPT oder Codex.
5. `E4_REPEATED_STABLE`: unveränderter Real-Host-Replay mit gebundener Evidence.

Ein Gate darf nur mit der in seinem Detaildokument verlangten Stufe auf `PASS` gesetzt werden. `E1_SYNTHETIC` beweist niemals eine echte Host-Funktion.

## 4. Abschlussmatrix

| Gate | Pflichtpunkt | Aktueller Status | Aktuelle Evidence | Für PASS erforderlich | Detail |
| --- | --- | --- | --- | --- | --- |
| G00 | Source of Truth, Statusregister, Checkpoints | `PASS` | Dokumentensatz in PR #239 gemergt; Required Gate grün; Resume-Regel getestet | Fresh-Main-gebundener Dokumentensatz und eindeutiger nächster Gate-Schritt | [G00](00-governance-and-source-of-truth.md) |
| G01 | Vollständige Custom-GPT-Funktionsinventur und Migration | `PASS` | 30 operationIds, fünf Skills, Manifest und kanonische Quellen abgebildet; Self-Tests grün | Jede benötigte Fähigkeit besitzt Zielkomponente, Test und Disposition; Live-Parität bleibt nachgelagert | [G01](01-custom-gpt-capability-migration.md) |
| G02 | Universelles Plugin-Paket | `PARTIAL` | `.codex-plugin`, Skills und lokaler stdio-MCP vorhanden | Paket in Codex und ChatGPT installierbar, versioniert und ohne lokale Pfadannahmen | [G02](02-universal-plugin-package.md) |
| G03 | Normales ChatGPT erkennt und nutzt das Plugin | `FAIL` | Live-Test fand kein installiertes KGG-Plugin | Tool Discovery und read-only Tool-Aufruf im normalen ChatGPT mit E3-Evidence | [G03](03-chatgpt-plugin-connection.md) |
| G04 | Echte Browser-/UI-Brücke | `FAIL` | MCP meldet ausdrücklich „synthetic“ und „no real screen capture“ | Echte Session, Screenshot, Koordinaten-/Semantik-Aktionen und Zustandsbeobachtung | [G04](04-real-browser-bridge.md) |
| G05 | Visueller Screenshot-Aktions-Regelkreis | `BLOCKED` | nur Testskripte/Fixtures, kein Agenten-End-to-End-Kanal | Zwei-Screenshot-Loop mit echter Aktion und unabhängiger Zustandsprüfung | [G05](05-visual-interaction-loop.md) |
| G06 | Reale Quick Flows | `PARTIAL` | Contracts und synthetische Schritte vorhanden | Mindestens drei reale, versionierte Flows mit Fallback und Step Evidence | [G06](06-real-quick-flows.md) |
| G07 | Surface-Integration A/B/C | `PARTIAL` | Custom GPT Actions und Codex-MCP getrennt vorhanden | ehrliche, live geprüfte Capability-Matrix für A/B/C | [G07](07-surface-integration.md) |
| G08 | Safety, Datenschutz und Autorisierung | `PARTIAL` | starke Repo-/Action-Gates; Browsergrenze noch nicht real bewiesen | Domain-Allowlist, Lease, Limits, Sanitization und Negativtests am Realpfad | [G08](08-security-privacy-and-authorization.md) |
| G09 | Evidence und Provenance | `PARTIAL` | Measurement-Vertrag, JSONL-Adapter und Raw Capture vorhanden | Browser-Evidence retained, gehasht, run-gebunden; keine erfundenen Nullwerte | [G09](09-evidence-and-provenance.md) |
| G10 | Test-, Fault- und Stabilitätsloops | `PARTIAL` | breite Batteries und synthetische UI-Lab-Tests vorhanden | Black-Box-Realpfad, Negative, Regression, Full Gate, unveränderter Replay | [G10](10-testing-stability-and-recovery.md) |
| G11 | Brother-GPT-Eskalation und Dokumentpflege | `PARTIAL` | Escalation Skill vorhanden; neue Governance lokal | einmaliger geprüfter Handoff, Self-Review, Lead-Review und Herkunftsblock | [G11](11-brother-gpt-escalation.md) |
| G12 | Release, Migration und Betrieb | `BLOCKED` | Kandidat lokal/teilweise gemergt; Kernpfad nicht fertig | PR/Merge, Installation, Post-Merge-Canary, Rollback und finale Einsatzentscheidung | [G12](12-release-migration-and-operations.md) |

## 5. Kritischer Pfad

Die Ausführung folgt grundsätzlich dieser Reihenfolge:

`G00 → G01 → G02 → G03 → G04 → G05 → G06 → G07 → G08/G09 → G10 → G11 → G12`

G08 und G09 werden bei jedem Implementierungsschritt mitgeführt. Sie dürfen die Kernfunktion nicht durch endlose Metaaudits verdrängen.

Der nächste produktive Schwerpunkt ist:

`G02 Plugin-Paket preflighten → G03 ChatGPT-Verbindung beweisen → G04 echte Browser-Brücke implementieren.`

## 6. Globale Control-Loop-Regel

Für jeden Gate-Schritt:

1. `ORIENT`: Master, Statusregister und genau ein aktives Detaildokument lesen.
2. `FRESH`: Main, HEAD, Worktree und betroffene Vertrags-Hashes prüfen.
3. `PREFLIGHT`: Abhängigkeiten, Berechtigungen, Testumgebung und Host-Grenze vor dem Write prüfen.
4. `RED`: kleinstes scheiterndes Akzeptanz- oder Negativkriterium herstellen.
5. `FIX`: kleinsten wiederverwendenden Patch umsetzen.
6. `TARGETED`: Gate-spezifischen Test ausführen.
7. `NEGATIVE`: Fehlpfade und Safety prüfen.
8. `REGRESSION`: nur betroffene bestehende Suites ausführen.
9. `EVIDENCE`: Resultate, Hashes und Evidence-Stufe festhalten.
10. `GATE`: `PASS`, `PARTIAL`, `BLOCKED` oder `FAIL` entscheiden.
11. `CHECKPOINT`: nächsten Schritt speichern; bestandene Arbeit nicht wiederholen.

Bei einem unbekannten Problem wird nicht geraten. Es gilt [G11](11-brother-gpt-escalation.md).

## 7. Regeln für kleinere Modelle

- Immer nur ein Gate und ein kleinster Sub-Step gleichzeitig.
- Keine Architektur aus Chatverlauf rekonstruieren; diese Dokumente sind der Arbeitsindex.
- Keine neue Bibliothek oder Plattform, bevor vorhandene KGG-Komponenten geprüft wurden.
- Keine erfundenen Kommandos; Befehle aus Repo, Detaildokument oder Testregister ableiten.
- Keine Vollanalyse nach jedem Resume; nur Hashes und betroffene Checkpoints prüfen.
- Kein `PASS` ohne Evidence-Link, ausgeführten Test und geforderte Evidence-Stufe.
- Bei Unsicherheit genau einen gezielten Read; danach Brother-Handoff statt Schleife.
- Keine Mikrofreigaben innerhalb eines bereits aktivierten bounded Envelopes.

## 8. Zugehörige Steuerdateien

- Maschinenlesbarer Gate-Stand: [gate-status.json](gate-status.json)
- Einheitliche Struktur: [gate-template.md](gate-template.md)
- Driftfester Arbeitsauftrag: [kgg-project-completion-goal-prompt.md](kgg-project-completion-goal-prompt.md)
- Brother-Handoff und Herkunftsregeln: [G11](11-brother-gpt-escalation.md)
