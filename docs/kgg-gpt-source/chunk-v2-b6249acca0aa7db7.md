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
    }
  ],
  "latestVersionName": "1.0.87-ticket-015-live-fix",
  "archiveSnapshots": [
    {
      "repositoryPath": "docs/changelog-archive/kgg-therapist-changelog-through-v062.json",
      "snapshotVersionCode": 62,
      "entryCount": 34,
      "entriesSha256": "d1b3a5d67dd78ae6819bfbf28b321c66cdacdc173b4c39b358344e380fb30fef",
      "retainedEntryCountAtCompaction": 14,
      "createdByPatchId": "kgg-v063-changelog-archive-window"
    }
  ]
}
</script>
<!-- END kgg-changelog -->
