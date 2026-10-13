# KGG – API-freie Gemini-Web-Video-QA

Status: zusätzlicher Test-/Review-Baustein, **keine Produktfreigabe**.
Workstream: Draft-PR #307, auf main nach Merge von Parity-PR #303.
Browser-Owner: vorhandener Codex-MCP **fahrklar_gemini_web**.
**Keine Gemini-API, kein API-Fallback, keine neuen Secrets, kein Account-Wechsel.**

## Wiederverwendung statt Doppelbau

- Bestehender synthetischer KGG-Playwright-Recorder und dessen phone-legacy.webm, phone-react.webm und report.json.
- Bestehender Fahrklar-Codex-MCP fahrklar_gemini_web: @playwright/mcp@0.0.83 mit Chrome und eigenem persistentem, bereits konfiguriertem Profil.
- Das in Fahrklar erprobte Verfahren Prepare → Browser-Upload → Generierung beobachten → Antwort zweimal prüfen → Finalize.
- Keine Übernahme der fahrregelspezifischen Prompts/Schemas. Kein Kopieren von Browserprofilen oder Zugangsdaten.
- Der frühere Gemini-API-Workflow wurde beim Merge von PR #303 aus main entfernt. Nicht wieder einführen.

## Codex-Ablauf je genauem KGG-Kandidat

1. Zuerst frische GitHub-/PR- und CI-Stände sowie docs/ACTIVE_WORK.md prüfen.
   Aktuelle synthetische Chromium-Parity-Evidenz erzeugen, zusammen mit WebKit-Gate.
   Echte Patientendaten niemals hochladen.
2. KGG-Prepare mit EXAKTEM 40-stelligen Kandidaten-SHA:

       node release-pipeline/kgg_patient_gemini_web_handoff.mjs prepare "C:\ABSOLUT\patient-ui-parity" <EXAKTER_SHA> "C:\ABSOLUT\handoff.json"

   Prüft PASS, Chromium, synthetische Daten, Kandidaten-SHA, harte Checks,
   beide WebM-Videos, Größen, Report-Hash, SHA-256. Falscher Stand wird abgelehnt.
3. Codex benutzt **sein bereits installiertes** fahrklar_gemini_web-MCP für
   https://gemini.google.com/. Profil/Login NICHT neu erzeugen. Sichtbar
   Gemini 3.1 Pro und falls verfügbar Extended Thinking auswählen.
   Login, Modell oder Quota nicht verfügbar → UNAVAILABLE; kein API-Fallback.
4. Im selben Prompt zuerst handoff.videos.legacy.path und danach
   handoff.videos.react.path anhängen. Sichtbare Anhänge BEIDER Videos bestätigen.
   Den Text handoff.prompt unverändert senden.
5. Beobachten: Upload, Start/Ende der Generierung, Modellanzeige; nach
   Abschluss zwei gleiche Antwort-Snapshots mit mindestens 2 Sekunden Abstand.
   Kleine, wiederholte Beobachtungsschritte; absolute Gesamtdauer maximal 240s.
   Unklarer Zustand ist nicht PASS.
6. Nach dem **wirklich beobachteten** Browserdurchlauf observation.json
   mit tatsächlichem Modell, Thinking-Label, Upload-/Generierungs-Flags,
   Uhrzeiten und beiden unveränderten Gemini-JSON-Textantworten erzeugen.
   Dann:

       node release-pipeline/kgg_patient_gemini_web_handoff.mjs finalize "C:\ABSOLUT\handoff.json" "C:\ABSOLUT\observation.json" "C:\ABSOLUT\gemini-web-review.json"

   Finalize bindet Video-/Report-Hashes wieder an denselben Kandidaten,
   prüft Modell/Upload/Antwortstabilität und validiert das JSON streng.
7. Das erzeugte gemini-web-review.json der KGG-Testevidenz zuordnen.
   Vier Statuswerte: PASS, REVIEW_REQUIRED, INCONCLUSIVE, UNAVAILABLE.
   Modell-PASS ist ausschließlich beratend; nichts automatisch mergen,
   veröffentlichen oder als Gesamt-App-Regressionstest zählen.

### Observation-Schema (nur Beispiel, keine echte Evidenz)

    {
      "observedModel": "Gemini 3.1 Pro",
      "thinkingLabel": "Pro · Erweitert",
      "uploadVisible": {"legacy": true, "react": true},
      "generationObserved": true,
      "generationStopped": true,
      "startedAt": "2026-10-12T10:00:00.000Z",
      "stoppedAt": "2026-10-12T10:00:20.000Z",
      "responseSnapshots": [
        {"observedAt": "2026-10-12T10:00:22.000Z", "text": "<GENAUER JSON-TEXT>"},
        {"observedAt": "2026-10-12T10:00:24.200Z", "text": "<IDENTISCHER JSON-TEXT>"}
      ]
    }

Beispiel-Uhrzeiten und Statusflags dürfen nie als tatsächlicher Review
ausgegeben werden. Hash- und Schema-Prüfung ersetzt keine Live-Browserbeobachtung.
Modelltext muss aus der UI stammen, nicht aus dem Output des Modells.

### Wenn die Web-Anmeldung / Quota / UI nicht funktioniert

    node release-pipeline/kgg_patient_gemini_web_handoff.mjs unavailable "C:\ABSOLUT\handoff.json" LOGIN_REQUIRED "C:\ABSOLUT\gemini-web-review.json"

