# 2026-08-13 - Custom-GPT Antwortzug-Reaktivierung und Editor-/Action-Drift

## Problem

Ein KGG Custom GPT kann nach dem Ende seines ChatGPT-Antwortzugs nicht selbst
einen neuen Antwortzug starten. Ein laufender GitHub-Workflow kann zwar weiter
arbeiten, aber Run-, Job- und Artifact-Status werden danach nicht von selbst
erneut gelesen. Wenn Codex den GPT erneut aktiviert, kann ohne klare Uebergabe
ein doppelter Preview-Dispatch, eine falsche Fortschrittsbehauptung oder ein
unerkannter Editor-/Knowledge-/Action-Drift entstehen.

## Zeit

- `2026-08-13T18:51:16Z` - beobachtete Workflow-Grenze und dokumentierte
  Reaktivierungsregel.

## GPT

- Betroffene Profile: `KGG Update-Agent` und `KGG Patienten-App Update-Agent`.
- Die konkrete GPT-ID wird nur genannt, wenn sie fuer den Beleg noetig ist;
  niemals Authentisierung, Patientendaten oder Chat-Inhalt protokollieren.

## Auftrag/Ziel

- Sicheres Fortsetzen eines bereits gestarteten Read-/Run-Pruefvorgangs ohne
  neuen Preview-, PR- oder Live-Dispatch.
- Sicheren Stopp bei nicht bestaetigtem Editor-/Knowledge-/Action-Vertrag.

## Vorheriger sichtbarer Zustand/Run-ID

- `response_turn_ended`: der vorherige Antwortzug ist beendet; der GPT kann
  keinen neuen Chat- oder Pollingzug selbst starten.
- `empty_response`, `aborted_response` oder `answer_timeout`: die sichtbare
  GPT-Antwort war leer, abgebrochen oder zeitlimitiert und muss bei einer
  erneuten Aufforderung als vorheriger Zustand festgehalten werden.
- `monitoring_ambiguous`: Ein sichtbarer Button `Antwort stoppen` kann auch
  nach mehreren bereits vollstaendig sichtbaren Antworten noch aktiv bleiben.
  Er ist deshalb kein alleiniger Beweis fuer `in_progress`.
- `model_ui_ambiguous`: Editor-Auswahl und Preview-Banner koennen verschiedene
  Modellbezeichnungen anzeigen. Das beweist keinen Modellwechsel.
- `manual_reactivation`: Codex startet einen neuen, begrenzten GPT-Auftrag.
- `editor_drift` oder `action_drift`: Editor-Konfiguration, Knowledge oder
  Actions stimmen nicht nachweisbar mit dem Resource-Manifest ueberein.
- `stale_context`: ein benoetigter Live-Read, Source-Hash oder Main-Beleg fehlt.

## Beleg

- `docs/kgg-custom-gpt-playbook.md` und der Admin-Bootstrap erlauben Polling
  nur innerhalb des laufenden Antwortzugs; die externe GitHub-Pipeline kann
  danach weiterlaufen, der ChatGPT-Dialog aber nicht selbst fortsetzen.
- `docs/kgg-patient-custom-gpt-editor-snapshot.json` steht bis zu einer echten
  Editor-Pruefung auf `target-pending-live-editor-sync`; dieser Zustand ist
  kein Nachweis fuer sichere Patient-Actions.
- Der jeweils aktuelle Nachweis ist der passende
  `kgg_custom_gpt_resource_audit.py --check`-Lauf plus Run-/Artifact-Status
  oder eine echte Editor-Pruefung, nie eine erinnerte Chat-Aussage.
- Mehrere vollstaendig sichtbare Browser-Antworten hatten weiterhin den aktiven
  Button `Antwort stoppen`. Completion wird deshalb ueber Antwortinhalt,
  Action-Ergebnis, Run-Beleg oder einen stabilen Textzustand festgestellt,
  niemals nur ueber diesen Button.
- Die Editor-Auswahl hielt `Thinking 5.6`, waehrend ein Preview-Banner
  `Vom Ersteller empfohlenes Modell wird verwendet: GPT-5.6 Sol` zeigte.
  Das ist eine UI-/Verifikationsmehrdeutigkeit, kein behaupteter Modellwechsel.

## Auswirkung

- Ohne Reaktivierung bleibt nur der zuletzt belegte Zwischenstand bekannt.
- Nach `editor_drift`, `action_drift` oder `stale_context` sind Preview-, PR-
  und Live-Writes gesperrt.
