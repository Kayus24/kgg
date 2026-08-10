# KGG Source Chunk 002

- Source: `kgg-update/src` modular source
- Lines: 841-1260

```html
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
      "type": "local-html-patch",
      "title": "Lokale Test-Batterien und Satz-Textblock-Erkennung",
      "reason": "Mobile-Inbox, Sync und Terminheld-/Satz-Textbloecke brauchen wiederholbare lokale Checks; rohe Satzzeilen duerfen keine eigenen Uebungskarten erzeugen.",
      "whatChanged": [
        "Erkennt strukturierte Textbloecke aus Uebungsname plus Satz 1/2/3 vor dem normalen Komma-/Zeilen-Split.",
        "Satz-Zeilen werden als Werte gelesen und nicht als eigene Uebungen angelegt.",
        "Lokale Test-Batterien pruefen Mobile-Inbox-Dry-run, Sync-Safe-Logik und Textblock-Erkennung."
      ],
      "touchedAreas": [
        "Textblock parser",
        "Release pipeline tests",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Plan-State",
        "Storage",
        "Exercise database"
      ]
    },
    {
      "versionCode": 32,
      "versionName": "1.0.32-no-boot-redirect",
      "patchId": "kgg-v032-no-boot-redirect",
      "status": "active",
      "type": "local-html-patch",
      "title": "Keine automatische Release-Navigation beim Start",
      "reason": "ChatGPT-/Android-Datei-Viewer werden verlassen, wenn die HTML beim Booten per location.replace auf GitHub-Pages navigiert.",
      "whatChanged": [
        "Remote-Web-Updates werden nur noch als sichtbarer manueller Update-Hinweis angeboten.",
        "Der alte Auto-Apply-Hook bleibt kompatibel vorhanden, navigiert aber nicht mehr automatisch.",
        "Explizite Buttons in der Update-Zentrale duerfen externe Links weiterhin bewusst oeffnen."
      ],
      "touchedAreas": [
        "GitHub/Web-Update-Pruefung",
        "Boot-Navigation",
        "HTML embedded metadata"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Plan-State",
        "Exercise database",
        "Phone drag UI"
      ]
    },
    {
      "versionCode": 31,
      "versionName": "1.0.31-phone-drag-mobile-inbox",
      "patchId": "kgg-v014-phone-viewport-state-release-guard",
      "status": "active",
      "type": "local-html-patch",
      "title": "Phone-Viewport-State-Leak-Guard und Update-Zentrale lokal stabilisiert",
      "reason": "Phone-only Touch/Layout-State konnte nach Resize/Orientation in Tablet/Querformat weiterwirken; lokale content/file Tests sollten keinen GitHub-Auto-Redirect auslösen und die Update-Zentrale braucht ohne native Bridge einen Fallback.",
      "whatChanged": [
        "Adds a final phone viewport leak guard that removes stale kggPlanCardReordering, kggPlanCardSwiping, kggPlanSectionFrozen, is-scrolling, phoneTextFocus and kggPhoneDrawerOpen classes after gesture end and when leaving phone viewport.",
        "Cleans leaked inline drag/swipe styles on plan cards and restores #planList position when a phone drag is cancelled by resize/orientation.",
        "Keeps phone drag-reorder anchored to #planList local absolute coordinates instead of viewport fixed positioning.",
        "Keeps existing local content/file no-auto-redirect logic while preserving the normal update prompt.",
        "Keeps existing KGGReleaseControl local fallback before kgg-release-center-v28-script and does not overwrite a native bridge."
      ],
      "touchedAreas": [
        "Phone viewport state cleanup",
        "Plan-card drag/reorder UI guard",
        "HTML embedded metadata",
        "Source Truth",
        "Changelog"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Plan-State",
        "Storage",
        "Exercise database"
      ],
      "testStatus": {
        "phoneDragAnchoredToFinger": "code-inspected",
        "phoneStateCleanupOnGestureEnd": "code-inspected",
        "tabletLayoutNoGlobalContainerOverride": "code-inspected",
        "localContentNoAutoRedirect": "code-inspected",
        "releaseCenterFallbackBeforeV28": "code-inspected"
      },
      "createdAt": "2026-06-23T00:00:00+02:00"
    },
    {
      "versionCode": 24,
      "versionName": "1.0.24-rollback-v023-debug-breakage",
      "patchId": "kgg-v024-rollback-v023-debug-breakage",
      "status": "active",
      "type": "github-web-update",
      "title": "Rollback v023 Debug-Layout-Bruch",
      "reason": "v023 machte den Debug-Floating-Button sichtbar, brach aber erneut das Tablet-Layout und zeigte doppelte Debug-Einstiege.",
      "whatChanged": [
        "Removes active v023 debug style/script block.",
        "Removes active v022 debug style/script block if still present.",
        "Adds a small rollback guard that hides leftover debug buttons/overlays.",
        "Leaves the workflow indexUrl fix in place.",
        "Does not change PDF, QR generation, patient app, scan camera, parser, plan state or storage."
      ],
      "touchedAreas": [
        "Admin debug UI rollback",
        "HTML embedded metadata",
        "Source Truth",
        "Changelog",
        "Patch rules"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Tablet-Core-Layout",
        "Plan-State",
        "Storage"
      ],
      "testStatus": {
        "tabletLayoutRestored": "pending",
        "debugButtonsHidden": "pending",
        "versionIndexUrl": "pending"
      },
      "createdAt": "2026-06-21T00:56:01.513302+00:00"
    },
    {
      "versionCode": 23,
      "versionName": "1.0.23-admin-debug-visible-hotfix",
      "patchId": "kgg-v023-admin-debug-visible-hotfix",
      "status": "active",
      "type": "github-web-update",
      "title": "Admin Debug sichtbar Hotfix",
      "reason": "v022 aktualisierte Version/Metadaten, aber der sichtbare Debug-Einstieg erschien in der Tablet-UI nicht zuverlässig.",
      "whatChanged": [
        "Adds always-visible Admin Debug floating button independent of .adminMode.",
        "Keeps KGG_ADMIN_DEBUG_MENU.report() available for future agents.",
        "Repairs active kgg-source-truth insertion when older source-truth text is trapped inside an HTML comment.",
        "Does not change PDF, QR generation, patient app, scan camera, parser, plan state or storage."
      ],
      "touchedAreas": [
        "Admin debug UI",
        "HTML embedded metadata",
        "Source Truth",
        "Changelog",
        "Patch rules"
```
