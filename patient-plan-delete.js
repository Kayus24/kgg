(()=>{
  const VERSION='plan-delete-3-red-x-rename';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const CURRENT_KEY='kggCurrentPlanV1';
  const MEDIA_DB='kgg_patient_media_v1';
  const MEDIA_STORE='images';
  const PANEL_ID='kggPlanDeletePanel';
  const BACKDROP_ID='kggPlanDeleteBackdrop';
  if(window.__kggPlanDelete===VERSION)return;
  window.__kggPlanDelete=VERSION;
  const $=id=>document.getElementById(id);
  const isEn=()=>localStorage.getItem('kggPatientLang')==='en';
  const t=(de,en)=>isEn()?en:de;
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const clone=v=>{try{return JSON.parse(JSON.stringify(v))}catch(e){return v}};
  const safe=fn=>{try{return fn()}catch(e){return null}};

  function readState(){try{return JSON.parse(localStorage.getItem(MULTI_KEY)||'null')}catch(e){return null}}
  function writeState(state){state.updatedAt=new Date().toISOString();localStorage.setItem(MULTI_KEY,JSON.stringify(state))}
  function persistCurrent(raw){localStorage.setItem(CURRENT_KEY,JSON.stringify({plan:raw,importedAt:new Date().toISOString()}))}
  function planTitle(raw,index){return String(raw&&raw.t||raw&&raw.title||t('Plan ','Plan ')+(index+1))}
  function runtimeFromRaw(raw){return{id:raw.i||'plan',title:raw.t||'KGG Trainingsplan',version:+raw.v||1,days:+raw.d||6,extendDays:raw.extendDays!==false,stepDays:+raw.stepDays||6,ex:(raw.e||[]).map(e=>({n:e[0]||'Übung',sets:Number(e[1])||3,side:e[2]||'LR',u:e[3]||'kg',m:e[4]||'Wdh',sl:e[5]||'',sm:e[6]||'',media:e[7]||'',videoUrl:e[8]||'',videoLabel:e[9]||'Video öffnen',painMode:e[10]||'exercise'}))}}
  function planHash(raw){
    const ex=(raw.e||[]).map(e=>[e[0]||'Übung',Number(e[1])||3,e[2]||'LR',e[3]||'kg',e[4]||'Wdh']);
    const text=JSON.stringify({i:raw.i||'plan',t:raw.t||'KGG Trainingsplan',e:ex});
    let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)
  }
  function planStoragePrefix(raw){return 'kgg-'+String(raw&&raw.i||'plan')+'-'+planHash(raw||{})}
  function planStorageKeys(raw){const base=planStoragePrefix(raw);return[base+'-values',base+'-done',base+'-meta']}
  function mediaIds(raw){
    const ids=new Set();
    (raw&&Array.isArray(raw.e)?raw.e:[]).forEach(ex=>{
      const media=Array.isArray(ex&&ex[7])?ex[7]:(ex&&ex[7]?[ex[7]]:[]);
      media.forEach(item=>{const id=typeof item==='string'?item:String(item&&item.id||'');if(id)ids.add(id)})
    });
    return ids
  }
  function removePlanState(source,index){
    const state=clone(source||{});state.plans=Array.isArray(state.plans)?state.plans:[];
    const idx=Number(index);
    if(state.plans.length<=1||!Number.isInteger(idx)||idx<0||idx>=state.plans.length)return{ok:false,state,removed:null,newActive:Number(state.active)||0,activeRemoved:false};
    const oldActive=Math.max(0,Math.min(Number(state.active)||0,state.plans.length-1));
    const removed=state.plans[idx];state.plans.splice(idx,1);
    let newActive=oldActive;
    if(idx===oldActive)newActive=Math.min(idx,state.plans.length-1);
    else if(idx<oldActive)newActive=oldActive-1;
    state.active=Math.max(0,newActive);
    return{ok:true,state,removed,newActive:state.active,activeRemoved:idx===oldActive}
  }
  function renamePlanState(source,index,title){
    const state=clone(source||{});state.plans=Array.isArray(state.plans)?state.plans:[];
    const idx=Number(index);const nextTitle=String(title??'').trim().replace(/\s+/g,' ');
    if(!nextTitle||nextTitle.length>80||!Number.isInteger(idx)||idx<0||idx>=state.plans.length)return{ok:false,state,oldPlan:null,newPlan:null};
    const oldPlan=clone(state.plans[idx]||{});const newPlan=clone(oldPlan)||{};newPlan.t=nextTitle;delete newPlan.title;state.plans[idx]=newPlan;
    return{ok:true,state,oldPlan,newPlan,index:idx}
  }
  function removeLocalPlanKeys(raw){planStorageKeys(raw).forEach(key=>localStorage.removeItem(key))}
  function migratePlanKeys(oldRaw,newRaw){const oldKeys=planStorageKeys(oldRaw||{}),newKeys=planStorageKeys(newRaw||{});oldKeys.forEach((oldKey,index)=>{const newKey=newKeys[index];if(oldKey===newKey)return;const value=safe(()=>localStorage.getItem(oldKey));if(value!==null&&localStorage.getItem(newKey)===null)localStorage.setItem(newKey,value);if(value!==null)localStorage.removeItem(oldKey)})}
  function deleteMediaRecords(removed,remaining){
    if(!('indexedDB'in window))return Promise.resolve();
    const keep=new Set();(remaining||[]).forEach(raw=>mediaIds(raw).forEach(id=>keep.add(id)));
    const ids=[...mediaIds(removed)].filter(id=>!keep.has(id));if(!ids.length)return Promise.resolve();
    return new Promise(resolve=>{const req=indexedDB.open(MEDIA_DB,1);req.onerror=()=>resolve();req.onupgradeneeded=()=>resolve();req.onsuccess=()=>{const db=req.result;try{const tx=db.transaction(MEDIA_STORE,'readwrite');ids.forEach(id=>tx.objectStore(MEDIA_STORE).delete(id));tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>{db.close();resolve()}}catch(e){db.close();resolve()}}})
  }
  function loadActive(raw){
    window.p=runtimeFromRaw(raw);persistCurrent(raw);
    safe(()=>{window.v=read(sk(),'{}')});safe(()=>{const flow=window.KGGPatientDayFlow;window.done=flow&&typeof flow.normalizeDone==='function'?flow.normalizeDone(read(dk(),'[]')):read(dk(),'[]').map(Number).filter(n=>n>=1&&(p.extendDays!==false||n<=p.days))});
    safe(()=>typeof restoreDay==='function'&&restoreDay());safe(()=>save());safe(()=>render());
    [80,300,900].forEach(delay=>setTimeout(()=>{safe(()=>window.KGGPatientMediaRetryCache&&window.KGGPatientMediaRetryCache.prefetch&&window.KGGPatientMediaRetryCache.prefetch());safe(()=>window.KGGPatientMediaRetryCache&&window.KGGPatientMediaRetryCache.render&&window.KGGPatientMediaRetryCache.render())},delay))
  }
  async function deletePlan(index,confirmFn){
    const api=window.KGGPatientMultiPlan;const state=api&&api.ensureState?api.ensureState():readState();
    if(!state||!Array.isArray(state.plans)||state.plans.length<=1)return false;
    const idx=Number(index);const raw=state.plans[idx];if(!raw)return false;
    const ask=confirmFn||window.confirm;if(!ask(t('Plan „','Delete plan “')+planTitle(raw,idx)+t('“ wirklich löschen?','” permanently?')))return false;
    if(Number(state.active)===idx&&api&&api.saveCurrentSlot)api.saveCurrentSlot();
    const fresh=api&&api.ensureState?api.ensureState():readState();const result=removePlanState(fresh,idx);if(!result.ok)return false;
    writeState(result.state);removeLocalPlanKeys(result.removed);await deleteMediaRecords(result.removed,result.state.plans);
    const next=result.state.plans[result.newActive];if(next)loadActive(next);
    closePanel();safe(()=>setStatus(t('Plan gelöscht. Andere Pläne bleiben erhalten.','Plan deleted. Other plans were kept.'),'ok'));return true
  }
  async function renamePlan(index,promptFn){
    const api=window.KGGPatientMultiPlan;const state=api&&api.ensureState?api.ensureState():readState();if(!state||!Array.isArray(state.plans))return false;
    const idx=Number(index);const raw=state.plans[idx];if(!raw)return false;const ask=promptFn||window.prompt;const answer=ask(t('Neuer Name für den Plan:','New name for this plan:'),planTitle(raw,idx));if(answer===null)return false;
    const freshTitle=String(answer).trim().replace(/\s+/g,' ');if(!freshTitle||freshTitle.length>80){safe(()=>window.alert(t('Bitte einen Namen mit 1 bis 80 Zeichen eingeben.','Enter a name with 1 to 80 characters.')));return false;}
    if(Number(state.active)===idx&&api&&api.saveCurrentSlot)api.saveCurrentSlot();const fresh=api&&api.ensureState?api.ensureState():readState();const result=renamePlanState(fresh,idx,freshTitle);if(!result.ok)return false;
    writeState(result.state);migratePlanKeys(result.oldPlan,result.newPlan);if(Number(result.state.active)===idx)loadActive(result.newPlan);closePanel();safe(()=>setStatus(t('Planname gespeichert.','Plan name saved.'),'ok'));return true
  }
  function ensureDom(){
    if(!$('kggPlanDeleteStyle')){const s=document.createElement('style');s.id='kggPlanDeleteStyle';s.textContent='#'+BACKDROP_ID+'{position:fixed;inset:0;z-index:2760;background:#0f172a33}#'+BACKDROP_ID+'[hidden],#'+PANEL_ID+'[hidden]{display:none!important}#'+PANEL_ID+'{position:fixed;z-index:2761;left:12px;right:12px;top:76px;max-width:520px;max-height:calc(100dvh - 104px);overflow:auto;margin:auto;background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:12px;box-shadow:0 22px 70px #0f172a38}.kggPlanManageHead{display:flex;align-items:center;justify-content:space-between;gap:8px}.kggPlanManageHead h3{margin:0;font-size:18px}.kggPlanManageClose{width:38px;height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;font-size:22px}.kggPlanManageList{display:grid;gap:8px;margin-top:10px}.kggPlanManageCard{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;border:1px solid #dbe3ef;border-radius:15px;padding:10px}.kggPlanManageCard b{font-size:15px}.kggPlanManageMeta{font-size:12px;color:#64748b;margin-top:2px}.kggPlanManageActions{display:flex;align-items:center;gap:6px}.kggPlanRenameBtn,.kggPlanDeleteBtn{width:40px;height:40px;min-height:40px;border-radius:999px;padding:0;font-weight:900}.kggPlanRenameBtn{border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;font-size:19px}.kggPlanRenameBtn:active{transform:scale(.94);background:#dbeafe}.kggPlanRenameBtn:focus-visible{outline:3px solid #93c5fd;outline-offset:2px}.kggPlanDeleteBtn{border:1px solid #fecaca;background:#fff1f2;color:#b91c1c;font-size:25px;line-height:1}.kggPlanDeleteBtn:active{transform:scale(.94);background:#ffe4e6}.kggPlanDeleteBtn:focus-visible{outline:3px solid #fda4af;outline-offset:2px}';document.head.appendChild(s)}
    if(!$(BACKDROP_ID)){const b=document.createElement('div');b.id=BACKDROP_ID;b.hidden=true;b.onclick=closePanel;document.body.appendChild(b)}
    if(!$(PANEL_ID)){const p=document.createElement('section');p.id=PANEL_ID;p.hidden=true;document.body.appendChild(p)}
  }
  function closePanel(){const b=$(BACKDROP_ID),p=$(PANEL_ID);if(b)b.hidden=true;if(p)p.hidden=true}
  function openPanel(){ensureDom();renderPanel();$(BACKDROP_ID).hidden=false;$(PANEL_ID).hidden=false}
  function renderPanel(){
    const panel=$(PANEL_ID);if(!panel)return;const state=window.KGGPatientMultiPlan&&window.KGGPatientMultiPlan.ensureState?window.KGGPatientMultiPlan.ensureState():readState();const plans=state&&Array.isArray(state.plans)?state.plans:[];
    panel.innerHTML='<div class="kggPlanManageHead"><h3>'+t('Übungspläne verwalten','Manage exercise plans')+'</h3><button class="kggPlanManageClose" type="button">×</button></div><div class="kggPlanManageList">'+plans.map((raw,index)=>'<div class="kggPlanManageCard"><div><b>'+esc(planTitle(raw,index))+'</b><div class="kggPlanManageMeta">'+(Number(state.active)===index?t('Aktiver Plan','Active plan'):t('Gespeicherter Plan','Saved plan'))+'</div></div><div class="kggPlanManageActions"><button type="button" class="kggPlanRenameBtn" data-index="'+index+'" aria-label="'+esc(t('Plan umbenennen','Rename plan'))+'" title="'+esc(t('Plan umbenennen','Rename plan'))+'">✎</button>'+(plans.length>1?'<button type="button" class="kggPlanDeleteBtn" data-index="'+index+'" aria-label="'+esc(t('Plan löschen','Delete plan'))+'" title="'+esc(t('Plan löschen','Delete plan'))+'">×</button>':'')+'</div></div>').join('')+'</div>';
    panel.querySelector('.kggPlanManageClose').onclick=closePanel;panel.querySelectorAll('.kggPlanRenameBtn').forEach(btn=>btn.onclick=async()=>{if(await renamePlan(Number(btn.dataset.index)))renderPanel()});panel.querySelectorAll('.kggPlanDeleteBtn').forEach(btn=>btn.onclick=async()=>{if(await deletePlan(Number(btn.dataset.index)))renderPanel()})
  }
  function ensureButton(){
    const box=$('kggActionBubbles');if(!box)return;if($('kggBubblePlans'))return;
    const button=document.createElement('button');button.type='button';button.id='kggBubblePlans';button.className='kggBubble';button.textContent='🗂 '+t('Pläne','Plans');button.onclick=e=>{e.preventDefault();e.stopPropagation();const fab=$('kggActionFab');box.hidden=true;if(fab)fab.classList.remove('open');openPanel()};box.appendChild(button)
  }
  function init(){ensureDom();ensureButton();setInterval(ensureButton,500)}
  if(window.__KGG_TEST__)window.__kggPlanDeleteTest={removePlanState,renamePlanState,migratePlanKeys,planStoragePrefix,planStorageKeys,mediaIds};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
