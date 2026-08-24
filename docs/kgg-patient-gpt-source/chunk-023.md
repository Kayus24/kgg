# KGG Patient Source Chunk 023

- Source file: `patient-plan-link-choice.js`
- Characters: 1-9307
- Full source SHA-256: `29db160f0fbaffead0dcb2983d093a7cbf6b5742b35adeef1b917f99fbbc4fd5`

```
(()=>{
  const VERSION='v81-plan-link-choice-kgg-h3';
  const CURRENT_KEY='kggCurrentPlanV1';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const PENDING_KEY='kggPendingPlanLinkV1';
  const TTL_MS=5*60*1000;
  if(window.__kggPatientPlanLinkChoice===VERSION)return;
  window.__kggPatientPlanLinkChoice=VERSION;
  let pendingMemory=null;

  function clone(value){try{return JSON.parse(JSON.stringify(value))}catch(e){return value&&typeof value==='object'?{...value}:value}}
  function readJson(storage,key){try{return JSON.parse(storage.getItem(key)||'null')}catch(e){return null}}
  function decodePayload(value){
    if(window.KGGPlanFormat&&typeof window.KGGPlanFormat.decodePlanText==='function'){
      try{return window.KGGPlanFormat.decodePlanText(value).raw}catch(e){return null}
    }
    let text=String(value||'').trim().replace(/^KGGH2:/i,'').replace(/-/g,'+').replace(/_/g,'/');
    if(!text)return null;
    try{
      while(text.length%4)text+='=';
      const binary=atob(text),bytes=new Uint8Array(binary.length);
      for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
      const decoded=typeof TextDecoder==='function'?new TextDecoder().decode(bytes):decodeURIComponent(escape(binary));
      const raw=JSON.parse(decoded);
      return raw&&typeof raw==='object'&&Array.isArray(raw.e)?raw:null;
    }catch(e){return null}
  }
  function incomingLink(){
    try{
      const query=new URLSearchParams(location.search),queryValue=query.get('plan')||query.get('kgg')||'';
      if(queryValue)return{raw:decodePayload(queryValue),source:'query'};
      const hash=String(location.hash||'').slice(1);
      if(/^KGGH[23]:/i.test(hash))return{raw:decodePayload(hash),source:'hash'};
    }catch(e){}
    return null;
  }
  function activeStoredPlan(){
    const state=readJson(window.localStorage,MULTI_KEY);
    if(state&&Array.isArray(state.plans)&&state.plans.length){
      const index=Math.max(0,Math.min(Number(state.active)||0,state.plans.length-1));
      if(state.plans[index]&&typeof state.plans[index]==='object')return state.plans[index];
    }
    const wrapper=readJson(window.localStorage,CURRENT_KEY);
    return wrapper&&wrapper.plan&&typeof wrapper.plan==='object'?wrapper.plan:null;
  }
  function planKey(raw){
    const id=raw&&String(raw.sourcePlanId||raw.i||'').trim();
    if(id)return'id:'+id;
    try{return'json:'+JSON.stringify(raw)}catch(e){return'object'}
  }
  function stripIncomingUrl(){
    try{if(window.history&&typeof history.replaceState==='function')history.replaceState(null,'',location.pathname)}catch(e){}
  }
  function writePending(link){
    const now=Date.now();
    pendingMemory={version:1,source:link.source,raw:clone(link.raw),createdAt:now,expiresAt:now+TTL_MS};
    try{sessionStorage.setItem(PENDING_KEY,JSON.stringify(pendingMemory))}catch(e){}
  }
  function clearPending(){
    pendingMemory=null;
    try{sessionStorage.removeItem(PENDING_KEY)}catch(e){}
  }
  function readPending(){
    let value=pendingMemory;
    if(!value){try{value=JSON.parse(sessionStorage.getItem(PENDING_KEY)||'null')}catch(e){value=null}}
    if(!value||!value.raw||!Array.isArray(value.raw.e)){clearPending();return null}
    if(Number(value.expiresAt)<=Date.now()){clearPending();return null}
    return value;
  }
  function setStatus(text,kind){try{if(typeof window.setStatus==='function')window.setStatus(text,kind||'')}catch(e){}}
  function readyForChoice(){
    return !!(document&&document.body&&activeStoredPlan()&&
      window.KGGPatientPlanSlots&&typeof window.KGGPatientPlanSlots.addPlan==='function'&&
      window.KGGPatientPlanImport&&typeof window.KGGPatientPlanImport.replaceConfirmed==='function');
  }
  function ensureStyle(){
    if(document.getElementById('kggPlanLinkChoiceStyle'))return;
    const style=document.createElement('style');
    style.id='kggPlanLinkChoiceStyle';
    style.textContent='#kggPlanLinkChoiceBackdrop{position:fixed;inset:0;z-index:2860;background:#0f172a55;padding:14px;display:grid;place-items:center}#kggPlanLinkChoiceBackdrop[hidden],#kggPlanLinkChoice[hidden]{display:none!important}#kggPlanLinkChoice{width:min(100%,520px);box-sizing:border-box;background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:18px;box-shadow:0 22px 70px #0f172a44;font:500 15px/1.4 system-ui,-apple-system,Segoe UI,Arial,sans-serif;color:#111827}#kggPlanLinkChoice h2{margin:0;font-size:20px;line-height:1.2}#kggPlanLinkChoice p{margin:10px 0;color:#475569}#kggPlanLinkChoice .kggPlanLinkChoiceNames{display:grid;gap:8px;margin:12px 0 16px;padding:12px;border-radius:14px;background:#f8fafc;border:1px solid #e2e8f0}#kggPlanLinkChoice .kggPlanLinkChoiceNames b{display:block;color:#64748b;font-size:12px}#kggPlanLinkChoice .kggPlanLinkChoiceNames span{display:block;overflow-wrap:anywhere}#kggPlanLinkChoice .kggPlanLinkChoiceActions{display:grid;gap:8px}#kggPlanLinkChoice button{min-height:46px;border-radius:13px;padding:9px 12px;font:800 15px/1.2 system-ui,-apple-system,Segoe UI,Arial,sans-serif;cursor:pointer}#kggPlanLinkChoice button:disabled{opacity:.55;cursor:wait}#kggPlanLinkChoiceAdd{border:1px solid #166534;background:#15803d;color:#fff}#kggPlanLinkChoiceReplace{border:1px solid #1d4ed8;background:#2563eb;color:#fff}#kggPlanLinkChoiceCancel{border:1px solid #cbd5e1;background:#fff;color:#111827}';
    document.head.appendChild(style);
  }
  function closeDialog(){
    const backdrop=document.getElementById('kggPlanLinkChoiceBackdrop');
    if(backdrop)backdrop.remove();
  }
  function showDialog(pending){
    if(document.getElementById('kggPlanLinkChoiceBackdrop'))return;
    ensureStyle();
    const current=activeStoredPlan(),incoming=pending.raw;
    const backdrop=document.createElement('div');backdrop.id='kggPlanLinkChoiceBackdrop';backdrop.setAttribute('role','presentation');
    const dialog=document.createElement('section');dialog.id='kggPlanLinkChoice';dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby','kggPlanLinkChoiceTitle');
    const title=document.createElement('h2');title.id='kggPlanLinkChoiceTitle';title.textContent='Neuen Trainingsplan öffnen?';
    const intro=document.createElement('p');intro.textContent='Es ist bereits ein anderer Trainingsplan gespeichert. Bitte wähle, wie der neue Plan geöffnet werden soll.';
    const names=document.createElement('div');names.className='kggPlanLinkChoiceNames';
    const oldLabel=document.createElement('div'),oldName=document.createElement('span'),newLabel=document.createElement('div'),newName=document.createElement('span');
    oldLabel.innerHTML='<b>Vorhandener Plan</b>';newLabel.innerHTML='<b>Neuer Plan</b>';
    oldName.textContent=String(current&& (current.t||current.title)||'Aktueller Plan');newName.textContent=String(incoming&&(incoming.t||incoming.title)||'Neuer Plan');
    names.append(oldLabel,oldName,newLabel,newName);
    const actions=document.createElement('div');actions.className='kggPlanLinkChoiceActions';
    const add=document.createElement('button');add.type='button';add.id='kggPlanLinkChoiceAdd';add.textContent='Als zusätzlichen Plan hinzufügen';
    const replace=document.createElement('button');replace.type='button';replace.id='kggPlanLinkChoiceReplace';replace.textContent='Aktiven Plan ersetzen';
    const cancel=document.createElement('button');cancel.type='button';cancel.id='kggPlanLinkChoiceCancel';cancel.textContent='Abbrechen';
    actions.append(add,replace,cancel);dialog.append(title,intro,names,actions);backdrop.appendChild(dialog);document.body.appendChild(backdrop);
    let busy=false;
    const finish=choice=>{
      if(busy)return;
      if(choice==='cancel'){clearPending();closeDialog();setStatus('Import abgebrochen.','');return}
      busy=true;[add,replace,cancel].forEach(button=>button.disabled=true);
      let result=false;
      try{result=choice==='add'?window.KGGPatientPlanSlots.addPlan(clone(incoming)):window.KGGPatientPlanImport.replaceConfirmed(clone(incoming))}catch(e){result=false}
      Promise.resolve(result).then(ok=>{
        if(ok){clearPending();closeDialog()}
        else{busy=false;[add,replace,cancel].forEach(button=>button.disabled=false);setStatus('Der neue Plan konnte nicht übernommen werden.','warn')}
      });
    };
    add.onclick=()=>finish('add');replace.onclick=()=>finish('replace');cancel.onclick=()=>finish('cancel');
    add.focus({preventScroll:true});
  }
  function scheduleDialog(){
    let attempts=0;
    const attempt=()=>{
      const pending=readPending();
      if(!pending)return;
      if(readyForChoice()){showDialog(pending);return}
      if(attempts++<120)setTimeout(attempt,50);
    };
    setTimeout(attempt,0);
  }

  const first=incomingLink(),current=activeStoredPlan();
  if(first&&first.raw&&current&&planKey(first.raw)!==planKey(current)){writePending(first);stripIncomingUrl()}
  window.KGGPatientPlanLinkChoice={version:VERSION,pendingKey:PENDING_KEY,readPending,clearPending,showPending:scheduleDialog};
  if(window.__KGG_TEST__)window.__kggPatientPlanLinkChoiceTest={decodePayload,planKey,readPending,clearPending,TTL_MS};
  if(typeof document!=='undefined'){
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scheduleDialog,{once:true});
    else scheduleDialog();
  }
})();
```
