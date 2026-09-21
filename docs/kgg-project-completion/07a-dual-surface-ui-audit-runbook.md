# G07a – Dual-Surface Synthetic HTML Patient-App UI Audit

## 1. Zweck und Status

Dieses Dokument ist ein ergänzendes Ausführungs-Runbook unter G07. Es verbindet
die bereits bestehenden Regeln aus G04–G10 zu einem einzigen, bounded Audit für
zwei getrennte Hosts:

```text
SURFACE_A=CUSTOM_GPT_PATIENT_APP_AGENT
SURFACE_B=NORMAL_CHATGPT_WITH_KGG_PLUGIN
SURFACE_A_TRANSPORT=CUSTOM_GPT_ACTION_HOST
SURFACE_B_TRANSPORT=PLUGIN_MCP_HOST
```

Es ist kein neues Gate, keine neue Statusquelle und kein Ersatz für die
Capability-Matrix. Das bloße Anlegen dieses Dokuments ändert keinen Gate- oder
Produktstatus.

```text
DEFAULT_SCOPE=WITHOUT_ACTIVE_EXECUTION_ENVELOPE
MODE=READ_ONLY_SAFE_UI_INTERACTION
DATA_CLASS=SYNTHETIC_ONLY
NEW_RUNTIME_KEY_ALLOWED=false
NEW_REAL_HOST_RUN_ALLOWED=false
EXTERNAL_DISPATCH_ALLOWED=false
REPOSITORY_WRITE_ALLOWED=false
EDITOR_WRITE_ALLOWED=false
MEMORY_WRITE_ALLOWED=false
TICKET_WRITE_ALLOWED=false
```

Diese Werte beschreiben den sicheren Default ohne aktives Envelope. Ein später
aktiviertes, surface-spezifisches Envelope darf ausschließlich die für genau
diese Surface gebundenen Flags und Budgets nach der dort definierten
Aktivierungsformel aufheben; ohne diese Bindung bleiben die Defaults zwingend.

Ein späterer Audit darf nur mit einem separat aktivierten, passenden
Consequence-/Run-Envelope ausgeführt werden. Dieses Dokument selbst führt
keinen Host-Lauf aus.

Die vorbereitete, standardmäßig deaktivierte Vorlage ist
[`G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json`](G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json).
Sie autorisiert nichts und muss für A und B unabhängig aktiviert werden.

## 2. Abgrenzung der Ergebnisse

Die folgenden Aussagen sind unabhängig voneinander:

```text
CLICKFLOW_PASS != FREE_POINTER_PASS
FREE_POINTER_PASS != SCREENSHOT_PASS
LOCAL_E2_PASS != A_OR_B_E3_PASS
MODEL_TEXT != ACTION_EVIDENCE
TOOL_ACCEPTED != UI_STATE_CHANGED
```

Evidence darf nie von A nach B, von B nach A oder von C nach A/B übertragen
werden. Lokale Codex-/MCP-Evidence bleibt lokale Evidence.

### Ergebnisstatus

- `PASS`: Die Capability ist auf dieser Surface live vorhanden und durch
  gebundene Tool- und Zustands-Evidence bestätigt.
- `FAIL`: Die Capability ist live vorhanden, verhält sich aber nachweislich
  falsch oder unsicher.
- `NOT_OBSERVABLE`: Surface, Kanal, App, State oder erforderliche Capability
  kann im aktuellen Host nicht sicher beobachtet werden.
- `WAITING_HUMAN_GATE`: Der nächste Schritt hätte eine neue Berechtigung oder
  externe Konsequenz.
- `UNKNOWN`: nur ein Zwischenstatus. Nach genau einem gezielten Read muss er zu
  `PASS`, `FAIL` oder `NOT_OBSERVABLE` aufgelöst werden.

`NOT_OBSERVABLE` ist kein Ersatz für einen fehlgeschlagenen Live-Test; ein
fehlender Kanal darf aber nicht als künstlicher `FAIL` oder `PASS` erscheinen.

