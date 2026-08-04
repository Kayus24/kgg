(()=>{
  const VERSION='plan-replace-active-slot-v1';
  if(window.__kggPlanReplaceSlotFix===VERSION)return;
  window.__kggPlanReplaceSlotFix=VERSION;

  const MULTI_KEY='kggPatientMultiPlansV1';
  const nativeSetItem=Storage.prototype.setItem;

  function parse(value){
    try{return JSON.parse(String(value||''))}catch(e){return null}
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

  Storage.prototype.setItem=function(key,value){
    if(this===window.localStorage&&String(key)===MULTI_KEY){
      const previous=parse(nativeSetItem===Storage.prototype.setItem?null:this.getItem(MULTI_KEY));
      const incoming=parse(value);
      if(incoming){
        const normalized=normalizeReplacement(previous,incoming);
        return nativeSetItem.call(this,key,JSON.stringify(normalized));
      }
    }
    return nativeSetItem.call(this,key,value);
  };
})();
