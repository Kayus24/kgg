# AGENTS.md - KGG Physio-App

## Projekt

KGG/Physio-App für Therapeut:innen: Trainingspläne erstellen, Übungen verwalten, PDFs und QR/Patienten-App erzeugen, Scan/OCR nutzen, Medien verwalten und Releases kontrolliert veröffentlichen.

## Verbindliche Arbeitsregeln

- Nicht neu bauen und ohne ausdrücklichen Auftrag nicht refaktorieren.
- Immer den kleinsten sicheren Patch und nur eine logische Änderung pro Patch umsetzen.
- Bestehende funktionierende Hooks erhalten und keine Layoutänderungen nebenbei durchführen.
- Keine API-Keys, Tokens oder anderen Geheimnisse in Dateien oder Ausgaben speichern.
- Patient:innen erhalten keine JSON-Dateien und sehen keine Roh-JSON-, Base64- oder Debugdaten als normale Ausgabe.
- `KGGDataStore.currentPlan` bleibt die zentrale Plan-State-Quelle.
- Bestehende fremde oder uncommitted Änderungen niemals zurücksetzen.

## Geschützte Bereiche

PDF, QR/Patienten-App, Scan/OCR, Parser, Plan-State, Medien/Upload, API-Key-Logik, Android/APK, GitHub-Manifest und Handy-Layout nur mit ausdrücklichem Auftrag anfassen und anschließend bereichsgerecht testen.

## Live-Stand

- Tatsächliche Web-Version und Quelle aus `kgg-update/version.json` laden.
- Tatsächliche Releases und APK-Versionen aus `therapist-app/android_update_manifest.json` laden.
- Nicht aus lokalen Altdateien oder Modellgedächtnis auf den Live-Stand schließen.
- App-, HTML-, Release- und Uploadänderungen niemals direkt auf `main` schreiben; Branch, Tests und Pull Request verwenden.

## Workspace-Schutz

- In jedem neuen Clone vor der ersten Aenderung einmal `python release-pipeline/kgg_hook_guard.py --install` ausfuehren.
- Vor Commit oder Push mit `python release-pipeline/kgg_hook_guard.py --check` pruefen, dass `.githooks` aktiv ist.
- Fehlende Hook-Aktivierung ist ein Stop-Signal. GitHub Push Protection und Required Gate bleiben zusaetzliche, nicht ersetzende Schutzschichten.

## Repo-Navigation und Suchhygiene

- Patienten-App: `index.html`, `patient-*.js`, `collapse-cards.js`, `service-worker.js` und die zugehörigen PWA-Dateien.
- Editierbare Therapeut:innen-Quelle: `kgg-update/src/**`.
- Generiertes Therapeut:innen-Artefakt: `kgg-update/index.html`; niemals direkt als Patchbasis bearbeiten.
- Source-/Kandidatenstand: `kgg-update/version.json`. Ein Kandidat kann dem veröffentlichten Stand voraus sein und ist deshalb nicht automatisch live.
- Kanonischer Live- und APK-Stand: `therapist-app/android_update_manifest.json`, getrennt nach Admin- und Kolleg:innen-Kanal.
- `therapist-app/kgg_update_manifest.json` ist eine Legacy-Kompatibilitätsdatei und keine kanonische Patch- oder Live-Quelle.
- Android-Quelle: `android-wrapper/**`; Release- und Prüfwerkzeuge: `release-pipeline/**`.
- `therapist-app/releases/**` enthält unveränderliche historische Artefakte und wird nur für gezielte Release-, Hash- oder Regressionsprüfungen geöffnet.
- `therapist-app/admin.html` ist bytegleich mit `therapist-app/releases/web/r0389/admin.html` und dem v389-Admin-Artefakt. Es ist ein historischer Alias, keine Patchbasis.
- `therapist-app/kollegen.html` ist bytegleich mit dem historischen v389-Kolleg:innen-Artefakt, aber nicht mit `therapist-app/releases/web/r0389/colleague.html`. Auch diese Datei ist keine Patchbasis.
- Normale Suchen vom Repository-Root aus auf die aktive Quelle begrenzen. `--no-ignore` nur zusammen mit einem ausdrücklich eingegrenzten Historienpfad verwenden.

Normale Suche:

```powershell
rg -n "KGGDataStore|finishWithPdf" kgg-update/src release-pipeline
rg -n "KGGH2|patientVersion" . -g "index.html" -g "patient-*.js" -g "service-worker.js"
```

Gezielte Historiensuche:

```powershell
rg --no-ignore -n "KGGDataStore" therapist-app/releases/web/r0424/admin.html
rg --no-ignore --files therapist-app/releases
```

## Privates Projektgedächtnis

- Repository: `Kayus24/kgg-project-memory` (privat).
- Wenn eine Aufgabe von Max' dauerhaften Entscheidungen, Begründungen, offenen Punkten oder Fehlerlektionen abhängt, zuerst `memory/index.json` lesen.
- Danach nur das kleinste passende Themenpaket aus `memory/packs/` laden; normalerweise höchstens zwei Packs.
- Records nur für Historie, Begründungen oder Konflikte öffnen. Niemals das gesamte Gedächtnis pauschal laden.
- Bestätigte neue dauerhafte Erkenntnisse automatisch über `KGG Project Memory Gate` ergänzen.
- Vor einem Update das passende Themenpaket auf Widersprüche prüfen.
- Bei gleicher Vorgabe mit anderem Wert nicht schreiben: Max alte und neue Aussage zeigen und seine ausdrückliche Freigabe abwarten.
- Ist das private Repository nicht erreichbar, fehlenden Memory-Kontext klar melden und nicht raten.
- Keine Chats, Patientendaten, Geheimnisse oder kurzlebigen Debugausgaben im Projektgedächtnis speichern.

## Tests

- Jede Codeänderung: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI-/HTML-/Layoutänderungen zusätzlich: `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT-Playbook-, Action- oder Memory-Integrationsänderungen zusätzlich: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`, `python release-pipeline\kgg_gpt_eval.py` und Knowledge-Pack-Freshness prüfen.

## Kommunikation

Mit Max auf Deutsch arbeiten: pragmatisch, direkt und mit wenigen Rückfragen. Wenn keine Vorgabe kollidiert und nichts blockiert, sinnvoll weiterarbeiten.
