# KGG Source Chunk 059

- Source: `kgg-update/index.html`
- Lines: 24781-25200

```html
      +'<button class="kggReleaseBtn soft" id="kggReleaseLogin" type="button" style="width:100%;margin-top:14px">Komfort: Mit GitHub verbinden</button>'
      +'<button class="kggReleaseBtn soft" id="kggReleaseTest" type="button" style="width:100%;margin-top:10px">Komfort: Verbindung testen</button>'
      +'<div class="kggReleaseGrid" style="margin-top:14px"><div class="kggReleaseField"><label for="kggReleaseId">Release-ID</label><input id="kggReleaseId" placeholder="z. B. r0391" autocomplete="off"></div><div class="kggReleaseField"><label for="kggReleaseVersion">Versionsname</label><input id="kggReleaseVersion" placeholder="Kurzer eindeutiger Name" autocomplete="off"></div><div class="kggReleaseField wide"><label for="kggReleaseNotes">Patch-Notiz</label><textarea id="kggReleaseNotes" placeholder="Was wurde geaendert? Keine Patientendaten oder Secrets."></textarea></div></div>'
      +'<div class="kggReleaseActions"><button class="kggReleaseBtn soft" id="kggReleaseUpload" type="button">Komfort: HTML direkt aus App hochladen</button><button class="kggReleaseBtn soft" id="kggReleasePromote" type="button">Komfort: Release-ID fuer Kolleg:innen freigeben</button><div class="kggReleaseActions two"><button class="kggReleaseBtn danger" id="kggReleaseRollbackAdmin" type="button">Admin-Rollback</button><button class="kggReleaseBtn danger" id="kggReleaseRollbackColleague" type="button">Kolleg:innen-Rollback</button></div></div>'
      +'</section>';
    document.body.appendChild(modal);
    document.getElementById('kggReleaseClose').onclick=close;
    document.getElementById('kggReleaseLogin').onclick=function(){window.KGGReleaseControl.beginLogin();startRefreshLoop();setTimeout(refresh,250);setTimeout(refresh,900);setTimeout(refresh,1800);};
    document.getElementById('kggReleaseCopyCode').onclick=function(){var code=(document.getElementById('kggReleaseCodeValue')||{}).textContent||'';if(code)copyText(code.trim());};
    document.getElementById('kggReleaseTest').onclick=function(){if(typeof window.KGGReleaseControl.testConnection==='function'){window.KGGReleaseControl.testConnection();startRefreshLoop();setTimeout(refresh,250);setTimeout(refresh,1200);}else{var message=document.getElementById('kggReleaseMessage');if(message)message.textContent='Bitte Admin-APK v392 installieren, dann ist der Verbindungstest verfuegbar.';}};
    document.getElementById('kggReleaseDownloadHtml').onclick=function(){if(typeof window.KGGReleaseControl.downloadCurrentHtml==='function'){window.KGGReleaseControl.downloadCurrentHtml();setTimeout(refresh,250);}else{var message=document.getElementById('kggReleaseMessage');if(message)message.textContent='Bitte Admin-APK v393 installieren, dann ist HTML speichern verfuegbar.';}};
    document.getElementById('kggReleaseMobileInbox').onclick=function(){if(typeof window.KGGReleaseControl.openMobileInbox==='function'){window.KGGReleaseControl.openMobileInbox();setTimeout(refresh,250);}else{openExternal(MOBILE_INBOX_URL);}};
    document.getElementById('kggReleasePromoteLatest').onclick=function(){if(typeof window.KGGReleaseControl.openPromoteLatest==='function'){window.KGGReleaseControl.openPromoteLatest();setTimeout(refresh,250);}else{openExternal(MOBILE_PROMOTE_URL);}};
    document.getElementById('kggReleaseUpload').onclick=function(){window.KGGReleaseControl.chooseAndUploadBeta(value('kggReleaseId'),value('kggReleaseVersion'),value('kggReleaseNotes'));setTimeout(refresh,250);};
    document.getElementById('kggReleasePromote').onclick=function(){window.KGGReleaseControl.confirmPromotion(value('kggReleaseId'));};
    document.getElementById('kggReleaseRollbackAdmin').onclick=function(){window.KGGReleaseControl.confirmRollback('admin',value('kggReleaseId'));};
    document.getElementById('kggReleaseRollbackColleague').onclick=function(){window.KGGReleaseControl.confirmRollback('colleague',value('kggReleaseId'));};
    modal.addEventListener('click',function(ev){if(ev.target===modal)close();});
    return modal;
  }
  function refresh(){var state=readStatus(),native=readAndroidStatus(),badge=document.getElementById('kggReleaseBadge'),message=document.getElementById('kggReleaseMessage'),codeBox=document.getElementById('kggReleaseCodeBox');if(!badge||!message)return;var phase=String(state.phase||'idle'),userCode=String(state.userCode||'').trim(),nativeText='';badge.textContent=state.authenticated?'Verbunden':(phase==='error'?'Fehler':(phase==='login_waiting'?'Code':'Bereit'));badge.className='kggReleaseBadge'+(state.authenticated?' isReady':(phase==='error'?' isError':''));if(native&&native.currentShellVersion)nativeText=' APK v'+native.currentShellVersion+(native.currentWebVersion?' · Web '+native.currentWebVersion:'');message.textContent=(state.message||'Release-Steuerung ist bereit.')+nativeText;if(codeBox){codeBox.classList.toggle('isOpen',!!userCode&&!state.authenticated);setText('kggReleaseCodeValue',userCode);}}
  function startRefreshLoop(){if(refreshTimer)return;refreshTimer=setInterval(refresh,1000);}
  function stopRefreshLoop(){if(refreshTimer){clearInterval(refreshTimer);refreshTimer=null;}}
  function open(){var modal=ensureModal();closeTabletMenu();modal.classList.add('isOpen');modal.setAttribute('aria-hidden','false');refresh();startRefreshLoop();}
  function close(){var modal=document.getElementById('kggReleaseCenterModal');if(!modal)return;modal.classList.remove('isOpen');modal.setAttribute('aria-hidden','true');stopRefreshLoop();}
  function actionButton(id,text,handler){var button=document.createElement('button');button.id=id;button.type='button';button.className='tabletSideMenuAction';button.textContent=text;button.onclick=handler;return button;}
  function installEntryPoints(){
    var menu=document.querySelector('.tabletSideMenuMain');
    if(menu&&!document.getElementById('kggReleaseMenuGroup')){
      var group=document.createElement('div');group.id='kggReleaseMenuGroup';group.className='tabletSideMenuGroup kggReleaseMenuGroup';group.innerHTML='<h3>Admin</h3>';
      group.appendChild(actionButton('kggReleaseAdminConfig','Admin-Konfig',function(){closeTabletMenu();var target=document.getElementById('adminConfigBtn');if(target)target.click();}));
      group.appendChild(actionButton('kggDeviceSyncOpen','Geräte-Sync',function(){closeTabletMenu();var target=document.getElementById('syncQrBtn');if(target)target.click();}));
      group.appendChild(actionButton('kggReleaseCenterOpen','Update-Zentrale',open));menu.appendChild(group);
    }
    var tools=document.querySelector('.adminCodePackageTools');
    if(tools&&!document.getElementById('kggReleaseCenterOpenPhone')){var phone=actionButton('kggReleaseCenterOpenPhone','Update-Zentrale',open);phone.className='mutedBtn wide';tools.appendChild(phone);}
  }
  window.KGGReleaseCenter={open:open,close:close,status:readStatus};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installEntryPoints,{once:true});else installEntryPoints();
})();
</script>
<!-- KGG_ADMIN_ONLY_END -->



<!-- KGG CLEAN MERGE v11: phone touch fixes only; no local auto-redirect blocker -->
<style id="kgg-phone-touch-tablet-parity-hard-v3-css">
@media (max-width:759px){
  /* Remove the phone-only v401 layout cage from the plan area. */
  #rightPlanStack,
  #currentPlanBlock.planSectionCurrent,
  body.kggPlanSectionFrozen #currentPlanBlock.planSectionCurrent{
    contain:none!important;
    overflow:visible!important;
    transform:none!important;
    backface-visibility:visible!important;
    -webkit-backface-visibility:visible!important;
    height:auto!important;
    min-height:0!important;
    max-height:none!important;
  }

  #currentPlanBlock .planSectionBody,
  body.kggPlanSectionFrozen #currentPlanBlock .planSectionBody,
  body.kggPlanCardSwiping #currentPlanBlock .planSectionBody,
  body.kggPlanCardReordering #currentPlanBlock .planSectionBody{
    contain:none!important;
    overflow:auto!important;
    touch-action:pan-y!important;
    overscroll-behavior:auto!important;
    -webkit-overflow-scrolling:touch!important;
    max-height:none!important;
    transform:none!important;
    backface-visibility:visible!important;
    -webkit-backface-visibility:visible!important;
  }

  #currentPlanBlock #planList.planList,
  body.kggPlanSectionFrozen #currentPlanBlock #planList.planList{
    contain:none!important;
    isolation:auto!important;
    overflow:visible!important;
    transform:none!important;
    backface-visibility:visible!important;
    -webkit-backface-visibility:visible!important;
  }

  /* Keep the rest of the phone UI tappable during plan gestures, like tablet. */
  body.kggPlanCardReordering :is(
    #bankArea,
    #dbTitle,
    .bankArea,
    .bankRows,
    .az,
    #inputWrap,
    #exerciseInput,
    .suggestion
  ){
    pointer-events:auto!important;
    transform:none!important;
    filter:none!important;
  }

  /* Swipe animation: remove phone-only cage effects; keep the same simple transform path as tablet. */
  body.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-dragging,
  body.is-scrolling.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-dragging{
    transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    transition:none!important;
    will-change:transform,opacity!important;
    z-index:8!important;
  }

  body.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-armed{
    transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
  }

  body.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-removing,
  body.is-scrolling.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-removing{
    transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    will-change:transform,opacity!important;
    z-index:8!important;
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
```