- Eine Reaktivierung darf denselben Run lesen, aber keinen bereits gestarteten
  Preview-Workflow erneut dispatchen.
- Kosten-/Leistungsbehauptungen duerfen nicht aus widerspruechlichen
  Modellbeschriftungen abgeleitet werden.

## Reaktivierungsaktion

1. Codex legt fuer jede Reaktivierung, leere/abgebrochene/zeitlimitierte
   Antwort oder jedes Hindernis einen datierten Eintrag im bestehenden
   `docs/bug-debug/`-Format an.
2. Der reaktivierte GPT laedt zuerst Manifest, Live-Kontext, Playbook und die
   aktuelle Main-SHA; danach liest er nur den bestehenden Run, Jobs und
   Artifacts. Ohne frischen Live-Vertrag kein neuer Dispatch.
3. Bei Editor-/Action-Drift erst die kanonischen Dateien im Editor abgleichen,
   den Snapshot ehrlich auf `live-synced` verifizieren und den strengen Audit
   ausfuehren. Bis dahin bleibt der Status `target-pending-live-editor-sync`.
   Aendert ein Patient-Feature die generierten Patient-GPT-Context-, Source-
   oder Knowledge-Artefakte, bleibt dessen Feature-Branch ebenfalls ehrlich
   `target-pending-live-editor-sync`: zuerst Feature-PR mergen, dann den
   Editor gegen die neuen Artefakte und Live-Reads synchronisieren und erst
   danach den `live-synced`-Snapshot in einem separaten Commit/PR festhalten.
   Niemals einen alten Live-Sync in einem Ressourcen-Aenderungsbranch behalten.
4. Wiederkehrende Muster werden nach Review als dauerhafte Lesson ueber das
   vorhandene KGG Project Memory Gate aufgenommen; ein einzelnes Laufzeitereignis
   wird nicht als Chat oder Memory-Muell gespeichert.
5. Bei `monitoring_ambiguous` wird Completion nur aus Antwortinhalt,
   Action-Ergebnis, Run-Beleg oder stabilem Textzustand bestimmt. Bei
   `model_ui_ambiguous` zuerst Editor-Auswahl und das Action-Verhalten
   pruefen; erst danach sind Modell-, Kosten- oder Performanceaussagen erlaubt.

## Ergebnis

- Die Wiederaufnahme liefert entweder einen belegten aktualisierten Run-Status
  oder einen weiterhin klar dokumentierten Blocker. Sie darf weder einen
  doppelten Preview-Dispatch noch eine unbelegte Erfolgsmeldung erzeugen.

## Folgeaktion

- Nur nach spaeterer gezielter Auswertung wird ein wiederkehrendes Muster an
  Instructions, Knowledge, Actions oder Tests angepasst und danach getestet.
  Dieses Ereignis aendert keine Regel automatisch.

## Ursache

ChatGPT-Antwortzuege und GitHub-Workflows haben getrennte Lebenszyklen. Die
Action-Reads koennen nur waehrend eines aktiven Antwortzugs ausgefuehrt werden.
Editor-Instructions, Knowledge-Dateien und OpenAPI-Actions werden ausserhalb
des Repositorys manuell verwaltet und koennen deshalb vom lokalen Vertrag
abweichen.

## Loesung/Fix

- Polling nach einem Dispatch im selben Antwortzug maximal ausnutzen und bei
  Ablauf nur den nachweisbaren Zwischenstand melden.
- Jede notwendige Codex-Reaktivierung, leere/abgebrochene/zeitlimitierte
  Antwort oder Drift als vorhandenen Bug-Debug-Handoff erfassen; der GPT
  liefert Zeit, GPT, Auftrag/Ziel, vorherigen sichtbaren Zustand/Run-ID,
  Auswirkung, Reaktivierungsaktion, Ergebnis und Folgeaktion, Codex speichert
  sie.
- Vor jeder Action-Nutzung Resource-Manifest, Editor-Snapshot und aktuelle
  Live-Reads abgleichen. Drift ist ein sicherer Stopp, kein Anlass zum Raten.
- Ein Ereignis veraendert keine GPT-Regel automatisch; Verbesserung folgt nur
  dem Ablauf dokumentieren -> spaeter auswerten -> gezielt aendern -> testen.
- Patient-GPT-Ressourcen haben einen festen Releaseablauf: Feature-PR merge ->
  Editor auf neue Artefakte und Live-Reads synchronisieren -> erst danach
  `live-synced`-Snapshot in separatem Commit/PR. Ein Ressourcen-Aenderungsbranch
  behaelt niemals einen alten Live-Sync.
