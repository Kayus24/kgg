# KGG Source Chunk 060

- Source: `kgg-update/src` modular source
- Lines: 25201-25620

```html
      "Phone drag-reorder uses #planList local absolute coordinates",
      "Phone plan freeze is neutralized only below 760px",
      "Local Android/content test files do not auto-redirect to GitHub; manifest prompt remains allowed"
    ]
  };
})();
</script>

<!-- KGG v12 FEATURE RESTORE: robust Update-Zentrale entrypoints; no touch/layout behavior changes -->
<script id="kgg-v12-release-center-entry-restore">
(function(){
  "use strict";
  var PATCH_ID = "kgg-v12-release-center-entry-restore";
  var installed = false;
  var observer = null;

  function byId(id){ return document.getElementById(id); }
  function q(sel){ try { return document.querySelector(sel); } catch(err){ return null; } }

  function releaseOpen(){
    try{
      if(window.KGGReleaseCenter && typeof window.KGGReleaseCenter.open === "function"){
        window.KGGReleaseCenter.open();
        return;
      }
    }catch(err){}
    try{
      if(window.KGGReleaseControl && typeof window.KGGReleaseControl.open === "function"){
        window.KGGReleaseControl.open();
        return;
      }
    }catch(err){}
    alert("Update-Zentrale ist im Code vorhanden, aber noch nicht initialisiert. Bitte App einmal neu laden.");
  }

  function makeButton(id, text, className){
    var btn = document.createElement("button");
    btn.id = id;
    btn.type = "button";
    btn.textContent = text;
    btn.className = className || "tabletSideMenuAction";
    btn.addEventListener("click", function(ev){
      ev.preventDefault();
      ev.stopPropagation();
      try{
        if(typeof closeTabletMenu === "function") closeTabletMenu();
      }catch(err){}
      releaseOpen();
    }, true);
    return btn;
  }

  function ensureTabletMenuEntry(){
    var menu = q(".tabletSideMenuMain");
    if(!menu) return false;

    var group = byId("kggReleaseMenuGroup");
    if(!group){
      group = document.createElement("div");
      group.id = "kggReleaseMenuGroup";
      group.className = "tabletSideMenuGroup kggReleaseMenuGroup";
      group.innerHTML = "<h3>Admin</h3>";
      menu.appendChild(group);
    }

    if(!byId("kggReleaseAdminConfig")){
      var admin = document.createElement("button");
      admin.id = "kggReleaseAdminConfig";
      admin.type = "button";
      admin.className = "tabletSideMenuAction";
      admin.textContent = "Admin-Konfig";
      admin.addEventListener("click", function(ev){
        ev.preventDefault();
        ev.stopPropagation();
        try{
          if(typeof closeTabletMenu === "function") closeTabletMenu();
        }catch(err){}
        var target = byId("adminConfigBtn");
        if(target) target.click();
      }, true);
      group.appendChild(admin);
    }

    if(!byId("kggReleaseCenterOpen")){
      group.appendChild(makeButton("kggReleaseCenterOpen", "Update-Zentrale", "tabletSideMenuAction"));
    }

    return true;
  }

  function ensurePhoneAdminEntry(){
    var tools = q(".adminCodePackageTools");
    if(!tools) return false;
    if(!byId("kggReleaseCenterOpenPhone")){
      var phone = makeButton("kggReleaseCenterOpenPhone", "Update-Zentrale", "mutedBtn wide");
      tools.appendChild(phone);
    }
    return true;
  }

  function ensureFallbackGlobal(){
    window.KGG_UPDATE_ZENTRALE_RESTORE = window.KGG_UPDATE_ZENTRALE_RESTORE || {};
    window.KGG_UPDATE_ZENTRALE_RESTORE.open = releaseOpen;
    window.KGG_UPDATE_ZENTRALE_RESTORE.install = install;
    window.KGG_UPDATE_ZENTRALE_RESTORE.status = function(){
      return {
        patchId: PATCH_ID,
        hasReleaseCenter: !!(window.KGGReleaseCenter && typeof window.KGGReleaseCenter.open === "function"),
        tabletButton: !!byId("kggReleaseCenterOpen"),
        phoneButton: !!byId("kggReleaseCenterOpenPhone"),
        tabletMenu: !!q(".tabletSideMenuMain"),
        phoneTools: !!q(".adminCodePackageTools")
      };
    };
  }

  function install(){
    ensureFallbackGlobal();
    var okTablet = ensureTabletMenuEntry();
    var okPhone = ensurePhoneAdminEntry();
    return okTablet || okPhone;
  }

  function scheduleInstall(){
    [0, 80, 180, 420, 900, 1600, 2800].forEach(function(ms){
      setTimeout(install, ms);
    });
  }

  function startObserver(){
    if(observer || !document.body) return;
    observer = new MutationObserver(function(){
      install();
    });
    observer.observe(document.body, {childList:true, subtree:true});
  }

  function boot(){
    if(installed) return;
    installed = true;
    install();
    scheduleInstall();
    startObserver();
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", boot, {once:true});
  }else{
    boot();
  }

  window.addEventListener("resize", function(){ setTimeout(install, 80); }, {passive:true});
  window.addEventListener("orientationchange", function(){ setTimeout(install, 180); }, {passive:true});
})();
</script>
<!-- END KGG v12 FEATURE RESTORE -->


<!-- KGG PATCH START kgg-v014-phone-viewport-state-release-guard -->
<style id="kgg-v014-phone-viewport-state-release-guard-css">
  /*
    v014: final phone-only gesture placement guard.
    - Phone drag cards are absolute inside #planList, not viewport fixed.
    - Scope is only max-width:759px so tablet layout containers are untouched.
  */
  @media (max-width:759px){
    body.kggPlanCardReordering #currentPlanBlock #planList.planList > .planCard.reorder-lifted{
      position:absolute!important;
      right:auto!important;
      bottom:auto!important;
      margin:0!important;
      transform:translate3d(0,0,0)!important;
      transition:none!important;
      will-change:left,top!important;
      pointer-events:none!important;
      z-index:9999!important;
    }

    body.kggPlanCardReordering #currentPlanBlock #planList.planList{
      position:relative;
    }

    body.kggPlanCardReordering #currentPlanBlock .planSectionBody{
      overflow:auto!important;
      touch-action:pan-y!important;
    }
  }
</style>

<script id="kgg-v014-phone-viewport-state-release-guard-js">
(function(){
  "use strict";

  var PATCH_ID = "kgg-v014-phone-viewport-state-release-guard";
  var PHONE_QUERY = "(max-width:759px)";
  var cleanupTimer = 0;

  function isPhone(){
    return !!(window.matchMedia && window.matchMedia(PHONE_QUERY).matches);
  }

  function body(){
    return document.body || null;
  }

  function planList(){
    return document.getElementById("planList");
  }

  function currentPlanBlock(){
    return document.getElementById("currentPlanBlock");
  }

  function hasLivePlanGesture(){
    return !!document.querySelector(
      "#currentPlanBlock .planCard.reorder-lifted," +
      "#currentPlanBlock .planCard.swipe-dragging," +
      "#currentPlanBlock .planCard.swipe-removing," +
      "#currentPlanBlock .planCard.reorder-prelift"
    );
  }

  function removeStyleProps(el, props){
    if(!el || !el.style) return;
    props.forEach(function(prop){
      try{ el.style.removeProperty(prop); }catch(err){}
    });
  }

  function cleanPlanCardInlineState(){
    var cards = document.querySelectorAll(
      "#currentPlanBlock .planCard," +
      "#planList .planCard," +
      ".planCard.reorder-lifted," +
      ".planCard.reorder-prelift," +
      ".planCard.swipe-dragging," +
      ".planCard.swipe-removing"
    );

    Array.prototype.forEach.call(cards, function(card){
      card.classList.remove(
        "reorder-lifted",
        "reorder-prelift",
        "reorder-gap-before",
        "reorder-gap-after",
        "swipe-dragging",
        "swipe-armed",
        "swipe-left",
        "swipe-right",
        "swipe-removing"
      );

      removeStyleProps(card, [
        "--drag-left",
        "--drag-top",
        "--drag-y",
        "--kgg-plan-swipe-x",
        "--swipe-strength",
        "position",
        "left",
        "top",
        "right",
        "bottom",
        "margin",
        "width",
        "transform",
        "transform-origin",
        "opacity",
        "transition",
        "will-change",
        "z-index",
        "filter"
      ]);
    });

    Array.prototype.forEach.call(document.querySelectorAll("#planList .reorder-placeholder"), function(ph){
      try{ ph.remove(); }catch(err){
        if(ph.parentNode) ph.parentNode.removeChild(ph);
      }
    });

    Array.prototype.forEach.call(document.querySelectorAll(".drag.reorder-armed"), function(handle){
      handle.classList.remove("reorder-armed");
    });
  }

  function cleanPlanContainerInlineState(){
    var block = currentPlanBlock();
    var list = planList();

    if(block){
      removeStyleProps(block, [
        "--kgg-current-plan-freeze-h",
        "height",
        "min-height",
        "max-height",
        "overflow",
        "contain"
      ]);
    }

    if(list){
      list.classList.remove("reorder-active");
      /*
        The phone drag code temporarily sets #planList to position:relative.
        If a resize/orientation interrupts cleanup, remove that inline value so
        tablet layout uses stylesheet rules again.
      */
      removeStyleProps(list, [
        "position",
        "overflow",
        "contain",
        "transform",
        "isolation"
      ]);
    }

    Array.prototype.forEach.call(document.querySelectorAll("#currentPlanBlock .planSectionBody"), function(section){
      removeStyleProps(section, [
        "height",
        "min-height",
        "max-height",
        "overflow",
        "contain",
        "transform",
        "touch-action"
      ]);
    });
  }

  function cleanBodyState(){
    var b = body();
    if(!b) return;

    b.classList.remove(
      "kggPlanCardReordering",
      "kggPlanCardSwiping",
      "kggPlanSectionFrozen",
      "is-scrolling",
      "phoneTextFocus",
      "kggPhoneDrawerOpen",
      "kggPhoneDbBrowseMode"
    );

    Array.prototype.forEach.call(document.querySelectorAll(".phoneButtonFloat"), function(btn){
      btn.classList.remove("phoneButtonFloat");
    });
  }

  function hardClean(reason){
    /*
      If a resize/orientation interrupts an active original drag handler, ask the
      original pointercancel listener to close first. Otherwise its later pointerup
      could see a removed placeholder and reorder the plan unexpectedly.
    */
    if(hasLivePlanGesture()){
      try{
        document.dispatchEvent(new Event("pointercancel", {bubbles:true, cancelable:true}));
      }catch(err){
        try{
          var ev = document.createEvent("Event");
          ev.initEvent("pointercancel", true, true);
          document.dispatchEvent(ev);
        }catch(err2){}
      }
    }

    cleanBodyState();
    cleanPlanCardInlineState();
    cleanPlanContainerInlineState();

    window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14.lastClean = {
      reason: reason || "manual",
      at: new Date().toISOString(),
      phone: isPhone()
    };
  }

  function cleanIfSafe(reason){
    /*
      During an active pointer gesture, the original handlers own the live motion.
      This must also protect tablet/split-screen swipes; otherwise a pointercancel
      can erase the visible card translation before pointerup resolves it.
    */
    if(hasLivePlanGesture()) return;
    hardClean(reason);
  }

  function scheduleClean(reason, delay){
    clearTimeout(cleanupTimer);
    cleanupTimer = setTimeout(function(){
      cleanIfSafe(reason);
    }, Number.isFinite(delay) ? delay : 80);
  }

  function install(){
    window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14 = window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14 || {};
    window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14.patchId = PATCH_ID;
    window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14.clean = hardClean;
    window.KGG_PHONE_VIEWPORT_STATE_RELEASE_GUARD_V14.check = function(){
      var b = body();
      var block = currentPlanBlock();
      var list = planList();
      return {
        patchId: PATCH_ID,
        phone: isPhone(),
        bodyClasses: b ? b.className : "",
        hasLivePlanGesture: hasLivePlanGesture(),
        planFreezeHeight: block ? block.style.getPropertyValue("--kgg-current-plan-freeze-h") : "",
        planListInlinePosition: list ? list.style.getPropertyValue("position") : "",
        releaseFallback: !!(window.KGGReleaseControl && window.KGGReleaseControl.fallback),
        nativeReleaseBridge: !!(window.KGGReleaseControl && !window.KGGReleaseControl.fallback)
      };
    };

    ["pointerup","pointercancel","touchend","touchcancel"].forEach(function(type){
      window.addEventListener(type, function(){
        scheduleClean(type, 140);
        scheduleClean(type + ":late", 420);
      }, {capture:true, passive:true});
```