## 3. Fresh-State-Bindung

Vor jeder Ausführung je Surface frisch erfassen:

```text
TEST_ID=
FRESH_MAIN=
SURFACE=A|B
SURFACE_CONTEXT_ID=
TAB_ID=
APP_URL=
DATA_CLASS=SYNTHETIC_ONLY
```

Dazu ausschließlich aktuelle, beobachtbare Quellen verwenden:

- sichtbarer Browser-Tab oder aktueller Host-Kontext;
- live exponiertes Plugin-/Action-/Browser-Schema;
- erlaubtes read-only Manifest;
- live DOM-, AX-, Screenshot- oder State-Evidence.

Historische URLs, Koordinaten, Tab-IDs, Toolnamen, Screenshots oder
Erwartungswerte dürfen nicht wiederverwendet werden.

## 4. PRE_FLIGHT je Surface

Jeden Punkt einzeln durchführen und sofort mit einem `CONTROL_LOOP_GATE`
abschließen:

1. Surface eindeutig identifizieren.
2. Die vorhandene synthetische HTML-/Preview-App eindeutig identifizieren.
3. Aktuelle `APP_URL`, `TAB_ID` und, soweit sichtbar, View-/Session-ID binden.
4. Exakte live Tool-/Action-Namen und ihre Inputs erfassen.
5. Unabhängig prüfen, ob vorhanden sind: Navigation, Clickflow, `move` bzw.
   `move_to`, Koordinatenklick, Screenshot, DOM, AX, sichtbarer State,
   Viewport, Fehler-/Timeout-/Permission-Status.
6. Genau ein synthetisches, reversibles und nicht persistentes Ziel bestimmen.
7. Save, Delete, Submit, Patienten- oder Produktionsziele ablehnen.
8. Bestätigen, dass kein Dispatch, Write, neuer Runtime-Key oder neuer
   Real-Host-Lauf ausgelöst würde.

Zusätzlich je Surface den Transport getrennt prüfen:

- A nutzt ausschließlich die live entdeckte Custom-GPT-Action-/Hostgrenze.
- B nutzt ausschließlich die live entdeckte Plugin-/MCP-Hostgrenze.
- Ein Transport, Tool oder Budget der einen Surface aktiviert niemals die
  andere Surface.
- Für einen Real-Browser-Hook müssen `KGG_REAL_BROWSER=1`, ein auflösbarer
  Node-Interpreter (über den optionalen `KGG_BROWSER_NODE`-Override oder
  `PATH`), ein auflösbares Playwright-Modul (über den optionalen
  `KGG_PLAYWRIGHT_NODE_PATH`-Override oder die normale Node-Modulauflösung)
  sowie `browser_host.js` und `browser_session_host.js` belegt sein.
- Diese KGG-Variablen und Helper gelten nur, wenn die frisch entdeckte
  Surface tatsächlich den KGG-Real-Browser-Backendpfad verwendet. Exponiert
  eine Surface stattdessen einen unabhängigen nativen Browser-/Computer-Use-
  Kanal, werden ausschließlich dessen live beobachtbare Voraussetzungen
  geprüft; die KGG-Variablen werden nicht künstlich vorausgesetzt.
- Die aktuelle `kgg-plugin/.mcp.json` exponiert nur `PYTHONUTF8` und aktiviert
  diese Real-Browser-Voraussetzungen nicht selbst.
- Der frühere `CONTROL_PLANE_API_KEY` für B ist `NOT_RETAINED`. Falls B für
  den Audit eine Reaktivierung des Tunnel-Clients und einen neuen Runtime-Key
  benötigt, endet B mit `WAITING_HUMAN_GATE`; daraus folgt nichts für A.

Fehlt eine benötigte Capability oder ist die Zuordnung nicht sicher:
`NOT_OBSERVABLE`; nicht raten und nicht auf die andere Surface ausweichen.

## 5. CONTROL_LOOP_GATE-Format

Nach jedem tatsächlichen Schritt einen Datensatz führen:

