<!-- KGG PATCH START kgg-v085-ticket-015-progressions -->
<!-- Progressionsvarianten -->
<script id="kgg-v085-ticket-015-progressions">
(function(){
  'use strict';
  const VERSION='ticket-015-progressions-v1';
  const $=id=>document.getElementById(id);
  const esc=value=>String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clone=value=>{try{return JSON.parse(JSON.stringify(value));}catch(err){return value;}};
  const idPart=value=>String(value||'').replace(/[^A-Za-z0-9_-]+/g,'_').slice(0,80)||'exercise';
  const mediaOf=ex=>{try{return typeof ensureExerciseMediaList==='function'?clone(ensureExerciseMediaList(ex)):clone(Array.isArray(ex&&ex.media)?ex.media:[]);}catch(err){return [];}};
  function groupId(ex){return String(ex&&ex.progressionGroupId||'pg_'+idPart(ex&&((ex.localId||ex.id)||'exercise')));}
  function variantId(group,index,value){return String(value&&value.id||('pv_'+idPart(group)+'_'+index));}
  function normalizeVariant(value,index,group,base){
    const source=value&&typeof value==='object'?value:{};
    const linked=source.sourceId||source.bankId||'';
    return {
      id:variantId(group,index,source),
      groupId:String(source.groupId||group),
      name:String(source.name||source.title||(index===0&&base&&base.name)||('Progressionsstufe '+(index+1))).trim(),
      order:Number.isFinite(Number(source.order))?Number(source.order):index,
      sourceId:String(linked),
      media:mediaOf(source.media!==undefined?source:base&&index===0?base:{}),
      sourceName:String(source.sourceName||'').trim()
    };
  }
  function normalizeVariants(ex,materialize){
    const group=groupId(ex),base=ex||{};
    const source=Array.isArray(ex&&ex.progressionVariants)?ex.progressionVariants:[];
    if(!source.length&&!materialize)return [];
    const values=source.length?source.map((item,index)=>normalizeVariant(item,index,group,base)):[normalizeVariant({id:'pv_'+idPart(group)+'_0',name:base.name,sourceId:base.sourceId||base.bankId||'',media:base},0,group,base)];
    if(!values.length)return [];
    values.sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id));
    return values.map((item,index)=>({...item,order:index,groupId:group}));
  }
  function wireVariants(ex){
    const values=normalizeVariants(ex,false);
    if(!values.length)return null;
    return {g:groupId(ex),v:values.map(item=>({i:item.id,n:item.name,o:item.order,s:item.sourceId||'',m:clone(item.media||[])}))};
  }
  function variantsFromWire(wire,ex){
    if(!wire||typeof wire!=='object'||!Array.isArray(wire.v)||!wire.v.length)return [];
    const group=String(wire.g||groupId(ex));
    return wire.v.map((item,index)=>normalizeVariant({id:item&&item.i,name:item&&item.n,order:item&&item.o,sourceId:item&&item.s,media:item&&item.m},index,group,ex));
  }
  function bankItems(){return typeof bank!=='undefined'&&Array.isArray(bank)?bank:[];}
  function currentExercise(){
    try{return typeof currentEditedExercise==='function'?currentEditedExercise():null;}catch(err){return null;}
  }
  let draft=null;
  function ensureDom(){
    let box=$('kgg015ProgressionBox');
    if(box)return box;
    const media=document.querySelector('.editorMediaBox');
    if(!media||!media.parentNode)return null;
    box=document.createElement('section');
    box.id='kgg015ProgressionBox';
    box.className='notice kgg015ProgressionBox';
    media.insertAdjacentElement('afterend',box);
    return box;
  }
  function ensureStyle(){
    if($('kgg015ProgressionStyle'))return;
    const style=document.createElement('style');
    style.id='kgg015ProgressionStyle';
    style.textContent=`
      .kgg015ProgressionBox{display:grid;gap:10px;background:#f8fafc;border:1px solid #dbe3ef;border-radius:16px;padding:12px}
      .kgg015ProgressionIntro{color:#475569;font-size:13px;line-height:1.35;font-weight:700}
      .kgg015ProgressionList{display:grid;gap:8px}
      .kgg015ProgressionRow{display:grid;grid-template-columns:32px minmax(0,1fr);gap:8px;align-items:start;background:#fff;border:1px solid #dbe3ef;border-radius:13px;padding:9px}
      .kgg015ProgressionNo{display:grid;place-items:center;min-height:38px;border-radius:10px;background:#111827;color:#fff;font-weight:950}
      .kgg015ProgressionFields{display:grid;gap:6px;min-width:0}
      .kgg015ProgressionFields input,.kgg015ProgressionFields select{width:100%;min-height:40px;border:1px solid #cbd5e1;border-radius:10px;padding:8px 9px;background:#fff;color:#111827;font:700 14px/1.2 system-ui}
      .kgg015ProgressionActions{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
      .kgg015ProgressionActions button{min-height:38px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#111827;font-weight:850}
      .kgg015ProgressionActions button[data-kgg015-remove]{color:#9f1239;border-color:#fecdd3;background:#fff1f2}
      .kgg015ProgressionEmpty{padding:9px;border:1px dashed #cbd5e1;border-radius:11px;color:#64748b;font-size:13px;font-weight:750}
      .kgg015ProgressionAdd{min-height:44px;border:1px solid #111827;border-radius:12px;background:#111827;color:#fff;font-weight:900}
      @media(max-width:430px){.kgg015ProgressionRow{grid-template-columns:28px minmax(0,1fr);padding:8px}.kgg015ProgressionActions button{font-size:12px;padding:4px}}
    `;
    document.head.appendChild(style);
  }
  function sourceOptions(selected,ex){
    const current=String(ex&&((ex.localId||ex.id)||''));
    const options=['<option value="">Neue Variante direkt anlegen</option>'];
    bankItems().forEach(item=>{
      if(!item||String(item.id||'')===current)return;
      const id=String(item.id||'');
      options.push('<option value="'+esc(id)+'"'+(id===String(selected||'')?' selected':'')+'>'+esc(item.name||id)+' · '+esc(item.unit||'Wdh')+'</option>');
    });
    return options.join('');
  }
  function renderDraft(){
    const box=ensureDom();
    if(!box||!draft)return;
    ensureStyle();
    const ex=draft.exercise||{};
    const list=draft.variants||[];
    box.innerHTML='<b>Progressionsstufen</b><div class="kgg015ProgressionIntro">Leichter steht links, schwerer rechts. Bestehende Übungen können verknüpft oder neue Stufen direkt angelegt werden. Die Hauptübung bleibt Teil derselben Kette.</div><div class="kgg015ProgressionList">'+(list.length?list.map((item,index)=>'<div class="kgg015ProgressionRow" data-kgg015-index="'+index+'"><div class="kgg015ProgressionNo">'+(index+1)+'</div><div class="kgg015ProgressionFields"><input data-kgg015-name placeholder="Name der Stufe" value="'+esc(item.name)+'"><select data-kgg015-source aria-label="Bestehende Übung verknüpfen">'+sourceOptions(item.sourceId,ex)+'</select><div class="kgg015ProgressionActions"><button type="button" data-kgg015-up '+(index===0?'disabled':'')+'>↑ leichter</button><button type="button" data-kgg015-down '+(index===list.length-1?'disabled':'')+'>↓ schwerer</button><button type="button" data-kgg015-remove>Stufe entfernen</button></div></div></div>').join(''):'<div class="kgg015ProgressionEmpty">Noch keine Progressionsstufen angelegt.</div>')+'</div><button type="button" class="kgg015ProgressionAdd" id="kgg015AddProgression">+ Progressionsstufe hinzufügen</button>';
    box.querySelectorAll('[data-kgg015-name]').forEach(input=>input.addEventListener('input',()=>{const row=input.closest('[data-kgg015-index]');const i=Number(row&&row.dataset.kgg015Index);if(draft.variants[i])draft.variants[i].name=input.value;}));
    box.querySelectorAll('[data-kgg015-source]').forEach(select=>select.addEventListener('change',()=>{const row=select.closest('[data-kgg015-index]');const i=Number(row&&row.dataset.kgg015Index),item=draft.variants[i];if(!item)return;const linked=bankItems().find(candidate=>String(candidate&&candidate.id||'')===String(select.value||''));if(linked){item.sourceId=String(linked.id||'');item.sourceName=String(linked.name||'');item.name=String(linked.name||item.name);item.media=mediaOf(linked);}else{item.sourceId='';item.sourceName='';}renderDraft();}));
    box.querySelectorAll('[data-kgg015-up]').forEach(button=>button.addEventListener('click',()=>moveVariant(Number(button.closest('[data-kgg015-index]')?.dataset.kgg015Index),-1)));
    box.querySelectorAll('[data-kgg015-down]').forEach(button=>button.addEventListener('click',()=>moveVariant(Number(button.closest('[data-kgg015-index]')?.dataset.kgg015Index),1)));
    box.querySelectorAll('[data-kgg015-remove]').forEach(button=>button.addEventListener('click',()=>{const i=Number(button.closest('[data-kgg015-index]')?.dataset.kgg015Index);draft.variants.splice(i,1);draft.changed=true;renderDraft();}));
    const add=$('kgg015AddProgression');
    if(add)add.onclick=()=>{if(!draft.variants.length)draft.variants.push(normalizeVariant({id:'pv_'+idPart(draft.groupId)+'_0',name:ex.name,sourceId:ex.sourceId||ex.bankId||'',media:ex},0,draft.groupId,ex));const base=draft.variants[0];draft.variants.push(normalizeVariant({name:String(ex.name||'Übung')+' – Stufe '+(draft.variants.length+1),media:base,sourceId:''},draft.variants.length,draft.groupId,ex));draft.changed=true;renderDraft();};
  }
  function moveVariant(index,delta){
    if(!draft||!Array.isArray(draft.variants))return;
    const target=index+delta;if(index<0||target<0||target>=draft.variants.length)return;
    const temp=draft.variants[index];draft.variants[index]=draft.variants[target];draft.variants[target]=temp;draft.variants.forEach((item,i)=>item.order=i);draft.changed=true;renderDraft();
  }
  function startDraft(ex){
    const values=normalizeVariants(ex,false);
    draft={exercise:ex,groupId:groupId(ex),variants:values.map(item=>({...item,media:clone(item.media||[])})),changed:false};
    renderDraft();
  }
  function persistDraft(ex){
    if(!ex||!draft||!draft.changed)return;
    const values=(draft.variants||[]).filter(item=>String(item.name||'').trim()).map((item,index)=>({...item,id:String(item.id||variantId(draft.groupId,index,item)),groupId:draft.groupId,name:String(item.name||'Progressionsstufe '+(index+1)).trim(),order:index,sourceId:String(item.sourceId||''),media:clone(item.media||[])}));
    ex.progressionGroupId=draft.groupId;
    ex.progressionVariants=values;
    try{if(typeof syncStatePlanToStore==='function')syncStatePlanToStore('ticket_015_progression_variants');}catch(err){console.warn('Progressionsstufen konnten nicht synchronisiert werden:',err)}
    try{if(typeof persistCustomBank==='function')persistCustomBank();}catch(err){console.warn('Progressionsstufen konnten nicht in der Übungsdatenbank gespeichert werden:',err)}
    try{if(typeof save==='function')save();}catch(err){console.warn('Progressionsstufen konnten nicht gespeichert werden:',err)}
  }
  function patchEditor(){
    if(window.__kggTicket015AdminPatched)return;
    const open=window.openEditor,saveEditor=window.saveEditedExercise;
    if(typeof open!=='function'||typeof saveEditor!=='function')return;
    window.__kggTicket015AdminPatched=true;
    window.openEditor=function(ex){const result=open.apply(this,arguments);startDraft(ex);const saveButton=$('saveExercise');if(saveButton)saveButton.onclick=window.saveEditedExercise;return result;};
    window.saveEditedExercise=function(){
      const editedId=typeof state!=='undefined'&&state?state.editId:null;
      const editedBefore=currentExercise();
      const result=saveEditor.apply(this,arguments);
      let edited=null;
      try{edited=typeof state!=='undefined'&&state&&Array.isArray(state.plan)?state.plan.find(item=>String(item.localId||item.id)===String(editedId)):null;}catch(err){}
      if(!edited&&editedBefore&&typeof bank!=='undefined'&&Array.isArray(bank))edited=bank.find(item=>String(item.id)===String(editedId));
      persistDraft(edited||editedBefore);
      draft=null;
      try{if(typeof render==='function')render();}catch(err){}
      return result;
    };
  }
  function patchSerializers(){
    if(window.__kggTicket015SerializersPatched)return;
    const compact=window.compactKggH2Exercise,expand=window.expandKggH2Exercise,patient=window.buildPatientExercisePayload;
    if(typeof compact!=='function'||typeof expand!=='function'||typeof patient!=='function')return;
    window.__kggTicket015SerializersPatched=true;
    window.compactKggH2Exercise=function(ex){const row=compact.apply(this,arguments);const variants=wireVariants(ex);if(variants)row[10]=variants;return row;};
    window.expandKggH2Exercise=function(item){const ex=expand.apply(this,arguments),wire=Array.isArray(item)?item[10]:null,variants=variantsFromWire(wire,ex);if(variants.length){ex.progressionGroupId=String(wire.g||groupId(ex));ex.progressionVariants=variants;}return ex;};
    window.buildPatientExercisePayload=function(ex){const copy=patient.apply(this,arguments),variants=normalizeVariants(ex,false);if(variants.length){copy.progressionGroupId=groupId(ex);copy.progressionVariants=variants.map(item=>{const next={...item,media:clone(item.media||[])};try{if(typeof buildExerciseMediaManifestForPatient==='function'){const m=buildExerciseMediaManifestForPatient(item);if(m&&m.length)next.media=m;}}catch(err){}return next;});}return copy;};
  }
  function init(){
    patchSerializers();
    patchEditor();
    setTimeout(patchSerializers,200);
    setTimeout(patchEditor,200);
    setTimeout(patchSerializers,800);
    setTimeout(patchEditor,800);
  }
  window.KGGTicket015Admin={version:VERSION,normalizeVariants,wireVariants,variantsFromWire};
  if(window.__KGG_TEST__)window.__kggTicket015AdminTest={normalizeVariants,wireVariants,variantsFromWire};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
</script>
<!-- KGG PATCH END kgg-v085-ticket-015-progressions -->
