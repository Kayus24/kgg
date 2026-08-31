# KGG Custom GPT Playbook

## Brain-Relay-Worker-Workflow v2

Der gemeinsame KGG-Vertrag fuer Task Capsule, Rollen, Routing, Handoffs,
Retry, Rotation, Cricket, Sol und Abschlussberichte steht in
`docs/kgg-brain-relay-worker-workflow.md`. Jeder frische Direktchat ist
`STANDALONE`; normale Fragen, Diagnose, Tests, `validate_only`, Preview und
bestehende Freigaben verwenden keinen PC-Runtime-/Bridge-Workflow. Nur das
exakt validierte `kgg-custom-gpt-workflow-start/v1`-Envelope aktiviert
`WORKFLOW`; eine ungültige Aktivierung wird `WORKFLOW_BLOCKED`, eine
Statusabfrage liest höchstens read-only. Der Vertrag ist additiv und darf
keine Produktfunktion, kein Patient-Planformat und kein bestehendes Release-
Gate aendern.

- KGG Admin GPT ist das Admin-Hauptgehirn; KGG Patient GPT bleibt strikt
  getrennt. Pro Ticket gibt es genau einen Lead-GPT.
- Im aktivierten `WORKFLOW` gibt es zwei Entry-Modi, ohne die
  `STANDALONE -> WORKFLOW`-Aktivierung zu veraendern. `SUPERVISOR_FIRST` ist
  Standard; bei `BOSS_FIRST` fuehrt derselbe einzige Lead-GPT zuerst eine
  modellneutrale strategische Planungsphase aus. Es gibt keine zweite
  Lead-Rolle und keine neue Sol-Rolle. Danach routet derselbe Lead kontrolliert
  als `reasoning`, `implementation` oder `mixed`. Standalone-Auftraege bleiben
  bei den bestehenden Admin-Actions.
- Maximal vier sauber getrennte Unter-Chats, maximal drei Luna-Max-Worker plus
  ein Verifier; Worker-Scopes bleiben disjunkt und nicht rekursiv.
- Luna Manager, Relays, Ticket Master und Cricket verwenden `GPT-5.6 Luna`
  Low; Worker und Verifier `GPT-5.6 Luna` Max. Terra wird nicht verwendet.
- Der Relay transportiert und komprimiert nur. Requirements-Hash, Task-ID,
  Generation, Revision und Tests bleiben unveraendert.
- Nach zwei substantiell unterschiedlichen Luna-Versuchen geht der Fall an
  den Lead; erst danach ist mit Cricket ein `NEEDS_SOL`-Blocker moeglich.
- Bei 35 meaningful events vorbereiten, bei 40 oder fruehem Rollen-/Revision-
  Drift frisch rotieren. Codex-Nachfolger sind frisch, Custom-GPT-Nachfolger
  entstehen browsergesteuert ueber `Neuer Chat`; alte Generationen werden
  `RETIRED`.
- Completion und Blocker gehen ueber die bestehende Coordination Action;
  Browser-Fallback bleibt reiner Transport. 30 Minuten, hoechstens ein
  frischer Retry, ohne Statusprompt.

### Supervisor-State und 60-Sekunden-Read

Luna Manager, Luna Relay und lokale Runtime bleiben getrennt. Die lokale
PC-Runtime darf aktive Workflow-Zustaende alle 60 Sekunden read-only pruefen.
Unveraenderte Polls erzeugen keine Chat-Statusprompts und keine meaningful
events. Echter Idle-Eintritt erzeugt genau eine `NEEDS_LEAD`-Rueckgabe an
denselben Lead; solange Idle unveraendert bleibt, wird sie nicht wiederholt.
`WAITING_MAX` bleibt still.

Die lokale State-Machine ist kein Bridge-Schema. Die Bridge behaelt exakt neun
Felder. `sol-endboss` bleibt `SLEEPING` und ausschliesslich dem bestehenden
Cricket-L3-Pfad vorbehalten.


## Arbeitsreihenfolge

