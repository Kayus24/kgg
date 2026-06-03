# KGG Release v360

Dieses Paket enthaelt die sauberen Rollout-Artefakte fuer die KGG-App.

Legacy-Hinweis: Diese v360-Pfade liefern inzwischen absichtlich den aktuellen
Stand aus. So bleiben alte gedruckte QR-Codes und Downloadlinks nutzbar.

## Dateien

- `android/KGG_ANDROID_SYNC_MVP_v360_debug.apk`
  - Android-Testversion mit integriertem lokalen WebView-Wrapper und Native-Sync-MVP.
- `ios/KGG_APP_IOS_HTML_v360_sync_bundle_qr.html`
  - iOS-/Safari-Testversion als einzelne HTML-Datei.
- `web/KGG_APP_KOLLEGEN_v360_sync_bundle_qr.html`
  - Kolleg:innen-Webversion fuer Browser/PWA-Tests.
- `web/kgg_therapist_manifest.webmanifest`
  - PWA-Manifest.
- `web/kgg_therapist_sw.js`
  - Service Worker fuer PWA-Test.
- `web/kgg_therapist_icon.svg`
  - PWA/Icon-Asset.

## Sicherheitsregeln

- Keine API-Keys in diesem Release-Paket.
- Keine Patientendaten in diesem Release-Paket.
- Keine Admin-Safe-Dateien in diesem Release-Paket.
- Patient:innen und Kolleg:innen sollen keine JSON/Base64-Rohdaten als normale Ausgabe sehen.

## Manuelle Tests nach Upload

- Android APK installieren und App starten.
- iOS-HTML in Safari oeffnen.
- Plan manuell erstellen.
- Uebung aus Datenbank uebernehmen.
- PDF erzeugen.
- QR/Patienten-App erzeugen.
- Sync-QR zwischen zwei Android-Geraeten testen.
- PWA-Installation und lokales Speichern pruefen.

## Bekannte Einschraenkungen

- Die Android-Datei ist eine Debug-APK, noch keine Store-signierte Produktionsdatei.
- ADB-/Realgeraete-Test wurde lokal nur moeglich, wenn ein Geraet angeschlossen ist.
- iOS-Sync bleibt HTML/PWA-basiert; native Android-Sync ist der erste Zielpfad.
