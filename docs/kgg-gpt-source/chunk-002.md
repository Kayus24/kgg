# KGG Source Chunk 002

- Source: `kgg-update/index.html`
- Lines: 841-1260

```html
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
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Plan-State",
        "Storage"
      ],
      "testStatus": {
        "debugFabVisible": "pending",
        "debugReportCopy": "pending",
        "workflowIndexUrl": "pending"
      },
      "createdAt": "2026-06-20T22:59:57.580956+00:00"
    },
    {
      "versionCode": 22,
      "versionName": "1.0.22-admin-debug-menu-feedback",
      "patchId": "kgg-v022-admin-debug-menu-feedback",
      "status": "active",
      "type": "github-web-update",
      "title": "Admin Debug-/Feedback-Menue",
      "reason": "Max braucht eine Admin-Oberfläche, die bei QR-, Layout-, Update-, Speicher- und anderen Problemen direkt verwertbares Feedback liefert.",
      "whatChanged": [
        "Adds Admin Debug / Feedback menu as v022.",
        "Tablet: Debug entry is inserted into the scan/admin side rail.",
        "Phone: Admin-Konfig, QR/Sync and Übungsdatenbank teilen are hidden from the scan hub and exposed through one Admin-Menue button.",
        "Debug report includes version, feature availability, QR debug, layout rectangles, source truth/changelog summary, localStorage key summary and last runtime errors.",
        "Adds global KGG_ADMIN_DEBUG_MENU.report() for future agents."
      ],
      "touchedAreas": [
        "Admin debug UI",
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
        "Tablet core layout/breakpoints",
        "Plan-State",
        "Storage"
      ],
      "testStatus": {
        "tabletMenu": "pending",
        "phoneMenu": "pending",
        "debugReportCopy": "pending",
        "adminActions": "pending"
      },
      "rollbackNote": "Remove or supersede only with explicit new admin debug menu patch; do not silently delete feedback tooling.",
      "createdAt": "2026-06-20T22:34:33.470984+00:00"
    },
    {
      "versionCode": 9,
      "versionName": "1.0.7-patch-retention-changelog-guard",
      "patchId": "web-v009-patch-retention-changelog-guard",
      "status": "active",
      "type": "github-web-update",
      "title": "Patch-Retention und Changelog-Größenwarnung",
      "reason": "Max will verhindern, dass spätere LLMs den letzten funktionalen Patch einer Funktion versehentlich löschen, und möchte gewarnt werden, wenn der interne Changelog zu groß wird.",
      "whatChanged": [
        "Patch-Retention-Policy direkt in kgg-source-truth eingebettet.",
        "kgg-patch-rules als eigener maschinenlesbarer JSON-Block ergänzt.",
        "Changelog-Größenpolicy mit Entry- und Byte-Warnschwellen ergänzt.",
        "Kleiner KGG_PATCH_GUARD im Browser ergänzt, der Source Truth/Changelog/Patch Rules auslesen und Changelog-Größe prüfen kann.",
        "LLM-Regeln erweitert: Patches nicht still löschen; bei Konflikten oder Größenwarnungen Max fragen."
      ],
      "touchedAreas": [
        "HTML embedded metadata",
        "Source Truth",
        "Changelog",
        "Patch rules",
        "Non-UI helper script"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Tablet-Layout",
        "Plan-State",
        "Storage"
      ],
      "supersedes": [],
      "removalPolicy": {
        "doNotDeleteReason": "Dieser Eintrag definiert die neue Regel, dass alte Fix-Patches nicht still entfernt werden dürfen.",
        "requiresExplicitMaxApprovalToRemove": true
      },
      "testStatus": {
        "githubPages": "pending",
        "androidApp": "pending",
        "llmReadability": "pending"
      }
    },
    {
      "versionCode": 8,
      "versionName": "1.0.6-qr-gallery-bitmap-debug",
      "type": "github-web-update",
      "title": "QR-Foto/Galerie-Import mit Debug und Bitmap-Fallback",
      "summary": "Verbessert QR-Erkennung aus Galerie-/Fotodatenbank-Bildern durch zusätzlichen BarcodeDetector-ImageBitmap-Fallback und sichtbare Warnungen, wenn ein Bild nicht dekodiert werden kann.",
      "changedAreas": [
        "QR-Bildimport",
        "HTML/JS",
        "eingebettete Source Truth",
        "eingebetteter Changelog"
      ],
      "notTouched": [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Tablet-Layout",
        "Plan-State",
        "Storage"
      ],
      "testStatus": {
        "githubPages": "pending",
        "androidApp": "pending",
        "qrGalleryImport": "pending"
      }
    },
    {
      "versionCode": 7,
      "versionName": "1.0.5-qr-photo-source-truth",
      "type": "github-web-update",
      "title": "QR-Foto-Upload + eingebettete Source Truth",
      "summary": "Verbessert QR-Erkennung aus Bild-/Fotodatenbank-Upload und bettet Source Truth sowie Changelog direkt in die App-HTML ein.",
      "changedAreas": [
        "QR photo upload decode",
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
        "Tablet-Layout",
        "Plan-State",
        "Storage"
      ],
      "testStatus": {
        "githubPages": "pending",
        "androidApp": "pending"
      },
      "handoffNote": "Lokale LLMs können index.html lesen und finden kgg-source-truth sowie kgg-changelog direkt im Code."
    }
  ],
  "latestVersionName": "1.0.45-phone-drawer-bank-align"
}
</script>
<!-- END kgg-changelog -->

<!-- BEGIN kgg-patch-rules: embedded Patch Rules; READ THIS BEFORE PATCHING -->
<script type="application/json" id="kgg-patch-rules">
{
  "schema": 1,
  "id": "kgg-patch-rules",
  "readFirst": [
    "#kgg-source-truth",
    "#kgg-changelog",
    "#kgg-patch-rules"
  ],
  "mustUpdateOnEveryPatch": [
    "kgg-source-truth.currentWebVersion",
    "kgg-source-truth.lastUpdateIntent",
    "kgg-changelog.entries",
    "kgg-update/version.json.versionCode",
    "kgg-update/version.json.versionName",
```