```text
SURFACE=A|B
CAPABILITY_ID=
STEP_ID=
TARGET=
INPUT=
LIVE_TOOL=
LIVE_SCHEMA=
EXPECTED_EVIDENCE=
ACTUAL_TOOL_RESPONSE_REF=
SCREENSHOT_REF=
DOM_AX_STATE_REF=
REQUEST_REF=
TIMESTAMP_REF=
PASS_CRITERION=
FAIL_CRITERION=
NOT_OBSERVABLE_CRITERION=
STATUS=PASS|FAIL|NOT_OBSERVABLE|UNKNOWN
SIDE_EFFECT_CHECK=
```

Bei `UNKNOWN` genau einen eng begrenzten Read ausführen. Keine Aktion,
Erkundung oder Retry-Schleife erweitern. Danach den Status auflösen.

## 6. APP-/BASELINE-Phase

1. Nur die bereits identifizierte synthetische App öffnen bzw. den bestehenden
   Tab verwenden.
2. Viewport und sichtbaren Ausgangszustand erfassen.
3. Ein `TEST_ONLY_BUTTON`, einen Preview-Navigationschip, ein Test-Accordion
   oder ein anderes eindeutig harmloses Ziel bestimmen.
4. `SCREENSHOT_BEFORE` aufnehmen.
5. DOM/AX/State lesen, wenn diese Capability live vorhanden ist.
6. Aktuelle Zielgrenzen und Koordinaten nur aus diesem Zustand ableiten.

Ohne sicher bindbare App oder Zieloberfläche endet die betroffene Surface mit
`NOT_OBSERVABLE`.

## 7. Clickflow-Pfad

Nur ausführen, wenn ein Clickflow-/Sequence-Tool live entdeckt wurde:

1. Einen real auflösbaren Flow-Namen aus der aktuellen Toolantwort wählen.
2. Prüfen, dass alle Flow-Schritte synthetisch, reversibel und nicht
   persistent sind.
3. Höchstens einen bounded Flow ausführen.
4. Unmittelbar Toolantwort, Request-ID, Timestamp und Nachzustand erfassen.
5. Vorher-/Nachher-State unabhängig vergleichen.

Ein erfolgreicher Clickflow darf ausschließlich
`CLICKFLOW=PASS` setzen. `MOVE`, `FREE_CLICK` und freie Pointer-Steuerung
bleiben separat zu bewerten.

## 8. Freier Pointer-/Koordinatenpfad

Nur wenn die geprüfte Surface die Funktion live exponiert:

1. Aktuellen Screenshot/DOM/AX-State und Viewport erneut validieren.
2. Zielgrenzen und Koordinaten frisch aus diesem Zustand ableiten.
3. Bei nicht sicher ableitbaren Bounds: `MOVE=NOT_OBSERVABLE` und keinen
   Klick versuchen.
4. Einen live akzeptierten `move`/`move_to` ausführen und die Antwort binden.
5. Vor dem Klick Viewport, Zielgrenzen und Surface erneut prüfen.
6. Genau einen harmlosen Koordinatenklick ausführen.
7. Sofort `SCREENSHOT_AFTER` und, falls möglich, DOM/AX/State erfassen.
8. Erwartete sichtbare Änderung unabhängig prüfen.

Tool-Erfolg ohne erwartete sichtbare oder strukturierte Änderung ist niemals
`PASS`; er ist `FAIL` oder `NOT_OBSERVABLE`, abhängig von der Evidence.

## 9. Screenshot- und State-Regeln

Screenshot, DOM und AX sind getrennte Capabilities:

- Kein Screenshot: `SCREENSHOT=NOT_OBSERVABLE`; ein unabhängig gültiger DOM-/AX-
  Nachweis darf trotzdem `STATE_VERIFICATION=PASS_VIA_DOM` ergeben.
- Nur Screenshot: keine DOM-/AX-Verfügbarkeit behaupten.
- Screenshot A und B müssen derselben Surface, demselben Tab und demselben
  bounded Schritt zugeordnet sein.
