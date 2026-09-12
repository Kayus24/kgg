
<!-- BEGIN kgg-changelog: embedded Changelog; READ THIS BEFORE PATCHING -->
<script type="application/json" id="kgg-changelog">
{
  "schema": 1,
  "latestVersionCode": 89,
  "entries": [
    {
      "versionCode": 89,
      "versionName": "1.0.89-changelog-archive-window-refresh",
      "patchId": "kgg-v089-changelog-archive-window-refresh",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Changelog-Archivfenster erweitert",
      "reason": "Vollständiger aktueller Changelog-Snapshot wird unveränderlich archiviert; im Laufzeitfenster bleiben die 15 neuesten Einträge.",
      "whatChanged": [
        "Vollständiger aktueller Changelog-Snapshot wird unveränderlich archiviert; im Laufzeitfenster bleiben die 15 neuesten Einträge."
      ],
      "touchedAreas": [
        "Changelog-Archivierung"
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
      "versionCode": 88,
      "versionName": "1.0.88-ticket-037-real-plan",
      "patchId": "kgg-v088-ticket-037-real-plan",
      "status": "candidate",
      "type": "module-patch",
      "title": "Therapie-Cockpit: normaler Plan direkt in Slot 1",
      "reason": "Der sichtbare Cockpit-Einstieg und der Fertig-Dialog übernehmen den zentralen aktuellen Plan über den bestehenden Plan-/Codec-/Importpfad; Fehler bleiben fail-closed.",
      "whatChanged": [
        "Der sichtbare #kggTherapyCockpitButton importiert den normalen aktuellen Plan.",
        "Der Fertig-Dialog enthält die verbindliche Cockpit-Plan-Aktion in der Reihenfolge PDF, App, Cockpit, Abbrechen.",
        "Blocking-Real-Plan-E2E und Negativtest sichern sichtbaren Klick, Slot 1 und den echten Fehlercode."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
        "Test-Harness",
        "Tablet-Fertig-Dialog"
      ],
      "notTouched": [
        "PDF-Core",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Medien/Upload",
        "Android/APK",
        "API-Key-Logik",
        "Phone-Design"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "KGG-TICKET-037; kein Main-, Live- oder Release-Auftrag."
    },
    {
      "versionCode": 87,
      "versionName": "1.0.87-ticket-015-live-fix",
      "patchId": "kgg-v087-ticket-015-live-fix",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Ticket 015 Live-Editor-Bridge",
      "reason": "Make the progression editor bridge robust and keep variant metadata out of patient info text.",
      "whatChanged": [
        "Make the progression editor bridge robust and keep variant metadata out of patient info text."
      ],
      "touchedAreas": [
        "Admin-Editor",
        "Patienten-App"
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
      "versionCode": 86,
      "versionName": "1.0.86-ticket-015-progressions-contract",
      "patchId": "kgg-v085-ticket-015-progressions",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Progressionsvarianten – Vertragsfix",
      "reason": "Der Progressionsvertrag wird releasefest ausgerichtet: painMode bleibt kompatibel, Auswahl/Medien werden sicher transportiert und Bank-Persistenz bleibt erhalten.",
      "whatChanged": [
        "Der Progressionsvertrag bleibt mit painMode kompatibel und transportiert Auswahl, Medien und Bank-Persistenz sicher."
      ],
      "touchedAreas": [
        "Plan-State",
        "QR/Patienten-App",
        "Handy-Layout"
      ],
      "notTouched": [
        "PDF",
        "Scan/OCR",
        "Parser",
        "Medien/Upload",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Ausdrücklicher Ausführungsauftrag KGG-TICKET-015; bestehende Nutzeranforderung für Variantenkette, QR und Patienten-Galerie."
    },
    {
      "versionCode": 84,
      "versionName": "1.0.84-therapy-cockpit-start-link",
      "patchId": "kgg-v084-therapy-cockpit-start-link",
      "status": "candidate",
      "type": "module-patch",
      "title": "Therapie-Cockpit Startlink",
      "reason": "Erzeugt aus einem bestehenden Therapeutenplan einen selbsttragenden Cockpit-Startlink mit kopierbarer Ausgabe.",
      "whatChanged": [
        "Erzeugt aus einem bestehenden Therapeutenplan einen selbsttragenden Cockpit-Startlink mit kopierbarer Ausgabe.",
        "Erreichbar über den leeren Cockpit-Zustand; die normale Therapeutenansicht bleibt unverändert."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
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
        "local": "pending",
        "certification": "pending"
      }
    },
    {
      "versionCode": 83,
      "versionName": "1.0.83-therapy-cockpit-id-guard",
      "patchId": "kgg-v083-therapy-cockpit-id-guard",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Therapie-Cockpit ID-Guard",
      "reason": "Weist unbekannte explizite Übungsbank-IDs vor dem Cockpit-Sync fail-closed ab.",
      "whatChanged": [
        "Weist unbekannte explizite Übungsbank-IDs vor dem Cockpit-Sync fail-closed ab."
      ],
      "touchedAreas": [
        "Therapie-Cockpit"
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
      "versionCode": 82,
      "versionName": "1.0.82-therapy-cockpit",
      "patchId": "kgg-v082-therapy-cockpit",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Therapie-Cockpit fuer begleitete Plaene",
      "reason": "Fuegt die additive Tablet-Cockpit-Ansicht mit selbsttragendem Linkcodec, drei RAM-Slots und Abschlussdokumentation hinzu.",
      "whatChanged": [
        "Fuegt die additive Tablet-Cockpit-Ansicht mit selbsttragendem Linkcodec, drei RAM-Slots und Abschlussdokumentation hinzu."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
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
        "local": "pending",
        "certification": "pending"
      }
    },
    {
      "versionCode": 81,
      "versionName": "1.0.81-qr-full-plan-device-ladder",
      "patchId": "kgg-v081-qr-full-plan-device-ladder",
      "status": "candidate",
      "type": "module-patch",
      "title": "Vollständige KGGH3-Plan-QRs und Geräte-Testleiter",
      "reason": "Komplette persönliche Pläne müssen von normalen Oppo-Ressourcen bis zu simulierten schwachen Geräten zuverlässig gelesen werden.",
      "whatChanged": [
        "Neue Plan-Ausgaben verwenden den lokalen, fest angehefteten KGGH3-Codec mit fflate 0.8.3 und Fehlerkorrektur M.",
        "KGGH2 bleibt lesbar; Query, Hash, iOS-Startlink und der interne QR-Scanner validieren beide Formate.",
        "Synthetische 1/3/7/12/20-Übungspläne werden über Decoder-, Parser-, Speicher- und Sichtbarkeits-Fingerabdrücke geprüft.",
        "Für Altgeräte gibt es zusätzlich einen kleinen QR nur für die öffentliche Patienten-App-Adresse; der persönliche KGGH3-Plan wird danach intern gelesen."
      ],
      "touchedAreas": [
        "QR/Patienten-App",
        "KGGH2/KGGH3",
        "Interner QR-Scanner",
        "Geräte-Testleiter"
      ],
      "notTouched": [
        "PDF",
        "Plan-State-Quelle",
        "Medien-/Upload-Logik",
        "API-Key-Logik",
        "Android/APK"
      ],
      "testStatus": {
        "local": "pending",
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "Vor einem echten Oppo-Test müssen die automatischen KGGH3-, Kamera-, Foto-Fallback- und Geräteprofile grün sein."
    },
    {
      "versionCode": 71,
      "versionName": "1.0.71-pdf-global-exercise-numbering",
      "patchId": "kgg-v071-pdf-global-exercise-numbering",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Fortlaufende Papierplan-Nummerierung",
      "reason": "Übungsnummern dürfen auf Folgeseiten nicht wieder bei EX1 beginnen.",
      "whatChanged": [
        "Verwendet den globalen Übungsindex für sichtbare Nummern, Maschinenzeilen und Seitenspannen.",
        "Ergänzt Regressionstests für klassische und große mehrseitige Papierpläne."
      ],
      "touchedAreas": [
        "PDF",
        "Papierplan-Nummerierung",
        "Regressionstests"
      ],
      "notTouched": [
        "QR/Patienten-App",
        "Scan/OCR",
        "Plan-State",
        "Storage",
        "Tablet-Layout",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Ticket 012: mehrseitige Papierpläne müssen über alle Seiten fortlaufend nummeriert werden."
    },
    {
      "versionCode": 70,
      "versionName": "1.0.70-tablet-package-save",
      "patchId": "kgg-v070-tablet-package-save",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Tablet-Paketbutton wiederherstellen",
      "reason": "Der bereits vorhandene Paket-Speichern-Dialog war in der Tablet-Ansicht nicht sichtbar bzw. erreichbar.",
      "whatChanged": [
        "Verschiebt ausschließlich den bestehenden savePackageBtn im Tablet-Modus in die Kopfzeile des aktuellen Plans und lässt den vorhandenen Dialog-Handler unverändert.",
        "Sichert für diesen Tablet-Button ein Touch-Ziel von mindestens 56 x 44 px."
      ],
      "touchedAreas": [
        "Tablet-Layout",
        "UI-Regressionstests"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Storage",
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
      "approvalNote": "Max hat die Wiederherstellung des Tablet-Paketbuttons und ein mindestens 44px hohes Tablet-Touch-Ziel ausdrücklich freigegeben."
    },
    {
      "versionCode": 69,
      "versionName": "1.0.69-plan-text-recovery-finalize",
      "patchId": "kgg-v069-plan-text-recovery-finalize",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Live-Plantext Recovery abschliessen",
      "reason": "Persistiert eine tatsaechliche Boot-Reparatur und unterscheidet kurze Zwischenedits von finalen Umbenennungen.",
      "whatChanged": [
        "Persistiert eine tatsaechliche Boot-Reparatur und unterscheidet kurze Zwischenedits von finalen Umbenennungen."
      ],
      "touchedAreas": [
        "Plan-State",
        "Storage"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
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
      "approvalNote": "Vom Code-Review beauftragter P1-Folgepatch: Live-Text-Plan-State und lokale Persistenz muessen ohne Datenverlust korrigiert werden."
    },
    {
      "versionCode": 68,
      "versionName": "1.0.68-plan-text-boot-restore",
      "patchId": "kgg-v068-plan-text-boot-restore",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Plan-Text Boot Restore",
      "reason": "Stellt gueltigen gespeicherten Live-Plantext beim Start wieder her und schuetzt nur kurz unvollstaendige Namenssegmente.",
      "whatChanged": [
        "Stellt gueltigen gespeicherten Live-Plantext beim Start wieder her und schuetzt nur kurz unvollstaendige Namenssegmente."
      ],
      "touchedAreas": [
        "Parser",
        "Plan-State"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
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
      "approvalNote": "Expliziter P0-Folgefix: Textfeld bleibt Live-Master, bestehende Mehruebungsplaene duerfen beim Boot oder bei Teilbearbeitung nicht verloren gehen."
    },
    {
      "versionCode": 67,
      "versionName": "1.0.67-plan-text-live-master-guard",
      "patchId": "kgg-v067-plan-text-live-master-guard",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Plan-Text Live-Master Schutz",
      "reason": "Schuetzt Mehruebungsplaene bei strukturierter Texteingabe vor einer destruktiven Reduktion.",
      "whatChanged": [
        "Schuetzt Mehruebungsplaene bei strukturierter Texteingabe vor einer destruktiven Reduktion."
      ],
      "touchedAreas": [
        "Parser",
        "Plan-State"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
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
      "approvalNote": "Max hat den P0 Parser- und Plan-State-Fix ausdruecklich beauftragt."
    },
    {
      "versionCode": 65,
      "versionName": "1.0.65-source-control-char-guard",
      "patchId": "kgg-v065-source-control-char-guard",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Source-Steuerzeichen-Guard",
      "reason": "Ersetzt vier versehentliche U+0008-Zeichen durch Regex-Wortgrenzen, repariert den fehlkodierten SJIS-Prüfwert und blockiert C0-, C1- sowie DEL-Steuerzeichen in editierbaren Source-Teilen.",
      "whatChanged": [
        "Ersetzt vier versehentliche U+0008-Zeichen durch Regex-Wortgrenzen, repariert den fehlkodierten SJIS-Prüfwert und blockiert C0-, C1- sowie DEL-Steuerzeichen in editierbaren Source-Teilen."
      ],
      "touchedAreas": [
        "Parser"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
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
      "approvalNote": "Max hat den separaten Parser-Hygiene-Patch im angepassten Strukturplan ausdrücklich freigegeben."
    },
    {
      "versionCode": 64,
      "versionName": "1.0.64-typed-update-versions",
      "patchId": "kgg-v064-typed-update-versions",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Strikte Update-Versionstypen",
      "reason": "Trennt Source-Code, Web-Release-ID, semantischen Versionsnamen und Android-Shell-Version fail-closed voneinander.",
      "whatChanged": [
        "Trennt Source-Code, Web-Release-ID, semantischen Versionsnamen und Android-Shell-Version fail-closed voneinander."
      ],
      "touchedAreas": [
        "GitHub Manifest",
        "Android/APK"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "Plan-State",
        "Medien/Upload",
        "API-Key-Logik",
        "Handy-Layout"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Max hat die getrennte Manifest- und Versionsauswertung im angepassten Strukturplan ausdrücklich freigegeben."
    }
  ],
  "latestVersionName": "1.0.89-changelog-archive-window-refresh",
  "archiveSnapshots": [
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v062.json",
      "snapshotVersionCode": 62,
      "entryCount": 34,
      "entriesSha256": "d1b3a5d67dd78ae6819bfbf28b321c66cdacdc173b4c39b358344e380fb30fef",
      "retainedEntryCountAtCompaction": 14,
      "createdByPatchId": "kgg-v063-changelog-archive-window"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v089.json",
      "snapshotVersionCode": 89,
      "entryCount": 30,
      "entriesSha256": "7c9c4d1d87e64c989ae670af3cd4892d7f046a3540c0dfbd4cc180bc75e4aa7e",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v089-changelog-archive-window-refresh"
    }
  ]
}
</script>
<!-- END kgg-changelog -->
