# KGG Patient Source Chunk 028

- Source file: `patient-set-summary-groups.js`
- Characters: 24001-35444
- Full source SHA-256: `1f3645b629eef7f15921f77d131b4c1927e2f2419f621b5c67e13a01075d3c75`

```
form='translate3d(calc(-33.333333% + '+dx+'px),0,0)'};
    pager.onpointerup=event=>finish(event);pager.onpointercancel=event=>finish(event,true);pager.onlostpointercapture=()=>{if(startX!==null){startX=null;track.classList.remove('is-dragging');track.style.transform='translate3d(-33.333333%,0,0)'}};
  }
  function renderMainProgressionControls(index=activeSet.index,setNo=activeSet.setNo){
    const values=valuesForExercise(index);if(!values.length)return;
    const box=mainMediaBox(index),card=box&&box.closest('.ex'),mediaList=box&&box.closest('.kggMediaList');if(!box||!card||!mediaList)return;
    mediaList.classList.add('kgg015MainProgressionHost');mediaList.querySelectorAll('.kgg015MainPager').forEach(node=>node.remove());
    const id=selectedId(index,setNo),at=Math.max(0,values.findIndex(item=>String(item.id)===String(id)));
    const previous=at>0?values[at-1]:null,current=values[at]||values[0],next=at<values.length-1?values[at+1]:null,pager=document.createElement('div');
    pager.className='kgg015MainPager';
    const prevTarget=previous?'kgg015-main-'+index+'-'+setNo+'-'+previous.id:'',currentTarget='kgg015-main-'+index+'-'+setNo+'-'+current.id,nextTarget=next?'kgg015-main-'+index+'-'+setNo+'-'+next.id:'';
    pager.innerHTML='<div class="kgg015MainPagerTrack">'+pagerSlide(previous,prevTarget,index,setNo,at-1,false)+pagerSlide(current,currentTarget,index,setNo,at,true)+pagerSlide(next,nextTarget,index,setNo,at+1,false)+'</div><div class="kgg015MainProgressionControls"><button type="button" class="kgg015MainProgressionControl" data-kgg015-main-prev aria-label="Leichtere Progressionsstufe" '+(at===0?'disabled':'')+'><i class="kgg015MainProgressionTriangle prev" aria-hidden="true"></i></button><span class="kgg015MainProgressionStage" aria-live="polite">Stufe '+(at+1)+' · '+esc(current.name)+'</span><button type="button" class="kgg015MainProgressionControl" data-kgg015-main-next aria-label="Schwerere Progressionsstufe" '+(at===values.length-1?'disabled':'')+'><i class="kgg015MainProgressionTriangle next" aria-hidden="true"></i></button></div>';
    mediaList.appendChild(pager);pager.querySelector('[data-kgg015-main-prev]').onclick=()=>shiftVariant(index,setNo,-1);pager.querySelector('[data-kgg015-main-next]').onclick=()=>shiftVariant(index,setNo,1);bindMainPager(pager,index,setNo,values,at);mainPagerThumbs(card,index,setNo,values,at);
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
    originalRender=render;window.render=function(){syncRawVariants();applyDominantMedia(preferActiveMedia);const result=originalRender.apply(this,arguments);[0,70,260].forEach(delay=>setTimeout(()=>{renderGalleries()},delay));return result};
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
```
