# PATCHLOG v007 — QR-Scan aus Fotodatenbank reparieren

## Ziel

Der QR-Scan über die Kamera funktioniert, aber QR-Codes aus hochgeladenen Bildern/Fotos aus der Fotodatenbank werden nicht zuverlässig erkannt.

## Ursache

Der bestehende Datei-Pfad `scanQrFromImageFile(file)` lädt Bilder nur über `URL.createObjectURL(file)` in ein `Image`-Element und scannt anschließend eine 1800px-Canvas-Version mit wenigen Crops/Filtern.

Auf Android/WebView und bei Bildern aus der Galerie kann das fehlschlagen durch:

- EXIF-/Orientierungsprobleme,
- sehr große Fotos, bei denen der QR beim Downscaling zu klein wird,
- `content://`-/FileProvider-Verhalten,
- Screenshots/Fotos mit QR in einer Ecke,
- schwachen Kontrast oder Kompressionsartefakte.

## Patch

Neues Script:

```txt
scripts/apply_v007_qr_photo_upload_decode.py
```

Es patcht nur:

```txt
kgg-update/index.html
kgg-update/version.json
```

## Technische Änderungen

- `scanImageCanvasFromFile()` wird robuster:
  - zuerst `createImageBitmap(file, { imageOrientation: "from-image" })`
  - danach ObjectURL-Fallback
  - danach DataURL/FileReader-Fallback
- `scanQrFromImageFile()` wird robuster:
  - direkter `BarcodeDetector`-Versuch auf `ImageBitmap`
  - mehrere Canvas-Größen: 2200, 3200, 1600
  - mehr Crops: Ecken, Bänder, Drittelbereiche, Center
  - Rotationen: 0/90/180/270
  - mehr Filter: normal, softContrast, contrast, thresholdLow, threshold, thresholdHigh, invert
  - kleine Crops werden auf QR-freundliche Größe hochskaliert

## Nicht geändert

- Kamera-Scan
- PDF
- QR-Erzeugung
- Patienten-App
- Parser
- Android-Wrapper
- Tablet-Layout
- Plan-State
- Storage

## Version

Empfohlen:

```txt
versionCode: 7
versionName: 1.0.4-qr-photo-upload-decode
```

## Testplan

1. App öffnen.
2. QR-Scan über Kamera testen.
3. Foto-/Datei-Upload öffnen.
4. Ein gespeichertes QR-Bild aus der Galerie auswählen.
5. Erwartung: App erkennt den QR und verarbeitet ihn wie beim Kamera-Scan.
6. Negativtest: normales Papierplan-Foto ohne QR soll weiterhin in den Papierplan-/OCR-Pfad gehen.
