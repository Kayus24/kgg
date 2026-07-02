# KGG Source Chunk 062

- Source: `kgg-update/index.html`
- Lines: 26041-26460

```html
      font-size:24px!important;
    }
    #scanHub #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle::before{
      content:"";
      position:absolute;
      left:-8px;
      top:10px;
      bottom:10px;
      width:1px;
      background:rgba(7,16,39,.16);
      box-shadow:1px 0 0 rgba(255,255,255,.74);
      pointer-events:none;
    }
    body.kggPhonePhotoMenuOpen #scanHub #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle{
      background:rgba(7,16,39,.90)!important;
      color:#fff!important;
    }

    body.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      min-height:60px!important;
      height:60px!important;
      border-radius:22px!important;
      font-weight:1000!important;
      letter-spacing:-.2px!important;
    }

    .planActions.hasPlan{
      grid-template-columns:minmax(118px,.92fr) minmax(148px,1.08fr)!important;
      gap:10px!important;
    }
    .planActions.hasPlan #recentToggle{
      width:auto!important;
      min-width:148px!important;
      padding-left:14px!important;
      padding-right:14px!important;
      justify-content:center!important;
    }
    .planActions.hasPlan .recentText,
    .planActions.hasPlan .recentMini{
      max-width:180px!important;
      opacity:1!important;
    }

    #createPanel .planHeader .kggPhoneAdminMenuPanel{
      min-width:min(82vw,304px)!important;
      padding:10px!important;
      gap:10px!important;
      background:rgba(255,255,255,.94)!important;
      border:1px solid rgba(255,255,255,.88)!important;
      box-shadow:0 22px 54px rgba(7,16,39,.24),inset 0 1px 0 rgba(255,255,255,.96)!important;
    }
    .kggPhoneMenuGroup{
      display:grid;
      gap:6px;
      padding:8px;
      border-radius:16px;
      background:rgba(244,248,253,.82);
      border:1px solid rgba(220,227,235,.92);
    }
    .kggPhoneMenuGroupTitle{
      padding:2px 4px 4px;
      color:#637087;
      font-size:11px;
      font-weight:1000;
      letter-spacing:.05em;
      text-transform:uppercase;
    }
    .kggPhoneMenuGroup button{
      min-height:44px!important;
      border:0!important;
      border-radius:12px!important;
      background:#fff!important;
      color:#071027!important;
      box-shadow:0 5px 14px rgba(7,16,39,.07),inset 0 1px 0 rgba(255,255,255,.98)!important;
      text-align:left!important;
      font-weight:950!important;
    }
  }
</style>

<script id="kgg-v044-phone-liquid-actions-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v044-phone-liquid-actions";
  function byId(id){return document.getElementById(id);}
  function clickExisting(id){var el=byId(id); if(el&&typeof el.click==="function")el.click();}
  function closePhoneAdminMenu(){
    var panel=byId("kggPhoneAdminMenuPanel");
    var btn=byId("kggPhoneAdminMenuBtn");
    if(panel)panel.hidden=true;
    if(btn)btn.setAttribute("aria-expanded","false");
  }
  function openReleaseCenter(){
    closePhoneAdminMenu();
    if(window.KGGReleaseCenter&&typeof window.KGGReleaseCenter.open==="function"){window.KGGReleaseCenter.open();return;}
    clickExisting("kggReleaseCenterOpenPhone");
    clickExisting("kggReleaseCenterOpen");
  }
  function openDeviceSync(){
    closePhoneAdminMenu();
    if(typeof window.openSyncPairModal==="function"){window.openSyncPairModal();return;}
    clickExisting("syncQrBtn");
  }
  function openTherapistShare(){
    closePhoneAdminMenu();
    if(typeof window.openKggTherapistAppOnlyQr==="function"){window.openKggTherapistAppOnlyQr();return;}
    if(typeof window.openKggAdminMenuQr==="function"){
      window.openKggAdminMenuQr({
        title:"Kolleg:innen-App APK QR",
        hint:"Oeffnet die aktuelle Android-Download-Seite fuer Kolleg:innen. Keine API-Keys, keine Sync-Daten.",
        url:"https://kayus24.github.io/kgg/therapist-app/latest-android.html"
      });
    }
  }
  function openSharedBank(){
    closePhoneAdminMenu();
    if(window.KGGSharedBank&&typeof window.KGGSharedBank.open==="function"){window.KGGSharedBank.open();return;}
    clickExisting("sharedBankBtn");
  }
  function openAdminConfig(){
    closePhoneAdminMenu();
    if(window.KGGAdmin&&typeof window.KGGAdmin.openConfig==="function"){window.KGGAdmin.openConfig();return;}
    clickExisting("adminConfigBtn");
  }
  function bind(id,handler){
    var el=byId(id);
    if(!el||el.dataset.kggV044Bound==="1")return;
    el.dataset.kggV044Bound="1";
    el.addEventListener("click",function(ev){ev.preventDefault();ev.stopPropagation();handler();},true);
  }
  function enhanceScanButton(){
    var scan=byId("scanBtn");
    var label=scan?scan.querySelector(".phoneScanLabel"):null;
    var toggle=byId("phonePhotoMenuToggle");
    if(scan&&!scan.classList.contains("kggPhoneLiquidAction"))scan.classList.add("kggScanButtonWithMenu","kggPhoneLiquidAction");
    if(label&&label.textContent!=="📷 Plan scannen")label.textContent="📷 Plan scannen";
    if(toggle){
      if(!toggle.classList.contains("kggPhoneLiquidChevron"))toggle.classList.add("kggPhoneLiquidChevron");
      if(toggle.textContent!=="⌃")toggle.textContent="⌃";
      if(toggle.getAttribute("aria-label")!=="Foto-Optionen oeffnen")toggle.setAttribute("aria-label","Foto-Optionen oeffnen");
      if(toggle.getAttribute("title")!=="Foto-Optionen")toggle.setAttribute("title","Foto-Optionen");
    }
    var finish=byId("finishBtn");
    if(finish&&!finish.classList.contains("kggPhoneLiquidAction"))finish.classList.add("kggPhoneLiquidAction");
  }
  function enhancePhoneAdminMenu(){
    var panel=byId("kggPhoneAdminMenuPanel");
    if(!panel||panel.dataset.kggV044Menu==="1")return;
    panel.dataset.kggV044Menu="1";
    panel.innerHTML=
      '<div class="kggPhoneMenuGroup" data-kgg-phone-menu-group="update"><div class="kggPhoneMenuGroupTitle">Update</div><button id="kggPhoneUpdateCenterMenu" type="button">Update-Zentrale</button></div>'+
      '<div class="kggPhoneMenuGroup" data-kgg-phone-menu-group="sync-share"><div class="kggPhoneMenuGroupTitle">Sync &amp; Weitergeben</div><button id="kggPhoneDeviceSyncMenu" type="button">Geräte-Sync</button><button id="kggPhoneTherapistShareMenu" type="button">Kolleg:innen-App weitergeben</button><button id="kggPhoneBankShareMenu" type="button">Übungsdatenbank teilen</button></div>'+
      '<div class="kggPhoneMenuGroup" data-kgg-phone-menu-group="admin"><div class="kggPhoneMenuGroupTitle">Admin</div><button id="kggPhoneAdminConfigMenu" type="button">Admin-Konfig</button></div>';
    bind("kggPhoneUpdateCenterMenu",openReleaseCenter);
    bind("kggPhoneDeviceSyncMenu",openDeviceSync);
    bind("kggPhoneTherapistShareMenu",openTherapistShare);
    bind("kggPhoneBankShareMenu",openSharedBank);
    bind("kggPhoneAdminConfigMenu",openAdminConfig);
  }
  function install(){
    enhanceScanButton();
    enhancePhoneAdminMenu();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,220,600,1200].forEach(function(ms){setTimeout(install,ms);});
  if(document.body){
    new MutationObserver(function(){install();}).observe(document.body,{childList:true,subtree:true});
  }
  window.KGG_UI_PHONE_LIQUID_ACTIONS_V044={patchId:PATCH_ID,install:install};
})();
</script>
<!-- KGG PATCH END kgg-v044-phone-liquid-actions -->

<!-- KGG PATCH START kgg-v045-phone-drawer-bank-align -->
<style id="kgg-v045-phone-drawer-bank-align-style">
  @media(max-width:759px){
    #createPanel{
      margin-top:clamp(28px,5dvh,44px)!important;
    }
    body.kggPhoneDrawerSafeOpen .kggPhoneDrawerBackdrop{
      opacity:1!important;
      pointer-events:auto!important;
    }
    body.kggPhoneDrawerSafeOpen #recentToggle.phoneButtonFloat,
    body.kggPhoneDrawerSafeOpen #packageToggle.phoneButtonFloat{
      position:fixed!important;
      left:16px!important;
      right:16px!important;
      bottom:calc(12px + env(safe-area-inset-bottom))!important;
      z-index:92!important;
      width:auto!important;
      min-width:0!important;
      height:58px!important;
      min-height:58px!important;
      border-radius:18px!important;
      justify-content:center!important;
      background:#fff!important;
      color:var(--ink)!important;
      border:1px solid rgba(220,227,235,.96)!important;
      box-shadow:0 22px 54px rgba(7,16,39,.26),0 5px 14px rgba(7,16,39,.12)!important;
    }
    body.kggPhoneDrawerSafeOpen #recentList:not(.hidden),
    body.kggPhoneDrawerSafeOpen #packageList:not(.hidden){
      position:fixed!important;
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
```
