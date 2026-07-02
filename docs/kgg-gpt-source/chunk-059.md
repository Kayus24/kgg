# KGG Source Chunk 059

- Source: `kgg-update/index.html`
- Lines: 24781-25200

```html
  }

  /* Drag-reorder over the handle remains the tablet-style lifted card behavior. */
  body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-lifted,
  body.is-scrolling.kggPlanCardReordering #currentPlanBlock .planCard.reorder-lifted{
    transform:translateY(var(--drag-y,0px)) scale(1.035)!important;
    transition:none!important;
    will-change:transform!important;
    pointer-events:none!important;
    z-index:9999!important;
  }
}
</style>

<script id="kgg-phone-touch-tablet-parity-hard-v3-js">
(function(){
  'use strict';

  var PATCH_ID='kgg-phone-touch-tablet-parity-hard-v3';
  var PHONE_QUERY='(max-width:759px)';
  var installed=false;
  var originalClassListAdd=null;

  function isPhone(){
    return !!(window.matchMedia && window.matchMedia(PHONE_QUERY).matches);
  }

  function isBodyClassList(list){
    return !!(document.body && list === document.body.classList);
  }

  function currentPlanBlock(){
    return document.getElementById('currentPlanBlock');
  }

  function isInsidePlanCard(target){
    return !!(target && target.closest && target.closest('#currentPlanBlock .planCard'));
  }

  function cleanFreeze(){
    var body=document.body;
    var block=currentPlanBlock();

    if(body && body.classList.contains('kggPlanSectionFrozen')){
      body.classList.remove('kggPlanSectionFrozen');
    }

    if(block){
      block.style.removeProperty('--kgg-current-plan-freeze-h');
      block.style.removeProperty('height');
      block.style.removeProperty('min-height');
      block.style.removeProperty('max-height');
    }
  }

  function cleanScrollFlag(){
    if(document.body){
      document.body.classList.remove('is-scrolling');
    }
  }

  function cleanStaleGestureClasses(){
    if(!document.body || !isPhone()) return;

    var liveSwipe=document.querySelector('#currentPlanBlock .planCard.swipe-dragging,#currentPlanBlock .planCard.swipe-removing');
    var liveReorder=document.querySelector('#currentPlanBlock .planCard.reorder-lifted');

    if(!liveSwipe){
      document.body.classList.remove('kggPlanCardSwiping');
    }

    if(!liveReorder){
      document.body.classList.remove('kggPlanCardReordering');
    }

    cleanFreeze();
  }

  function installClassListFreezeBlock(){
    if(originalClassListAdd || !window.DOMTokenList || !DOMTokenList.prototype) return;

    originalClassListAdd=DOMTokenList.prototype.add;

    DOMTokenList.prototype.add=function(){
      var args=Array.prototype.slice.call(arguments);

      try{
        if(isPhone() && isBodyClassList(this) && args.indexOf('kggPlanSectionFrozen') !== -1){
          args=args.filter(function(token){ return token !== 'kggPlanSectionFrozen'; });
          setTimeout(cleanFreeze,0);
          if(!args.length) return undefined;
        }
      }catch(err){}

      return originalClassListAdd.apply(this,args);
    };
  }

  function disablePhoneScrollToggleForButtons(){
    /*
      These names are global in this single-file app. Assigning them here leaves
      every other feature intact but prevents phone drawer/buttons from being
      swallowed after a touch/scroll gesture.
    */
    try{
      if(typeof guardPhoneScrollToggle === 'function'){
        guardPhoneScrollToggle=function(){ return false; };
      }
    }catch(err){}

    try{
      if(typeof window.guardPhoneScrollToggle === 'function'){
        window.guardPhoneScrollToggle=function(){ return false; };
      }
    }catch(err){}
  }

  function installListeners(){
    if(installed || !document.body) return;
    installed=true;

    installClassListFreezeBlock();
    disablePhoneScrollToggleForButtons();

    /*
      Capture before document-level phone freeze side effects become visible.
      We do not stop propagation, so original swipe/delete/reorder handlers still run.
    */
    window.addEventListener('pointerdown',function(ev){
      if(!isPhone()) return;
      if(isInsidePlanCard(ev.target)){
        cleanScrollFlag();
        cleanFreeze();
        requestAnimationFrame(cleanFreeze);
      }
    },{capture:true,passive:true});

    window.addEventListener('pointermove',function(ev){
      if(!isPhone()) return;
      if(document.body && (
        document.body.classList.contains('kggPlanCardSwiping') ||
        document.body.classList.contains('kggPlanCardReordering')
      )){
        cleanScrollFlag();
        cleanFreeze();
      }
    },{capture:true,passive:true});

    ['pointerup','pointercancel','touchend','touchcancel'].forEach(function(type){
      window.addEventListener(type,function(){
        if(!isPhone()) return;
        cleanFreeze();
        setTimeout(cleanStaleGestureClasses,80);
        setTimeout(cleanStaleGestureClasses,260);
      },{capture:true,passive:true});
    });

    var observer=new MutationObserver(function(){
      if(!isPhone()) return;
      cleanFreeze();
    });

    observer.observe(document.body,{attributes:true,attributeFilter:['class']});

    window.addEventListener('resize',function(){
      setTimeout(cleanStaleGestureClasses,60);
    },{passive:true});

    window.addEventListener('orientationchange',function(){
      setTimeout(cleanStaleGestureClasses,140);
    },{passive:true});

    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',function(){
        setTimeout(cleanStaleGestureClasses,60);
      },{passive:true});
    }

    cleanStaleGestureClasses();

    window.KGG_PHONE_TOUCH_TABLET_PARITY_HARD_V3={
      patchId:PATCH_ID,
      scope:'phone-only max-width:759px',
      check:function(){
        return {
          patchId:PATCH_ID,
          phone:isPhone(),
          freezeBlocked:!!originalClassListAdd,
          bodyFrozen:!!(document.body && document.body.classList.contains('kggPlanSectionFrozen')),
          planFreezeHeight:currentPlanBlock() ? currentPlanBlock().style.getPropertyValue('--kgg-current-plan-freeze-h') : ''
        };
      },
      clean:cleanStaleGestureClasses
    };
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',installListeners,{once:true});
  }else{
    installListeners();
  }
})();
</script>
<!-- END KGG CLEAN MERGE v11 -->

<script id="kgg-v11-clean-merge-marker">
(function(){
  "use strict";
  window.KGG_PHONE_TOUCH_CLEAN_MERGE_V11={
    patchId:"kgg-v11-clean-merge-original-features-phone-drag-local-list",
    base:"KGG_CURRENT_ADMIN_HTML.html",
    keeps:"Original feature code, remote update prompt, QR/PDF/Scan/Parser/Storage/Plan-State/Admin",
    changes:[
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
```
