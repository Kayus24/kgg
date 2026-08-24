# Dual-Geräte QR-Test v404

## Zweck

Das Galaxy Tab S9 zeigt künstliche QR-Codes. Das Oppo Find X9 scannt sie mit
dem echten Scanner der Patienten-App. Beide Geräte benutzen dieselbe zufällige
Sitzungsnummer.

Die Oppo-PWA ist öffentlich lesbar. Sie enthält deshalb keine Zugangsdaten und
keine echten Patientendaten. Die Tab-APK wird als geschütztes GitHub-Artefakt
bereitgestellt. Auch eine APK darf niemals als geheimer Speicher behandelt
werden.

## Apps

- Tab: `KGG QR-Teststation`, Paket `de.kgg.preview`, Version
  `0.2.14-v404-dual-device-qr-test`.
- Oppo: `KGG Patienten-Test v404`, öffentliche installierbare PWA unter
  `https://kayus24.github.io/kgg-patient-preview/device-test/`.
- Berichte: private Issues in `Kayus24/kgg-device-test-reports`.

Die Apps besitzen kein GitHub-Token. Sie öffnen nur einen vorbereiteten
Issue-Entwurf. Der angemeldete Benutzer sendet ihn selbst ab.

Die Patienten-Test-PWA verwendet einen eigenen, sitzungsgebundenen
Speicherbereich. Sie liest oder überschreibt keine normalen Patientenpläne im
Chrome-Speicher. Auch der QR-Generator liegt lokal in der PWA. Der Test kann
deshalb nach dem ersten Laden ohne CDN weiterlaufen.

## Veröffentlichung nach ausdrücklicher Freigabe

Zuerst muss der lokale Branch des privaten Bericht-Repositories veröffentlicht
werden. Danach wird der v404-Branch gepusht. Erst dann darf der vorhandene
Preview-Workflow auf dem v404-Branch gestartet werden:

```powershell
gh workflow run kgg-gpt-preview-gate.yml `
  --ref codex/dual-device-qr-test-station-v404 `
  -f mode=publish_device_test `
  -f request_id=dual-device-v404-quick-001 `
  -f payload_json='{}' `
  -f source_sha=<vollständiger-commit-sha> `
  -f device_test_profile=quick
```

Für den Volltest wird nur `device_test_profile=full` geändert und eine neue
Request-ID verwendet. APK, PWA, Job-Manifest und Prüfsummen müssen aus
demselben Workflow-Lauf stammen.

## Installation

1. Auf dem Tab das APK-Artefakt des Workflow-Laufs herunterladen und
   `KGG QR-Teststation` installieren.
2. Auf dem Oppo die öffentliche Patienten-Testseite in Chrome öffnen und zum
   Startbildschirm hinzufügen.
3. Auf beiden Geräten prüfen, dass die angezeigte Version v404 ist.
4. Auf dem Tab die Teststation starten.
5. Den ersten Verbindungs-QR mit dem Oppo öffnen.

## Schnelltest

Der Schnelltest dauert ungefähr fünf bis acht Minuten:

1. Verbindungs-QR öffnen.
2. KGGH2 mit einer und sieben Übungen scannen.
3. KGGH3 mit sieben, zwölf und 20 Übungen scannen.
4. Den kleinen und schrägen KGGH3-Code scannen.
5. Prüfen, dass der Kamerastream beendet wird.
6. Auf beiden Geräten den vorbereiteten privaten Bericht absenden.

## Volltest

Der Volltest ergänzt:

- Tablet-Hochformat, Querformat und geteilten Bildschirm.
- KGGH2 mit zwölf und 20 Übungen als Diagnose.
- schwachen Kontrast und Foto-Auswahl.
- Hinzufügen, Ersetzen, Abbrechen, Planwechsel und Umbenennen.
- Speicherung, Reload sowie Offline-/Online-Wiederherstellung.

Die physischen QR-Scans werden in einem gemeinsamen Block durchgeführt.

## Abnahme

Ein echter Kameratest ist nur bestanden, wenn das Oppo den QR wirklich liest.
Emulator- und Browserprüfungen dürfen dieses Ergebnis nicht ersetzen. Bei jedem
Pflichtplan müssen Anzahl, Reihenfolge und Fingerabdruck stimmen. Ein Rückfall
auf nur eine Übung ist immer ein Fehler.

Das iPhone bleibt simuliert. Ein echter iPhone-Kameratest bleibt offen.

## Sperren

Ohne weitere Freigabe erfolgen kein Push, kein Merge, kein Release und kein
Ticketabschluss.
