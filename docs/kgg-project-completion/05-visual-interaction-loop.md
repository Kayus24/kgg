# G05 – Visueller Screenshot-Aktions-Regelkreis

## 1. Ziel

Ein Agent kann aus einem echten Screenshot den nächsten sicheren UI-Schritt ableiten, ihn ausführen lassen und anhand eines zweiten Screenshots plus Zustandsbeobachtung verifizieren.

## 2. Warum dieses Gate erforderlich ist

Koordinatensteuerung ohne Rückkopplung ist blind und instabil. Der Loop macht aus einzelnen Browsertools eine echte agentische UI-Testfähigkeit.

## 3. Scope und Nicht-Ziele

In Scope: synthetische KGG-Testdaten, begrenzte App-Workflows und sichtbare Bedienung. Nicht in Scope: Chain-of-Thought-Speicherung, CAPTCHA-Umgehung oder unbegrenzte autonome Webnavigation.

## 4. Abhängigkeiten

G04, G08 und G09.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=OPT_IN_PERSISTENT_REAL_VISUAL_LOOP`
- `LIVE_EVIDENCE_STATUS=LOCAL_REAL_OBSERVE_DECIDE_ACT_VERIFY`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T15:00:00+02:00`

## 6. Bestehende Evidence

Die G04-Brücke kann lokal klicken und zwei echte Screenshots erzeugen. Der neue opt-in Visual-Loop hält dafür eine Seite im selben Browserkontext offen: Screenshot A wird beobachtet, eine vom aufrufenden Agenten gelieferte Entscheidung wird gegen den bounded Action-Vertrag geprüft, genau eine Aktion ausgeführt und Screenshot/Zustand B unabhängig verifiziert.

## 7. Lücke und Root Cause

Der lokale „observe → decide → act → verify“-Lauf ist nachgewiesen. Für `PASS` fehlt noch die echte unterstützte Host-Surface (ChatGPT/Custom GPT oder Codex mit angeschlossenem Plugin); deshalb bleibt das Gate `PARTIAL`.

Die aktuelle read-only Prüfung der normalen ChatGPT-Plugin-Surface verschärft
diese Abgrenzung: `KGG UI Lab Private` wird im Plugin-Detail als „Read-only
synthetic KGG UI-Lab MCP bridge“ beschrieben und veröffentlicht keine
Fresh-Main-/Source-Revision; diese Beschreibung allein beweist jedoch keine
synthetic-only-Ausführung. Zwei gebundene Sitzungsstarts wurden zunächst vor
Browserstart abgewiesen (`session_schema_invalid`, danach `app_url_invalid`).
Ein separat gebundener Post-Fix-Diagnoselauf erreichte anschließend
`start_ui_session=PASS` (`requested -> ready`), aber
`observe_visual_state` wurde mit `request_schema_invalid` abgewiesen. Es gab
weiterhin keinen Screenshot, kein Artefakt und keinen Klick. Damit existiert
für B weiterhin keine Screenshot- oder Aktions-Evidence; der Befund ist weder
ein Beweis für einen aktuellen Playwright-/Chromium-Fehler noch für echte
Host-Parität. Der verbleibende Blocker liegt vorläufig auf der
Observe-Request-/Bundle-Bindung; die korrekte Einstufung lautet
`REAL_BROWSER_CAPABILITY_UNPROVEN_AFTER_OBSERVE_CONTRACT_REJECTION`.

Die lokale Ursache wurde eingegrenzt und behoben: Der MCP-Tool-Katalog hatte
`request` zuvor nur als unbeschriebenes Objekt veröffentlicht. Commit `75c8de1`
publiziert nun die sieben Pflichtfelder des `kgg-ui-lab/request/v1`-Vertrags
und einen Regressionstest. Das ändert den bereits verbundenen ChatGPT-Bundle-
Stand nicht automatisch; vor einem neuen Lauf muss das Bundle read-only an
diesen Contract gebunden bzw. neu verbunden werden.

## 8. Kleinschrittiger Arbeitsplan

