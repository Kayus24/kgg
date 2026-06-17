# Patient Link Standard v1

## Ziel
Neue Patient:innen-Links sollen zuerst iOS/PWA-sicher geteilt werden.

## Neuer bevorzugter Link

```text
https://kayus24.github.io/kgg/?plan=KGGH2:<payload>
```

oder kurz:

```text
/kgg/?plan=KGGH2:<payload>
```

## Alter Fallback-Link

```text
https://kayus24.github.io/kgg/#KGGH2:<payload>
```

Der alte Hash-Link bleibt gültig und dient als Fallback.

## Warum
Bei iOS Home-Screen/Favoriten kann der Hash `#KGGH2:...` verloren gehen oder die App startet nur `/kgg/`.
Der Query-Link `?plan=...` kann beim Öffnen vom neuen Install-Modul gelesen, lokal gespeichert und zurück in den normalen Plan geladen werden.

## Regel für neue QR-Codes und Updates
Wenn ein Plan-Link oder QR-Code erzeugt wird:

1. Primär: Query-Link `?plan=KGGH2:<payload>`
2. Optional darunter/Debug: Hash-Link `#KGGH2:<payload>` als Fallback

## Bereits gepatcht
`patient-install-guide.js` ab Version `install-guide-v2-query-plan-ios` liest:

- `?plan=KGGH2:<payload>`
- `?plan=<payload>`
- `?kgg=<payload>`

und speichert den Plan in `kggCurrentPlanV1`.

## Noch zu patchen
Die Therapeut:innen-/Admin-QR-Erzeugung muss künftig standardmäßig den Query-Link ausgeben.

Nicht ändern:
- Parser
- PDF
- Scan/OCR
- Numpad
- Hauptlayout
