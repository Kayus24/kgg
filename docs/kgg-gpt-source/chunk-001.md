# KGG Source Chunk 001

- Source: `kgg-update/index.html`
- Lines: 421-840

```html
        "version.json"
      ],
      "notTouched": [
        "Layout",
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "Sync",
        "API-Key-Logik",
        "Kolleg:innen-Freigabe"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v049 ist ein enger Encoding-Hotfix gegen sichtbare Symbol-Mojibake-Reste; wenn dieser Guard rot wird, nicht releasen."
    },
    {
      "versionCode": 47,
      "versionName": "1.0.47-phone-landscape-tablet-menu",
      "patchId": "kgg-v047-phone-landscape-tablet-menu",
      "status": "active",
      "type": "local-html-patch",
      "title": "Handy-Landscape nutzt Tablet-Menue",
      "reason": "Wenn das Handy quer gehalten wird, soll die App als kleine Tablet-Arbeitsflaeche mit Tablet-Menue nutzbar sein; Portrait bleibt Handy-UI.",
      "whatChanged": [
        "Ein frueher Viewport-Schalter setzt nur in flacher Landscape-Ansicht virtuell width=760.",
        "Die zentrale Layout-Erkennung behandelt diesen Landscape-Modus als Tablet-Layout.",
        "Aktive Phone-Dock-/Drawer-Patches werden in diesem Landscape-Tablet-Modus nicht installiert."
      ],
      "touchedAreas": [
        "Early viewport switching",
        "Phone landscape tablet menu",
        "Layout mode detection",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "Sync",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v047 ist ein Landscape-Viewport-Hotfix: Handy-Portrait bleibt Phone-UI, Handy-Landscape soll Tablet-Menue und Tablet-Arbeitsflaeche zeigen."
    },
    {
      "versionCode": 46,
      "versionName": "1.0.46-tablet-runtime-viewport-guard",
      "patchId": "kgg-v046-tablet-runtime-viewport-guard",
      "status": "active",
      "type": "local-html-patch",
      "title": "Tablet-Boot und Split-Screen-Phone-UI getrennt",
      "reason": "Phone-only Runtime-Patches duerfen den breiten Tablet-Boot nicht blockieren, muessen aber im schmalen Tablet-Split-Screen weiter aktiv bleiben.",
      "whatChanged": [
        "v041/v042 installieren Phone-Menues, Scan-Dock-Umbauten und Observer nur noch bei Viewports unter 760px.",
        "Beim Wechsel zur breiten Tablet-Ansicht werden Phone-Klassen, Phone-Menues und der umgebaute Scanbutton sauber zurueckgesetzt.",
        "Die UI-Testbatterie prueft echten Tablet-App-Boot und einen Tablet-Split-Screen-Phone-Layout-Fall."
      ],
      "touchedAreas": [
        "Phone viewport runtime gates",
        "Tablet boot runtime safety",
        "Tablet split-screen phone layout",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "Tablet layout CSS",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v046 ist ein Runtime-Gate-Hotfix: breite Tablets bleiben Tablet-UI, schmale Split-Screen-Viewports bekommen weiter die Phone-UI."
    },
    {
      "versionCode": 45,
      "versionName": "1.0.45-phone-drawer-bank-align",
      "patchId": "kgg-v045-phone-drawer-bank-align",
      "status": "active",
      "type": "local-html-patch",
      "title": "Handy-Drawer und Datenbank-Ausrichtung stabilisiert",
      "reason": "Plan-Historie und Uebungspakete duerfen beim Antippen nicht haengen; die geoeffnete Uebungsdatenbank soll sauber oberhalb des festen Plan-scannen-Docks enden.",
      "whatChanged": [
        "Plan-Historie und Uebungspakete nutzen im Phone-Modus einen finalen Safe-Click-Handler ohne Render- oder Tablet-Overlay-Nebenwirkung.",
        "Das neue Planfenster bekommt im Phone-Modus mehr oberen Abstand.",
        "Beim Oeffnen der Uebungsdatenbank wird die Ansicht nach dem Rendern so ausgerichtet, dass das Bank-Ende knapp oberhalb des Scan-Docks liegt.",
        "Die UI-Testbatterie prueft jetzt echte Klicks auf Plan-Historie/Uebungspakete und die Datenbank-Ausrichtung."
      ],
      "touchedAreas": [
        "Phone Plan-Historie drawer",
        "Phone Uebungspakete drawer",
        "Phone exercise-bank scroll alignment",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "Tablet layout",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v045 ist ein Phone-only Safety-Patch nach v044; er ersetzt keine Tablet-, Parser-, Sync- oder APK-Logik."
    },
    {
      "versionCode": 44,
      "versionName": "1.0.44-phone-liquid-actions",
      "patchId": "kgg-v044-phone-liquid-actions",
      "status": "active",
      "type": "local-html-patch",
      "title": "Handy-Aktionen als staerkere Glass-Kapseln",
      "reason": "Plan scannen und Fertig sollen optisch konsistent als staerkere Liquid-Glass-Aktionen erscheinen; das Phone-Admin-Menue soll ohne verschachtelte Umwege zur Update-Zentrale fuehren.",
      "whatChanged": [
        "Plan scannen bekommt eine helle Glass-Kapsel mit Label, Trennlinie und Chevron.",
        "Fertig nutzt im Phone-Planmodus denselben Glass-Stil.",
        "Plan-Historie bleibt im Phone-Planmodus lesbar und kollabiert nicht auf Icon-Breite.",
        "Das Phone-Admin-Menue wird in Update, Sync & Weitergeben und Admin gegliedert."
      ],
      "touchedAreas": [
        "Phone scan dock",
        "Phone finish action",
        "Phone admin submenu",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "Tablet layout",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v044 ist ein Phone-only UI-Aufraeumpatch auf Basis von v041/v042; Kamera-/Galerie-, Sync- und Update-Handler werden wiederverwendet."
    },
    {
      "versionCode": 43,
      "versionName": "1.0.43-tablet-card-reorder",
      "patchId": "kgg-v043-tablet-card-reorder",
      "status": "active",
      "type": "local-html-patch",
      "title": "Tablet-Karten direkt verschieben",
      "reason": "Im Tablet-Modus sollen Uebungskarten per Longpress auf der Karte verschiebbar sein, nicht nur ueber den linken Verschiebegriff.",
      "whatChanged": [
        "Tablet-Karten erhalten einen eigenen Longpress-Einstieg in die bestehende Reorder-Geste.",
        "Buttons, Eingabefelder, Links, Karten-Actions und der linke Verschiebegriff bleiben von der Kartenflaechen-Geste ausgenommen.",
        "Der vorhandene animierte Reorder-Pfad erkennt nun Griff- und Karten-Starts sauber ueber dieselbe Funktion.",
        "Static-Smokes pruefen die Tablet-only-Bindung und die interaktiven Zielausnahmen."
      ],
      "touchedAreas": [
        "Tablet plan-card reorder gesture",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v043 nutzt weiterhin den bestehenden animated reorder; nur Tablet-Kartenflaechen werden als zusaetzlicher Startbereich gebunden."
    },
    {
      "versionCode": 42,
      "versionName": "1.0.42-phone-dock-anchored-correction",
      "patchId": "kgg-v042-phone-dock-anchored-correction",
      "status": "active",
      "type": "local-html-patch",
      "title": "Handy-Dock korrigieren",
      "reason": "Der Foto-Pfeil gehoert in den Kamera-Button, das Admin-Menue soll in der UI verankert sein und Scan/Fertig duerfen Floating-Fenster nicht ueberdecken.",
      "whatChanged": [
        "Foto-Optionen werden als Pfeilbereich direkt im Plan-scannen-Button geoeffnet.",
        "Das Handy-Admin-Menue sitzt im Plan-Header statt fixed oben rechts.",
        "Plan scannen und Fertig erhalten eine dezente Glasoptik und bleiben z-index-seitig unter Drawern und Modals.",
        "Browser-Smokes pruefen Admin-Verankerung, integrierten Foto-Pfeil, Glasstil und Floating-Layer-Reihenfolge."
      ],
      "touchedAreas": [
        "Phone scan dock",
        "Phone admin submenu",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v042 korrigiert nur die v041-Handy-Dock-UI; bestehende Kamera/Galerie- und Fertig-Handler bleiben angebunden."
    },
    {
      "versionCode": 41,
      "versionName": "1.0.41-ui-mini-series",
      "patchId": "kgg-v041-ui-mini-series",
      "status": "active",
      "type": "local-html-patch",
      "title": "Kleine UI-Serie fuer Datenbank, Tablet und Handy",
      "reason": "Max sammelt kleine UI-Patches: Bildhinweise in der Uebungsdatenbank, reparierter Tablet-Layoutbutton und kompaktere Handy-Bedienung.",
      "whatChanged": [
        "Uebungsdatenbank-Zeilen zeigen bei vorhandenen Bildanhaengen eine kleine schwarz-weisse Vorschau oder einen neutralen Platzhalter.",
        "Layout anpassen auf Tablet oeffnet und schliesst das vorhandene Layout-Panel wieder sauber.",
        "Handy-Layout verschiebt Admin-Konfig, Uebungsdatenbank teilen und QR-Code teilen in ein kleines Menue oben rechts.",
        "Plan scannen schwebt auf Handy unten; Fertig kommt daneben dazu, sobald ein Plan Uebungen enthaelt.",
        "Der Foto-Dock bekommt ein kleines Dreieck mit Kamera- und Galerie-Auswahl."
      ],
      "touchedAreas": [
        "Exercise database cards",
        "Tablet layout menu",
        "Phone scan dock",
        "Phone admin submenu",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan/OCR parser",
        "Plan-State",
        "Android-Wrapper",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "UI-only patch auf kgg-update/index.html; bestehende Scan-, QR-, Medien- und Plan-State-Handler werden nur ueber vorhandene Buttons/Funktionen ausgeloest."
    },
    {
      "versionCode": 37,
      "versionName": "1.0.37-device-sync-menu",
      "patchId": "kgg-v037-device-sync-menu",
      "status": "active",
      "type": "local-html-patch",
      "title": "Geräte-Sync und App-Weitergabe trennen",
      "reason": "Therapeuten-App weitergeben soll nur die Kolleg:innen-App/APK teilen; Geräte-Daten-Sync braucht einen eigenen klaren Einstieg.",
      "whatChanged": [
        "Admin-Menü bekommt einen eigenen Button Geräte-Sync für Sync-Test, Sync-Datei speichern/importieren und Pairing.",
        "Therapeuten-App weitergeben öffnet direkt den Kolleg:innen-App/APK-QR statt Sync- oder API-Key-Optionen.",
        "Update-Zentrale bleibt Release/HTML/GitHub und wird nicht mit Geräte-Sync vermischt."
      ],
      "touchedAreas": [
        "Tablet admin menu",
        "Therapist app share QR",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Parser",
        "Plan-State"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "Im Tablet-Menü: Therapeuten-App weitergeben = Kolleg:innen-App/APK-QR; Admin > Geräte-Sync = Sync-Diagnose und Datei-Transfer."
    },
    {
      "versionCode": 36,
      "versionName": "1.0.36-native-sync-diagnostics",
      "patchId": "kgg-v036-native-sync-diagnostics",
      "status": "active",
      "type": "local-html-patch",
      "title": "Native Sync Diagnose und sichere Datei-Uebergabe",
      "reason": "Peer-to-Peer-Sync muss sichtbar machen, ob Android wirklich einen gemeinsamen Sync-Raum nutzt oder nur im privaten Rueckfall-Speicher schreibt.",
      "whatChanged": [
        "Sync-Dialog zeigt Modus, Raum, Peer-Anzahl, letzten Test und Sync-Pfad.",
        "Sync-Test schreibt/liest ueber die vorhandene Android-Bridge und meldet klare Ergebnisse.",
        "Sync-Datei speichern/importieren erlaubt einen sicheren manuellen Transfer fuer groessere Daten.",
        "Native-Sync-Testbatterie prueft Peer-Mesh, Auto-Download-Regeln, Self-Skip, Tombstones und Secret-Blockade."
      ],
      "touchedAreas": [
        "Sync diagnostics UI",
        "Safe sync file transfer",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Parser"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "Wenn der Sync-Dialog privaten Rueckfall-Speicher meldet, findet kein automatischer Geraete-Transfer statt; dann Sync-Datei exportieren/importieren oder Android-Dateizugriff pruefen."
    },
    {
      "versionCode": 35,
      "versionName": "1.0.35-parser-schmerz-tag-blocks",
      "patchId": "kgg-v035-parser-schmerz-tag-blocks",
      "status": "active",
      "type": "local-html-patch",
      "title": "Schmerz-/Tag-Textbloecke stabil erkennen",
      "reason": "Echte Trainingsblock-Texte enthalten Tag-Labels, Schmerzwerte und Satzzeilen wie 15 kg @ 12 Wdh; diese duerfen keine Satz-, Tag- oder Schmerz-Muellkarten erzeugen.",
      "whatChanged": [
        "Textfeld-Testbatterie enthaelt den echten Beinpresse/Kniebeuger/Singel-Leg/Romanian-Deadlift-Block.",
        "Satzzeilen mit Last vor Wiederholungen wie 15 kg @ 12 Wdh werden korrekt gelesen.",
        "Schmerz: n/10 und Tag 1 werden nicht mehr als Uebungskarten uebernommen."
      ],
      "touchedAreas": [
        "Textfield parser",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Storage"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "Regressionstest deckt den echten Schmerz-/Tag-Block ab und verhindert Satz-/Schmerz-Muellkarten."
    },
    {
      "versionCode": 34,
      "versionName": "1.0.34-free-textfield-units",
      "patchId": "kgg-v034-free-textfield-units",
      "status": "active",
      "type": "local-html-patch",
      "title": "Freie Einheiten im Textfeld weitergeben",
      "reason": "Textfeld-Eingaben koennen Einheiten enthalten, die noch nicht als feste App-Einheit hinterlegt sind; diese duerfen nicht still zu kg werden und muessen im aktuellen Plan erhalten bleiben.",
      "whatChanged": [
        "Textfeld-Testbatterie deckt bekannte App-Einheiten, freie Einheiten, Kurzformen und Satzvarianten ab.",
        "Freie Einheiten wie km/h, Grad, RPE, Level, cm und rpm bleiben in state.plan und KGGDataStore.currentPlan erhalten.",
        "S1, 1. Satz, 1) und Satz 1 - werden als Satzdaten erkannt, nicht als eigene Uebungskarten."
      ],
      "touchedAreas": [
        "Textfield parser",
        "Local test batteries",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Sync pipeline"
      ]
    },
    {
      "versionCode": 33,
      "versionName": "1.0.33-test-battery-textblocks",
      "patchId": "kgg-v033-test-battery-textblocks",
      "status": "active",
```
