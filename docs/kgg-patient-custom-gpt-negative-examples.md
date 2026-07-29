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
