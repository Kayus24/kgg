
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
