# Patienten-QR Kamera-Baseline auf `main`

Stand: 20.07.2026, Basis `5e985ca`, Produktionsscanner `start-scan-v5-urlencoded-plan-link`.

## Ergebnis

- 58 automatisierte Fälle ausgeführt
- 3 Fälle bestanden
- 35 bekannte Produktlücken dokumentiert
- 20 extreme Erkennungsgrenzen dokumentiert
- 0 unerwartete Testfehler

## Reproduzierte Produktlücken

- Es gibt noch keinen kontinuierlichen `getUserMedia`-Scan; die Aktualisieren-Funktion öffnet nur eine einzelne Fotoaufnahme.
- Ein Fehler des nativen `BarcodeDetector` fällt nicht auf jsQR zurück.
- jsQR wird noch über ein CDN statt lokal aus dem Service-Worker-Cache geladen.
- Bei 25 erfolgreichen Planupdates gingen vorhandene Medien, Video-Metadaten und zusätzliche Übungsfelder verloren.

## Einordnung

Die Testbatterie bleibt auf der aktuellen Produktionsbasis grün, weil diese bekannten Abweichungen ausdrücklich als Baseline markiert sind. Nach dem jeweiligen Produktionspatch werden die zugehörigen Fälle zu verbindlichen Pass-Kriterien. Ein synthetischer Stream ersetzt nicht den abschließenden Test mit einer echten Android-Rückkamera.
