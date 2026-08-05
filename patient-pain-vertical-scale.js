(()=>{
  const VERSION='vertical-pain-v5-lifecycle-remount';
  const STYLE_ID='kggPainVerticalStyle';
  const MODAL_ID='kggPainModal';
  const DIALOG_ID='kggPainModalDialog';
  const TITLE_ID='kggPainModalTitle';
  const MAX_DESC_ID='kggPainModalMaxDescription';
  const MIN_DESC_ID='kggPainModalMinDescription';
  const LANG_KEY='kggPatientLang';
  const ROOT_CLASS='kggPainVerticalReady';
  const MIN=0;
  const MAX=10;
  let observer=null;
  let mountTimer=0;
  let activeRoot=null;
  let modal=null;
  let bodyLock=null;
  let inerted=[];
  const states=new WeakMap();
  const safe=f=>{try{return f()}catch(e){return null}};
  const clampValue=value=>Math.max(MIN,Math.min(MAX,Math.round(Number(value)||0)));
  const valueFromY=(top,bottom,clientY)=>{
    const start=Number(top)||0,end=Math.max(start+1,Number(bottom)||start+1);
    const ratio=Math.max(0,Math.min(1,(Number(clientY)-start)/(end-start)));
    return clampValue(MAX-ratio*(MAX-MIN));
  };
  const isEnglish=()=>safe(()=>localStorage.getItem(LANG_KEY)==='en')===true;
  const currentText=(selected,value)=>selected?`${clampValue(value)}/10`:'–';
  const labelText=()=>isEnglish()?'Pain during exercise?':'Schmerzen bei der Übung?';
  const valueText=value=>isEnglish()?`${clampValue(value)} of 10`:`${clampValue(value)} von 10`;
  const maxDescription=()=>isEnglish()?'Worst imaginable pain':'Schlimmster vorstellbarer Schmerz';
  const minDescription=()=>isEnglish()?'No pain at all':'Gar kein Schmerz';
  const hintText=()=>isEnglish()?'Slide or tap a number':'Schieben oder Zahl antippen';
  const closeText=()=>isEnglish()?'Close pain scale':'Schmerzskala schließen';

  function ensureStyle(){
    let style=document.getElementById(STYLE_ID);
    if(style)return;
    style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`
      .pain.${ROOT_CLASS}>b,.pain.${ROOT_CLASS}>.painRow{display:none!important}
      .kggPainVertical{margin-top:4px;width:100%}
      .kggPainVerticalToggle{width:100%;min-height:48px;display:grid;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;gap:9px;padding:9px 10px;border:1px solid #cbd5e1;border-radius:13px;background:#fff;color:#111827;text-align:left;font:inherit;font-weight:900;touch-action:manipulation}
      .kggPainVerticalToggle:active{transform:scale(.99);background:#f8fafc}
      .kggPainVerticalToggle:focus-visible{outline:3px solid rgba(37,99,235,.28);outline-offset:2px}
      .kggPainVerticalLabel{min-width:0;line-height:1.25}
      .kggPainVerticalCurrent{min-width:42px;text-align:right;color:#475569;font-variant-numeric:tabular-nums}
      .kggPainVerticalChevron{font-size:17px;color:#64748b;transition:transform .18s ease}
      .kggPainVerticalToggle[aria-expanded="true"] .kggPainVerticalChevron{transform:rotate(180deg)}
      #${MODAL_ID}[hidden]{display:none!important}
      #${MODAL_ID}{position:fixed;inset:0;z-index:9500;box-sizing:border-box;display:flex;align-items:center;justify-content:flex-end;padding:calc(12px + env(safe-area-inset-top)) calc(12px + env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) calc(12px + env(safe-area-inset-left));background:rgba(15,23,42,.26);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);overscroll-behavior:contain;touch-action:none}
      #${DIALOG_ID}{box-sizing:border-box;width:min(270px,calc(100vw - 28px));max-height:calc(100dvh - 24px);display:flex;flex-direction:column;background:#fff;color:#111827;border:1px solid #dbe3ef;border-radius:22px;padding:12px;box-shadow:0 24px 70px rgba(15,23,42,.38);touch-action:auto;overflow:hidden;animation:kggPainModalIn .18s cubic-bezier(.16,.84,.44,1) both}
      .kggPainModalHead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:5px}
      #${TITLE_ID}{font-size:17px;line-height:1.25;font-weight:950;padding:6px 0 0}
      .kggPainModalClose{width:40px;height:40px;flex:0 0 40px;border:1px solid #cbd5e1;border-radius:999px;background:#fff;color:#111827;font:900 24px/1 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
      .kggPainModalClose:active{transform:scale(.96);background:#f8fafc}
      .kggPainModalClose:focus-visible{outline:3px solid rgba(37,99,235,.28);outline-offset:2px}
      .kggPainEndpoint{width:124px;margin-left:auto;color:#475569;font-size:12px;line-height:1.25;font-weight:850;text-align:right}
      .kggPainEndpointMax{margin-bottom:5px}
      .kggPainEndpointMin{margin-top:5px}
      .kggPainVerticalStage{position:relative;margin-left:auto;width:124px;height:min(484px,calc(100dvh - 182px));min-height:220px;flex:0 1 auto;touch-action:none;user-select:none;-webkit-user-select:none;outline:none;border-radius:16px;background:#f8fafc;border:1px solid #e2e8f0;overflow:hidden}
      .kggPainVerticalStage:focus-visible{box-shadow:0 0 0 3px rgba(37,99,235,.28)}
      .kggPainVerticalTrack{position:absolute;z-index:1;left:34px;top:calc(100% / 22);bottom:calc(100% / 22);width:5px;border-radius:999px;background:#cbd5e1;pointer-events:none}
      .kggPainVerticalFill{position:absolute;z-index:2;left:34px;bottom:calc(100% / 22);width:5px;height:calc(var(--kgg-pain-ratio,0) * (100% - 100% / 11));border-radius:999px;background:#2563eb;pointer-events:none}
      .kggPainVerticalThumb{position:absolute;z-index:4;left:36.5px;top:calc((100% / 22) + (1 - var(--kgg-pain-ratio,0)) * (100% - 100% / 11));width:32px;height:32px;border-radius:999px;background:#111827;border:4px solid #fff;box-shadow:0 4px 14px rgba(15,23,42,.28);transform:translate(-50%,-50%);pointer-events:none}
      .kggPainVerticalValues{position:relative;z-index:3;height:100%;display:flex;flex-direction:column}
      .kggPainVerticalValue{min-height:0;flex:1 1 0;width:100%;display:flex;align-items:center;justify-content:flex-end;padding:0 13px 0 58px;font-size:17px;font-weight:950;font-variant-numeric:tabular-nums;color:#475569;border-radius:10px}
      .kggPainVerticalValue[data-active="true"]{color:#1d4ed8;background:linear-gradient(90deg,transparent 0,rgba(219,234,254,.85) 48%,#dbeafe 100%)}
      .kggPainVerticalHint{width:124px;margin:7px 0 0 auto;text-align:right;color:#64748b;font-size:12px;line-height:1.25;font-weight:750}
      @keyframes kggPainModalIn{from{opacity:0;transform:translateY(10px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}
      @media(max-width:430px){#${DIALOG_ID}{width:min(260px,calc(100vw - 24px));padding:10px}.kggPainEndpoint,.kggPainVerticalStage,.kggPainVerticalHint{width:118px}.kggPainVerticalValue{padding-right:11px}}
      @media(max-height:520px){#${MODAL_ID}{padding-top:8px;padding-bottom:8px}#${DIALOG_ID}{max-height:calc(100dvh - 16px);padding:8px}.kggPainModalHead{margin-bottom:2px}#${TITLE_ID}{font-size:15px;padding-top:5px}.kggPainModalClose{width:36px;height:36px;flex-basis:36px}.kggPainEndpoint{font-size:11px}.kggPainVerticalStage{height:calc(100dvh - 142px);min-height:190px}.kggPainVerticalHint{display:none}}
      @media(prefers-reduced-motion:reduce){.kggPainVerticalChevron,#${DIALOG_ID}{animation:none!important;transition:none!important}}
    `;
    document.head.appendChild(style)
  }

  function painKey(ei){return safe(()=>typeof k==='function'?k(ei,0,'P','pain'):null)}
  function readStored(ei){
    const key=painKey(ei),store=safe(()=>v);
    const selected=Boolean(key&&store&&Object.prototype.hasOwnProperty.call(store,key)&&String(store[key]??'')!=='');
    return{selected,value:clampValue(selected?store[key]:0)}
  }
  function commitExisting(ei,value,root){
    const next=clampValue(value);
    if(typeof setPain==='function'){setPain(ei,next);return true}
    const button=root&&root.querySelector(`.kggPainScale button[data-val="${next}"]`);
    if(button){button.click();return true}
    return false
  }
  function originalReady(root){
    const row=root&&root.querySelector(':scope > .painRow');
    if(!row)return false;
    const values=[...row.querySelectorAll('.kggPainScale button[data-val]')].map(button=>Number(button.dataset.val));
    const buttons=values.length===11&&Array.from({length:11},(_,i)=>i).every(i=>values.includes(i));
    const range=row.querySelector('input[type="range"][min="0"][max="10"]');
    return buttons||Boolean(range)
  }
  function hideOriginal(root,state){
    const label=root.querySelector(':scope > b');
    const row=root.querySelector(':scope > .painRow');
    if(!row)return false;
    if(state.row!==row){
      state.row=row;state.rowHidden=row.hidden;state.rowAria=row.getAttribute('aria-hidden');state.rowInert=Boolean(row.inert);state.rowDisplay=row.style.getPropertyValue('display');state.rowDisplayPriority=row.style.getPropertyPriority('display')
    }
    if(state.oldLabel!==label){state.oldLabel=label;state.labelHidden=label?label.hidden:false}
    if(label)label.hidden=true;
    row.hidden=true;row.inert=true;row.setAttribute('aria-hidden','true');row.style.setProperty('display','none','important');
    row.querySelectorAll('button,input').forEach(control=>{if(!control.hasAttribute('data-kgg-old-tabindex'))control.setAttribute('data-kgg-old-tabindex',String(control.tabIndex));control.tabIndex=-1});
    return true
  }
  function restoreOriginal(state){
    const row=state&&state.row,label=state&&state.oldLabel;
    if(label&&label.isConnected)label.hidden=Boolean(state.labelHidden);
    if(row&&row.isConnected){
      row.hidden=Boolean(state.rowHidden);row.inert=Boolean(state.rowInert);
      if(state.rowDisplay)row.style.setProperty('display',state.rowDisplay,state.rowDisplayPriority||'');else row.style.removeProperty('display');
      if(state.rowAria==null)row.removeAttribute('aria-hidden');else row.setAttribute('aria-hidden',state.rowAria);
      row.querySelectorAll('[data-kgg-old-tabindex]').forEach(control=>{control.tabIndex=Number(control.getAttribute('data-kgg-old-tabindex'));control.removeAttribute('data-kgg-old-tabindex')})
    }
  }

  function lockBackground(){
    if(bodyLock)return;
    const body=document.body,scrollY=window.scrollY||0;
    bodyLock={scrollY,position:body.style.position,top:body.style.top,left:body.style.left,right:body.style.right,width:body.style.width,overflow:body.style.overflow};
    body.style.position='fixed';body.style.top=`-${scrollY}px`;body.style.left='0';body.style.right='0';body.style.width='100%';body.style.overflow='hidden';
    inerted=[];
    [...body.children].forEach(node=>{
      if(node===modal.overlay||!node||/^(SCRIPT|STYLE|LINK)$/i.test(node.tagName||''))return;
      inerted.push({node,inert:Boolean(node.inert),aria:node.getAttribute('aria-hidden')});
      node.inert=true;node.setAttribute('aria-hidden','true')
    })
  }
  function unlockBackground(){
    inerted.forEach(entry=>{
      if(!entry.node||!entry.node.isConnected)return;
      entry.node.inert=entry.inert;
      if(entry.aria==null)entry.node.removeAttribute('aria-hidden');else entry.node.setAttribute('aria-hidden',entry.aria)
    });
    inerted=[];
    if(!bodyLock)return;
    const body=document.body,lock=bodyLock;bodyLock=null;
    body.style.position=lock.position;body.style.top=lock.top;body.style.left=lock.left;body.style.right=lock.right;body.style.width=lock.width;body.style.overflow=lock.overflow;
    window.scrollTo(0,lock.scrollY)
  }

  function updateCompact(state,selected,value){
    state.selected=selected;state.committed=clampValue(value);state.current.textContent=currentText(selected,value);
    state.toggle.setAttribute('aria-label',`${labelText()}: ${currentText(selected,value)}`)
  }
  function updateStage(value){
    if(!modal)return;
    const next=clampValue(value),ratio=next/10;
    modal.draft=next;modal.stage.style.setProperty('--kgg-pain-ratio',String(ratio));modal.stage.setAttribute('aria-valuenow',String(next));modal.stage.setAttribute('aria-valuetext',valueText(next));
    modal.values.forEach(row=>row.dataset.active=String(Number(row.dataset.kggPainValue)===next))
  }
  function refreshLanguage(){
    document.querySelectorAll('.kggPainVerticalLabel').forEach(label=>label.textContent=labelText());
    if(!modal)return;
    modal.title.textContent=labelText();modal.maxDesc.textContent=maxDescription();modal.minDesc.textContent=minDescription();modal.hint.textContent=hintText();modal.close.setAttribute('aria-label',closeText());modal.stage.setAttribute('aria-label',labelText());
    if(activeRoot){const state=states.get(activeRoot);if(state)state.toggle.setAttribute('aria-label',`${labelText()}: ${currentText(state.selected,state.committed)}`)}
  }
  function refreshModalFromRoot(root){
    const state=states.get(root);if(!state||!modal)return false;
    const stored=readStored(state.ei);updateCompact(state,stored.selected,stored.value);modal.committed=stored.value;modal.selected=stored.selected;updateStage(stored.value);refreshLanguage();return true
  }
  function commitModal(value){
    if(!activeRoot||!modal)return false;
    const state=states.get(activeRoot),next=clampValue(value);
    if(!state||!commitExisting(state.ei,next,activeRoot))return false;
    modal.selected=true;modal.committed=next;updateStage(next);updateCompact(state,true,next);return true
  }

  function restoreModalDraft(){if(modal)updateStage(modal.committed)}
  function closeModal(options={}){
    if(!modal||modal.overlay.hidden)return;
    const returnFocus=options.returnFocus!==false,opener=activeRoot&&states.get(activeRoot)?.toggle;
    restoreModalDraft();modal.gesture=null;modal.keyboardDirty=false;modal.overlay.hidden=true;
    if(activeRoot){const state=states.get(activeRoot);if(state)state.toggle.setAttribute('aria-expanded','false')}
    activeRoot=null;unlockBackground();
    if(returnFocus&&opener&&opener.isConnected)setTimeout(()=>safe(()=>opener.focus({preventScroll:true})),0)
  }
  function openModal(root){
    const state=states.get(root);if(!state||!ensureModal())return;
    if(activeRoot&&activeRoot!==root){const prior=states.get(activeRoot);if(prior)prior.toggle.setAttribute('aria-expanded','false')}
    activeRoot=root;if(!refreshModalFromRoot(root)){activeRoot=null;return}
    modal.overlay.hidden=false;state.toggle.setAttribute('aria-expanded','true');lockBackground();
    requestAnimationFrame(()=>safe(()=>modal.stage.focus({preventScroll:true})))
  }
  function toggleModal(root){if(activeRoot===root&&modal&&!modal.overlay.hidden)closeModal();else openModal(root)}

  function modalKeydown(event){
    if(!modal||modal.overlay.hidden)return;
    if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closeModal();return}
    if(event.key!=='Tab')return;
    const focusables=[modal.stage,modal.close].filter(node=>node&&!node.disabled);
    if(!focusables.length)return;
    const current=document.activeElement,index=focusables.indexOf(current);
    event.preventDefault();
    const next=event.shiftKey?(index<=0?focusables.length-1:index-1):(index<0||index===focusables.length-1?0:index+1);
    focusables[next].focus()
  }

  function bindStage(){
    const stage=modal.stage;
    stage.addEventListener('pointerdown',event=>{
      if(event.button!=null&&event.button!==0)return;
      event.preventDefault();event.stopPropagation();
      const exact=event.target.closest('[data-kgg-pain-value]');
      const rect=stage.getBoundingClientRect(),rowHeight=rect.height/(MAX-MIN+1),top=rect.top+rowHeight/2,bottom=rect.bottom-rowHeight/2;
      const next=exact?clampValue(exact.dataset.kggPainValue):valueFromY(top,bottom,event.clientY);
      modal.gesture={pointerId:event.pointerId};try{stage.setPointerCapture&&stage.setPointerCapture(event.pointerId)}catch(e){}updateStage(next)
    });
    stage.addEventListener('pointermove',event=>{
      if(!modal.gesture||modal.gesture.pointerId!==event.pointerId)return;
      event.preventDefault();event.stopPropagation();
      const rect=stage.getBoundingClientRect(),rowHeight=rect.height/(MAX-MIN+1);
      updateStage(valueFromY(rect.top+rowHeight/2,rect.bottom-rowHeight/2,event.clientY))
    });
    stage.addEventListener('pointerup',event=>{
      if(!modal.gesture||modal.gesture.pointerId!==event.pointerId)return;
      event.preventDefault();event.stopPropagation();modal.gesture=null;
      try{stage.releasePointerCapture&&stage.releasePointerCapture(event.pointerId)}catch(e){}
      if(!commitModal(modal.draft))restoreModalDraft()
    });
    stage.addEventListener('pointercancel',event=>{if(!modal.gesture)return;event.preventDefault();event.stopPropagation();modal.gesture=null;restoreModalDraft()});
    stage.addEventListener('keydown',event=>{
      let next=modal.draft,handled=true;
      if(event.key==='ArrowUp'||event.key==='ArrowRight')next++;
      else if(event.key==='ArrowDown'||event.key==='ArrowLeft')next--;
      else if(event.key==='Home')next=MIN;
      else if(event.key==='End')next=MAX;
      else if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();commitModal(modal.draft);modal.keyboardDirty=false;return}
      else handled=false;
      if(handled){event.preventDefault();event.stopPropagation();modal.keyboardDirty=true;updateStage(next)}
    });
    stage.addEventListener('blur',()=>{if(modal.keyboardDirty){modal.keyboardDirty=false;restoreModalDraft()}})
  }

  function ensureModal(){
    if(modal&&modal.overlay&&modal.overlay.isConnected)return true;
    ensureStyle();
    try{
      const overlay=document.createElement('div');overlay.id=MODAL_ID;overlay.hidden=true;
      const dialog=document.createElement('section');dialog.id=DIALOG_ID;dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby',TITLE_ID);
      const head=document.createElement('div');head.className='kggPainModalHead';
      const title=document.createElement('strong');title.id=TITLE_ID;
      const close=document.createElement('button');close.type='button';close.className='kggPainModalClose';close.textContent='×';
      head.append(title,close);
      const maxDesc=document.createElement('div');maxDesc.id=MAX_DESC_ID;maxDesc.className='kggPainEndpoint kggPainEndpointMax';
      const stage=document.createElement('div');stage.className='kggPainVerticalStage';stage.tabIndex=0;stage.setAttribute('role','slider');stage.setAttribute('aria-valuemin','0');stage.setAttribute('aria-valuemax','10');stage.setAttribute('aria-orientation','vertical');stage.setAttribute('aria-describedby',`${MAX_DESC_ID} ${MIN_DESC_ID}`);
      const track=document.createElement('div');track.className='kggPainVerticalTrack';
      const fill=document.createElement('div');fill.className='kggPainVerticalFill';
      const thumb=document.createElement('div');thumb.className='kggPainVerticalThumb';
      const values=document.createElement('div');values.className='kggPainVerticalValues';const rows=[];
      for(let n=MAX;n>=MIN;n--){const row=document.createElement('div');row.className='kggPainVerticalValue';row.dataset.kggPainValue=String(n);row.textContent=String(n);values.appendChild(row);rows.push(row)}
      stage.append(track,fill,thumb,values);
      const minDesc=document.createElement('div');minDesc.id=MIN_DESC_ID;minDesc.className='kggPainEndpoint kggPainEndpointMin';
      const hint=document.createElement('div');hint.className='kggPainVerticalHint';
      dialog.append(head,maxDesc,stage,minDesc,hint);overlay.appendChild(dialog);document.body.appendChild(overlay);
      modal={overlay,dialog,title,close,maxDesc,minDesc,stage,values:rows,hint,selected:false,committed:0,draft:0,gesture:null,keyboardDirty:false};
      overlay.addEventListener('pointerdown',event=>{if(event.target===overlay){event.preventDefault();closeModal()}});
      dialog.addEventListener('pointerdown',event=>event.stopPropagation());
      close.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();closeModal()});
      overlay.addEventListener('keydown',modalKeydown,true);bindStage();refreshLanguage();return true
    }catch(e){safe(()=>document.getElementById(MODAL_ID)?.remove());modal=null;return false}
  }

  function buildCompact(root,ei){
    const wrap=document.createElement('div');wrap.className='kggPainVertical';
    const toggle=document.createElement('button');toggle.type='button';toggle.className='kggPainVerticalToggle';toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-controls',MODAL_ID);
    const label=document.createElement('span');label.className='kggPainVerticalLabel';
    const current=document.createElement('span');current.className='kggPainVerticalCurrent';
    const chevron=document.createElement('span');chevron.className='kggPainVerticalChevron';chevron.textContent='⌄';chevron.setAttribute('aria-hidden','true');
    toggle.append(label,current,chevron);wrap.appendChild(toggle);root.appendChild(wrap);
    const state={ei,wrap,toggle,label,current,selected:false,committed:0,row:null,oldLabel:null,labelHidden:false,rowHidden:false,rowAria:null,rowInert:false,rowDisplay:'',rowDisplayPriority:''};
    states.set(root,state);
    toggle.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();toggleModal(root)});
    wrap.addEventListener('click',event=>event.stopPropagation());return state
  }
  function refreshState(root,state){
    const stored=readStored(state.ei);state.label.textContent=labelText();updateCompact(state,stored.selected,stored.value)
  }
  function teardown(root){
    const state=states.get(root);if(!state)return;
    if(activeRoot===root)closeModal({returnFocus:false});restoreOriginal(state);state.wrap.remove();root.classList.remove(ROOT_CLASS);states.delete(root)
  }
  function mountRoot(root,ei){
    const card=root.closest('.ex');
    const setMode=Boolean(card&&card.querySelector('.kggSetPain'))||root.classList.contains('kggHiddenGlobalPain')||root.style.display==='none';
    if(setMode){teardown(root);return}
    if(!originalReady(root)||typeof setPain!=='function'||!ensureModal())return;
    let state=states.get(root);if(!state){state=buildCompact(root,ei);root.classList.add(ROOT_CLASS)}else state.ei=ei;
    if(!hideOriginal(root,state)){teardown(root);return}refreshState(root,state)
  }
  function mountAll(){
    ensureStyle();ensureModal();
    const cards=[...document.querySelectorAll('#list .ex')];
    cards.forEach((card,ei)=>{const root=card.querySelector(':scope > .pain');if(root)mountRoot(root,ei)});
    if(activeRoot&&!activeRoot.isConnected)closeModal({returnFocus:false});refreshLanguage()
  }
  function scheduleMount(delay=0){clearTimeout(mountTimer);mountTimer=setTimeout(mountAll,delay)}
  function observe(){
    const list=document.getElementById('list');if(!list)return;
    if(observer)observer.disconnect();observer=new MutationObserver(()=>scheduleMount(20));observer.observe(list,{childList:true,subtree:true,attributes:true,attributeFilter:['class']})
  }
  function init(){
    if(window.__kggPatientPainVertical===VERSION)return;window.__kggPatientPainVertical=VERSION;
    ensureStyle();ensureModal();observe();mountAll();setTimeout(()=>{observe();mountAll()},250);setTimeout(mountAll,900);
    document.addEventListener('click',event=>{if(event.target&&event.target.closest&&event.target.closest('#kggLangSwitch'))setTimeout(()=>{refreshLanguage();mountAll()},0)},true);
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&modal&&!modal.overlay.hidden){event.preventDefault();closeModal()}},true);
    const refreshAfterLifecycleChange=()=>[0,80,250].forEach(delay=>setTimeout(()=>{observe();mountAll()},delay));
    document.addEventListener('click',event=>{
      const target=event.target&&event.target.closest?event.target.closest('#days button,#kggDayHub button,#kggBubblePlans,#kggBubbleAdd,#kggBubbleReplace,#kggPlanScanBtn,#qr img'):null;
      if(!target)return;
      if(modal&&!modal.overlay.hidden)closeModal({returnFocus:false});
      refreshAfterLifecycleChange()
    },true);
    addEventListener('resize',()=>scheduleMount(80),{passive:true});addEventListener('orientationchange',()=>scheduleMount(180),{passive:true});addEventListener('pagehide',()=>closeModal({returnFocus:false}))
  }
  if(window.__KGG_TEST__)window.__kggPainVerticalTest={clampValue,valueFromY,currentText};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();