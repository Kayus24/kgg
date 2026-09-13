# KGG Designsystem und Designgedächtnis

Version 1 · bestätigte Grundlage für spätere UI-, Gesten- und Animationsarbeit

## Zweck

Diese Referenz hält die gemeinsame KGG-Sprache fest. Sie beschreibt Entscheidungen, keine neue App-Struktur. Der persönliche Skill `kgg-design-language` enthält den übertragbaren Kern; das private KGG-Projektgedächtnis enthält die bestätigten KGG-Regeln und ihre Historie.

## Arbeitsregel

Vor einer späteren UI-Arbeit werden zuerst der allgemeine Skill, danach der aktive `ui`-Memory-Pack und anschließend diese KGG-Referenz gelesen. Nur `confirmed`-Regeln sind verbindlich. Neue Ideen bleiben `proposed`, bis Max sie bestätigt. Abweichungen werden nie still überschrieben.

## Visuelle Sprache

- professionell, ruhig und systemnah; inspiriert von Apple-Klarheit, ohne Apple-Komponenten zu kopieren;
- systemnahe Typografie, klare Hierarchie, normale und mittlere Gewichte;
- ruhige Flächen und subtile Trennlinien; Schatten nur bei tatsächlicher räumlicher Anhebung;
- Blau für Bewegung und Auswahl, Rot ausschließlich für destruktive Zustände;
- einheitliche Outline-Symbole statt wechselnder Emojis;
- 4-/8-Pixel-Abstände, ungefähr 16 Pixel Kartenradius und mindestens 44 Pixel Touch-Ziele.

Die maschinenlesbaren Werte stehen in [design-tokens.json](design-tokens.json).

## Gestenprinzip

Jede Komponente erklärt ihre natürliche Bewegungsachse. Die Löschachse steht immer exakt 90 Grad dazu. Diese Bedeutung wird nicht aus „links“, „rechts“, „oben“ oder „unten“ global abgeleitet.

Für horizontal angeordnete Schwierigkeitsstufen gilt: links/rechts verschiebt eine Übung zwischen benachbarten Stufen; oben/unten löscht. Eine spätere Komponente darf eine andere, auch diagonale Achse verwenden, muss sie aber ausdrücklich deklarieren.

Der vollständige Vertrag steht in [gesture-contract.md](gesture-contract.md).

## Speicherregeln

Bestätigte Entscheidungen werden append-only im privaten `Kayus24/kgg-project-memory`-Repository gespeichert. Records enthalten stabile Schlüssel, Version, Status, Gültigkeitsbereich und Begründung. Bei einer echten Änderung wird Max zuerst mit alter und neuer Aussage konfrontiert; erst danach entsteht ein neuer Record mit `supersedes`.
