/* Patient-side Live-Sync UI.  It never renders pairing secrets or JSON. */
(function installPatientLiveSync(global){
  'use strict';
  if(global.__KGGPatientLiveSyncInstalled)return;
  global.__KGGPatientLiveSyncInstalled=true;
  const live=global.KGGLiveSync;
  if(!live)return;
  const $=id=>document.getElementById(id);
  const state={store:live.makeKeyStore({allowMemory:false}),pairingId:'',planRef:'',client:null,lastPlanRevision:'',sent:new Map(),timer:0};
  const mode=()=>live.config().mode;
  const text=(value,fallback)=>String(value==null||value===''?fallback||'':value);
  const statusNode=()=>$('kggLiveSyncPatientStatus');
  function setStatus(value,kind){const node=statusNode();if(!node)return;node.textContent=value;node.dataset.state=kind||'';}
  function localPlan(){try{const saved=JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null');return saved&&saved.plan&&typeof saved.plan==='object'?saved.plan:null;}catch(err){return null;}}
  function currentPlanRef(plan){return String(plan&&plan.i||'');}
  function patientExerciseShape(raw){const value=Array.isArray(raw)?raw:[];return {n:value[0]||'Übung',sets:Number(value[1])||3,side:value[2]||'LR',u:value[3]||'kg',m:value[4]||'Wdh'};}
  function exactValuesKey(plan){
    if(!plan||!plan.i)return null;
    const exercises=Array.isArray(plan.e)?plan.e.map(patientExerciseShape):[],raw=JSON.stringify({i:plan.i,t:plan.t,e:exercises.map(exercise=>[exercise.n,exercise.sets,exercise.side,exercise.u,exercise.m])});
    let hash=2166136261;for(let i=0;i<raw.length;i++){hash^=raw.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return 'kgg-'+plan.i+'-'+(hash>>>0).toString(36)+'-values';
  }
  function stableExerciseId(plan,index){
    const raw=Array.isArray(plan&&plan.e&&plan.e[index])?plan.e[index]:[],explicit=String(raw[11]||'');if(explicit)return explicit;const name=String(raw[0]||'Übung'),key=name.toLowerCase(),occurrence=Array.isArray(plan&&plan.e)?plan.e.slice(0,index).filter(item=>String(item&&item[0]||'').toLowerCase()===key).length:0;let hash=2166136261;const value=name+'|'+occurrence;for(let i=0;i<value.length;i++){hash^=value.charCodeAt(i);hash=Math.imul(hash,16777619);}return'ex_'+(hash>>>0).toString(16);
  }
  function planHashInput(plan){
    const exercises=Array.isArray(plan&&plan.e)?plan.e.map((raw,index)=>({id:stableExerciseId(plan,index),name:String(raw&&raw[0]||''),sets:Number(raw&&raw[1])||0,side:String(raw&&raw[2]||''),unit:String(raw&&raw[3]||''),measure:String(raw&&raw[4]||''),order:index})):[];
    return {title:String(plan&&plan.t||'KGG Trainingsplan'),days:Number(plan&&plan.d)||6,exercises};
  }
  async function currentPlanRevision(plan){return live.sha256Hex(live.canonicalJson(planHashInput(plan)));}
  function valueStoreForPlan(plan){
    const key=exactValuesKey(plan);if(!key)return null;
    try{const value=JSON.parse(localStorage.getItem(key)||'null');return value&&typeof value==='object'?value:null;}catch(err){return null;}
  }
  function exerciseId(plan,index){return stableExerciseId(plan,index);}
  function eventValue(value){const raw=String(value??'').trim();if(/^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(raw)){const number=Number(raw.replace(',','.'));if(Number.isFinite(number))return number;}return raw;}
  async function buildEvents(){
    const plan=localPlan(),values=valueStoreForPlan(plan);if(!plan||!values)return {events:[],revision:''};
    const revision=await currentPlanRevision(plan),events=[];
    for(const [key,value] of Object.entries(values)){
      const parts=key.split('|');if(parts.length!==5||String(value??'').trim()==='')continue;
      const [day,exercise,set,side,field]=parts;const n=Number(day),ei=Number(exercise),sn=Number(set);if(!Number.isInteger(n)||n<1||!Number.isInteger(ei)||ei<0||!Number.isInteger(sn)||sn<1)continue;
      const event={eventId:'',exerciseId:exerciseId(plan,ei),day:n,set:sn,side:String(side),metric:String(field),value:eventValue(value),recordedAt:new Date().toISOString()};
      event.eventId='evt_'+String(await live.sha256Hex(live.canonicalJson({...event,planRevision:revision}))).slice(0,48);
      events.push(event);
    }
    const painByExercise=new Map();Object.entries(values).forEach(([key,value])=>{const parts=key.split('|');if(parts.length===5&&parts[3]==='P'&&parts[4]==='pain'&&String(value??'').trim()!=='')painByExercise.set(parts[0]+'|'+parts[1],Number(value));});
    events.forEach(event=>{const pain=painByExercise.get(String(event.day)+'|'+String(plan.e.findIndex(raw=>exerciseId(plan,plan.e.indexOf(raw))===event.exerciseId)));if(Number.isInteger(pain)&&pain>=0&&pain<=10)event.pain=pain;});
    return {events:events.slice(-400),revision};
  }
  function pairingStorageMessage(){return 'Sicherer Kopplungsspeicher ist auf diesem Gerät nicht verfügbar. Live-Sync bleibt aus.';}
  async function clearActivePairing(reason){
    const hadPairing=!!state.pairingId||!!state.planRef||!!state.client,pairingId=state.pairingId,client=state.client;
    state.client=null;state.pairingId='';state.planRef='';state.sent.clear();
    try{if(client&&typeof client.close==='function')await client.close({sendClose:false,reason:reason||'plan_changed'});if(client&&typeof client.failClosed==='function')client.failClosed(reason||'plan_changed');}catch(err){try{if(client&&typeof client.failClosed==='function')client.failClosed(reason||'plan_changed');}catch(closeErr){}}
    try{if(pairingId&&state.store&&typeof state.store.remove==='function')await state.store.remove(pairingId);}catch(err){}
    if(hadPairing)setStatus('Plan gewechselt. Bitte neuen Kopplungs-QR scannen.','warn');
  }
  async function ensurePlanBinding(){
    const current=currentPlanRef(localPlan());
    if(!state.planRef||!current||state.planRef!==current){await clearActivePairing('plan_changed');return false;}
    return true;
  }
  function renderShell(){
    if(mode()==='off'||$('kggLiveSyncPatient'))return;
    const anchor=$('status')||$('plan');if(!anchor)return;
    const box=document.createElement('section');box.id='kggLiveSyncPatient';box.className='card kggLiveSyncPatient';box.innerHTML='<h2>Live-Sync</h2><p class="muted">Freiwillig: Trainingswerte werden für höchstens zwei Stunden verschlüsselt geteilt. Du kannst jederzeit beenden.</p><p class="kggLiveTestHint" id="kggLiveTestHint" hidden>TESTMODUS · Nur synthetische Daten.</p><div class="kggLivePairActions"><button class="btn2" id="kggLivePairScan" type="button">Kopplungs-QR scannen</button></div><div class="row"><input id="kggLiveSessionCode" inputmode="numeric" autocomplete="one-time-code" maxlength="8" placeholder="8-stelliger Sitzungscode" aria-label="Sitzungscode"><button class="btn" id="kggLiveJoin" type="button">Verbinden</button></div><div class="status" id="kggLiveSyncPatientStatus">Noch nicht gekoppelt.</div><button class="btn2 hide" id="kggLiveLeave" type="button">Sitzung beenden</button></section>';
    anchor.insertAdjacentElement('afterend',box);$('kggLiveTestHint').hidden=mode()!=='test';
    $('kggLivePairScan').onclick=()=>{if(global.__kggPatientStartScanTest&&typeof global.__kggPatientStartScanTest.openCameraScan==='function')global.__kggPatientStartScanTest.openCameraScan('update');else setStatus('Scanner wird noch geladen. Bitte erneut versuchen.','warn');};
    $('kggLiveJoin').onclick=joinSession;$('kggLiveLeave').onclick=()=>endSession('patient_requested');
    checkStorage();
  }
  async function checkStorage(){
    if(mode()==='off')return;
    if(!(await state.store.available())){setStatus(pairingStorageMessage(),'warn');$('kggLivePairScan').disabled=true;$('kggLiveJoin').disabled=true;return;}
    setStatus('Kopplungs-QR des Therapeuten scannen.','');
  }
  async function handleScannedText(raw){
    if(!live.isPairingQr(raw))return false;
    if(mode()==='off'){setStatus('Live-Sync ist deaktiviert. QR/Offline-Nutzung bleibt verfügbar.','warn');return true;}
    try{
      const plan=localPlan(),planRef=currentPlanRef(plan);if(!planRef)throw new Error('Kein aktiver Plan.');
      if(state.client||state.pairingId)await clearActivePairing('pairing_replaced');
      const result=await live.importPairingQr(raw,state.store,{planRef});if(currentPlanRef(localPlan())!==planRef)throw new Error('Plan wurde gewechselt.');state.pairingId=result.pairingId;state.planRef=planRef;
      setStatus('Kopplung gespeichert. Bitte den 8-stelligen Sitzungscode eingeben.','ok');return true;
    }catch(err){setStatus(err.code==='SECURE_STORAGE_UNAVAILABLE'?pairingStorageMessage():'Kopplungs-QR konnte nicht gespeichert werden.','warn');return true;}
  }
  function makeClient(){
    if(state.client&&!state.client.closed&&state.client.pairingId===state.pairingId)return state.client;
    state.client=live.createClient({role:'patient',mode:mode(),simulator:mode()==='test'&&global.KGG_LIVE_TEST_SIMULATOR===true,pairingId:state.pairingId,planRef:state.planRef,keyStore:state.store,onStatus:info=>{const connected=!!info.connected;setStatus(info.status==='ready'?'Verschlüsselt verbunden.':info.status==='connected'?'Sitzung wird sicher gekoppelt.':info.status==='offline'?'Offline-Queue aktiv.':info.status==='closed'?'Sitzung beendet.':'Live-Sync: '+text(info.status,'bereit') ,info.status==='ready'?'ok':'');$('kggLiveLeave').classList.toggle('hide',!connected&&info.status!=='offline');},onMessage:receiveMessage,onReady:async()=>{setStatus('Verschlüsselt verbunden.','ok');await sendCurrentEvents();}});
    return state.client;
  }
  async function joinSession(){
    if(!state.pairingId){setStatus('Bitte zuerst den Kopplungs-QR scannen.','warn');return;}
    if(!(await ensurePlanBinding()))return;
    const input=$('kggLiveSessionCode'),code=String(input&&input.value||'').replace(/\D/g,'');if(!/^\d{8}$/.test(code)){setStatus('Bitte den 8-stelligen Sitzungscode eingeben.','warn');return;}
    if(mode()==='test'&&!global.KGG_LIVE_TEST_SYNTHETIC_DATA){setStatus('TESTMODUS: Nur die synthetische Testschnittstelle darf Daten senden.','warn');return;}
    try{state.sent.clear();setStatus('Sitzung wird sicher verbunden.','');await makeClient().join(code);}catch(err){setStatus('Sitzung konnte nicht verbunden werden.','warn');}
  }
  async function receiveMessage(message){
    if(!message||message.type!=='plan_snapshot')return;
    if(!(await ensurePlanBinding()))return;
    state.lastPlanRevision=message.planRevision;
    const raw={i:(localPlan()&&localPlan().i)||'live-plan',t:String(message.title||'KGG Trainingsplan'),v:1,d:Number(message.days)||6,extendDays:message.extendDays!==false,stepDays:Number(message.stepDays)||6,e:(message.exercises||[]).filter(exercise=>!exercise.archived).map(exercise=>[exercise.name||'Übung',Number(exercise.sets)||3,exercise.side||'BI',exercise.unit||'kg',exercise.measure||'Wdh',exercise.startLoad||'',exercise.startMetric||'', '',exercise.videoUrl||'',exercise.videoLabel||'Video öffnen',exercise.painMode||'exercise',exercise.id])};
    try{if(!(await ensurePlanBinding()))return;if(global.KGGPatientPlanImport&&typeof global.KGGPatientPlanImport.replaceConfirmed==='function')global.KGGPatientPlanImport.replaceConfirmed(raw);setStatus('Plan aktualisiert. Trainingswerte bleiben lokal erhalten.','ok');}catch(err){setStatus('Plan konnte nicht übernommen werden.','warn');}
  }
  async function sendCurrentEvents(){
    if(!state.client||!state.client.key)return;
    if(!(await ensurePlanBinding()))return;
    try{
      if(mode()==='test'){
        if(global.KGG_LIVE_TEST_SYNTHETIC_DATA!==true)return;
        const fixtures=live.testFixtures(),pending=fixtures.trainingEvents.filter(event=>!state.sent.has(event.eventId));if(!pending.length)return;await state.client.sendTrainingEvents(pending,fixtures.planRevision);pending.forEach(event=>state.sent.set(event.eventId,true));return;
      }
      const result=await buildEvents(),pending=result.events.filter(event=>!state.sent.has(event.eventId));if(!pending.length)return;await state.client.sendTrainingEvents(pending,result.revision);pending.forEach(event=>state.sent.set(event.eventId,true));
    }catch(err){if(err.code!=='KEY_NOT_READY')setStatus('Werte bleiben lokal und werden bei Verbindung gesendet.','');}
  }
  async function poll(){if(mode()!=='off')await sendCurrentEvents();state.timer=setTimeout(poll,900);}
  async function endSession(reason){const client=state.client;if(client&&typeof client.close==='function')await client.close({reason:reason||'patient_requested'});state.client=null;state.sent.clear();}
  async function removePairingForPlan(planRef){const target=String(planRef||'');if(state.planRef===target)await clearActivePairing('plan_deleted');try{if(state.store&&typeof state.store.removeByPlanRef==='function')await state.store.removeByPlanRef(target);}catch(err){}}
  async function reset(){clearTimeout(state.timer);await clearActivePairing('app_reset');try{if(state.store&&typeof state.store.clearAll==='function')await state.store.clearAll();}catch(err){}state.sent.clear();setStatus('Live-Sync lokal zurückgesetzt.','');}
  function init(){renderShell();if(mode()!=='off'){poll();document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')sendCurrentEvents();});window.addEventListener('pagehide',()=>{if(state.client&&state.client.close)state.client.close({reason:'page_hidden'});});}}
  global.KGGPatientLiveSync={handleScannedText,init,removePairingForPlan,reset,status:()=>state.client?state.client.status():{mode:mode(),connected:false,pairingId:!!state.pairingId}};
  global.KGGLiveSync.handleScannedText=handleScannedText;
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})(typeof window!=='undefined'?window:globalThis);