Erlaubte Gründe: LOGIN_REQUIRED, QUOTA, BROWSER_UNAVAILABLE, UPLOAD_FAILED,
MODEL_UNAVAILABLE, TIMEOUT, UNKNOWN. Niemals Phantom-PASS.

## Grenzen, Tests und Integration

- Vertrags-/Fehlertests: node --test release-pipeline/kgg_patient_gemini_web_handoff.test.mjs.
- Bestehende deterministische Playwright-/Geometrie-/Storage-/Pixelgates
  bleiben die harte Grundlage; Gemini darf deren RED nie in GREEN umwandeln.
- Bewertet wird nur die synthetische Telefonansicht des NumPad-Ablaufs.
  Tablet, komplette Patienten-App, iPhone/Safari, physisches Oppo und
  nicht sichtbare 1-Frame-Compositor-Probleme bleiben ungeprüft.
- Vorhandene alte Videos dürfen NUR mit ihrem damaligen exakten SHA
  geprüft werden, nicht als aktuelle Kandidatenfreigabe.
- Codex führt die Browsersteuerung durch; das neue KGG-Skript kopiert
  keine Fahrklar-MCP-Implementierung, Login-Daten oder Browsercode.
- Unterbrechungen: Arbeitsstand, aktuelle PR-Commits, laufende Prozesse
  und bereits erfolgte Uploads **zuerst prüfen**, nicht blind wiederholen.

## Verifizierter Integrationscheckpoint – 2026-10-12

- KGG-Parity-PR #303 ist auf main gemergt; Ausgangs-SHA dieses Arbeitsstrangs: f59bc55e6e22e1b04061557c710069f6cf8f0b21.
- Draft-PR #307 enthält ausschließlich fünf Web-Handoff-, Bericht-, CI-Test- und Dokumentationsdateien. Alter Gemini-API-Code bleibt entfernt.
- Auf der aktualisierten main-Basis: 25/25 Node-Vertragstests lokal PASS, inklusive fehlerhafter/gefälschter Modellantworten; Hook-Guard und Secret-Scan PASS.
- Ältere auf damaligem #303-Head b2f1560 frisch erzeugte Chromium-Parity-Videos: 392 Prüfungen PASS, 0 Abweichungen. Nicht auf neueren Commit übertragen.
- Reale Gemini-Weboberfläche war im Browser-Preflight erreichbar; beim eigentlichen Lauf war das persistente Fahrklar-Profil durch einen schon laufenden Codex-MCP belegt. Vorhandene Sitzung wurde geschützt, kein Upload.
- Bis zu einem echten Browserdurchlauf gilt die lokale Video-QA als UNAVAILABLE/BROWSER_UNAVAILABLE. Kein Modell-PASS.
- Breite lokale Critical-Batterie auf älterem Worktree blieb in Release-Contract-Tests ohne Endstatus und wurde abgebrochen: INCOMPLETE. Neuer GitHub-CI-Stand ist separat zu verifizieren.


## Tatsächlich ausgeführter Gemini-Web-Review – 2026-10-13

Der zuvor offene echte Browser-Review wurde jetzt abgeschlossen, nicht nur gemockt. Zwei synthetische Videos (Legacy, React) wurden in der angemeldeten Gemini-Web-App an einen Auftrag angehängt. Modell 3.1 Pro mit Hoch wurde im UI nachgewiesen; zwei getrennte Readbacks der vollständigen JSON-Antwort waren identisch. SHA-Bindung an den synthetischen PR-Kandidaten a5680798e23f0d9256ac542329a4a2ad2cb74602 ist per Finalize erfolgreich.

Ergebnis: REVIEW_REQUIRED (Gemini: suspected_regression / confidence high / severity critical). Die unabhängige Video-Einzelbildprüfung bestätigt sichtbare graue Aussetzer mit oben verbleibenden Abbrechen-/OK-Schaltflächen. Die Störung ist **in beiden Aufnahmen** vorhanden: sie belegt keine React-spezifische Regression. Der genaue Ursprung App-Compositor vs. Aufzeichnungsweg bleibt unbekannt. Vergleichsbericht und Strukturresultat liegen als synthetische Evidence vor. Siehe docs/quality/evidence/kgg-video-grey-frame-audit-20261013.md und das JSON im selben Ordner.

Die ursprüngliche Dauer der Webgenerierung lässt sich nachträglich nicht sekundengenau beweisen. Der Handoff unterstützt daher eine **ausdrücklich markierte POSTHOC-Readback-Auswertung** mit zwei stabilen Antworten: Modell-Funde bleiben REVIEW_REQUIRED, aber ein zeitlich unbestätigter Nullbefund kann niemals PASS ergeben, sondern nur INCONCLUSIVE. Es werden keine Uhrzeiten erfunden. Normale neue Durchläufe verlangen weiterhin die vollständige 240-Sekunden-Timingkontrolle. Die harten Playwright-/Realgeräte-Gates und die Unterscheidung von Videoartefakt und App-Bug bleiben maßgeblich.

KGG-Reviewstatus offen als gesonderte Frame-/Compositor-Ursachenanalyse; automatische Video-Handoff-Implementierung durchgeführt. Draft-PR #307 wird nicht ohne Code-/Testreview gemergt.
