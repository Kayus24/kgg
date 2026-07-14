# KGG Source Chunk 063

- Source: `kgg-update/src` modular source
- Lines: 26461-26880

```html
      left:16px!important;
      right:16px!important;
      bottom:calc(86px + env(safe-area-inset-bottom))!important;
      z-index:91!important;
      overscroll-behavior:contain!important;
      touch-action:pan-y!important;
      overflow:auto!important;
      background:rgba(255,255,255,.98)!important;
      border:1px solid rgba(220,227,235,.96)!important;
      border-radius:22px!important;
      padding:10px!important;
      box-shadow:0 22px 58px rgba(7,16,39,.24),0 4px 14px rgba(7,16,39,.10)!important;
      backdrop-filter:blur(10px)!important;
      -webkit-backdrop-filter:blur(10px)!important;
      max-height:min(54dvh,390px)!important;
    }
    body.kggPhoneDrawerSafeOpen #recentList:not(.hidden) .notice,
    body.kggPhoneDrawerSafeOpen #packageList:not(.hidden) .notice{margin-top:0!important}
    body.kggPhoneDrawerSafeOpen #scanHub,
    body.kggPhoneDrawerSafeOpen #createPanel.planMode #finishBtn:not(.hidden){
      z-index:40!important;
    }
    body.kggPhoneDrawerSafeOpen .kggPhonePhotoMenu{display:none!important}
  }
</style>

<script id="kgg-v045-phone-drawer-bank-align-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v045-phone-drawer-bank-align";
  var PHONE_QUERY="(max-width:759px)";
  function byId(id){return document.getElementById(id);}
  function isPhone(){return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches&&!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive()));}
  function ensureBackdrop(){
    var backdrop=byId("phoneDrawerBackdrop");
    if(!backdrop){
      backdrop=document.createElement("div");
      backdrop.id="phoneDrawerBackdrop";
      backdrop.className="kggPhoneDrawerBackdrop";
      backdrop.setAttribute("aria-hidden","true");
      document.body.appendChild(backdrop);
    }
    if(backdrop.dataset.kggV045Bound!=="1"){
      backdrop.dataset.kggV045Bound="1";
      backdrop.addEventListener("click",function(ev){
        ev.preventDefault();
        ev.stopImmediatePropagation();
        closePhoneDrawerSafe();
      },true);
    }
    return backdrop;
  }
  function closePhoneDrawerSafe(){
    var recent=byId("recentList");
    var packages=byId("packageList");
    var recentBtn=byId("recentToggle");
    var packageBtn=byId("packageToggle");
    if(recent)recent.classList.add("hidden");
    if(packages)packages.classList.add("hidden");
    if(recentBtn){recentBtn.classList.remove("phoneButtonFloat");recentBtn.setAttribute("aria-expanded","false");}
    if(packageBtn){packageBtn.classList.remove("phoneButtonFloat");packageBtn.setAttribute("aria-expanded","false");}
    if(document.body)document.body.classList.remove("kggPhoneDrawerSafeOpen","kggPhoneDrawerOpen");
  }
  function openPhoneDrawerSafe(kind){
    if(!isPhone())return false;
    var recent=byId("recentList");
    var packages=byId("packageList");
    var recentBtn=byId("recentToggle");
    var packageBtn=byId("packageToggle");
    var target=kind==="recent"?recent:packages;
    var targetBtn=kind==="recent"?recentBtn:packageBtn;
    var other=kind==="recent"?packages:recent;
    var otherBtn=kind==="recent"?packageBtn:recentBtn;
    if(!target||!targetBtn)return false;
    if(!target.classList.contains("hidden")&&targetBtn.classList.contains("phoneButtonFloat")){
      closePhoneDrawerSafe();
      return true;
    }
    ensureBackdrop();
    if(other)other.classList.add("hidden");
    if(otherBtn){otherBtn.classList.remove("phoneButtonFloat");otherBtn.setAttribute("aria-expanded","false");}
    target.classList.remove("hidden");
    targetBtn.classList.add("phoneButtonFloat");
    targetBtn.setAttribute("aria-expanded","true");
    if(document.body){
      document.body.classList.add("kggPhoneDrawerSafeOpen");
      document.body.classList.remove("kggPhonePhotoMenuOpen");
    }
    return true;
  }
  function bindDrawerButton(id,kind){
    var btn=byId(id);
    if(!btn||btn.dataset.kggV045DrawerBound==="1")return;
    btn.dataset.kggV045DrawerBound="1";
    btn.addEventListener("click",function(ev){
      if(!isPhone())return;
      ev.preventDefault();
      ev.stopImmediatePropagation();
      openPhoneDrawerSafe(kind);
    },true);
  }
  function alignBankEndToScanDock(){
    if(!isPhone())return false;
    var bank=byId("bankArea");
    var hub=byId("scanHub");
    if(!bank||!hub||!bank.classList.contains("bankOpen"))return false;
    var bankRect=bank.getBoundingClientRect();
    var hubRect=hub.getBoundingClientRect();
    if(!bankRect.height||!hubRect.height)return false;
    var targetBottom=hubRect.top-10;
    var delta=bankRect.bottom-targetBottom;
    if(Math.abs(delta)>2)window.scrollBy({top:delta,behavior:"auto"});
    return true;
  }
  function scheduleBankAlign(){
    if(!isPhone())return;
    var run=function(){alignBankEndToScanDock();};
    if(typeof requestAnimationFrame==="function"){
      requestAnimationFrame(function(){requestAnimationFrame(run);});
      setTimeout(run,260);
      setTimeout(run,520);
    }else{
      setTimeout(run,80);
      setTimeout(run,320);
    }
  }
  function bindBankOpenAlign(id){
    var el=byId(id);
    if(!el||el.dataset.kggV045BankAlignBound==="1")return;
    el.dataset.kggV045BankAlignBound="1";
    el.addEventListener("click",function(){
      if(!isPhone())return;
      var bank=byId("bankArea");
      var opening=!(bank&&bank.classList.contains("bankOpen"));
      if(opening)scheduleBankAlign();
    },true);
    el.addEventListener("keydown",function(ev){
      if(!isPhone()||!(ev.key==="Enter"||ev.key===" "))return;
      var bank=byId("bankArea");
      var opening=!(bank&&bank.classList.contains("bankOpen"));
      if(opening)scheduleBankAlign();
    },true);
  }
  function install(){
    bindDrawerButton("recentToggle","recent");
    bindDrawerButton("packageToggle","package");
    bindBankOpenAlign("bankToggle");
    bindBankOpenAlign("dbTitle");
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,220,600,1200].forEach(function(ms){setTimeout(install,ms);});
  if(document.body){
    new MutationObserver(function(){install();}).observe(document.body,{childList:true,subtree:true});
  }
  window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045={
    patchId:PATCH_ID,
    install:install,
    closeDrawer:closePhoneDrawerSafe,
    openDrawer:openPhoneDrawerSafe,
    alignBank:alignBankEndToScanDock
  };
})();
</script>
<!-- KGG PATCH END kgg-v045-phone-drawer-bank-align -->

<!-- SOURCE FILE: kgg-update/src/patches/v046-tablet-runtime-viewport-guard.html -->

<!-- KGG PATCH START kgg-v046-tablet-runtime-viewport-guard -->
<script id="kgg-v046-tablet-runtime-viewport-guard-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v046-tablet-runtime-viewport-guard";
  var PHONE_QUERY="(max-width:759px)";
  function isPhoneViewport(){return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches);}
  window.KGG_TABLET_RUNTIME_VIEWPORT_GUARD_V046={
    patchId:PATCH_ID,
    phoneQuery:PHONE_QUERY,
    check:function(){
      return {
        patchId:PATCH_ID,
        phoneViewport:isPhoneViewport(),
        phoneHasPlanClass:!!(document.body&&document.body.classList.contains("kggPhoneHasPlan")),
        phonePhotoOpen:!!(document.body&&document.body.classList.contains("kggPhonePhotoMenuOpen")),
        scanHydrated:!!(document.getElementById("scanBtn")&&document.getElementById("scanBtn").dataset.kggV042ScanHydrated==="1")
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v046-tablet-runtime-viewport-guard -->

<!-- SOURCE FILE: kgg-update/src/patches/v050-phone-ui-mini-fix.html -->

<!-- KGG PATCH START kgg-v050-phone-ui-mini-fix -->
<style id="kgg-v050-phone-ui-mini-fix-style">
  @media(max-width:759px){
    body.adminMode #createPanel.planMode .planHeader{
      position:relative!important;
      grid-template-columns:minmax(0,1fr) auto!important;
    }
    body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenu{
      position:absolute!important;
      top:8px!important;
      right:88px!important;
      left:auto!important;
      transform:none!important;
      z-index:74!important;
      margin:0!important;
      align-self:auto!important;
      justify-self:auto!important;
    }
    body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenuPanel{
      top:calc(100% + 8px)!important;
      right:0!important;
    }
    body.kggPhoneHasPlan #createPanel.planMode .planActions.hasPlan{
      grid-template-columns:1fr!important;
      gap:10px!important;
    }
    body.kggPhoneHasPlan #createPanel.planMode .planActions.hasPlan #recentToggle,
    body.kggPhoneHasPlan #createPanel.planMode .planActions.hasPlan #packageToggle{
      width:100%!important;
      min-width:0!important;
      max-width:none!important;
      justify-content:space-between!important;
      padding-left:18px!important;
      padding-right:18px!important;
      overflow:visible!important;
    }
    body.kggPhoneHasPlan #createPanel.planMode .planActions.hasPlan #recentToggle .recentText,
    body.kggPhoneHasPlan #createPanel.planMode .planActions.hasPlan #recentToggle .recentMini{
      display:inline-flex!important;
      max-width:none!important;
      min-width:0!important;
      opacity:1!important;
      overflow:visible!important;
      white-space:nowrap!important;
    }

    #scanHub.kggPhoneScanMenuInline{
      align-content:end!important;
      overflow:visible!important;
      transition:min-height .18s ease, padding .18s ease!important;
    }
    body.kggPhonePhotoMenuOpen #scanHub.kggPhoneScanMenuInline{
      min-height:170px!important;
      padding-top:10px!important;
    }
    #scanHub.kggPhoneScanMenuInline #scanBtn.kggScanButtonWithMenu{
      position:relative!important;
      overflow:visible!important;
      isolation:isolate!important;
    }
    #scanHub.kggPhoneScanMenuInline #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle{
      align-self:center!important;
      height:60px!important;
      min-height:60px!important;
      width:54px!important;
      min-width:54px!important;
      flex-basis:54px!important;
      border:0!important;
      border-radius:18px!important;
      background:transparent!important;
      box-shadow:none!important;
      font-size:26px!important;
      line-height:1!important;
    }
    #scanHub.kggPhoneScanMenuInline #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle::before{
      content:none!important;
      display:none!important;
    }
    body.kggPhonePhotoMenuOpen #scanHub.kggPhoneScanMenuInline #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle{
      background:rgba(7,16,39,.92)!important;
      color:#fff!important;
      box-shadow:0 10px 24px rgba(7,16,39,.20),inset 0 1px 0 rgba(255,255,255,.16)!important;
    }
    #scanHub.kggPhoneScanMenuInline #kggPhonePhotoMenu{
      order:-1!important;
      position:static!important;
      display:none!important;
      width:100%!important;
      min-width:0!important;
      margin:0 0 9px 0!important;
      padding:9px!important;
      border:1px solid rgba(255,255,255,.82)!important;
      border-radius:22px!important;
      background:rgba(255,255,255,.86)!important;
      box-shadow:0 18px 42px rgba(7,16,39,.18),inset 0 1px 0 rgba(255,255,255,.94)!important;
      backdrop-filter:blur(24px) saturate(1.45)!important;
      -webkit-backdrop-filter:blur(24px) saturate(1.45)!important;
      gap:8px!important;
      z-index:auto!important;
    }
    body.kggPhonePhotoMenuOpen #scanHub.kggPhoneScanMenuInline #kggPhonePhotoMenu{
      display:grid!important;
    }
    #scanHub.kggPhoneScanMenuInline #kggPhonePhotoMenu button{
      width:100%!important;
      min-height:52px!important;
      border:0!important;
      border-radius:16px!important;
      background:rgba(243,247,253,.96)!important;
      color:#071027!important;
      font-weight:1000!important;
      font-size:18px!important;
      text-align:center!important;
    }
  }
</style>

<script id="kgg-v050-phone-ui-mini-fix-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v050-phone-ui-mini-fix";
  var PHONE_QUERY="(max-width:759px)";
  function byId(id){return document.getElementById(id);}
  function isPhone(){
    return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches&&!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive()));
  }
  function placeAdminMenu(){
    var menu=byId("kggPhoneAdminMenu");
    var header=document.querySelector("#createPanel.planMode .planHeader");
    if(menu&&header&&!header.contains(menu))header.appendChild(menu);
  }
  function placeInlinePhotoMenu(){
    var hub=byId("scanHub");
    var menu=byId("kggPhonePhotoMenu");
    var toggle=byId("phonePhotoMenuToggle");
    if(!hub||!menu)return;
    if(!isPhone()){
      if(hub.classList.contains("kggPhoneScanMenuInline"))hub.classList.remove("kggPhoneScanMenuInline");
      if(menu.parentElement!==document.body)document.body.appendChild(menu);
      return;
    }
    if(!hub.classList.contains("kggPhoneScanMenuInline"))hub.classList.add("kggPhoneScanMenuInline");
    if(menu.parentElement!==hub)hub.appendChild(menu);
    if(toggle){
      if(toggle.textContent!=="\u2303")toggle.textContent="\u2303";
      if(toggle.getAttribute("aria-label")!=="Foto-Optionen oeffnen")toggle.setAttribute("aria-label","Foto-Optionen oeffnen");
      if(toggle.getAttribute("title")!=="Foto-Optionen")toggle.setAttribute("title","Foto-Optionen");
    }
  }
  function install(){
    if(!document.body)return;
    placeAdminMenu();
    placeInlinePhotoMenu();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,220,600,1200].forEach(function(ms){setTimeout(install,ms);});
  window.addEventListener("resize",function(){setTimeout(install,90);},{passive:true});
  window.addEventListener("orientationchange",function(){setTimeout(install,180);},{passive:true});
  if(document.body){
    new MutationObserver(function(){install();}).observe(document.body,{childList:true,subtree:true});
  }
  window.KGG_UI_PHONE_MINI_FIX_V050={patchId:PATCH_ID,install:install};
})();
</script>
<!-- KGG PATCH END kgg-v050-phone-ui-mini-fix -->

<!-- SOURCE FILE: kgg-update/src/patches/v051-android-qr-pdf-bridge.html -->

<!-- KGG PATCH START kgg-v051-android-qr-pdf-bridge -->
<script id="kgg-v051-android-qr-pdf-bridge-probe">
window.KGG_ANDROID_QR_PDF_BRIDGE_V051={
  patchId:'kgg-v051-android-qr-pdf-bridge',
  qrPrintButtonId:'kggAdminMenuQrPrint',
  androidShellVersion:'v399'
};
</script>
<!-- KGG PATCH END kgg-v051-android-qr-pdf-bridge -->

<!-- SOURCE FILE: kgg-update/src/patches/v052-pdf-plan-thumbnails.html -->

<!-- KGG PATCH START kgg-v052-pdf-plan-thumbnails -->
<script id="kgg-v052-pdf-plan-thumbnails-probe">
window.KGG_PDF_PLAN_THUMBNAILS_V052={
  patchId:'kgg-v052-pdf-plan-thumbnails',
  snapshotHelper:'attachKggPdfExerciseThumbnails',
  drawTarget:'drawKggExerciseBox'
};
</script>
<!-- KGG PATCH END kgg-v052-pdf-plan-thumbnails -->

<!-- SOURCE FILE: kgg-update/src/patches/v053-ui-tablet-stability.html -->

<!-- KGG PATCH START kgg-v053-ui-tablet-stability -->
<style id="kgg-v053-ui-tablet-stability-style">
  @media(max-width:759px){
    body.phoneTextFocus #scanHub,
    body.phoneTextFocus.kggPhoneHasPlan #scanHub{
      bottom:calc(12px + env(safe-area-inset-bottom))!important;
      transform:translateY(var(--kgg-phone-keyboard-inset,0px))!important;
    }
    body.phoneTextFocus.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      bottom:calc(12px + env(safe-area-inset-bottom))!important;
      transform:translateY(var(--kgg-phone-keyboard-inset,0px))!important;
    }
    body.adminMode #createPanel.planMode .planHeader{
      padding-right:54px!important;
      grid-template-columns:minmax(0,1fr) auto!important;
    }
    body.adminMode #createPanel.planMode .planHeader #kggPhoneAdminMenu{
      position:absolute!important;
      top:4px!important;
      right:0!important;
      left:auto!important;
      transform:none!important;
      z-index:76!important;
      margin:0!important;
    }
    body.adminMode #createPanel.planMode .planHeader #savePackageBtn:not(.hidden){
      margin-right:8px!important;
    }
  }

  @media(min-width:760px){
    body.tabletLayoutCustom #scanHub{
      position:relative!important;
```
