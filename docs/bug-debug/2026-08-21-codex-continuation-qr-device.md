# Codex-Fortsetzung – QR / Device-Variance / Ticket 032

Stand: 2026-08-21

- Admin-Kamera-Smoke grün: BarcodeDetector, jsQR-Fallback, Berechtigungsfallback und manuelles Foto.
- Patient-Scanner-Suite läuft mit Multi-Plan-Erhalt, Track-Cleanup und vielen synthetischen Perspektiv-/Distanz-/Rotations-/Lichtfällen.
- Extreme Klein-/Dunkel-, Trapez-, Asymmetrie- und starke Yaw/Pitch-Fälle melden weiterhin `WARN` bzw. keine sichere Erkennung.
- Kein `adb` installiert und kein echtes Android-Gerät verbunden; reale Gerätevarianz ist ungeprüft.
- Keine Produktänderung und kein Preview-Dispatch erfolgt.

Nächster Schritt: mit echtem Android-/iPhone-Gerät, Modell, Browser-Version und reproduzierbarem QR-Foto testen. Synthetische Warnfälle nicht als erledigt markieren.