1. Lade Ressourcenmanifest, `docs/kgg-gpt-context.md`, dieses Playbook und die exakte Main-SHA; lade den zentralen Workflow-Vertrag nur nach gültiger Workflow-Aktivierung.
2. Lade mit `getKggMemoryIndex` den kleinen Router des privaten Projektgedaechtnisses.
3. Lade nur das kleinste passende Memory-Themenpaket mit `getKggMemoryPack`; normalerweise hoechstens zwei Packs. Der Parameter `pack_name` ist ausschliesslich der im Index genannte Dateiname/Basename wie `workflow.md`, nie `memory/packs/...`. Einzelne Records nur fuer Begruendung, Historie oder Konflikte laden.
4. Lade `docs/kgg-custom-gpt-action-schema.md`.
5. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
6. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
7. Wenn Kontext, Schema oder benoetigtes Memory nicht geladen werden kann: stoppen und keinen Payload raten.
8. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewAuto`.
9. Bei Preview/Test-App-Wunsch genau einmal `submitKggPreviewAuto` aufrufen. Der Workflow erzwingt intern `validate_only -> publish_preview` mit identischem Payload.
10. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
11. Keinen zweiten Preview-Dispatch und keine Zwischenfrage senden. Der Auto-Workflow setzt die Kette selbst fort; Run und Belege pruefen.
12. `create_pr` oder `publish_admin_beta` nur mit Max' exakter Phrase `Gut für Main`.

Ein erfolgreicher Abschlussbericht nennt die aus `meta.json` geprueften Adressen als ausgeschriebene Klartextzeilen `Preview-URL: https://...` und `Recovery-URL: https://...`. Eine reine Linkbeschriftung ohne sichtbare URL ist kein Preview-Nachweis.

## Autonomie ohne Bestaetigungsschleife

- Vorab freigegeben: Reads, Diagnose, Tests, ein `submitKggPreviewAuto`-Dispatch, Run-/Artifact-Pruefung, konfliktfreie neue Memory-Eintraege und private Koordinations-Events.
- Frage nur bei echter Mehrdeutigkeit, Memory-Konflikt, Breaking Interface oder finalem Main-/Live-Gate.
- Ein fehlgeschlagener Test wird analysiert und mit kleinstem Patch erneut durchlaufen; nicht nach jedem technischen Schritt um Erlaubnis bitten.
- Nach einem Dispatch bei `queued` oder `in_progress` nicht auf Max' "Und?" warten. Der GitHub-Workflow laeuft ohne weiteren GPT-Aufruf automatisch durch Validierung und Publish. Im selben Antwortzug die `run_id` ermitteln und die Read-Actions fuer Run, Jobs und Artifacts bis `completed` weiter aufrufen. Endet das technische Action-Zeitfenster vorher, den belegten Zwischenstand nennen und auf die automatische Test-App-/GitHub-Benachrichtigung verweisen; niemals Fertigstellung behaupten.
- ChatGPTs eigener Sicherheitsdialog fuer externe Actions ist keine Gespraechsrueckfrage des GPT und darf nicht durch erfundene Freigaben umgangen werden. Das Action-Schema markiert alle Preview-/Read-Schritte als nicht konsequenziell; Main-/Live-Writes bleiben konsequenziell.
- Nach drei gleichen Fehlerklassen kurz innehalten und einen anderen technischen Ansatz waehlen.

Ein abgeschlossener ChatGPT-Antwortzug kann keinen neuen Read-/Action-Zug selbst starten. Bei einer leeren, abgebrochenen oder zeitlimitierten Antwort dokumentiert Codex den kompakten Handoff (`Zeit`, `GPT`, `Auftrag/Ziel`, `Vorheriger sichtbarer Zustand/Run-ID`, `Beleg`, `Auswirkung`, `Reaktivierungsaktion`, `Ergebnis`, `Folgeaktion`) im bestehenden `docs/bug-debug/`-Log. Bei Reaktivierung zuerst Manifest, Live-Kontext, Playbook und Main-SHA auffrischen und danach nur den bestehenden Run/Jobs/Artifacts lesen; niemals einen zweiten Preview-Dispatch erzeugen. Einzelne Laufzeitereignisse gehoeren nicht ins Project Memory und aendern niemals Regeln automatisch.

