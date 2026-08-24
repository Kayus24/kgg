# KGG Patient Source Chunk 024

- Source file: `patient-plan-replace-slot-fix.js`
- Characters: 1-10380
- Full source SHA-256: `fc3bb7afe889cd09b340630c7796211fbfdfa742de5039c04174a19c1c6949a2`

```
(()=>{
  const VERSION='patient-plan-slots-v2-add-mode';
  if(window.__kggPlanReplaceSlotFix===VERSION)return;
  window.__kggPlanReplaceSlotFix=VERSION;

  const MULTI_KEY='kggPatientMultiPlansV1';
  const CURRENT_KEY='kggCurrentPlanV1';
  const nativeSetItem=Storage.prototype.setItem;
  const nativeParse=JSON.parse;
  let addSession=null;
  let refreshQueued=false;

  function parse(value){
    try{return nativeParse(String(value||''))}catch(e){return null}
  }
  function clone(value){
    try{return nativeParse(JSON.stringify(value))}catch(e){return value&&typeof value==='object'?{...value}:value}
  }
  function clampActive(state){
    const plans=Array.isArray(state&&state.plans)?state.plans:[];
    return Math.max(0,Math.min(Number(state&&state.active)||0,Math.max(0,plans.length-1)));
  }
  function isReplacement(plan){
    return !!(plan&&typeof plan==='object'&&('sourcePlanId' in plan)&&/-r[a-z0-9]+$/i.test(String(plan.i||'')));
  }
  function normalizeReplacement(previous,incoming){
    if(!incoming||!Array.isArray(incoming.plans)||!incoming.plans.length)return incoming;
    const appended=incoming.plans[incoming.plans.length-1];
    if(!isReplacement(appended))return incoming;

    const beforePlans=previous&&Array.isArray(previous.plans)?previous.plans:[];
    const activeBefore=clampActive(previous||incoming);
    const expectedAppend=beforePlans.length
      ? incoming.plans.length===beforePlans.length+1
      : incoming.plans.length===2;
    const pointsToAppended=Number(incoming.active)===incoming.plans.length-1;
    if(!expectedAppend||!pointsToAppended)return incoming;

    const plans=beforePlans.length?incoming.plans.slice(0,-1):[];
    if(plans.length)plans[activeBefore]=appended;
    else plans.push(appended);
    incoming.plans=plans;
    incoming.active=beforePlans.length?activeBefore:0;
    incoming.day=incoming.day&&typeof incoming.day==='object'?incoming.day:{};
    delete incoming.day[String(incoming.plans.length)];
    incoming.day[incoming.active]=1;
    return incoming;
  }
  function normalizeAddedPlan(raw,stamp){
    const plan=clone(raw&&typeof raw==='object'?raw:{});
    const sourceId=String(plan.i||'plan');
    plan.sourcePlanId=sourceId;
    plan.i=sourceId+'-p'+String(stamp||Date.now()).toString(36);
    plan.t=plan.t||'KGG Trainingsplan';
    plan.v=Number(plan.v)||1;
    plan.d=Number(plan.d)||6;
    plan.extendDays=plan.extendDays!==false;
    plan.stepDays=Number(plan.stepDays)||6;
    plan.e=Array.isArray(plan.e)?plan.e.map(clone):[];
    return plan;
  }
  function applyAddState(previous,current,added){
    const state=previous&&Array.isArray(previous.plans)?clone(previous):{version:1,plans:[],active:0,day:{}};
    state.version=Number(state.version)||1;
    state.plans=Array.isArray(state.plans)?state.plans:[];
    state.day=state.day&&typeof state.day==='object'?state.day:{};
    if(!state.plans.length&&current)state.plans.push(clone(current));
    state.plans.push(clone(added));
    state.active=state.plans.length-1;
    state.day[state.active]=1;
    state.updatedAt=new Date().toISOString();
    return state;
  }
  function existingPlanCount(){
    const state=parse(window.localStorage&&window.localStorage.getItem(MULTI_KEY));
    if(state&&Array.isArray(state.plans)&&state.plans.length)return state.plans.length;
    const current=parse(window.localStorage&&window.localStorage.getItem(CURRENT_KEY));
    if(current&&current.plan&&typeof current.plan==='object')return 1;
    try{if(typeof p!=='undefined'&&p&&Array.isArray(p.ex))return 1}catch(e){}
    return 0;
  }
  function nextPlanNumber(){return existingPlanCount()+1}
  function ordinalEn(number){
    const n=Math.max(1,Number(number)||1),mod100=n%100;
    if(mod100>=11&&mod100<=13)return n+'th';
    return n+({1:'st',2:'nd',3:'rd'}[n%10]||'th');
  }
  function isEnglish(){
    try{return window.localStorage.getItem('kggPatientLang')==='en'}catch(e){return false}
  }
  function currentRaw(){
    const saved=parse(window.localStorage&&window.localStorage.getItem(CURRENT_KEY));
    return saved&&saved.plan&&typeof saved.plan==='object'?clone(saved.plan):null;
  }
  function currentState(){
    const state=parse(window.localStorage&&window.localStorage.getItem(MULTI_KEY));
    return state&&Array.isArray(state.plans)?clone(state):{version:1,plans:[],active:0,day:{}};
  }
  function beginAdd(){
    try{
      const api=window.KGGPatientMultiPlan;
      if(api&&typeof api.saveCurrentSlot==='function')api.saveCurrentSlot();
    }catch(e){}
    addSession={
      state:currentState(),
      current:currentRaw(),
      captured:null,
      added:null,
      number:nextPlanNumber(),
      expiresAt:Date.now()+5*60*1000
    };
    refreshUi();
    return addSession.number;
  }
  function cancelAdd(){addSession=null;refreshUi()}
  function capturePlan(value){
    if(!addSession||addSession.captured||Date.now()>addSession.expiresAt)return;
    if(value&&typeof value==='object'&&Array.isArray(value.e))addSession.captured=clone(value);
  }
  function setRuntimeFromPlan(plan){
    try{
      if(typeof p!=='undefined')p={
        id:plan.i||'plan',title:plan.t||'KGG Trainingsplan',version:Number(plan.v)||1,
        days:Number(plan.d)||6,extendDays:plan.extendDays!==false,
        stepDays:Number(plan.stepDays)||6,
        ex:(plan.e||[]).map(e=>({n:e[0]||'Übung',sets:Number(e[1])||3,side:e[2]||'LR',u:e[3]||'kg',m:e[4]||'Wdh',sl:e[5]||'',sm:e[6]||'',media:e[7]||'',videoUrl:e[8]||'',videoLabel:e[9]||'Video öffnen',painMode:e[10]||'exercise'}))
      };
      if(typeof v!=='undefined')v={};
      if(typeof done!=='undefined')done=[];
      if(typeof d!=='undefined')d=1;
    }catch(e){}
  }
  function writeAddedCurrent(key){
    if(!addSession||!addSession.captured)return null;
    if(!addSession.added)addSession.added=normalizeAddedPlan(addSession.captured,Date.now());
    const wrapper={plan:addSession.added,importedAt:new Date().toISOString(),source:'add'};
    nativeSetItem.call(window.localStorage,key,JSON.stringify(wrapper));
    setRuntimeFromPlan(addSession.added);
    return addSession.added;
  }
  function finishAdd(key){
    if(!addSession||!addSession.added)return false;
    const state=applyAddState(addSession.state,addSession.current,addSession.added);
    nativeSetItem.call(window.localStorage,key,JSON.stringify(state));
    addSession=null;
    queueRefresh();
    return true;
  }
  function addPlan(raw){
    if(!raw||typeof raw!=='object'||!Array.isArray(raw.e))return false;
    if(addSession)cancelAdd();
    beginAdd();
    addSession.captured=clone(raw);
    writeAddedCurrent(CURRENT_KEY);
    const added=finishAdd(MULTI_KEY);
    if(added){
      try{save()}catch(e){}
      try{render()}catch(e){}
      try{[80,300,900].forEach(delay=>setTimeout(()=>{window.KGGPatientMediaRetryCache&&window.KGGPatientMediaRetryCache.render&&window.KGGPatientMediaRetryCache.render()},delay))}catch(e){}
    }
    return added;
  }

  JSON.parse=function(text,reviver){
    const value=nativeParse.call(JSON,text,reviver);
    capturePlan(value);
    return value;
  };

  Storage.prototype.setItem=function(key,value){
    const name=String(key);
    if(this===window.localStorage&&name===CURRENT_KEY&&addSession&&addSession.captured){
      writeAddedCurrent(key);
      return;
    }
    if(this===window.localStorage&&name===MULTI_KEY){
      if(addSession&&addSession.added&&finishAdd(key))return;
      const previous=parse(this.getItem(MULTI_KEY));
      const incoming=parse(value);
      if(incoming){
        const normalized=normalizeReplacement(previous,incoming);
        const result=nativeSetItem.call(this,key,JSON.stringify(normalized));
        queueRefresh();
        return result;
      }
    }
    const result=nativeSetItem.call(this,key,value);
    if(this===window.localStorage&&(name===CURRENT_KEY||name===MULTI_KEY))queueRefresh();
    return result;
  };

  function refreshUi(){
    if(typeof document==='undefined')return;
    const number=addSession&&addSession.number?addSession.number:nextPlanNumber();
    const en=isEnglish();
    const label=en?ordinalEn(number)+' plan':number+'. Plan';
    const hidden=document.getElementById('kggPatientAddPlanBtn');
    if(hidden&&hidden.textContent!==(label+' +'))hidden.textContent=label+' +';
    const bubble=document.getElementById('kggBubbleAdd');
    if(bubble&&bubble.textContent!==('➕ '+label))bubble.textContent='➕ '+label;
    if(addSession){
      const scanner=document.getElementById('kggLiveScan');
      if(scanner){
        scanner.setAttribute('aria-label',en?'Scan additional plan':'Zusätzlichen Plan scannen');
        const title=scanner.querySelector('.kggLiveScanHead b');
        const wanted=en?'Scan QR for '+ordinalEn(number)+' plan':'QR für '+number+'. Plan scannen';
        if(title&&title.textContent!==wanted)title.textContent=wanted;
        const status=scanner.querySelector('#kggLiveScanStatus');
        if(status&&/Plan erkannt.*(aktualisiert|Updating)/i.test(status.textContent||'')){
          status.textContent=en?'Plan detected. Adding as a separate plan …':number+'. Plan erkannt. Wird separat hinzugefügt …';
        }
      }
    }
  }
  function queueRefresh(){
    if(refreshQueued)return;
    refreshQueued=true;
    const run=()=>{refreshQueued=false;refreshUi()};
    if(typeof queueMicrotask==='function')queueMicrotask(run);else if(typeof setTimeout==='function')setTimeout(run,0);else run();
  }
  function installDomBridge(){
    if(typeof document==='undefined')return;
    document.addEventListener('click',event=>{
      const target=event&&event.target&&event.target.closest?event.target.closest('#kggPatientAddPlanBtn,#kggLiveScan .kggLiveScanClose'):null;
      if(!target)return;
      if(target.id==='kggPatientAddPlanBtn')beginAdd();
      else if(target.classList&&target.classList.contains('kggLiveScanClose'))cancelAdd();
    },true);
    if(typeof MutationObserver==='function'){
      const observer=new MutationObserver(queueRefresh);
      const root=document.documentElement||document.body;
      if(root)observer.observe(root,{childList:true,subtree:true,characterData:true});
    }
    queueRefresh();
  }

  window.KGGPatientPlanSlots={
    version:VERSION,
    normalizeReplacement,
    normalizeAddedPlan,
    applyAddState,
    nextPlanNumber,
    beginAdd,
    cancelAdd,
    addPlan
  };
  installDomBridge();
})();
```
