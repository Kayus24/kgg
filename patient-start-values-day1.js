(()=>{
  const VERSION='start-values-day1-v1';
  const MARK_PREFIX='kggStartValuesDay1AppliedV1:';
  let busy=false;
  const safe=f=>{try{return f()}catch(e){return null}};
  const txt=x=>String(x??'').trim();
  const hasValue=x=>txt(x)!=='';
  const isEmptyValue=x=>x===undefined||x===null||txt(x)==='';
  const hash=s=>{let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)};
  function ready(){return typeof p!=='undefined'&&p&&Array.isArray(p.ex)&&typeof v!=='undefined'&&v&&Array.isArray(done)&&typeof k==='function'&&typeof save==='function'}
  function signature(){return hash(JSON.stringify({id:p.id||'plan',title:p.title||'',days:p.days||0,e:p.ex.map(e=>[e.n,e.sets,e.side,e.u,e.m,e.sl||'',e.sm||''])}))}
  function markKey(){return MARK_PREFIX+(p.id||'plan')+':'+signature()}
  function startValuePairs(e){const out=[];if(hasValue(e.sl)&&hasValue(e.u))out.push(['a',txt(e.sl)]);if(hasValue(e.sm)&&hasValue(e.m))out.push(['b',txt(e.sm)]);return out}
  function hasAnyStartValues(){return p.ex.some(e=>startValuePairs(e).length>0)}
  function hasPatientProgress(){if(done&&done.length)return true;return Object.keys(v||{}).some(key=>/^[0-9]+\|/.test(key)&&hasValue(v[key]))}
  function sidesFor(e){return e.side==='LR'?['L','R']:['B']}
  function applyStartValues(){
    if(busy||!ready())return false;
    busy=true;
    try{
      if(!hasAnyStartValues())return false;
      const marker=markKey();
      if(localStorage.getItem(marker))return false;
      if(hasPatientProgress()){localStorage.setItem(marker,'skipped-existing-progress');return false}
      let wrote=0;
      (p.ex||[]).forEach((e,ei)=>{
        const sets=Number(e.sets)||3,pairs=startValuePairs(e),sides=sidesFor(e);
        if(!pairs.length)return;
        for(let s=1;s<=sets;s++)sides.forEach(side=>pairs.forEach(([field,value])=>{
          const key=k(ei,s,side,field,1);
          if(isEmptyValue(v[key])){v[key]=value;wrote++}
        }))
      });
      if(!wrote){localStorage.setItem(marker,'no-empty-targets');return false}
      if(!done.includes(1))done.push(1);
      if(Number(p.days||0)>=2)d=2;else d=1;
      save();
      localStorage.setItem(marker,new Date().toISOString());
      safe(()=>setStatus('Startwerte aus der Therapie wurden als Tag 1 gespeichert.','ok'));
      safe(()=>render());
      return true;
    }finally{busy=false}
  }
  function patchRender(){if(window.__kggStartValuesDay1RenderPatch||typeof render!=='function')return;window.__kggStartValuesDay1RenderPatch=1;const old=render;render=function(){const r=old.apply(this,arguments);setTimeout(applyStartValues,0);return r}}
  function init(){window.__kggPatientStartValuesDay1=VERSION;patchRender();setTimeout(applyStartValues,0);setTimeout(applyStartValues,300);setTimeout(applyStartValues,1200)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();