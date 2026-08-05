# KGG Patient Source Chunk 020

- Source file: `patient-pain-vertical-scale.js`
- Characters: 1-16846
- Full source SHA-256: `70c3d1e97826c658e690fa7694c6678dc710182c80920d8e41a9e6bec806fc6c`

```
(()=>{
  const VERSION='vertical-pain-v2-force-hide-legacy';
  const STYLE_ID='kggPainVerticalStyle';
  const LANG_KEY='kggPatientLang';
  const ROOT_CLASS='kggPainVerticalReady';
  const OPEN_CLASS='kggPainVerticalOpen';
  const MIN=0;
  const MAX=10;
  const ROW_HEIGHT=44;
  let openRoot=null;
  let observer=null;
  let mountTimer=0;
  const states=new WeakMap();
  const safe=f=>{try{return f()}catch(e){return null}};
  const clampValue=value=>Math.max(MIN,Math.min(MAX,Math.round(Number(value)||0)));
  const valueFromY=(top,bottom,clientY)=>{
    const start=Number(top)||0,end=Math.max(start+1,Number(bottom)||start+1);
    const ratio=Math.max(0,Math.min(1,(Number(clientY)-start)/(end-start)));
    return clampValue(MAX-ratio*(MAX-MIN));
  };
  const isEnglish=()=>safe(()=>localStorage.getItem(LANG_KEY)==='en')===true;
  const currentText=(selected,value,en=isEnglish())=>selected?`${clampValue(value)}/10`:'–';
  const labelText=()=>isEnglish()?'Pain during exercise':'Schmerzen bei der Übung';
  const valueText=value=>isEnglish()?`${clampValue(value)} of 10`:`${clampValue(value)} von 10`;

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
      .kggPainVerticalLabel{min-width:0;line-height:1.25}
      .kggPainVerticalCurrent{min-width:42px;text-align:right;color:#475569;font-variant-numeric:tabular-nums}
      .kggPainVerticalChevron{font-size:17px;color:#64748b;transition:transform .18s ease}
      .${OPEN_CLASS} .kggPainVerticalChevron{transform:rotate(180deg)}
      .kggPainVerticalPanel{display:grid;grid-template-rows:0fr;opacity:0;pointer-events:none;transition:grid-template-rows .22s cubic-bezier(.16,.84,.44,1),opacity .16s ease;margin-top:0}
      .${OPEN_CLASS} .kggPainVerticalPanel{grid-template-rows:1fr;opacity:1;pointer-events:auto;margin-top:8px}
      .kggPainVerticalPanelInner{min-height:0;overflow:hidden}
      .kggPainVerticalStage{position:relative;margin-left:auto;width:124px;height:${ROW_HEIGHT*(MAX-MIN+1)}px;flex:0 0 124px;touch-action:none;user-select:none;-webkit-user-select:none;outline:none;border-radius:16px;background:#f8fafc;border:1px solid #e2e8f0;overflow:hidden}
      .kggPainVerticalStage:focus-visible{box-shadow:0 0 0 3px rgba(17,24,39,.22)}
      .kggPainVerticalTrack{position:absolute;z-index:1;left:34px;top:22px;bottom:22px;width:5px;border-radius:999px;background:#cbd5e1;pointer-events:none}
      .kggPainVerticalFill{position:absolute;z-index:2;left:34px;bottom:22px;width:5px;height:calc(var(--kgg-pain-ratio,0) * 440px);border-radius:999px;background:#2563eb;pointer-events:none}
      .kggPainVerticalThumb{position:absolute;z-index:4;left:36.5px;top:calc(22px + (1 - var(--kgg-pain-ratio,0)) * 440px);width:32px;height:32px;border-radius:999px;background:#111827;border:4px solid #fff;box-shadow:0 4px 14px rgba(15,23,42,.28);transform:translate(-50%,-50%);pointer-events:none}
      .kggPainVerticalValues{position:relative;z-index:3;height:100%;display:flex;flex-direction:column}
      .kggPainVerticalValue{height:${ROW_HEIGHT}px;min-height:${ROW_HEIGHT}px;width:100%;display:flex;align-items:center;justify-content:flex-end;padding:0 13px 0 58px;font-size:17px;font-weight:950;font-variant-numeric:tabular-nums;color:#475569;border-radius:10px}
      .kggPainVerticalValue[data-active="true"]{color:#1d4ed8;background:linear-gradient(90deg,transparent 0,rgba(219,234,254,.85) 48%,#dbeafe 100%)}
      .kggPainVerticalHint{margin:7px 2px 0;text-align:right;color:#64748b;font-size:12px;font-weight:750}
      @media(max-width:430px){.kggPainVerticalStage{width:118px;flex-basis:118px}.kggPainVerticalValue{padding-right:11px}}
      @media(prefers-reduced-motion:reduce){.kggPainVerticalPanel,.kggPainVerticalChevron{transition:none!important}}
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
      state.row=row;state.rowHidden=row.hidden;state.rowAria=row.getAttribute('aria-hidden');state.rowInert=Boolean(row.inert);state.rowDisplay=row.style.getPropertyValue('display');state.rowDisplayPriority=row.style.getPropertyPriority('display');
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
      row.hidden=Boolean(state.rowHidden);row.inert=Boolean(state.rowInert);if(state.rowDisplay)row.style.setProperty('display',state.rowDisplay,state.rowDisplayPriority||'');else row.style.removeProperty('display');
      if(state.rowAria==null)row.removeAttribute('aria-hidden');else row.setAttribute('aria-hidden',state.rowAria);
      row.querySelectorAll('[data-kgg-old-tabindex]').forEach(control=>{control.tabIndex=Number(control.getAttribute('data-kgg-old-tabindex'));control.removeAttribute('data-kgg-old-tabindex')})
    }
  }

  function updateVisual(state,value,selected=state.selected){
    const next=clampValue(value),ratio=next/10;
    state.draft=next;
    state.stage.style.setProperty('--kgg-pain-ratio',String(ratio));
    state.stage.setAttribute('aria-valuenow',String(next));
    state.stage.setAttribute('aria-valuetext',valueText(next));
    state.current.textContent=currentText(selected,next);
    state.values.forEach(row=>row.dataset.active=String(Number(row.dataset.kggPainValue)===next))
  }
  function refreshState(root,state){
    const stored=readStored(state.ei);
    state.selected=stored.selected;state.committed=stored.value;
    updateVisual(state,stored.value,stored.selected);
    state.titleLabel.textContent=labelText();
    state.stage.setAttribute('aria-label',labelText());
    state.hint.textContent=isEnglish()?'Slide or tap a number':'Schieben oder Zahl antippen';
    state.toggle.setAttribute('aria-label',`${labelText()}: ${currentText(stored.selected,stored.value)}`)
  }
  function closePanel(root,restoreDraft=true){
    const state=states.get(root);if(!state)return;
    clearTimeout(state.closeTimer);
    if(restoreDraft)updateVisual(state,state.committed,state.selected);
    root.classList.remove(OPEN_CLASS);state.toggle.setAttribute('aria-expanded','false');
    state.closeTimer=setTimeout(()=>{if(!root.classList.contains(OPEN_CLASS))state.panel.hidden=true},180);
    if(openRoot===root)openRoot=null
  }
  function openPanel(root){
    const state=states.get(root);if(!state)return;
    if(openRoot&&openRoot!==root)closePanel(openRoot,true);
    refreshState(root,state);clearTimeout(state.closeTimer);state.panel.hidden=false;
    requestAnimationFrame(()=>root.classList.add(OPEN_CLASS));state.toggle.setAttribute('aria-expanded','true');openRoot=root
  }
  function togglePanel(root){root.classList.contains(OPEN_CLASS)?closePanel(root,true):openPanel(root)}
  function commit(state,root,value){
    const next=clampValue(value);
    if(!commitExisting(state.ei,next,root)){closePanel(root,true);return}
    state.selected=true;state.committed=next;updateVisual(state,next,true);
    state.toggle.setAttribute('aria-label',`${labelText()}: ${next}/10`);
    clearTimeout(state.closeTimer);state.closeTimer=setTimeout(()=>closePanel(root,false),300)
  }

  function build(root,ei){
    const wrap=document.createElement('div');wrap.className='kggPainVertical';
    const toggle=document.createElement('button');toggle.type='button';toggle.className='kggPainVerticalToggle';toggle.setAttribute('aria-expanded','false');
    const label=document.createElement('span');label.className='kggPainVerticalLabel';
    const current=document.createElement('span');current.className='kggPainVerticalCurrent';
    const chevron=document.createElement('span');chevron.className='kggPainVerticalChevron';chevron.textContent='⌄';chevron.setAttribute('aria-hidden','true');
    toggle.append(label,current,chevron);
    const panel=document.createElement('div');panel.className='kggPainVerticalPanel';panel.hidden=true;
    const panelInner=document.createElement('div');panelInner.className='kggPainVerticalPanelInner';
    const stage=document.createElement('div');stage.className='kggPainVerticalStage';stage.tabIndex=0;stage.setAttribute('role','slider');stage.setAttribute('aria-valuemin','0');stage.setAttribute('aria-valuemax','10');stage.setAttribute('aria-orientation','vertical');
    const panelId=`kggPainVerticalPanel-${Date.now()}-${ei}-${Math.random().toString(36).slice(2,7)}`;panel.id=panelId;toggle.setAttribute('aria-controls',panelId);
    const track=document.createElement('div');track.className='kggPainVerticalTrack';
    const fill=document.createElement('div');fill.className='kggPainVerticalFill';
    const thumb=document.createElement('div');thumb.className='kggPainVerticalThumb';
    const values=document.createElement('div');values.className='kggPainVerticalValues';
    const rows=[];
    for(let n=MAX;n>=MIN;n--){const row=document.createElement('div');row.className='kggPainVerticalValue';row.dataset.kggPainValue=String(n);row.textContent=String(n);values.appendChild(row);rows.push(row)}
    stage.append(track,fill,thumb,values);panelInner.appendChild(stage);panel.appendChild(panelInner);
    const hint=document.createElement('div');hint.className='kggPainVerticalHint';panelInner.appendChild(hint);
    wrap.append(toggle,panel);root.appendChild(wrap);
    const state={ei,wrap,toggle,titleLabel:label,current,panel,stage,values:rows,hint,selected:false,committed:0,draft:0,gesture:null,keyboardDirty:false,closeTimer:0,row:null,oldLabel:null,labelHidden:false,rowHidden:false,rowAria:null,rowInert:false,rowDisplay:'',rowDisplayPriority:''};
    states.set(root,state);
    toggle.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();togglePanel(root)});
    wrap.addEventListener('click',event=>event.stopPropagation());
    stage.addEventListener('pointerdown',event=>{
      if(event.button!=null&&event.button!==0)return;
      event.preventDefault();event.stopPropagation();
      const exact=event.target.closest('[data-kgg-pain-value]');
      const rect=stage.getBoundingClientRect(),top=rect.top+ROW_HEIGHT/2,bottom=rect.bottom-ROW_HEIGHT/2;
      const next=exact?clampValue(exact.dataset.kggPainValue):valueFromY(top,bottom,event.clientY);
      state.gesture={pointerId:event.pointerId};stage.setPointerCapture&&stage.setPointerCapture(event.pointerId);updateVisual(state,next,true)
    });
    stage.addEventListener('pointermove',event=>{
      if(!state.gesture||state.gesture.pointerId!==event.pointerId)return;
      event.preventDefault();event.stopPropagation();
      const rect=stage.getBoundingClientRect();updateVisual(state,valueFromY(rect.top+ROW_HEIGHT/2,rect.bottom-ROW_HEIGHT/2,event.clientY),true)
    });
    stage.addEventListener('pointerup',event=>{
      if(!state.gesture||state.gesture.pointerId!==event.pointerId)return;
      event.preventDefault();event.stopPropagation();state.gesture=null;
      try{stage.releasePointerCapture&&stage.releasePointerCapture(event.pointerId)}catch(e){}
      commit(state,root,state.draft)
    });
    stage.addEventListener('pointercancel',event=>{if(!state.gesture)return;event.preventDefault();event.stopPropagation();state.gesture=null;updateVisual(state,state.committed,state.selected)});
    stage.addEventListener('keydown',event=>{
      let next=state.draft,handled=true;
      if(event.key==='ArrowUp'||event.key==='ArrowRight')next++;
      else if(event.key==='ArrowDown'||event.key==='ArrowLeft')next--;
      else if(event.key==='Home')next=MIN;
      else if(event.key==='End')next=MAX;
      else if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();commit(state,root,state.draft);state.keyboardDirty=false;return}
      else if(event.key==='Escape'){event.preventDefault();event.stopPropagation();state.keyboardDirty=false;closePanel(root,true);toggle.focus();return}
      else handled=false;
      if(handled){event.preventDefault();event.stopPropagation();state.keyboardDirty=true;updateVisual(state,next,true)}
    });
    stage.addEventListener('blur',()=>{if(state.keyboardDirty){state.keyboardDirty=false;updateVisual(state,state.committed,state.selected)}});
    return state
  }

  function teardown(root){
    const state=states.get(root);if(!state)return;
    if(openRoot===root)openRoot=null;clearTimeout(state.closeTimer);restoreOriginal(state);state.wrap.remove();root.classList.remove(ROOT_CLASS,OPEN_CLASS);states.delete(root)
  }
  function mountRoot(root,ei){
    const card=root.closest('.ex');
    const setMode=Boolean(card&&card.querySelector('.kggSetPain'))||root.classList.contains('kggHiddenGlobalPain')||root.style.display==='none';
    if(setMode){teardown(root);return}
    if(!originalReady(root)||typeof setPain!=='function')return;
    let state=states.get(root);if(!state){state=build(root,ei);root.classList.add(ROOT_CLASS)}else state.ei=ei;
    if(!hideOriginal(root,state)){teardown(root);return}
    refreshState(root,state)
  }
  function mountAll(){
    ensureStyle();
    const cards=[...document.querySelectorAll('#list .ex')];
    cards.forEach((card,ei)=>{const root=card.querySelector(':scope > .pain');if(root)mountRoot(root,ei)});
    if(openRoot&&!openRoot.isConnected)openRoot=null
  }
  function scheduleMount(delay=0){clearTimeout(mountTimer);mountTimer=setTimeout(mountAll,delay)}
  function observe(){
    const list=document.getElementById('list');if(!list)return;
    if(observer)observer.disconnect();observer=new MutationObserver(()=>scheduleMount(20));observer.observe(list,{childList:true,subtree:true,attributes:true,attributeFilter:['class']})
  }
  function init(){
    if(window.__kggPatientPainVertical===VERSION)return;window.__kggPatientPainVertical=VERSION;
    ensureStyle();observe();mountAll();setTimeout(()=>{observe();mountAll()},250);setTimeout(mountAll,900);
    document.addEventListener('click',event=>{
      if(event.target&&event.target.closest&&event.target.closest('#kggLangSwitch'))setTimeout(mountAll,0);
      if(openRoot&&!event.target.closest('.kggPainVertical'))closePanel(openRoot,true)
    },true);
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&openRoot)closePanel(openRoot,true)},true);
    addEventListener('resize',()=>scheduleMount(80),{passive:true});addEventListener('orientationchange',()=>scheduleMount(180),{passive:true})
  }
  if(window.__KGG_TEST__)window.__kggPainVerticalTest={clampValue,valueFromY,currentText};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
```
