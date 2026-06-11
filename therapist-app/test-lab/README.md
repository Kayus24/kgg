# KGG Test-Lab

Dieser Ordner ist die Sicherheitszone fuer Experimente an der KGG-App.

Ziel:
- Tests bauen, ohne die Haupt-App zu beruehren.
- v389 bleibt Source-Basis fuer aktuelle Tests.
- Jede Testidee bekommt einen eigenen Unterordner oder eine eigene Testdatei.

Regeln:
- Keine Aenderung an therapist-app/admin.html, kollegen.html oder aktuellen Release-Dateien, solange ein Test nicht geprueft ist.
- Keine PDF/QR/Patienten-App/Scan/Parser-Aenderungen, wenn der Test nur UI/Karten betrifft.
- Ein Test = ein klarer Zweck.
- Erst testen, dann entscheiden, ob ein Mini-Patch in die Haupt-App darf.

Aktuelle Testthemen:
- cardlogic360: Kartenbewegung/Drag/Swipe im Bereich "Uebungen im Plan".

Wichtige aktuelle Hauptbasis:
- therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html
- therapist-app/releases/v389/web/KGG_APP_ADMIN_v389_flow_stability.html

Nicht als Hauptbasis verwenden:
- alte v360/v366-Bundles nur als Referenz fuer Verhalten.
