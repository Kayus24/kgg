# ChatGPT-Patch-Regeln für das KGG-/Physio-App-Projekt

Ziel: Änderungen sollen kontrolliert passieren, damit funktionierende Teile nicht ungesehen kaputt gepatcht werden.

## Grundregel

ChatGPT darf nicht mehr blind die komplette App ersetzen.

Jeder Patch muss vorher klar sagen:

1. Welche Datei oder welcher Funktionsbereich geändert wird
2. Welche Bereiche ausdrücklich nicht angefasst werden
3. Warum die Änderung nötig ist
4. Welche Mini-Testliste danach ausgeführt werden muss

## Standard-Prompt vor jeder Änderung

```text
Aktueller stabiler Stand: [Versionsname eintragen]
Ziel der Änderung: [kurz beschreiben]

Bitte zuerst analysieren, noch nichts ändern.
Sag mir:
1. Welche Stelle wahrscheinlich betroffen ist
2. Welche Datei/Funktion du ändern würdest
3. Welche Bereiche du ausdrücklich nicht anfassen wirst
4. Welche Tests ich danach machen muss

Wichtig:
- Keine komplette App blind neu schreiben
- Kamera nicht anfassen, außer es geht ausdrücklich um Kamera
- Galerie nicht anfassen, außer es geht ausdrücklich um Galerie
- PDF/QR nicht anfassen, außer es geht ausdrücklich darum
- Patienten-App und Therapeut:innen-App getrennt behandeln
```

## Patch-Prompt nach der Analyse

```text
Okay, gib mir jetzt den Patch.
Bitte nur den betroffenen Bereich oder die betroffene Datei ausgeben.
Keine anderen Funktionen umbauen.
Danach eine kurze Testliste geben.
```

## Sperrbereiche

Diese Bereiche dürfen bei normalen Änderungen nicht versehentlich verändert werden:

- Kamera-Scan
- Galerie-Upload
- Mehrseiten-Scan-Flow
- PDF-Export
- QR-Export
- Patientenansicht
- Therapeut:innenansicht
- Lokaler Speicher
- Übungsbank
- Übungspakete

## Kamera/Galerie-Regel

Kamera und Galerie dürfen nicht zwei verschiedene Scan-Logiken benutzen.

Beide Wege müssen am Ende dieselbe zentrale Funktion aufrufen, zum Beispiel:

```text
addScannedImageToCurrentPlan(imageData)
```

Danach muss immer dieselbe Frage erscheinen:

1. Soll dem Plan noch eine Seite angehängt werden?
2. Soll noch ein Plan gescannt werden?
3. Fertig

## Wenn ein Fehler wiederkommt

Nicht sofort neu patchen.

Erst klären:

1. Welche letzte Version war stabil?
2. Welche Änderung kam danach?
3. Welche Funktion war betroffen?
4. Ist der Fehler Kamera, Galerie, Scan-Flow, Speicher oder UI?

## Arbeitsprinzip

Lieber kleine sichere Schritte als große Komplett-Patches.

Nach jeder funktionierenden Änderung:

1. Version notieren
2. Pflicht-Test machen
3. Commit speichern
4. Erst dann weiterarbeiten
