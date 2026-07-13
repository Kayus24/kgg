# KGG Source Chunk 058

- Source: `kgg-update/index.html`
- Lines: 24361-24780

```html
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
```
