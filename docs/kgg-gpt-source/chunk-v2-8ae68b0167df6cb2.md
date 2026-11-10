
<!-- BEGIN kgg-changelog: embedded Changelog; READ THIS BEFORE PATCHING -->
<script type="application/json" id="kgg-changelog">
{
  "schema": 1,
  "latestVersionCode": 137,
  "entries": [
    {
      "versionCode": 137,
      "versionName": "1.0.137-tablet-two-slot-edge-taps",
      "patchId": "kgg-v137-tablet-two-slot-edge-taps",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Tablet-Zwei-Slot Rand-Taps",
      "reason": "Scanner- und Fertig-Überlagerung an Paket-/Basis-Rändern im Tablet-Zwei-Slot-Pane ohne Button-Verlust verhindern.",
      "whatChanged": [
        "Scanner- und Fertig-Überlagerung an Paket-/Basis-Rändern im Tablet-Zwei-Slot-Pane ohne Button-Verlust verhindern."
      ],
      "touchedAreas": [
        "Tablet-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      }
    },
    {
      "versionCode": 136,
      "versionName": "1.0.136-tablet-scan-flow-collision",
      "patchId": "kgg-v136-tablet-scan-flow-collision",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Tablet-Scanner kollisionsfrei im Zwei-Slot-Pane",
      "reason": "Scanner im kompakten Tablet-Zwei-Slot-Pane vor dem Plan im Layoutfluss platzieren, damit Plan-, Paket- und Scanner-Taps frei bleiben.",
      "whatChanged": [
        "Scanner im kompakten Tablet-Zwei-Slot-Pane vor dem Plan im Layoutfluss platzieren, damit Plan-, Paket- und Scanner-Taps frei bleiben."
      ],
      "touchedAreas": [
        "Tablet-Cockpit-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      }
    },
    {
      "versionCode": 135,
      "versionName": "1.0.135-tablet-package-1024-tap",
      "patchId": "kgg-v135-tablet-package-1024-tap",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Tablet-Pakete bei 1024px bedienbar",
      "reason": "Tablet-Zwei-Slot-Scanbereich verdeckt den Pakete-Tap nicht mehr; Scanner bleibt bedienbar.",
      "whatChanged": [
        "Tablet-Zwei-Slot-Scanbereich verdeckt den Pakete-Tap nicht mehr; Scanner bleibt bedienbar."
      ],
      "touchedAreas": [
        "Tablet-Cockpit-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      }
    },
    {
      "versionCode": 134,
      "versionName": "1.0.134-cockpit-qr-explicit-import",
      "patchId": "kgg-v134-cockpit-qr-explicit-import",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Cockpit QR nur nach bewusster Uebernahme",
      "reason": "QR Scan darf Cockpit Slots nicht automatisch belegen; sichtbarer Import Button ist die einzige Uebernahmeaktion.",
      "whatChanged": [
        "QR Scan darf Cockpit Slots nicht automatisch belegen; sichtbarer Import Button ist die einzige Uebernahmeaktion."
      ],
      "touchedAreas": [
        "Cockpit",
        "Scan/OCR"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Nutzerauftrag 29.10. und Fortsetzung 04.11.2026; kein automatischer Import"
    },
    {
      "versionCode": 133,
      "versionName": "1.0.133-phone-dock-owner",
      "patchId": "kgg-v133-phone-dock-owner",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Phone Cockpit Dock Owner",
      "reason": "Phone-Button bleibt nach Resize und Cockpit-Wechsel im zentralen Dock und ueberdeckt Fertig nicht.",
      "whatChanged": [
        "Phone-Button bleibt nach Resize und Cockpit-Wechsel im zentralen Dock und ueberdeckt Fertig nicht."
      ],
      "touchedAreas": [
        "Handy-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Aktueller KGG-Auftrag: reproduzierter Dock-Fehler #355 muss behoben und getestet werden."
    },
    {
      "versionCode": 132,
      "versionName": "1.0.132-plan-card-space",
      "patchId": "kgg-v132-plan-card-space",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Mehr Platz fuer Uebungskarten",
      "reason": "Bild-Badge bei echter Miniatur ausblenden und Handy-X sowie Zahnrad rechts platzsparend mit getrennten Touchzielen ausrichten.",
      "whatChanged": [
        "Bild-Badge bei echter Miniatur ausblenden und Handy-X sowie Zahnrad rechts platzsparend mit getrennten Touchzielen ausrichten."
      ],
      "touchedAreas": [
        "Cockpit",
        "Handy-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Vom Nutzer am 28.10.2026 mit drei Tab-S9-Screenshots beauftragte UI-Nachbesserung; kein Release."
    },
    {
      "versionCode": 131,
      "versionName": "1.0.131-qr-cockpit-tablet-integrated",
      "patchId": "kgg-v131-qr-cockpit-link-fixes",
      "status": "implemented",
      "type": "module-patch",
      "title": "QR-Scantext, kompakte Cockpit-Links und stabiler Tablet-Split",
      "reason": "Kopierbare Scan- und Abschlussausgaben statt automatischer Cockpit-Oeffnung; installierte Admin-App soll verifizierte HTTPS-Links entgegennehmen.",
      "whatChanged": [
        "QR-Scan behaelt seine bisherige Ausgabe und haengt den Cockpit-Link am Ende an, ohne das Cockpit automatisch zu oeffnen.",
        "Abschlussausgabe enthaelt nur Uebungen/Saetze, optionale Notizen und am Schluss den komprimierten Cockpit-Link; Planquellenwarnungen erscheinen separat.",
        "Abwaertskompatibler Deflate-Codec fuer Cockpit-Links; Android-Manifest aktiviert autoVerify fuer exakt den bestehenden Deep-Link-Pfad.",
        "Uebernimmt den auf main integrierten v130-Tablet-Hoehenfix ohne die Cockpit-QR-Aenderungen zu verlieren."
      ],
      "touchedAreas": [
        "QR/Patienten-App",
        "Scan/OCR",
        "Plan-State",
        "Cockpit",
        "Android/APK"
      ],
      "notTouched": [
        "PDF",
        "Parser",
        "Medien/Upload",
        "API-Key-Logik",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "v130 QR/Cockpit und v130 Tablet separat PASS; gemeinsame v131-Integration NOT_RUN",
        "certification": "pending: neue gemeinsame v131-Regression und Android-App-Link-Geraeteabnahme"
      },
      "approvalNote": "Max beauftragt am 2026-10-27 KGG QR/Cockpit-Fixes und Android-App-Link-Verifikation samt fortlaufender Drive-Dokumentation; kein produktiver Merge/Release vor Abnahme."
    },
    {
      "versionCode": 130,
      "versionName": "1.0.130-plan-card-height-stability",
      "patchId": "kgg-v130-plan-card-height-stability",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Stabile Plan-Karten im Tablet-Split",
      "reason": "Verhindert hoehenbedingte Ueberlagerungen beim Ziehen der Tablet-Cockpit-Trennlinie; lesbare Namen und getrennte 44px-Aktionen bleiben erhalten.",
      "whatChanged": [
        "Verhindert hoehenbedingte Ueberlagerungen beim Ziehen der Tablet-Cockpit-Trennlinie; lesbare Namen und getrennte 44px-Aktionen bleiben erhalten."
      ],
      "touchedAreas": [
        "Cockpit",
        "Handy-Layout"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Vom Nutzer am 27.10.2026 ausdruecklich beauftragter UI-Fix; keine Release-Freigabe."
    },
    {
      "versionCode": 129,
      "versionName": "1.0.129-cockpit-qr-resume",
      "patchId": "kgg-v129-cockpit-qr-resume",
      "status": "implemented",
      "type": "module-patch",
      "title": "Cockpit-Link nach Patienten-QR mit manueller Prioritaet",
      "reason": "Patienten-QR erzeugt einen Cockpit-Link; Notizen und manuell bearbeitete Werte bleiben bei erneuten Scans erhalten.",
      "whatChanged": [
        "Patienten-QR erzeugt einen Cockpit-Link; Notizen und manuell bearbeitete Werte bleiben bei erneuten Scans erhalten."
      ],
      "touchedAreas": [
        "QR/Patienten-App",
        "Scan/OCR",
        "Plan-State",
        "Cockpit"
      ],
      "notTouched": [
        "PDF",
        "Parser",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "PASS: QR scan, portable/local resume, field priority, notes and failure recovery",
        "certification": "pending"
      },
      "approvalNote": "Max beauftragt am 2026-10-26 Cockpit-Aktivierungslink nach Patienten-QR und Vorrang eigener Eintraege bei erneutem Scan; nur lokale reversible Umsetzung, kein Release."
    },
    {
      "versionCode": 128,
      "versionName": "1.0.128-button-touch-responsiveness",
      "patchId": "kgg-v128-button-touch-responsiveness",
      "status": "implemented",
      "type": "module-patch",
      "title": "Direkte Touchreaktion fuer Buttons",
      "reason": "Buttons deklarieren touch-action:manipulation gegen verzoegerte Touch-Clicks; spezifische Scroll- und Ziehgesten sowie bestehende Handler bleiben erhalten.",
      "whatChanged": [
        "Die vorhandene globale button-Regel ergaenzt ausschliesslich touch-action:manipulation. Spezifischere none-/pan-Regeln, Click-/Tastaturhandler, Viewport und Layout bleiben unveraendert."
      ],
      "touchedAreas": [
        "UI"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "Physische A/B/A-Kontrolle auf dem isolierten v127-Kandidaten: 9/9 Close-Proben; touchend-bis-click in B 1.8-2.0 ms statt 137-210.1 ms in den A-Phasen. Pflichtpruefungen des v128-Artefakts noch ausstehend.",
        "certification": "pending"
      },
      "approvalNote": "Max 23.10.2026: am physischen Tablet weiter pruefen und verbessern. Enger, kausal kontrollierter CSS-Eingriff; kein Handler-, Viewport-, Layout-, Native-, Merge- oder Releasewechsel."
    },
    {
      "versionCode": 127,
      "versionName": "1.0.127-menu-sync-qr-responsiveness",
      "patchId": "kgg-v127-menu-sync-qr-responsiveness",
      "status": "implemented",
      "type": "module-patch",
      "title": "Reaktionssicheres Menue und schneller Sync-QR",
      "reason": "Das Menue verarbeitet einen Pointergestus genau einmal; der Sync-QR nutzt vorhandene SVG-Ausgabe statt pixelweiser GIF-Erzeugung. QR-Inhalt und Layout bleiben erhalten.",
      "whatChanged": [
        "Ein zusammengehoerender Pointerdruck und sein nachfolgender Click loesen nur eine Menueaktivierung aus; Tastatur- und Assistenzaktivierung bleiben erhalten.",
        "Der Sync-QR verwendet die SVG-Ausgabe der vorhandenen QR-Bibliothek, behaelt Matrix, Groesse, Rand und GIF-Legacyfallback.",
        "Tatsaechliche Pointergesten und die Pixeldekodierung der angezeigten QR-Grafik werden im vorhandenen UI-Testpfad geprueft."
      ],
      "touchedAreas": [
        "UI"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "Gezielte und abschliessende Nachweise am zugehoerigen PR/Commit; keine physische Geraeteabnahme behauptet.",
        "certification": "pending"
      },
      "approvalNote": "Max 23.10.2026: KGG-Arbeit fortsetzen und offene Performancebefunde abschliessen. Nur Sync-QR-Bilddarstellung und Menueeingabe; kein QR-Datenformat-/Layout-/Patienten-/Native-/Releasewechsel."
