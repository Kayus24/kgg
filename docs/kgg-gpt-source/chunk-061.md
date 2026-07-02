# KGG Source Chunk 061

- Source: `kgg-update/index.html`
- Lines: 25621-26040

```html
  }
  function ensurePhoneAdminMenu(){
    if(byId("kggPhoneAdminMenu"))return;
    var root=document.createElement("div");
    root.id="kggPhoneAdminMenu";
    root.className="kggPhoneAdminMenu";
    root.innerHTML='<button id="kggPhoneAdminMenuBtn" class="kggPhoneAdminMenuBtn" type="button" aria-label="Admin-Menue" aria-expanded="false"><span aria-hidden="true">&#8942;</span></button><div id="kggPhoneAdminMenuPanel" class="kggPhoneAdminMenuPanel" hidden><button id="kggPhoneAdminConfigMenu" type="button">Admin-Konfig</button><button id="kggPhoneBankShareMenu" type="button">Uebungsdatenbank teilen</button><button id="kggPhoneQrShareMenu" type="button">QR-Code teilen</button></div>';
    document.body.appendChild(root);
    byId("kggPhoneAdminMenuBtn").addEventListener("click",function(ev){
      ev.preventDefault();
      ev.stopPropagation();
      var panel=byId("kggPhoneAdminMenuPanel");
      var next=!!(panel&&panel.hidden);
      if(panel)panel.hidden=!next;
      this.setAttribute("aria-expanded",String(next));
      closePhonePhotoMenu();
    });
    byId("kggPhoneAdminConfigMenu").addEventListener("click",function(){closePhoneAdminMenu(); if(window.KGGAdmin&&typeof window.KGGAdmin.openConfig==="function")window.KGGAdmin.openConfig(); else clickExisting("adminConfigBtn");});
    byId("kggPhoneBankShareMenu").addEventListener("click",function(){closePhoneAdminMenu(); if(window.KGGSharedBank&&typeof window.KGGSharedBank.open==="function")window.KGGSharedBank.open(); else clickExisting("sharedBankBtn");});
    byId("kggPhoneQrShareMenu").addEventListener("click",function(){closePhoneAdminMenu(); clickExisting("syncQrBtn");});
    document.addEventListener("click",function(ev){
      var menu=byId("kggPhoneAdminMenu");
      if(menu&&!menu.contains(ev.target))closePhoneAdminMenu();
    },true);
  }
  function closePhonePhotoMenu(){
    document.body&&document.body.classList.remove("kggPhonePhotoMenuOpen");
    var btn=byId("phonePhotoMenuToggle");
    if(btn)btn.setAttribute("aria-expanded","false");
  }
  function closePhoneUi(){
    closePhonePhotoMenu();
    closePhoneAdminMenu();
    if(document.body){
      document.body.classList.remove("kggPhoneHasPlan","kggPhonePhotoMenuOpen");
    }
    if(observer){
      observer.disconnect();
      observer=null;
    }
  }
  function ensurePhonePhotoMenu(){
    var hub=byId("scanHub");
    var scan=byId("scanBtn");
    if(!hub||!scan)return;
    if(!byId("phonePhotoMenuToggle")){
      var toggle=document.createElement("button");
      toggle.id="phonePhotoMenuToggle";
      toggle.className="phonePhotoMenuToggle";
      toggle.type="button";
      toggle.setAttribute("aria-label","Foto-Optionen");
      toggle.setAttribute("aria-expanded","false");
      toggle.innerHTML='<span aria-hidden="true">&#9652;</span>';
      scan.insertAdjacentElement("afterend",toggle);
      toggle.addEventListener("click",function(ev){
        ev.preventDefault();
        ev.stopPropagation();
        var next=!document.body.classList.contains("kggPhonePhotoMenuOpen");
        document.body.classList.toggle("kggPhonePhotoMenuOpen",next);
        this.setAttribute("aria-expanded",String(next));
        closePhoneAdminMenu();
      });
    }
    if(!byId("kggPhonePhotoMenu")){
      var panel=document.createElement("div");
      panel.id="kggPhonePhotoMenu";
      panel.className="kggPhonePhotoMenu";
      panel.innerHTML='<button id="phonePhotoCamera" type="button">Foto aufnehmen</button><button id="phonePhotoGallery" type="button">Aus Galerie hochladen</button>';
      document.body.appendChild(panel);
      byId("phonePhotoCamera").addEventListener("click",function(){closePhonePhotoMenu(); if(window.KGGScan&&typeof window.KGGScan.pick==="function")window.KGGScan.pick("camera");});
      byId("phonePhotoGallery").addEventListener("click",function(){closePhonePhotoMenu(); if(window.KGGScan&&typeof window.KGGScan.pick==="function")window.KGGScan.pick("file"); else clickExisting("filePickBtn");});
      document.addEventListener("click",function(ev){
        var panel=byId("kggPhonePhotoMenu");
        var toggle=byId("phonePhotoMenuToggle");
        if(panel&&!panel.contains(ev.target)&&toggle&&!toggle.contains(ev.target))closePhonePhotoMenu();
      },true);
    }
  }
  function syncPhonePlanState(){
    if(!isPhone()){
      closePhoneUi();
      return;
    }
    var createPanel=byId("createPanel");
    var hasPlan=!!(createPanel&&createPanel.classList.contains("planMode"))||!!document.querySelector("#planList .planCard[data-plan-id]");
    document.body.classList.toggle("kggPhoneHasPlan",hasPlan);
  }
  function installObserver(){
    if(observer||!document.body||!isPhone())return;
    observer=new MutationObserver(function(){syncPhonePlanState();});
    observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:["class"]});
  }
  function install(){
    if(!document.body)return;
    if(!isPhone()){
      closePhoneUi();
      return;
    }
    ensurePhoneAdminMenu();
    ensurePhonePhotoMenu();
    installObserver();
    syncPhonePlanState();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  window.addEventListener("resize",function(){setTimeout(install,80);},{passive:true});
  window.addEventListener("orientationchange",function(){setTimeout(install,180);},{passive:true});
  window.KGG_UI_MINI_SERIES={
    patchId:PATCH_ID,
    check:function(){
      return {
        patchId:PATCH_ID,
        phone:isPhone(),
        adminMenu:!!byId("kggPhoneAdminMenu"),
        photoToggle:!!byId("phonePhotoMenuToggle"),
        photoMenu:!!byId("kggPhonePhotoMenu"),
        phoneHasPlan:!!(document.body&&document.body.classList.contains("kggPhoneHasPlan")),
        bankThumbnails:document.querySelectorAll("[data-bank-thumb-id]").length
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v041-ui-mini-series -->

<!-- KGG PATCH START kgg-v042-phone-dock-anchored-correction -->
<style id="kgg-v042-phone-dock-anchored-correction-style">
  @media(max-width:759px){
    #createPanel .planHeader{
      position:relative;
      grid-template-columns:minmax(0,1fr) auto auto;
    }
    body.adminMode #createPanel .planHeader .kggPhoneAdminMenu{
      display:block;
      position:relative!important;
      right:auto!important;
      top:auto!important;
      z-index:46!important;
      align-self:center;
      justify-self:end;
      grid-column:auto;
    }
    body.adminMode > .kggPhoneAdminMenu{display:none!important}
    #createPanel .planHeader .kggPhoneAdminMenuBtn{
      width:42px;
      height:42px;
      min-width:42px;
      min-height:42px;
      border-radius:15px;
      border:1px solid rgba(255,255,255,.72);
      background:linear-gradient(180deg,rgba(255,255,255,.86),rgba(238,244,252,.64));
      color:#071027;
      box-shadow:0 10px 24px rgba(7,16,39,.14),inset 0 1px 0 rgba(255,255,255,.9);
      backdrop-filter:blur(16px) saturate(1.35);
      -webkit-backdrop-filter:blur(16px) saturate(1.35);
    }
    #createPanel .planHeader .kggPhoneAdminMenuPanel{
      top:calc(100% + 8px);
      right:0;
      z-index:96;
      background:rgba(255,255,255,.92);
      backdrop-filter:blur(18px) saturate(1.28);
      -webkit-backdrop-filter:blur(18px) saturate(1.28);
    }

    #scanHub{
      grid-template-columns:minmax(0,1fr)!important;
      z-index:40!important;
    }
    #scanHub > .phonePhotoMenuToggle{display:none!important}
    #scanHub #scanBtn,
    body.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      border:1px solid rgba(255,255,255,.68)!important;
      background:
        linear-gradient(180deg,rgba(255,255,255,.86),rgba(233,242,252,.58))!important;
      color:#071027!important;
      box-shadow:0 14px 30px rgba(7,16,39,.18),inset 0 1px 0 rgba(255,255,255,.95)!important;
      backdrop-filter:blur(18px) saturate(1.38)!important;
      -webkit-backdrop-filter:blur(18px) saturate(1.38)!important;
    }
    #scanHub #scanBtn{
      display:flex!important;
      grid-column:1!important;
      justify-content:space-between!important;
      gap:10px!important;
      padding:0 7px 0 18px!important;
      text-align:left!important;
    }
    #scanHub #scanBtn .phoneScanLabel{
      min-width:0;
      flex:1 1 auto;
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
    }
    #scanHub #scanBtn #phonePhotoMenuToggle{
      position:static!important;
      display:inline-flex!important;
      flex:0 0 46px;
      width:46px!important;
      height:46px!important;
      min-width:46px!important;
      min-height:46px!important;
      align-items:center!important;
      justify-content:center!important;
      border-radius:14px!important;
      border:1px solid rgba(255,255,255,.82)!important;
      background:rgba(255,255,255,.74)!important;
      color:#071027!important;
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
```
