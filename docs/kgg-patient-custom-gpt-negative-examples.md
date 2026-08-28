# KGG Patient Custom GPT Negative Examples

## Direkter Livegang

Falsch: Nach einer plausiblen Codeidee sofort `publish_patient_live` ausfuehren.

Richtig: Live-Reads, `validate_only`, identisches `publish_preview`, Belege, Max' Browser-Abnahme und erst danach der ausdruecklich angeforderte Live-Modus.

## Veraltete Basis

Falsch: Einen Dateiausschnitt aus Knowledge mit einer geratenen SHA patchen.

Richtig: Main-SHA und aktuellen Source-Chunk live laden. Bei abweichendem Datei-SHA `stale_base` melden.

## Versionspatch

Falsch: `APP_VERSION`, `CACHE_NAME`, `const RELEASE` oder `patient-version-label.js?v=` in einer Operation ersetzen.

Richtig: Nur die Funktionsaenderung senden. Das Gate synchronisiert alle Versionsmarker und das Changelog.

## Patientendaten

Falsch: Einen echten Planlink oder einen aus dem Chat kopierten KGGH2-/KGGD1-String als Preview-Fixture speichern.

Richtig: Keine Patientendaten uebertragen. Das Gate erzeugt einen festen synthetischen Testplan.

## Interface

Falsch: KGGH2 oder KGGD1 umbenennen und gleichzeitig die Patient:innen-App live schalten.

Richtig: Nur additive, rueckwaertskompatible Erweiterungen mit `risk_class=interface`; Breaking Changes stoppen und koordinierten Release verlangen.

## Browser

Falsch: Behaupten, der Custom GPT habe den Codex-internen Browser selbst bedient.

Richtig: Preview-Link und Testliste liefern und auf Max' ausdrueckliches Browser-Ergebnis warten.

## Speicher

Falsch: Zur Fehlerbehebung `localStorage.clear()` oder `indexedDB.deleteDatabase()` einbauen.

Richtig: Bestehende Werte erhalten und Recovery nur auf PWA-Cache/Service-Worker begrenzen.

## Koordinations-404

Falsch: Wegen eines Queue-`404` auch einen isolierten visuellen Patient-UI-Patch abbrechen, obwohl Patient-Kontext, Main-SHA, Source und Dateihash frisch sind.

Richtig: `coordination_unavailable` transparent melden und nur den visuellen Standard-Patch fortsetzen. Bei QR-/Hash-/Storage- oder Cross-App-Vertraegen bleibt die Queue Pflicht und der Write stoppt.

## Kamera-Zuschnitt

Falsch: Einen optischen Kamera-Zoom durch neue `getUserMedia`-Zoom-Constraints oder Aenderungen an QR-/Planlogik beheben.

Richtig: Zuerst Frame- und Video-Seitenverhaeltnis sowie `object-fit` pruefen. Eine Aenderung an `patient-start-scan.js` muss `patient-camera`, `patient-scan` und den Full-Frame-Test ausloesen.

## Brain-Relay-Worker ohne Patient-Lead

Falsch: Einen Patient-Write direkt aus einem Worker, aus dem Admin-GPT oder aus
dem Browser-Fallback starten.

Richtig: Genau einen Patient-Lead aus der Task Capsule verwenden. Unter-Chats,
Relay, Luna-Max-Worker und Verifier liefern nur begrenzte Handoffs; der Lead
synthetisiert, prueft die Patient-Gates und meldet Completion/Blocker ueber den
bestehenden append-only Coordination-Weg.

## Brain-Relay-Worker-Limits und Sol

Falsch: Mehr als vier Unter-Chats, ueberlappende Worker-Scopes, rekursive
Delegation, einen dritten Luna-Versuch oder Sol-Code verlangen.

Richtig: Drei Luna-Max-Worker plus ein Verifier, zwei unterschiedliche Luna-
Versuche, danach Lead-Review und nur mit Cricket `NEEDS_SOL`. Sol bleibt
`SLEEPING`; eine Cricket-Eskalation erlaubt keine Patient-, Live- oder
Release-Aktion.
