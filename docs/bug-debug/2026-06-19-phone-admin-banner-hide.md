# Buglog — Phone Admin-Datei Banner ausblenden

## Datum

2026-06-19

## Einordnung

Triage: Mini-Patch

## Problem

Im Handy-Layout ist eine gelbe interne Admin-/Testbox sichtbar:

```html
<div class="adminTestBanner">ADMIN-DATEI ...</div>
```

Diese Box gehört nicht in den normalen Handy-Flow.

## Gewünschtes Verhalten

- Im Handy-Layout bis 759px soll die Admin-Testbox nicht sichtbar sein.
- Tablet-Layout ab 760px bleibt unverändert.
- Keine Änderungen an PDF, QR, Patient-App, Scan, Parser, Plan-State oder Storage.

## Patch-Prinzip

Phone-only CSS:

```css
@media (max-width:759px){
  .adminTestBanner{
    display:none!important;
  }
}
```

## Sicherer Anwendungsweg

Der GitHub-Connector soll die vorhandene große `kgg-update/index.html` nicht blind durch eine lokale ZIP-Version ersetzen, wenn diese ältere Build-Identity enthält.

Stattdessen vom Repository-Root aus anwenden:

```bash
python3 scripts/apply_v004_phone_hide_admin_banner.py
```

Danach prüfen:

```bash
git diff -- kgg-update/index.html kgg-update/version.json
```

Erwartete Änderung:

- In `kgg-update/index.html` wird genau ein Style-Block mit der ID `kgg-mini-patch-v400-08-phone-hide-admin-file-banner` vor `</head>` eingefügt.
- `kgg-update/version.json` bekommt neue SHA-256 und Version `1.0.3-phone-admin-banner-clean`.

## Testplan

1. Clean State: `localStorage.clear(); sessionStorage.clear(); location.reload();`
2. Handy-Viewport: 390 x 844.
3. Prüfen:
   - `window.innerWidth <= 759`
   - `matchMedia('(max-width:759px)').matches === true`
   - Gelbe `ADMIN-DATEI`-Box nicht sichtbar.
4. Tablet-Viewport: 820 x 1180.
5. Prüfen:
   - `window.innerWidth >= 760`
   - Tablet-Layout unverändert.

## Nicht anfassen

- PDF
- QR
- Patienten-App
- Scan
- Parser
- Android Wrapper
- Tablet-Layout
- Plan-State
- Storage
