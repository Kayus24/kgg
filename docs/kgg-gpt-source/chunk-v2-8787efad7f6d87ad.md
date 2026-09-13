<!-- KGG PATCH START kgg-v090-cockpit-exercises-only -->
<!-- Therapie-Cockpit ohne Basisdaten -->
<!-- Therapie-Cockpit aus Übungen ohne Basisdaten -->
<!-- Additive Ticket-037-Fortsetzung: kein neuer Plan-State, neutraler Payload-Name nur im Cockpit-Codec. -->
<script id="kgg-v090-cockpit-exercises-only-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v090-cockpit-exercises-only";
  var FALLBACK_PLAN_NAME="Übungsplan ohne Patientendaten";
  var api=window.KGGTherapyCockpit;
  var installed=false;
  function error(code){var err=new Error(code);err.code=code;return err;}
  function safeErrorCode(errorValue){
    var code=errorValue&&typeof errorValue.code==="string"?errorValue.code:"cockpit_import_failed";
    return /^[a-z0-9_]{1,48}$/.test(code)?code:"cockpit_import_failed";
  }
  function currentPlan(){
    var store=window.KGGDataStore;
    if(!store||typeof store.getCurrentPlan!=="function")throw error("plan_state_unavailable");
    return store.getCurrentPlan()||{};
  }
  function planInfo(plan){
    var source=plan||{},patient=source.patient||{};
    var name=String(patient.name||source.name||source.patientName||"").trim();
    var exercises=Array.isArray(source.exercises)?source.exercises:[];
    return {plan:source,name:name,exercises:exercises,ready:exercises.length>0};
  }
  function codecPlan(info){
    if(info.name)return info.plan;
    var patient=Object.assign({},info.plan&&info.plan.patient||{}, {name:FALLBACK_PLAN_NAME});
    return Object.assign({},info.plan,{patient:patient,name:FALLBACK_PLAN_NAME});
  }
  function clearSuccessState(){
    window.KGGTherapyCockpitLastErrorCode="";
    var toast=document.getElementById("kggTherapyCockpitToast");
    if(toast){toast.classList.remove("show");toast.textContent="";}
  }
  function notify(errorValue){
    var code=safeErrorCode(errorValue),toast=document.getElementById("kggTherapyCockpitToast");
    window.KGGTherapyCockpitLastErrorCode=code;
    if(!toast)return;
    toast.textContent="Plan konnte nicht ins Cockpit geladen werden ("+code+").";
    toast.classList.add("show");
    setTimeout(function(){toast.classList.remove("show");},3200);
  }
  function syncEntryVisibility(){
    var button=document.getElementById("kggTherapyCockpitButton");
    if(!button)return;
    var state=api&&typeof api.getState==="function"?api.getState():null;
    var ready=!!(state&&state.slotCount>0);
    if(!ready){try{ready=planInfo(currentPlan()).ready;}catch(e){ready=false;}}
    button.classList.toggle("kgg-tc-entry-ready",ready);
  }
  function installPlanStoreHook(){
    var store=window.KGGDataStore;
    if(store&&typeof store.setCurrentPlan==="function"&&!store.__kggTicket090EntryWrapped){
      var setCurrentPlan=store.setCurrentPlan;
      store.setCurrentPlan=function(){var result=setCurrentPlan.apply(this,arguments);syncEntryVisibility();return result;};
      store.__kggTicket090EntryWrapped=true;
    }
    syncEntryVisibility();
  }
  function importCurrentPlan(){
    if(!api||typeof api.getState!=="function"||typeof api.open!=="function")throw error("cockpit_unavailable");
    var state=api.getState(),info=planInfo(currentPlan());
    if(!info.ready)throw error("current_plan_not_ready");
    if(typeof api.fromPlan!=="function"||typeof api.contentKey!=="function"||typeof api.makeLink!=="function"||typeof api.importCode!=="function")throw error("cockpit_content_contract_unavailable");
    var payload=api.fromPlan(codecPlan(info)),contentKey=api.contentKey(payload);
    if(Array.isArray(state&&state.slots)&&state.slots.some(function(slot){return slot&&slot.contentKey===contentKey;})){api.open();return {reused:true,state:state};}
    if(state&&state.slotCount>=3)throw error("slots_full");
    return api.importCode(api.makeLink(payload));
  }
  function activateDirectPlan(){
    try{var state=api&&typeof api.getState==="function"?api.getState():null;if(state&&state.slotCount>0){api.open();clearSuccessState();return true;}importCurrentPlan();clearSuccessState();}
    catch(errorValue){notify(errorValue);}
    return true;
  }
  function activateFinish(event){
    event.preventDefault();
    event.stopImmediatePropagation();
    try{importCurrentPlan();clearSuccessState();var modal=document.getElementById("shareModal");if(modal)modal.classList.remove("open");}
    catch(errorValue){notify(errorValue);}
  }
  function install(){
    if(installed)return;
    installed=true;
    api=window.KGGTherapyCockpit;
    window.KGGTherapyCockpitDirectPlanClick=activateDirectPlan;
    window.KGGTherapyCockpitEntryVisibilitySync=syncEntryVisibility;
    installPlanStoreHook();
    ["finishCockpitBtn","finishCockpitGaugeBtn"].forEach(function(id){var button=document.getElementById(id);if(button)button.addEventListener("click",activateFinish,true);});
    window.KGG_PATCHES=window.KGG_PATCHES||{};
    window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v088-ticket-037-real-plan"};
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
</script>
<!-- KGG PATCH END kgg-v090-cockpit-exercises-only -->