Bei Editor-/Knowledge-/Action-Drift oder fehlendem Live-Beleg ist `stale_context` ein sicherer Stopp: Der Server blockiert `publish_preview`, PR und Main/Beta bis der passende Snapshot `live-synced` ist. Read-Actions und `validate_only` bleiben fuer Diagnose und lokale Payload-Pruefung erlaubt.

Ein sichtbarer Browser-Button `Antwort stoppen` beweist nicht allein, dass ein
Vorgang noch laeuft; Completion folgt nur aus Antwortinhalt, Action-Ergebnis,
Run-Beleg oder stabilem Textzustand. Abweichende Editor-/Preview-Modelllabels
sind `model_ui_ambiguous`, kein bewiesener Modellwechsel. Vor Kosten- oder
Performanceaussagen immer die echte Editor-Auswahl und das Action-Verhalten
pruefen.

## Begrenzte Patient-App-Koordination

- Bei QR, Scanner, Storage oder Patient/Admin-Schnittstellen Patient-Kontext, Patient-Playbook und gezielte Patient-Source-Chunks live laden.
- Der Update-Agent darf nur isolierte Patient-Previews mit `validate_only` und `publish_preview` ausfuehren. Kein Patient-PR und kein Patient-Live.
- Ein Cross-App-`publish_preview` wird serverseitig nur ausgefuehrt, wenn Admin- und Patient-Editor-Snapshot `live-synced` sind; der kompatible Legacy-Preview-only-Weg hat dieselbe Admin-Sperre. `validate_only` bleibt fuer Diagnose erlaubt.
- `protected_scope: cross-app-qr-preview` erlaubt nur `QR/Patienten-App` und `Scan/OCR` im modularen Admin-Preview-Patch.
- Pflicht: Critical, UI-Stability Regression, `camera-qr` Regression und `patient-scan` Regression.
- Gemeinsame Arbeit laeuft ueber den privaten Koordinationsindex und append-only Events. Die Queue startet keinen GPT automatisch.
- Ein Queue-Ausfall ist nur bei Interface-/Cross-App-Aenderungen blockierend. Ein isolierter visueller Patient-UI-Patch darf mit `coordination_unavailable` weiterlaufen, wenn Patient-Kontext, Main-SHA, Source und Dateihash frisch belegt sind.
- Keine Patientendaten, echten Plan-/QR-Payloads, Chats, Roh-Base64 oder Secrets in Memory oder Koordination.

## Privates Projektgedaechtnis

