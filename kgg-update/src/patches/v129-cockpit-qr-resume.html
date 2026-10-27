<!-- KGG PATCH START kgg-v129-cockpit-qr-resume -->
<!-- Cockpit-Link nach Patienten-QR mit manueller Prioritaet -->
<style id="kgg-v129-cockpit-qr-resume-style">
  .kgg-tc-notes-label{display:grid;gap:6px;margin-top:14px;font-size:14px;font-weight:700;min-width:0}
  .kgg-tc-notes-label textarea{box-sizing:border-box;min-height:72px;width:100%;resize:vertical;font:inherit;font-weight:400}
  #kggTherapyCockpitActivationLink{display:block;box-sizing:border-box;text-align:center;text-decoration:none;overflow-wrap:anywhere;margin:10px 0}
</style>
<script id="kgg-v129-cockpit-qr-resume">
(function(){
  "use strict";
  const PATCH_ID="kgg-v129-cockpit-qr-resume";
  var api=window.KGGTherapyCockpit;
  function fail(code){var error=new Error(code);error.code=code;throw error;}
  function currentSnapshot(planId){
    var state=api.getState(),entry=state.slots.find(function(slot){return slot&&slot.planId===planId;});
    return entry?api.getSlot(entry.slot):api.getResumePlan(planId);
  }
  function pair(value){if(!Array.isArray(value)||value.length!==2)fail("return_set_invalid");return [value[0]==null?"":String(value[0]),value[1]==null?"":String(value[1])];}
  function sideValue(value,index){var parts=String(value==null?"":value).split(/\s*\/\s*/);return parts.length===2?parts[index]:parts[0];}
  function scanPayload(result,primaryNames){
    if(!result||["KGGH2","KGGH3","KGGD1"].indexOf(result.qrType)<0)return null;
    var data=result.json||{},isReturn=result.qrType==="KGGD1",planId=String(isReturn?data.i||"":data.meta&&data.meta.planId||"").trim();
    if(!planId)fail("plan_id_required");
    var saved=currentSnapshot(planId),patient=data.patient||{},rows=isReturn?data.e:data.plan;
    if(!Array.isArray(rows)||!rows.length)fail("exercise_count_invalid");
    var exercises=[];
    rows.forEach(function(row){
      var source=isReturn?{name:row&&row[0],sets:row&&row[1],side:row&&row[2],loadUnit:row&&row[3],metricUnit:row&&row[4]}:row;
      if(!source||!source.name)fail("exercise_name_required");
      var name=String(primaryNames&&primaryNames[source.name]||source.name),count=Number(source.sets)||3;
      if(!Number.isInteger(count)||count<1||count>8)fail("set_structure_invalid");
      var sides=source.side==="LR"?[0,1]:[null];
      sides.forEach(function(side){
        // Separate labelled sides preserve every return value in the existing
        // two-field Cockpit editor, without changing the patient wire format.
        var displayName=name+(side==null?"":side===0?" (links)":" (rechts)"),ref=api.registry.lookup(displayName)||api.registry.derive(displayName,source);
        var previous=saved&&saved.exercises.find(function(ex){return ex.id===ref.id;}),values;
        if(isReturn){
          var sets=row[5];if(!Array.isArray(sets)||sets.length!==count)fail("return_set_invalid");
          values=sets.map(function(set){if(side==null)return pair(set);if(!Array.isArray(set)||set.length!==4)fail("return_set_invalid");return pair(set.slice(side*2,side*2+2));});
        }else values=Array.from({length:count},function(){return [sideValue(source.startLoad,side||0),sideValue(source.startMetric,side||0)];});
        var exercise=Object.assign({},isReturn&&previous||{},source,{id:ref.id,name:displayName,sets:count,side:"BI",loadUnit:source.loadUnit||source.weightUnit||"kg",metricUnit:source.metricUnit||source.unit||"Wdh",previous:values,today:values.map(function(value){return value.slice();})});
        exercises.push(exercise);
      });
    });
    return {planId:planId,name:patient.name||saved&&saved.name||"Plan ohne Patientendaten",date:patient.date||saved&&saved.date||new Date().toISOString().slice(0,10),notes:typeof patient.notes==="string"?patient.notes:"",exercises:exercises};
  }
  function outputLink(link){
    var modal=document.getElementById("kggTherapyCockpitOutputModal");if(!modal)return;
    var anchor=document.getElementById("kggTherapyCockpitActivationLink");
    if(!anchor){anchor=document.createElement("a");anchor.id="kggTherapyCockpitActivationLink";anchor.className="kgg-tc-btn primary";anchor.textContent="Cockpit öffnen";var output=document.getElementById("kggTherapyCockpitOutput");output.before(anchor);anchor.addEventListener("click",function(event){event.preventDefault();try{var decoded=api.decode(anchor.href),entry=api.getState().slots.find(function(slot){return slot&&slot.planId===decoded.planId;}),index=entry?entry.slot:api.importCode(anchor.href).slot;modal.hidden=true;api.open();if(typeof api.selectSlot==="function")api.selectSlot(index);}catch(error){anchor.textContent="Cockpit konnte nicht geöffnet werden";}});}
    anchor.hidden=!link;if(link)anchor.href=link;else anchor.removeAttribute("href");
  }
  function showActivation(imported){
    var modal=document.getElementById("kggTherapyCockpitOutputModal"),output=document.getElementById("kggTherapyCockpitOutput");if(!modal||!output)return;
    var slot=api.getSlot(imported.slot);
    if(typeof api.selectSlot==="function")api.selectSlot(imported.slot);
    modal.querySelector("h2").textContent="Cockpit-Link bereit";
    modal.querySelector("p").textContent=imported.persisted?"Diesen Link in der Dokumentation speichern. Eigene Einträge haben bei weiteren Scans Vorrang.":"Diesen Link in der Dokumentation speichern. Der Browser konnte den Stand nicht dauerhaft speichern.";
    output.value=["KGG Therapie-Cockpit",slot.name,"Aktivierungslink:",imported.link].join("\n");
    outputLink(imported.link);modal.hidden=false;
  }
  window.KGGCockpitQrAccepted=function(result,primaryNames){var payload=scanPayload(result,primaryNames);if(!payload)return null;var imported=api.importPatientPlan(payload,{background:true});return imported;};
  window.KGGCockpitSetOutputLink=outputLink;
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,contract:"patient QR activation, durable notes and per-cell therapist priority"};
})();
</script>
<!-- KGG PATCH END kgg-v129-cockpit-qr-resume -->
