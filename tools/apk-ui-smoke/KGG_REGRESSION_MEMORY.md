# KGG Regression Memory

Diese Datei speichert gefundene echte Fix-Regeln, damit dieselben Fehler nicht in spaeteren Chats oder Patches neu entstehen. Vor UI-/Layout-Patches zusammen mit `KGG_UI_FLOW_CONTRACT.md` lesen.

## REG-LOCAL-001 - Lokale HTML darf nicht auf GitHub/v389 springen

- Symptom: Lokale Testdateien oeffnen kurz, werden dann aber durch Auto-Update oder Service Worker auf eine alte GitHub-Version umgeleitet.
- Fix-Regel: Bei `file:`, `localhost` und `127.0.0.1` kein GitHub-Auto-Update starten und keinen Service Worker registrieren.
- Testfall: Lokale Datei mit `?qa=1` oeffnen; Build-Badge und `location.href` muessen auf der aktuellen lokalen HTML bleiben.
- Tabu: Kein lokaler Test darf durch Manifest/Service-Worker-Cache automatisch auf Release- oder GitHub-Dateien wechseln.

## REG-TABLET-001 - Tablet bleibt zweispaltig und folgt Golden Layout

- Symptom: Tablet-Layout wirkt gequetscht, Seitenmenue ist halb sichtbar oder die Plan-/Datenbankbereiche ueberlappen.
- Fix-Regel: Tablet ab `760px`; leerer Plan mit offener Sidebar, aktiver Plan mit geschlossener Sidebar, manuelles Oeffnen/Schliessen bleibt jederzeit moeglich.
- Testfall: `800x1280`, `1280x800` und `900x700`; links Datenbank/A-Z, rechts Planbereich, keine Ueberdeckung durch Historie/Pakete/Fertig.
- Tabu: Tablet-Fixes duerfen nicht die Handy-UI als Ersatzlayout erzwingen.

## REG-PHONE-001 - Handy-UI darf nicht flackern oder abgeschnitten werden

- Symptom: Scroll-Leiste/A-Z-Leiste wird abgeschnitten, Planbox flackert oder Bedienelemente verschwinden in Safe-Area/Keyboard.
- Fix-Regel: Handy-Layout bekommt eigene Scroll-/Safe-Area-Grenzen; waehrend Scroll/Touch keine unnoetigen Height-Spruenge oder Layoutanimationen.
- Testfall: `390x844`; mehrere Plan-Karten, Datenbank/A-Z und Editor oeffnen; keine abgeschnittene Leiste und keine springende Planbox.
- Tabu: Tablet-CSS darf keine Handy-Side-Effekte erzeugen.

## REG-PLAN-001 - Zahnrad muss die richtige Plan-Uebung oeffnen

- Symptom: Bei mehreren Plan-Karten oeffnet ein Zahnrad die falsche Uebung.
- Fix-Regel: Plan-Karten-Buttons muessen mindestens per stabiler `localId` und Index-Fallback an genau die gerenderte Karte gebunden werden.
- Testfall: Drei bis fuenf Uebungen erzeugen; Zahnrad bei Karte 1, 2, 3 und letzter Karte oeffnet jeweils den passenden Namen.
- Tabu: Nicht per sichtbarem Text oder DOM-Position allein binden, wenn stabile IDs verfuegbar sind.

## REG-AZ-001 - A-Z-Leiste bleibt sichtbar und tippbar

- Symptom: A-Z-Leiste kollabiert, wird zu schmal, zu hoch gestaucht oder verschwindet neben der Uebungsdatenbank.
- Fix-Regel: A-Z ist eine kompakte vertikale Schnellleiste mit stabiler Mindestbreite und Touch-Zielen; Scrub/Touch darf nicht durch Flex-Shrink oder Zoom kollabieren.
- Testfall: Leere Suche und Suchtrefferliste auf Handy und Tablet; A-Z bleibt sichtbar, scrollbar/scrubbable und ueberdeckt keine Bank-Zeilen.
- Tabu: Keine grossen Touch-Ziele erzwingen, die bei kleiner Hoehe die gesamte Bankkarte sprengen.

## REG-PHONE-002 - Sichtbarer Bank-Button muss nach Scroll oeffnen

- Symptom: Im Handy-Layout ist der Button `Uebungsdatenbank oeffnen` sichtbar, ein Tap wird aber vom Scroll-/Touch-Guard verschluckt und die Datenbank bleibt geschlossen.
- Fix-Regel: Wenn der Phone-Scroll-Guard einen echten Tap auf dem Bank-Button abfaengt, muss die Bank nach kurzer Beruhigungszeit trotzdem kontrolliert oeffnen.
- Testfall: `390x844`, mehrere Plan-Karten, zur Bank scrollen, `Uebungsdatenbank oeffnen` tippen; `#bankArea.bankOpen`, `.bankRows` und A-Z-Leiste erscheinen.
- Tabu: Nicht den Scroll-Guard global deaktivieren; nur den sichtbaren Bank-Button gezielt nachfassen.

## REG-PARSER-001 - QR-/Satzblock-Schreibweisen bleiben eine saubere Planstruktur

- Symptom: Mehrzeilige QR-/Scan-Texte wie `Rudern — Tag 2` mit `1. Satz: 45 kg @ 15 Wdh` oder `Typ: qr` mit mehreren Uebungen werden als falsche Einzelsegmente oder Namen mit Satzdaten importiert.
- Fix-Regel: Strukturierte Satzbloecke werden vor dem normalen Komma-/Zeilensplit erkannt; Uebungsnamen werden von Nummern und `Tag N` bereinigt; Satzzeilen akzeptieren `Satz 1`, `1. Satz`, `12 Wdh @ 40 kg` und `45 kg @ 15 Wdh`.
- Testfall: `Rudern — Tag 2` ergibt 1 Karte `Rudern` mit 3 Saetzen und Schmerz; nummerierter und unnummerierter `Typ: qr`-Block ergibt 7 Karten mit korrekten kg/Wdh-Satzwerten.
- Tabu: Satzzeilen nicht mehr ueber `scanResultToApplyText` zu einer Komma-Liste eindampfen, wenn strukturierte Sets vorhanden sind.
