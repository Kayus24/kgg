(()=>{
  const VERSION='plan-delete-v2-stable-plan-id';
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
  function stableHash(value){let h=2166136261,text=String(value||'');for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)}
  function planStoragePrefix(raw){return window.KGGPatientStorageV7?window.KGGPatientStorageV7.stableBase(raw):'kgg-v7-'+stableHash(String(raw&&raw.i||''))}
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
    const byId=String(state.activePlanId||''),byIdIndex=byId?state.plans.findIndex(raw=>String(raw&&raw.i||'')===byId):-1;
    const oldActive=byIdIndex>=0?byIdIndex:Math.max(0,Math.min(Number(state.active)||0,state.plans.length-1));
    const removed=state.plans[idx];state.plans.splice(idx,1);
    let newActive=oldActive;
    if(idx===oldActive)newActive=Math.min(idx,state.plans.length-1);
    else if(idx<oldActive)newActive=oldActive-1;
    state.active=Math.max(0,newActive);
    state.activePlanId=String(state.plans[state.active]&&state.plans[state.active].i||'');
    state.version=Math.max(2,Number(state.version)||0);
    return{ok:true,state,removed,newActive:state.active,activeRemoved:idx===oldActive}
  }
  function removeLocalPlanKeys(raw){if(window.KGGPatientStorageV7){window.KGGPatientStorageV7.removePlan(raw);return}planStorageKeys(raw).forEach(key=>localStorage.removeItem(key))}
  function deleteMediaRecords(removed,remaining){
    if(!('indexedDB'in window))return Promise.resolve();
    const keep=new Set();(remaining||[]).forEach(raw=>mediaIds(raw).forEach(id=>keep.add(id)));
    const ids=[...mediaIds(removed)].filter(id=>!keep.has(id));if(!ids.length)return Promise.resolve();
    return new Promise(resolve=>{const req=indexedDB.open(MEDIA_DB,1);req.onerror=()=>resolve();req.onupgradeneeded=()=>resolve();req.onsuccess=()=>{const db=req.result;try{const tx=db.transaction(MEDIA_STORE,'readwrite');ids.forEach(id=>tx.objectStore(MEDIA_STORE).delete(id));tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>{db.close();resolve()}}catch(e){db.close();resolve()}}})
  }
  function loadActive(raw){
    p=runtimeFromRaw(raw);persistCurrent(raw);
    const state=safe(()=>window.KGGPatientStorageV7&&window.KGGPatientStorageV7.load(raw,p));
    if(state){v=state.values;done=state.done.map(Number).filter(n=>n>=1&&n<=p.days)}
    else{safe(()=>{v=read(sk(),'{}')});safe(()=>{done=read(dk(),'[]').map(Number).filter(n=>n>=1&&n<=p.days)})}
    safe(()=>save());safe(()=>render());
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
  function ensureDom(){
    if(!$('kggPlanDeleteStyle')){const s=document.createElement('style');s.id='kggPlanDeleteStyle';s.textContent='#'+BACKDROP_ID+'{position:fixed;inset:0;z-index:2760;background:#0f172a33}#'+BACKDROP_ID+'[hidden],#'+PANEL_ID+'[hidden]{display:none!important}#'+PANEL_ID+'{position:fixed;z-index:2761;left:12px;right:12px;top:76px;max-width:520px;max-height:calc(100dvh - 104px);overflow:auto;margin:auto;background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:12px;box-shadow:0 22px 70px #0f172a38}.kggPlanManageHead{display:flex;align-items:center;justify-content:space-between;gap:8px}.kggPlanManageHead h3{margin:0;font-size:18px}.kggPlanManageClose{width:38px;height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;font-size:22px}.kggPlanManageList{display:grid;gap:8px;margin-top:10px}.kggPlanManageCard{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;border:1px solid #dbe3ef;border-radius:15px;padding:10px}.kggPlanManageCard b{font-size:15px}.kggPlanManageMeta{font-size:12px;color:#64748b;margin-top:2px}.kggPlanDeleteBtn{min-height:40px;border-radius:12px;border:1px solid #fecaca;background:#fff1f2;color:#b91c1c;padding:7px 10px;font-weight:900}.kggPlanDeleteBtn:disabled{opacity:.45}';document.head.appendChild(s)}
    if(!$(BACKDROP_ID)){const b=document.createElement('div');b.id=BACKDROP_ID;b.hidden=true;b.onclick=closePanel;document.body.appendChild(b)}
    if(!$(PANEL_ID)){const p=document.createElement('section');p.id=PANEL_ID;p.hidden=true;document.body.appendChild(p)}
  }
  function closePanel(){const b=$(BACKDROP_ID),p=$(PANEL_ID);if(b)b.hidden=true;if(p)p.hidden=true}
  function openPanel(){ensureDom();renderPanel();$(BACKDROP_ID).hidden=false;$(PANEL_ID).hidden=false}
  function renderPanel(){
    const panel=$(PANEL_ID);if(!panel)return;const state=window.KGGPatientMultiPlan&&window.KGGPatientMultiPlan.ensureState?window.KGGPatientMultiPlan.ensureState():readState();const plans=state&&Array.isArray(state.plans)?state.plans:[];
    panel.innerHTML='<div class="kggPlanManageHead"><h3>'+t('Übungspläne verwalten','Manage exercise plans')+'</h3><button class="kggPlanManageClose" type="button">×</button></div><div class="kggPlanManageList">'+plans.map((raw,index)=>'<div class="kggPlanManageCard"><div><b>'+esc(planTitle(raw,index))+'</b><div class="kggPlanManageMeta">'+(Number(state.active)===index?t('Aktiver Plan','Active plan'):t('Gespeicherter Plan','Saved plan'))+'</div></div><button type="button" class="kggPlanDeleteBtn" data-index="'+index+'" '+(plans.length<=1?'disabled':'')+'>'+t('Löschen','Delete')+'</button></div>').join('')+'</div>';
    panel.querySelector('.kggPlanManageClose').onclick=closePanel;panel.querySelectorAll('.kggPlanDeleteBtn').forEach(btn=>btn.onclick=async()=>{if(await deletePlan(Number(btn.dataset.index)))renderPanel()})
  }
  function ensureButton(){
    const box=$('kggActionBubbles');if(!box)return;if($('kggBubblePlans'))return;
    const button=document.createElement('button');button.type='button';button.id='kggBubblePlans';button.className='kggBubble';button.textContent='🗂 '+t('Pläne','Plans');button.onclick=e=>{e.preventDefault();e.stopPropagation();const fab=$('kggActionFab');box.hidden=true;if(fab)fab.classList.remove('open');openPanel()};box.appendChild(button)
  }
  function init(){ensureDom();ensureButton();setInterval(ensureButton,500)}
  if(window.__KGG_TEST__)window.__kggPlanDeleteTest={removePlanState,removeLocalPlanKeys,planStoragePrefix,planStorageKeys,mediaIds};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
