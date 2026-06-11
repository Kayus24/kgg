# CardLogic360 Test

Ziel:
Die Bewegungslogik der Uebungskarten testen, ohne die Haupt-App zu beruehren.

Problem:
In v389 sind die Bewegungsanimationen der Karten im Bereich "Uebungen im Plan" kaum noch sichtbar bzw. wirken jitterig. Ein frueherer Jitter-Fix hat das Verhalten verschlechtert.

Referenz:
- KGG_APP_KOLLEGEN_v360_sync_bundle_qr (1).html
- Hinweis: Datei traegt intern v366 Mobile Floating History Packages.

Aktuelle Basis:
- therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html

Testziel:
- v389 behalten.
- Nur Kartenlogik testen.
- Drag/Reorder wieder mit alter Hold-Logik pruefen.

Soll-Verhalten:
- Drag startet erst nach ca. 100 bis 140 ms Halten am Drag-Handle.
- Bewegung vor dem Hold > 10 bis 12 px bricht Drag ab.
- Vertikale Bewegung startet nicht sofort Reorder.
- Links/Rechts-Swipe bleibt separat testbar.

Nicht anfassen:
- PDF
- QR
- Patienten-App
- Scan-Core
- Parser
- Hauptlayout
- Release-Dateien ohne ausdrueckliche Freigabe

Naechster Schritt:
Eine volle v389-Testkopie in diesem Ordner erzeugen, z. B.:
- KGG_APP_KOLLEGEN_v389_cardlogic360_TEST.html

Erst nach erfolgreichem Test darf ein Mini-Patch in die Haupt-App uebernommen werden.
