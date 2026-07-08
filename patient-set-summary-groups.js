(()=>{
  const VERSION='set-summary-groups-v1';
  if(window.__kggSetSummaryGroups===VERSION)return;
  window.__kggSetSummaryGroups=VERSION;

  function normalizeValue(value){return String(value||'').replace(/\s+/g,' ').trim().toLowerCase()}
  function setLine(line){return String(line||'').match(/^(\s*)(Satz|Set)\s*(\d+)\s*:\s*(.*?)\s*$/i)}
  function labelText(label,start,end,value,indent){const head=start===end?`${label} ${start}:`:`${label} ${start}–${end}:`;return `${indent||''}${head} ${String(value||'').trim()}`.trimEnd()}
  function flushGroup(out,group){
    if(!group.length)return;
    let start=group[0],prev=group[0],same=[group[0]];
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
  function apply(){
    const el=document.getElementById('sum');
    if(!el)return;
    const before=el.textContent||'';
    const after=compressText(before);
    if(after!==before)el.textContent=after;
  }
  function patchShowQr(){
    if(window.__kggSetSummaryGroupsPatched||typeof showQr!=='function')return;
    window.__kggSetSummaryGroupsPatched=1;
    const old=showQr;
    window.showQr=function(){const r=old.apply(this,arguments);setTimeout(apply,0);setTimeout(apply,80);setTimeout(apply,240);return r};
  }
  function init(){patchShowQr();setTimeout(patchShowQr,300);setTimeout(patchShowQr,1000);setTimeout(apply,1200)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
