# KGG Source Chunk 063

- Source: `kgg-update/index.html`
- Lines: 26461-26880

```html
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

<!-- KGG PATCH START kgg-v051-android-qr-pdf-bridge -->
<script id="kgg-v051-android-qr-pdf-bridge-probe">
window.KGG_ANDROID_QR_PDF_BRIDGE_V051={
  patchId:'kgg-v051-android-qr-pdf-bridge',
  qrPrintButtonId:'kggAdminMenuQrPrint',
  androidShellVersion:'v399'
};
</script>
<!-- KGG PATCH END kgg-v051-android-qr-pdf-bridge -->

<!-- KGG PATCH START kgg-v052-pdf-plan-thumbnails -->
<script id="kgg-v052-pdf-plan-thumbnails-probe">
window.KGG_PDF_PLAN_THUMBNAILS_V052={
  patchId:'kgg-v052-pdf-plan-thumbnails',
  snapshotHelper:'attachKggPdfExerciseThumbnails',
  drawTarget:'drawKggExerciseBox'
};
</script>
<!-- KGG PATCH END kgg-v052-pdf-plan-thumbnails -->

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
      z-index:82!important;
    }
    body.tabletLayoutCustom #tabletMenuBtn{
      position:fixed!important;
      left:10px!important;
      top:var(--kgg-tablet-safe-top)!important;
      z-index:1505!important;
      pointer-events:auto!important;
    }
    #editorModal .editorSheet{
      width:min(94vw,920px)!important;
      max-height:min(90vh,760px)!important;
      overflow:hidden!important;
      display:grid!important;
      grid-template-columns:minmax(0,1fr) minmax(300px,.92fr)!important;
      grid-template-areas:
        "header header"
        "name media"
        "sets media"
        "units media"
        "start media"
        "advanced media"
        "actions actions"
        "cancel cancel"!important;
      column-gap:14px!important;
      row-gap:9px!important;
      padding:16px!important;
    }
    #editorModal .editorHeader{grid-area:header!important;margin-bottom:0!important}
    #editorModal .editorSheet > .field:first-of-type{grid-area:name!important;margin:0!important}
    #editorModal .editorSheet > .grid2:nth-of-type(1){grid-area:sets!important}
    #editorModal .editorSheet > .grid2:nth-of-type(2){grid-area:units!important}
    #editorModal .editorStartHint{grid-area:start!important;margin:0!important}
    #editorModal .editorMediaBox{
      grid-area:media!important;
      margin:0!important;
      min-height:0!important;
      display:grid!important;
      grid-template-rows:auto minmax(190px,1fr) auto!important;
      align-self:stretch!important;
    }
    #editorModal .editorMediaPreview{
      min-height:190px!important;
      max-height:min(42vh,330px)!important;
      overflow:hidden!important;
    }
    #editorModal .editorMediaPreview img{
      width:100%!important;
      height:100%!important;
      object-fit:contain!important;
    }
    #editorModal .editorAdvanced{
      grid-area:advanced!important;
      margin:0!important;
      max-height:112px!important;
      overflow:auto!important;
    }
    #editorModal .editorActions{
      grid-area:actions!important;
      margin:0!important;
    }
    #editorModal .editorCancelBtn{
      grid-area:cancel!important;
      margin:0!important;
    }
  }
</style>
<script id="kgg-v053-ui-tablet-stability-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v053-ui-tablet-stability";
  function byId(id){return document.getElementById(id);}
  function isTablet(){
    return !!(window.matchMedia&&window.matchMedia("(min-width:760px)").matches&&document.body&&document.body.classList.contains("tabletLayoutCustom"));
  }
  function anchorTabletMenuButton(){
    var btn=byId("tabletMenuBtn");
    var hub=byId("scanHub");
    if(!btn||!hub||!document.body)return;
    if(isTablet()){
      if(btn.parentElement!==document.body)document.body.appendChild(btn);
      return;
    }
    if(btn.parentElement!==hub)hub.insertBefore(btn,hub.firstChild);
  }
  function resetTabletSwipe(card){
    if(!card)return;
    card.classList.remove("swipe-dragging","swipe-armed","swipe-left","swipe-right","swipe-removing");
    document.body.classList.remove("kggPlanCardSwiping");
    card.style.removeProperty("transform");
    card.style.removeProperty("opacity");
    card.style.removeProperty("transition");
    card.style.removeProperty("--swipe-strength");
    card.style.removeProperty("--kgg-plan-swipe-x");
  }
  function startTabletSwipeForCard(ev,card){
    if(!isTablet())return;
    if(!card)return;
    if(ev.button!=null&&ev.button!==0)return;
    if(ev.target&&ev.target.closest&&ev.target.closest("button,input,textarea,select,a,.planCardActions,.drag"))return;
    var pointerKey=String(ev.pointerId||"mouse");
    if(card.dataset.kggV053SwipePointer===pointerKey)return;
    card.dataset.kggV053SwipePointer=pointerKey;
    card.dataset.kggV053SwipeStarted="1";
    var planId=card.dataset&&card.dataset.planId?String(card.dataset.planId):"";
    function currentCard(){
      if(card&&card.isConnected)return card;
      if(planId){
        var cards=Array.from(document.querySelectorAll("#planList .planCard[data-plan-id]"));
        var live=cards.find(function(node){return node.dataset&&String(node.dataset.planId)===planId;});
        if(live)return live;
      }
      return card;
    }
    var startX=ev.clientX,startY=ev.clientY,pointerId=ev.pointerId,active=false,dx=0,cancelTimer=null;
    function threshold(){var live=currentCard();return Math.min(132,Math.max(78,(live?live.offsetWidth:0)*0.34));}
    function cleanup(){
      clearTimeout(cancelTimer);
      delete card.dataset.kggV053SwipePointer;
      document.removeEventListener("pointermove",move,true);
      document.removeEventListener("pointerup",up,true);
      document.removeEventListener("pointercancel",cancel,true);
    }
    function move(e){
      var live=currentCard();
      if(!live){cleanup();return;}
      dx=e.clientX-startX;
      var dy=e.clientY-startY;
      if(!active){
        if(Math.abs(dy)>10&&Math.abs(dy)>Math.abs(dx)*1.2){cleanup();return;}
        if(Math.abs(dx)<12||Math.abs(dx)<Math.abs(dy)*1.25)return;
        active=true;
        document.body.classList.add("kggPlanCardSwiping");
        live.classList.add("swipe-dragging");
        try{live.setPointerCapture&&live.setPointerCapture(pointerId);}catch(err){}
      }
      e.preventDefault();
      if(e.stopImmediatePropagation)e.stopImmediatePropagation();
      dx=Math.max(-live.offsetWidth*.86,Math.min(live.offsetWidth*.86,dx));
      var strength=Math.min(1,Math.abs(dx)/threshold());
      live.classList.toggle("swipe-left",dx<0);
      live.classList.toggle("swipe-right",dx>0);
      live.classList.toggle("swipe-armed",Math.abs(dx)>=threshold());
      live.style.setProperty("--swipe-strength",String(strength));
      live.style.setProperty("--kgg-plan-swipe-x",dx+"px");
      live.style.transform="translateX(var(--kgg-plan-swipe-x,0px))";
      live.style.opacity=String(1-strength*.16);
    }
    function up(e){
      var live=currentCard();
      cleanup();
      if(!active){resetTabletSwipe(live);return;}
      e.preventDefault();
      document.body.classList.remove("kggPlanCardSwiping");
      if(Math.abs(dx)>=threshold()){
        live.classList.add("swipe-removing");
        live.style.transition="transform .18s cubic-bezier(.2,.9,.2,1), opacity .18s ease";
        live.style.setProperty("--kgg-plan-swipe-x",((dx<0?-1:1)*(live.offsetWidth+96))+"px");
        live.style.opacity="0";
        setTimeout(function(){
          var del=live.querySelector(".planDeleteBtn,[data-del]");
          if(del&&typeof del.click==="function")del.click();
        },160);
        return;
      }
      live.style.transition="transform .22s cubic-bezier(.2,.9,.2,1), opacity .18s ease";
      live.style.setProperty("--kgg-plan-swipe-x","0px");
      live.style.opacity="1";
      setTimeout(function(){resetTabletSwipe(live);},230);
    }
    function cancel(){
      var live=currentCard();
      if(active){
        clearTimeout(cancelTimer);
        cancelTimer=setTimeout(function(){cleanup();resetTabletSwipe(currentCard());},900);
        return;
      }
      cleanup();
      resetTabletSwipe(live);
    }
    document.addEventListener("pointermove",move,true);
    document.addEventListener("pointerup",up,true);
    document.addEventListener("pointercancel",cancel,true);
  }
  function startTabletSwipe(ev){
    startTabletSwipeForCard(ev,ev.currentTarget);
  }
  function bindTabletSwipeGuard(){
    if(!document.body)return;
    if(document.documentElement&&!document.documentElement.dataset.kggV053TabletSwipeDocumentGuard){
      document.documentElement.dataset.kggV053TabletSwipeDocumentGuard="1";
      document.addEventListener("pointerdown",function(ev){
        if(!isTablet())return;
        var target=ev.target;
        var card=target&&target.closest&&target.closest("#planList .planCard[data-plan-id]");
        if(card)startTabletSwipeForCard(ev,card);
      },true);
    }
    document.querySelectorAll("#planList .planCard[data-plan-id]").forEach(function(card){
      if(card.dataset.kggV053TabletSwipeGuard==="1")return;
      card.dataset.kggV053TabletSwipeGuard="1";
      card.addEventListener("pointerdown",startTabletSwipe,true);
      card.onpointerdown=card.onpointerdown||startTabletSwipe;
    });
  }
  function install(){
    var menu=byId("kggPhoneAdminMenu");
    var header=document.querySelector("#createPanel.planMode .planHeader")||document.querySelector("#createPanel .planHeader");
    if(menu&&header&&!header.contains(menu))header.appendChild(menu);
    anchorTabletMenuButton();
    bindTabletSwipeGuard();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,240,700].forEach(function(ms){setTimeout(install,ms);});
  window.addEventListener("resize",function(){setTimeout(install,80);},{passive:true});
  window.addEventListener("orientationchange",function(){setTimeout(install,160);},{passive:true});
  if(document.body){
    new MutationObserver(function(){install();}).observe(document.body,{attributes:true,attributeFilter:["class"],childList:true,subtree:true});
  }
  window.KGG_UI_TABLET_STABILITY_V053={
    patchId:PATCH_ID,
    install:install,
    check:function(){
      var menu=byId("kggPhoneAdminMenu");
```
