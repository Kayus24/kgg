# KGG Source Chunk 059

- Source: `kgg-update/src` modular source
- Lines: 24781-25200

```html
      try{
        var oldResult = await oldDetect(canvas, detector);
        if(oldResult) return oldResult;
      }catch(e){}
    }
    return jsqrFallback(canvas);
  }
  try{ window.detectQrOnCanvas = wrappedDetect; }catch(e){}
  try{ detectQrOnCanvas = wrappedDetect; }catch(e){}
  window.KGG_QR_GALLERY_DEBUG = {
    patchId: 'kgg-v021-embed-jsqr-gallery-decode',
    check: function(){ return { patchId:this.patchId, jsQR:typeof window.jsQR==='function', detectQrOnCanvas:typeof window.detectQrOnCanvas }; }
  };
})();

</script>
<!-- KGG PATCH END kgg-v021-embed-jsqr-gallery-decode wrapper -->

<!-- KGG_ADMIN_ONLY_START -->
<style id="kgg-release-center-v31-style">
  .kggReleaseOverlay{position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;padding:18px;background:rgba(7,16,39,.46);backdrop-filter:blur(10px)}
  .kggReleaseOverlay.isOpen{display:flex}
  .kggReleaseSheet{width:min(720px,96vw);max-height:92vh;overflow:auto;border:1px solid rgba(10,16,36,.12);border-radius:26px;background:#fff;color:#0a1024;padding:22px;box-shadow:0 30px 90px rgba(10,16,36,.28);font-family:inherit}
  .kggReleaseHead{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:14px}
  .kggReleaseHead h2{margin:0;font-size:1.45rem;font-weight:950}
  .kggReleaseHead p{margin:5px 0 0;color:#667085;font-weight:700;line-height:1.35}
  .kggReleaseClose{flex:0 0 auto;width:44px;height:44px;border:1px solid rgba(10,16,36,.12);border-radius:14px;background:#fff;color:#0a1024;font-size:24px;font-weight:900}
  .kggReleaseStatus{display:grid;grid-template-columns:auto 1fr;gap:8px 12px;align-items:center;margin:0 0 16px;padding:13px 14px;border:1px solid #dce7f2;border-radius:18px;background:#f5f9fd}
  .kggReleaseBadge{display:inline-flex;align-items:center;justify-content:center;min-height:30px;padding:0 10px;border-radius:999px;background:#e7eef7;color:#344054;font-size:.78rem;font-weight:950;text-transform:uppercase;letter-spacing:.04em}
  .kggReleaseBadge.isReady{background:#dcfce7;color:#166534}
  .kggReleaseBadge.isError{background:#fee2e2;color:#991b1b}
  .kggReleaseMessage{min-width:0;font-weight:850;line-height:1.3}
  .kggReleaseCodeBox{display:none;margin:-2px 0 14px;padding:14px;border-radius:18px;border:2px solid #b8d9f6;background:#edf6ff;box-shadow:0 10px 26px rgba(7,50,84,.08)}
  .kggReleaseCodeBox.isOpen{display:grid;gap:10px}
  .kggReleaseCodeLabel{color:#073254;font-size:.86rem;font-weight:950}
  .kggReleaseCodeValue{font-size:clamp(2rem,9vw,3.6rem);line-height:1;letter-spacing:.08em;font-weight:1000;text-align:center;color:#071027;background:#fff;border:1px solid #cfe4f8;border-radius:16px;padding:14px 8px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
  .kggReleaseCodeHint{color:#475467;font-size:.85rem;font-weight:800;line-height:1.35}
  .kggReleaseInboxHint{margin:12px 0 0;padding:13px 14px;border:1px solid #b8d9f6;border-radius:18px;background:#f7fbff;color:#073254;font-size:.88rem;font-weight:850;line-height:1.35}
  .kggReleaseInboxHint strong{display:block;color:#071027;font-weight:1000;margin-bottom:3px}
  .kggReleaseGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .kggReleaseField{display:grid;gap:6px}
  .kggReleaseField.wide{grid-column:1/-1}
  .kggReleaseField label{font-size:.82rem;color:#475467;font-weight:900}
  .kggReleaseField input,.kggReleaseField textarea{width:100%;box-sizing:border-box;border:1px solid #cfd9e5;border-radius:15px;background:#fff;color:#0a1024;padding:12px 13px;font:inherit;font-weight:750;outline:none}
  .kggReleaseField textarea{min-height:92px;resize:vertical}
  .kggReleaseField input:focus,.kggReleaseField textarea:focus{border-color:#5ea7e8;box-shadow:0 0 0 4px rgba(94,167,232,.16)}
  .kggReleaseActions{display:grid;gap:10px;margin-top:16px}
  .kggReleaseActions.two{grid-template-columns:1fr 1fr}
  .kggReleaseBtn{min-height:50px;border:1px solid rgba(10,16,36,.13);border-radius:16px;background:#fff;color:#0a1024;padding:10px 14px;font:inherit;font-weight:950;box-shadow:0 8px 20px rgba(10,16,36,.07)}
  .kggReleaseBtn.primary{background:#0a1024;color:#fff}
  .kggReleaseBtn.soft{background:#edf6ff;border-color:#b8d9f6;color:#073254}
  .kggReleaseBtn.danger{background:#fff5f5;border-color:#fecaca;color:#991b1b}
  .kggReleaseMenuGroup{margin-top:10px}
  .kggReleaseMenuGroup h3{margin:0 0 8px}
  @media(max-width:759px){.kggReleaseOverlay{padding:10px;align-items:flex-end}.kggReleaseSheet{width:100%;max-height:94vh;border-radius:24px 24px 16px 16px;padding:17px}.kggReleaseGrid,.kggReleaseActions.two{grid-template-columns:1fr}.kggReleaseField.wide{grid-column:1}.kggReleaseHead h2{font-size:1.25rem}}
</style>
<script id="kgg-release-center-v31-script">
(function(){
  'use strict';
  var MOBILE_INBOX_URL='https://github.com/Kayus24/kgg/upload/mobile-inbox/mobile-inbox';
  var MOBILE_PROMOTE_URL='https://github.com/Kayus24/kgg/actions/workflows/promote-latest-admin-beta.yml';
  if(!window.KGGReleaseControl&&(location.hostname==='127.0.0.1'||location.hostname==='localhost')&&location.search.indexOf('kggReleaseUiTest=1')>=0){
    window.KGGReleaseControl={status:function(){return JSON.stringify({phase:'idle',message:'Lokaler UI-Test',available:true,authenticated:false,repository:'Kayus24/kgg'});},beginLogin:function(){return false;},testConnection:function(){return false;},downloadCurrentHtml:function(){return false;},openMobileInbox:function(){window.open(MOBILE_INBOX_URL,'_blank');return true;},openPromoteLatest:function(){window.open(MOBILE_PROMOTE_URL,'_blank');return true;},chooseAndUploadBeta:function(){return false;},confirmPromotion:function(){return false;},confirmRollback:function(){return false;}};
  }
  if(!window.KGGReleaseControl||window.KGGReleaseCenter)return;
  var refreshTimer=null;
  function readStatus(){try{return JSON.parse(window.KGGReleaseControl.status()||'{}');}catch(err){return {phase:'error',message:'Status konnte nicht gelesen werden.'};}}
  function readAndroidStatus(){try{if(window.KGGAndroidApp&&typeof window.KGGAndroidApp.updateStatus==='function')return JSON.parse(window.KGGAndroidApp.updateStatus()||'{}');}catch(err){}return null;}
  function value(id){var el=document.getElementById(id);return el?(el.value||'').trim():'';}
  function setText(id,text){var el=document.getElementById(id);if(el)el.textContent=text||'';}
  function copyText(text){try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text);return true;}}catch(err){}try{var input=document.createElement('input');input.value=text;input.style.position='fixed';input.style.opacity='0';document.body.appendChild(input);input.select();document.execCommand('copy');input.remove();return true;}catch(err){return false;}}
  function openExternal(url){try{window.open(url,'_blank');return true;}catch(err){try{location.href=url;return true;}catch(inner){return false;}}}
  function closeTabletMenu(){document.body.classList.remove('tabletMenuOpen');var menu=document.getElementById('tabletSideMenu');if(menu)menu.setAttribute('aria-hidden','true');}
  function ensureModal(){
    var existing=document.getElementById('kggReleaseCenterModal');
    if(existing)return existing;
    var modal=document.createElement('div');
    modal.id='kggReleaseCenterModal';modal.className='kggReleaseOverlay';modal.setAttribute('aria-hidden','true');
    modal.innerHTML='<section class="kggReleaseSheet" role="dialog" aria-modal="true" aria-labelledby="kggReleaseTitle">'
      +'<div class="kggReleaseHead"><div><h2 id="kggReleaseTitle">KGG Update-Zentrale</h2><p>Standard: HTML speichern und per GitHub-Mobile-Inbox hochladen. Direktupload bleibt Komfortweg.</p></div><button class="kggReleaseClose" id="kggReleaseClose" type="button" aria-label="Update-Zentrale schliessen">&times;</button></div>'
      +'<div class="kggReleaseStatus"><span class="kggReleaseBadge" id="kggReleaseBadge">Status</span><span class="kggReleaseMessage" id="kggReleaseMessage">Wird geladen …</span></div>'
      +'<div class="kggReleaseCodeBox" id="kggReleaseCodeBox" aria-live="polite"><div class="kggReleaseCodeLabel">GitHub-Code</div><div class="kggReleaseCodeValue" id="kggReleaseCodeValue"></div><button class="kggReleaseBtn soft" id="kggReleaseCopyCode" type="button">Code kopieren</button><div class="kggReleaseCodeHint">Diesen Code auf der GitHub-Seite eingeben. Wenn GitHub langsam laedt: Code kopieren, spaeter verbinden oder den Mobile-Inbox-Weg nutzen.</div></div>'
      +'<button class="kggReleaseBtn soft" id="kggReleaseDownloadHtml" type="button" style="width:100%;margin-top:10px">Aktuelle HTML speichern</button>'
      +'<button class="kggReleaseBtn primary" id="kggReleaseMobileInbox" type="button" style="width:100%;margin-top:10px">GitHub-Mobile-Inbox oeffnen</button>'
      +'<div class="kggReleaseInboxHint"><strong>Handy-Workflow ohne Codex</strong>1. HTML speichern. 2. Diese Datei in GitHub hochladen. 3. GitHub Actions erzeugt Admin-Beta und PR automatisch.</div>'
      +'<button class="kggReleaseBtn soft" id="kggReleasePromoteLatest" type="button" style="width:100%;margin-top:10px">Kolleg:innen-Freigabe in GitHub oeffnen</button>'
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
```