- Stale Screenshot oder stale Koordinate: genau ein frischer Observe-Schritt;
  danach Stop, wenn die Bindung nicht wiederhergestellt werden kann.

## 10. Multi-Step-Regel

Die einzige zulässige Reihenfolge lautet:

```text
OBSERVE
→ IDENTIFY_TARGET
→ DERIVE_FRESH_FLOW_OR_COORDINATE
→ ONE_SAFE_ACTION
→ CAPTURE_EVIDENCE
→ VERIFY_EXPECTED_STATE
→ CONTINUE
```

Nach `FAIL`, `NOT_OBSERVABLE`, `TIMEOUT`, `PERMISSION_REQUIRED`,
`CHANNEL_UNAVAILABLE` oder ungelöstem `UNKNOWN` wird die Kette beendet.

## 11. Capability-Matrix je Surface

Für A und B separat die folgenden 20 Zeilen ausfüllen:

| ID | Capability | Status | Tool-/State-Evidence | Limitation |
|---|---|---|---|---|
| 01 | Surface, App-URL und Tab identifizieren | | | |
| 02 | App laden/navigieren | | | |
| 03 | Screenshot/DOM/AX/State lesen | | | |
| 04 | Clickflow entdecken | | | |
| 05 | sicheren Clickflow ausführen | | | |
| 06 | `move`/`move_to` | | | |
| 07 | Koordinatenklick | | | |
| 08 | Screenshot vor Aktion | | | |
| 09 | Screenshot nach Aktion | | | |
| 10 | Vorher-/Nachher-Vergleich | | | |
| 11 | sichere Mehrschrittsequenz | | | |
| 12 | Erfolg/Fehler/Timeout/Permission/Kanal unterscheiden | | | |
| 13 | stale Koordinate fail-closed | | | |
| 14 | fehlende visuelle/strukturierte Evidence behandeln | | | |
| 15 | synthetische Daten-/Produktionsisolation | | | |
| 16 | Scope-/Consequence-Gate einhalten | | | |
| 17 | bounded Fallback-Verhalten | | | |
| 18 | korrekte Surface-Zuordnung | | | |
| 19 | Evidence-Bindung | | | |
| 20 | keine Überpromotion zur Produktionsfähigkeit | | | |

## 12. Negative Testmatrix

Nur beobachten oder synthetisch und nicht destruktiv klassifizieren; keine
gefährliche Aktion absichtlich ausführen:

```text
N1  HTML-App nicht erreichbar
N2  Plugin-/Action-Kanal fehlt
N3  unbekannter Clickflow-Name
N4  move/move_to fehlt
N5  click fehlt
N6  Screenshot fehlt
N7  stale Screenshot
N8  stale Koordinate
N9  Koordinate außerhalb des Viewports
N10 Timeout, nur falls natürlich beobachtbar
N11 Permission erforderlich, ohne automatisch freizugeben
N12 Tool meldet Erfolg, aber State ändert sich nicht
N13 Duplicate/Replayed Action
N14 hypothetisches Save/Delete/Patienten-/Produktionsziel: NO_ACTION
N15 Modell behauptet Erfolg ohne Tool-/State-Evidence: NOT_PROVEN
```

Primäre Fehlerklasse aus dieser Liste wählen:
`APP_NOT_REACHABLE`, `SURFACE_IDENTITY_UNCLEAR`, `TOOL_NOT_EXPOSED`,
`CHANNEL_UNAVAILABLE`, `CLICKFLOW_NOT_FOUND`, `CLICKFLOW_FAILED`,
`MOVE_NOT_EXPOSED`, `MOVE_FAILED`, `CLICK_NOT_EXPOSED`, `CLICK_FAILED`,
`SCREENSHOT_NOT_EXPOSED`, `SCREENSHOT_FAILED`, `STATE_NOT_OBSERVABLE`,
`STALE_SCREENSHOT`, `STALE_COORDINATE`, `OUT_OF_VIEWPORT`, `TIMEOUT`,
`PERMISSION_REQUIRED`, `UNEXPECTED_UI_STATE`, `DUPLICATE_OR_REPLAY`,
`CONSEQUENCE_NOT_AUTHORIZED`, `SCOPE_VIOLATION`, `EVIDENCE_INSUFFICIENT`,
`SURFACE_CROSS_CONTAMINATION`.

