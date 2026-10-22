<!-- KGG PATCH START kgg-v098-cockpit-tablet-edge-navigation -->
<!-- Therapie-Cockpit: Tablet-Randnavigation -->
<style id="kgg-v098-cockpit-tablet-edge-navigation-style">
  @media(min-width:760px){
    body:not(.kggTherapyCockpitOpen) #kggTherapyCockpitButton.kggTcTabletEdge,
    body.kggTherapyCockpitOpen #kggTherapyCockpitButton.kggTcTabletEdge{
      position:fixed!important;top:50%!important;left:auto!important;right:0!important;z-index:2147481500!important;
      box-sizing:border-box!important;display:flex!important;align-items:center!important;justify-content:center!important;
      width:52px!important;min-width:52px!important;max-width:52px!important;min-height:48px!important;height:auto!important;
      margin:0!important;padding:8px 4px!important;border:1px solid rgba(255,255,255,.72)!important;
      border-right:0!important;border-radius:12px 0 0 12px!important;background:rgba(239,246,255,.84)!important;
      color:#17233a!important;box-shadow:0 6px 18px rgba(15,23,42,.2),inset 0 1px 0 rgba(255,255,255,.82)!important;
      backdrop-filter:blur(14px) saturate(1.25)!important;-webkit-backdrop-filter:blur(14px) saturate(1.25)!important;
      font:800 12px/1.15 system-ui,sans-serif!important;text-align:center!important;white-space:normal!important;
      transform:translateY(-50%)!important;touch-action:manipulation!important;cursor:pointer!important;
    }
    body:not(.kggTherapyCockpitOpen) #kggTherapyCockpitButton.kggTcTabletEdge:not(.kgg-tc-entry-ready){display:none!important;}
    body.kggTherapyCockpitOpen #kggTherapyCockpitButton.kggTcTabletEdge{left:0!important;right:auto!important;border-left:0!important;border-right:1px solid rgba(255,255,255,.72)!important;border-radius:0 12px 12px 0!important;}
    body.kggTherapyCockpitOpen #kggTherapyCockpitButton.kggTcTabletEdge{background:rgba(248,250,252,.82)!important;color:#334155!important;}
    @media(max-width:1100px){
      body.kggTherapyCockpitOpen.kggTcSlots1 .app>.adminTestBanner{display:none!important;}
      body.kggTherapyCockpitOpen.kggTcSlots1 .app>.topbar #kggRuntimeVersion,
      body.kggTherapyCockpitOpen.kggTcSlots1 .app>.topbar .kggBuildBadge{display:none!important;}
      body.kggTherapyCockpitOpen.kggTcSlots1 .app>.panel{order:0!important;}
      body.kggTherapyCockpitOpen.kggTcSlots1 .app>.scanHub{order:1!important;}
    }
    body.kggTherapyCockpitOpen .kgg-tc-actions [data-tc-action="import-open"]{
      border-color:#cbd5e1!important;background:#f8fafc!important;color:#334155!important;box-shadow:none!important;
    }
  }