1. Screenshot-Metadaten und Viewport-Koordinatensystem festlegen. ✅
2. Aktionsrequest mit Ziel, Koordinaten, erwarteter Änderung und Safety-Klasse definieren. ✅ bounded decision contract
3. Vorher-Screenshot und Zustandsfingerprint speichern. ✅ persistent in-memory page
4. genau eine Aktion ausführen. ✅ one action per request
5. Nachher-Screenshot und Zustand erfassen. ✅ same page / second screenshot
6. erwartete Änderung unabhängig prüfen. ✅ expected state + hash pair
7. bei Nichtänderung einmal semantisches Ziel oder frischen Screenshot nutzen; nicht blind wiederklicken.
8. Abschluss/Fehler mit Evidence ausgeben.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G05_VISUAL_LOOP`
- `INPUT=echte Session, Screenshot A, bounded Aufgabe`
- `PROCEDURE=Ziel bestimmen; eine Aktion; Screenshot B; Zustandsassertion; gegebenenfalls ein kontrollierter Fallback`
- `PASS_CRITERIA=beabsichtigte sichtbare Zustandsänderung mit gebundener Vorher-/Nachher-Evidence`
- `FAIL_CRITERIA=keine Änderung, falsches Ziel, wiederholter Blindklick oder ausschließlich modellgemeldeter Erfolg`
- `RETRY_RULE=maximal ein neuer Observe-Schritt bei plausibel veraltetem Screenshot`
- `FALLBACK=bei stale/unerwartetem Zustand keine zweite Aktion; Session schließen und Quick Flow oder frischen Observe-Schritt verwenden`
- `EVIDENCE_OUTPUT=VISUAL_LOOP_RUN_V1`
- `NEXT_ON_PASS=G06 und G07`
- `NEXT_ON_FAIL=Root Cause oder G11`
- `INVALIDATION_TRIGGERS=Viewport-, Screenshot-, Aktions- oder Zustandsvertrag ändert sich`

## 10. Tests

- Zielbutton an variierenden Positionen.
- DPI/Viewport-Skalierung.
- Overlay, Scroll, verzögertes Rendering und nicht anklickbares Ziel.
- Negativ: Screenshot veraltet, Aktion außerhalb Bounds, Zustand unverändert.
- `python -m unittest release-pipeline/test_kgg_real_browser_bridge.py -v`: vier lokale Real-Bridge-Tests PASS, inklusive persistentem Visual-Loop.
- zwei unveränderte reale Durchläufe.
- Normal-ChatGPT-Bindungsprüfung 2026-09-23: read-only `get_current_state`
  einmal PASS; zwei Sessionstarts zunächst vor Browserstart FAIL; ein
  gebundener Post-Fix-Diagnoselauf erreichte `ready`, dessen
  `observe_visual_state` aber mit `request_schema_invalid` scheiterte. Keine
  Screenshot- oder Aktions-Evidence. Kein weiterer Observe-/Action-Retry.
- Lokaler Contract-Fix `75c8de1`: vollständiges `request/v1`-Schema im
  Tool-Katalog, 10/10 Real-Bridge-Tests, 10/10 Plugin-Candidate-Tests und
  GPT-Critical-Battery grün. Kein externer Bundle-Rebind ausgeführt.

## 11. Safety und Datenschutz

Keine echten Patientenscreenshots. Destruktive oder externe Aktionen benötigen eigene Toolklassifikation und gegebenenfalls Human Gate.

## 12. Brother-GPT-Eskalation

Bei stabil wiederholtem Wahrnehmungs-/Aktionsfehler erhält der Brother anonymisierte Screenshots, Metadaten und Events; nie Secrets oder Patientendaten. Der externe Host-Paritätsblocker bleibt separat als G03 geführt.

## 13. Abschlussartefakte

Loop-Vertrag, Referenzimplementierung, Evidence-Beispiel und robuste Black-Box-Tests.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX_PLUS_BROTHER_GPT`, `CONTRIBUTION_DATE=2026-09-23`, `HANDOFF_ID=G04_G05_BINDING_REVIEW_20260923`, `REVIEW_STATUS=PARTIAL`, `NOTE=Local persistent observe/decide/act/verify loop is real and fail-closed; the connected normal-ChatGPT bundle is described as a read-only synthetic bridge and has no exposed Fresh-Main revision, but synthetic-only execution is not proven because the post-fix session reached ready. Observation was rejected before returning a visual state; supported external agent-host parity remains unproven.`
