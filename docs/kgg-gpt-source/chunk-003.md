# KGG Source Chunk 003

- Source: `kgg-update/index.html`
- Lines: 1261-1680

```html
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
  "lastUpdatedByPatchId": "kgg-v014-phone-viewport-state-release-guard",
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
  <title>KGG Update v55 Kolleg:innen Share APK Fix</title>
  <style>
    :root{
      --bg:#e8eef6;--paper:#fff;--ink:#071027;--muted:#657386;--line:#dce3eb;--blue:#dcecff;--blue2:#eef6ff;--accent:#0a1024;--danger:#e23b54;--soft:#f6f8fb;--shadow:0 4px 14px rgba(7,16,39,.08);--r:22px;
    }
    *{box-sizing:border-box;-webkit-tap-highlight-color:transparent} html,body{margin:0;min-height:100%;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink)}
    body{display:flex;justify-content:center}.app{width:min(100%,520px);min-height:100vh;background:var(--bg);padding:14px 12px 64px}.topbar{position:sticky;top:0;z-index:10;margin:-14px -12px 12px;padding:10px 12px;background:rgba(232,238,246,.92);backdrop-filter:blur(8px);border-bottom:1px solid rgba(220,227,235,.7)}
    .topbar h1{font-size:18px;margin:0}.topbar small{color:var(--muted);font-weight:700}.scanHub{background:var(--blue2);border:2px solid #5ea7e8;border-radius:20px;padding:14px;margin:8px 0 12px;box-shadow:var(--shadow)}.scanBtn,.primary{background:var(--accent);color:white;border:0;border-radius:14px;padding:12px 18px;font-weight:900;font-size:16px;box-shadow:0 4px 10px rgba(7,16,39,.18)}button{font:inherit;cursor:pointer}.mutedBtn{background:white;border:1px solid var(--line);border-radius:14px;padding:10px 12px;font-weight:800}.scanMeta{border-top:1px solid var(--line);margin-top:14px;padding-top:12px;color:var(--muted);font-weight:900;font-size:20px}.scanMeta.filePickBtn{cursor:pointer;user-select:none}.scanMeta.filePickBtn:focus-visible{outline:3px solid rgba(94,167,232,.45);outline-offset:4px;border-radius:10px}.scanMeta small{display:block;font-size:14px;margin-top:6px}.panel{background:var(--paper);border:2px solid #1b2230;border-radius:26px;padding:12px;margin:0 0 12px;box-shadow:var(--shadow)}.panelTitle{font-size:30px;line-height:1;font-weight:1000;margin:0 0 12px;letter-spacing:-1px}.inner{border:2px solid #1b2230;border-radius:22px;padding:10px;background:white}.row{display:flex;align-items:center;gap:8px}.baseCard,.drawerBtn{width:100%;background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px;font-size:18px;font-weight:900;box-shadow:var(--shadow);display:flex;justify-content:space-between;align-items:center}.label{font-size:14px;font-weight:900;margin:12px 0 6px}.inputWrap{position:relative;border:1px solid var(--line);border-radius:16px;background:white;box-shadow:var(--shadow);overflow:hidden}textarea{width:100%;min-height:72px;resize:vertical;border:0;outline:0;padding:16px 46px 16px 14px;font-size:20px;line-height:1.35;color:var(--ink);background:white}textarea::placeholder{color:#8c98a9}.clearBtn{position:absolute;right:10px;top:10px;border:0;background:transparent;color:var(--danger);font-size:24px;font-weight:1000;padding:6px}.suggestion{background:#edf5ff;border-top:1px solid var(--line);padding:10px 12px;font-weight:1000;font-size:18px}.suggestion small{display:block;font-size:11px;color:var(--muted);margin-bottom:4px}.tools{display:grid;gap:10px;margin-top:10px}.drawerBtn{font-size:18px}.drawerBtn .mini{font-size:12px;color:var(--muted)}.planList{display:grid;gap:8px;margin:10px 0}.planCard{border:1px solid var(--line);border-radius:16px;padding:10px 12px;background:#fbfdff;box-shadow:var(--shadow);display:grid;grid-template-columns:1fr auto;gap:8px}.planCard b{font-size:17px}.planCard small{color:var(--muted);font-weight:800}.iconBtn{border:0;background:transparent;font-size:18px;padding:8px}.dbHead{display:flex;align-items:center;justify-content:space-between}.dbTitle{font-size:24px;font-weight:1000;margin:8px 0;display:flex;align-items:center;justify-content:flex-start;gap:10px;cursor:pointer;user-select:none}.finishBtn{width:100%;margin-top:14px;border-radius:18px;padding:16px;font-size:22px}.planMode .panelTitle{font-size:28px}.planCard{position:relative}.planCard .drag{display:inline-grid;place-items:center;width:34px;height:34px;border:0;border-radius:999px;background:#edf5ff;margin-right:8px;color:#31536f;font-weight:1000;touch-action:none;user-select:none;cursor:pointer}.planCard.reorder-placeholder{opacity:.55;transform:scaleY(.5);transform-origin:center;min-height:34px;border:2px dashed #9bb7d8;background:#edf5ff;box-shadow:none}.planCard.reorder-gap-before{margin-top:18px}.planCard.reorder-gap-after{margin-bottom:18px}.planCard.reorder-lifted{position:fixed!important;z-index:80;width:calc(min(100vw,520px) - 48px);left:var(--drag-left,12px);top:var(--drag-top,0px);transform:translateY(var(--drag-y,0px)) scale(1.035);opacity:.94;box-shadow:0 2px 3px rgba(7,16,39,.10),0 10px 24px rgba(7,16,39,.18),0 28px 60px rgba(7,16,39,.22);filter:drop-shadow(0 1px 0 rgba(255,255,255,.65));pointer-events:none}.planList.reorder-active .planCard:not(.reorder-lifted){transition:transform .14s ease,margin .14s ease,opacity .14s ease}.drag.reorder-armed{background:#dcecff;box-shadow:0 0 0 3px rgba(94,167,232,.25);color:#123a5c}.planCard.reorder-prelift{box-shadow:0 8px 20px rgba(7,16,39,.15);transform:scale(1.006);transition:box-shadow .12s ease,transform .12s ease}.planCard .planMain{display:flex;align-items:center}.planCard .planText{display:grid}.bankArea{margin-top:0;border-radius:16px;overflow:hidden;background:white}.bankOpen{border:1px solid var(--line);box-shadow:var(--shadow)}.bankRows{max-height:440px;overflow:auto;scroll-behavior:smooth;background:white}.bankRow{display:grid;grid-template-columns:1fr auto;gap:8px;padding:10px 12px;border-bottom:1px solid #eef2f6;background:white}.bankRow b{font-size:15px}.bankRow small{display:block;color:var(--muted);font-weight:800;margin-top:3px;font-size:11px}.bankLabel{background:#edf5ff;color:#4d6685;font-size:11px;font-weight:1000;padding:5px 10px}.bankWithAz{display:grid;grid-template-columns:42px 1fr}.az{background:#f5f8fc;border-right:1px solid var(--line);padding:7px 0;text-align:center;font-size:11px;font-weight:1000;color:#425267;line-height:1.28;user-select:none;touch-action:none;overscroll-behavior:contain;overflow:visible}.az button{display:block;position:relative;width:100%;min-height:16px;border:0;background:transparent;font-size:11px;font-weight:1000;color:#425267;padding:0;border-radius:999px;transform-origin:center;transition:transform .1s ease,background .1s ease,color .1s ease,box-shadow .1s ease}.az button.active,.az button:active{background:#071027;color:#fff;transform:scale(1.08)}.az.azTouching button.active,.az button:active{z-index:3;transform:translateY(-6px) scale(1.45);box-shadow:0 5px 12px rgba(7,16,39,.2)}.bottomPad{height:220px}.stateBadge{display:inline-block;background:#071027;color:#fff;border-radius:999px;padding:6px 10px;font-weight:900;font-size:12px}.hidden{display:none!important}.modal{position:fixed;inset:0;background:rgba(7,16,39,.45);z-index:50;display:none;align-items:flex-end;justify-content:center}.modal.open{display:flex}.sheet{width:min(100%,520px);background:white;border-radius:24px 24px 0 0;padding:16px;box-shadow:0 -8px 30px rgba(0,0,0,.18)}.sheet h2{margin:0 0 10px}.field{display:grid;gap:5px;margin:8px 0}.field label{font-size:12px;color:var(--muted);font-weight:900}.field input,.field select{border:1px solid var(--line);border-radius:12px;padding:11px;font-size:16px;background:white;color:var(--ink);width:100%}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.notice{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;color:#38475b;font-weight:750;margin-top:10px}.danger{color:var(--danger)}.apiBox{background:#fff8e8;border:1px solid #f2d38a;border-radius:16px;padding:12px;margin-top:10px;color:#6a4c00;font-weight:750}.patientOutput{background:#f7fbff;border:2px solid #5ea7e8;border-radius:18px;padding:12px;margin-top:10px}.patientLink{display:block;text-align:center;background:#071027;color:#fff;text-decoration:none;border-radius:14px;padding:13px 12px;font-weight:1000;margin-top:10px}.qrBox{display:grid;place-items:center;background:#fff;border:1px solid var(--line);border-radius:16px;min-height:clamp(220px,64vw,340px);padding:14px;margin-top:10px}.qrBox img{width:92%;max-width:380px;height:auto;image-rendering:pixelated}.qrStatus{font-size:12px;color:var(--muted);font-weight:900;text-align:center;margin-top:8px}.footerActions{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(100%,520px);display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;background:rgba(232,238,246,.94);padding:10px 12px calc(10px + env(safe-area-inset-bottom));border-top:1px solid var(--line);backdrop-filter:blur(8px)}
    @media (max-width:390px){.panelTitle{font-size:25px}.dbTitle{font-size:24px}textarea{font-size:18px}.bankRows{max-height:380px}}
    @media (max-width:759px){
      .tools{position:relative}
      #recentList:not(.hidden),#packageList:not(.hidden){position:absolute;left:0;right:0;bottom:calc(100% + 10px);z-index:42;max-height:min(54vh,360px);overflow:auto;background:rgba(255,255,255,.97);border:1px solid rgba(220,227,235,.94);border-radius:22px;padding:10px;box-shadow:0 18px 48px rgba(7,16,39,.2),0 4px 14px rgba(7,16,39,.1);backdrop-filter:blur(10px);transform-origin:bottom center;animation:mobileDrawerRise .26s cubic-bezier(.18,.84,.24,1) both}
      #recentList:not(.hidden) .notice,#packageList:not(.hidden) .notice{margin-top:0}
      @keyframes mobileDrawerRise{0%{opacity:0;transform:translateY(18px) scale(.97);filter:blur(2px)}70%{opacity:1;transform:translateY(-3px) scale(1.01);filter:blur(0)}100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}
    }
    .topbar,.footerActions,body>.app>.apiBox,#debugPayloadBox{display:none!important}.nativeFileInput{position:fixed;left:-100vw;top:0;width:1px;height:1px;opacity:.01}.app{padding-top:12px;padding-bottom:24px}.bottomPad{height:24px}.finishChoices{display:grid;gap:10px;margin-top:12px}.finishChoices button{width:100%;min-height:52px}.finishPdfRow{display:grid;grid-template-columns:minmax(0,1fr) 58px;gap:8px}.finishPdfLargeBtn{font-size:24px;line-height:1;padding:0;min-height:52px;border-radius:16px}.pdfPreviewSheet{width:min(96vw,860px);height:min(92vh,780px);display:grid;grid-template-rows:auto auto auto minmax(220px,1fr) auto auto;gap:8px}.pdfPreviewFrame{width:100%;height:100%;border:1px solid var(--line);border-radius:16px;background:#fff}.pdfPreviewFallback{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;background:#f6f8fb;border:1px solid var(--line);border-radius:16px;padding:10px 12px;color:#38475b;font-weight:800}.pdfPreviewFallback.hidden{display:none!important}.pdfPreviewFallback small{display:block;color:var(--muted);font-weight:800;margin-top:2px}.pdfPreviewFallback .mutedBtn{white-space:nowrap}.patientOutput.hidden{display:none!important}.modal{align-items:center}.sheet{border-radius:24px;max-height:92vh;overflow:auto}
    .pdfPreviewMobileBridge{display:grid;gap:8px;background:#f6f8fb;border:1px solid var(--line);border-radius:16px;padding:10px 12px}.pdfPreviewMobileBridge.hidden{display:none!important}.pdfPreviewMobileBridge .primary{width:100%;min-height:56px;border-radius:16px}.pdfPreviewMobileBridge small{display:block;color:var(--muted);font-weight:800;line-height:1.25}.pdfPreviewModalMobile .pdfPreviewSheet{height:auto;grid-template-rows:auto auto auto auto auto}.pdfPreviewModalMobile .pdfPreviewFrame{display:none}.pdfPreviewModalMobile .pdfPreviewFallback{display:none!important}
    .dbTitle{position:relative;min-height:32px;overflow:visible;gap:0;margin:6px 0 6px;font-size:22px;line-height:1.15}.dbTitle .dbTitleTrain{display:inline-block;white-space:nowrap;transform-origin:left center}.dbTitle.fullBankOpen,.dbTitle.searchBankOpen{margin:6px 0 6px}.dbTitle.fullBankOpen .dbTitleTrain{animation:dbTitleSlideUp .48s cubic-bezier(.2,.9,.2,1) both}.dbTitle.searchBankOpen .dbTitleTrain{animation:none}.bankArea.bankOpen{display:block;padding:8px}.bankArea.bankOpen #bankContent{min-width:0;margin-top:8px}.drawerBtn.dbMascotDock{width:56px;height:56px;min-height:56px;margin:0;padding:0;border:0;background:transparent;box-shadow:none;justify-content:center}.dbToggleMain{display:flex;align-items:center;gap:10px;min-width:0}.dbToggleText{white-space:nowrap}.dbMascotBubble{display:inline-flex;align-items:center;justify-content:center;gap:2px;width:48px;height:48px;border:2px solid #1b2230;border-radius:999px;background:#fff;box-shadow:var(--shadow);line-height:1;flex:0 0 auto}.dbMascotBubble .dbCaret{font-size:13px;line-height:1;transform:translateY(-1px)}.dbMascotBubble .dbMascot{font-size:18px;line-height:1}.bankArea:not(.bankOpen) .dbMascotBubble{width:auto;height:auto;border:0;border-radius:0;background:transparent;box-shadow:none}.bankArea:not(.bankOpen) .dbMascotBubble .dbCaret{font-size:18px}.drawerBtn.dbMascotDock .dbToggleText{display:none}@keyframes dbTitleSlideUp{0%{transform:translateY(var(--db-title-start-y,86px)) scale(.98);opacity:.86}100%{transform:translateY(0) scale(1);opacity:1}}
    .bankArea.bankOpen.alphaBankOpen{position:relative}.bankArea.bankOpen.alphaBankOpen #bankToggle{position:absolute;left:8px;top:8px;z-index:2}.bankArea.bankOpen.alphaBankOpen #bankContent{margin-top:0}.bankArea.bankOpen.alphaBankOpen .bankWithAz{grid-template-columns:56px minmax(0,1fr);column-gap:8px}.bankArea.bankOpen.alphaBankOpen .az{width:42px;justify-self:center;margin-top:64px;border-right:0;border-radius:999px}.bankArea.bankOpen.alphaBankOpen .bankRows{grid-column:2}
    .planActions{display:grid;grid-template-columns:minmax(0,0fr) minmax(0,1fr);gap:10px;align-items:stretch;transition:grid-template-columns .34s cubic-bezier(.2,.85,.2,1)}.planActions.hasPlan{grid-template-columns:minmax(112px,1fr) 56px}.planActions .finishBtn{margin:0;min-width:0;overflow:hidden;white-space:nowrap;transform-origin:left center;opacity:0;scale:.65 1;transition:opacity .18s ease,scale .34s cubic-bezier(.2,.85,.2,1),padding .34s cubic-bezier(.2,.85,.2,1)}.planActions .finishBtn.hidden{display:block!important;visibility:hidden;pointer-events:none;padding-left:0;padding-right:0;border-width:0}.planActions.hasPlan .finishBtn{opacity:1;scale:1 1;animation:finishGrowIn .34s cubic-bezier(.2,.85,.2,1) both}.planActions #recentToggle{min-width:0;overflow:hidden;transition:width .34s cubic-bezier(.2,.85,.2,1),padding .34s cubic-bezier(.2,.85,.2,1);white-space:nowrap}.recentIcon{flex:0 0 auto}.recentText,.recentMini{overflow:hidden;transition:max-width .24s ease,opacity .18s ease}.planActions.hasPlan #recentToggle{width:56px;min-width:56px;padding-left:0;padding-right:0;justify-content:center}.planActions.hasPlan .recentText,.planActions.hasPlan .recentMini{max-width:0;opacity:0}@keyframes finishGrowIn{0%{transform:scaleX(.48);opacity:.1}65%{transform:scaleX(1.03);opacity:1}100%{transform:scaleX(1);opacity:1}}
    .planHeader{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:8px;margin-bottom:12px}.planHeader .panelTitle{margin:0}.packageSaveBtn{position:relative;width:auto;min-width:74px;height:44px;padding:0 13px;border:2px solid #1b2230;border-radius:16px;background:#fff;box-shadow:0 2px 8px rgba(7,16,39,.08);display:flex;align-items:center;justify-content:center;gap:6px;overflow:hidden;font-weight:1000;margin:0}.packageSaveBtn.hidden{display:none!important}.packageSaveBtn .packageBox{font-size:27px;line-height:1}.packageSaveBtn .packagePlus{font-size:20px;line-height:1;color:#071027;text-shadow:0 1px 0 #fff}.packageSaveBtn.packagePulse .packagePlus{animation:packagePlusFly .48s cubic-bezier(.2,.9,.2,1) both}.packageSaveBtn.packagePulse .packageBox{animation:packageBoxPop .48s cubic-bezier(.2,.9,.2,1) both}@keyframes packagePlusFly{0%{transform:translate(0,0) scale(1);opacity:1}55%{transform:translate(14px,7px) scale(.82);opacity:1}100%{transform:translate(20px,9px) scale(.45);opacity:0}}@keyframes packageBoxPop{0%,100%{transform:scale(1)}58%{transform:scale(1.08)}}
    .inputWrap textarea{padding-right:36px}.inputWrap #exerciseInput{overflow:hidden;resize:none}.inputWrap #exerciseInput.hasText{min-height:0}.clearBtn{top:2px;right:4px;padding:4px 6px;line-height:1}
    .planActions:not(.hasPlan){grid-template-columns:minmax(0,0fr) minmax(0,1fr);gap:0}.planActions:not(.hasPlan) #recentToggle,#createPanel:not(.planMode) #packageToggle{height:58px;min-height:58px;box-sizing:border-box;align-items:center}.planActions:not(.hasPlan) .finishBtn.hidden{width:0}
    .az.azTouching button.active:not(.touch-preview){transform:scale(1.08);box-shadow:none}.az button.az-empty:not(.active){color:#7f8b9a;background:#e3e9f0}.az.azTouching button.touch-near2{z-index:4;transform:translateY(-10px) scale(1.16)}.az.azTouching button.touch-near1{z-index:5;transform:translateY(-24px) scale(1.48);box-shadow:0 5px 14px rgba(7,16,39,.14)}.az.azTouching button.touch-preview,.az button:active{z-index:6;transform:translateY(-48px) scale(2.15);box-shadow:0 10px 24px rgba(7,16,39,.24),0 0 0 2px rgba(255,255,255,.92)}
    .planCard.reorder-lifted{opacity:.98;border-color:rgba(120,137,158,.34);box-shadow:0 1px 2px rgba(7,16,39,.08),0 8px 18px rgba(7,16,39,.18),0 22px 42px rgba(7,16,39,.16);filter:none}
    .planCard.reorder-placeholder{opacity:1;transform:none;min-height:48px;border:0;background:transparent;box-shadow:none;backdrop-filter:none;position:relative;overflow:visible}
    .planCard.reorder-placeholder::before{content:"";position:absolute;left:9%;right:9%;top:50%;height:44%;transform:translateY(-50%);border-radius:999px;background:radial-gradient(ellipse at center,rgba(7,16,39,.24) 0%,rgba(7,16,39,.15) 34%,rgba(7,16,39,.07) 58%,rgba(7,16,39,0) 78%);filter:blur(9px)}
    .patientLinkCopyField{width:100%;min-height:64px;margin-top:8px;border:1px solid var(--line);border-radius:12px;padding:9px 10px;font-size:12px;line-height:1.25;background:#fff;color:#38475b;resize:none;word-break:break-all}
    .adminConfigBtn,.sharedBankBtn{display:none;width:100%;margin-top:10px}.adminMode .adminConfigBtn,.adminMode .sharedBankBtn{display:block}.secretStatus{display:block;color:var(--muted);font-size:13px;font-weight:800;margin-top:4px}.adminCodePackageTools{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.adminCodePackageTools .wide{grid-column:1/-1}.adminPackageHint{font-size:12px;color:var(--muted);font-weight:800;margin-top:8px}.sharedBankText{width:100%;min-height:180px;margin-top:8px;border:1px solid var(--line);border-radius:12px;padding:10px;font-size:12px;line-height:1.3;background:#fff;color:#38475b}
    .dbTitle.fullBankOpen .dbTitleTrain{animation:dbTitleGlideUp .34s cubic-bezier(.22,.61,.36,1) both}.bankArea.bankOpen #bankContent{animation:bankContentGlide .24s cubic-bezier(.22,.61,.36,1) both;transform-origin:top center}@keyframes dbTitleGlideUp{0%{transform:translateY(clamp(18px,var(--db-title-start-y,42px),44px));opacity:.72}100%{transform:translateY(0);opacity:1}}@keyframes bankContentGlide{0%{opacity:.68;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}
    .editorSheet{padding:18px 16px calc(22px + env(safe-area-inset-bottom));scroll-padding-bottom:24px}.editorHeader{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.editorHeader h2{margin:0}.editorDeleteBtn{width:44px;height:44px;min-width:44px;padding:0;border:1px solid rgba(226,59,84,.24);border-radius:14px;background:#fff5f7;display:grid;place-items:center;font-size:21px;box-shadow:0 4px 12px rgba(226,59,84,.10)}.editorSheet .field{margin:7px 0}.editorSheet .notice{margin-top:12px}.editorMediaBox{display:grid;gap:10px}.editorMediaHead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.editorMediaStatus{display:block;color:var(--muted);font-size:13px;font-weight:800;margin-top:3px}.editorMediaPreview{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#f6f8fb;min-height:96px;display:grid;place-items:center;color:var(--muted);font-size:13px;font-weight:800}.editorMediaPreview img{width:100%;max-height:180px;object-fit:cover;display:block}.editorMediaActions{display:grid;grid-template-columns:1fr auto;gap:8px}.editorMediaActions button{min-height:48px}.editorAdvanced{padding:13px 12px}.editorAdvanced summary{min-height:34px;display:flex;align-items:center}.editorAdvancedGrid{grid-template-columns:1fr;margin-top:12px}.editorActions{display:grid;grid-template-columns:1fr;gap:10px;margin-top:12px}.editorActions button,.editorCancelBtn{min-height:52px}.editorCancelBtn{width:100%;margin-top:10px}
    @media (min-width:760px){body{align-items:flex-start}.app{width:min(100%,960px);padding:20px 22px 76px;display:grid;grid-template-columns:minmax(260px,330px) minmax(420px,1fr);gap:14px;align-items:start}.topbar{grid-column:1/-1;margin:-20px -22px 0;padding:12px 22px}.scanHub{grid-column:1;position:sticky;top:76px;margin:0}.panel{grid-column:2;margin:0}.bottomPad{grid-column:1/-1;height:70px}.footerActions{width:min(100%,960px)}.modal{align-items:center}.sheet{width:min(92vw,620px);border-radius:24px}}
    @media (min-width:760px){
      body{align-items:flex-start}
      .app{width:min(100%,1180px);padding:18px;display:grid;grid-template-columns:1fr;grid-template-rows:auto auto 1fr;gap:14px;align-items:stretch}
      .scanHub{grid-column:1;position:static;top:auto;margin:0;display:grid;grid-template-columns:minmax(180px,1fr) minmax(180px,1fr);gap:10px;align-items:center;padding:12px;border-radius:22px}
      .scanHub .scanBtn,.scanHub .scanMeta{height:58px;min-height:58px;display:flex;align-items:center;justify-content:center}
      .scanHub .scanMeta{border-top:0;margin:0;padding:0 14px;background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);font-size:18px;color:var(--ink)}
      .scanHub .scanMeta small{display:inline;margin:0 0 0 8px;font-size:12px;color:var(--muted)}
      .adminMode .scanHub{grid-template-columns:minmax(180px,1fr) minmax(180px,1fr) minmax(150px,.7fr) minmax(190px,.9fr)}
      .adminMode .scanHub .adminConfigBtn,.adminMode .scanHub .sharedBankBtn{display:flex;margin:0;height:58px;align-items:center;justify-content:center}
      .scanHub #scanPreview{grid-column:1/-1;margin:0}
      .panel{grid-column:1;margin:0;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:12px}
      .planHeader{margin:0}
      .planHeader .panelTitle{font-size:30px}
      .panel .inner{display:grid;grid-template-columns:minmax(360px,430px) minmax(0,1fr);grid-template-rows:auto auto auto auto minmax(0,1fr);gap:10px 14px;align-items:start;min-height:560px}
      #baseToggle{grid-column:1/-1;grid-row:1}
      #baseFields{grid-column:1/-1;grid-row:2}
      #inputLabel{grid-column:1;grid-row:3;margin:0}
      #dbTitle{grid-column:1;grid-row:4}
      #inputWrap{grid-column:1;grid-row:5}
      #bankArea{grid-column:1;grid-row:6;min-width:0}
      #currentPlanBlock{grid-column:2;grid-row:3/7;align-self:stretch;min-width:0;border:1px solid var(--line);border-radius:18px;background:#fbfdff;padding:12px;box-shadow:var(--shadow)}
      #currentPlanBlock.hidden{display:block!important;visibility:hidden;pointer-events:none}
      #currentPlanBlock .label{margin-top:0;font-size:16px}
      #planList{max-height:530px;overflow:auto;padding-right:2px}
      #exerciseInput{min-height:118px}
      .bankArea.bankOpen #bankContent{margin-top:8px}
      .bankRows{max-height:420px}
      .tools{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,.48fr);gap:10px;margin-top:0}
      .planActions{grid-column:1;min-height:58px}
      #recentList{grid-column:1/-1}
      #packageToggle{grid-column:2;grid-row:1;height:58px;min-height:58px}
      #packageList{grid-column:1/-1}
      .bottomPad{grid-column:1;height:12px}
      .footerActions{width:min(100%,1180px)}
      .modal{align-items:center}
      .sheet{width:min(92vw,620px);border-radius:24px}
    }
    @media (min-width:760px){
      .app{min-height:100vh}
      .scanHub{grid-template-columns:minmax(190px,.9fr) minmax(190px,.9fr);align-self:start}
      .panel{min-height:calc(100vh - 124px)}
      .panel .inner{grid-template-columns:minmax(380px,440px) minmax(0,1fr);grid-template-rows:auto auto auto auto auto minmax(0,1fr);min-height:0;height:min(72vh,690px);align-content:start}
      #baseFields:not(.hidden){display:grid;grid-template-columns:1fr 1fr;gap:10px}
      #baseFields .field{margin:0}
      #baseFields .field:last-child{grid-column:1/-1}
      #inputWrap{min-height:0;align-self:start}
      #exerciseInput{min-height:112px;max-height:190px}
      #bankArea{align-self:stretch;overflow:hidden}
      #bankArea.bankOpen{max-height:100%;display:flex;flex-direction:column}
      #bankArea.bankOpen #bankContent{flex:1;min-height:0}
      .bankRows{max-height:360px}
      #bankArea.bankOpen .bankRows{max-height:none;flex:1;min-height:0;overflow:auto}
      #currentPlanBlock{display:block!important;min-height:0;overflow:hidden}
      #currentPlanBlock.hidden{visibility:hidden;pointer-events:none}
      #planList{max-height:calc(100dvh - 300px);overflow:auto}
      .planCard{padding:12px 14px}
      .planCard b{font-size:18px}
      .planActions.hasPlan{grid-template-columns:minmax(220px,1fr) 66px}
      .planActions.hasPlan #recentToggle{width:66px;min-width:66px}
      #packageToggle{justify-content:center}
      #recentList,#packageList{max-height:220px;overflow:auto}
    }
    .planCard[data-plan-id]{touch-action:pan-y;overflow:hidden}
    .planCard.swipe-dragging{transition:none;will-change:transform,opacity,box-shadow;box-shadow:0 8px 22px rgba(7,16,39,.14)}
    .planCard.swipe-armed{background:#fffafa;box-shadow:0 0 0 2px rgba(226,59,84,.18),0 14px 34px rgba(7,16,39,.2)}
    .planCard.swipe-removing{pointer-events:none}
    .planCard.swipe-dragging::after{content:"Löschen";position:absolute;top:50%;transform:translateY(-50%);padding:6px 10px;border-radius:999px;background:rgba(226,59,84,.1);color:#b01830;font-size:12px;font-weight:1000;opacity:var(--swipe-strength,0)}
    .planCard.swipe-left::after{right:14px}.planCard.swipe-right::after{left:14px}
    .bankRow[data-bank-id]{touch-action:pan-y;overflow:hidden;position:relative}
    .bankRow.bank-swipe-dragging{transition:none;will-change:transform,opacity,box-shadow;box-shadow:0 8px 20px rgba(7,16,39,.12);z-index:1}
    .bankRow.bank-swipe-armed{background:#fffafa;box-shadow:0 0 0 2px rgba(226,59,84,.18),0 10px 26px rgba(7,16,39,.16)}
    .bankRow.bank-swipe-dragging::after{content:"Löschen";position:absolute;top:50%;transform:translateY(-50%);padding:5px 9px;border-radius:999px;background:rgba(226,59,84,.1);color:#b01830;font-size:11px;font-weight:1000;opacity:var(--bank-swipe-strength,0)}
    .bankRow.bank-swipe-left::after{right:12px}.bankRow.bank-swipe-right::after{left:12px}
    .topbar{display:flex;align-items:center;justify-content:space-between;gap:10px}.topbarText{min-width:0}.visionBtn{flex:0 0 auto;border:2px solid #071027;background:#fff;color:#071027;border-radius:14px;padding:9px 12px;font-weight:1000;font-size:17px;line-height:1;min-width:48px}
    body.a11y{--bg:#fff;--paper:#fff;--ink:#000;--muted:#172033;--line:#111;--blue:#e9f4ff;--blue2:#f6fbff;--accent:#000;--danger:#b00020;--shadow:none}
    body.a11y .app{width:min(100%,640px);padding-bottom:18px}body.a11y .topbar{background:#fff;border-bottom:2px solid #111}body.a11y .topbar h1{font-size:23px;line-height:1.12}body.a11y .topbar small{font-size:15px;color:#111}body.a11y .stateBadge{font-size:15px;border-radius:10px}
    body.a11y .scanBtn,body.a11y .primary,body.a11y .mutedBtn,body.a11y .drawerBtn,body.a11y .baseCard{font-size:20px;min-height:52px;border-width:2px}body.a11y .panelTitle{font-size:34px;line-height:1.08;letter-spacing:0}body.a11y .label{font-size:18px}body.a11y textarea{font-size:24px;line-height:1.45;min-height:92px}body.a11y .suggestion{font-size:22px}body.a11y .suggestion small{font-size:15px}
    body.a11y .planCard{border:2px solid #111;padding:14px;grid-template-columns:1fr}body.a11y .planCard b{font-size:23px}body.a11y .planCard small{font-size:19px;color:#111;line-height:1.35}body.a11y .planCard .drag{width:44px;height:44px;font-size:24px}body.a11y .iconBtn{font-size:25px;min-width:44px;min-height:44px}
    body.a11y .field label{font-size:17px;color:#111}body.a11y .field input,body.a11y .field select{font-size:21px;min-height:52px;border:2px solid #111}body.a11y .notice,body.a11y .apiBox{font-size:18px;line-height:1.35;border:2px solid #111;color:#111}body.a11y .footerActions{position:static;left:auto;bottom:auto;transform:none;width:100%;grid-template-columns:1fr;margin-top:10px;background:#fff;border-top:2px solid #111}body.a11y .bottomPad{height:12px}
    .adminTestBanner{grid-column:1/-1;background:#fff8e8;border:2px solid #b88700;border-radius:16px;padding:10px 12px;margin:0 0 10px;color:#3d2a00;font-weight:900;box-shadow:var(--shadow)}.adminTestBanner small{display:block;margin-top:3px;color:#6a4c00;font-weight:800}
    .kggBuildBadge{display:block;margin-top:4px;color:#536273;font-size:10px;line-height:1.25;font-weight:850;word-break:break-word}
    @media (min-width:760px){
      body{align-items:flex-start;padding:18px;background:#e8eef6}
      .app{width:min(100%,1180px);height:calc(100vh - 36px);min-height:640px;background:#f7f9fc;border:3px solid #111827;border-radius:34px;box-shadow:0 20px 60px rgba(7,16,39,.18);padding:18px;display:grid;grid-template-columns:minmax(360px,430px) minmax(0,1fr) 160px;grid-template-rows:auto 68px minmax(126px,auto) minmax(0,1fr) 64px;gap:14px;align-items:stretch;overflow:hidden}
      .scanHub{grid-column:1;grid-row:2;margin:0;padding:0;background:transparent;border:0;box-shadow:none;display:grid;grid-template-columns:1fr 1fr;gap:10px;min-width:0}
      .scanHub .scanBtn,.scanHub .scanMeta{height:100%;min-height:0;margin:0;display:flex;align-items:center;justify-content:center;border-radius:16px;font-size:17px}
      .scanHub .scanMeta{border:1px solid var(--line);padding:0 12px;background:#fff;box-shadow:var(--shadow);color:var(--ink);border-top:1px solid var(--line)}
      .scanHub .scanMeta small{display:none}
      .scanHub input.hidden{display:none!important}
      .scanHub #scanPreview{grid-column:1/-1;margin:0}
      .adminMode .scanHub{grid-template-columns:1fr 1fr;grid-auto-rows:68px}
      .adminMode .scanHub .adminConfigBtn,.adminMode .scanHub .sharedBankBtn{display:flex;margin:0;height:68px;align-items:center;justify-content:center;border-radius:16px}
      .panel,.panel .inner,.tools{display:contents}
      .planHeader{display:contents}
      .planHeader .panelTitle{grid-column:2/4;grid-row:1;font-size:30px;margin:0;line-height:1.05;align-self:end}
      #savePackageBtn{grid-column:3;grid-row:2;align-self:stretch;width:100%;height:68px;min-height:68px;border-radius:18px}
      #savePackageBtn.hidden{display:block!important;visibility:hidden;pointer-events:none}
      #baseToggle{grid-column:2;grid-row:2;height:68px;min-height:68px;border-radius:18px;font-size:21px;box-shadow:var(--shadow)}
      #baseFields{grid-column:1/4;grid-row:2;background:#fff;border:1px solid var(--line);border-radius:18px;padding:12px;box-shadow:var(--shadow);z-index:4}
      #baseFields.hidden{display:none!important}
      #inputLabel{grid-column:1;grid-row:1;margin:0;align-self:end;font-size:20px;line-height:1;font-weight:1000}
      #dbTitle{grid-column:1;grid-row:1;margin:0;align-self:end}
      #inputWrap{grid-column:1;grid-row:3;align-self:stretch;border-radius:20px}
      #exerciseInput{min-height:126px;max-height:190px;font-size:22px}
      #bankArea{grid-column:1;grid-row:4;align-self:stretch;min-height:0;overflow:hidden;background:#fff;border-radius:20px}
      #bankArea.bankOpen{display:flex;flex-direction:column;overflow:hidden;border:2px solid #111827;box-shadow:var(--shadow);padding:10px;height:100%;min-height:0}
      #bankArea.bankOpen #bankContent{flex:1;min-height:0;margin-top:8px}
      #bankArea.bankOpen .bankRows{max-height:none;height:100%}
      #bankArea:not(.bankOpen) .drawerBtn{height:64px;min-height:64px;border:2px solid #111827;border-radius:20px;font-size:20px}
      #currentPlanBlock{grid-column:2/4;grid-row:3/5;align-self:start;min-height:38vh;min-width:0;background:#fff;border:2px solid #111827;border-radius:24px;box-shadow:var(--shadow);padding:14px;overflow:hidden}
      #currentPlanBlock.hidden{display:block!important;visibility:hidden;pointer-events:none}
      #currentPlanBlock .label{margin:0 0 12px;font-size:20px;line-height:1;font-weight:1000}
      #planList{max-height:calc(100dvh - 310px);overflow:auto;padding-right:2px}
      .planCard{border-radius:18px;padding:12px 14px;grid-template-columns:minmax(0,1fr) auto}
      .planCard b{font-size:20px}
      .planCard small{font-size:14px}
      .planActions{grid-column:2;grid-row:5;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:14px;align-self:stretch}
      .planActions:not(.hasPlan){grid-template-columns:1fr}
      .planActions:not(.hasPlan) #finishBtn.hidden{display:none!important}
      #createPanel:not(.planMode) #recentToggle,#createPanel:not(.planMode) #packageToggle{height:64px;min-height:64px;width:100%;box-sizing:border-box;align-self:stretch}
      #finishBtn{grid-column:auto;grid-row:auto;height:64px;min-height:64px;margin:0;border-radius:18px;font-size:22px}
      #finishBtn.hidden{display:block!important;visibility:hidden;pointer-events:none;padding-left:0;padding-right:0;border-width:0}
      #recentToggle{grid-column:auto;grid-row:auto;height:64px;min-height:64px;border-radius:18px;justify-content:center}
      #packageToggle{grid-column:3;grid-row:5;height:64px;min-height:64px;border-radius:18px;justify-content:center}
      #createPanel:not(.planMode) .planActions{grid-column:2/4;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
      #createPanel:not(.planMode) #recentToggle{grid-column:1;width:100%}
      #createPanel:not(.planMode) #packageToggle{grid-column:2/4;grid-row:5;justify-self:end;width:calc(50% - 7px)}
      #createPanel.planMode .planHeader .panelTitle{grid-column:2;grid-row:1}
      #createPanel.planMode .planActions{display:contents}
      #createPanel.planMode #finishBtn{grid-column:3;grid-row:1;align-self:end;justify-self:stretch;width:100%;height:54px;min-height:54px;border-radius:18px;font-size:20px;opacity:1;scale:1 1;animation:none}
      #createPanel.planMode #recentToggle{grid-column:2;grid-row:5;width:100%;min-width:0}
      #createPanel.planMode #packageToggle{grid-column:3;grid-row:5;width:100%}
      .planActions.hasPlan #recentToggle{width:auto;min-width:0;padding:10px 12px}
      #createPanel.planMode #recentToggle{width:100%;justify-self:stretch}
      .planActions.hasPlan .recentText,.planActions.hasPlan .recentMini{max-width:none;opacity:1}
      #recentList,#packageList{grid-row:4/5;align-self:end;z-index:28;max-height:min(42vh,360px);overflow:auto;background:rgba(255,255,255,.96);border:1px solid rgba(220,227,235,.92);border-radius:22px;padding:10px;box-shadow:0 18px 48px rgba(7,16,39,.18),0 4px 14px rgba(7,16,39,.08);backdrop-filter:blur(10px);transform-origin:bottom center;animation:tabletDrawerRise .28s cubic-bezier(.18,.84,.24,1) both}
      #recentList{grid-column:2}
      #packageList{grid-column:2/4}
      #recentList.hidden,#packageList.hidden{display:none!important}
      #recentList .notice,#packageList .notice{margin-top:0}
      @keyframes tabletDrawerRise{0%{opacity:0;transform:translateY(22px) scale(.96);filter:blur(2px)}70%{opacity:1;transform:translateY(-4px) scale(1.01);filter:blur(0)}100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}
      .bottomPad{display:none}
      .footerActions{display:none!important}
      .modal{align-items:center}
      .sheet{width:min(92vw,620px);border-radius:24px}
      .app.softKeyboard{height:calc(var(--kgg-visual-vh,100vh) - 20px);min-height:0;padding:12px;gap:10px;grid-template-rows:auto 56px minmax(82px,auto) minmax(0,1fr)}
      .app.softKeyboard .scanHub{gap:8px}
      .app.softKeyboard .scanHub .scanBtn,.app.softKeyboard .scanHub .scanMeta{font-size:15px;border-radius:14px}
      .app.softKeyboard .planHeader .panelTitle{font-size:26px}
      .app.softKeyboard #baseToggle,.app.softKeyboard #savePackageBtn{height:56px;min-height:56px;border-radius:15px}
      .app.softKeyboard #inputLabel,.app.softKeyboard #dbTitle{font-size:18px}
      .app.softKeyboard #inputWrap{border-radius:16px}
      .app.softKeyboard #exerciseInput{min-height:82px;max-height:120px;font-size:20px;line-height:1.25;padding-top:12px;padding-bottom:12px}
      .app.softKeyboard #bankArea{grid-row:4;min-height:0}
      .app.softKeyboard #bankArea.bankOpen{padding:8px;height:100%;min-height:0}
      .app.softKeyboard #bankArea.bankOpen #bankContent,.app.softKeyboard #bankArea.bankOpen .bankWithAz{height:100%;min-height:0}
      .app.softKeyboard #bankArea.bankOpen.alphaBankOpen .az{display:flex;flex-direction:column;height:calc(100% - 58px);margin-top:58px;padding:2px 0}
      .app.softKeyboard #bankArea.bankOpen.alphaBankOpen .az button{flex:1 1 0;min-height:0;font-size:10px;line-height:1}
      .app.softKeyboard .bankRow{padding:8px 10px}
      .app.softKeyboard .bankRow b{font-size:14px}
      .app.softKeyboard .bankRow small{font-size:10px}
      .app.softKeyboard #currentPlanBlock{padding:10px;border-radius:20px}
```
