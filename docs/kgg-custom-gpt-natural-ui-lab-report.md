# KGG Natural-Language UI Repair Lab Report

Status: HARNESS GREEN / PRODUCTION LANGUAGE GREEN / LIVE ROUNDS PENDING / TEST-APP PENDING

## Konfiguration

- Produktions-GPT: `KGG Update-Agent`
- Isolierter Reparatur-GPT: `KGG Repair-Lab Eval`
- Modell: hoechstes im Editor angebotenes Actions-kompatibles Modell, fuer beide Profile identisch
- Umfang: zwei Runden mit je sechs frischen Challenges
- Oeffentlicher Branch: `gpt-natural-ui-lab`
- Golden-Daten: nur temporaeres internes CI-Manifest

## Lokale Kontrollen

| Runde | Golden | Beschaedigt | Kontrollreparatur | Markierte Screenshots |
| --- | --- | --- | --- | --- |
| `natural-control-20260726-a` | 6/6 PASS | 6/6 EXPECTED FAIL | 6/6 PASS | 6/6 PASS |
| `natural-control-20260726-b` | 6/6 PASS | 6/6 EXPECTED FAIL | 6/6 PASS | 6/6 PASS |

Beide Kontrollrunden liefen gegen die bytegenau gebaute Source
`6a7ec5ced5709040321bf6b6503067a331bfa8492c8cb7a636a9367b8afbf4cd`.

## Produktions-GPT Sprache

| Test | Ergebnis | Nachweis |
| --- | --- | --- |
| Eindeutige verrauschte UI-Anfrage ohne Rueckfrage | PASS | Browser-Editor 2026-07-26: Scale und Spaltenbreite korrekt getrennt; keine Rueckfrage, Preview oder Write. |
| Echte Mehrdeutigkeit mit genau einer Rueckfrage | PASS | Browser-Editor 2026-07-26: genau eine Frage zu zwei sichtbaren Zielen; Klarstellung `Basisdaten` ohne zweite Frage oder Write. |

## Blinde Eval-Runden

Erster Live-Infrastruktur-Canary `30207660270` scheiterte vor der Challenge-
Veroeffentlichung mit `ci_tooling`: Chromium war installiert, aber `playwright`
fehlte im `NODE_PATH` des Python-gestarteten Browserprozesses. Der Workflow
installiert die Laufzeit deshalb dauerhaft unter `$RUNNER_TEMP/kgg-playwright`
und exportiert den Modulpfad jobweit; ein Vertragstest deckt diesen Fehler ab.

Die verworfene Live-Runde `natural-live-20260726-r1` fand danach einen
Evaluatorfehler: Runs `30208200265` und `30208301247` erkannten `handy` und
`menue`, werteten die korrekte Formulierung `innerhalb des Kopfs`/`Plan-Header`
aber nicht als `im Kopf`. Die semantischen Aliasse und ein Regressionstest
wurden erweitert. Diese Runde zaehlt nicht zur Akzeptanz; die zwei Pflicht-
Runden beginnen mit neuen Seeds.

| Runde | Challenges | First-attempt PASS | Final PASS | Neue Fehlerklasse |
| --- | ---: | ---: | ---: | --- |
| Runde 1 | 0/6 | 0/6 | 0/6 | PENDING |
| Runde 2 | 0/6 | 0/6 | 0/6 | PENDING |

## Preview/Test-App

| Gate | Ergebnis | Nachweis |
| --- | --- | --- |
| `validate_only` | PENDING | |
| `publish_preview` | PENDING | |
| Artifact/HTML/APK/meta HTTP 200 | PENDING | |
| API-35 Emulator | PENDING | |
| Max Test-App-Freigabe | PENDING | |

`publish_admin_beta` und Main bleiben gesperrt, bis Max die Test-App ausdruecklich freigibt.
