# Pitfalls / Hindernisse bei der KGG-App

Diese Punkte sind Projektregeln aus der bisherigen Entwicklung. Sie sollen verhindern, dass spätere Versionen alte Fehler wieder einbauen.

## UX / Grundflow

- Nicht zu viele UI-Schritte bauen. Der beste Flow ist: `Übungen eintippen → aktueller Plan entsteht links → PDF/QR`.
- Zwischenstufen wie „erkannte Eingaben“ oder extra „übernehmen“ verwirren und sollen nicht zum Hauptflow werden.
- PDF/QR-Buttons gehören direkt in den aktuellen Planbereich, nicht versteckt in Untermenüs.
- Die Therapeuten-App bleibt zunächst lokal, bis sie stabil läuft. GitHub dient vorerst primär der Patienten-App.

## Übungseingabe / Übungsbank

- Das Eingabefeld darf nicht automatisch auf Datenbanknamen umgeschrieben werden. Die freie Schreibweise des Therapeuten muss erhalten bleiben.
- Neue Übungen dürfen nicht beim Tippen dauerhaft gespeichert werden. Sonst entstehen Datenbank-Leichen aus halben Eingaben wie `knie c`.
- Neue Übungen erst speichern bei Bestätigung oder PDF-/QR-Freigabe.
- Die letzte Übung muss live im aktuellen Plan erscheinen, ohne dass man aus dem Textfeld klicken muss.
- Zahnrad-Bearbeitung darf kein Pflicht-„Fertig“ zum Speichern brauchen. Änderungen sollen automatisch speichern; Button nur „schließen“.
- Startwerte pro Übung sind optional und sollen als T1-Vorschlag erscheinen, nicht als unveränderlicher Pflichtwert.

## Android/Oppo / Touch-Probleme

- Textfelder dürfen sich beim Öffnen von Zahnrad/Katalog nicht automatisch fokussieren, sonst öffnet sich auf Android/Oppo nervig die Tastatur.
- Long-Press auf Übungskarten kann auf Android Textauswahl/Tastatur/Kontextmenü auslösen.
- Für Drag-Karten Textauswahl und Kontextmenü blockieren, aber Eingabefelder im Editor normal nutzbar lassen.
- PDF-Download auf Oppo/Android ist problematisch mit Blob-Links. Immer Share-/Download-Fallback anbieten.
- Direkte PDF-Vorschau nur optional einsetzen.

## Drag & Drop

- Drag & Drop muss visuell geführt werden: gezogene Karte hervorheben, Ziel-Lücke anzeigen, Nachbarkarten leicht auseinander gleiten lassen.
- Die Ursprungslücke beim Herausziehen darf nicht zu groß bleiben; Karten sollen etwas zusammenrücken, aber Zielposition sichtbar bleiben.
- ↑/↓ Pfeile wurden als überflüssig empfunden, wenn Drag-Griff funktioniert.

## QR / PWA / GitHub

- QR-Erzeugung im Browser kann scheitern, wenn die QR-Library nicht lädt. Immer Link anzeigen + Fallback anbieten.
- GitHub Pages kann Code kostenlos hosten, aber keine Patientendaten/API-Keys ins Repo.
- API-Key pro Gerät lokal eintragen.
- API-Key in HTML verstecken ist nicht sicher. Im Browser ist alles auslesbar.
- Für echte API-Key-Sicherheit braucht es später Proxy/Server.
- GitHub-gehostete App ist nur offlinefähig mit `manifest.json` und `service-worker.js`.
- Lokale HTML bleibt offline wie bisher.
- QR-Lesen kann offline passieren, wenn lokal im Browser dekodiert wird. Kritisch ist nicht das QR-Lesen, sondern was im QR steht.
- Patienten-App muss separat aktualisiert werden, wenn die Therapeuten-App neue Payload-Felder sendet, z. B. `extendDays`, Startwerte oder Medien.

## Datenschutz / Scan

- Screenshot-Schutz ist im Browser nicht zuverlässig. Maximal Privacy-Overlay bei App-Wechsel/Tab-Verlassen möglich.
- Datenschutz-Scan-Regel hart halten: Originalfoto bleibt lokal, Gemini bekommt nur Leseansicht/Crops, kein Ganzblatt-Fallback.
- Wenn Crop-/Leseansicht fehlerhaft ist, abbrechen statt Gemini raten lassen.
- Bei Scan-Ergebnissen mehrere Pläne getrennt anzeigen. Nicht alles in ein Textfeld mischen.
- Patientenkürzel möglichst lokal hinzufügen.
- Wenn Kürzel in QR/PDF stehen, sind sie pseudonymisierte personenbezogene Daten, nicht anonym.

## L/R und PDF

- L/R-Erkennung darf nicht nur exakt `links/rechts` prüfen. Varianten wie `LR`, `L/R`, `links-rechts`, `linksrechts`, `left/right` robust erkennen.
- PDF-L/R-Spalten müssen explizit `li` und `re` anzeigen, wenn Übung links/rechts ist.
- Medien in PDF können browserabhängig zicken. Bilder vor PDF-Einbau ggf. per Canvas zu JPEG normalisieren.
- Videos im PDF ignorieren.

## Medien / Speicher

- Große Medien direkt in lokaler HTML/localStorage können schnell schwer werden.
- Für viele Videos/Bilder später Speicherstrategie klären.
- Patienten-App braucht Medienanzeige und ein erstes Pop-up: „Bild-/Videomaterial immer anzeigen?“

## Versionsstrategie

- Nach jedem größeren Modul eigene HTML-Datei speichern, damit man bei Crash zurückgehen und das fehlerhafte Modul eingrenzen kann.
- Bei GitHub-Änderungen Patienten-App und Therapeuten-App getrennt denken.
