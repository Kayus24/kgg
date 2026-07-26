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
