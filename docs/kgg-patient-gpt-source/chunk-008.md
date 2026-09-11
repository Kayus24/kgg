# KGG Patient Source Chunk 008

- Source file: `patient-card-progress.js`
- Characters: 1-15326
- Full source SHA-256: `bb62bcbb38e6dffa16560af68fbf71d54abc7e7c0a66809e1ac7eadf5ecc04f5`

```
(()=>{
  const VERSION='card-progress-v2-complete-fields';
  const STYLE_ID='kgg-card-progress-style';
  const BADGE_CLASS='kggCardProgress';
  if(window.__kggCardProgress===VERSION)return;
  window.__kggCardProgress=VERSION;

  function stateForCount(count,total){
    const filled=Math.max(0,Number(count)||0);
    const expected=Math.max(0,Number(total)||0);
    if(filled===0)return 'open';
    if(expected>0&&filled>=expected)return 'done';
    return 'partial'
  }
  function language(){return localStorage.getItem('kggPatientLang')==='en'?'en':'de'}
  function labelForState(state,lang){
    const en=(lang||language())==='en';
    if(state==='done')return en?'✓ Done':'✓ Bearbeitet';
    if(state==='partial')return en?'◐ Partial':'◐ Teilweise';
    return en?'○ Open':'○ Offen'
  }
  function normalValueInputs(card){
    if(!card||typeof card.querySelectorAll!=='function')return [];
    return [...card.querySelectorAll('.set input.num')]
  }
  function filledCount(card){
    return normalValueInputs(card).filter(input=>String(input&&input.value!=null?input.value:'').trim()!=='').length
  }
  function ensureStyle(){
    if(document.getElementById(STYLE_ID))return;
    const style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`.${BADGE_CLASS}{display:none}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS},body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}{display:inline-flex!important;align-items:center;width:max-content;max-width:100%;margin:0 0 2px;padding:3px 8px;border:1px solid #cbd5e1;border-radius:999px;background:#f8fafc;color:#64748b;font-size:11px;font-weight:900;line-height:1.2;white-space:nowrap}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressPartial,body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressPartial{border-color:#fcd34d;background:#fffbeb;color:#92400e}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressDone,body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressDone{border-color:#86efac;background:#ecfdf5;color:#166534}`;
    document.head.appendChild(style)
  }
  function ensureBadge(card){
    let badge=card.querySelector('.'+BADGE_CLASS);
    if(badge)return badge;
    badge=document.createElement('span');
    badge.className=BADGE_CLASS;
    badge.setAttribute('aria-live','polite');
    const title=card.querySelector('h3');
    if(title&&title.insertAdjacentElement)title.insertAdjacentElement('afterend',badge);
    else card.insertBefore(badge,card.firstChild||null);
    return badge
  }
  function updateCard(card){
    if(!card)return;
    const inputs=normalValueInputs(card);
    const count=inputs.filter(input=>String(input&&input.value!=null?input.value:'').trim()!=='').length;
    const state=stateForCount(count,inputs.length);
    const badge=ensureBadge(card);
    const nextClass=BADGE_CLASS+' kggProgress'+state.charAt(0).toUpperCase()+state.slice(1);
    const nextLabel=labelForState(state);
    if(badge.className!==nextClass)badge.className=nextClass;
    if(badge.textContent!==nextLabel)badge.textContent=nextLabel;
    if(badge.dataset.kggProgress!==state)badge.dataset.kggProgress=state;
    if(badge.dataset.kggFilledCount!==String(count))badge.dataset.kggFilledCount=String(count);
    if(badge.dataset.kggExpectedCount!==String(inputs.length))badge.dataset.kggExpectedCount=String(inputs.length);
    if(badge.title!==nextLabel)badge.title=nextLabel;
    if(badge.getAttribute('aria-label')!==nextLabel)badge.setAttribute('aria-label',nextLabel)
  }
  function cards(){return [...document.querySelectorAll('#list .ex')]}
  function updateAll(){ensureStyle();cards().forEach(updateCard)}
  let updateTimer=0;
  function scheduleUpdate(delay){
    clearTimeout(updateTimer);
    updateTimer=setTimeout(updateAll,Number(delay)||0)
  }
  function bindEvents(){
    if(window.__kggCardProgressEvents)return;
    window.__kggCardProgressEvents=1;
    document.addEventListener('input',event=>{if(event.target&&event.target.matches&&event.target.matches('#list .set input.num'))scheduleUpdate(0)},true);
    document.addEventListener('change',event=>{if(event.target&&event.target.matches&&event.target.matches('#list .set input.num'))scheduleUpdate(0)},true);
    document.addEventListener('click',event=>{
      if(event.target&&event.target.closest&&event.target.closest('.padOk,.padCancel,.padLast,.padGrid,#days')){
        scheduleUpdate(40);setTimeout(updateAll,180);setTimeout(updateAll,360)
      }
    },true)
  }
  function observeList(){
    const list=document.getElementById('list');
    if(!list||list.dataset.kggCardProgressObserved==='1'||typeof MutationObserver==='undefined')return;
    list.dataset.kggCardProgressObserved='1';
    const observer=new MutationObserver(()=>scheduleUpdate(0));
    observer.observe(list,{childList:true,subtree:true})
  }
  function patchRender(){
    if(window.__kggCardProgressRenderPatched||typeof render!=='function')return;
    window.__kggCardProgressRenderPatched=1;
    const old=render;
    window.render=function(){const result=old.apply(this,arguments);scheduleUpdate(0);setTimeout(updateAll,120);return result}
  }

  const TICKET034_META='__kggTicket034WarnCountersV1';
  const FINISH_STYLE_ID='kggTicket034FinishStyle';
  const FINISH_MODAL_ID='kggTicket034FinishModal';
  const FINISH_MESSAGE_ID='kggTicket034FinishMessage';
  let finishPending=null;
  let finishFinalizing=false;
  let finishBypass=false;

  function ticket034NormalizeCounter(value){
    const count=Number(value);
    if(!Number.isFinite(count)||count<=0)return 0;
    if(count>=2)return 2;
    return 1
  }
  function ticket034CounterMap(create){
    if(typeof v==='undefined'||!v||typeof v!=='object')return {};
    const current=v[TICKET034_META];
    if(current&&typeof current==='object'&&!Array.isArray(current))return current;
    if(!create)return {};
    const next={};
    v[TICKET034_META]=next;
    return next
  }
  function ticket034CounterFor(ei){
    return ticket034NormalizeCounter(ticket034CounterMap(false)[String(ei)])
  }
  function ticket034SetCounter(ei,value){
    const key=String(ei),next=ticket034NormalizeCounter(value),map=ticket034CounterMap(true);
    if(ticket034NormalizeCounter(map[key])===next&&Object.prototype.hasOwnProperty.call(map,key))return false;
    map[key]=next;
    return true
  }
  function ticket034HasNormalValue(exerciseIndex,day,values,plan,keyFn){
    const sourcePlan=plan||p;
    const sourceValues=values||v;
    const ex=sourcePlan&&Array.isArray(sourcePlan.ex)?sourcePlan.ex[exerciseIndex]:null;
    if(!ex)return false;
    const sets=Math.max(1,Number(ex.sets)||1);
    const sides=ex.side==='LR'?['L','R']:['B'];
    const makeKey=keyFn||k;
    for(let setNo=1;setNo<=sets;setNo++){
      for(const side of sides){
        for(const field of ['a','b']){
          if(String((sourceValues&&sourceValues[makeKey(exerciseIndex,setNo,side,field,day)])??'').trim()!=='')return true
        }
      }
    }
    return false
  }
  function ticket034Candidates(day){
    if(typeof p==='undefined'||!p||!Array.isArray(p.ex))return [];
    return p.ex.map((ex,ei)=>({ei,name:String(ex&&ex.n||'Übung'),counter:ticket034CounterFor(ei)}))
      .filter(item=>item.counter<2&&!ticket034HasNormalValue(item.ei,day))
  }
  function ticket034IncrementCandidates(candidates){
    let changed=false;
    (Array.isArray(candidates)?candidates:[]).forEach(item=>{
      const before=ticket034NormalizeCounter(item&&item.counter);
      if(before<2)changed=ticket034SetCounter(item.ei,before+1)||changed
    });
    return changed
  }
  function ticket034ResetAfterNormalValue(ei,value){
    if(String(value??'').trim()===''||ticket034CounterFor(ei)===0)return false;
    return ticket034SetCounter(ei,0)
  }

  function ensureFinishStyle(){
    if(document.getElementById(FINISH_STYLE_ID))return;
    const style=document.createElement('style');
    style.id=FINISH_STYLE_ID;
    style.textContent=`#${FINISH_MODAL_ID}[hidden]{display:none!important}#${FINISH_MODAL_ID}{position:fixed;inset:0;z-index:2900;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(15,23,42,.58)}#${FINISH_MODAL_ID} .kggTicket034Dialog{width:min(100%,520px);max-height:calc(100dvh - 32px);overflow:auto;background:#fff;color:#111827;border:1px solid #dbe3ef;border-radius:20px;padding:18px;box-shadow:0 22px 70px rgba(15,23,42,.28)}#${FINISH_MODAL_ID} .kggTicket034Message{margin:0;font-size:16px;line-height:1.5;font-weight:700}#${FINISH_MODAL_ID} .kggTicket034Actions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:18px}#${FINISH_MODAL_ID} .kggTicket034Actions .btn,#${FINISH_MODAL_ID} .kggTicket034Actions .btn2{min-height:50px;margin-top:0}#${FINISH_MODAL_ID} button:focus-visible{outline:3px solid #94a3b8;outline-offset:2px}@media(max-width:430px){#${FINISH_MODAL_ID}{padding:12px}#${FINISH_MODAL_ID} .kggTicket034Dialog{padding:16px;border-radius:18px}#${FINISH_MODAL_ID} .kggTicket034Actions{grid-template-columns:1fr}}`;
    document.head.appendChild(style)
  }
  function ensureFinishModal(){
    ensureFinishStyle();
    let modal=document.getElementById(FINISH_MODAL_ID);
    if(modal)return modal;
    modal=document.createElement('div');
    modal.id=FINISH_MODAL_ID;
    modal.hidden=true;
    modal.setAttribute('role','dialog');
    modal.setAttribute('aria-modal','true');
    modal.setAttribute('aria-label','Training beenden');
    modal.setAttribute('aria-describedby',FINISH_MESSAGE_ID);
    const dialog=document.createElement('div');
    dialog.className='kggTicket034Dialog';
    const message=document.createElement('p');
    message.id=FINISH_MESSAGE_ID;
    message.className='kggTicket034Message';
    const actions=document.createElement('div');
    actions.className='kggTicket034Actions';
    const cancel=document.createElement('button');
    cancel.type='button';
    cancel.className='btn2';
    cancel.dataset.kggTicket034Action='cancel';
    cancel.textContent='Weiter trainieren';
    const confirm=document.createElement('button');
    confirm.type='button';
    confirm.className='btn';
    confirm.dataset.kggTicket034Action='confirm';
    confirm.textContent='Training beenden';
    actions.append(cancel,confirm);
    dialog.append(message,actions);
    modal.appendChild(dialog);
    modal.addEventListener('click',event=>{if(event.target===modal)ticket034CancelFinish()});
    modal.addEventListener('keydown',event=>{
      if(event.key==='Escape'){event.preventDefault();ticket034CancelFinish();return}
      if(event.key!=='Tab')return;
      const buttons=[cancel,confirm].filter(button=>!button.disabled);
      if(!buttons.length){event.preventDefault();return}
      const first=buttons[0],last=buttons[buttons.length-1],active=document.activeElement;
      if(event.shiftKey&&(active===first||!modal.contains(active))){event.preventDefault();last.focus()}
      else if(!event.shiftKey&&(active===last||!modal.contains(active))){event.preventDefault();first.focus()}
    });
    cancel.addEventListener('click',ticket034CancelFinish);
    confirm.addEventListener('click',ticket034ConfirmFinish);
    document.body.appendChild(modal);
    return modal
  }
  function ticket034RestoreFocus(target){
    if(target&&typeof target.focus==='function'&&document.contains(target)){
      try{target.focus({preventScroll:true})}catch(e){target.focus()}
    }
  }
  function ticket034CloseModal(restore){
    const modal=document.getElementById(FINISH_MODAL_ID);
    const focusTarget=finishPending&&finishPending.restoreFocus;
    if(modal)modal.hidden=true;
    if(restore)ticket034RestoreFocus(focusTarget)
  }
  function ticket034OpenFinish(candidates){
    if(finishPending||finishFinalizing||!Array.isArray(candidates)||!candidates.length)return false;
    const modal=ensureFinishModal();
    const active=document.activeElement;
    const fallback=document.querySelector('#plan .btn[onclick*="showQr(true)"]');
    finishPending={
      candidates:candidates.map(item=>({ei:item.ei,counter:item.counter})),
      restoreFocus:active&&active!==document.body?active:fallback
    };
    const message=document.getElementById(FINISH_MESSAGE_ID);
    message.textContent=`Sie haben noch die Übung „${candidates[0].name}“ offen. Sicher, dass Sie das Training beenden wollen?`;
    const cancel=modal.querySelector('[data-kgg-ticket034-action="cancel"]');
    const confirm=modal.querySelector('[data-kgg-ticket034-action="confirm"]');
    cancel.disabled=false;
    confirm.disabled=false;
    modal.hidden=false;
    setTimeout(()=>cancel.focus({preventScroll:true}),0);
    return true
  }
  function ticket034CancelFinish(){
    if(finishFinalizing||!finishPending)return;
    const snapshot=finishPending;
    ticket034CloseModal(false);
    finishPending=null;
    ticket034RestoreFocus(snapshot.restoreFocus)
  }
  function ticket034ConfirmFinish(){
    if(finishFinalizing||!finishPending)return;
    const snapshot=finishPending;
    const modal=ensureFinishModal();
    const cancel=modal.querySelector('[data-kgg-ticket034-action="cancel"]');
    const confirm=modal.querySelector('[data-kgg-ticket034-action="confirm"]');
    finishFinalizing=true;
    cancel.disabled=true;
    confirm.disabled=true;
    let error=null;
    try{
      finishBypass=true;
      window.showQr(true);
      finishBypass=false;
      if(ticket034IncrementCandidates(snapshot.candidates)&&typeof save==='function')save();
      ticket034CloseModal(false);
      finishPending=null
    }catch(err){
      error=err;
      finishBypass=false;
      cancel.disabled=false;
      confirm.disabled=false
    }finally{
      finishFinalizing=false
    }
    if(error)throw error
  }
  function patchPut(){
    if(window.__kggTicket034PutPatched||typeof put!=='function')return;
    window.__kggTicket034PutPatched=1;
    const old=put;
    window.put=function(ei,s,side,key,value){
      const result=old.apply(this,arguments);
      if(ticket034ResetAfterNormalValue(ei,value)&&typeof save==='function')save();
      return result
    }
  }
  function patchShowQr(){
    if(window.__kggTicket034ShowQrPatched||typeof showQr!=='function')return;
    window.__kggTicket034ShowQrPatched=1;
    const old=showQr;
    window.showQr=function(finalize){
      if(!finalize||finishBypass)return old.apply(this,arguments);
      if(finishPending||finishFinalizing)return;
      const candidates=ticket034Candidates(Number(d)||1);
      if(!candidates.length)return old.apply(this,arguments);
      ticket034OpenFinish(candidates)
    }
  }

  function init(){
    ensureStyle();bindEvents();observeList();patchRender();patchPut();patchShowQr();ensureFinishStyle();updateAll();
    setTimeout(()=>{observeList();patchRender();patchPut();patchShowQr();updateAll()},300);
    setTimeout(()=>{observeList();patchRender();patchPut();patchShowQr();updateAll()},1000)
  }
  if(window.__KGG_TEST__)window.__kggCardProgressTest={stateForCount,labelForState,filledCount,normalValueInputs,ticket034NormalizeCounter,ticket034HasNormalValue,ticket034Candidates,ticket034IncrementCandidates,ticket034ResetAfterNormalValue,ticket034OpenFinish,ticket034CancelFinish,ticket034ConfirmFinish,patchPut,patchShowQr};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
```
