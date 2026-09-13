<!-- KGG PATCH START kgg-v093-cockpit-shared-editor -->
<!-- Therapie-Cockpit: vorhandenen Übungseditor und Progressionswechsel verbinden -->
<style id="kgg-v093-cockpit-shared-editor-style">
  .kgg-tce-stage-switcher{display:flex;align-items:center;gap:7px;margin:0 9px 7px;padding:6px 8px;border:1px solid #dbe7f3;border-radius:9px;background:#f8fbff;color:#475569;font-size:11px;font-weight:800;}
  .kgg-tce-stage-switcher label{white-space:nowrap;}
  .kgg-tce-stage-switcher select{min-width:0;flex:1;min-height:34px;padding:5px 7px;border:1px solid #bfd5ed;border-radius:7px;background:#fff;color:#1e3a5f;font:700 12px/1.2 system-ui,sans-serif;}
  .kgg-tce-stage-switcher small{color:#64748b;font-weight:700;}
  #editorModal .kgg-tce-cockpit-stages{margin:13px 0 0;padding:11px;border:1px solid #dbe3ee;border-radius:12px;background:#f8fafc;}
  #editorModal .kgg-tce-cockpit-stages>strong{display:block;margin-bottom:8px;color:#334155;}
  #editorModal .kgg-tce-cockpit-stage-list{display:grid;gap:8px;}
  #editorModal .kgg-tce-cockpit-stage-row{display:grid;grid-template-columns:30px minmax(0,1fr) auto;gap:6px;align-items:center;}
  #editorModal .kgg-tce-cockpit-stage-row .stageNo{display:grid;place-items:center;min-height:36px;border-radius:8px;background:#1e293b;color:#fff;font-weight:900;}
  #editorModal .kgg-tce-cockpit-stage-row .stageMain{display:grid;gap:5px;min-width:0;}
  #editorModal .kgg-tce-cockpit-stage-row input,#editorModal .kgg-tce-cockpit-stage-row select{width:100%;min-width:0;box-sizing:border-box;min-height:36px;padding:6px 7px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;color:#0f172a;font:700 12px/1.2 system-ui,sans-serif;}
  #editorModal .kgg-tce-cockpit-stage-row .stageActions{display:flex;gap:4px;}
  #editorModal .kgg-tce-cockpit-stage-row .stageActions button{min-width:32px;min-height:34px;padding:4px 6px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;color:#334155;font-weight:800;cursor:pointer;}
  #editorModal .kgg-tce-cockpit-stage-row .stageActions button:last-child{color:#b91c1c;background:#fff7f7;}
  body.kggTherapyCockpitOpen #editorModal.open{visibility:visible!important;pointer-events:auto!important;z-index:2147481900!important;}
  @media(max-width:600px){#editorModal .kgg-tce-cockpit-stage-row{grid-template-columns:27px minmax(0,1fr);}.kgg-tce-stage-switcher{margin-left:7px;margin-right:7px;}#editorModal .kgg-tce-cockpit-stage-row .stageActions{grid-column:2;}}
</style>
<script id="kgg-v093-cockpit-shared-editor-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v093-cockpit-shared-editor",api=null,root=null,board=null,editState=null,installed=false;
  function clone(value){try{return JSON.parse(JSON.stringify(value));}catch(e){return value;}}
  function esc(value){return String(value==null?"":value).replace(/[&<>"']/g,function(ch){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch];});}
  function slot(index){return api&&typeof api.getSlot==="function"?api.getSlot(index):null;}
  function card(index){return board&&board.querySelector('.kgg-tc-card[data-tc-card="'+index+'"]');}
  function showError(code){var toast=document.getElementById("kggTherapyCockpitToast");if(toast){toast.textContent="Cockpit-Änderung fehlgeschlagen ("+(code||"update_failed")+")";toast.classList.add("show");}}
  function safeUpdate(index,next,reason){try{api.updateSlot(index,next,reason);if(api.syncSlot)api.syncSlot(index);return true;}catch(errorValue){showError(errorValue&&errorValue.code||"update_failed");return false;}}
  function bankItems(){
    var list=[];try{var shared=window.KGGSharedBank&&window.KGGSharedBank.exportPayload?window.KGGSharedBank.exportPayload():null;list=shared&&Array.isArray(shared.exercises)?shared.exercises:[];}catch(e){}
    if(!list.length&&api&&api.registry&&api.registry.entries)list=api.registry.entries();
    var seen=Object.create(null);return list.filter(function(item){var id=String(item&&item.id||item&&item.cockpitId||item&&item.name||"");if(!id||seen[id])return false;seen[id]=true;return true;});
  }
  function sourceOptions(item){
    var selected=String(item.sourceId||item.bankId||""),items=bankItems(),html='<option value="">Keine Übungsbank-Zuordnung</option>';
    if(selected&&!items.some(function(candidate){return String(candidate.id||candidate.cockpitId||"")===selected}))html+='<option value="'+esc(selected)+'" selected>'+esc(item.sourceName||selected)+' (bestehend)</option>';
    return html+items.map(function(candidate){var id=String(candidate.id||candidate.cockpitId||""),name=String(candidate.name||id);return '<option value="'+esc(id)+'" '+(id===selected?'selected':'')+'>'+esc(name)+'</option>';}).join("");
  }
  function stageMarkup(ex){
    var variants=Array.isArray(ex&&ex.progressionVariants)?ex.progressionVariants:[];
    if(!variants.length)return '<div class="kgg-tce-empty-slot">Noch keine Progressionsstufen. Du kannst sie hier hinzufügen.</div>';
    return variants.map(function(item,index){return '<div class="kgg-tce-cockpit-stage-row" data-cockpit-stage="'+index+'"><span class="stageNo">'+(index+1)+'</span><div class="stageMain"><input data-cockpit-stage-name value="'+esc(item.name||"")+'" aria-label="Name der Progressionsstufe '+(index+1)+'"><select data-cockpit-stage-source aria-label="Übungsbank-Zuordnung der Progressionsstufe '+(index+1)+'">'+sourceOptions(item)+'</select></div><div class="stageActions"><button type="button" data-cockpit-stage-up="'+index+'" '+(index?'':'disabled')+'>↑</button><button type="button" data-cockpit-stage-down="'+index+'" '+(index===variants.length-1?'disabled':'')+'>↓</button><button type="button" data-cockpit-stage-remove="'+index+'">×</button></div></div>';}).join("");
  }
  function captureStages(){
    if(!editState||!editState.exercise)return;
    var box=document.getElementById("kggCockpitStageEditor"),names=box?Array.from(box.querySelectorAll("[data-cockpit-stage-name]")):[],sources=box?Array.from(box.querySelectorAll("[data-cockpit-stage-source]")):[],items=bankItems();
    (editState.exercise.progressionVariants||[]).forEach(function(item,index){
      if(names[index])item.name=String(names[index].value||item.name).trim().slice(0,80);
      var sourceId=sources[index]?String(sources[index].value||""):String(item.sourceId||"");
      if(sourceId){var linked=items.find(function(candidate){return String(candidate.id||candidate.cockpitId||"")===sourceId;});item.sourceId=sourceId;item.bankId=sourceId;item.sourceName=linked?String(linked.name||sourceId):String(item.sourceName||sourceId);if(linked&&Array.isArray(linked.media))item.media=clone(linked.media);}
      else{item.sourceId="";item.bankId="";item.sourceName="";}
      item.order=index;
    });
  }
  function renderStages(){var box=document.getElementById("kggCockpitStageList");if(box&&editState)box.innerHTML=stageMarkup(editState.exercise);}
  function installStageEditor(){
    var modal=document.getElementById("editorModal");if(!modal||document.getElementById("kggCockpitStageEditor"))return;
    var actions=modal.querySelector(".editorActions");if(!actions)return;
    var section=document.createElement("section");section.id="kggCockpitStageEditor";section.className="kgg-tce-cockpit-stages";section.hidden=true;section.innerHTML='<strong>Progressionsstufen im Cockpit</strong><div id="kggCockpitStageList" class="kgg-tce-cockpit-stage-list"></div><button type="button" class="mutedBtn" id="kggCockpitAddStage">+ Progressionsstufe hinzufügen</button>';
    actions.parentNode.insertBefore(section,actions);
    section.addEventListener("click",function(event){var target=event.target;if(!target)return;if(target.id==="kggCockpitAddStage"){captureStages();editState.exercise.progressionVariants=editState.exercise.progressionVariants||[];editState.exercise.progressionVariants.push({id:"pv_cockpit_"+Date.now()+"_"+editState.exercise.progressionVariants.length,groupId:editState.exercise.progressionGroupId||"",name:"Progressionsstufe "+(editState.exercise.progressionVariants.length+1),order:editState.exercise.progressionVariants.length,sourceId:"",sourceName:"",media:[]});renderStages();return;}var index;if(target.hasAttribute("data-cockpit-stage-up")){index=Number(target.getAttribute("data-cockpit-stage-up"));captureStages();var list=editState.exercise.progressionVariants,item=list.splice(index,1)[0];list.splice(index-1,0,item);renderStages();}else if(target.hasAttribute("data-cockpit-stage-down")){index=Number(target.getAttribute("data-cockpit-stage-down"));captureStages();var down=editState.exercise.progressionVariants,entry=down.splice(index,1)[0];down.splice(index+1,0,entry);renderStages();}else if(target.hasAttribute("data-cockpit-stage-remove")){index=Number(target.getAttribute("data-cockpit-stage-remove"));captureStages();var removed=editState.exercise.progressionVariants.splice(index,1)[0];if(removed&&editState.exercise.activeProgressionId===String(removed.id))editState.exercise.activeProgressionId=editState.exercise.progressionVariants[0]&&String(editState.exercise.progressionVariants[0].id)||"";renderStages();}});
  }
  function openSharedEditor(slotIndex,exerciseIndex){
    var current=slot(slotIndex),ex=current&&current.exercises&&current.exercises[exerciseIndex];if(!ex||!window.KGGSharedExerciseEditor||typeof window.KGGSharedExerciseEditor.open!=="function")return;
    editState={slotIndex:slotIndex,exerciseIndex:exerciseIndex,exercise:clone(ex)};installStageEditor();
    window.KGGSharedExerciseEditor.open(editState.exercise,{exercise:editState.exercise,onOpen:function(){var section=document.getElementById("kggCockpitStageEditor");if(section)section.hidden=false;renderStages();},onSave:function(saved){captureStages();var latest=slot(editState.slotIndex);if(!latest)return false;var next=clone(latest);next.exercises=next.exercises.map(function(item,index){return index===editState.exerciseIndex?clone(saved):item;});return safeUpdate(editState.slotIndex,next,"cockpit_shared_editor_save");},onDelete:function(){var latest=slot(editState.slotIndex);if(!latest||!latest.exercises[editState.exerciseIndex])return false;if(!window.confirm("Übung '"+latest.exercises[editState.exerciseIndex].name+"' aus diesem Cockpit-Slot löschen?"))return false;var article=card(editState.slotIndex)&&card(editState.slotIndex).querySelectorAll(".kgg-tc-exercise")[editState.exerciseIndex];if(article){article.classList.add("reorder-lifted");article.style.opacity="0";}var index=editState.exerciseIndex;setTimeout(function(){var now=slot(slotIndex);if(!now)return;var next=clone(now);next.exercises.splice(index,1);if(next.openExercise===index)next.openExercise=null;else if(Number.isInteger(next.openExercise)&&next.openExercise>index)next.openExercise-=1;safeUpdate(slotIndex,next,"cockpit_shared_editor_delete");},170);return true;},onClose:function(){var section=document.getElementById("kggCockpitStageEditor");if(section)section.hidden=true;editState=null;}});
  }
  function stageSwitchMarkup(ex,slotIndex,exerciseIndex){
    var variants=Array.isArray(ex&&ex.progressionVariants)?ex.progressionVariants:[];if(!variants.length)return null;
    var active=String(ex.activeProgressionId||variants[0].id||"");
    var wrap=document.createElement("div");wrap.className="kgg-tce-stage-switcher";wrap.setAttribute("data-tce-stage-switcher","1");
    var label=document.createElement("label");label.textContent="Stufe";var select=document.createElement("select");select.setAttribute("aria-label","Aktive Progressionsstufe");select.setAttribute("data-tce-stage-switch","1");
    variants.forEach(function(item){var option=document.createElement("option");option.value=String(item.id||"");option.textContent=String(item.name||"Progressionsstufe");option.selected=option.value===active;select.appendChild(option);});
    select.addEventListener("change",function(){var current=slot(slotIndex);if(!current||!current.exercises[exerciseIndex])return;var next=clone(current);next.exercises[exerciseIndex].activeProgressionId=select.value;if(!safeUpdate(slotIndex,next,"cockpit_progression_switch"))select.value=String(current.exercises[exerciseIndex].activeProgressionId||variants[0].id||"");});
    wrap.appendChild(label);wrap.appendChild(select);return wrap;
  }
  function enhanceStageSwitchers(){
    if(!board)return;Array.from(board.querySelectorAll(".kgg-tc-card[data-tc-card]")).forEach(function(article){var slotIndex=Number(article.getAttribute("data-tc-card")),current=slot(slotIndex);if(!current)return;Array.from(article.querySelectorAll(".kgg-tc-exercise")).forEach(function(exerciseArticle,index){var old=exerciseArticle.querySelector("[data-tce-stage-switcher]");if(old)old.remove();var next=stageSwitchMarkup(current.exercises[index],slotIndex,index),head=exerciseArticle.querySelector(".kgg-tce-exercise-head");if(next&&head)head.after(next);});});
  }
  function interceptEdit(event){
    var target=event.target&&event.target.closest?event.target.closest('[data-tce-action="edit"]'):null;if(!target||!root||!root.contains(target))return;event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();openSharedEditor(Number(target.getAttribute("data-tce-slot")),Number(target.getAttribute("data-tce-ex")));}
  function observe(){var boardObserver=new MutationObserver(function(){window.setTimeout(enhanceStageSwitchers,0);});boardObserver.observe(board,{childList:true,subtree:true});enhanceStageSwitchers();}
  function patch(){
    if(installed)return;api=window.KGGTherapyCockpit;if(!api||!root||!board||!window.KGGSharedExerciseEditor)return;installed=true;var old=document.getElementById("kggTceEditModal");if(old)old.remove();installStageEditor();document.addEventListener("click",interceptEdit,true);observe();window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v092-cockpit-live-edit",contract:"existing editor bridge, live progression selection and isolated slot edits"};
  }
  function init(){root=document.getElementById("kggTherapyCockpitRoot");board=document.getElementById("kggTherapyCockpitBoard");if(root&&board&&window.KGGTherapyCockpit&&window.KGGSharedExerciseEditor)patch();else window.setTimeout(init,50);}
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init,{once:true}):init();
})();
</script>
<!-- KGG PATCH END kgg-v093-cockpit-shared-editor -->
