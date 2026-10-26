# KGG-Testbatterien: Auswahl, Pflichtnachweis und Messgrenzen

Arbeitsbasis: main `b01f10f18f3e6accca40955dabae3fe6ddc0cfd1`, 22.10.2026.
Auftrag: vorhandenen Schutz zuverlässig auswählen und verbindlich prüfen; bestehende Runner weiterverwenden.

## Nachgewiesenes Problem

Die bisherige Required-Gate-Auswahl rief die UI-Regression bei einer alleinigen Änderung an
`patient-plan-replace-slot-fix.js`, einer React-TSX-Datei oder dem Import-Regressionstest
nicht auf. Die kritische Batterie lief weiterhin. Die vorhandene integrierte
Chromium/WebKit-Acceptance war ein unabhängiger Workflow und kein erforderlicher
Vorgänger von `required-gate`.

## Neuer Vertrag

- Konservative Patient-/React-/Testpfade wählen die vorhandene UI-Regression und
  integrierte Acceptance. Die Feature-Test-Map bleibt beratend.
- `required-gate` bleibt der Name des vorhandenen Pflichtchecks.
- Der vorhandene Parity-Workflow wird mit `workflow_call` genau einmal aus dem
  Required Gate aufgerufen. Der zusätzliche direkte Main-PR-Trigger entfällt.
- Der Aufruf übergibt die vollständige `github.sha` des PR-Mergekandidaten,
  also denselben Stand wie Core und Patient-Browser. Checkout-SHA, Runnerbelege
  und Artefaktnamen sind daran gebunden.
- Eine erforderliche Acceptance benötigt den erfolgreichen gesamten Call und
  `accepted=true`, das erst nach erfolgreichem Runner entsteht.
  Skip, fehlende Belege, Fehler oder Abbruch liefern keine Freigabe.
- Anwendbarkeitsflags müssen ausdrücklich `true` oder `false` sein.
- Passende Admin-Runtime-/Sync-Änderungen führen den vorhandenen synthetischen
  Zwei-Client-Sync-E2E im Core aus. Auch er benötigt einen expliziten
  erfolgreichen Ausführungsnachweis; seine Fehlerartefakte bleiben erhalten.
- Reine unabhängige Dokumentation erzwingt diese zusätzlichen Browserläufe
  nicht. Die vorhandene kritische Basisbatterie bleibt unbedingt.

Die neuen Selektortests führen die tatsächlichen Bash-Blöcke der Workflows mit
synthetischen Dateilisten aus. Es gibt keinen zweiten produktiven Selektor.
Die negativen Acceptance-Reporter-Verträge bleiben unverändert.

## Laufzeit und Prozessgrenzen

Günstige Ressourcen-/Freshness-Prüfungen stehen vor der langen kritischen
Batterie. Die identische Scannerregression im Core läuft bei Scanner- oder
Admin-Kamera-Änderungen einmal. Andere ähnliche Prüfungen werden nicht allein
aufgrund gleicher Dateinamen zusammengelegt.

Nur `patient-browser` verwendet das offizielle, digest-gepinnte
Playwright-`1.61.1-noble`-Image. Imageversion, Paketdeklaration, Lockfile und
installiertes Playwright müssen exakt übereinstimmen. Die Testbefehle bleiben
erhalten; die erneute Browser-/Systempaketinstallation entfällt.
Die Joblaufzeit muss einschließlich Image-Pull bewertet werden.

Der allgemeine Batterierunner begrenzt jedes Unterkommando standardmäßig auf
600 Sekunden. `KGG_TEST_COMMAND_TIMEOUT_SECONDS` kann für begründete Umgebungen
eine andere positive, endliche Frist setzen. Diese Frist ist ein Hängerschutz,
kein Produkt-Performancebudget. Timeout bricht den eigenen Prozessbaum ab und
meldet `TIMEOUT`; ein unvollständiges Cleanup bleibt sichtbar. Ein
Benutzerabbruch wird nach dem Cleanup weitergereicht.

Die Prozessbaumprüfung wurde für Linux vorgesehen. Der Windows-Pfad übernimmt
das vorhandene `taskkill /T /F`-Muster; ein Linux-Test behauptet keinen echten
Windows-/PC-Nachweis. Die bestehenden CMD-/PowerShell-Einstiege bleiben erhalten.

## Sichtbare Sync-Messung

Der bestehende Rename-Fall misst zusätzlich zwei getrennte Strecken:

1. Tatsächlicher Speichern-Klick bis der neue Name derselben ID lokal sichtbar
   und der Editor geschlossen ist, mit der monotonen Uhr in Client A.
2. Auslösen der Aktion bis der neue Name in Client B sichtbar beobachtet wird,
   mit einer gemeinsamen monotonen Node-Uhr einschließlich Automationsanteil.

Die Beobachter werden vor der Aktion aktiviert. Der Test prüft echte gerenderte
Namen, Viewport, Scroll-Clipping und Verdeckung. Er ersetzt diese Endpunkte
nicht durch einen internen Katalog-PASS und scrollt nicht nach Messbeginn.

`--ui-delay-probe-ms 250` fügt in einem ausdrücklich synthetischen Kontrolllauf
einen einmaligen Stillstand am echten Speichern-Klick ein. Der Messwert muss
die tatsächlich ausgeführte Verzögerung enthalten. Das ist eine
Empfindlichkeitsprüfung, keine neue 250-ms-Produktvorgabe.

Der Report nennt Fixturegröße, Browser-/Node-Version, Quellen-/Harnesshash und
den Dateisystem-Testadapter mit 65 ms künstlicher Verzögerung. Das
Produkt-Polling bleibt unverändert. Fehlende Messung bedeutet `INCOMPLETE`.
Die Geschwindigkeitsbewertung bleibt
`NOT_EVALUATED_NO_PRODUCT_BUDGET`, bis eine belastbare Vergleichsreihe und eine
fachliche Grenze vorliegen. Ein einzelner Rename-Messwert beweist keine p95,
große Medienlast, Touch-/Scroll-Leistung oder echte Cloud-/SAF-Latenz.

## Prüfkommandos

```bash
python release-pipeline/test_kgg_required_gate.py
python -m unittest release-pipeline/test_kgg_battery_command_timeout.py
node release-pipeline/kgg_patient_full_acceptance_report.test.mjs
python release-pipeline/kgg_test_battery.py --level critical
node release-pipeline/kgg_drive_sync_e2e.js --run --run-id timing-reference
node release-pipeline/kgg_drive_sync_e2e.js --run --run-id timing-delay --ui-delay-probe-ms 250
```

Jeder Sync-Lauf benötigt einen eigenen `run-id`. Ergebnisse stehen unter
`output/drive-sync-e2e-20261015/<run-id>/round-1/report.json`.
Die gesamte integrierte Acceptance bleibt über
`kgg_patient_integrated_acceptance.py` und `patient-integrated-suites.json`
definiert. Aktuelle Ausführungsergebnisse und Commit-SHA gehören in den PR;
diese Beschreibung ist selbst kein Testnachweis.

Native Android-/APK-Compile-/Profilprüfungen und echte Geräteabnahme bleiben
nach ihrem tatsächlichen Scope zu bewerten. Vorhandene statische/native
Critical-Verträge wurden nicht entfernt. Dieser Patch ist keine
Produktveröffentlichung und ändert keine Geräte- oder iPhone-Ausnahme.