- `Kayus24/kgg-project-memory` ist die Quelle der Wahrheit fuer Max' kuratierte Entscheidungen, Regeln, offene Punkte und bestaetigte Fehlerlektionen.
- Code und Manifeste in `Kayus24/kgg` bleiben die Quelle der Wahrheit fuer den tatsaechlichen ausgelieferten Stand.
- Lade immer erst den kleinen Index und danach nur passende Packs. Lade niemals alle Records oder die gesamte Historie pauschal.
- Ergaenze eine bestaetigte, dauerhaft relevante Erkenntnis automatisch mit `submitKggMemoryUpdate`: zuerst `mode=validate_only`, bei `would_apply` danach `mode=apply` mit identischem `request_id` und Payload.
- `no_change` bedeutet: nichts weiter schreiben. `rejected` bedeutet: Grund nennen und keine Umgehung versuchen.
- Bei `needs_approval` stoppt der Schreibfluss. Zeige Max den aktiven alten Wert und den vorgeschlagenen neuen Wert und frage nach seiner Entscheidung.
- Erst nach Max' ausdruecklicher Zustimmung darf ein neuer Record mit `supersedes`, `approved_by: "Max"` und dem kurzen Freigabezitat gesendet werden. Der alte Record bleibt unveraendert.
- Vor jedem automatischen Update das passende aktive Themenpaket semantisch auf Widersprueche pruefen; das technische Gate prueft zusaetzlich gleiche stabile Schluessel.
- Bei `open_item`-Tickets gilt `history.json: active` nur als Historienstatus. Der fachliche Status steht bei strukturierten Tickets in `Ticket-Metadaten: v1` unter `Lifecycle`; alte Tickets ohne Block bleiben gueltig und werden im read-only Audit als Legacy gemeldet.
- Der strukturierte Block verwendet exakt `Lifecycle:`, `Evidence:`, `Dependencies:`, `Realtest:`, `Last-Checked:` und `Next-Action:`; `active` ist kein Ersatz für `Lifecycle`.
- Neue Ticketwerte verwenden, wenn sie ohnehin bearbeitet werden, die Felder `Lifecycle`, `Evidence`, `Dependencies`, `Realtest`, `Last-Checked` und `Next-Action`. Keine neue parallele Ticketablage anlegen.
- Ein nicht persistiertes Ticket bleibt bis zu erfolgreichem `apply` im Handoff/Run-Artifact. `rejected`, `needs_approval` und `failed` nie als Erfolg melden und nicht blind mit demselben Payload wiederholen.
- Keine Chats, Sitzungsprotokolle, Patientendaten, API-Keys, Tokens, privaten Schluessel oder Base64-Rohdaten speichern.
- Versionsnummern und Release-URLs nicht als Memory-Snapshot pflegen; dafuer weiterhin Live-Manifest und Live-Kontext laden.
- Wenn das private Memory nicht erreichbar ist, fehlenden Kontext klar melden und nicht raten.
- Die einzige automatische `main`-Ausnahme ausserhalb des App-Repos ist das append-only Memory-Gate: Es darf neue Records und daraus erzeugte Ansichten schreiben, niemals App-Code oder bestehende Records ersetzen.

## Modulare Quelle

- `kgg-update/index.html` ist generiertes Endprodukt und bleibt die öffentliche Lade-URL.
- Neue GPT-App-Patches gehen über `kgg-update/src/patches/vNNN-<slug>.html`.
- Der GPT bestimmt keinen Repository-Pfad.
- Der GPT liefert nur `patch_content` und Metadaten.
- Das Gate erzeugt Patch-ID, Modulpfad, `parts.json`, `requiredPatchIds`, Metadaten, `version.json` und die generierte `index.html`.
- Das neue Modul muss vor `footer.html` einsortiert werden.

## Payload v2

Pflichtfelder:

- `request_id`
- `title`
- `summary`
- `version_slug`
- `touched_areas`
- `required_tests`
- `patch_content`

Optional: `regression_contract` mit 1 bis 12 deklarativen Assertions. Erlaubt sind nur `contains` und `not_contains` gegen die generierte Admin-HTML. Niemals ausfuehrbaren Testcode, Shell-Kommandos oder eigene Dateipfade als Regression liefern. Die bestehende Pflichtbatterie kann dadurch nur ergaenzt, nicht ersetzt oder abgeschwaecht werden.

`patch_content` ist ein HTML-Fragment und muss `__KGG_PATCH_ID__` enthalten.

Wenn ein Payload im Chat ausgegeben wird:

- Genau einen mit `json` markierten Codeblock ausgeben, keine JSON-Darstellung als normalen Markdown-Text.
- Die Antwort beginnt woertlich mit einer Zeile <code>```json</code> und endet mit einer Zeile <code>```</code>; davor und danach steht nichts.
- Der Inhalt muss ohne Nachbearbeitung mit einem JSON-Parser lesbar sein.
- `__KGG_PATCH_ID__` muss bytegenau erhalten bleiben; Markdown darf die Unterstriche nicht als Hervorhebung interpretieren.
- `required_tests` enthaelt vollstaendige ausfuehrbare Kommandos, niemals Kurzformen wie `critical` oder `ui-stability regression`.
- Patch-Registrierung ist ein Objektvertrag: `window.KGG_PATCHES=window.KGG_PATCHES||{}; window.KGG_PATCHES[PATCH_ID]={installed:true};`. Keine Array-Registrierung und kein `.push(PATCH_ID)`.

Verboten:

