# KGG Patient Source Chunk 025

- Source file: `patient-set-summary-groups.js`
- Characters: 1-6075
- Full source SHA-256: `78061311ef7a80b2c6f2ee35733a192ddcc9a87ed88a34644da90f9207ff71a2`

```
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
```
