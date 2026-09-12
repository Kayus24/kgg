# KGG Patient Source Chunk 028

- Source file: `patient-set-summary-groups.js`
- Characters: 24001-28546
- Full source SHA-256: `5057bdc79010eeab48ecd52c9f7f76a329df1d3a7bc44a8b5662bbe8e8f1abe5`

```
rec.previousId),to=variantById(values,rec.id);if(from&&to)rows.push((originalNames[index]||'Übung')+': '+from.name+' → '+to.name)});
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
```
