# KGG Custom GPT Repair-Lab Report

Status: HARNESS GREEN / REAL GPT ROUNDS PENDING

## Konfiguration

- Produktions-GPT: `KGG Update-Agent`
- Eval-GPT: isolierter Clone `KGG Repair-Lab Eval`
- Modellregel: hoechstes im Editor angebotenes, Actions-kompatibles Modell
- Aktuell verifiziertes Modell: `GPT-5.6 Thinking`
- Produktionsfaehigkeiten: Web Search, Code Interpreter, Image Generation, Custom Actions
- Eval-Faehigkeiten: Code Interpreter und ausschliesslich Repair-Lab Actions
- Eval gesperrt: Web Search, Apps, Canvas, Image Generation, Production Actions, Production Knowledge

## Harness-Kontrollen

| Runde | Kernfaelle | Holdouts | Golden | Beschaedigt | Kontrollreparatur |
| --- | ---: | ---: | --- | --- | --- |
| local-control-1 | 8/8 | 2/2 | PASS | EXPECTED FAIL | PASS |
| local-control-2 | 8/8 | 2/2 | PASS | EXPECTED FAIL | PASS |

Beide Kontrollrunden liefen gegen Source-Hash `6a7ec5ced5709040321bf6b6503067a331bfa8492c8cb7a636a9367b8afbf4cd`. Runde 2 verwendete zehn neue, aus `round_id` und Source-Hash abgeleitete Challenge-IDs.

## Echte Blindrunden

Noch nicht ausgefuehrt. Run-IDs, Modell, Ressourcenhash, Challenge-ID, Payloadhash, Ergebnis und Fehlerklasse werden hier nach jedem echten Eval-GPT-Lauf eingetragen.

## Akzeptanz

- Zwei aufeinanderfolgende vollstaendige Blindrunden unter identischem Modell- und Ressourcenhash.
- Pro Runde 8/8 Kernfaelle und 2/2 Holdouts.
- Kein Zugriff auf Golden Source oder interne Assertions.
- Keine drei gleichen Fehler hintereinander; in diesem Fall ist ein Alternativweg erforderlich.
- Repair-Lab-Erfolg ersetzt nicht Test-App- und Max-Freigabe.
