# KGG Source Chunk 001

- Source: `kgg-update/index.html`
- Lines: 421-840

```html
        "androidApp": "not-applicable"
      },
      "handoffNote": "v053 ist Web-UI-only: nach jedem Folgepatch phone-scan-dock, phone-admin-menu, tablet-card-reorder und tablet-editor-layout laufen lassen."
    },
    {
      "versionCode": 52,
      "versionName": "1.0.52-pdf-plan-thumbnails",
      "patchId": "kgg-v052-pdf-plan-thumbnails",
      "status": "active",
      "type": "local-html-patch",
      "title": "PDF-Planbilder in Trainingskarten",
      "reason": "PDF-Trainingskarten sollen vorhandene lokale Uebungsbilder oben rechts als kleine Schwarzweiss-Thumbnails zeigen, ohne die Kartenhoehe zu veraendern.",
      "whatChanged": [
        "PDF-Snapshot sammelt lokale Uebungsbilder aus IndexedDB und laesst fehlende Bilder still aus.",
        "Thumbnails werden lokal entschluesselt, verkleinert und in Schwarzweiss als JPEG-DataURL in den PDF-Snapshot gelegt.",
        "drawKggExerciseBox zeichnet das Thumbnail oben rechts im vorhandenen freien Raum.",
        "Die Offline-PDF-Runtime kann JPEG-XObjects einbetten."
      ],
      "touchedAreas": [
        "PDF snapshot",
        "PDF exercise card rendering",
        "Offline PDF runtime",
        "PDF test battery",
        "Source Truth",
        "version.json"
      ],
      "notTouched": [
        "Parser",
        "Scan/OCR parser",
        "Plan-State",
        "Phone card gestures",
        "Tablet layout content",
        "QR/Patienten-App",
        "Android/APK",
        "Sync data model",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "not-applicable"
      },
      "handoffNote": "v052 ist nur PDF-Planbilder; Android v399 und QR-Druck bleiben aus v051."
    },
    {
      "versionCode": 51,
      "versionName": "1.0.51-android-qr-pdf-bridge",
      "patchId": "kgg-v051-android-qr-pdf-bridge",
      "status": "active",
      "type": "local-html-patch",
      "title": "Kolleg:innen-QR drucken und Android-PDF/Icon-Bridge",
      "reason": "Kolleg:innen-App/APK-QR soll direkt druckbar sein und die Android-APK braucht v399 mit App-Icon sowie internem PDF-Fallback, wenn kein externer PDF-Viewer vorhanden ist.",
      "whatChanged": [
        "Das Admin-QR-Modal bekommt den Button QR drucken.",
        "QR-Druck erzeugt lokal eine kleine PDF-Seite mit Titel, QR-Code und Link.",
        "Android v399 stellt die native PDF-Bridge kompatibel bereit und bekommt das KGG-Launcher-Icon.",
        "Android oeffnet PDFs intern als Vorschau, wenn kein externer PDF-Viewer gefunden wird."
      ],
      "touchedAreas": [
        "Admin QR modal",
        "QR print PDF helper",
        "Android wrapper PDF bridge",
        "Android launcher resources",
        "Android update manifest",
        "Release artifacts",
        "Source Truth",
        "version.json"
      ],
      "notTouched": [
        "Parser",
        "Scan/OCR parser",
        "Plan-State",
        "Phone card gestures",
        "Tablet layout content",
        "PDF plan exercise-image thumbnails",
        "Sync data model",
        "API-Key-Logik"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "v051 ist QR/PDF/Android-Shell; PDF-Planbilder bleiben separat fuer v052."
    },
    {
      "versionCode": 50,
      "versionName": "1.0.50-phone-ui-mini-fix",
      "patchId": "kgg-v050-phone-ui-mini-fix",
      "status": "active",
      "type": "local-html-patch",
      "title": "Phone-UI: Plan-Menue, Historie und Scan-Optionen",
      "reason": "Im Phone-Planmodus sass das 3-Punkte-Menue zu mittig, Plan-Historie kollabierte und die Foto/Galerie-Auswahl wirkte wie ein separates Floating-Menue.",
      "whatChanged": [
        "Das 3-Punkte-Menue wird im Plan-Header oben rechts verankert.",
        "Plan-Historie bleibt im Phone-Planmodus als voller lesbarer Button sichtbar.",
        "Der Scanbutton zeigt Foto/Galerie-Optionen inline und waechst beim Oeffnen nur vertikal."
      ],
      "touchedAreas": [
        "Phone plan header menu",
        "Phone Plan-Historie button",
        "Phone scan dock photo options",
        "UI stability tests",
        "Source Truth",
        "version.json"
      ],
      "notTouched": [
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
        "androidApp": "not-applicable"
      },
      "handoffNote": "v050 ist UI-only fuer Phone; bei Problemen zuerst ui-stability phone-scan-dock und phone-history-packages laufen lassen."
    },
    {
      "versionCode": 50,
      "versionName": "1.0.50-phone-ui-mini-fix",
      "patchId": "kgg-v049-symbol-encoding-hotfix",
      "status": "active",
      "type": "local-html-patch",
      "title": "Mojibake-Symbolreste repariert",
      "reason": "Nach der grossen UTF-8-Reparatur waren noch kaputte Symbolsequenzen wie Pfeile, Zahnrad und QR-ASCII-Blockzeichen sichtbar bzw. im HTML enthalten.",
      "whatChanged": [
        "Kaputte Pfeil-, Zahnrad-, Caret- und QR-ASCII-Symbolstrings wurden durch echte Unicode-Zeichen ersetzt.",
        "Der Encoding-Guard erkennt jetzt auch einfache sichtbare Mojibake-Symbolfamilien.",
        "Die Encoding-Guard-Unit-Tests enthalten gute Unicode-Zeichen und rote Symbol-Mojibake-Faelle."
      ],
      "touchedAreas": [
        "HTML symbol strings",
        "QR helper embedded strings",
        "Critical encoding guard",
        "Local test batteries",
        "Source Truth",
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
```
