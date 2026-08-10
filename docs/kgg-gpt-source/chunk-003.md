# KGG Source Chunk 003

- Source: `kgg-update/src` modular source
- Lines: 1261-1680

```html
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
  "latestVersionName": "1.0.62-tablet-recent-package-shell-geometry"
}
</script>
<!-- END kgg-changelog -->

<!-- SOURCE FILE: kgg-update/src/metadata/patch-rules.html -->

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
    "kgg-update/version.json.sha256",
    "kgg-source-truth.currentVersion",
    "kgg-patch-rules",
    "kgg-update/version.json.indexUrl"
  ],
  "protectedAreas": [
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
  "patchRetentionPolicy": {
    "rule": "Never delete the latest patch for a function silently.",
    "why": "The last patch for a feature is often what fixed or stabilized the bug; removing it without tracking can reintroduce old bugs.",
    "defaultBehavior": "Preserve previous patch code and patch history unless Max explicitly approves removal.",
    "whenReplacingPatch": [
      "Mark old changelog entry as superseded, not deleted.",
      "Add supersededBy on the old entry when practical.",
      "Add supersedes on the new entry.",
      "Record whySuperseded/removalReason/testEvidence/rollbackNote."
    ],
    "requiredWhenRemovingPatch": [
      "supersededBy",
      "removalReason",
      "testEvidence",
      "rollbackNote",
      "explicitMaxApproval"
    ],
    "pipelineExpectation": "If patch markers or active fixes disappear without changelog documentation, stop and ask Max."
  },
  "changelogSizePolicy": {
    "scope": "embedded kgg-changelog in index.html",
    "warnAtEntries": 18,
    "maxEmbeddedEntries": 30,
    "warnAtBytes": 35000,
    "maxEmbeddedBytes": 55000,
    "actionWhenWarningThresholdReached": "Warn Max before adding more large entries; propose compact summaries or external archival.",
    "actionWhenMaxExceeded": "Stop non-critical updates until Max approves compaction/archive strategy.",
    "doNotAutoDeleteHistory": true
  },
  "blockPatchIfMissing": [
    "kgg-source-truth",
    "kgg-changelog",
    "kgg-patch-rules"
  ],
  "requiredOnPatchRemoval": [
    "supersededBy or replacementPatchId",
    "removalReason",
    "testEvidence",
    "rollbackNote",
    "explicitMaxApproval"
  ],
  "llmInstruction": "If changelog size exceeds policy thresholds or a patch-removal is not documented, warn Max and ask before changing code.",
  "adminDebugMenuPolicy": {
    "patchId": "kgg-v022-admin-debug-menu-feedback",
    "purpose": "Keep an in-app admin feedback/debug path available for future QR/layout/update/storage issues.",
    "doNotRemoveWithout": [
      "supersededBy",
      "reason",
      "testEvidence",
      "Max approval"
    ],
    "expectedGlobal": "KGG_ADMIN_DEBUG_MENU.report()"
  },
  "adminDebugVisibleHotfix": {
    "patchId": "kgg-v023-admin-debug-visible-hotfix",
    "purpose": "Debug entry must be visible in admin/therapist app even when adminMode class is missing.",
    "expectedGlobal": "KGG_ADMIN_DEBUG_MENU.report()",
    "expectedButton": "#kggAdminDebugFab",
    "doNotRemoveWithout": [
      "supersededBy",
      "reason",
      "testEvidence",
      "Max approval"
    ]
  },
  "adminDebugRollbackPolicy": {
    "patchId": "kgg-v024-rollback-v023-debug-breakage",
    "reason": "v023 broke tablet layout; debug UI must not be reintroduced without isolated viewport tests.",
    "blockedUntil": [
      "tablet screenshot proof",
      "phone screenshot proof",
      "no duplicate debug entry",
      "Max approval"
    ]
  },
  "lastUpdatedByPatchId": "kgg-v062-tablet-recent-package-shell-geometry",
  "phoneViewportLeakGuardPolicy": {
    "patchId": "kgg-v014-phone-viewport-state-release-guard",
    "purpose": "Phone-only gesture/layout state must not leak into tablet or landscape viewports.",
    "requirements": [
      "Gate phone behavior with matchMedia('(max-width:759px)').",
      "When leaving phone viewport, remove kggPlanCardReordering, kggPlanCardSwiping, kggPlanSectionFrozen and stale inline drag/swipe styles.",
      "Do not fix phone drag by changing global tablet containers such as #currentPlanBlock or .planSectionBody outside max-width:759px.",
      "Phone drag-reorder must use #planList local absolute coordinates, not viewport fixed positioning.",
      "Local content://, file:// and /media/external/file/ tests must not auto-redirect to GitHub; the normal update prompt may remain."
    ],
    "doNotRemoveWithout": [
      "supersededBy",
      "reason",
      "phone portrait test",
      "tablet/landscape test",
      "Max approval"
    ]
  }
}
</script>
<!-- END kgg-patch-rules -->

<!-- SOURCE FILE: kgg-update/src/metadata/changelog-guard.html -->

<!-- BEGIN kgg-changelog-size-guard: console/helper warning when embedded changelog grows too large -->
<script id="kgg-changelog-size-guard">
(function(){
  "use strict";
  var FALLBACK_POLICY = {
    warnAtEntries: 18,
    maxEmbeddedEntries: 30,
    warnAtBytes: 35000,
    maxEmbeddedBytes: 55000
  };
  function readJsonBlock(id){
    var el = document.getElementById(id);
    if(!el) return null;
    try{ return JSON.parse((el.textContent||"").trim()); }
    catch(err){ return {__parseError:String(err)}; }
  }
  function changelogSizeReport(){
    var el = document.getElementById("kgg-changelog");
    var rules = readJsonBlock("kgg-patch-rules") || {};
    var policy = (rules && rules.changelogSizePolicy) || FALLBACK_POLICY;
    var text = el ? (el.textContent || "") : "";
    var entries = 0;
    var parseError = "";
    try{
      var data = text ? JSON.parse(text) : {};
      entries = Array.isArray(data.entries) ? data.entries.length : 0;
    }catch(err){
      parseError = String(err);
    }
    var bytes = 0;
    try{ bytes = new TextEncoder().encode(text).length; }
    catch(err){ bytes = text.length; }
    var warnings = [];
    if(!el) warnings.push("kgg-changelog block missing");
    if(parseError) warnings.push("kgg-changelog parse error: " + parseError);
    if(entries >= Number(policy.warnAtEntries || FALLBACK_POLICY.warnAtEntries)){
      warnings.push("embedded changelog entries approaching limit: " + entries + "/" + (policy.maxEmbeddedEntries || FALLBACK_POLICY.maxEmbeddedEntries));
    }
    if(bytes >= Number(policy.warnAtBytes || FALLBACK_POLICY.warnAtBytes)){
      warnings.push("embedded changelog bytes approaching limit: " + bytes + "/" + (policy.maxEmbeddedBytes || FALLBACK_POLICY.maxEmbeddedBytes));
    }
    return {
      entries: entries,
      bytes: bytes,
      policy: policy,
      warnings: warnings,
      shouldWarn: warnings.length > 0
    };
  }
  window.KGG_PATCH_GUARD = window.KGG_PATCH_GUARD || {};
  window.KGG_PATCH_GUARD.readSourceTruth = function(){ return readJsonBlock("kgg-source-truth"); };
  window.KGG_PATCH_GUARD.readChangelog = function(){ return readJsonBlock("kgg-changelog"); };
  window.KGG_PATCH_GUARD.readPatchRules = function(){ return readJsonBlock("kgg-patch-rules"); };
  window.KGG_PATCH_GUARD.checkChangelogSize = changelogSizeReport;
  var report = changelogSizeReport();
  window.KGG_PATCH_GUARD.lastChangelogSizeReport = report;
  if(report.shouldWarn && console && console.warn){
    console.warn("KGG changelog/source-truth warning:", report);
  }
})();
</script>
<!-- END kgg-changelog-size-guard -->

<!-- SOURCE FILE: kgg-update/src/base-app.html -->
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <script id="kgg-v047-phone-landscape-tablet-viewport-early">
  (function(){
    "use strict";
    var PATCH_ID="kgg-v047-phone-landscape-tablet-menu";
    var FORCED_VIEWPORT="width=760, initial-scale=1, viewport-fit=cover";
    var meta=document.querySelector('meta[name="viewport"]');
    var defaultViewport=meta?meta.getAttribute("content")||"width=device-width, initial-scale=1, viewport-fit=cover":"width=device-width, initial-scale=1, viewport-fit=cover";
    var active=false;
    function metrics(){
      var vv=window.visualViewport||null;
      var w=Math.round((vv&&vv.width)||window.innerWidth||0);
      var h=Math.round((vv&&vv.height)||window.innerHeight||0);
      var orientation=screen&&screen.orientation&&screen.orientation.type?String(screen.orientation.type):"";
      return {width:w,height:h,shortSide:Math.min(w||0,h||0),longSide:Math.max(w||0,h||0),screenOrientation:orientation};
    }
    function shouldForceTabletViewport(){
      var m=metrics();
      var landscapeByViewport=!!(m.width&&m.height&&m.width>m.height);
      var landscapeByScreen=/landscape/i.test(m.screenOrientation||"");
      var landscape=landscapeByViewport||landscapeByScreen;
      return !!(landscape&&m.longSide>=560&&m.shortSide>0&&m.shortSide<=560);
    }
    function apply(){
      var next=shouldForceTabletViewport();
      if(meta)meta.setAttribute("content",next?FORCED_VIEWPORT:defaultViewport);
      active=next;
      document.documentElement.classList.toggle("kggLandscapeTabletViewport",next);
      return active;
    }
    window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047={
      patchId:PATCH_ID,
      apply:apply,
      isActive:function(){return active||shouldForceTabletViewport();},
      metrics:metrics,
      forcedViewport:FORCED_VIEWPORT
    };
    apply();
    window.addEventListener("resize",function(){setTimeout(apply,40);},{passive:true});
    window.addEventListener("orientationchange",function(){setTimeout(apply,80);setTimeout(apply,220);},{passive:true});
    if(window.visualViewport)window.visualViewport.addEventListener("resize",function(){setTimeout(apply,40);},{passive:true});
  })();
  </script>
  <meta name="theme-color" content="#0a1024">
  <meta name="application-name" content="KGG Plan App">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="KGG Plan">
  <meta name="mobile-web-app-capable" content="yes">
  <link rel="manifest" href="kgg_therapist_manifest.webmanifest">
  <link rel="icon" href="kgg_therapist_icon.svg" type="image/svg+xml">
  <title>KGG Update v062 Plan-Historie mit stabiler Hintergrund-Geometrie</title>
  <style>
    :root{
      --bg:#e8eef6;--paper:#fff;--ink:#071027;--muted:#657386;--line:#dce3eb;--blue:#dcecff;--blue2:#eef6ff;--accent:#0a1024;--danger:#e23b54;--soft:#f6f8fb;--shadow:0 4px 14px rgba(7,16,39,.08);--r:22px;
```
