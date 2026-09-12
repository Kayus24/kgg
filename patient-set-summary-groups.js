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
  const VERSION='ticket-015-progressions-v2-main-controls';
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
  let originalOpenPad=null;
  let currentPlanId='';
  let activeSet={index:0,setNo:1};
  let preferActiveMedia=false;

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
  function planId(){return String(typeof p!=='undefined'&&p&&p.id||'plan')}
  function ensureDay(){const day=currentDay(),pid=planId();if(String(history.current&&history.current.planId||'')!==pid||Number(history.current&&history.current.day)!==day){history.current={planId:pid,day,records:{}};sessionSelection={}}if(!history.current.records||typeof history.current.records!=='object')history.current.records={};return history.current}
  function rawPlan(){const saved=safeJson(localStorage.getItem('kggCurrentPlanV1'),null);return saved&&saved.plan?saved.plan:null}
  function rawExercise(index){const plan=rawPlan();return plan&&Array.isArray(plan.e)?plan.e[index]:null}
  function groupOf(ex,index){return String(ex&&ex.progressionGroupId||'pg_'+idPart(ex&&((ex.localId||ex.id)||('exercise_'+index))));}
  function variantFrom(value,index,group,base){
    const item=value&&typeof value==='object'?value:{};
    const media=Array.isArray(item.media)?clone(item.media):(item.media?clone(item.media):Array.isArray(base&&base[7])?clone(base[7]):base&&base.media?clone(base.media):[]);
    return {id:String(item.id||item.i||('pv_'+idPart(group)+'_'+index)),groupId:String(item.groupId||group),name:String(item.name||item.n||item.title||('Progressionsstufe '+(index+1))).trim(),order:Number.isFinite(Number(item.order??item.o))?Number(item.order??item.o):index,media,sourceId:String(item.sourceId||item.s||'')};
  }
  function variantsFor(ex,index){
    const group=groupOf(ex,index),raw=rawExercise(index),wire=raw&&raw[11]&&typeof raw[11]==='object'?raw[11]:(raw&&raw[10]&&typeof raw[10]==='object'?raw[10]:null);
    let source=Array.isArray(ex&&ex.progressionVariants)?ex.progressionVariants:[];
    if(!source.length&&wire&&typeof wire==='object'&&Array.isArray(wire.v))source=wire.v.map(item=>({id:item&&item.i,name:item&&item.n,order:item&&item.o,sourceId:item&&item.s,media:item&&item.m}));
    if(!source.length)return [];
    const values=source.map((item,i)=>variantFrom(item,i,String(wire&&wire.g||group),raw||ex));
    values.sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id));
    return values.map((item,i)=>({...item,order:i,groupId:String(wire&&wire.g||group)}));
  }
  function syncRawVariants(){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex))return;
    if(currentPlanId&&currentPlanId!==planId()){sessionSelection={};originalNames=[];originalMedia=[];history.current={planId:planId(),day:currentDay(),records:{}}}
    currentPlanId=planId();
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
    const storageKey=planId()+'|'+gid;
    if(!history.groups[storageKey])history.groups[storageKey]={lastBySet:{},dominantId:''};
    const group=history.groups[storageKey];group.lastBySet=group.lastBySet&&typeof group.lastBySet==='object'?group.lastBySet:{};
    return {gid,storageKey,group,values};
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
    ensureDay();
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
    const counts={};const records=dayOnly&&String(history.current.planId||'')===planId()&&Number(history.current.day)===currentDay()?history.current.records:state.group.lastBySet;
    Object.keys(records||{}).forEach(key=>{
      const rec=records[key];if(!rec||Number(rec.exerciseIndex??String(key).split('|')[0])!==Number(index))return;
      const id=String(rec.id||rec);if(variantById(values,id))counts[id]=(counts[id]||0)+1;
    });
    let winner=null;values.forEach(item=>{const count=counts[item.id]||0;if(!winner||count>winner.count||(count===winner.count&&item.order>winner.item.order))winner={item,count}});
    return winner&&winner.count>0?winner.item:null;
  }
  function applyDominantMedia(preferActiveSet=false){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex))return;
    syncRawVariants();
    p.ex.forEach((ex,index)=>{
      const values=valuesForExercise(index);if(!values.length)return;
      const state=groupState(index),winner=state.group.dominantId&&variantById(values,state.group.dominantId)||dominantFor(index,false)||values[0];
      const active=preferActiveSet&&activeSet&&Number(activeSet.index)===index?variantById(values,selectedId(index,activeSet.setNo)):null;
      ex.media=clone((active||winner)&&((active||winner).media)||originalMedia[index]||[]);
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
      .kgg015MainProgressionHost{position:relative;overflow:hidden}
      .kgg015MainPager{position:absolute;inset:0;z-index:3;overflow:hidden;border-radius:12px;background:#e2e8f0;touch-action:pan-y}
      .kgg015MainPagerTrack{display:flex;width:300%;height:100%;transform:translate3d(-33.333333%,0,0);transition:transform .32s cubic-bezier(.2,.78,.2,1);will-change:transform}
      .kgg015MainPagerTrack.is-dragging{transition:none;cursor:grabbing}
      .kgg015MainPagerSlide{position:relative;display:grid;place-items:center;flex:0 0 33.333333%;min-width:0;height:100%;opacity:.55;transform:scale(.94);transition:opacity .24s ease,transform .24s ease}
      .kgg015MainPagerSlide[data-active="true"]{opacity:1;transform:scale(1)}
      .kgg015MainPagerSlide .kggProgressionMediaBox{width:100%;height:100%;min-height:100%;border:0;border-radius:0;background:#e2e8f0}
      .kgg015MainPagerSlide .kggProgressionMediaBox img{max-height:100%;height:100%;object-fit:contain}
      .kgg015MainPagerPlaceholder{display:grid;place-items:center;height:100%;padding:12px;color:#64748b;font-size:12px;font-weight:800;text-align:center}
      .kgg015MainProgressionControls{position:absolute;inset:0;display:flex;align-items:center;justify-content:space-between;padding:0 8px;pointer-events:none;z-index:4}
      .kgg015MainProgressionControl{pointer-events:auto;width:44px;height:44px;border:1px solid rgba(255,255,255,.72);border-radius:999px;background:rgba(255,255,255,.68);color:#111827;box-shadow:0 8px 22px rgba(15,23,42,.18),inset 0 1px 0 rgba(255,255,255,.88);backdrop-filter:blur(16px) saturate(1.35);-webkit-backdrop-filter:blur(16px) saturate(1.35);line-height:1;font-weight:900;display:grid;place-items:center}
      .kgg015MainProgressionControl:disabled{opacity:.32;cursor:default}
      .kgg015MainProgressionControl:focus-visible{outline:3px solid #2563eb;outline-offset:2px}
      .kgg015MainProgressionTriangle{display:block;width:0;height:0;border-top:9px solid transparent;border-bottom:9px solid transparent}
      .kgg015MainProgressionTriangle.prev{border-right:14px solid currentColor;margin-left:-3px}
      .kgg015MainProgressionTriangle.next{border-left:14px solid currentColor;margin-right:-3px}
      .kgg015MainProgressionStage{position:absolute;left:50%;bottom:8px;transform:translateX(-50%);max-width:calc(100% - 112px);padding:4px 9px;border:1px solid rgba(255,255,255,.7);border-radius:999px;background:rgba(255,255,255,.7);color:#334155;font-size:11px;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
      .kgg015MainProgressionThumbs{display:flex;justify-content:center;gap:8px;overflow-x:auto;scrollbar-width:none;margin:8px 8px 2px;padding:2px 8px 4px;touch-action:pan-x}
      .kgg015MainProgressionThumbs::-webkit-scrollbar{display:none}
      .kgg015MainProgressionThumb{position:relative;flex:0 0 58px;width:58px;height:46px;padding:0;border:2px solid transparent;border-radius:10px;background:#f1f5f9;overflow:hidden;cursor:pointer;transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}
      .kgg015MainProgressionThumb[aria-current="true"]{border-color:#2563eb;box-shadow:0 0 0 3px #dbeafe;transform:scale(1.06)}
      .kgg015MainProgressionThumb .kggProgressionMediaBox{height:100%;min-height:100%;border:0;border-radius:0;padding:0;background:#e2e8f0}
      .kgg015MainProgressionThumb .kggProgressionMediaBox img{display:block;width:100%;height:100%;object-fit:cover}
      .kgg015MainProgressionThumbLabel{position:absolute;right:3px;bottom:2px;padding:1px 4px;border-radius:999px;background:rgba(255,255,255,.78);color:#334155;font-size:9px;font-weight:900}
      @media(max-width:430px){.kgg015MainProgressionControl{width:40px;height:40px}.kgg015MainProgressionControls{padding:0 6px}.kgg015MainProgressionStage{bottom:6px}.kgg015MainProgressionThumb{flex-basis:52px;width:52px;height:42px}}
      @media(max-width:430px){.kgg015Gallery{grid-template-columns:32px minmax(0,1fr) 32px;padding:7px}.kggProgressionMediaBox{min-height:70px}.kggProgressionMediaBox img{max-height:110px}}
    `;document.head.appendChild(style);
  }
  function mainMediaBox(index){const card=[...document.querySelectorAll('#list .ex')][index];return card&&card.querySelector('.kggMediaList .kggMediaBox');}
  function progressionThumbMarkup(item,targetId,index,setNo,stageIndex){
    const media=item&&item.media&&item.media[0];
    if(!media)return '<span class="kgg015MainPagerPlaceholder">Kein Bild hinterlegt</span>';
    const node='<div class="kggProgressionMediaBox loading" data-kgg-progression-media="'+esc(targetId)+'"><span>…</span></div>';
    setTimeout(()=>{try{if(window.KGGPatientMediaRetryCache&&typeof window.KGGPatientMediaRetryCache.loadMedia==='function')window.KGGPatientMediaRetryCache.loadMedia(media,index,setNo,targetId)}catch(err){}},0);
    return node;
  }
  function pagerSlide(item,targetId,index,setNo,stageIndex,active){
    return '<div class="kgg015MainPagerSlide" data-active="'+(active?'true':'false')+'" data-stage-index="'+stageIndex+'">'+progressionThumbMarkup(item,targetId,index,setNo,stageIndex)+'</div>';
  }
  function mainPagerThumbs(card,index,setNo,values,at){
    card.querySelectorAll('.kgg015MainProgressionThumbs').forEach(node=>node.remove());
    const thumbs=document.createElement('div');thumbs.className='kgg015MainProgressionThumbs';thumbs.setAttribute('aria-label','Progressionsstufen auswählen');
    thumbs.innerHTML=values.map((item,i)=>{const target='kgg015-thumb-'+index+'-'+setNo+'-'+item.id;return '<button type="button" class="kgg015MainProgressionThumb" data-kgg015-main-stage="'+esc(item.id)+'" aria-current="'+(i===at?'true':'false')+'" aria-label="Stufe '+(i+1)+': '+esc(item.name)+'"><div class="kggProgressionMediaBox loading" data-kgg-progression-media="'+esc(target)+'"><span>…</span></div><span class="kgg015MainProgressionThumbLabel">'+(i+1)+'</span></button>'}).join('');
    const mediaList=card.querySelector('.kggMediaList');if(mediaList)mediaList.insertAdjacentElement('afterend',thumbs);else card.appendChild(thumbs);
    thumbs.querySelectorAll('[data-kgg015-main-stage]').forEach(button=>button.onclick=()=>selectVariant(index,setNo,button.dataset.kgg015MainStage));
    values.forEach((item,i)=>{const media=item.media&&item.media[0];if(!media)return;const target='kgg015-thumb-'+index+'-'+setNo+'-'+item.id;setTimeout(()=>{try{if(window.KGGPatientMediaRetryCache&&typeof window.KGGPatientMediaRetryCache.loadMedia==='function')window.KGGPatientMediaRetryCache.loadMedia(media,index,setNo,target)}catch(err){}},0);});
    const active=thumbs.querySelector('[aria-current="true"]');if(active)active.scrollIntoView({block:'nearest',inline:'center'});
  }
  function bindMainPager(pager,index,setNo,values,at){
    const track=pager.querySelector('.kgg015MainPagerTrack');let startX=null,lastX=0;
    const finish=(event,cancelled=false)=>{if(startX===null)return;const dx=lastX-startX;startX=null;try{pager.releasePointerCapture?.(event.pointerId)}catch(err){}track.classList.remove('is-dragging');if(cancelled||Math.abs(dx)<38){track.style.transform='translate3d(-33.333333%,0,0)';return}shiftVariant(index,setNo,dx<0?1:-1)};
    pager.onpointerdown=event=>{if(event.target.closest('button'))return;startX=event.clientX;lastX=startX;track.classList.add('is-dragging');try{pager.setPointerCapture?.(event.pointerId)}catch(err){}};
    pager.onpointermove=event=>{if(startX===null)return;lastX=event.clientX;const raw=lastX-startX,atStart=at===0&&raw>0,atEnd=at===values.length-1&&raw<0,dx=atStart||atEnd?raw*.28:raw;track.style.transform='translate3d(calc(-33.333333% + '+dx+'px),0,0)'};
    pager.onpointerup=event=>finish(event);pager.onpointercancel=event=>finish(event,true);pager.onlostpointercapture=()=>{if(startX!==null){startX=null;track.classList.remove('is-dragging');track.style.transform='translate3d(-33.333333%,0,0)'}};
  }
  function renderMainProgressionControls(index=activeSet.index,setNo=activeSet.setNo){
    const values=valuesForExercise(index);if(!values.length)return;
    const box=mainMediaBox(index),card=box&&box.closest('.ex');if(!box||!card)return;
    box.classList.add('kgg015MainProgressionHost');box.querySelectorAll('.kgg015MainPager').forEach(node=>node.remove());
    const id=selectedId(index,setNo),at=Math.max(0,values.findIndex(item=>String(item.id)===String(id)));
    const previous=at>0?values[at-1]:null,current=values[at]||values[0],next=at<values.length-1?values[at+1]:null,pager=document.createElement('div');
    pager.className='kgg015MainPager';
    const prevTarget=previous?'kgg015-main-'+index+'-'+setNo+'-'+previous.id:'',currentTarget='kgg015-main-'+index+'-'+setNo+'-'+current.id,nextTarget=next?'kgg015-main-'+index+'-'+setNo+'-'+next.id:'';
    pager.innerHTML='<div class="kgg015MainPagerTrack">'+pagerSlide(previous,prevTarget,index,setNo,at-1,false)+pagerSlide(current,currentTarget,index,setNo,at,true)+pagerSlide(next,nextTarget,index,setNo,at+1,false)+'</div><div class="kgg015MainProgressionControls"><button type="button" class="kgg015MainProgressionControl" data-kgg015-main-prev aria-label="Leichtere Progressionsstufe" '+(at===0?'disabled':'')+'><i class="kgg015MainProgressionTriangle prev" aria-hidden="true"></i></button><span class="kgg015MainProgressionStage" aria-live="polite">Stufe '+(at+1)+' · '+esc(current.name)+'</span><button type="button" class="kgg015MainProgressionControl" data-kgg015-main-next aria-label="Schwerere Progressionsstufe" '+(at===values.length-1?'disabled':'')+'><i class="kgg015MainProgressionTriangle next" aria-hidden="true"></i></button></div>';
    box.appendChild(pager);pager.querySelector('[data-kgg015-main-prev]').onclick=()=>shiftVariant(index,setNo,-1);pager.querySelector('[data-kgg015-main-next]').onclick=()=>shiftVariant(index,setNo,1);bindMainPager(pager,index,setNo,values,at);mainPagerThumbs(card,index,setNo,values,at);
  }
  function refreshMainProgression(index=activeSet.index){
    try{if(window.KGGPatientMediaRetryCache&&typeof window.KGGPatientMediaRetryCache.render==='function')window.KGGPatientMediaRetryCache.render()}catch(err){}
    [0,80,320].forEach(delay=>setTimeout(()=>renderMainProgressionControls(index,activeSet.setNo),delay));
  }
  function shiftVariant(index,setNo,delta){const values=valuesForExercise(index);if(!values.length)return;const at=Math.max(0,values.findIndex(item=>String(item.id)===String(selectedId(index,setNo)))),next=values[at+delta];if(!next)return;selectVariant(index,setNo,next.id)}
  function selectVariant(index,setNo,id){const values=valuesForExercise(index),item=variantById(values,id);if(!item)return;activeSet={index:Number(index),setNo:Number(setNo)};preferActiveMedia=true;sessionSelection[currentRecordKey(index,setNo)]=String(id);applyDominantMedia(true);renderGalleries(index);refreshMainProgression(index)}
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
    css();ensureDay();const cards=[...document.querySelectorAll('#list .ex')];cards.forEach((card,index)=>{if(onlyIndex!==undefined&&Number(onlyIndex)!==index)return;card.querySelectorAll('.kgg015Gallery').forEach(node=>node.remove());if(!valuesForExercise(index).length)return;});applyDisplayNames();if(onlyIndex===undefined||Number(onlyIndex)===Number(activeSet.index))renderMainProgressionControls(activeSet.index,activeSet.setNo);
  }
  function notesFor(day){
    if(String(history.current.planId||'')!==planId()||Number(history.current.day)!==Number(day))return '';
    const rows=[];Object.keys(history.current.records||{}).forEach(key=>{const rec=history.current.records[key];if(!rec||!rec.previousId||String(rec.previousId)===String(rec.id))return;const index=Number(rec.exerciseIndex),values=valuesForExercise(index),from=variantById(values,rec.previousId),to=variantById(values,rec.id);if(from&&to)rows.push((originalNames[index]||'Übung')+': '+from.name+' → '+to.name)});
    return rows.length?'\n\nVariantenwechsel:\n'+[...new Set(rows)].join('\n'):'';
  }
  function qrProgressionSelection(index){
    const state=groupState(index),values=state.values;
    if(!values.length)return null;
    const selected=[];
    const setCount=Math.max(1,Number(p&&p.ex&&p.ex[index]&&p.ex[index].sets)||1);
    for(let setNo=1;setNo<=setCount;setNo++){
      const id=selectedId(index,setNo),item=variantById(values,id);
      selected.push({s:setNo,i:id,n:item&&item.name||''});
    }
    return {k:'kgg015',g:state.gid,s:selected};
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
    const finalizedKey=planId()+'|'+String(day);if(Number(history.finalized[finalizedKey]||0)===1)return;
    ensureDay();if(String(history.current.planId||'')!==planId()||Number(history.current.day)!==Number(day))return;
    p.ex.forEach((ex,index)=>{const state=groupState(index),winner=dominantFor(index,true);if(winner)state.group.dominantId=winner.id});
    history.finalized[finalizedKey]=1;saveHistory();applyDominantMedia();
  }
  function wrapShowQr(){
    if(originalShowQr||typeof showQr!=='function')return;
    originalShowQr=showQr;window.showQr=function(finalize){const day=currentDay();if(finalize)preferActiveMedia=false;if(finalize)finalizeDominance(day);const originalRows=window.rows;if(typeof originalRows==='function'){window.rows=function(qrDay){return originalRows(qrDay).map((row,index)=>{const selection=qrProgressionSelection(index);if(selection)row.push(selection);return row})}}let result;try{result=originalShowQr.apply(this,arguments)}finally{if(originalRows)window.rows=originalRows}setTimeout(()=>{applyDominantMedia(false);applyDisplayNames();renderGalleries()},0);return result};
  }
  function wrapOpenPad(){
    if(originalOpenPad||typeof openPad!=='function')return;
    originalOpenPad=openPad;window.openPad=function(input,meta){if(meta&&meta.ei!==undefined&&meta.s!==undefined){activeSet={index:Number(meta.ei),setNo:Number(meta.s)};preferActiveMedia=true;applyDominantMedia(true);refreshMainProgression(activeSet.index)}return originalOpenPad.apply(this,arguments)};
  }
  function wrapRender(){
    if(originalRender||typeof render!=='function')return;
    originalRender=render;window.render=function(){syncRawVariants();applyDominantMedia(false);const result=originalRender.apply(this,arguments);[0,70,260].forEach(delay=>setTimeout(()=>{renderGalleries()},delay));return result};
  }
  function init(){
    syncRawVariants();applyDominantMedia(preferActiveMedia);wrapRender();wrapPut();wrapText();wrapShowQr();wrapOpenPad();css();renderGalleries();refreshMainProgression();
    [250,800,1600].forEach(delay=>setTimeout(()=>{syncRawVariants();applyDominantMedia(preferActiveMedia);wrapRender();wrapPut();wrapText();wrapShowQr();wrapOpenPad();renderGalleries();refreshMainProgression()},delay));
  }
  function testDominant(values,records){const counts={};Object.values(records||{}).forEach(record=>{const id=String(record&&record.id||record);if(values.some(item=>String(item.id)===id))counts[id]=(counts[id]||0)+1});let winner=null;values.forEach(item=>{const count=counts[item.id]||0;if(!winner||count>winner.count||(count===winner.count&&item.order>winner.item.order))winner={item,count}});return winner&&winner.item||null}
  function testNote(previous,current,name){return previous&&String(previous)!==String(current)?String(name||'Übung')+': '+previous+' → '+current:''}
  if(window.__KGG_TEST__)window.__kggTicket015PatientTest={version:VERSION,normalizeVariant:variantFrom,dominant:testDominant,note:testNote,qrProgressionSelection};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