</style>
<script id="kgg-v098-cockpit-tablet-edge-navigation">
(function(){
  "use strict";
  const PATCH_ID="kgg-v098-cockpit-tablet-edge-navigation";
  const TABLET_QUERY="(min-width:760px)";
  var api=null,button=null,installed=false,previousVisibilitySync=null,previousDirectPlanClick=null,pointerStart=null;
  function isTablet(){return !!(window.matchMedia&&window.matchMedia(TABLET_QUERY).matches);}
  function slotCount(){
    try{var state=api&&api.getState?api.getState():{};return Number.isFinite(Number(state&&state.slotCount))?Math.max(0,Math.min(3,Number(state.slotCount))):Array.isArray(state&&state.slots)?state.slots.filter(Boolean).length:0;}catch(error){return 0;}
  }
  function sync(){
    if(!api||!document.body)return;
    button=document.getElementById("kggTherapyCockpitButton");if(!button)return;
    if(isTablet()){
      button.classList.add("kggTcTabletEdge");
      if(button.parentElement!==document.body)document.body.appendChild(button);
      if(document.body.classList.contains("kggTherapyCockpitOpen")){
        button.textContent="KGG";button.setAttribute("aria-label","Zur Therapeuten-App zurückkehren");button.setAttribute("title","Zur Therapeuten-App");
      }else{
        var count=slotCount();button.textContent=count?"Cockpit "+count+"/3":"Cockpit";
        button.setAttribute("aria-label",count?"Therapie-Cockpit öffnen – "+count+" von 3 Plänen":"Therapie-Cockpit öffnen");button.setAttribute("title",count?"Therapie-Cockpit öffnen":"Therapie-Cockpit öffnen");
      }
    }else button.classList.remove("kggTcTabletEdge");
  }
  function isInteractive(target){
    return !!(target&&target.closest&&target.closest("button,a,input,textarea,select,[role=button],[data-tc-action],[data-tce-action],.modal,#editorModal,.editorSheet,.kgg-tce-modal,.kgg-tc-modal,.kgg015ProgressionBox,.kgg015ProgressionDetails,.kgg015ProgressionBody,.kgg015StageRail,.kgg015StageCard,.kgg015AddPanel,.kgg015DeleteDialog,.kgg-tc-scroll,.kgg-tc-board,.planCard,.planList,.bankRows,.az,.tabletSideMenu,.tabletPackageCards,.editorRail"));
  }
  function onPointerDown(event){
    if(!isTablet()||event.pointerType!=="touch"||event.isPrimary===false||isInteractive(event.target))return;
    var edge=22,width=document.documentElement.clientWidth||window.innerWidth;
    if(event.clientX<=edge)pointerStart={x:event.clientX,y:event.clientY,t:Date.now(),id:event.pointerId,side:"left"};
    else if(event.clientX>=width-edge)pointerStart={x:event.clientX,y:event.clientY,t:Date.now(),id:event.pointerId,side:"right"};
    else pointerStart=null;
  }
  function onPointerUp(event){
    var start=pointerStart;pointerStart=null;if(!start||event.pointerId!==start.id||Date.now()-start.t>1000)return;
    var dx=event.clientX-start.x,dy=event.clientY-start.y;
    if(Math.abs(dx)<72||Math.abs(dx)<Math.abs(dy)*1.25)return;
    var count=slotCount(),open=document.body.classList.contains("kggTherapyCockpitOpen");
    if(start.side==="right"&&dx<0&&!open){if(count>0)api.open();else if(typeof previousDirectPlanClick==="function")previousDirectPlanClick(event);}
    else if(start.side==="left"&&dx>0&&open&&count>0)api.close();
  }
  function syncAfterResize(){window.setTimeout(sync,120);}
  function install(){
    if(installed)return;api=window.KGGTherapyCockpit;
    if(!api||typeof api.open!=="function"||typeof api.close!=="function"||!document.getElementById("kggTherapyCockpitButton")){window.setTimeout(install,50);return;}
    installed=true;previousVisibilitySync=window.KGGTherapyCockpitEntryVisibilitySync;
    window.KGGTherapyCockpitEntryVisibilitySync=function(){if(typeof previousVisibilitySync==="function")previousVisibilitySync();sync();};
    previousDirectPlanClick=window.KGGTherapyCockpitDirectPlanClick;
    window.KGGTherapyCockpitDirectPlanClick=function(event){
      if(isTablet()&&document.body.classList.contains("kggTherapyCockpitOpen")){api.close();return true;}
      return typeof previousDirectPlanClick==="function"?previousDirectPlanClick(event):false;
    };
    document.addEventListener("pointerdown",onPointerDown,{capture:true,passive:true});
    document.addEventListener("pointerup",onPointerUp,{capture:true,passive:true});
    document.addEventListener("pointercancel",function(){pointerStart=null;},{capture:true,passive:true});
    window.addEventListener("resize",syncAfterResize,{passive:true});window.addEventListener("orientationchange",syncAfterResize,{passive:true});
    sync();window.KGG_PATCHES=window.KGG_PATCHES||{};
    window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v097-cockpit-independent-tablet-scroll",contract:"tablet uses the existing cockpit entry as a half-transparent edge switch on the right in normal mode and left while open; touch edge swipes switch only between existing view APIs and ignore interactive/list gesture origins"};
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
</script>
<!-- KGG PATCH END kgg-v098-cockpit-tablet-edge-navigation -->