- Browser-UI-Signale nur als Hinweis behandeln: Der sichtbare Button
  `Antwort stoppen` beweist keinen laufenden Vorgang; abweichende Modelllabels
  beweisen keinen Modellwechsel. Beide Beobachtungen zuerst gegen Actions,
  Run-Belege und die tatsaechliche Editor-Auswahl pruefen.

## Test / Abnahmekriterien

- `python release-pipeline/kgg_bug_knowledge.py --check` ist gruen.
- `python release-pipeline/kgg_custom_gpt_knowledge_pack.py --check` ist gruen.
- `python release-pipeline/kgg_patient_gpt_resources.py --check` ist gruen.
- Der Resource-Audit akzeptiert nur passende Hashes; nach einer kanonischen
  Knowledge-Aenderung bleibt ein Profil bis zur echten Editor-Pruefung ehrlich
  `target-pending-live-editor-sync`.
- Ein reaktivierter GPT liest den vorhandenen Run und erzeugt keinen zweiten
  Preview-Dispatch.

## Nicht anfassen

- App-Feature-Code, PDF, QR-/Patienten-App-Vertrag, Scan/OCR, Parser,
  Plan-State, Medien/Upload, Android/APK, Manifest und Geheimnisse.
- Keine Patientendaten, echte Plan-/QR-Payloads, Chats, Tokens oder Rohdaten im
  Bug-Debug-Log, in der Koordination oder im Project Memory speichern.

## Folge-Risiken

- Ein fehlender Ereignislog erschwert spaetere Workflow-Verbesserungen und kann
  doppelte Dispatches beguenstigen.
- Ein fiktiver `live-synced`-Status trotz geaenderter Knowledge oder Actions
  wuerde Editor-Drift verdecken.
- Die Queue oder ein GitHub-Workflow startet keinen GPT automatisch; das muss
  im Handoff klar bleiben.

## Folgeereignis 2026-08-20 - Read-only-Statuszug ohne Abschluss

### Vorheriger sichtbarer Zustand/Run-ID

- `manual_reactivation`: Ein neuer, begrenzter Read-only-Auftrag wurde im
  Admin-GPT gestartet.
- Auftrag: Main-SHA, PR-/Gate-Status und GPT-eigene Grenzen ermitteln; kein
  Preview, kein Dispatch, kein Memory-Update und keine Codeaenderung.
- Der GPT zeigte nacheinander nur Zwischenmeldungen wie
  `Konfiguration zusammenfassen`, `Arbeitsablaeufe einordnen` und
  `Offene Themen geordnet`; eine belastbare Abschlussantwort oder Run-ID wurde
  nicht geliefert.
- Der Browser-Antwortzug ueberschritt nach mehreren Live-Reads das lokale
  Ausfuehrungs-/Zeitfenster. Es wurde kein Write und kein Dispatch beobachtet.

### Auswirkung

- Der GPT konnte den Statusauftrag in diesem Antwortzug nicht abschliessen.
- Die sichtbare Schaltflaeche `Antwort stoppen` war dabei kein belastbarer
  Beweis fuer echten Fortschritt; sie darf nicht als Run-Status verwendet
  werden.
- GitHub-Status wurde deshalb separat read-only mit dem vorhandenen CLI
  geprueft. Der GPT wurde nicht mehrfach blind neu angestossen.

### Reaktivierungsaktion und Folgeaktion

- Codex uebernimmt bei einem erneuten Timeout die konkrete Statusabfrage direkt
  aus der kanonischen Read-only-Quelle und notiert nur belegte Werte.
- Zukuenftige GPT-Statusauftraege werden in einzelne kleine Auftraege geteilt:
  erst Main/PRs, danach Runs, danach offene GPT-Aufgaben. Jeder Auftrag darf
  maximal einen begrenzten Read-/Action-Satz enthalten.
- Ein erneuter GPT-Auftrag darf keinen bereits begonnenen Preview-/PR-/Live-
  Dispatch wiederholen. Vor einer Wiederaufnahme werden sichtbarer Zustand,
  Auftrag, Startzeit und vorhandene Run-ID notiert; fehlt eine Run-ID, bleibt
  der Zustand `no_verified_run`.
- Dieses Ereignis aendert keine Instructions, Knowledge-Datei oder Action
  automatisch. Eine dauerhafte Anpassung folgt nur nach Auswertung,
  gezielter Aenderung und Tests.

## Bereiche

- debug
- sync
