
<!-- BEGIN kgg-changelog: embedded Changelog; READ THIS BEFORE PATCHING -->
<script type="application/json" id="kgg-changelog">
{
  "schema": 1,
  "latestVersionCode": 95,
  "entries": [
    {
      "versionCode": 95,
      "versionName": "1.0.95-cockpit-responsive-entry",
      "patchId": "kgg-v095-cockpit-responsive-entry",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Cockpit-Einstieg im Phone-Dock",
      "reason": "Zeigt bei geladenen Cockpit-Trainingsplänen einen gezählten Handy-Einstieg neben dem schwebenden Scan-Dock und hält den Tablet-Einstieg leerzustandsfest.",
      "whatChanged": [
        "Zeigt bei geladenen Cockpit-Trainingsplänen einen gezählten Handy-Einstieg neben dem schwebenden Scan-Dock und hält den Tablet-Einstieg leerzustandsfest."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
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
      "approvalNote": "Expliziter Nutzerauftrag: Im Handy-Dock soll bei geladenen Cockpit-Trainingsplänen ein gezählter Cockpit-Button erscheinen; der Tablet-Button darf ohne Plan nicht sichtbar sein."
    },
    {
      "versionCode": 94,
      "versionName": "1.0.94-shared-reorder-core",
      "patchId": "kgg-v094-shared-reorder-core",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Shared Reorder Core",
      "reason": "Teilt die bestehende Reorder-Berechnung und Array-Umordnung zwischen Planerstellung und Therapie-Cockpit.",
      "whatChanged": [
        "Teilt die bestehende Reorder-Berechnung und Array-Umordnung zwischen Planerstellung und Therapie-Cockpit."
      ],
      "touchedAreas": [
        "therapy-cockpit"
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
      "versionCode": 93,
      "versionName": "1.0.93-cockpit-shared-editor",
      "patchId": "kgg-v093-cockpit-shared-editor",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Cockpit gemeinsamer Editor und Progressionswechsel",
      "reason": "Verwendet den bestehenden Übungseditor auch für Cockpit-Slots und speichert den sichtbaren Progressionswechsel pro Slot.",
      "whatChanged": [
        "Verwendet den bestehenden Übungseditor auch für Cockpit-Slots und speichert den sichtbaren Progressionswechsel pro Slot."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
        "Plan-State",
        "Test-Harness"
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
      "approvalNote": "Expliziter Zielauftrag KGG-TICKET-037: Cockpit-Übungen müssen mit denselben Planerstellungsfunktionen bearbeitbar sein; das Changelog wird über den unveränderlichen Snapshot-Mechanismus archiviert."
    },
    {
      "versionCode": 92,
      "versionName": "1.0.92-cockpit-live-edit",
      "patchId": "kgg-v092-cockpit-live-edit",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Therapie-Cockpit direkt bearbeiten",
      "reason": "Erweitert das Cockpit um vollständige Übungsbearbeitung pro Slot und eine mobile aktive Patient:innenkarte.",
      "whatChanged": [
        "Erweitert das Cockpit um vollständige Übungsbearbeitung pro Slot und eine mobile aktive Patient:innenkarte."
      ],
      "touchedAreas": [
        "Handy-Layout",
        "Plan-State",
        "Medien/Upload"
      ],
      "notTouched": [
        "PDF",
        "QR/Patienten-App",
        "Scan/OCR",
        "Parser",
        "API-Key-Logik",
        "Android/APK",
        "GitHub Manifest"
      ],
      "testStatus": {
        "local": "pending",
        "certification": "pending"
      },
      "approvalNote": "Expliziter Nutzerauftrag: Cockpit-Pläne direkt auf Phone und Tablet vollständig bearbeiten."
    },
    {
      "versionCode": 91,
      "versionName": "1.0.91-plan-add-exercise-card",
      "patchId": "kgg-v091-plan-add-exercise-card",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Übung hinzufügen – Plus-Karte in der Planliste",
      "reason": "Die Planliste erhält eine kleine leere Plus-Karte, die den bestehenden Eingabe- und Übungsdatenbankweg zum Hinzufügen einer weiteren Übung öffnet.",
      "whatChanged": [
        "Kleine leere Plus-Karte am Ende der aktuellen Planliste ergänzt.",
        "Der Klick fokussiert den bestehenden Übungseingang und öffnet bei Bedarf die Übungsdatenbank.",
        "Plan-State, Übungsdatenbank, Reorder-Mechanismus und Speicherweg bleiben unverändert."
      ],
      "touchedAreas": [
        "Planerstellung",
        "UI"
      ],
      "notTouched": [
        "Therapie-Cockpit",
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
      }
    },
    {
      "versionCode": 90,
      "versionName": "1.0.90-cockpit-exercises-only",
      "patchId": "kgg-v090-cockpit-exercises-only",
      "status": "scaffolded",
      "type": "module-patch",
      "title": "Therapie-Cockpit ohne Basisdaten",
      "reason": "Cockpit-Pläne können aus mindestens einer gültigen Übung auch ohne Patient:innen-Basisdaten erzeugt werden; der neutrale Codec-Name bleibt flüchtig und alte Fehlerhinweise werden nach Erfolg gelöscht.",
      "whatChanged": [
        "Cockpit-Pläne können aus mindestens einer gültigen Übung auch ohne Patient:innen-Basisdaten erzeugt werden; der neutrale Codec-Name bleibt flüchtig und alte Fehlerhinweise werden nach Erfolg gelöscht."
      ],
      "touchedAreas": [
        "Therapie-Cockpit",
        "Test-Harness"
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
    }
  ],
  "latestVersionName": "1.0.95-cockpit-responsive-entry",
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
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v090.json",
      "snapshotVersionCode": 90,
      "entryCount": 31,
      "entriesSha256": "9338e9ab7cc88ef314427fe9e4224da1502b9fe375833e87d121be1f051ca04c",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v090-cockpit-exercises-only"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v091.json",
      "snapshotVersionCode": 91,
      "entryCount": 32,
      "entriesSha256": "49a8b739cbd3fb285351fcded6cd6a7e3bb0b73cb10ddbc098e7a3e4431d7e3a",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v091-plan-add-exercise-card"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v092.json",
      "snapshotVersionCode": 92,
      "entryCount": 33,
      "entriesSha256": "f45be1a63673425f82fa6075a77ce0070508b80ec9022aba203a309af4e962e8",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v092-cockpit-live-edit"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v093.json",
      "snapshotVersionCode": 93,
      "entryCount": 34,
      "entriesSha256": "8e2320be08c56aed8ee20830ebcc2bcdd2abb6d8f4bfab360cb05df5a923da9a",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v093-cockpit-shared-editor"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v094.json",
      "snapshotVersionCode": 94,
      "entryCount": 35,
      "entriesSha256": "0aed8ea8e500e26ff0a23dc0561cf16d73be7ab33b4103c22630da600761f9cc",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v094-shared-reorder-core"
    },
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v095.json",
      "snapshotVersionCode": 95,
      "entryCount": 36,
      "entriesSha256": "0c1b56d0a436b875e4f4bdf403b95cc23150aed2d309caba8f62241dd3ed4053",
      "retainedEntryCountAtCompaction": 15,
      "createdByPatchId": "kgg-v095-cockpit-responsive-entry"
    }
  ]
}
</script>
<!-- END kgg-changelog -->