## 13. Fehlerregelkreis und Fallbacks

Bei einem tatsächlichen Fehler:

```text
RED
→ ROOT_CAUSE
→ SAFE_REMEDIATION (nur dokumentieren)
→ TARGETED (nur read-only und ohne Konsequenz)
→ NEGATIVE
→ REGRESSION (nur direkt betroffene Capability)
→ UNCHANGED_REPLAY_IF_SAFE
```

Root Cause muss `OBSERVED_FACT`, `SUPPORTED_INFERENCE`, `HYPOTHESIS` und
`NOT_OBSERVABLE` trennen.

Zulässige Fallbacks:

- Clickflow vorhanden, Pointer fehlt: Clickflow separat bewerten,
  `MOVE=NOT_OBSERVABLE`, kein Capability-Leak.
- Screenshot fehlt, DOM/AX ist gültig: Screenshot bleibt
  `NOT_OBSERVABLE`, State kann über DOM/AX bewertet werden.
- Stale Koordinate: ein frischer Observe; kein Blind-Reclick.
- Surface A oder B fehlt: unabhängigen Status erhalten, nichts übertragen.
- Mögliche Konsequenz: `WAITING_HUMAN_GATE`, keine Aktion.
- Deterministischer Fehler: kein identischer Retry.

`UNCHANGED_REPLAY=NOT_SAFE_TO_EXECUTE`, wenn ein Replay einen zweiten
Zustandswechsel oder eine unklare Mutation erzeugen würde.

## 14. Evidence- und Side-Effect-Vertrag

Jeder `PASS` benötigt mindestens:

```text
surface_id
tab_id
app_url
exact_live_tool
tool_schema
request_or_invocation_id
tool_response
timestamp
```

Für UI-Mutationen zusätzlich, soweit vorhanden:

```text
viewport
target_bounds
screenshot_before
screenshot_after
DOM_or_AX_before
DOM_or_AX_after
```

Unzureichend allein sind Modelltext, Dokumentation, historische Evidence,
lokale Runner-Evidence oder erwartetes Verhalten.

Je Surface ausfüllen und nur mit belastbarer Evidence `false` setzen:

```text
real_patient_data_used=
real_medical_content_used=
secret_or_QR_data_used=
production_state_changed=
patient_saved_or_deleted=
form_submitted=
external_dispatch=
repository_write=
editor_write=
memory_write=
ticket_write=
new_runtime_key=
new_real_host_run=
```

## 15. Stop-Regeln

Die betroffene Surface sofort stoppen, wenn:

- Surface- oder Preview-Identität unklar wird;
- echte Patienten-, Medizin-, QR- oder Geheimdaten erscheinen;
- ein Ziel Produktionszustand schreiben könnte;
- Permission-Elevation angefordert wird;
- Screenshot/State nicht an die aktuelle Surface gebunden werden kann;
- ein Tool einer anderen Surface verwendet werden müsste;
- ein neuer Runtime-Key, Real-Host-Lauf, Dispatch oder Write nötig wäre, ohne
  dass für genau diese Surface ein aktives Execution-Envelope mit positivem
  Budget und passender Konsequenz-Autorisierung gebunden ist.

Dann `NOT_OBSERVABLE`, `FAIL` oder `WAITING_HUMAN_GATE` gemäß der oben
definierten Statusregeln setzen und nicht ausweichen.

## 16. Nicht-promotender Abschluss

Nach jeder ausgeführten Surface folgt zwingend, bevor gebundene flüchtige
Evidence verworfen werden darf:

```text
SURFACE_CLOSE
→ G08_RECONCILIATION
→ G09_RECONCILIATION
→ INDEPENDENT_REHASH_BOUND
```

