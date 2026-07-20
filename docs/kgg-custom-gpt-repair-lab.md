# KGG Custom GPT Repair-Lab

## Ziel

Der Repair-Lab misst, ob ein isolierter Custom GPT eine fehlende UI- oder Funktionsverbindung in einer vollstaendigen, aktuellen Admin-App als neues modulares v2-Patchmodul wiederherstellen kann. Er ist kein Ersatz fuer Preview/Test-App oder Max' Freigabe.

## Blindheit

- Der Eval-GPT erhaelt nur Symptom, sichtbares Sollverhalten und die beschaedigte Voll-App in exakten Source-Chunks.
- Er erhaelt keinen Zugriff auf `main`, Golden Source, interne Fallnamen, Browser-Assertions, Kontrollpayloads oder produktive Source-Knowledge-Dateien.
- Web Search ist im Eval-GPT aus. Nur die beiden Repair-Lab Actions und `docs/kgg-custom-gpt-eval-knowledge.md` sind erlaubt.
- Challenge-IDs sind Hashwerte. Die zwei Holdouts sind im oeffentlichen Index nicht als Holdout markiert.

## Acht Kernbereiche

1. Phone-Admin-Menue
2. Phone-Foto-Menue
3. Uebungsdatenbank-Thumbnails
4. Live-Uebungseingabe loeschen
5. Phone-Verlauf/Pakete-Drawer
6. Tablet-Uebungseditor
7. Tablet-Karten-Reorder
8. Tablet-Skalierung speichern/laden

Zwei zusaetzliche Holdouts pruefen Layout-Panel und Phone-Menue-Verankerung. Diese zwei verdeckten Holdouts und ihre interne Zuordnung werden nicht in den GPT-Kontext geladen.

## Ablauf

1. `publish_challenges` erzeugt alle Voll-App-Varianten aus der bytegenau gebauten aktuellen `kgg-update/index.html`.
2. Nur `public/` wird auf Branch `gpt-repair-lab` veroeffentlicht.
3. Der Eval-GPT liest eine undurchsichtige Challenge und erzeugt ein v2-Payload ohne Pfadangabe.
4. `evaluate_attempt` regeneriert intern dieselbe Runde, prueft Payload und Hash und setzt das Patchmodul nur in einer temporaeren Kopie ein.
5. Chromium prueft sichtbares Verhalten, Interaktionen, Seitenfehler und blockierte externe Requests.
6. Nach drei gleichen Fehlerklassen fuer dieselbe Challenge wird gestoppt und ein alternativer Ansatz verlangt.
7. Erfolg erst nach zwei vollstaendigen Runden mit 8/8 Kernfaellen und 2/2 Holdouts unter identischem Modell- und Ressourcenhash.

## Lokale Kontrollen

```powershell
python release-pipeline/kgg_gpt_repair_lab.py --self-test
python release-pipeline/kgg_gpt_repair_lab.py --self-test --browser
python release-pipeline/kgg_gpt_repair_stabilize.py --self-test
python release-pipeline/kgg_custom_gpt_resource_audit.py --check
```

Der Browser-Selbsttest verlangt pro Fall: Golden `PASS`, beschaedigt `FAIL`, Kontrollreparatur `PASS`. Alle Ausgaben liegen nur im temporaeren Testverzeichnis und duerfen weder in Production-Knowledge noch in den Lab-Branch gelangen.

## Produktionsgrenze

Ein Repair-Lab-PASS erzeugt weder Preview/Test-App noch PR oder Main-Aenderung. Ein echter App-Patch laeuft weiterhin separat ueber `validate_only -> publish_preview -> Max prueft Test-App -> create_pr/publish_admin_beta`.
