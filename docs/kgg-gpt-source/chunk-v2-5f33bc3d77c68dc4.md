<!-- KGG PATCH START kgg-v095-cockpit-responsive-entry -->
<!-- Cockpit-Einstieg im Phone-Dock -->
<style id="kgg-v095-cockpit-responsive-entry-style">
  @media(max-width:759px){
    body.kggPhoneHasCockpit #scanHub{
      right:12px!important;
      grid-template-columns:minmax(0,1fr) minmax(108px,124px)!important;
      gap:8px!important;
    }
    #scanHub #kggTherapyCockpitButton.kgg-tc-entry{
      grid-column:2!important;
      grid-row:1!important;
      display:none!important;
      pointer-events:none!important;
    }
    body.kggPhoneHasCockpit #scanHub #kggTherapyCockpitButton.kgg-tc-entry{
      display:flex!important;
      align-items:center!important;
      justify-content:center!important;
      min-width:0!important;
      width:100%!important;
      height:56px!important;
      min-height:56px!important;
      margin:0!important;
      padding:0 8px!important;
      border:1px solid rgba(255,255,255,.72)!important;
      border-radius:16px!important;
      background:linear-gradient(180deg,rgba(255,255,255,.92),rgba(220,236,255,.78))!important;
      color:#071027!important;
      box-shadow:0 10px 24px rgba(7,16,39,.22),inset 0 1px 0 rgba(255,255,255,.96)!important;
      backdrop-filter:blur(18px) saturate(1.38)!important;
      -webkit-backdrop-filter:blur(18px) saturate(1.38)!important;
      font:900 13px/1.08 system-ui,sans-serif!important;
      text-align:center!important;
      white-space:normal!important;
      cursor:pointer!important;
      pointer-events:auto!important;
      touch-action:manipulation!important;
      z-index:1193!important;
    }
    body.kggPhoneHasCockpit #scanHub #kggTherapyCockpitButton.kgg-tc-entry:active{
      transform:translateY(1px)!important;
    }
    body.kggPhoneHasCockpit.kggPhoneHasPlan #createPanel.planMode #finishBtn:not(.hidden){
      bottom:calc(76px + env(safe-area-inset-bottom))!important;
    }
    body.kggPhoneHasCockpit.kggPhoneHasPlan #scanHub #scanPreview:not(.hidden){
      bottom:calc(146px + env(safe-area-inset-bottom))!important;
    }
  }
</style>

<script id="kgg-v095-cockpit-responsive-entry">
(function(){
  "use strict";
  const PATCH_ID="kgg-v095-cockpit-responsive-entry";
  const PHONE_QUERY="(max-width:759px)";
  var previousEntrySync=null;
  var installed=false;

  function byId(id){return document.getElementById(id);}
  function isPhone(){
    return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches&&!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive&&window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive()));
  }
  function cockpitState(){
    var api=window.KGGTherapyCockpit;
    return api&&typeof api.getState==="function"?api.getState():null;
  }
  function loadedPlanCount(state){
    if(state&&Number.isFinite(Number(state.slotCount)))return Math.max(0,Math.min(3,Number(state.slotCount)));
    return state&&Array.isArray(state.slots)?state.slots.filter(function(slot){return !!slot;}).length:0;
  }
  function normalPlanHasExercises(){
    var store=window.KGGDataStore;
    if(!store||typeof store.getCurrentPlan!=="function")return false;
    var plan=store.getCurrentPlan()||{};
    return Array.isArray(plan.exercises)&&plan.exercises.length>0;
  }
  function planLabel(count){return count===1?"Cockpit · 1 Plan":"Cockpit · "+count+" Pläne";}
  function sync(){
    var button=byId("kggTherapyCockpitButton"),hub=byId("scanHub"),base=byId("baseToggle"),state=cockpitState(),count=loadedPlanCount(state),phone=isPhone();
    if(!button)return;
    var hasCockpit=count>0;
    if(document.body){
      document.body.classList.toggle("kggPhoneHasCockpit",phone&&hasCockpit);
    }
    if(phone&&hasCockpit&&hub){
      if(button.parentElement!==hub)hub.appendChild(button);
      button.textContent=planLabel(count);
      button.setAttribute("aria-label","Therapie-Cockpit öffnen – "+count+" geladene "+(count===1?"Trainingsplan":"Trainingspläne"));
      button.setAttribute("title",planLabel(count));
    }else{
      if(base&&button.parentElement!==base)base.appendChild(button);
      if(!phone)button.textContent=count>0?"Cockpit "+count+"/3":"Cockpit";
      else button.textContent="Cockpit";
      button.setAttribute("aria-label","Therapie-Cockpit öffnen");
      button.removeAttribute("title");
    }
    if(!phone)button.classList.toggle("kgg-tc-entry-ready",normalPlanHasExercises()||hasCockpit);
  }
  function install(){
    if(installed)return;
    installed=true;
    previousEntrySync=window.KGGTherapyCockpitEntryVisibilitySync;
    window.KGGTherapyCockpitEntryVisibilitySync=function(){
      if(typeof previousEntrySync==="function")previousEntrySync();
      sync();
    };
    sync();
    window.addEventListener("resize",function(){setTimeout(sync,80);},{passive:true});
    window.addEventListener("orientationchange",function(){setTimeout(sync,180);},{passive:true});
    window.KGG_PATCHES=window.KGG_PATCHES||{};
    window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v094-shared-reorder-core",contract:"phone cockpit entry is visible only for loaded cockpit plans and displays loaded plan count; tablet entry stays hidden in empty state"};
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
</script>
<!-- KGG PATCH END kgg-v095-cockpit-responsive-entry -->
