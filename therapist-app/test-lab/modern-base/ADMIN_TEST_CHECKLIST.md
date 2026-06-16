# KGG Admin Modern Base - Test Checklist

## Ziel

Diese Datei testet die Admin-App als neue Hauptlinie auf Basis der alten v360/v366-HTML. Es geht zuerst um Kernstabilitaet, nicht um neue Features.

## Testdatei

- `KGG_APP_ADMIN_v390_v360_v366_modern_base_candidate.html`
- Basis: `therapist-app/releases/v366/web/KGG_APP_ADMIN_v366_mobile_floating_history_packages.html`
- Nur Test-Lab-Identity geaendert, keine Funktionslogik.

## Handy Kern-UI

- Admin-Datei ueber Test-Lab oeffnen.
- Mindestens 5 Uebungen in den Plan legen.
- Zahnrad bei Uebung 1, 3 und 5 oeffnen.
- Pruefen: Es oeffnet immer exakt die richtige Uebung.
- Drag am Griff testen: startet erst nach kurzem Halten.
- Swipe links/rechts testen: Karte bewegt sich sichtbar und loescht echt.
- Scrollen im Plan testen: keine springende Planbox, kein starkes Flackern.

## Einheiten / Editor

- Bestehende Einheiten pruefen: kg, BW, Stufe, Watt, keine.
- Notieren, ob freie Einheiten fehlen oder UI blockieren.
- Noch nicht als Fehler patchen, erst nach Zahnrad-Test.

## Parser-Test

Testtext spaeter fuer Parser-Patch:

```text
Rudern - Tag 2
1. Satz: 45 kg @ 15 Wdh
2. Satz: 45 kg @ 15 Wdh
3. Satz: 45 kg @ 15 Wdh
Schmerz: 2/10
```

Erwartung spaeter: eine Uebung `Rudern`, drei Satzwerte, Schmerz 2/10.

## Bilder / Patient-App

- Eine Test-Uebung mit Bild anlegen.
- Bild muss in der Plan-Karte sichtbar sein.
- Patient-App/QR oeffnen.
- Neu laden und pruefen, ob Bild erhalten bleibt.
- Wenn Bild verschwindet: Zeitpunkt notieren, z. B. sofort, nach Reload, nach App-Neustart.

## Tablet

- Tablet quer oeffnen.
- Sandwich-Menue oeffnen und schliessen.
- Schliessen per X, Backdrop und Escape testen, falls verfuegbar.
- A-Z-Leiste/Bank scrollen: Buchstaben duerfen nicht gequetscht oder unbedienbar sein.
- Plan-Actions duerfen Karten nicht ueberdecken.

## Entscheidung nach Test

- Wenn Kern-UI besser als v389 ist: Admin-v360/v366 wird Modernisierungsbasis.
- Wenn Zahnrad/Plan-Kern schon kaputt ist: zuerst diesen Kernpatch, keine Admin-/Tablet-Erweiterung.
- Wenn Tablet-Menue kaputt ist, aber Handy-Kern stabil: Tablet-Menue separat neu bauen.
