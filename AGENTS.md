# AGENTS.md - KGG Git Worktree

## Wichtigste Source of Truth

- Vor Admin-/Tablet-UI-Patches immer zuerst lesen:
  `therapist-app/test-lab/tablet-golden/TABLET_GOLDEN_LAYOUT_SOURCE_OF_TRUTH.md`
- Diese Datei ist verbindlich fuer das Tablet-Golden-Layout und muss angepasst werden, wenn Max den Standard aendert.
- Vor UI-/Layout-Patches immer auch lesen:
  `tools/apk-ui-smoke/KGG_UI_FLOW_CONTRACT.md`
  `tools/apk-ui-smoke/KGG_REGRESSION_MEMORY.md`
- Wenn ein Fehler bereits im Regression Memory steht, zuerst dessen Fix-Regel und Testfall anwenden, nicht neu raten.

## Arbeitsregeln

- Nicht neu bauen und keine grossen Mischfixes.
- Bei Codeaenderungen neue Test-Lab-Zielversion erstellen.
- Keine Release-Dateien oder APKs aendern, ausser Max fordert es ausdruecklich.
- Keine API-Keys hardcoden oder in Git ablegen.
- PDF, QR/Patient:innen-App, Scan/OCR, Parser, Medien-/Upload-Core und Android-Build nicht nebenbei anfassen.
- `KGGDataStore.currentPlan` bleibt zentrale Plan-State-Quelle.

## Aktuelle Tablet-Testlinie

- Aktuelle Golden-Testdatei:
  `therapist-app/test-lab/modern-base/KGG_APP_ADMIN_v390_local_p06_parser_formats.html`
- QA-Modus:
  `?qa=1`

## Aktuelle lokale Admin-Testbasis

- Lokale Hauptbasis fuer neue Admin-HTML-Patches:
  `therapist-app/test-lab/modern-base/KGG_APP_ADMIN_v390_local_p06_parser_formats.html`
- Diese Basis schuetzt lokale Tests vor GitHub-Auto-Update und Service-Worker-Ruecksprung.
