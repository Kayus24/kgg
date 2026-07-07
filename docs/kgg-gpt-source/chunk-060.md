# KGG Source Chunk 060

- Source: `kgg-update/index.html`
- Lines: 25201-25620

```html
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
    });

    window.addEventListener("resize", function(){
      if(!isPhone()) hardClean("leave-phone-resize");
      else scheduleClean("phone-resize", 160);
    }, {passive:true});

    window.addEventListener("orientationchange", function(){
      setTimeout(function(){
        if(!isPhone()) hardClean("leave-phone-orientation");
        else scheduleClean("phone-orientation", 220);
      }, 120);
    }, {passive:true});

    if(window.visualViewport){
      window.visualViewport.addEventListener("resize", function(){
        if(!isPhone()) hardClean("leave-phone-visualViewport");
        else scheduleClean("phone-visualViewport", 160);
      }, {passive:true});
    }

    if(window.matchMedia){
      try{
        var mq = window.matchMedia(PHONE_QUERY);
        var onChange = function(ev){
          if(!ev.matches) hardClean("matchMedia-leave-phone");
          else scheduleClean("matchMedia-enter-phone", 120);
        };
        if(mq.addEventListener) mq.addEventListener("change", onChange);
        else if(mq.addListener) mq.addListener(onChange);
      }catch(err){}
    }

    var mo = new MutationObserver(function(){
      if(!isPhone()){
        if(hasLivePlanGesture()) return;
        var b = body();
        if(b && (
          b.classList.contains("kggPlanCardReordering") ||
          b.classList.contains("kggPlanCardSwiping") ||
          b.classList.contains("kggPlanSectionFrozen") ||
          b.classList.contains("phoneTextFocus") ||
          b.classList.contains("kggPhoneDrawerOpen")
        )){
          hardClean("mutation-leave-phone");
        }
      }
    });

    if(body()) mo.observe(body(), {attributes:true, attributeFilter:["class"]});

    window.addEventListener("pagehide", function(){ hardClean("pagehide"); }, {passive:true});
    scheduleClean("boot", 260);
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", install, {once:true});
  }else{
    install();
  }
})();
</script>

<script id="kgg-v014-local-update-release-marker">
(function(){
  "use strict";
  window.KGG_V014_PHONE_VIEWPORT_STATE_RELEASE_GUARD = {
    patchId: "kgg-v014-phone-viewport-state-release-guard",
    confirms: [
      "phone-only gesture code remains gated by matchMedia('(max-width:759px)')",
      "stale phone classes and inline styles are cleaned when leaving phone viewport",
      "phone drag reorder stays absolute inside #planList instead of position:fixed",
      "global tablet layout containers are not overridden outside max-width:759px",
      "content://, file:// and /media/external/file/ local tests do not auto-redirect to GitHub",
      "KGGReleaseControl local fallback is kept and native bridge is not overwritten"
    ]
  };
})();
</script>
<!-- KGG PATCH END kgg-v014-phone-viewport-state-release-guard -->

<!-- KGG v13 marker: Update-Zentrale initialization fixed without changing phone/tablet touch behavior -->
<script id="kgg-v13-update-zentrale-marker">
(function(){
  "use strict";
  window.KGG_UPDATE_ZENTRALE_V13 = {
    patchId: "kgg-v13-release-control-local-fallback",
    base: "KGG_CURRENT_ADMIN_HTML_v12_features_restored_phone_fixed.html",
    changes: [
      "Defines a safe KGGReleaseControl fallback before kgg-release-center-v28-script runs",
      "Allows KGGReleaseCenter to initialize in content://, file:// and normal browser test mode",
      "Does not override the native Admin-APK/GitHub bridge when it exists",
      "Does not change phone drag, tablet layout, QR, PDF, Scan, Parser, Storage or Plan-State"
    ]
  };
})();
</script>

<!-- KGG PATCH START kgg-v041-ui-mini-series -->
<style id="kgg-v041-ui-mini-series-style">
  .bankAddBtn{display:flex!important;align-items:center;gap:10px;text-align:left;width:100%;min-width:0}
  .bankText{display:grid;min-width:0}
  .bankText b{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .bankThumb{position:relative;display:inline-block;flex:0 0 42px;width:42px;height:42px;border:1px solid rgba(7,16,39,.24);border-radius:7px;background:#f6f7f9;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,255,255,.7)}
  .bankThumb img{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1) contrast(1.05)}
  .bankThumbFallback::before{content:"";position:absolute;inset:0;background:linear-gradient(135deg,#fff 0 48%,#111 49% 51%,#fff 52% 100%);opacity:.72}
  .bankThumbFallback::after{content:"";position:absolute;inset:9px;border:2px solid rgba(17,24,39,.42);border-radius:5px}
  .kggPhoneAdminMenu,.phonePhotoMenuToggle,.kggPhonePhotoMenu{display:none}

  @media(max-width:759px){
    body.adminMode .kggPhoneAdminMenu{display:block;position:fixed;right:12px;top:max(10px,calc(env(safe-area-inset-top) + 8px));z-index:1450}
    .kggPhoneAdminMenuBtn{width:44px;height:44px;min-width:44px;min-height:44px;border:1px solid rgba(7,16,39,.18);border-radius:14px;background:#fff;color:#071027;font-size:24px;font-weight:1000;line-height:1;box-shadow:0 10px 24px rgba(7,16,39,.16);display:grid;place-items:center}
    .kggPhoneAdminMenuPanel{position:absolute;right:0;top:52px;min-width:224px;background:#fff;border:1px solid rgba(7,16,39,.18);border-radius:14px;box-shadow:0 18px 38px rgba(7,16,39,.22);padding:8px;display:grid;gap:6px}
    .kggPhoneAdminMenuPanel[hidden]{display:none!important}
```
