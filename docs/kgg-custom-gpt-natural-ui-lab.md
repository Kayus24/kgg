# KGG Natural-Language UI Repair Lab

## Ziel

Das Natural UI Lab misst getrennt, ob der KGG Update-Agent Max' natuerliche, fehlerhafte Alltagssprache und markierte Screenshots versteht und ob das modellgleiche isolierte Eval-Profil daraus einen sicheren modularen UI-Patch erzeugt.

## Testintegritaet

- Der Produktions-GPT prueft nur Sprachverstehen, UI-Ziel und Rueckfrageverhalten. Er erhaelt keine Blind-Challenge-ID, damit seine intakten Production-Source-Actions den Test nicht durch einen direkten Vergleich kompromittieren.
- Der isolierte Eval-GPT erhaelt verrauschte Nachricht, markierten Screenshot, Viewport und beschaedigte Source-Chunks.
- Kanonische Absicht, Golden Source, Browser-Assertions, Klarstellungsantwort und Kontrollpatch bleiben ausschliesslich im temporaeren internen Manifest.
- Der oeffentliche Branch `gpt-natural-ui-lab` enthaelt keine internen Feldnamen oder Musterloesungen.

## Sechs Klassen

1. Unklares Tablet-Editor-Layout.
2. Doppeltes altes Phone-Admin-Control.
3. Falsch verankertes Phone-Menue.
4. Vermischte Skalierung und Spaltenbreite.
5. Aktiver Layout-Button mit verborgenem Panel.
6. Zwei markierte Menues mit genau einer notwendigen Rueckfrage.

Die konkrete Formulierung wird pro Runde aus anonymisierten Sprachmustern und neu erzeugten Varianten bestimmt. Screenshots entstehen erst aus der beschaedigten Voll-App und erhalten danach gelbe benutzeraehnliche Markierungen.

## Bewertung

Jede Abgabe enthaelt `interpretation` und einen modularen v2-`payload`. Der private Evaluator bewertet getrennt:

Der oeffentliche Vertrag typisiert alle Interpretationsfelder. Insbesondere ist
`confidence` einer der Strings `low`, `medium` oder `high`; `clarification_count`
ist die Ganzzahl `0` oder `1`.

- rekonstruierte Benutzerabsicht,
- UI-Diagnose,
- Rueckfragepolitik,
- Patch-Sicherheit,
- Browser-Verhalten,
- sichtbares Ergebnis.

Akzeptanz sind zwei Runden mit je sechs frischen Challenges, mindestens 10 von 12 Erfolgen im ersten Versuch und alle 12 spaetestens im zweiten Versuch. Nach drei gleichen Fehlerklassen ist ein alternativer Ansatz Pflicht.

## Lokale Kontrollen

```powershell
python release-pipeline/kgg_gpt_natural_ui_lab.py --self-test
python release-pipeline/kgg_gpt_natural_ui_lab.py --self-test --browser
python release-pipeline/kgg_gpt_natural_ui_stabilize.py --self-test
```

Ein Lab-PASS erzeugt keine Preview und keine Main-Aenderung. Der beste erfolgreiche Patch muss separat durch `validate_only -> publish_preview -> Test-APK -> Max-Freigabe`.
