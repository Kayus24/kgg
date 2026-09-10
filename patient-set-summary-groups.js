(()=>{
  const VERSION='set-summary-groups-v2-range-label';
  if(window.__kggSetSummaryGroups===VERSION)return;
  window.__kggSetSummaryGroups=VERSION;

  function normalizeValue(value){return String(value||'').replace(/\s+/g,' ').trim().toLowerCase()}
  function setLine(line){return String(line||'').match(/^(\s*)(Satz|Set)\s*(\d+)\s*:\s*(.*?)\s*$/i)}
  function labelText(label,start,end,value,indent){const head=start===end?`${label} ${start}:`:`${label} ${start}–${end}:`;return `${indent||''}${head} ${String(value||'').trim()}`.trimEnd()}
  function flushGroup(out,group){
    if(!group.length)return;
    let prev=group[0],same=[group[0]];
    const pushSame=()=>{out.push(labelText(same[0].label,same[0].no,same[same.length-1].no,same[0].value,same[0].indent))};
    for(let i=1;i<group.length;i++){
      const cur=group[i];
      if(cur.no===prev.no+1&&normalizeValue(cur.value)===normalizeValue(prev.value)){same.push(cur)}
      else{pushSame();same=[cur]}
      prev=cur;
    }
    pushSame();
  }
  function compressLines(text){
    const src=String(text||'');
    const lines=src.split(/\n/);
    const out=[];let group=[];
    lines.forEach(line=>{const m=setLine(line);if(m){group.push({indent:m[1]||'',label:m[2],no:Number(m[3]),value:m[4]||''});return}flushGroup(out,group);group=[];out.push(line)});
    flushGroup(out,group);
    return out.join('\n')
  }
  function compressInline(text){
    const src=String(text||'');
    if(src.includes('\n'))return compressLines(src);
    const re=/\b(Satz|Set)\s*(\d+)\s*:\s*([\s\S]*?)(?=(?:\s*\b(?:Satz|Set)\s*\d+\s*:)|$)/gi;
    const group=[];let m,last=0;
    while((m=re.exec(src))){if(src.slice(last,m.index).trim())return src;group.push({indent:'',label:m[1],no:Number(m[2]),value:(m[3]||'').trim()});last=re.lastIndex}
    if(group.length<2||src.slice(last).trim())return src;
    const out=[];flushGroup(out,group);return out.join('\n')
  }
  function compressText(text){return compressInline(compressLines(text))}

  function exerciseName(ex){return String(ex&&(ex.n||ex.name||ex.title||ex[0])||'').trim()}
  function exerciseSets(ex){return Math.max(1,Number(ex&&(ex.sets||ex[1]))||1)}
  function valueMapSignature(values,day,exerciseIndex,setNo){
    const prefix=`${day}|${exerciseIndex}|${setNo}|`;
    const entries=Object.keys(values||{}).filter(key=>key.startsWith(prefix)).map(key=>[key.slice(prefix.length),String(values[key]??'').trim()]).filter(entry=>entry[1]!=='').sort((a,b)=>a[0].localeCompare(b[0]));
    return entries.length?JSON.stringify(entries.map(entry=>[entry[0],normalizeValue(entry[1])])):''
  }
  function hasUniformCompletedSets(values,day,exerciseIndex,setCount){
    if(!values||!day||setCount<2)return false;
    const signatures=[];
    for(let setNo=1;setNo<=setCount;setNo++){
      const signature=valueMapSignature(values,day,exerciseIndex,setNo);
      if(!signature)return false;
      signatures.push(signature);
    }
    return signatures.every(signature=>signature===signatures[0])
  }
  function lineMatchesExercise(line,name){
    const a=normalizeValue(line).replace(/^\s*(?:\d+[.)]|[-•])\s*/,'');
    const b=normalizeValue(name);
    return !!b&&(a===b||a.startsWith(b+':')||a.endsWith(' '+b))
  }
  function rangeLabel(lines,start,end,setCount){
    const segment=lines.slice(start,end).join('\n');
    const language=(localStorage.getItem('kggPatientLang')==='en'||/\bSet\s*\d+/i.test(segment))?'Set':'Satz';
    return `${language} 1–${setCount}:`
  }
  function annotateUniformSetRanges(text,context){
    const plan=context&&context.plan;
    const values=context&&context.values;
    const day=Number(context&&context.day)||0;
    const exercises=plan&&Array.isArray(plan.ex)?plan.ex:[];
    if(!exercises.length||!values||!day)return String(text||'');
    const lines=String(text||'').split(/\n/);
    const positions=[];
    exercises.forEach((ex,index)=>{
      const name=exerciseName(ex);
      if(!name)return;
      const lineIndex=lines.findIndex((line,at)=>!positions.some(pos=>pos.lineIndex===at)&&lineMatchesExercise(line,name));
      if(lineIndex>=0)positions.push({exerciseIndex:index,lineIndex,name,setCount:exerciseSets(ex)})
    });
    positions.sort((a,b)=>a.lineIndex-b.lineIndex);
    for(let posIndex=positions.length-1;posIndex>=0;posIndex--){
      const pos=positions[posIndex];
      if(pos.setCount<2||!hasUniformCompletedSets(values,day,pos.exerciseIndex,pos.setCount))continue;
      const end=posIndex+1<positions.length?positions[posIndex+1].lineIndex:lines.length;
      const segment=lines.slice(pos.lineIndex,end).join('\n');
      const completeRange=new RegExp(`\\b(?:Satz|Set)\\s*1\\s*[–—-]\\s*${pos.setCount}\\s*:`,`i`);
      if(completeRange.test(segment))continue;
      if(/\b(?:Satz|Set)\s*\d+\s*:/i.test(segment))continue;
      lines.splice(pos.lineIndex+1,0,rangeLabel(lines,pos.lineIndex,end,pos.setCount));
    }
    return lines.join('\n')
  }
  function currentContext(){
    return {
      plan:typeof p!=='undefined'&&p?p:null,
      values:typeof v!=='undefined'&&v&&typeof v==='object'?v:null,
      day:typeof d!=='undefined'?Number(d):0
    }
  }
  function apply(){
    const el=document.getElementById('sum');
    if(!el)return;
    const before=el.textContent||'';
    const compressed=compressText(before);
    const after=annotateUniformSetRanges(compressed,currentContext());
    if(after!==before)el.textContent=after;
  }
  function patchShowQr(){
    if(window.__kggSetSummaryGroupsPatched||typeof showQr!=='function')return;
    window.__kggSetSummaryGroupsPatched=1;
    const old=showQr;
    window.showQr=function(){const r=old.apply(this,arguments);setTimeout(apply,0);setTimeout(apply,80);setTimeout(apply,240);return r};
  }
  if(window.__KGG_TEST__)window.__kggSetSummaryGroupsTest={compressText,annotateUniformSetRanges,valueMapSignature,hasUniformCompletedSets};
  function init(){patchShowQr();setTimeout(patchShowQr,300);setTimeout(patchShowQr,1000);setTimeout(apply,1200)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();

(()=>{
  const VERSION='ticket-015-progressions-v1';
  if(window.__kggTicket015Patient===VERSION)return;
  window.__kggTicket015Patient=VERSION;
  const HISTORY_KEY='kggProgressionHistoryV1';
  const HISTORY_VERSION=1;
  const $=id=>document.getElementById(id);
  const clone=value=>{try{return JSON.parse(JSON.stringify(value));}catch(err){return value;}};
  const esc=value=>String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const idPart=value=>String(value||'').replace(/[^A-Za-z0-9_-]+/g,'_').slice(0,80)||'exercise';
  const safeJson=(value,fallback)=>{try{return JSON.parse(value||'')}catch(err){return fallback}};
  let history=loadHistory();
  let sessionSelection={};
  let rawVariantsReady=false;
  let originalNames=[];
  let originalMedia=[];
  let originalRender=null;
  let originalPut=null;
  let originalText=null;
  let originalShowQr=null;

  function loadHistory(){
    const value=safeJson(localStorage.getItem(HISTORY_KEY),null);
    if(!value||value.version!==HISTORY_VERSION||!value.groups||typeof value.groups!=='object')return {version:HISTORY_VERSION,groups:{},current:{day:0,records:{}},finalized:{}};
    value.current=value.current&&typeof value.current==='object'?value.current:{day:0,records:{}};
    value.current.records=value.current.records&&typeof value.current.records==='object'?value.current.records:{};
    value.finalized=value.finalized&&typeof value.finalized==='object'?value.finalized:{};
    return value;
  }
  function saveHistory(){try{localStorage.setItem(HISTORY_KEY,JSON.stringify(history))}catch(err){}}
  function currentDay(){return Number(typeof d!=='undefined'?d:1)||1}
  function ensureDay(){const day=currentDay();if(Number(history.current&&history.current.day)!==day){history.current={day,records:{}}}if(!history.current.records||typeof history.current.records!=='object')history.current.records={};return history.current}
  function rawPlan(){const saved=safeJson(localStorage.getItem('kggCurrentPlanV1'),null);return saved&&saved.plan?saved.plan:null}
  function rawExercise(index){const plan=rawPlan();return plan&&Array.isArray(plan.e)?plan.e[index]:null}
  function groupOf(ex,index){return String(ex&&ex.progressionGroupId||'pg_'+idPart(ex&&((ex.localId||ex.id)||('exercise_'+index))));}
  function variantFrom(value,index,group,base){
    const item=value&&typeof value==='object'?value:{};
    const media=Array.isArray(item.media)?clone(item.media):(item.media?clone(item.media):Array.isArray(base&&base[7])?clone(base[7]):base&&base.media?clone(base.media):[]);
    return {id:String(item.id||item.i||('pv_'+idPart(group)+'_'+index)),groupId:String(item.groupId||group),name:String(item.name||item.n||item.title||('Progressionsstufe '+(index+1))).trim(),order:Number.isFinite(Number(item.order??item.o))?Number(item.order??item.o):index,media,sourceId:String(item.sourceId||item.s||'')};
  }
  function variantsFor(ex,index){
    const group=groupOf(ex,index),raw=rawExercise(index),wire=raw&&raw[10];
    let source=Array.isArray(ex&&ex.progressionVariants)?ex.progressionVariants:[];
    if(!source.length&&wire&&typeof wire==='object'&&Array.isArray(wire.v))source=wire.v.map(item=>({id:item&&item.i,name:item&&item.n,order:item&&item.o,sourceId:item&&item.s,media:item&&item.m}));
    if(!source.length)return [];
    const values=source.map((item,i)=>variantFrom(item,i,String(wire&&wire.g||group),raw||ex));
    values.sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id));
    return values.map((item,i)=>({...item,order:i,groupId:String(wire&&wire.g||group)}));
  }
  function syncRawVariants(){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex))return;
    if(!originalNames.length)originalNames=p.ex.map(ex=>String(ex&&ex.n||''));
    if(!originalMedia.length)originalMedia=p.ex.map(ex=>clone(ex&&ex.media));
    p.ex.forEach((ex,index)=>{
      const values=variantsFor(ex,index);
      if(values.length){ex.progressionGroupId=values[0].groupId;ex.progressionVariants=values}
    });
    rawVariantsReady=true;
  }
  function valuesForExercise(index){
    if(typeof p==='undefined'||!p||!p.ex||!p.ex[index])return [];
    return variantsFor(p.ex[index],index);
  }
  function groupState(index){
    const ex=p&&p.ex&&p.ex[index],values=valuesForExercise(index),gid=values[0]&&values[0].groupId||groupOf(ex,index);
    if(!history.groups[gid])history.groups[gid]={lastBySet:{},dominantId:''};
    const group=history.groups[gid];group.lastBySet=group.lastBySet&&typeof group.lastBySet==='object'?group.lastBySet:{};
    return {gid,group,values};
  }
  function variantById(values,id){return values.find(item=>String(item.id)===String(id))||null}
  function defaultId(index,setNo){
    const state=groupState(index),values=state.values;if(!values.length)return '';
    const key=String(index)+'|'+String(setNo),selected=sessionSelection[key];
    if(selected&&variantById(values,selected))return selected;
    if(state.group.lastBySet[key]&&variantById(values,state.group.lastBySet[key]))return state.group.lastBySet[key];
    if(state.group.dominantId&&variantById(values,state.group.dominantId))return state.group.dominantId;
    return values[0].id;
  }
  function selectedId(index,setNo){return defaultId(index,setNo)}
  function currentRecordKey(index,setNo){return String(index)+'|'+String(setNo)}
  function recordSuccessfulEdit(index,setNo){
    const state=groupState(index),values=state.values;if(!values.length)return;
    const id=selectedId(index,setNo),key=currentRecordKey(index,setNo);if(!id)return;
    const dayState=ensureDay(),old=dayState.records[key];
    if(!old)dayState.records[key]={exerciseIndex:index,setNo:Number(setNo),id:String(id),previousId:state.group.lastBySet[key]?String(state.group.lastBySet[key]):''};
    else old.id=String(id);
    state.group.lastBySet[key]=String(id);
    saveHistory();
    applyDominantMedia();
    renderGalleries(index);
  }
  function dominantFor(index,dayOnly){
    const state=groupState(index),values=state.values;if(!values.length)return null;
    const counts={};const records=dayOnly&&Number(history.current.day)===currentDay()?history.current.records:state.group.lastBySet;
    Object.keys(records||{}).forEach(key=>{
      const rec=records[key];if(!rec||Number(rec.exerciseIndex??String(key).split('|')[0])!==Number(index))return;
      const id=String(rec.id||rec);if(variantById(values,id))counts[id]=(counts[id]||0)+1;
    });
    let winner=null;values.forEach(item=>{const count=counts[item.id]||0;if(!winner||count>winner.count||(count===winner.count&&item.order>winner.item.order))winner={item,count}});
    return winner&&winner.count>0?winner.item:null;
  }
  function applyDominantMedia(){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex))return;
    syncRawVariants();
    p.ex.forEach((ex,index)=>{
      const values=valuesForExercise(index);if(!values.length)return;
      const state=groupState(index),winner=state.group.dominantId&&variantById(values,state.group.dominantId)||dominantFor(index,false)||values[0];
      ex.media=clone(winner&&winner.media||originalMedia[index]||[]);
    });
  }
  function displayedVariant(index){
    const state=groupState(index),values=state.values;if(!values.length)return null;
    return state.group.dominantId&&variantById(values,state.group.dominantId)||dominantFor(index,false)||values[0];
  }
  function applyDisplayNames(){
    if(!document||typeof document.querySelectorAll!=='function')return;
    document.querySelectorAll('#list .ex').forEach((card,index)=>{const variant=displayedVariant(index),title=card.querySelector('h3');if(variant&&title)title.textContent=variant.name;});
  }
  function css(){
    if(!document||typeof document.createElement!=='function'||!document.head)return;
    if($('kggTicket015PatientStyle'))return;
    const style=document.createElement('style');style.id='kggTicket015PatientStyle';style.textContent=`
      .kgg015Gallery{display:grid;grid-template-columns:36px minmax(0,1fr) 36px;gap:7px;align-items:stretch;margin-top:10px;padding:9px;border:1px solid #d8dee9;border-radius:14px;background:#f8fafc}
      .kgg015Gallery button{min-height:38px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#111827;font-weight:900}
      .kgg015GalleryViewport{min-width:0;text-align:center;display:grid;gap:5px;touch-action:pan-y}
      .kgg015GalleryStage{font-size:12px;font-weight:900;color:#334155;min-height:18px}
      .kggProgressionMediaBox{min-height:82px;display:grid;place-items:center;overflow:hidden;border-radius:11px;background:#e2e8f0;color:#64748b;font-size:12px;font-weight:750}
      .kggProgressionMediaBox img{display:block;width:100%;max-height:130px;object-fit:contain;background:#fff}
      .kggProgressionMediaBox small{padding:3px 5px;font-size:10px}
      .kgg015GalleryDots{display:flex;justify-content:center;gap:5px;flex-wrap:wrap}
      .kgg015GalleryDots button{min-height:25px;min-width:25px;padding:2px 7px;border-radius:999px;font-size:11px}
      .kgg015GalleryDots button[aria-current="true"]{background:#111827;color:#fff;border-color:#111827}
      .kgg015VariantBadge{display:inline-flex;align-items:center;gap:5px;margin-left:7px;padding:2px 7px;border-radius:999px;background:#eef2ff;color:#3730a3;font-size:11px;font-weight:850}
      @media(max-width:430px){.kgg015Gallery{grid-template-columns:32px minmax(0,1fr) 32px;padding:7px}.kggProgressionMediaBox{min-height:70px}.kggProgressionMediaBox img{max-height:110px}}
    `;document.head.appendChild(style);
  }
  function selectVariant(index,setNo,id){const values=valuesForExercise(index);if(!variantById(values,id))return;sessionSelection[currentRecordKey(index,setNo)]=String(id);renderGalleries(index)}
  function mediaMarkup(item,targetId,index,setNo){
    if(!item)return '<span>Kein Bild hinterlegt</span><small>Die Stufe ist trotzdem auswählbar.</small>';
    const node='<div class="kggProgressionMediaBox loading" data-kgg-progression-media="'+esc(targetId)+'"><span>Bild wird geladen ...</span><small>Verschlüsselte Datei wird lokal verwendet.</small></div>';
    setTimeout(()=>{try{if(window.KGGPatientMediaRetryCache&&typeof window.KGGPatientMediaRetryCache.loadMedia==='function')window.KGGPatientMediaRetryCache.loadMedia(item,index,setNo,targetId)}catch(err){}},0);
    return node;
  }
  function galleryHtml(index,setNo,cardSet){
    const state=groupState(index),values=state.values;if(!values.length)return;
    const id=selectedId(index,setNo),at=Math.max(0,values.findIndex(item=>item.id===id)),item=values[at],target='kgg015-media-'+index+'-'+setNo+'-'+id;
    const dots=values.map((value,i)=>'<button type="button" data-kgg015-stage="'+esc(value.id)+'" aria-current="'+(i===at?'true':'false')+'" aria-label="Stufe '+(i+1)+': '+esc(value.name)+'">'+(i+1)+'</button>').join('');
    const box=document.createElement('div');box.className='kgg015Gallery';box.dataset.kgg015Gallery=index+'|'+setNo;box.innerHTML='<button type="button" data-kgg015-prev aria-label="Leichtere Progressionsstufe" '+(at===0?'disabled':'')+'>‹</button><div class="kgg015GalleryViewport"><div class="kgg015GalleryStage">Stufe '+(at+1)+' von '+values.length+' · '+esc(item.name)+'</div>'+mediaMarkup(item.media&&item.media[0],target,index,setNo)+'<div class="kgg015GalleryDots">'+dots+'</div></div><button type="button" data-kgg015-next aria-label="Schwerere Progressionsstufe" '+(at===values.length-1?'disabled':'')+'>›</button>';
    box.querySelector('[data-kgg015-prev]').onclick=()=>{if(at>0)selectVariant(index,setNo,values[at-1].id)};
    box.querySelector('[data-kgg015-next]').onclick=()=>{if(at<values.length-1)selectVariant(index,setNo,values[at+1].id)};
    box.querySelectorAll('[data-kgg015-stage]').forEach(button=>button.onclick=()=>selectVariant(index,setNo,button.dataset.kgg015Stage));
    let startX=null;const viewport=box.querySelector('.kgg015GalleryViewport');if(viewport){viewport.onpointerdown=event=>{startX=event.clientX};viewport.onpointerup=event=>{if(startX==null)return;const dx=event.clientX-startX;startX=null;if(Math.abs(dx)<35)return;event.preventDefault();if(dx>0&&at>0)selectVariant(index,setNo,values[at-1].id);if(dx<0&&at<values.length-1)selectVariant(index,setNo,values[at+1].id)}}
    cardSet.appendChild(box);
  }
  function renderGalleries(onlyIndex){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex)||!document||typeof document.querySelectorAll!=='function')return;
    css();const cards=[...document.querySelectorAll('#list .ex')];cards.forEach((card,index)=>{if(onlyIndex!==undefined&&Number(onlyIndex)!==index)return;card.querySelectorAll('.kgg015Gallery').forEach(node=>node.remove());const values=valuesForExercise(index);if(!values.length)return;const sets=[...card.querySelectorAll('.set')];sets.forEach((set,setIndex)=>galleryHtml(index,setIndex+1,set));});applyDisplayNames();
  }
  function notesFor(day){
    if(Number(history.current.day)!==Number(day))return '';
    const rows=[];Object.keys(history.current.records||{}).forEach(key=>{const rec=history.current.records[key];if(!rec||!rec.previousId||String(rec.previousId)===String(rec.id))return;const index=Number(rec.exerciseIndex),values=valuesForExercise(index),from=variantById(values,rec.previousId),to=variantById(values,rec.id);if(from&&to)rows.push((originalNames[index]||'Übung')+': '+from.name+' → '+to.name)});
    return rows.length?'\n\nVariantenwechsel:\n'+[...new Set(rows)].join('\n'):'';
  }
  function wrapText(){
    if(originalText||typeof text!=='function')return;
    originalText=text;window.text=function(day){
      syncRawVariants();const savedNames=p&&p.ex?p.ex.map(ex=>ex.n):[];
      try{if(p&&p.ex)p.ex.forEach((ex,index)=>{const variant=displayedVariant(index);if(variant)ex.n=variant.name});return String(originalText.apply(this,arguments)||'')+notesFor(day)}finally{if(p&&p.ex)p.ex.forEach((ex,index)=>{ex.n=savedNames[index]})}
    };
  }
  function wrapPut(){
    if(originalPut||typeof put!=='function')return;
    originalPut=put;window.put=function(e,s,x,y,z){const result=originalPut.apply(this,arguments);if(String(z??'').trim()!=='')recordSuccessfulEdit(Number(e),Number(s));return result};
  }
  function finalizeDominance(day){
    if(Number(history.finalized[day]||0)===1)return;
    ensureDay();if(Number(history.current.day)!==Number(day))return;
    p.ex.forEach((ex,index)=>{const state=groupState(index),winner=dominantFor(index,true);if(winner)state.group.dominantId=winner.id});
    history.finalized[day]=1;saveHistory();applyDominantMedia();
  }
  function wrapShowQr(){
    if(originalShowQr||typeof showQr!=='function')return;
    originalShowQr=showQr;window.showQr=function(finalize){const day=currentDay();if(finalize)finalizeDominance(day);const result=originalShowQr.apply(this,arguments);setTimeout(()=>{applyDominantMedia();applyDisplayNames();renderGalleries()},0);return result};
  }
  function wrapRender(){
    if(originalRender||typeof render!=='function')return;
    originalRender=render;window.render=function(){syncRawVariants();applyDominantMedia();const result=originalRender.apply(this,arguments);[0,70,260].forEach(delay=>setTimeout(()=>{renderGalleries()},delay));return result};
  }
  function init(){
    syncRawVariants();wrapRender();wrapPut();wrapText();wrapShowQr();css();renderGalleries();
    [250,800,1600].forEach(delay=>setTimeout(()=>{syncRawVariants();wrapRender();wrapPut();wrapText();wrapShowQr();renderGalleries()},delay));
  }
  function testDominant(values,records){const counts={};Object.values(records||{}).forEach(record=>{const id=String(record&&record.id||record);if(values.some(item=>String(item.id)===id))counts[id]=(counts[id]||0)+1});let winner=null;values.forEach(item=>{const count=counts[item.id]||0;if(!winner||count>winner.count||(count===winner.count&&item.order>winner.item.order))winner={item,count}});return winner&&winner.item||null}
  function testNote(previous,current,name){return previous&&String(previous)!==String(current)?String(name||'Übung')+': '+previous+' → '+current:''}
  if(window.__KGG_TEST__)window.__kggTicket015PatientTest={version:VERSION,normalizeVariant:variantFrom,dominant:testDominant,note:testNote};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
