# KGG Natural-Language UI Repair Lab Report

Status: HARNESS GREEN / PRODUCTION LANGUAGE GREEN / LIVE ROUNDS GREEN / TEST-APP PENDING

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

Die ebenfalls verworfene Runde `natural-accept-20260726-a` fand mit Run
`30208592767` eine Luecke im oeffentlichen Interpretationsvertrag:
`confidence` war als Feld genannt, aber nicht auf `low|medium|high` typisiert.
Der Contract, Eval-Bootstrap und das isolierte Knowledge nennen die Typen nun
explizit; ungueltige Interpretationsformen werden als `payload_schema`
klassifiziert. Auch diese Runde zaehlt nicht zur Akzeptanz.

Run `30209320029` in der verworfenen Runde `natural-accept-20260726-b`
erreichte trotz korrektem `zweispaltig` nur 67 Prozent, weil der Scorer exakt
`Spalte` suchte. Nach drei Wiederholungen der morphologischen Fehlerklasse
wurde der Ansatz gewechselt: Der Scorer erkennt jetzt begrenzt deutsche
Wortstaemme in Komposita. Regressionstests decken `zweispaltig` und
`innerhalb des Kopfs` ab. Runde B zaehlt nicht zur Akzeptanz.

Die spaeteren Diagnose-Runden J bis O wurden ebenfalls nicht gezaehlt. Sie
fanden vier voneinander getrennte Haertungen: jede falsche berechnete
Layout-Eigenschaft muss am exakt betroffenen Container korrigiert werden;
deutsche Begriffe wie `UI-Groesse`, `Klon`, `Breitenverhaeltnis` und
`Historienliste oeffnen` werden semantisch bewertet; Interaktions-Patches
verwenden vorhandene kanonische Handler statt paralleler Teilzustaende.
Nach jeder Aenderung wurden neue Seeds erzeugt und die Runde neu begonnen.

| Runde | Challenges | First-attempt PASS | Final PASS | Neue Fehlerklasse |
| --- | ---: | ---: | ---: | --- |
| `natural-accept-20260726-p` | 6/6 | 5/6 | 6/6 | keine neue Klasse; ein bekannter `payload_schema`-Fehler im ersten P4-Versuch |
| `natural-accept-20260726-q` | 6/6 | 6/6 | 6/6 | keine |

Gesamt: 11/12 Challenges im ersten Patchversuch, 12/12 spaetestens im
zweiten Versuch. Beide Mehrdeutigkeitsfaelle stellten genau eine gezielte
Rueckfrage und reparierten danach ausschliesslich die Plan-Historie.

### Run-Nachweise

- Runde P Publish: `30217365240`
- Runde P PASS: `30217482128`, `30217590137`, `30217696595`,
  `30217934725`, `30218071317`, `30218199559`
- P4 Erstversuch: `30217859263` (`payload_schema`, fehlende exakte
  `required_tests`); zweiter Versuch `30217934725` PASS
- Runde Q Publish: `30218243210`
- Runde Q PASS: `30218358083`, `30218455483`, `30218577294`,
  `30218723089`, `30218898188`, `30219071820`

## Preview/Test-App

| Gate | Ergebnis | Nachweis |
| --- | --- | --- |
| `validate_only` | PENDING | |
| `publish_preview` | PENDING | |
| Artifact/HTML/APK/meta HTTP 200 | PENDING | |
| API-35 Emulator | PENDING | |
| Max Test-App-Freigabe | PENDING | |

`publish_admin_beta` und Main bleiben gesperrt, bis Max die Test-App ausdruecklich freigibt.