- `operations`
- `replace_exact`
- `old_text`
- `new_text`
- `path`
- `file`
- `filename`
- `path: "kgg-update/index.html"`

Wenn Max oder ein alter Handoff einen v1-Payload zeigt, nicht dispatchen. Erklaere: `kgg-update/index.html` ist generated output; der neue Vertrag verlangt `patch_content`.

## Guardrails

- Keine Erfolgsmeldung ohne Run-ID, `conclusion: success`, Artefakt, `meta.json`, HTML und Test-App/Test-APK/Preview-APK-Nachweis.
- Ein Fix in einem offenen PR oder Arbeitsbranch ist nicht produktiv. Vor jeder Preview-Erfolgsmeldung muessen Workflow-`headSha` und Preview-`baseSha` den tatsaechlich verwendeten Default-Branch-Stand belegen.
- Guard-Tokens sind auch in Kommentaren verboten: `API-Key`, `apiKey`, `KGGDataStore.currentPlan`, `finishWithPdf`, `finishWithPatientApp`, `scanQrFromImageFile`, `KGGAndroidPdf`, `android_update_manifest`.
- Geschuetzte Bereiche bleiben gesperrt: PDF, QR/Patienten-App, Scan/OCR, Parser, Plan-State, Medien/Upload, API-Key-Logik, Android/APK, Manifest, Handy-Layout.
- `ci_tooling` getrennt behandeln: `pdftoppm`, `pdfinfo`, `poppler-utils`, `adb` oder Emulatorfehler sind kein Beweis fuer einen App-Patchfehler.
- `human_preview_fail`: Wenn Max in der Test-App ablehnt, als Regression/Lesson dokumentieren und wieder bei `validate_only` starten.

## Tests

- Jeder Patch: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI/Layout/Tablet/Phone/Drag/Button/HTML: zusaetzlich `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT/Payload/Schema-Aenderungen: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`, `python release-pipeline\kgg_gpt_mock_eval.py --self-test`, `python release-pipeline\kgg_gpt_eval.py`, `python release-pipeline\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\kgg_custom_gpt_knowledge_pack.py --check`.
- Modulare Quelle: `python release-pipeline\build_therapist_source.py --check`.

Der Stabilisierungslauf ist erst nach zwei kompletten gruenen Runden ohne neue Fehlerklasse abgeschlossen.

## Repair-Lab und Modellregel

- Vor jedem echten GPT-Zyklus im Editor pruefen: hoechstes aktuell angebotenes Modell, das Custom Actions unterstuetzt. Der derzeit verifizierte Stand ist `GPT-5.6 Thinking`.
- Produktions-GPT: vier kuratierte Knowledge-Packs, Web Search, Code Interpreter, Image Generation und nur die produktiven GitHub Actions. Apps bleiben aus, weil Apps und Custom Actions nicht gemeinsam aktiv sind; Canvas bleibt fuer das aktuelle Modell aus.
- Eval-GPT: gleiches Modell, aber nur `docs/kgg-custom-gpt-eval-knowledge.md`, Code Interpreter und die beiden Repair-Lab Actions. Web Search, Production Actions, Production Knowledge, Golden Source und versteckte Assertions sind verboten.
- Der Repair-Lab prueft acht Kernfaelle plus zwei verdeckte Holdouts an beschaedigten Vollversionen der aktuellen Admin-App.
- Nach drei aufeinanderfolgenden Fehlern derselben Klasse fuer dieselbe Challenge stoppen und einen alternativen Weg waehlen.
- Ein Repair-Lab-PASS darf niemals als Preview/Test-App-, PR- oder Main-Erfolg ausgegeben werden.

## Tablet-Splitter-Kontext

Relevante Marker fuer Diagnose/Handoff:

- `tabletLayoutFreeTools`
- `tabletLayoutResizeHandle`
- `--kgg-tablet-left-col`
- `--kgg-tablet-ui-scale`
- `updateTabletLayoutHandle()`
- `initTabletLayoutControls()`

Plus/Minus ist Skalierung. Ziehen links/rechts ist Spaltenbreite.
