# 2026-07-29 - OCR-Kamera und nativer Scanner

## Problem

Die Test-App startete die rueckseitige Systemkamera mit einem optisch starken
Zoom. Ein vorheriger HTML-Preview-Patch versuchte das ueber den Datei-Input zu
beheben, umging dabei aber die native Picker-Modus-Meldung und beschaedigte den
automatischen Scan-Ablauf.

## Nachgewiesene Aufrufkette

`KGGScan.pick('camera')` meldet den Modus ueber `KGGNativeCamera` beziehungsweise
`KGGAndroidApp` und klickt danach `fileInput`. `MainActivity.onShowFileChooser()`
verwendete fuer Kameraaufnahmen bisher `MediaStore.ACTION_IMAGE_CAPTURE`.
Dieser Intent bietet keinen portablen Vertrag fuer einen Start-Zoom.

## Custom-GPT-Beobachtung

- Der GPT lud Live-Kontext, Playbook und Source-Routing.
- Er rekonstruierte die HTML- und Bridge-Aufrufkette korrekt.
- Er behauptete weder CameraX noch einen nicht vorhandenen Zoom-Regler.
- Er erkannte, dass der alte Preview-Patch die native Modusmeldung umging.
- Er stoppte korrekt als `capability_gap`, weil der damalige Source-Kontext
  keine nativen Android-Dateien und das Write-Gate keinen nativen Patchvertrag
  enthielten.
- Nach Bereitstellung der echten Android-Struktur empfahl er einen
  Preview-only ML-Kit-Dokument-Scanner mit bestehender Kamera als Fallback.

Die Arbeitsweise war sicher und fachlich sinnvoll. Korrigiert werden mussten
der vorgeschlagene Request-Code, die bestehende Berechtigungslogik und die
explizite Modulverfuegbarkeitspruefung.

## Loesung/Fix

- Nur das Preview-Profil verwendet den ML-Kit-Dokument-Scanner.
- Galerieimport bleibt aus, Ausgabe bleibt ein einzelnes JPEG.
- Das dynamische Google-Play-Modul wird vor dem Start geprueft und kontrolliert
  installiert.
- Installations- oder Startfehler fallen auf den bisherigen Kamera-Intent
  zurueck.
- Ein echter Abbruch im bereits gestarteten Scanner bleibt ein Abbruch.
- Alle Scannerpfade schliessen denselben `ValueCallback<Uri[]>` genau einmal.
- Der generierte GPT-Source-Kontext enthaelt nun feste read-only Android-Quellen
  und passende Kamera-/Scanner-Marker.

## Tests

- Android-Vertrag gruen.
- Preview-Debug-APK baut lokal gruen.
- Vollstaendige Critical-Batterie gruen.
- UI-Stability Regression isoliert gruen.
- API-35-Emulator: APK installiert und gestartet, kein App-Crash.
- ML-Kit-Modul war im Emulator nicht ladbar; der neue technische Fallback
  erreichte nachweisbar die bestehende Kamera-Berechtigungsabfrage.

## Verbleibendes Gate

Der Emulator besitzt keine verlaessliche Kamera und kann die optische Wirkung
des Dokument-Scanners nicht bewerten. Vor Admin/Main muss Max die Preview-APK
auf dem echten Handy pruefen: normales weites Kamerabild, automatische
Dokumenterkennung, Rueckgabe an den bestehenden OCR-Ablauf und unveraenderter
Galerieimport.

## Bereiche

- android
- scan-ocr
- custom-gpt
- preview
