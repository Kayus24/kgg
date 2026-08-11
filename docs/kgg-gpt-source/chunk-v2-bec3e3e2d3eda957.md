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

