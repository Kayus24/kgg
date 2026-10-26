      if(typeof shared.exportPayload==="function"){var exportBank=shared.exportPayload;shared.exportPayload=function(){var payload=exportBank.apply(this,arguments)||{};if(Array.isArray(payload.exercises))payload.exercises=payload.exercises.map(bankEntryWithCockpitId);return payload;};}
      if(typeof shared.merge==="function"){var mergeBank=shared.merge;shared.merge=function(raw){var value=raw;if(raw&&typeof raw==="object"&&Array.isArray(raw.exercises))value=Object.assign({},raw,{exercises:raw.exercises.map(bankEntryWithCockpitId)});return mergeBank.call(this,value);};}
      shared.__kggTherapyCockpitWrapped=true;
    }
    var nativeSync=window.KGGNativeExerciseSync;
    if(nativeSync&&!nativeSync.__kggTherapyCockpitWrapped){
      if(typeof nativeSync.build==="function"){var buildSync=nativeSync.build;nativeSync.build=function(){var doc=buildSync.apply(this,arguments)||{};if(Array.isArray(doc.exerciseBank))doc=Object.assign({},doc,{exerciseBank:doc.exerciseBank.map(bankEntryWithCockpitId)});return doc;};}
      if(typeof nativeSync.merge==="function"){var mergeSync=nativeSync.merge;nativeSync.merge=function(raw,options){var value=raw;if(raw&&typeof raw==="object"&&Array.isArray(raw.exerciseBank))value=Object.assign({},raw,{exerciseBank:raw.exerciseBank.map(bankEntryWithCockpitId)});return mergeSync.call(this,value,options);};}
      nativeSync.__kggTherapyCockpitWrapped=true;
    }
  }
  var slots=[null,null,null],activeInput=null,currentView="normal",root=null,board=null,notice="",toastTimer=null;
  function htmlEscape(value){return String(value==null?"":value).replace(/[&<>"']/g,function(ch){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch];});}
  function initials(name){return String(name||"?").trim().split(/\s+/).slice(0,2).map(function(x){return x.charAt(0);}).join("").toUpperCase()||"?";}
  function slotCount(){return slots.reduce(function(total,slot){return total+(slot?1:0);},0);}
  function firstFreeSlot(){for(var i=0;i<MAX_SLOTS;i++)if(!slots[i])return i;return -1;}
  function slotProgress(slot){var total=0,done=0;(slot&&slot.exercises||[]).forEach(function(ex){(ex.today||[]).forEach(function(pair){total+=2;if(pair[0])done++;if(pair[1])done++;});});return total?Math.round(done/total*100):0;}
  function normalizeSlot(decoded){var key=contentKey(decoded);return {planId:decoded.planId,name:decoded.name,date:decoded.date,notes:cleanNotes(decoded.notes),notesManual:!!decoded.notesManual,editedAt:Number(decoded.editedAt)||0,removedIds:Array.isArray(decoded.removedIds)?decoded.removedIds.slice():[],exercises:(decoded.exercises||[]).map(exerciseInput),contentKey:key,sourceContentKey:key,openExercise:null,lastCompletion:null};}
  function payloadFromSlot(slot,useTodayAsPrevious){return {planId:slot.planId,name:slot.name,date:new Date().toISOString().slice(0,10),notes:slot.notes,notesManual:slot.notesManual,editedAt:slot.editedAt,removedIds:slot.removedIds,exercises:slot.exercises.map(function(ex){var next=exerciseInput(ex);next.previous=(useTodayAsPrevious?ex.today:ex.previous).map(function(p){return p.slice();});next.today=ex.today.map(function(p){return p.slice();});return next;})};}
  function cloneJson(value){try{return JSON.parse(JSON.stringify(value));}catch(e){return value;}}
  function slotSnapshot(slot){if(!slot)return null;return {planId:slot.planId,name:slot.name,date:slot.date,notes:slot.notes,notesManual:slot.notesManual,editedAt:slot.editedAt,removedIds:cloneJson(slot.removedIds||[]),exercises:cloneJson(slot.exercises||[]),openExercise:Number.isInteger(slot.openExercise)?slot.openExercise:null};}
  function resumeStorageKey(planId){return "kgg_cockpit_resume_v1:"+encodeURIComponent(planId);}
  function readRemembered(planId){
    if(!planId)return null;
    try{var text=window.localStorage&&window.localStorage.getItem(resumeStorageKey(planId));if(!text)return null;var decoded=decodeCode(text);return decoded.planId===planId?normalizeSlot(decoded):null;}catch(e){return null;}
  }
  var resumeSaveFailed=false;
  function resumeStatus(){var status=document.getElementById("kggTherapyCockpitStatus");if(status){status.setAttribute("role","status");status.textContent=resumeSaveFailed?'Nicht lokal gespeichert. Vor dem Schließen „Plan fertig“ wählen und den neuen Link speichern.':"Wiederaufnahme per Link · maximal 3 Slots";}}
  function rememberSlot(slot){
    if(!slot||!slot.planId||!slot.exercises.length)return false;
    try{var code=encodePayload(payloadFromSlot(slot,false));if(!window.localStorage)throw error("storage_unavailable");window.localStorage.setItem(resumeStorageKey(slot.planId),code);resumeSaveFailed=false;resumeStatus();return true;}catch(e){resumeSaveFailed=true;resumeStatus();return false;}
  }
  function markEdited(slot){slot.editedAt=Math.max(Date.now(),Number(slot.editedAt||0)+1);return rememberSlot(slot);}
  function markCell(slot,ex,set,field){ex.manual=manualCells(ex.manual,ex.sets);ex.manual[set][field]=true;markEdited(slot);}
  function matchingSlot(planId){if(!planId)return -1;for(var i=0;i<MAX_SLOTS;i++)if(slots[i]&&slots[i].planId===planId)return i;return -1;}
  function mergePatientSlot(incoming,saved,keepIncomingManual){
    if(!saved||saved.planId!==incoming.planId)return incoming;
    var previous=Object.create(null);saved.exercises.forEach(function(ex){previous[ex.id]=ex;});
    var removed=(keepIncomingManual?incoming.removedIds:saved.removedIds)||[],items=incoming.exercises.filter(function(ex){return removed.indexOf(ex.id)<0;}).map(function(ex){
      var old=previous[ex.id];if(!old)return ex;
      var incomingFields=keepIncomingManual?(ex.manualFields||[]).slice():[];
      (old.manualFields||[]).forEach(function(field){if(incomingFields.indexOf(field)<0)ex[field]=cloneJson(old[field]);});
      ex.manualFields=Array.from(new Set(incomingFields.concat(old.manualFields||[])));
      var incomingCells=manualCells(keepIncomingManual&&ex.manual,ex.sets),oldCells=manualCells(old.manual,ex.sets);ex.manual=manualCells(null,ex.sets);
      ex.previous=valueArray(ex.previous,ex.sets);ex.today=valueArray(ex.today,ex.sets);
      ex.manual.forEach(function(pair,set){pair.forEach(function(_,field){
        if(incomingCells[set][field]){pair[field]=true;return;}
        if(oldCells[set][field]){var value=old.today[set]&&old.today[set][field]||"";ex.previous[set][field]=value;ex.today[set][field]=value;pair[field]=true;}
        else{var previousValue=old.today[set]&&old.today[set][field]||"";if(ex.previous[set][field]==="")ex.previous[set][field]=previousValue;if(ex.today[set][field]==="")ex.today[set][field]=previousValue;}
      });});
      if(oldCells.some(function(pair){return pair[0];})&&!incomingCells.some(function(pair){return pair[0];})){ex.loadUnit=old.loadUnit;ex.weightUnit=old.weightUnit;}
      if(oldCells.some(function(pair){return pair[1];})&&!incomingCells.some(function(pair){return pair[1];})){ex.metricUnit=old.metricUnit;ex.unit=old.unit;ex.measure=old.measure;}
      return exerciseInput(ex);
    });
    saved.exercises.forEach(function(ex){if(!items.some(function(item){return item.id===ex.id;})&&removed.indexOf(ex.id)<0)items.push(exerciseInput(ex));});
    incoming.exercises=items;incoming.removedIds=removed.slice();incoming.editedAt=Math.max(incoming.editedAt,saved.editedAt);
    if(!(keepIncomingManual&&incoming.notesManual)){incoming.notes=saved.notesManual?saved.notes:(incoming.notes||saved.notes);incoming.notesManual=saved.notesManual;}
    // Names remain therapist-side display data; they are never the matching key.
    if(!keepIncomingManual&&saved.name&&saved.name!=="Plan ohne Patientendaten")incoming.name=saved.name;
    incoming.contentKey=contentKey(incoming);return incoming;
  }
  function importPatientPlan(payload){
    if(!payload||!String(payload.planId||"").trim())throw error("plan_id_required");
    // Validate every field before touching a loaded slot or a saved snapshot.
    var incoming=normalizeSlot(decodeCode(encodePayload(payload))),index=matchingSlot(incoming.planId),saved=index>=0?slots[index]:readRemembered(incoming.planId);
    var merged=mergePatientSlot(incoming,saved);encodePayload(payloadFromSlot(merged,false));
    if(index<0)index=firstFreeSlot();if(index<0)throw error("slots_full");
    slots[index]=merged;notice="";var persisted=rememberSlot(merged);currentView="cockpit";setCockpitOpen(true);render();
    return {slot:index,link:makeLink(payloadFromSlot(merged,false)),persisted:persisted,state:getState()};
  }
  function valuesLabel(pair,ex){var load=pair&&pair[0]||"–",metric=pair&&pair[1]||"–";return load+" "+(ex.loadUnit||"")+" / "+metric+" "+(ex.metricUnit||"");}
  function mediaMarkup(ex){var current=ex&&ex.media&&Array.isArray(ex.media)?ex.media[0]:null;if(current&&current.downloadUrl&&/^data:image\//i.test(current.downloadUrl))return '<img alt="" src="'+htmlEscape(current.downloadUrl)+'">';return htmlEscape(initials(ex&&ex.name));}
  function renderPad(slotIndex,exerciseIndex,setIndex,field,ex){
    var fieldName=field==="load"?(ex.loadUnit||"kg"):(ex.metricUnit||"Wdh"),html='<div class="kgg-tc-pad" data-tc-pad="1"><div class="kgg-tc-pad-head"><span>Wert eingeben · '+htmlEscape(fieldName)+'</span><span class="kgg-tc-pad-modes">';
    html+='<button type="button" class="kgg-tc-pad-mode '+(field==="load"?"active":"")+'" data-tc-action="mode" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="load">'+htmlEscape(ex.loadUnit||"kg")+'</button>';
    html+='<button type="button" class="kgg-tc-pad-mode '+(field==="metric"?"active":"")+'" data-tc-action="mode" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="metric">'+htmlEscape(ex.metricUnit||"Wdh")+'</button></span></div><div class="kgg-tc-pad-keys">';
    ["1","2","3","4","5","6","7","8","9","0",",","⌫","C","–","OK"].forEach(function(keyValue){var cls=(keyValue===","||keyValue==="⌫"||keyValue==="C"||keyValue==="–"||keyValue==="OK")?" action":"";html+='<button type="button" class="kgg-tc-key'+cls+'" data-tc-action="key" data-tc-key="'+htmlEscape(keyValue)+'" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="'+field+'">'+htmlEscape(keyValue)+'</button>';});
    return html+'</div></div>';
  }
  function renderExercise(slot,slotIndex,ex,exerciseIndex){
    var open=slot.openExercise===exerciseIndex,summary=(ex.today||[]).map(function(pair){return valuesLabel(pair,ex);}).join(" · ");
    var sideMatch=String(ex.name).match(/^(.*) \((links|rechts)\)$/i),displayName=sideMatch?sideMatch[2]+" · "+sideMatch[1]:ex.name,sideLabel=sideMatch?sideMatch[2]:ex.side==="LR"?"links/rechts":"beidseitig";
    var html='<article class="kgg-tc-exercise '+(open?"open":"")+'"><button type="button" class="kgg-tc-card-toggle" data-tc-action="toggle" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'"><span class="kgg-tc-thumb" aria-hidden="true">'+mediaMarkup(ex)+'</span><span class="kgg-tc-exercise-summary"><strong>'+htmlEscape(displayName)+'</strong><small>'+ex.sets+' Sätze · '+htmlEscape(sideLabel)+(summary?" · "+htmlEscape(summary):"")+'</small></span><span class="kgg-tc-chevron" aria-hidden="true">'+(open?"⌃":"⌄")+'</span></button>';
    if(open){
      html+='<div class="kgg-tc-exercise-detail"><div class="kgg-tc-values-head"><span>Satz</span><span>Vorwert</span><span>Heute</span></div>';
      for(var setIndex=0;setIndex<ex.sets;setIndex++){
        var prev=ex.previous[setIndex]||["",""];var today=ex.today[setIndex]||["",""];html+='<div class="kgg-tc-set-row"><span class="kgg-tc-set-no">S'+(setIndex+1)+'</span><button type="button" class="kgg-tc-prev" data-tc-action="use-previous" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" aria-label="Vorwerte für Satz '+(setIndex+1)+' übernehmen" '+(!prev[0]&&!prev[1]?'disabled':'')+'>'+htmlEscape(valuesLabel(prev,ex))+'</button>';
        ["load","metric"].forEach(function(field){var val=field==="load"?today[0]:today[1],active=activeInput&&activeInput.slot===slotIndex&&activeInput.exercise===exerciseIndex&&activeInput.set===setIndex&&activeInput.field===field;html+='<button type="button" class="kgg-tc-field '+(active?"active ":"")+(val?"":"empty")+'" data-tc-action="input" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="'+field+'" aria-label="Heute '+htmlEscape(field==="load"?(ex.loadUnit||"kg"):(ex.metricUnit||"Wdh"))+'">'+htmlEscape(val||"—")+'</button>';if(active)html+=renderPad(slotIndex,exerciseIndex,setIndex,field,ex);});
        html+='</div>';
      }
      html+='</div>';
    }
    return html+'</article>';
  }
  function renderCard(slot,slotIndex){
    var progress=slotProgress(slot),color=COLORS[slotIndex%COLORS.length],html='<article class="kgg-tc-card" style="--tc-color:'+color+'" data-tc-card="'+slotIndex+'"><div class="kgg-tc-card-head"><span class="kgg-tc-avatar" aria-hidden="true">'+htmlEscape(initials(slot.name))+'</span><span class="kgg-tc-card-title"><strong>'+htmlEscape(slot.name)+'</strong><small>'+slot.exercises.length+' Übungen · '+progress+' % erledigt</small></span><span class="kgg-tc-card-tools"><button type="button" class="kgg-tc-icon-btn" data-tc-action="remove" data-tc-slot="'+slotIndex+'" aria-label="Patient entfernen">×</button></span></div><div class="kgg-tc-progress" aria-label="Fortschritt '+progress+' Prozent"><span style="width:'+progress+'%"></span></div><div class="kgg-tc-card-body"><div class="kgg-tc-scroll">';
    html+=slot.exercises.map(function(ex,index){return renderExercise(slot,slotIndex,ex,index);}).join("");
    html+='<label class="kgg-tc-notes-label">Therapienotizen<textarea class="kgg-tc-input" data-tc-notes="'+slotIndex+'" maxlength="2000" rows="2" placeholder="Eigene Notizen zu diesem Plan">'+htmlEscape(slot.notes)+'</textarea></label>';
    return html+'</div></div><div class="kgg-tc-card-foot"><button type="button" class="kgg-tc-btn primary" data-tc-action="finish" data-tc-slot="'+slotIndex+'">Plan fertig</button></div></article>';
  }
  function render(){
    resumeStatus();
    var scrollPositions={};if(board)board.querySelectorAll('.kgg-tc-card[data-tc-card]').forEach(function(card){var scroller=card.querySelector('.kgg-tc-scroll');if(scroller)scrollPositions[card.dataset.tcCard]=scroller.scrollTop;});
    var count=slotCount(),button=document.getElementById("kggTherapyCockpitButton");
    if(button)button.textContent=count?"Cockpit "+count+"/3":"Cockpit";
    if(typeof window.KGGTherapyCockpitEntryVisibilitySync==="function")window.KGGTherapyCockpitEntryVisibilitySync();
    if(!board)return;
    var content="";
    if(notice)content+='<div class="kgg-tc-notice" role="status">'+htmlEscape(notice)+'</div>';
    if(!count){content+='<div class="kgg-tc-empty"><div class="kgg-tc-empty-box"><strong>Noch kein Cockpit-Link geladen</strong><span>Bis zu drei begleitete Trainingspläne können unabhängig nebeneinander geöffnet werden.</span><div style="margin-top:14px"><button type="button" class="kgg-tc-btn primary" data-tc-action="import-open">Cockpit-Link laden</button></div></div></div>';board.innerHTML=content;return;}
    var gridClass=count===1?"one":count===2?"two":"";content+='<div class="kgg-tc-grid '+gridClass+'">';for(var i=0;i<MAX_SLOTS;i++)if(slots[i])content+=renderCard(slots[i],i);content+='</div>';board.innerHTML=content;
    board.querySelectorAll('.kgg-tc-card[data-tc-card]').forEach(function(card){var scroller=card.querySelector('.kgg-tc-scroll');if(scroller&&scrollPositions[card.dataset.tcCard]!=null)scroller.scrollTop=scrollPositions[card.dataset.tcCard];});
    setTimeout(function(){if(!activeInput)return;var active=board.querySelector('.kgg-tc-field.active');if(active&&active.scrollIntoView)active.scrollIntoView({block:"nearest",inline:"nearest"});},0);
  }
  function closePad(){if(activeInput){activeInput=null;render();}}
  function setActiveInput(slot,exercise,set,field){if(!slots[slot])return;slots[slot].openExercise=exercise;activeInput={slot:slot,exercise:exercise,set:set,field:field};render();}
  function applyKey(slot,exercise,set,field,keyValue){
    var target=slots[slot],ex=target&&target.exercises[exercise];if(!ex)return;var pair=ex.today[set]||(ex.today[set]=["",""]),index=field==="load"?0:1,current=String(pair[index]||"");
    if(keyValue==="OK"){activeInput=null;render();return;}
    if(keyValue==="⌫")current=current.slice(0,-1);else if(keyValue==="C")current="";else if(keyValue==="–")current="0";else if(keyValue===","){if(!current.includes("."))current=current?current+".":"0.";}else if(/^\d$/.test(keyValue)){if(current.length<8)current+=keyValue;}
    pair[index]=current;markCell(target,ex,set,index);render();
  }
  function dispatchPlanHook(slot){
    var store=window["KGGDataStore"];if(!store||typeof store.getCurrentPlan!=="function"||typeof store.setCurrentPlan!=="function")return "hook_unavailable";
    var current;try{current=store.getCurrentPlan()||{};}catch(e){return "hook_unavailable";}
    if(!slot.planId||!current.id||String(slot.planId)!==String(current.id))return "plan_mismatch";
    var currentKey;try{currentKey=contentKey(buildFromPlan(current));}catch(e){return "plan_mismatch";}
    if(slot.sourceContentKey&&slot.sourceContentKey!==currentKey)return "plan_mismatch";
    var originals=Array.isArray(current.exercises)?current.exercises:[],used=Object.create(null),changed=0;
    var exercises=slot.exercises.map(function(hit){
      var ref=registryLookup(hit&& (hit.id||hit.sourceId||hit.bankId||hit.name)),originalIndex=-1;
      if(ref)originalIndex=originals.findIndex(function(original){var originalRef=registryLookup(original&& (original.sourceId||original.bankId||original.id||original.name));return originalRef&&originalRef.id===ref.id&&!used[originalRef.id];});
      var original=originalIndex>=0?originals[originalIndex]:null;
      if(original){var originalRef=registryLookup(original.sourceId||original.bankId||original.id||original.name);used[originalRef.id]=true;changed++;return Object.assign({},original,{name:hit.name,...germanNameField(hit.nameDe),...(typeof hit.nameEn==="string"?{nameEn:hit.nameEn}:{}),sets:hit.sets,side:hit.side,loadUnit:hit.loadUnit,weightUnit:hit.weightUnit||hit.loadUnit,metricUnit:hit.metricUnit,unit:hit.unit||hit.metricUnit,measure:hit.measure,startLoad:hit.startLoad,startMetric:hit.startMetric,videoUrl:hit.videoUrl,videoLabel:hit.videoLabel,media:cloneJson(hit.media||original.media||[]),progressionGroupId:hit.progressionGroupId,progressionVariants:(hit.progressionVariants||[]).map(function(stage){var old=(original&&original.progressionVariants||[]).find(function(item){return item.id===stage.id;});return Object.assign({},old||{},stage);}),activeProgressionId:hit.activeProgressionId,previous:cloneJson(hit.previous||[]),today:cloneJson(hit.today||[]),lastTraining:hit.today.map(function(pair){return {load:pair[0],metric:pair[1]};}),cockpitPrevious:hit.today.map(function(pair){return pair.slice();}),lastTrainingDate:new Date().toISOString().slice(0,10)});}
      if(ref){changed++;return {id:ref.id,name:hit.name,...germanNameField(hit.nameDe),...(typeof hit.nameEn==="string"?{nameEn:hit.nameEn}:{}),sourceId:ref.id,bankId:ref.id,sets:hit.sets,side:hit.side,loadUnit:hit.loadUnit,weightUnit:hit.weightUnit||hit.loadUnit,metricUnit:hit.metricUnit,unit:hit.unit||hit.metricUnit,measure:hit.measure,startLoad:hit.startLoad,startMetric:hit.startMetric,videoUrl:hit.videoUrl,videoLabel:hit.videoLabel,media:cloneJson(hit.media||[]),progressionGroupId:hit.progressionGroupId,progressionVariants:cloneJson(hit.progressionVariants||[]),activeProgressionId:hit.activeProgressionId,previous:cloneJson(hit.previous||[]),today:cloneJson(hit.today||[]),lastTraining:hit.today.map(function(pair){return {load:pair[0],metric:pair[1]};}),cockpitPrevious:hit.today.map(function(pair){return pair.slice();}),lastTrainingDate:new Date().toISOString().slice(0,10)};}
      return null;
    }).filter(Boolean);
    if(!changed)return "exercise_mismatch";
    try{var updatedPlan=Object.assign({},current,{exercises:exercises});store.setCurrentPlan(updatedPlan,"therapy_cockpit_edit");slot.sourceContentKey=contentKey(buildFromPlan(updatedPlan));if(typeof CustomEvent!=="undefined")window.dispatchEvent(new CustomEvent("kgg:therapy-cockpit-finished",{detail:{planId:slot.planId,exerciseCount:changed}}));return "updated";}catch(e){return "hook_failed";}
  }
  function documentationFor(slot,link){
    var lines=["KGG Therapie-Cockpit · "+new Date().toLocaleDateString("de-DE"),"Patient: "+slot.name,"Plan fertig · heutige Werte"];slot.exercises.forEach(function(ex){lines.push("",ex.name);ex.today.forEach(function(pair,index){lines.push("S"+(index+1)+": "+valuesLabel(pair,ex));});});if(slot.notes)lines.push("","Therapienotizen:",slot.notes);lines.push("","Neuer Cockpit-Link:",link);return lines.join("\n");
  }
  function showOutput(results){
    var modal=document.getElementById("kggTherapyCockpitOutputModal"),output=document.getElementById("kggTherapyCockpitOutput");if(!modal||!output)return;if(!slotCount())setCockpitOpen(true);var allUpdated=results.length>0&&results.every(function(result){return result.hook==="updated";}),title=modal.querySelector("h2"),hint=modal.querySelector("p");if(title)title.textContent=allUpdated?"Dokumentation bereit":"Dokumentationstext bereit";if(hint)hint.textContent=allUpdated?"Die verknüpften Planquellen wurden mit der vorhandenen Aktion aktualisiert.":"Link und Text sind bereit. Mindestens eine Planquelle wurde nicht übernommen; bitte den Status im Text prüfen.";var labels={updated:"Planquelle aktualisiert",plan_mismatch:"Planquelle nicht übernommen: Plan stimmt nicht überein",exercise_mismatch:"Planquelle nicht übernommen: keine Übung zugeordnet",hook_unavailable:"Planquelle nicht übernommen: Aktualisierung nicht verfügbar",hook_failed:"Planquelle nicht übernommen: Aktualisierung fehlgeschlagen","nicht übernommen":"Planquelle nicht übernommen"};output.value=results.map(function(result){return result.text+"\n\n"+(labels[result.hook]||"Planquelle nicht übernommen");}).join("\n\n--------------------\n\n");modal.hidden=false;if(typeof window.KGGCockpitSetOutputLink==="function")window.KGGCockpitSetOutputLink(results.length===1?results[0].link:"");
  }
  function finishSlot(index,skipRender){
    var slot=slots[index];if(!slot)return null;var link,hook="nicht übernommen";try{link=makeLink(payloadFromSlot(slot,true));hook=dispatchPlanHook(slot);}catch(e){notice="Abschluss fehlgeschlagen ("+(e.code||"invalid_payload")+").";if(!skipRender)render();return null;}
    var result={slot:index,link:link,text:documentationFor(slot,link),hook:hook};rememberSlot(normalizeSlot(payloadFromSlot(slot,true)));slot.lastCompletion=result;slots[index]=null;if(activeInput&&activeInput.slot===index)activeInput=null;if(!slotCount()){currentView="normal";setCockpitOpen(false);}if(!skipRender)render();return result;
  }
  function setCockpitOpen(open){if(document.body&&document.body.classList)document.body.classList.toggle("kggTherapyCockpitOpen",!!open);}
  function finishAll(){var results=[];for(var i=0;i<MAX_SLOTS;i++){var result=finishSlot(i,true);if(result)results.push(result);}currentView="normal";setCockpitOpen(false);render();if(results.length)showOutput(results);}
  function removeSlot(index){if(index<0||index>=MAX_SLOTS||!slots[index])return;slots[index]=null;if(activeInput&&activeInput.slot===index)activeInput=null;notice="";if(!slotCount()){currentView="normal";setCockpitOpen(false);}render();}
  function updateSlot(index,next,reason){
    if(index<0||index>=MAX_SLOTS||!slots[index])throw error("slot_not_found");
    var current=slots[index],source=next||{},name=String(source.name==null?current.name:source.name).trim()||"Plan ohne Patientendaten",exercises=Array.isArray(source.exercises)?source.exercises.map(exerciseInput):[];
    if(exercises.length>MAX_EXERCISES)throw error("exercise_count_invalid");
    var candidate={planId:source.planId==null?current.planId:cleanPlanId(source.planId),name:name,date:cleanDate(source.date==null?current.date:source.date),notes:source.notes==null?current.notes:cleanNotes(source.notes),notesManual:current.notesManual||source.notes!=null&&cleanNotes(source.notes)!==current.notes,editedAt:Math.max(Date.now(),Number(current.editedAt||0)+1),removedIds:(current.removedIds||[]).slice(),exercises:exercises};
    if(candidate.planId!==current.planId)throw error("plan_id_mismatch");
    current.exercises.forEach(function(old){if(!exercises.some(function(ex){return ex.id===old.id;})&&candidate.removedIds.indexOf(old.id)<0)candidate.removedIds.push(old.id);});
    exercises.forEach(function(ex){
      candidate.removedIds=candidate.removedIds.filter(function(id){return id!==ex.id;});
      var old=current.exercises.find(function(item){return item.id===ex.id;}),cells=manualCells(old&&old.manual,ex.sets),fields=(old&&old.manualFields||[]).slice();
      ex.today.forEach(function(pair,set){pair.forEach(function(value,field){if(!old||value!==(old.today[set]&&old.today[set][field]||""))cells[set][field]=true;});});
      MANUAL_FIELDS.forEach(function(field){if((!old||JSON.stringify(ex[field])!==JSON.stringify(old[field]))&&fields.indexOf(field)<0)fields.push(field);});
      ex.manual=cells;ex.manualFields=fields;
    });
    if(exercises.length)encodePayload(candidate);
    var normalized=normalizeSlot(candidate);normalized.sourceContentKey=current.sourceContentKey||current.contentKey;normalized.openExercise=Number.isInteger(source.openExercise)&&source.openExercise>=0&&source.openExercise<exercises.length?source.openExercise:null;normalized.contentKey=contentKey(candidate);slots[index]=normalized;rememberSlot(normalized);notice="";render();return slotSnapshot(normalized);
  }
  function syncSlotToPlan(index){if(index<0||index>=MAX_SLOTS||!slots[index])return "slot_not_found";return dispatchPlanHook(slots[index]);}
  function importCode(value){
    var code=extractCode(value)||String(value||"").trim(),decoded=decodeCode(code),index=matchingSlot(decoded.planId),incoming=normalizeSlot(decoded),saved=index>=0?slots[index]:readRemembered(decoded.planId);
    if(saved){var newer=saved.editedAt>=incoming.editedAt?saved:incoming,older=newer===saved?incoming:saved;incoming=mergePatientSlot(normalizeSlot(payloadFromSlot(newer,false)),older,true);}
    if(incoming.exercises.length)encodePayload(payloadFromSlot(incoming,false));
    if(index<0)index=firstFreeSlot();if(index<0)throw error("slots_full");slots[index]=incoming;rememberSlot(incoming);notice="";currentView="cockpit";setCockpitOpen(true);render();return {slot:index,state:getState()};
  }
  function openView(){currentView="cockpit";setCockpitOpen(true);render();}
  function closeView(){currentView="normal";activeInput=null;setCockpitOpen(false);render();}
  function clearIncomingParam(){try{var url=new URL(window.location.href),changed=false;["cockpit","kggtc"].forEach(function(name){if(url.searchParams.has(name)){url.searchParams.delete(name);changed=true;}});if(changed&&window.history&&history.replaceState)history.replaceState({},document.title,url.pathname+(url.search?url.search:"")+url.hash);}catch(e){}}
  function notify(message){var toast=document.getElementById("kggTherapyCockpitToast");if(!toast)return;toast.textContent=message;toast.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(function(){toast.classList.remove("show");},3200);}
  function installDom(){
    if(!document.body)return;
    if(!document.getElementById("kggTherapyCockpitButton")){
      var base=document.getElementById("baseToggle"),button=document.createElement(base?"span":"button");if(!base)button.type="button";button.id="kggTherapyCockpitButton";button.className="kgg-tc-entry";button.textContent="Cockpit";button.setAttribute("aria-label","Therapie-Cockpit öffnen");if(base){button.setAttribute("role","button");button.setAttribute("tabindex","0");base.appendChild(button);}else{var scanHub=document.getElementById("scanHub"),topbar=document.querySelector(".topbar"),vision=document.getElementById("visionBtn");if(scanHub)scanHub.appendChild(button);else if(topbar)topbar.insertBefore(button,vision||null);}
    }
    if(!document.getElementById("kggTherapyCockpitRoot")){
      var container=document.createElement("div");container.id="kggTherapyCockpitRoot";container.innerHTML='<div class="kgg-tc-shell"><header class="kgg-tc-header"><div class="kgg-tc-title"><strong>Therapie-Cockpit</strong><small>begleitete Trainingspläne</small></div><div class="kgg-tc-actions"><button type="button" class="kgg-tc-btn" data-tc-action="normal">Therapeuten-App</button><button type="button" class="kgg-tc-btn primary" data-tc-action="import-open">+ Cockpit-Link</button></div></header><main class="kgg-tc-board" id="kggTherapyCockpitBoard"></main><footer class="kgg-tc-footer"><small id="kggTherapyCockpitStatus">RAM-Sitzung · maximal 3 Slots</small><button type="button" class="kgg-tc-btn primary" data-tc-action="finish-all">Alle Pläne speichern</button></footer></div><div class="kgg-tc-modal" id="kggTherapyCockpitImportModal" hidden><div class="kgg-tc-sheet" role="dialog" aria-modal="true" aria-labelledby="kggTherapyCockpitImportTitle"><h2 id="kggTherapyCockpitImportTitle">Cockpit-Link laden</h2><p>Den vollständigen Link aus dem offiziellen Dokumentationsprogramm einfügen.</p><textarea class="kgg-tc-input" id="kggTherapyCockpitImportInput" spellcheck="false" autocomplete="off"></textarea><div class="kgg-tc-modal-actions"><button type="button" class="kgg-tc-btn" data-tc-action="import-cancel">Abbrechen</button><button type="button" class="kgg-tc-btn primary" data-tc-action="import-submit">Slot laden</button></div></div></div><div class="kgg-tc-modal" id="kggTherapyCockpitOutputModal" hidden><div class="kgg-tc-sheet" role="dialog" aria-modal="true" aria-labelledby="kggTherapyCockpitOutputTitle"><h2 id="kggTherapyCockpitOutputTitle">Dokumentation bereit</h2><p>Link und Text können jetzt in die Dokumentation kopiert werden.</p><textarea class="kgg-tc-output" id="kggTherapyCockpitOutput" readonly></textarea><div class="kgg-tc-modal-actions"><button type="button" class="kgg-tc-btn" data-tc-action="output-close">Schließen</button><button type="button" class="kgg-tc-btn primary" data-tc-action="output-copy">Text kopieren</button></div></div></div>';
      document.body.appendChild(container);
    }
    if(!document.getElementById("kggTherapyCockpitToast")){var toast=document.createElement("div");toast.id="kggTherapyCockpitToast";toast.className="kgg-tc-toast";toast.setAttribute("role","status");document.body.appendChild(toast);}
    root=document.getElementById("kggTherapyCockpitRoot");board=document.getElementById("kggTherapyCockpitBoard");
    var rootButton=document.getElementById("kggTherapyCockpitButton");if(rootButton){var directPlanClick=function(event){var handler=window.KGGTherapyCockpitDirectPlanClick;return typeof handler==="function"&&handler(event)===true;};rootButton.addEventListener("click",function(event){event.stopPropagation();if(directPlanClick(event))return;openView();});rootButton.addEventListener("keydown",function(event){if(event.key==="Enter"||event.key===" "){event.preventDefault();event.stopPropagation();if(directPlanClick(event))return;openView();}});}
    root.addEventListener("click",handleClick);
    root.addEventListener("input",function(event){var input=event.target;if(!input||!input.hasAttribute("data-tc-notes"))return;var slot=slots[Number(input.getAttribute("data-tc-notes"))];if(slot){slot.notes=cleanNotes(input.value);slot.notesManual=true;markEdited(slot);}});
    document.addEventListener("pointerdown",handleOutsidePointer,true);
    render();
    var incoming=extractCode(window.location.href);if(incoming){try{importCode(incoming);clearIncomingParam();}catch(e){notice="Cockpit-Link nicht geladen ("+(e.code||"invalid_format")+").";render();notify("Cockpit-Link konnte nicht geladen werden.");}}
  }
  function handleOutsidePointer(event){
    if(!activeInput||!document.body.classList.contains("kggTherapyCockpitOpen"))return;
    var target=event.target;if(target&&target.closest&& (target.closest("[data-tc-pad]")||target.closest('[data-tc-action="input"]')))return;
    activeInput=null;render();
    if(target&&root&&root.contains(target)){event.stopPropagation();event.preventDefault();}
  }
  function numberAttribute(target,name){var value=Number(target&&target.getAttribute(name));return Number.isInteger(value)?value:-1;}
  function handleClick(event){
