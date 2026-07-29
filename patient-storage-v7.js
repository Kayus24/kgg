(()=>{
  'use strict';
  const VERSION='patient-storage-v7-stable-plan-id';
  const CURRENT_KEY='kggCurrentPlanV1';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const V7_PREFIX='kgg-v7-';
  if(window.KGGPatientStorageV7&&window.KGGPatientStorageV7.version===VERSION)return;

  const clone=value=>{try{return JSON.parse(JSON.stringify(value))}catch(e){return value&&typeof value==='object'?{...value}:value}};
  const readJson=(key,fallback)=>{try{const value=localStorage.getItem(key);return value===null?clone(fallback):JSON.parse(value)}catch(e){return clone(fallback)}};
  const writeJson=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
  const cleanId=value=>String(value||'').trim();
  const isWeakId=value=>!cleanId(value)||cleanId(value).toLowerCase()==='plan';
  const uuid=()=>{
    if(globalThis.crypto&&typeof globalThis.crypto.randomUUID==='function')return globalThis.crypto.randomUUID();
    const bytes=new Uint8Array(16);
    globalThis.crypto.getRandomValues(bytes);
    bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
    const hex=[...bytes].map(value=>value.toString(16).padStart(2,'0')).join('');
    return`${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
  };
  const hashText=value=>{
    const text=String(value),h0=2166136261;
    let h=h0;
    for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)}
    return(h>>>0).toString(36);
  };
  const stableBase=value=>V7_PREFIX+hashText(typeof value==='object'?cleanId(value&&value.i):cleanId(value));
  const storageKeys=value=>{
    const base=stableBase(value);
    return{base,values:base+'-values',done:base+'-done',meta:base+'-meta',previous:base+'-previous-raw'};
  };
  const normName=value=>String(value||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9äöüß]+/g,' ').replace(/\s+/g,' ').trim();
  const normSide=value=>{
    const raw=String(value||''),normal=normName(raw);
    return raw==='LR'||normal==='lr'||normal.includes('links rechts')||normal.includes('left right')?'LR':'B';
  };
  const normUnit=value=>{
    const normal=normName(value).replace(/\s+/g,'');
    if(!normal||normal==='keine'||normal==='none'||normal==='-')return'';
    if(['wdh','wiederholung','wiederholungen','rep','reps'].includes(normal))return'reps';
    if(['s','sek','sekunde','sekunden','sec','secs','second','seconds'].includes(normal))return'sec';
    if(['min','minute','minuten','mins','minutes'].includes(normal))return'min';
    if(['kg','kilogramm','kilogram','kilograms'].includes(normal))return'kg';
    if(['stufe','level'].includes(normal))return'level';
    if(['w','watt'].includes(normal))return'watt';
    return normal;
  };
  function exerciseRefs(raw){
    const counts=new Map();
    return(Array.isArray(raw&&raw.e)?raw.e:[]).map(exercise=>{
      const item=Array.isArray(exercise)?exercise:[];
      const base=[normName(item[0]),normSide(item[2]),normUnit(item[3]),normUnit(item[4])].join('|');
      const occurrence=(counts.get(base)||0)+1;counts.set(base,occurrence);
      return{id:base+'|'+occurrence,name:normName(item[0]),side:normSide(item[2]),unitA:normUnit(item[3]),unitB:normUnit(item[4]),occurrence};
    });
  }
  function rawFromRuntime(runtime,baseRaw){
    const raw=clone(baseRaw&&typeof baseRaw==='object'?baseRaw:{});
    raw.i=cleanId(runtime&&runtime.id)||cleanId(raw.i);
    raw.t=runtime&&runtime.title||raw.t||'KGG Trainingsplan';
    raw.v=Number(runtime&&runtime.version)||Number(raw.v)||1;
    raw.d=Number(runtime&&runtime.days)||Number(raw.d)||6;
    raw.extendDays=runtime?runtime.extendDays!==false:raw.extendDays!==false;
    raw.stepDays=Number(runtime&&runtime.stepDays)||Number(raw.stepDays)||6;
    const old=Array.isArray(raw.e)?raw.e:[];
    raw.e=Array.isArray(runtime&&runtime.ex)?runtime.ex.map((exercise,index)=>{
      const item=Array.isArray(old[index])?old[index].slice():[];
      item[0]=exercise.n||'Übung';item[1]=Number(exercise.sets)||3;item[2]=exercise.side||'LR';
      item[3]=exercise.u||'';item[4]=exercise.m||'';
      if(item.length<6)item[5]=exercise.sl||'';if(item.length<7)item[6]=exercise.sm||'';
      return item;
    }):old;
    return raw;
  }
  function legacyHash(raw){
    const exercises=(Array.isArray(raw&&raw.e)?raw.e:[]).map(item=>{
      const exercise=Array.isArray(item)?item:[];
      return[exercise[0]||'Übung',Number(exercise[1])||3,exercise[2]||'LR',exercise[3]||'kg',exercise[4]||'Wdh'];
    });
    return hashText(JSON.stringify({i:cleanId(raw&&raw.i)||'plan',t:raw&&raw.t||'KGG Trainingsplan',e:exercises}));
  }
  const legacyBase=raw=>'kgg-'+(cleanId(raw&&raw.i)||'plan')+'-'+legacyHash(raw||{});
  const legacyKeys=raw=>{
    const base=legacyBase(raw);
    return{base,values:base+'-values',done:base+'-done',meta:base+'-meta'};
  };
  const sameRaw=(left,right)=>JSON.stringify(left||null)===JSON.stringify(right||null);
  function prepareRaw(input){
    const raw=clone(input&&typeof input==='object'?input:{});
    if(isWeakId(raw.i))raw.i=uuid();
    const keys=storageKeys(raw);
    const meta=readJson(keys.meta,null);
    if(meta&&meta.planId&&meta.planId!==cleanId(raw.i))raw.i=uuid();
    return raw;
  }
  function rememberPrevious(previous,incoming){
    if(!previous||!incoming)return false;
    const oldId=cleanId(previous.i),nextId=cleanId(incoming.i);
    if(!oldId||oldId!==nextId||sameRaw(previous,incoming))return false;
    writeJson(storageKeys(incoming).previous,previous);
    return true;
  }
  function knownRaws(planId,current,previous){
    const raws=[];
    const add=raw=>{
      if(raw&&cleanId(raw.i)===planId&&!raws.some(existing=>sameRaw(existing,raw)))raws.push(raw);
    };
    add(previous);add(current);
    const saved=readJson(CURRENT_KEY,null);add(saved&&saved.plan);
    const multi=readJson(MULTI_KEY,null);
    if(multi&&Array.isArray(multi.plans))multi.plans.forEach(add);
    return raws;
  }
  function parseValueKey(key){
    const parts=String(key).split('|');
    if(parts.length!==5)return null;
    const day=Number(parts[0]),exercise=Number(parts[1]),set=Number(parts[2]);
    if(!Number.isInteger(day)||day<1||!Number.isInteger(exercise)||exercise<0||!Number.isInteger(set)||set<0)return null;
    return{day,exercise,set,side:parts[3],field:parts[4]};
  }
  const valueKey=item=>[item.day,item.exercise,item.set,item.side,item.field].join('|');
  const orphanKey=item=>[item.ref&&item.ref.id||'',item.day,item.set,item.side,item.field,String(item.value)].join('|');
  function remapValues(values,fromRefs,toRefs,orphans){
    const targets=new Map((toRefs||[]).map((ref,index)=>[ref.id,index]));
    const next={},nextOrphans=[],seen=new Set();
    const keepOrphan=item=>{
      if(!item||!item.ref||!item.ref.id)return;
      const copy=clone(item),key=orphanKey(copy);
      if(!seen.has(key)){seen.add(key);nextOrphans.push(copy)}
    };
    Object.entries(values&&typeof values==='object'?values:{}).forEach(([key,value])=>{
      const parsed=parseValueKey(key),ref=parsed&&fromRefs&&fromRefs[parsed.exercise];
      if(!parsed||!ref){return}
      const exercise=targets.get(ref.id);
      if(exercise===undefined){keepOrphan({ref,...parsed,value});return}
      const target=valueKey({...parsed,exercise});
      if(!(target in next))next[target]=value;
    });
    (Array.isArray(orphans)?orphans:[]).forEach(item=>{
      const exercise=item&&item.ref?targets.get(item.ref.id):undefined;
      if(exercise===undefined){keepOrphan(item);return}
      const target=valueKey({...item,exercise});
      if(!(target in next))next[target]=item.value;
      else keepOrphan(item);
    });
    return{values:next,orphans:nextOrphans};
  }
  function readLegacy(base,raw){
    const values=readJson(base+'-values',null),done=readJson(base+'-done',null),meta=readJson(base+'-meta',null);
    if(values===null&&done===null&&meta===null)return null;
    return{base,raw:raw||meta&&meta.planRaw||null,values:values&&typeof values==='object'?values:{},done:Array.isArray(done)?done:[],meta:meta&&typeof meta==='object'?meta:{}};
  }
  function legacyCandidates(raw){
    const planId=cleanId(raw.i),keys=storageKeys(raw),previous=readJson(keys.previous,null),known=knownRaws(planId,raw,previous);
    const result=[],used=new Set(),add=(base,sourceRaw)=>{
      if(!base||used.has(base))return;
      used.add(base);const candidate=readLegacy(base,sourceRaw);
      if(candidate)result.push(candidate);
    };
    if(previous&&cleanId(previous.i)===planId)add(legacyBase(previous),previous);
    add(legacyBase(raw),raw);
    const pattern=new RegExp('^kgg-'+planId.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'-([a-z0-9]+)-meta$');
    const latest=[];
    for(let index=0;index<localStorage.length;index++){
      const key=localStorage.key(index),match=key&&key.match(pattern);
      if(!match)continue;
      const base=key.slice(0,-5),meta=readJson(key,{});
      latest.push({base,meta,time:Date.parse(meta&&meta.lastSavedAt||'')||0});
    }
    latest.sort((left,right)=>right.time-left.time).forEach(item=>{
      const sourceRaw=item.meta&&item.meta.planRaw||known.find(candidate=>legacyBase(candidate)===item.base)||null;
      add(item.base,sourceRaw);
    });
    return result;
  }

  let activePlanId='',activeRefs=[],activeOrphans=[],activeOpaque=[];
  function writeRecord(raw,values,done,day,extra){
    const keys=storageKeys(raw),refs=exerciseRefs(raw),completed=[...new Set((done||[]).map(Number).filter(Number.isFinite))].sort((a,b)=>a-b);
    writeJson(keys.values,values||{});
    writeJson(keys.done,completed);
    writeJson(keys.meta,{
      storageVersion:7,planId:cleanId(raw.i),planRaw:clone(raw),refs,lastSavedAt:new Date().toISOString(),
      lastOpenDay:Number(day)||1,lastCompletedDay:completed.length?Math.max(...completed):0,
      migratedFrom:extra&&extra.migratedFrom||null,orphans:clone(activeOrphans),opaqueLegacy:clone(activeOpaque)
    });
    activePlanId=cleanId(raw.i);activeRefs=refs;
    return{values:values||{},done:completed,meta:readJson(keys.meta,{})};
  }
  function load(rawInput,runtime){
    const raw=prepareRaw(rawInput),keys=storageKeys(raw),refs=exerciseRefs(raw),meta=readJson(keys.meta,null);
    let values={},done=[],day=1,migratedFrom=null;
    activeOrphans=[];activeOpaque=[];
    if(meta&&Number(meta.storageVersion)===7&&meta.planId===cleanId(raw.i)){
      const mapped=remapValues(readJson(keys.values,{}),Array.isArray(meta.refs)?meta.refs:refs,refs,meta.orphans);
      values=mapped.values;activeOrphans=mapped.orphans;activeOpaque=Array.isArray(meta.opaqueLegacy)?clone(meta.opaqueLegacy):[];
      done=readJson(keys.done,[]);day=Number(meta.lastOpenDay)||1;migratedFrom=meta.migratedFrom||null;
    }else{
      const candidate=legacyCandidates(raw)[0]||null;
      if(candidate){
        if(candidate.raw){
          const mapped=remapValues(candidate.values,exerciseRefs(candidate.raw),refs,[]);
          values=mapped.values;activeOrphans=mapped.orphans;
        }else{
          activeOpaque=[{legacyBase:candidate.base,values:clone(candidate.values)}];
        }
        done=candidate.done;day=Number(candidate.meta.lastOpenDay)||1;migratedFrom=candidate.base;
      }
    }
    activePlanId=cleanId(raw.i);activeRefs=refs;
    const result=writeRecord(raw,values,done,day,{migratedFrom});
    return{raw,runtime:runtime||null,values:result.values,done:result.done,meta:result.meta};
  }
  function save(runtime,values,done,day,baseRaw){
    const raw=prepareRaw(rawFromRuntime(runtime,baseRaw));
    const nextRefs=exerciseRefs(raw);
    let mapped={values:values&&typeof values==='object'?values:{},orphans:activeOrphans};
    if(activePlanId===cleanId(raw.i)&&activeRefs.length){
      mapped=remapValues(mapped.values,activeRefs,nextRefs,activeOrphans);
    }else{
      const keys=storageKeys(raw),meta=readJson(keys.meta,null);
      if(meta&&meta.planId===cleanId(raw.i)){
        mapped=remapValues(readJson(keys.values,{}),Array.isArray(meta.refs)?meta.refs:nextRefs,nextRefs,meta.orphans);
      }
    }
    activeOrphans=mapped.orphans;
    const result=writeRecord(raw,mapped.values,done,day,{migratedFrom:readJson(storageKeys(raw).meta,{}).migratedFrom||null});
    const old=legacyKeys(raw);
    writeJson(old.values,result.values);writeJson(old.done,result.done);
    writeJson(old.meta,{lastSavedAt:new Date().toISOString(),lastOpenDay:Number(day)||1,lastCompletedDay:result.done.length?Math.max(...result.done):0,storageVersion:6,planId:cleanId(raw.i),planRaw:clone(raw)});
    return{raw,values:result.values,done:result.done,meta:result.meta};
  }
  function removePlan(rawInput){
    const raw=rawInput&&typeof rawInput==='object'?rawInput:{i:rawInput},planId=cleanId(raw.i);
    if(!planId)return[];
    const removed=[],keys=storageKeys(raw);
    [keys.values,keys.done,keys.meta,keys.previous].forEach(key=>{if(localStorage.getItem(key)!==null){localStorage.removeItem(key);removed.push(key)}});
    const pattern=new RegExp('^kgg-'+planId.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'-([a-z0-9]+)-(values|done|meta)$');
    const legacy=[];
    for(let index=0;index<localStorage.length;index++){const key=localStorage.key(index);if(key&&pattern.test(key))legacy.push(key)}
    legacy.forEach(key=>{localStorage.removeItem(key);removed.push(key)});
    return removed;
  }
  window.KGGPatientStorageV7={
    version:VERSION,prepareRaw,rememberPrevious,load,save,removePlan,stableBase,storageKeys,
    legacyBase,legacyKeys,hash:hashText,exerciseRefs,remapValues,normName,normSide,normUnit,rawFromRuntime
  };
})();
