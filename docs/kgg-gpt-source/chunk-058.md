# KGG Source Chunk 058

- Source: `kgg-update/src` modular source
- Lines: 24361-24780

```html
  if($('kggAdminMenuQrOpen'))$('kggAdminMenuQrOpen').onclick=()=>{const link=$('kggAdminMenuQrLink'); if(link&&link.value&&/^https?:\/\//.test(link.value))window.open(link.value,'_blank','noopener');};
  if($('kggAdminMenuQrPrint'))$('kggAdminMenuQrPrint').onclick=()=>printKggAdminMenuQr();
  $('dismissInstallPrompt').onclick=()=>{localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString()); closeInstallPrompt();};
  $('acceptInstallPrompt').onclick=acceptInstallPrompt;
  $('installPromptModal').addEventListener('click',ev=>{if(ev.target===$('installPromptModal')){$('dismissInstallPrompt').click();}});
  $('printPdfPreview').onclick=printCurrentPdfPreview;
  $('downloadPdfPreview').onclick=downloadCurrentPdfPreview;
  $('openPdfPreviewTab').onclick=openCurrentPdfPreviewTab;
  $('openPdfPreviewFallback').onclick=openCurrentPdfPreviewTab;
  $('openPdfPreviewMobileBridge').onclick=openCurrentPdfPreviewTab;
  $('closePdfPreview').onclick=closePdfPreview;
  $('pdfPreviewModal').addEventListener('click',ev=>{if(ev.target===$('pdfPreviewModal'))closePdfPreview();});
  $('savePackageBtn').onclick=openPackageSaveModal;
  $('cancelPackageSave').onclick=closePackageSaveModal;
  $('confirmPackageSave').onclick=confirmPackageSave;
  $('packageSaveModal').addEventListener('click',ev=>{if(ev.target===$('packageSaveModal'))closePackageSaveModal();});
  $('packageNameInput').addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();confirmPackageSave();} if(ev.key==='Escape'){ev.preventDefault();closePackageSaveModal();}});
  $('cancelBankDelete').onclick=closeBankDeleteModal;
  $('confirmBankDelete').onclick=confirmBankDelete;
  $('bankDeleteModal').addEventListener('click',ev=>{if(ev.target===$('bankDeleteModal'))closeBankDeleteModal();});
  function installKggV383UiFlowStability(){
    let phoneTapSuppressUntil=0;
    let phoneBankBrowseMode=false;
    const pointFromEvent=ev=>{
      const point=ev&&ev.touches&&ev.touches[0]||ev&&ev.changedTouches&&ev.changedTouches[0]||ev||{};
      return {x:Number(point.clientX)||0,y:Number(point.clientY)||0};
    };
    trackPhoneTouchStart=function(ev){
      if(!isPhoneLayout())return;
      const point=pointFromEvent(ev);
      phoneTapSuppressUntil=0;
      kggPhoneTouchStart={x:point.x,y:point.y,moved:false};
    };
    trackPhoneTouchMove=function(ev){
      if(!isPhoneLayout())return;
      const point=pointFromEvent(ev);
      if(kggPhoneTouchStart){
        const dx=Math.abs(point.x-kggPhoneTouchStart.x);
        const dy=Math.abs(point.y-kggPhoneTouchStart.y);
        if(dx>7||dy>7)kggPhoneTouchStart.moved=true;
      }
      if(kggPhoneTouchStart&&kggPhoneTouchStart.moved)markPhoneUserScrolling();
    };
    trackPhoneTouchEnd=function(){
      if(kggPhoneTouchStart&&kggPhoneTouchStart.moved){
        phoneTapSuppressUntil=Date.now()+170;
        markPhoneUserScrolling();
      }
      kggPhoneTouchStart=null;
    };
    shouldIgnorePhoneScrollToggle=function(){
      return isPhoneLayout()&&Date.now()<phoneTapSuppressUntil;
    };
    guardPhoneScrollToggle=function(ev){
      if(!shouldIgnorePhoneScrollToggle())return false;
      if(ev){ev.preventDefault();ev.stopPropagation();}
      return true;
    };
    initPhoneScrollGuard=function(){
      if(window.__kggPhoneScrollGuardBound)return;
      window.__kggPhoneScrollGuardBound=true;
      window.addEventListener('scroll',markPhoneUserScrolling,{passive:true});
      if(window.PointerEvent){
        document.addEventListener('pointerdown',ev=>{if(ev.pointerType==='touch')trackPhoneTouchStart(ev);},{passive:true});
        document.addEventListener('pointermove',ev=>{if(ev.pointerType==='touch')trackPhoneTouchMove(ev);},{passive:true});
        document.addEventListener('pointerup',ev=>{if(ev.pointerType==='touch')trackPhoneTouchEnd(ev);},{passive:true});
        document.addEventListener('pointercancel',ev=>{if(ev.pointerType==='touch')trackPhoneTouchEnd(ev);},{passive:true});
      }else{
        document.addEventListener('touchstart',trackPhoneTouchStart,{passive:true});
        document.addEventListener('touchmove',trackPhoneTouchMove,{passive:true});
        document.addEventListener('touchend',trackPhoneTouchEnd,{passive:true});
        document.addEventListener('touchcancel',trackPhoneTouchEnd,{passive:true});
      }
    };
    markPhoneButtonFloat=function(){};
    const blurPhoneComposerForBrowse=()=>{
      if(!isPhoneLayout())return;
      phoneBankBrowseMode=true;
      document.body.classList.add('kggPhoneDbBrowseMode');
      const input=$('exerciseInput');
      if(input&&document.activeElement===input){
        try{input.blur();}catch(err){}
      }
      document.body.classList.remove('phoneTextFocus');
      updatePhoneKeyboardInset();
    };
    const openOrCloseBankFromBrowseTap=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      if(isPhoneLayout())blurPhoneComposerForBrowse();
      const opening=!state.bankOpen;
      if(opening&&isTabletLayout())openTabletExclusivePanel('bank');
      state.bankOpen=opening;
      render();
      setTabletOverlayActiveFlag();
    };
    const input=$('exerciseInput');
    if(input){
      input.addEventListener('focus',()=>{phoneBankBrowseMode=false;document.body.classList.remove('kggPhoneDbBrowseMode');});
      input.addEventListener('input',()=>{phoneBankBrowseMode=false;document.body.classList.remove('kggPhoneDbBrowseMode');});
    }
    const oldApplySelectedExerciseToText=applySelectedExerciseToText;
    applySelectedExerciseToText=function(ex,options){
      const next={...(options||{})};
      if(isPhoneLayout()&&phoneBankBrowseMode)next.keepFocus=false;
      return oldApplySelectedExerciseToText(ex,next);
    };
    if($('bankToggle'))$('bankToggle').onclick=openOrCloseBankFromBrowseTap;
    if($('dbTitle')){
      $('dbTitle').onclick=openOrCloseBankFromBrowseTap;
      $('dbTitle').onkeydown=null;
      $('dbTitle').addEventListener('keydown',ev=>{
        if(ev.key==='Enter'||ev.key===' '){
          ev.preventDefault();
          ev.stopImmediatePropagation();
          openOrCloseBankFromBrowseTap(ev);
        }
      },true);
    }
    if($('baseToggle'))$('baseToggle').onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      const base=$('baseFields');
      const opening=base.classList.contains('hidden');
      if(isTabletLayout()){
        if(opening)openTabletAnchoredPanel('base'); else closeTabletAnchoredPanel('base');
      }else{
        base.classList.toggle('hidden',!opening);
        setTabletOverlayActiveFlag();
        updateToggleCarets();
      }
    };
    if($('recentToggle'))$('recentToggle').onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      const recent=$('recentList');
      const opening=recent.classList.contains('hidden');
      if(isTabletLayout()){
        if(opening)openTabletAnchoredPanel('recent'); else closeTabletAnchoredPanel('recent');
      }else{
        openPhoneFloatingDrawer('recent');
      }
    };
    const packageToggleBtn=$('packageToggle');
    if(packageToggleBtn)packageToggleBtn.onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      if(isTabletLayout())toggleTabletPackageOverlay();
      else openPhoneFloatingDrawer('package');
    };
    const modalClosers={
      editorModal:typeof closeEditor==='function'?closeEditor:null,
      shareModal:typeof closeFinishModal==='function'?closeFinishModal:null,
      largePdfModal:typeof closeLargePdfModal==='function'?closeLargePdfModal:null,
      longMediaConfirmModal:typeof closeLongMediaConfirmModal==='function'?closeLongMediaConfirmModal:null,
      adminSecretsModal:typeof closeAdminSecretsModal==='function'?closeAdminSecretsModal:null,
      sharedBankModal:typeof closeSharedBankModal==='function'?closeSharedBankModal:null,
      syncPairModal:typeof closeSyncPairModal==='function'?closeSyncPairModal:null
    };
    document.querySelectorAll('.modal').forEach(modal=>{
      if(modal.dataset.kggV383BackdropBound==='1')return;
      modal.dataset.kggV383BackdropBound='1';
      modal.addEventListener('pointerup',ev=>{
        if(ev.target!==modal)return;
        ev.preventDefault();
        ev.stopPropagation();
        const close=modalClosers[modal.id];
        if(typeof close==='function')close();
        else modal.classList.remove('open');
      });
    });
    const adminQrModal=$('kggAdminMenuQrModal');
    if(adminQrModal&&!adminQrModal.dataset.kggV383BackdropBound){
      adminQrModal.dataset.kggV383BackdropBound='1';
      adminQrModal.addEventListener('pointerup',ev=>{
        if(ev.target!==adminQrModal)return;
        ev.preventDefault();
        if(typeof closeKggAdminMenuQrModal==='function')closeKggAdminMenuQrModal();
      });
    }
    const oldApplyNativeSyncInvite=applyNativeSyncInvite;
    applyNativeSyncInvite=function(invite){
      setScanStatus('QR erkannt: Sync-Kopplung wird gelesen ...');
      try{
        const entry=oldApplyNativeSyncInvite(invite);
        const peers=syncPeerDisplayEntries().length;
        setScanStatus('Sync-Kopplung gespeichert. Dieses Geraet liest und schreibt im Sync-Raum. '+(peers?'Anderes Geraet gefunden: Synchronisation aktiv.':'Warte auf weitere Geraete mit diesem QR.'));
        return entry;
      }catch(err){
        setScanStatus('Fehler: ungueltige Sync-Daten.');
        throw err;
      }
    };
    const oldApplyNativeSyncBundle=applyNativeSyncBundle;
    applyNativeSyncBundle=async function(bundle){
      setScanStatus('QR erkannt: Sync-Datenpaket wird gelesen ...');
      try{
        const result=await oldApplyNativeSyncBundle(bundle);
        const peers=syncPeerDisplayEntries().length;
        setScanStatus('Sync-Datenpaket gespeichert. Verbindung und Daten wurden lokal uebernommen. '+(peers?'Synchronisation aktiv.':'Warte auf weitere Geraete mit diesem QR.'));
        return result;
      }catch(err){
        setScanStatus('Fehler: Sync-Verbindung nicht moeglich.');
        throw err;
      }
    };
  }
  function installKggV388AndroidFlowFixes(){
    let lastTabletMenuToggleAt=0;
    const menu=tabletMenuBtn;
    const toggle=ev=>{
      if(!isTabletLayout())return;
      const now=Date.now();
      if(now-lastTabletMenuToggleAt<220){
        if(ev){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();}
        return;
      }
      lastTabletMenuToggleAt=now;
      if(ev){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();}
      setTabletSideMenuOpen(!document.body.classList.contains('tabletMenuOpen'));
    };
    const isMenuHit=ev=>{
      if(!menu||!ev)return false;
      const point=ev.touches&&ev.touches[0]?ev.touches[0]:ev;
      const r=menu.getBoundingClientRect();
      const pad=10;
      return point.clientX>=r.left-pad&&point.clientX<=r.right+pad&&point.clientY>=r.top-pad&&point.clientY<=r.bottom+pad;
    };
    if(menu&&menu.dataset.kggV388MenuBound!=='1'){
      menu.dataset.kggV388MenuBound='1';
      menu.addEventListener('pointerdown',toggle,{capture:true});
      menu.addEventListener('click',toggle,{capture:true});
      menu.addEventListener('touchstart',toggle,{capture:true,passive:false});
      menu.addEventListener('keydown',ev=>{
        if(ev.key!=='Enter'&&ev.key!==' ')return;
        toggle(ev);
      },true);
      document.addEventListener('pointerdown',ev=>{
        if(!isTabletLayout()||!isMenuHit(ev))return;
        toggle(ev);
      },true);
      document.addEventListener('touchstart',ev=>{
        if(!isTabletLayout()||!isMenuHit(ev))return;
        toggle(ev);
      },{capture:true,passive:false});
    }
    const close=tabletMenuClose;
    if(close&&close.dataset.kggV388MenuBound!=='1'){
      close.dataset.kggV388MenuBound='1';
      close.addEventListener('click',ev=>{ev.preventDefault();setTabletSideMenuOpen(false);},{capture:true});
    }
    const backdrop=tabletSideBackdrop;
    if(backdrop&&backdrop.dataset.kggV388MenuBound!=='1'){
      backdrop.dataset.kggV388MenuBound='1';
      backdrop.addEventListener('click',ev=>{ev.preventDefault();setTabletSideMenuOpen(false);},{capture:true});
    }
  }
  installKggV383UiFlowStability();
  installKggV388AndroidFlowFixes();
  load(); initLargePdfMode(); renderRuntimeVersionInUi(); renderBuildIdentityInUi(); setTimeout(renderBuildIdentityInUi,500); initPwaAndUpdates(); initAdminModeAccess(); initTabletSoftKeyboardLayout(); initPhoneKeyboardAndDrawers(); initTabletLayoutControls(); initNativeExerciseBankSync(); ensureKGGDataStore().init({appVersion:VERSION}); syncStatePlanToStore('app_init_after_load'); if(state.patient.name) $('patientName').value=state.patient.name; if(state.patient.date) $('planDate').value=state.patient.date; if(state.patient.therapist) $('therapistName').value=state.patient.therapist; if(state.patient.notes) $('planNotes').value=state.patient.notes; syncTextInputFromPlan('app_init_text_master'); render(); setTabletOverlayActiveFlag(); tryApplyKggSetupFromHash().catch(err=>{console.warn('Therapeuten-Setup konnte nicht uebernommen werden:',err);});
})();
</script>

<script id="kgg-mini-patch-v400-04-phone-clean-state-guard">
/* v400 mini04: räumt nur im Phone-Viewport Tablet-Zustände auf.
   Kein Eingriff in PDF/QR/Scan/Parser/Plan-State. */
(function(){
  const PHONE_QUERY='(max-width: 759px)';
  function isPhone(){
    return !!(window.matchMedia && window.matchMedia(PHONE_QUERY).matches);
  }
  function cleanPhoneTabletState(){
    if(!isPhone()) return;
    const body=document.body;
    if(!body) return;
    body.classList.remove('tabletMenuOpen','tabletPackageOverlayOpen','tabletLayoutEditMode');
    const menu=document.getElementById('tabletSideMenu');
    if(menu) menu.setAttribute('aria-hidden','true');
    const menuBtn=document.getElementById('tabletMenuBtn');
    if(menuBtn){
      menuBtn.setAttribute('aria-expanded','false');
      menuBtn.setAttribute('aria-label','Tablet-Menue oeffnen');
    }
    const packageOverlay=document.getElementById('tabletPackageOverlay');
    if(packageOverlay) packageOverlay.setAttribute('aria-hidden','true');
    const shareModal=document.getElementById('kggTherapistShareModal');
    if(shareModal){
      shareModal.classList.remove('isOpen');
      shareModal.setAttribute('aria-hidden','true');
    }
    const adminQr=document.getElementById('kggAdminMenuQrModal');
    if(adminQr){
      adminQr.classList.remove('isOpen');
      adminQr.setAttribute('aria-hidden','true');
    }
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',cleanPhoneTabletState,{once:true});
  }else{
    cleanPhoneTabletState();
  }
  window.addEventListener('resize',()=>setTimeout(cleanPhoneTabletState,30),{passive:true});
  window.addEventListener('orientationchange',()=>setTimeout(cleanPhoneTabletState,140),{passive:true});
  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',()=>setTimeout(cleanPhoneTabletState,30),{passive:true});
  }
})();
</script>
<script id="kgg-github-patch-v401-phone-plan-ui-isolation">
/* v401 GitHub Update 003: Phone-only Plan-Interaktion einfrieren.
   Hält die Außen-UI stabil, während Plan-Karten angetippt/verschoben werden.
   Keine Änderung an Plan-State, Parser, QR, PDF, Kamera oder Tablet-Layout. */
(function(){
  const PHONE_QUERY='(max-width:759px)';
  let releaseTimer=0;
  let bodyObserver=null;

  function isPhone(){
    return !!(window.matchMedia && window.matchMedia(PHONE_QUERY).matches);
  }

  function currentPlanBlock(){
    return document.getElementById('currentPlanBlock');
  }

  function isPlanCardTarget(target){
    return !!(target && target.closest && target.closest('#currentPlanBlock .planCard'));
  }

  function freezePlanSection(ms){
    if(!isPhone()) return;
    const block=currentPlanBlock();
    const body=document.body;
    if(!block || !body) return;

    const rect=block.getBoundingClientRect();
    if(rect && rect.height > 0){
      block.style.setProperty('--kgg-current-plan-freeze-h', Math.ceil(rect.height) + 'px');
    }

    body.classList.add('kggPlanSectionFrozen');
    clearTimeout(releaseTimer);
    releaseTimer=setTimeout(releasePlanSection, Number.isFinite(ms) ? ms : 520);
  }

  function releasePlanSection(){
    const body=document.body;
    const block=currentPlanBlock();
    if(body) body.classList.remove('kggPlanSectionFrozen');
    if(block) block.style.removeProperty('--kgg-current-plan-freeze-h');
  }

  function delayedRelease(delay){
    clearTimeout(releaseTimer);
    releaseTimer=setTimeout(releasePlanSection, Number.isFinite(delay) ? delay : 320);
  }

  function installListeners(){
    if(!document.body) return;

    document.addEventListener('pointerdown', function(ev){
      if(isPlanCardTarget(ev.target)) freezePlanSection(760);
    }, {capture:true, passive:true});

    document.addEventListener('pointermove', function(){
      const body=document.body;
      if(body && body.classList.contains('kggPlanCardReordering')) freezePlanSection(760);
    }, {capture:true, passive:true});

    document.addEventListener('pointerup', function(){
      const body=document.body;
      if(body && (body.classList.contains('kggPlanCardReordering') || body.classList.contains('kggPlanSectionFrozen'))){
        delayedRelease(340);
      }
    }, {capture:true, passive:true});

    document.addEventListener('pointercancel', function(){
      delayedRelease(220);
    }, {capture:true, passive:true});

    bodyObserver=new MutationObserver(function(){
      const body=document.body;
      if(!body || !isPhone()) return;
      if(body.classList.contains('kggPlanCardReordering') || body.classList.contains('kggPlanCardSwiping')){
        freezePlanSection(800);
      }
    });
    bodyObserver.observe(document.body,{attributes:true,attributeFilter:['class']});
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', installListeners, {once:true});
  }else{
    installListeners();
  }

  window.addEventListener('resize', function(){
    if(!isPhone()) releasePlanSection();
  }, {passive:true});
})();
</script>

<!-- KGG PATCH START kgg-v021-embed-jsqr-gallery-decode wrapper -->
<script id="kgg-v021-embed-jsqr-gallery-decode-wrapper">

(function(){
  var oldDetect = window.detectQrOnCanvas;
  function getImageData(canvas){
    try{
      var ctx = canvas && canvas.getContext && canvas.getContext('2d',{willReadFrequently:true});
      return ctx ? ctx.getImageData(0,0,canvas.width,canvas.height) : null;
    }catch(e){ return null; }
  }
  function jsqrFallback(canvas){
    if(!canvas || typeof window.jsQR !== 'function') return '';
    var img = getImageData(canvas);
    if(!img) return '';
    try{
      var hit = window.jsQR(img.data, canvas.width, canvas.height, {inversionAttempts:'attemptBoth'});
      return hit && hit.data ? String(hit.data) : '';
    }catch(e){ return ''; }
  }
  async function wrappedDetect(canvas, detector){
    if(typeof oldDetect === 'function' && oldDetect !== wrappedDetect){
```
