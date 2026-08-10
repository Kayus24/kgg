# WebView-Kamera und Cross-App-QR brauchen reale Vertragsbelege

## Problem

Eine gruen gebaute HTML-Preview behauptete automatische QR-Uebernahme, auf dem Android-Geraet erschien aber weiter die alte stark gezoomte Systemkamera.

## Ursache

Der HTML-Patch nutzte `getUserMedia`, doch der Android-WebView leitete `PermissionRequest.RESOURCE_VIDEO_CAPTURE` nicht an die Seite weiter. Der Catch-Pfad oeffnete still die alte Datei-/Systemkamera. Mocks bewiesen nur JavaScript-Logik, nicht den nativen WebView-Vertrag.

## Loesung/Fix

WebView-Kameraberechtigung nur fuer lokal verifizierte HTML und ausschliesslich Video freigeben. Einen versionierten nativen Capability-Vertrag anbieten. Die Admin-Kamera nutzt denselben BarcodeDetector-plus-lokalen-jsQR-Fallback wie der Patientenscanner und uebergibt QR-Rohtext direkt an den Admin-Parser.

## Test

Pflicht sind Critical, UI-Stability, Admin `camera-qr`, Patient `patient-scan`, Android-Wrapper-Vertrag und Preview-APK-Build. Browser-Smoke prueft Auto-QR, jsQR-Fallback, Permission-Fallback, manuelles Foto und Track-Cleanup getrennt. Ein Emulator ersetzt den abschliessenden Handytest nicht.

## Nicht anfassen

Kein Mikrofonzugriff, kein erzwungener Zoom, keine echten Patientendaten oder echten QR-Payloads in Tests, Memory oder Agent-Koordination.

## Risiken

Ein gruenes HTML-Mock ohne nativen Capability-Test ist kein Beweis fuer die Test-App. Ein stiller Fallback kann den alten Fehler verdecken.
