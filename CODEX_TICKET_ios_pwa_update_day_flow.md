# Codex Ticket: iOS PWA / Favoriten / Update- und Tageswechsel-Probleme

## Problem
Bei iOS-Patient:innen gibt es mehrere zusammenhängende Probleme:

1. Viele können die Web-App nicht sauber zum Home Screen hinzufügen.
2. Sie speichern den Plan stattdessen als Safari-Favorit/Bookmark.
3. Beim Öffnen über Favoriten wird oft zuerst eine alte Version aus Safari/Service-Worker-Cache geöffnet.
4. Die App aktualisiert sich erst verzögert.
5. Der aktuelle Trainingstag springt nicht zuverlässig automatisch auf den nächsten offenen Tag.
6. Patient:innen müssen über „Frühere Trainings“ selbst zurück zum aktuellen Tag.
7. Trainingstage darüber hinaus werden nicht automatisch angezeigt.

## Hinweise aus aktuellem Code

- `manifest.json` enthält nur ein SVG-Icon. Für iOS sollte zusätzlich ein PNG `apple-touch-icon` und Apple-Meta-Tags im HTML-Head vorhanden sein.
- `service-worker.js` cached `./index.html` und injiziert Module. Bei alten Safari/Favoriten/QR-Links kann zuerst altes HTML/alte SW-Version laufen.
- `next()` im Haupt-HTML berechnet den nächsten Tag nur aus `done`: `done.length ? max(done)+1 : 1`. Es gibt keine robuste tages-/datumsbasierte Fortschaltung.
- Trainingstage jenseits von `p.days` werden nur über `extendDays()` sichtbar, nicht automatisch beim Öffnen nach Ablauf/Erreichen des letzten Tages.

## Wahrscheinliche Ursachen

### A) iOS-Installation/Favoriten
- User öffnen aus Kamera/Safari/Favoriten statt echter Home-Screen-Web-App.
- iOS zeigt „Zum Home-Bildschirm“ nur zuverlässig über Safari Share Sheet, nicht aus jedem In-App-Browser/Kamera-Kontext.
- Fehlende Apple-spezifische Icons/Meta-Tags können die Installation weniger vertrauenswürdig/uneindeutig machen.

### B) Alte Version beim Öffnen
- Favorit zeigt auf denselben alten URL/Hash.
- Alte Service-Worker-Version kann beim ersten Öffnen noch `index.html`/Module aus Cache liefern.
- Update wird erst nach `activate`/zweitem Laden sichtbar.

### C) Tageswechsel
- Tageslogik ist nicht datumsbasiert.
- `restoreDay()` bevorzugt `lastOpenDay`, wenn dieser offen ist.
- Dadurch bleibt Patient:in auf altem offenen Tag hängen, statt automatisch auf heutigen/nächsten sinnvollen Tag zu springen.

### D) Weitere Trainingstage
- `extendBtn` ist manuell.
- Bei `extendDays=true` / `stepDays=6` sollte die App beim Erreichen des Endes automatisch weitere Tage anhängen oder klar fragen.

## Lösungsvorschläge

### Lösung 1: iOS-Installations- und Update-Schild
Kleiner Patch.

Dateien:
- `index.html`
- optional `apple-touch-icon.png`
- `patient-install-guide.js`
- `service-worker.js`

Änderungen:
- Apple-Meta-Tags ergänzen:
  - `apple-mobile-web-app-capable=yes`
  - `apple-mobile-web-app-title=KGG Plan`
  - `apple-mobile-web-app-status-bar-style=default`
  - `apple-touch-icon` als PNG, ideal 180x180
- In `patient-install-guide.js` iOS-Anleitung klarer:
  - „In Safari öffnen“
  - Teilen-Symbol
  - „Zum Home-Bildschirm“
- Wenn App nicht standalone läuft, prominenter Hinweis:
  - „Bitte nicht als Favorit speichern. Zum Home-Bildschirm hinzufügen.“

Risiko: niedrig.

### Lösung 2: Update-Gate nach Service-Worker-Aktivierung
Mittelgroßer Patch.

Dateien:
- `service-worker.js`
- neues kleines Modul `patient-update-gate.js`

Änderungen:
- SW sendet bereits `APP_UPDATE_READY`.
- Client soll darauf reagieren:
  - kleiner Banner „Neue Version verfügbar – jetzt neu laden“
  - Button lädt per `location.reload()` neu
- Bei sehr alter Version optional automatisches Reload nach kurzer Verzögerung, aber nur wenn keine Eingabe offen ist.
- Anzeige einer sichtbaren Versionsnummer im Debug/klein unten, damit man weiß, welche App-Version läuft.

Risiko: mittel, weil Auto-Reload keine Eingaben verlieren darf.

### Lösung 3: Tageslogik von „lastOpenDay“ entkoppeln
Wichtiger Patch.

Dateien:
- Haupt-HTML oder kleines Zusatzmodul `patient-day-auto-advance.js`
- ggf. `patient-day-history.js`

Änderungen:
- `restoreDay()` darf nicht dauerhaft auf altem `lastOpenDay` kleben.
- Beim App-Start berechnen:
  1. Wenn letzter Tag fertig: nächster Tag.
  2. Wenn heute ein neuer Kalendertag ist und letzter offener Tag alt ist: nächsten sinnvollen offenen Tag vorschlagen/setzen.
  3. Falls Patient bewusst früheren Tag öffnet, nur temporär speichern, nicht als dauerhaften Starttag.
- Speichern von `lastSeenDate` / `lastAutoDayDate` in `mk()`.
- Button/Info: „Heute: Tag X“.

Risiko: mittel, weil Patient:innen alte Tage weiter öffnen können müssen.

### Lösung 4: Automatisches Erweitern der Trainingstage
Kleiner bis mittlerer Patch.

Dateien:
- Haupt-HTML oder Zusatzmodul `patient-auto-extend-days.js`

Änderungen:
- Wenn `p.extendDays === true` und der nächste Tag > `p.days`:
  - automatisch `p.days += stepDays || 6`
  - Plan speichern
  - Status: „Weitere Trainingstage wurden hinzugefügt.“
- Wenn `extendDays` nicht gesetzt ist:
  - Button sichtbar lassen, aber klarer beschriften.

Risiko: niedrig bis mittel.

### Lösung 5: Favoriten-Rettungsmodus
Kleiner Zusatzpatch.

Dateien:
- neues Modul `patient-bookmark-recovery.js`

Änderungen:
- Wenn App in Safari nicht standalone und iOS erkannt:
  - Hinweis oberhalb des Plans:
    „Du öffnest den Plan als Favorit. Updates und Offline-Funktion sind zuverlässiger über Home-Bildschirm.“
- Zusätzlich Button:
  - „Aktuelle Version neu laden“
  - setzt `location.href` auf kanonische URL ohne alten Hash, wenn Plan bereits lokal gespeichert ist.

Risiko: niedrig.

## Empfehlung Reihenfolge

1. Lösung 1: iOS-Installationsfähigkeit verbessern.
2. Lösung 2: Update-Gate sichtbar machen.
3. Lösung 3: Tages-Auto-Advance reparieren.
4. Lösung 4: Auto-Extend der Trainingstage.
5. Lösung 5: Favoriten-Rettungsmodus.

## Nicht anfassen
- PDF
- QR-Erzeugung, außer später für kanonische Links nötig
- Scan/OCR
- Parser
- Übungsdatenbank
- Numpad-UI
