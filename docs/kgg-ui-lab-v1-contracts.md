# KGG UI Lab V1 – Vertragskern

Stand 14. September 2026. Dieser Vertrag beschreibt die ersten lokalen,
reversiblen Architektur-Slices. Der semantische Browser-Runner und der
MCP-shaped Adapter sind jetzt als injizierbare Vertragsimplementierungen
vorhanden; sie öffnen noch keinen echten Browser und kein anderes GPT.

## Session und Runner

`release-pipeline/kgg_ui_lab_contract.py` prüft die Schemata
`kgg-ui-lab/session/v1`, `kgg-ui-lab/request/v1` und `kgg-ui-lab/event/v1`.

`release-pipeline/kgg_ui_lab_session.py` kapselt darauf aufbauend die lokale
`RunnerRegistry`, den `SessionStore` und die `QuickFlowRegistry`. Alle drei
Stores sind derzeit bewusst in-memory. `kgg_ui_lab_browser.py` nimmt nur einen
semantischen Observer entgegen; `kgg_ui_lab_mcp_adapter.py` stellt den festen
Tool-Katalog ohne Shell-, Editor-, Live- oder externe Nachrichten-Operationen
dar.

Die semantische Browser-Schrittmenge deckt `click`/`tap`, `type`, `scroll`,
`reload`, `back`, `read_state` und `capture_screenshot` ab. `wait` ist ein
expliziter, host-ausführbarer Schritt mit einer fail-closed Obergrenze von
5.000 ms; der Contract stellt keinen unbounded sleep bereit.

- Sessions sind an einen Actor, eine Ablauf-Lease, Main-/Preview-SHA, einen
  Runner und ein synthetisches Device-Profil gebunden.
- HTTPS ist Pflicht; unverschlüsseltes HTTP ist nur für `localhost` bzw.
  `127.0.0.1` erlaubt.
- Capability-Gates werden vor einer Operation geprüft. Eine UI-Ausblendung ist
  keine Berechtigung.
- Event-Logs sind append-only, beginnen bei Sequenz 1, sind lückenlos und
  akzeptieren dieselbe Request-/Event-Kombination nicht zweimal.
- Evidenz besteht nur aus gehashten Artefakt-Referenzen. Roh-QR, Tokens,
  Browserrohtext, Secrets und Patientendaten werden fail-closed abgewiesen.

## Retry und Bruder-Fallback

`release-pipeline/kgg_ui_lab_runtime.py` klassifiziert Fehler in die elf
öffentlichen Klassen des Zielauftrags. Transiente Fehler bekommen höchstens
einen unveränderten Retry. Danach wird entweder ein lokaler Bruder-Handoff
erzeugt oder bei geschützten Zuständen (`permission`, `editor_drift`, Replay)
direkt für Max pausiert.

Der Bruder-Handoff:

- trägt `kgg-brain-relay-worker/handoff-v2` als Transportvertrag,
- bleibt zunächst `local_queue_only` und `PENDING_USER_CONFIRMATION`,
- enthält ausschließlich eine kurze Problembeschreibung und gehashte
  Evidenz-Referenzen,
- verbietet Ziel-, Scope-, Safety-, Hash-, Berechtigungs- und Release-
  Änderungen.

Eine Bruder-Antwort darf nur taktische Felder wie Retry-Budget, Timeout,
Schrittfolge, Evidenzfelder oder Quick-Flow vorschlagen. Jede Scope-, Ziel- oder
Gate-Änderung wird als `MAX_REQUIRED` gestoppt.

`release-pipeline/kgg_ui_lab_migration_gate.py` wertet die fünf unabhängigen
Migrations-Gates (`PARITY_PASS`, `SAFETY_PASS`, `EFFICIENCY_PASS`,
`CROSS_SURFACE_PASS`, `STABILITY_PASS`) fail-closed aus. Selbst ein
`MIGRATION_ELIGIBLE`-Ergebnis autorisiert keinen Release oder externen Write.

`release-pipeline/kgg_ui_lab_fault_injection.py` führt zusätzlich eine
deterministische, lokale Matrix für die elf im Zielauftrag genannten
Fehlerfälle aus. Jede Injektion endet entweder beim begrenzten Retry/Bruder-
Pfad oder bei `MAX_REQUIRED`; die Matrix kann selbst keinen externen Write
auslösen.

## Testschleife

Die Contract-, Quick-Flow-, Browser-, MCP-, Candidate-Gate- und Fallback-Tests
laufen als eigener `ui-lab`-Eintrag in der Critical-Test-Battery. Der sichere
Ausbaupfad bleibt:

1. Contract Red → Green (erledigt).
2. Lokale Runner-Registry, SessionStore und QuickFlowRegistry (erledigt).
3. Browser- und Quick-Flow-Adapter mit unverändertem Replay (semantisch
   umgesetzt).
4. Sichere Evidence-Artefakte und simulierter Bruder-Handoff (umgesetzt).
5. Drei zertifizierte Quick Flows einschließlich #180-Reproduktion (Vertrag
   umgesetzt).
6. Expliziter synthetischer Read-only-Live-Pilot im internen Browser (zwei
   unveränderte lokale Runden sind im Report
   `docs/kgg-ui-lab-v1-pilot-2026-09-14.md` belegt; Fresh-Main-Parität bleibt
   offen).

Bis zu einem erfolgreichen Pilotnachweis gibt es keinen Main-/Live-/Patient-
Release und keine automatische externe GPT-Nachricht.
