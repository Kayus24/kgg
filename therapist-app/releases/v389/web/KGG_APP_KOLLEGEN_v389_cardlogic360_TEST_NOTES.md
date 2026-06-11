# KGG v389 CardLogic360 Test Notes

Ziel: v389 als Basis behalten, aber die Kartenbewegung im Bereich "Übungen im Plan" wieder ruhiger testen.

Quelle/Basis:
- therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html

Referenz:
- KGG_APP_KOLLEGEN_v360_sync_bundle_qr (1).html
- Hinweis: Datei trägt intern v366 Mobile Floating History Packages.

Problem in v389:
- Drag/Reorder startet zu aggressiv bei vertikaler Bewegung am Drag-Handle.
- Dadurch sind die sichtbaren Bewegungsanimationen kaum noch wahrnehmbar oder wirken jitterig.
- Der alte v360/v366-Stand wirkte ruhiger, weil Drag erst nach kurzem Halten startete.

Mini-Testpatch-Idee:
Nur startAnimatedReorderPress anpassen.

Soll-Verhalten:
- Drag erst nach ca. 100 bis 140 ms Hold starten.
- Wenn vorher Bewegung > 10 bis 12 px passiert: Drag abbrechen.
- Vertikale Bewegung darf nicht sofort Reorder starten.
- Touch-Support aus v389 behalten.
- Swipe-Löschen vorerst nicht umbauen.

Nicht anfassen:
- PDF
- QR
- Patienten-App
- Scan-Core
- Parser
- Layout allgemein

Geplanter Test-Dateiname:
- KGG_APP_KOLLEGEN_v389_cardlogic360_TEST.html

Status:
- Diese Notes-Datei ist nur Übergabe/Marker.
- Die eigentliche HTML-Testdatei soll als Kopie von v389 erstellt werden und nur die Karten-Gesture-Logik überschreiben.