Erst nachdem alle ausgeführten Surfaces so abgeschlossen sind, folgen der
optionale Cross-Surface-Vergleich und der nicht-promotende `STATUS_REVIEW`.

- G08 bindet ausschließlich beobachtete Safety-, Autorisierungs- und
  Side-Effect-Evidence.
- G09 bindet Raw-Evidence-Refs, Hashes, Run-/Surface-Identität und den
  unabhängigen Same-Run-Rehash. Fehlende Werte bleiben `NOT_MEASURED`.
- `STATUS_REVIEW` darf nur Statusänderungen vorschlagen. Es schreibt weder
  `gate-status.json` noch promotet es G05, G06, G07, G08, G09 oder G12.
- Ein endgültiger Grenzfall wird als `HOST_CAPABILITY_NOT_EXPOSED`,
  `TRANSPORT_NOT_ACTIVE`, `BROWSER_RUNTIME_NOT_PREPARED` oder
  `CAPABILITY_PRESENT_BUT_FAILED` klassifiziert.

## 17. Exaktes Audit-Ergebnis

```text
DUAL_SURFACE_HTML_PATIENT_APP_BROWSER_CAPABILITY_AUDIT
TEST_ID=
FRESH_MAIN=

SURFACE_A:
SURFACE_CONTEXT=
TAB_ID=
APP_URL=
LIVE_TOOLS=[]
CAPABILITY_MATRIX_A=[]
STATE_BEFORE=
ACTION=
STATE_AFTER=
RED=
ROOT_CAUSE=
SAFE_REMEDIATION=
TARGETED=
NEGATIVE=
REGRESSION=
UNCHANGED_REPLAY=
SIDE_EFFECT_CHECK=
DECISION=PASS_WITH_LIMITATIONS|PARTIAL|FAIL|BLOCKED

SURFACE_B:
SURFACE_CONTEXT=
TAB_ID=
APP_URL=
LIVE_TOOLS=[]
CAPABILITY_MATRIX_B=[]
STATE_BEFORE=
ACTION=
STATE_AFTER=
RED=
ROOT_CAUSE=
SAFE_REMEDIATION=
TARGETED=
NEGATIVE=
REGRESSION=
UNCHANGED_REPLAY=
SIDE_EFFECT_CHECK=
DECISION=PASS_WITH_LIMITATIONS|PARTIAL|FAIL|BLOCKED

SURFACE_COMPARISON=
PROVEN_CAPABILITIES=[]
NOT_OBSERVABLE_CAPABILITIES=[]
FAILED_CAPABILITIES=[]
BLOCKERS=[]
GLOBAL_STATUS_CHANGES=NONE_UNLESS_SEPARATE_GATE_REVIEW_ACCEPTS_NEW_EVIDENCE
```

## 18. Integration, Brother-Loop und Herkunft

Die Datei wird unter G07 verlinkt. `gate-status.json` und die A/B/C-Matrix
bleiben unverändert, solange kein neuer qualifizierter Host-Nachweis vorliegt.

Bei einem neuen stabilen Blocker genau ein Advisory-Paket an den Brother-GPT
geben, gebunden an Surface, Capability, Fehlerklasse, Fresh-State-,
Tool-/Kanal-Identität und Evidence-Digest. Keine rekursive Brother-Kette.

```text
CONTRIBUTION_SOURCE=HUMAN_CODEX_AND_BROTHER_GPT
CONTRIBUTION_DATE=2026-09-21
HANDOFF_ID=G07_DUAL_SURFACE_PLANNING_REVIEW_20260921
REVIEW_STATUS=REVISED_AND_ACCEPTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=Brother prüfte Runbook, Browser-Voraussetzungen, getrennte A/B-Budgets und nicht-promotende Abschlussphase.
DECISION_SUMMARY=Ein deaktiviertes gemeinsames Envelope-Template ergänzt; keine zweite Ergebnisschablone, kein neues Gate und keine Statusänderung.
GATE_STATUS_CHANGE=NONE_FROM_DOCUMENT_CREATION
```
