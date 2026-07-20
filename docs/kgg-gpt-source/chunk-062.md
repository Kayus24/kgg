# KGG Source Chunk 062

- Source: `kgg-update/src` modular source
- Lines: 26041-26460

```html
      box-shadow:inset 0 1px 0 rgba(255,255,255,.96),0 4px 12px rgba(7,16,39,.12)!important;
      font-size:24px!important;
      font-weight:1000!important;
      line-height:1!important;
      pointer-events:auto!important;
    }
    body.kggPhonePhotoMenuOpen #scanHub #scanBtn #phonePhotoMenuToggle{
      background:rgba(7,16,39,.88)!important;
      color:#fff!important;
    }
    body.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      z-index:41!important;
    }
    .kggPhonePhotoMenu{
      z-index:94!important;
      background:rgba(255,255,255,.92)!important;
      backdrop-filter:blur(18px) saturate(1.28);
      -webkit-backdrop-filter:blur(18px) saturate(1.28);
    }
    #scanHub #scanPreview:not(.hidden){z-index:70!important}
    body.kggPhoneDrawerOpen #scanHub,
    body.kggPhoneDrawerOpen #createPanel.planMode #finishBtn:not(.hidden){
      z-index:40!important;
    }
    body.kggPhoneDrawerOpen .kggPhonePhotoMenu{display:none!important}
  }
</style>

<script id="kgg-v042-phone-dock-anchored-correction-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v042-phone-dock-anchored-correction";
  var PHONE_QUERY="(max-width:759px)";
  var observer=null;
  function byId(id){return document.getElementById(id);}
  function isPhone(){return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches&&!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive()));}
  function closePhotoMenu(){
    if(document.body)document.body.classList.remove("kggPhonePhotoMenuOpen");
    var toggle=byId("phonePhotoMenuToggle");
    if(toggle)toggle.setAttribute("aria-expanded","false");
  }
  function closeAdminMenu(){
    var panel=byId("kggPhoneAdminMenuPanel");
    var btn=byId("kggPhoneAdminMenuBtn");
    if(panel)panel.hidden=true;
    if(btn)btn.setAttribute("aria-expanded","false");
  }
  function togglePhotoMenu(ev){
    if(ev){
      ev.preventDefault();
      ev.stopPropagation();
      if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
    }
    var next=!(document.body&&document.body.classList.contains("kggPhonePhotoMenuOpen"));
    if(document.body)document.body.classList.toggle("kggPhonePhotoMenuOpen",next);
    var toggle=byId("phonePhotoMenuToggle");
    if(toggle)toggle.setAttribute("aria-expanded",String(next));
    closeAdminMenu();
  }
  function anchorAdminMenu(){
    var menu=byId("kggPhoneAdminMenu");
    var header=document.querySelector("#createPanel .planHeader");
    if(menu&&header&&!header.contains(menu))header.appendChild(menu);
  }
  function restoreTabletScanButton(){
    var scan=byId("scanBtn");
    var toggle=byId("phonePhotoMenuToggle");
    if(toggle&&scan&&toggle.parentElement===scan)toggle.remove();
    if(scan&&scan.dataset.kggV042ScanHydrated==="1"){
      scan.classList.remove("kggScanButtonWithMenu");
      delete scan.dataset.kggV042ScanHydrated;
      scan.textContent="\uD83D\uDCF7 Plan scannen";
    }
  }
  function closeViewportPhoneUi(){
    closePhotoMenu();
    closeAdminMenu();
    restoreTabletScanButton();
    if(observer){
      observer.disconnect();
      observer=null;
    }
  }
  function integratePhotoToggle(){
    var scan=byId("scanBtn");
    if(!scan)return;
    var old=byId("phonePhotoMenuToggle");
    if(old&&old.parentElement!==scan)old.remove();
    if(scan.dataset.kggV042ScanHydrated==="1")return;
    scan.dataset.kggV042ScanHydrated="1";
    scan.classList.add("kggScanButtonWithMenu");
    scan.textContent="";
    var label=document.createElement("span");
    label.className="phoneScanLabel";
    label.textContent="📷 Plan scannen";
    var toggle=document.createElement("span");
    toggle.id="phonePhotoMenuToggle";
    toggle.className="phonePhotoMenuToggle";
    toggle.setAttribute("role","button");
    toggle.setAttribute("tabindex","0");
    toggle.setAttribute("aria-label","Foto-Optionen");
    toggle.setAttribute("aria-expanded","false");
    toggle.textContent="⌃";
    toggle.addEventListener("click",togglePhotoMenu,true);
    toggle.addEventListener("pointerdown",function(ev){ev.stopPropagation();},true);
    toggle.addEventListener("keydown",function(ev){
      if(ev.key==="Enter"||ev.key===" "){togglePhotoMenu(ev);}
    },true);
    scan.appendChild(label);
    scan.appendChild(toggle);
  }
  function syncLayerState(){
    if(!isPhone())closePhotoMenu();
    if(document.body&&document.body.classList.contains("kggPhoneDrawerOpen"))closePhotoMenu();
  }
  function installObserver(){
    if(observer||!document.body||!isPhone())return;
    observer=new MutationObserver(function(){
      if(isPhone())install();
    });
    observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:["class"]});
  }
  function install(){
    if(!isPhone()){
      closeViewportPhoneUi();
      return;
    }
    anchorAdminMenu();
    integratePhotoToggle();
    installObserver();
    syncLayerState();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,220,600,1200].forEach(function(ms){setTimeout(install,ms);});
  window.addEventListener("resize",function(){setTimeout(install,90);},{passive:true});
  window.addEventListener("orientationchange",function(){setTimeout(install,180);},{passive:true});
  window.KGG_UI_MINI_SERIES_V042={
    patchId:PATCH_ID,
    install:install,
    check:function(){
      var menu=byId("kggPhoneAdminMenu");
      var toggle=byId("phonePhotoMenuToggle");
      var scan=byId("scanBtn");
      return {
        patchId:PATCH_ID,
        phone:isPhone(),
        adminAnchored:!!(menu&&menu.closest("#createPanel .planHeader")),
        photoToggleInsideScan:!!(toggle&&scan&&toggle.parentElement===scan),
        dockZ:getComputedStyle(byId("scanHub")||document.body).zIndex,
        finishZ:getComputedStyle(byId("finishBtn")||document.body).zIndex
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v042-phone-dock-anchored-correction -->

<!-- SOURCE FILE: kgg-update/src/patches/v044-phone-liquid-actions.html -->

<!-- KGG PATCH START kgg-v044-phone-liquid-actions -->
<style id="kgg-v044-phone-liquid-actions-style">
  @media(max-width:759px){
    #createPanel{
      margin-top:16px!important;
    }

    #scanHub #scanBtn.kggScanButtonWithMenu,
    body.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      border:1px solid rgba(255,255,255,.9)!important;
      background:
        radial-gradient(circle at 18% 8%,rgba(255,255,255,.98),rgba(255,255,255,.58) 42%,rgba(232,241,252,.46) 100%),
        linear-gradient(180deg,rgba(255,255,255,.94),rgba(236,244,253,.68))!important;
      color:#071027!important;
      box-shadow:
        0 22px 48px rgba(7,16,39,.20),
        0 5px 16px rgba(7,16,39,.10),
        inset 0 1px 0 rgba(255,255,255,1),
        inset 0 -1px 0 rgba(124,149,178,.16)!important;
      backdrop-filter:blur(30px) saturate(1.72) contrast(1.04)!important;
      -webkit-backdrop-filter:blur(30px) saturate(1.72) contrast(1.04)!important;
    }

    #scanHub #scanBtn.kggScanButtonWithMenu{
      min-height:60px!important;
      height:60px!important;
      border-radius:22px!important;
      padding:0 8px 0 18px!important;
      gap:12px!important;
      align-items:center!important;
      justify-content:space-between!important;
    }
    #scanHub #scanBtn.kggScanButtonWithMenu .phoneScanLabel{
      display:inline-flex!important;
      align-items:center!important;
      gap:8px!important;
      min-width:0!important;
      color:#071027!important;
      font-size:17px!important;
      font-weight:1000!important;
      letter-spacing:-.2px!important;
    }
    #scanHub #scanBtn.kggScanButtonWithMenu #phonePhotoMenuToggle{
      position:relative!important;
      flex:0 0 50px!important;
      width:50px!important;
      min-width:50px!important;
      height:50px!important;
      min-height:50px!important;
      border:0!important;
      border-radius:18px!important;
      background:rgba(255,255,255,.38)!important;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.96)!important;
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

<!-- SOURCE FILE: kgg-update/src/patches/v045-phone-drawer-bank-align.html -->

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
```
