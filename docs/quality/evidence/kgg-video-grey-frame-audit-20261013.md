# KGG-Videoanalyse – kurzzeitiger grauer Bildaussetzer (2026-10-13)

**Status:** VIDEO_ANOMALY_CONFIRMED / ROOT_CAUSE_UNKNOWN / REVIEW_REQUIRED.
**Kein Nachweis einer neuen React-spezifischen Regression.**
Geltungsbereich: synthetische KGG-Patienten-App-Videos, Chromium/Playwright,
Telefon 390 × 844. Keine echten Patientendaten; keine App-/Releaseänderung.

## Quellen und Befund

- Aufzeichnungsstand: a5680798e23f0d9256ac542329a4a2ad2cb74602.
- Deterministischer Parity-Bericht: PASS, 392 Prüfungen, 0 Unterschiede.
  Dies deckt compositor-/screencast-basierte Einzelbildstabilität nicht ab.
- Gemini-Webanalyse: 3.1 Pro, Denktiefe Hoch, API-frei.
  [Strukturierter Modellbefund](kgg-gemini-web-review-a568079-20261013.json).
- Beide synthetischen Videoanhänge und die fertige Gemini-Antwort wurden
  im Browser beobachtet. Die Ausgabe blieb bei zwei Browserabfragen
  identisch. Video- und Report-SHA-256 wurden durch Finalize verifiziert.
- Ursprüngliche Start-/Endzeiten der Gemini-Generierung wurden nicht
  sekundengenau erfasst. Ergebnis korrekt mit
  timingStatus UNVERIFIED_POSTHOC gespeichert; kein automatisches PASS.

Gemini meldet suspected_regression mit confidence high, severity critical,
bei remaining-kg (Legacy etwa 00:06, React etwa 00:05): zeitweise
eine graue Fläche mit Abbrechen und OK oben. Diese Beschreibung ist
durch extrahierte Einzelbilder tatsächlich belegt.

| Aufnahme | Belegzeit | Einzelbild |
| --- | --- | --- |
| Legacy | ca. 6,33 s | [synthetischer Beleg](kgg-grey-frame-legacy-6s.png) |
| React | ca. 5,47 s | [synthetischer Beleg](kgg-grey-frame-react-5s.png) |

## Unabhängiger Einzelbildaudit

FFmpeg-Dekodierung der gespeicherten WebM-Dateien mit 30 fps und
100 × 216 Pixeln. Im unteren Bildausschnitt (y=106 bis 203)
wurden dunkle Pixel unter 1,5 % sowie graue Pixel über 97 %
als auffälliger Grauframe klassifiziert.

- **Legacy:** 7 auffällige 30-fps-Samples bei 5,23; 5,37; 6,23;
  6,33; 6,97; 8,40; 8,53 Sekunden. Sieben einzelne Aussetzer
  mit ungefähr 33 ms Dauer pro Sample.
- **React:** 7 auffällige 30-fps-Samples bei 3,73; 4,73; 4,80;
  5,37; 5,47; 5,50; 6,80 Sekunden. Sechs Aussetzer,
  einer mit zwei aufeinanderfolgenden Samples (etwa 67 ms).

Die Zahlen stammen aus dem dekodierten 30-fps-Ausgabestrom, nicht
aus einer unabhängigen Messung der tatsächlich sichtbaren
Original-Displayframes. Benachbarte Einzelbilder zeigen wieder
das vollständige NumPad.

Ein separat protokollierter kg/Wdh-Wechsel zeigte in beiden Varianten
padOpen=true, window.scrollY=0 und main.scrollTop=273 über die
abgetasteten Animationsframes. Diese Messung schließt einen kurzen
Compositor-/Paint-/Recorderfehler nicht aus.

## Einordnung und weiterer Test

- Die optische Störung ist in beiden Videodateien real vorhanden.
- Ein React-**Mehrfehler** gegenüber Legacy ist nicht bewiesen.
- Ungeklärt ist, ob das Original-Chromium-Rendering, der Compositor
  beim Aufnehmen oder der Playwright-Recorder verursacht.
- Die Modellbezeichnung critical ist keine objektiv bestätigte
  klinische oder technische Kritikalität.
- Der frühere Oppo-/Android-Flackerfix darf aufgrund eines
  Desktop-Video-Artefakts nicht als rückgängig behauptet werden.
- Ein Alt=Neu-Test kann einen gemeinsamen Bildfehler übersehen.

**Nächster gesonderter Debug-Schritt:** denselben synthetischen Ablauf
gleichzeitig per unabhängigem Browser-Screencast und Playwright-WebM
aufnehmen, Framezeiten/Compositor-Paint und Overlay/Scroll-Positionen
abgleichen. Danach vorhandenes KGG UI Lab und Oppo-Realgerät nutzen.
Produktcode erst nach Reproduktion gezielt ändern. Optional
advisory Frame-Anomaly-Test ergänzen. Keine Testassertions abschwächen.

**Freigabe:** Gemini-Review korrekt als REVIEW_REQUIRED dokumentiert.
Kein automatischer Merge, kein Release, kein Gesamt-App-PASS.
