# Codex Ticket: KGG Test-App als schneller Preview-Testpfad erreichbar machen

## Beobachtung

Die KGG Test-App/Preview soll der unkomplizierte Weg sein, neue Funktionen schnell selbst zu testen. Aktuell kann sie aus einer normalen Arbeits-Session nicht einfach angesteuert bzw. mit einem neuen Teststand geladen werden.

Für den Therapie-Cockpit-Integrations-Harness konnte der lokale Testlauf vollständig grün ausgeführt werden. Der autorisierte Remote-Weg zur Test-App benötigt jedoch die Aktion `submitKggPreviewAuto`. Diese Aktion ist in der aktuellen Session nicht verfügbar.

Ein direkter `gh workflow run`-Aufruf wurde bewusst nicht als Ersatz verwendet, weil er den vorgeschriebenen Preview-Write-Gate umgehen würde. Dadurch gibt es für diesen Lauf keine verifizierte Remote-Preview-URL und kein Test-App-Artefakt, obwohl die Code- und Browser-Prüfungen grün sind.

## Auswirkung

- Max kann eine neue Funktion nicht mit einem einfachen „auf Test-App laden“-Schritt öffnen.
- Für jede schnelle Sichtprüfung ist ein lokaler HTTP-Server oder ein manueller technischer Umweg nötig.
- Ein grüner lokaler Test wird dadurch nicht automatisch in der Test-App sichtbar.
- Es besteht das Risiko, dass jemand den Gate-geschützten Workflow direkt per CLI ausführt, nur um schneller testen zu können.

## Erwartetes Verhalten

Ein autorisierter Preview-Aufruf soll aus dem vorgesehenen KGG-Workflow heraus möglich sein:

1. Test-/Preview-Wunsch mit stabiler Request-ID absenden.
2. Genau einen `submitKggPreviewAuto`-Aufruf ausführen.
3. Intern unverändert `validate_only` und danach `publish_preview` mit demselben Payload ausführen.
4. Den Run bis zum Abschluss verfolgen.
5. Test-App-URL, `meta.json`, Artefakt und Status sichtbar zurückgeben.
6. Keine PR-, Main- oder Live-Aktion auslösen.

Die Bedienung soll für Max wie ein unkomplizierter „Test-App laden“-Schritt wirken; der bestehende Write-Gate bleibt dabei aktiv.

## Technische Ursache

- Die Workflows `KGG GPT Preview Auto` und `KGG GPT Preview Gate` sind im Repository vorhanden.
- Der aktuelle Agent-/GPT-Kontext stellt die dafür vorgeschriebene callable Aktion `submitKggPreviewAuto` jedoch nicht bereit.
- Die zugehörigen Status-/Run-/Artefakt-Leseaktionen sind ebenfalls nicht verfügbar.
- Der lokale Harness ist deshalb nur lokal bzw. über den mitgelieferten Smoke-Runner prüfbar.

## Akzeptanzkriterien

- [ ] Eine berechtigte Preview-Anfrage kann ohne manuellen CLI-Workflow an die Test-App gesendet werden.
- [ ] Pro Anfrage entsteht genau ein Auto-Run mit sichtbarer Request-ID.
- [ ] `validate_only` läuft vor `publish_preview`; bei roter Validierung wird nichts veröffentlicht.
- [ ] Nach Erfolg werden Run-ID, Status, Artefakt, `meta.json` und ausgeschriebene Test-App-URL angezeigt.
- [ ] Max kann die Test-App direkt öffnen und die Funktion selbst prüfen.
- [ ] PR/Main/Live bleiben bis zur separaten Freigabe vollständig unangetastet.
- [ ] Payloads, Patientendaten, Secrets und interne Debugdaten erscheinen weder im Status noch in der normalen Test-App-Ausgabe.
- [ ] Ein fehlender oder nicht verbundener Action-Weg wird als klarer Blocker gemeldet, statt einen unautorisierten CLI-Ersatz zu verwenden.

## Aktueller Workaround

Der Cockpit-Harness kann lokal geöffnet werden:

`release-pipeline/kgg_therapy_cockpit_integration_harness.html`

Automatischer Lauf über alle Tablet-Viewports:

`node release-pipeline/kgg_therapy_cockpit_integration_harness_smoke.js`

## Abgrenzung

Dieses Ticket fordert keinen Main-/Live-Release, keine Änderung der Patienten-App und keinen Bypass des bestehenden Preview-Gates.

## Nachweis aus dem betroffenen Lauf

- Lokaler Integrations-Harness: 24/24 Prüfungen grün bei 820x1180, 1024x768 und 1280x800.
- PR #197 blieb Draft mit `kgg-no-release`.
- Remote Required Gate, Validate/build und Android-Wrapper waren grün.
- Remote Test-App-Dispatch: nicht ausgeführt, weil `submitKggPreviewAuto` im aktuellen Kontext nicht verfügbar war.

