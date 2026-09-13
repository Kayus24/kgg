# KGG Gesture Contract v1

Jede bewegliche Komponente muss ihre Bewegungs- und Löschachse ausdrücklich deklarieren. `movementAxis` ist die fachliche Bewegungsachse; `deleteAxis` ist exakt 90 Grad dazu. Beide Richtungen der Löschachse bedeuten Löschen.

Vor dem Achsen-Lock von ungefähr 10 Pixeln bleibt normales Scrollen möglich. Danach wird die stärkere deklarierte Achse gewählt. Bei unklarer oder widersprüchlicher Bewegung wird keine Aktion ausgelöst. Die gewählte Achse bleibt bis zum Loslassen gesperrt.

Die Standardwerte sind: Griff 80 ms halten, Kartenfläche 220 ms halten, Aktionsschwelle 28 Prozent der verfügbaren Strecke, Zurücksetzen 180–220 ms und Undo fünf Sekunden.

## Schwierigkeitsstufen

Bei horizontal angeordneten Schwierigkeitsstufen verschiebt links/rechts eine Übung in die vorherige beziehungsweise nächste Stufe. Oben/unten löscht sie. An den Randstufen federt die Karte zurück. Während der Bewegung wird die Zielstufe sichtbar markiert.

Die Komponente braucht zusätzlich sichtbare Buttons für dieselben Aktionen, Tastaturbedienung, Screenreader-Ankündigungen, Fokuszustände und ein Verhalten ohne Bewegungsanimation.
