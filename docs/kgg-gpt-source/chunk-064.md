# KGG Source Chunk 064

- Source: `kgg-update/index.html`
- Lines: 26881-27183

```html
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
      var editor=document.querySelector("#editorModal .editorSheet");
      return {
        patchId:PATCH_ID,
        menuAnchored:!!(menu&&menu.closest("#createPanel .planHeader")),
        editorDisplay:editor?getComputedStyle(editor).display:"",
        editorColumns:editor?getComputedStyle(editor).gridTemplateColumns:""
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v053-ui-tablet-stability -->
<!-- KGG PATCH START kgg-v060-tablet-html-release-label -->
<!-- Tablet HTML Release Label -->
<style id="kgg-v060-tablet-html-release-label-style">
#kggTabletHtmlReleaseLabel{display:none}
@media (min-width:760px){
  #tabletSideMenu{
    overflow-y:hidden!important;
  }
  #tabletSideMenu .tabletSideMenuMain{
    flex:1 1 auto;
    min-height:0;
    overflow-y:auto!important;
    align-content:start;
  }
  #tabletSideMenu #kggTabletHtmlReleaseLabel{
    display:block;
    flex:0 0 auto;
    align-self:flex-end;
    max-width:100%;
    margin:0;
    padding:5px 7px;
    border:1px solid rgba(10,16,36,.10);
    border-radius:9px;
    background:rgba(255,255,255,.94);
    color:#667085;
    font-size:10px;
    font-weight:850;
    line-height:1.2;
    overflow-wrap:anywhere;
    text-align:right;
    pointer-events:none;
  }
}
</style>
<script id="kgg-v060-tablet-html-release-label">
(function(){
  "use strict";
  var PATCH_ID="kgg-v060-tablet-html-release-label";

  function parseStatus(value){
    if(value&&typeof value==="object")return value;
    if(typeof value!=="string"||!value.trim())return {};
    try{return JSON.parse(value);}catch(err){return {};}
  }

  function nativeStatus(){
    try{
      if(window.KGGAndroidApp&&typeof window.KGGAndroidApp.updateStatus==="function"){
        return parseStatus(window.KGGAndroidApp.updateStatus());
      }
      if(window.KGGNativeAppUpdate&&typeof window.KGGNativeAppUpdate.status==="function"){
        return parseStatus(window.KGGNativeAppUpdate.status());
      }
    }catch(err){}
    return {};
  }

  function fileName(value){
    var clean=String(value||"").split(/[?#]/)[0].replace(/\\/g,"/");
    var parts=clean.split("/").filter(Boolean);
    var last=parts.pop()||"";
    try{return decodeURIComponent(last);}catch(err){return last;}
  }

  function buildInfo(){
    try{if(typeof KGG_BUILD_INFO!=="undefined"&&KGG_BUILD_INFO)return KGG_BUILD_INFO;}catch(err){}
    if(window.KGG_BUILD_INFO)return window.KGG_BUILD_INFO;
    try{
      var source=document.getElementById("kgg-source-truth");
      var data=source?JSON.parse(source.textContent||"{}"):{};
      var current=data.currentVersion||{};
      var code=Number(current.versionCode);
      if(Number.isFinite(code))return {release:"v"+String(code).padStart(3,"0"),versionName:current.versionName||"",htmlFile:"kgg-update/index.html"};
    }catch(err){}
    return {};
  }

  function currentIdentity(){
    var native=nativeStatus();
    var info=buildInfo();
    var path=String((window.location&&window.location.pathname)||"");
    var release=String(native.releaseId||"").trim();
    var pathRelease=path.match(/\/releases\/web\/(r[0-9]+)\//i);
    if(!release&&pathRelease)release=pathRelease[1].toLowerCase();
    var build=info.release||"";
    var source=fileName(native.loadedHtmlSource)||fileName(path)||fileName(info.htmlFile)||"index.html";
    var parts=[];
    if(release)parts.push(release);
    if(build&&build!==release)parts.push(build);
    parts.push(source);
    return "HTML "+parts.join(" · ");
  }

  function render(){
    var label=document.getElementById("kggTabletHtmlReleaseLabel");
    if(!label)return;
    var text=currentIdentity();
    label.textContent=text;
    label.title=text;
  }

  function install(){
    var menu=document.getElementById("tabletSideMenu");
    if(!menu)return false;
    var label=document.getElementById("kggTabletHtmlReleaseLabel");
    if(!label){
      label=document.createElement("small");
      label.id="kggTabletHtmlReleaseLabel";
      label.setAttribute("aria-label","Aktuell geladene HTML-Version");
      menu.appendChild(label);
    }
    render();
    var button=document.getElementById("tabletMenuBtn");
    if(button&&!button.dataset.kggHtmlReleaseLabelBound){
      button.dataset.kggHtmlReleaseLabelBound="1";
      button.addEventListener("click",function(){window.setTimeout(render,0);});
    }
    return true;
  }

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  window.addEventListener("pageshow",render);
  document.addEventListener("visibilitychange",function(){if(!document.hidden)render();});

  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true,render:render,currentIdentity:currentIdentity};
})();
</script>
<!-- KGG PATCH END kgg-v060-tablet-html-release-label -->

</body>
</html>
```
