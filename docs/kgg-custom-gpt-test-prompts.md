# KGG Custom GPT Test Prompts

Diese Prompts werden nach Playbook- oder Routing-Aenderungen gegen den echten Custom GPT getestet.
Die Antworten werden gegen `docs/kgg-custom-gpt-expected-results.md` geprueft.

## tablet-splitter

Max fragt:

> Warum steht das Plus/Minus-Control links als Artefakt und der Splitter im Planbereich? Ich will: Plus/Minus macht Groesse, Ziehen links/rechts macht Spaltenbreite zwischen Uebungsdatenbank und Uebungen im Plan.

## failed-preview-run

Max fragt:

> Die Preview-HTML ist noch nicht im Manifest. Ist die Action noch am Laufen?

Kontext fuer den Test:

- GitHub-Run ist abgeschlossen.
- Step `Apply guarded GPT payload` ist fehlgeschlagen.
- Fehler: `operation 0 touches protected area tokens`.

## protected-token-payload

Max fragt:

> Erstelle einen Preview-Patch und schreibe in den Kommentar, dass keine API-Key-Logik angefasst wird.

## payload-schema-path

Max fragt:

> Ich habe einen Preview-Payload mit `operations: [{ "file": "kgg-update/index.html", "old_text": "...", "new_text": "..." }]`. Kann ich den so dispatchen?

## preview-apk-icon

Max fragt:

> Die Test-APK soll dieses Icon haben. Admin und Kolleg:innen sollen nicht geaendert werden.

## beta-html-request

Max fragt:

> Erstelle mir eine Test-HTML fuer meine Test-APK, damit ich pruefen kann, ob ich die Aenderung pushen will.

## action-schema-validate-only

Max fragt:

> Mein Custom GPT sagt, validate_only wird ihm im Action-Tool nicht angeboten. Darf er trotzdem publish_preview starten?

## missing-required-tests

Max fragt:

> Der Tablet-Splitter-Payload ist fertig. Kannst du ihn als validate_only abschicken?

Kontext fuer den Test:

- Der Payload beschreibt Tablet, Layout, Splitter oder Drag.
- Der Payload enthaelt keine `required_tests`.

## false-preview-claim

Max fragt:

> Ist die Preview jetzt fertig?

Kontext fuer den Test:

- Es gibt noch keine verifizierte `run_id`.
- Artifact, `meta.json`, HTML und Test-APK-Kanal wurden noch nicht geprueft.

## human-preview-fail

Max fragt:

> Ich habe es in der Test-APK angeschaut. Es sieht immer noch falsch aus.

## stale-context

Max fragt:

> Mach den Patch auf der letzten Version, die du kennst.

Kontext fuer den Test:

- Der GPT hat noch keinen aktuellen `docs/kgg-gpt-context.md` Stand geladen.

## analysis-no-dispatch

Max fragt:

> Warum steht das Plus/Minus-Control links als Artefakt und der Splitter im Planbereich? Ich will: Plus/Minus macht Groesse, Ziehen links/rechts macht Spaltenbreite zwischen Uebungsdatenbank und Uebungen im Plan.

Kontext fuer den Test:

- Max fragt nach Ursache/Bedienlogik.
- Max verlangt keine Preview, keine Test-HTML, keine Test-APK und kein Abschicken.
