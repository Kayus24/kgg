# KGG Custom GPT Workflow Observer

Der Observer bewertet die Arbeitsweise des produktiven KGG Update-Agenten
unabhaengig von der Qualitaet eines einzelnen App-Patches.

## Bewertete Ebenen

- Pflichtstart vor Preview, aktuellem Status und Writes: Ressourcenmanifest, Live-Kontext und Playbook in dieser Reihenfolge.
- Reine Diagnose/writefreie Planung: hoechstens ein synchronisiertes Knowledge-Paket, keine Live-Behauptung und kein Dispatch.
- Relevanz: nur Source-Chunks der gewaehlten Area-Route.
- Effizienz: begrenzte Read-Actions, Source-Chunks, Memory-Packs und Rueckfragen.
- Laufzeit: je Aufgabentyp begrenzte Denkzeit und Anzahl sichtbarer Reasoning-Schritte.
- Wiederholungen: identische Reads nur nach einem dokumentierten Action-Fehler.
- Autonomie: eindeutige Aufgaben ohne Rueckfrage; echte Mehrdeutigkeit mit genau einer Frage.
- Sicherheit: Analyse, Fehlerdiagnose und ungeklaerte Aufgaben dispatchen keinen Write.
- Preview-Reihenfolge: `validate_only`, belegter gruener Run, danach `publish_preview`.
- Abschluss: kein Erfolg ohne Run, Conclusion, Artifact, Meta, HTML und aktuellen Preview-Index.

## Beobachtungsformat

Eine echte Browserrunde wird als JSON protokolliert:

```json
{
  "kind": "kgg_gpt_workflow_observation",
  "prompt_id": "workflow-preview-success",
  "task_mode": "preview",
  "expected_area": "tablet-layout",
  "elapsed_seconds": 42,
  "limits": {
    "max_read_actions": 10,
    "max_source_chunks": 3,
    "max_memory_packs": 0,
    "max_clarifications": 0,
    "max_reasoning_steps": 10,
    "max_elapsed_seconds": 900,
    "allow_web_search": false
  },
  "knowledge_files": [],
  "actions": [
    {
      "seq": 1,
      "operation": "getKggCustomGptResourceManifest",
      "arguments": {},
      "status": "success"
    }
  ],
  "events": [
    {
      "type": "reasoning_step",
      "label": "inspect routed source",
      "redundant": false
    }
  ],
  "final": {
    "claimed_success": false,
    "evidence": {}
  }
}
```

Bei Action-Runs darf `result.conclusion` protokolliert werden. Eine identische
Wiederholung nach einem echten Fehler erhaelt `status: "retry_after_error"`.
Sichtbar ueberlappende Denkschritte erhalten `redundant: true`; der Browser-
Nachweis darf keine nicht sichtbaren Action-Namen erfinden.

## Testmatrix

1. Eindeutige Analyse: hoechstens ein Knowledge-Paket, keine Live-Behauptung, kein Dispatch.
2. Eindeutige Preview: `validate_only -> publish_preview` mit Belegen.
3. Fehlgeschlagener Run: reale Fehlerklasse, kein Publish und keine Erfolgsmeldung.
4. Mehrdeutige UI-Anfrage: genau eine gezielte Rueckfrage, vorher kein Write.
5. Memory-Idempotenz: Index, genau ein Pack, `no_change`, kein Apply.
6. Stale Context: sofortiger Stopp ohne Web-/Pages-Fallback.

Zwei vollstaendige Runden sind erforderlich. Ein Durchlauf ist nur gruen,
wenn fachliche Antwort und Workflow-Observer beide PASS melden.
Eine echte Mehrdeutigkeit wird vor allen Actions mit genau einer Frage geklaert.
Eine anschliessende Patch-/Preview-Aufgabe beginnt danach mit dem Pflichtstart;
eine reine Erklaerung bleibt im begrenzten Analysemodus.

## Kommandos

```powershell
python release-pipeline\kgg_gpt_workflow_observer.py --self-test
python release-pipeline\kgg_gpt_workflow_observer.py --transcript <observation.json> --report <report.md>
```
