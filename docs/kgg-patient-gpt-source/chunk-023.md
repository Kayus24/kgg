# KGG Patient Source Chunk 023

- Source file: `patient-pain-vertical-scale.js`
- Characters: 24001-30485
- Full source SHA-256: `5668ab6f68630dbf65510bb8855388be2d3e3a1b8624e3b9ae77d4bdbb3b3b89`

```
ation();closeModal()});
      overlay.addEventListener('keydown',modalKeydown,true);bindStage();refreshLanguage();return true
    }catch(e){safe(()=>document.getElementById(MODAL_ID)?.remove());modal=null;return false}
  }

  function buildCompact(root,ei,setIndex=0){
    const wrap=document.createElement('div');wrap.className='kggPainVertical';
    const toggle=document.createElement('button');toggle.type='button';toggle.className='kggPainVerticalToggle';toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-controls',MODAL_ID);
    const icon=document.createElement('span');icon.className='kggPainVerticalIcon';icon.setAttribute('aria-hidden','true');icon.innerHTML='<svg viewBox="0 0 48 30" focusable="false"><rect class="kggPainIconCapsule" x="0.75" y="0.75" width="46.5" height="28.5" rx="14.25" fill="#F8F9FB" stroke="#8E9EC0" stroke-width="1.5"/><path class="kggPainBolt" d="M13.8 7.2 9.6 13.2l3.1.8-1.5 4.5 6.9-7-3.5-.9 2-3.4Z" fill="#FCD08F"/><path class="kggPainBolt" d="M23.6 4.2 20 14h3.4l-1.5 11.5 6.7-13h-3.8l2.3-8.3Z" fill="#FCD08F"/><path class="kggPainBolt" d="M35.7 7.7 30.3 14.1l3.3.8-4.2 7 9.6-8-3.5-.9 3.1-3.5Z" fill="#FCD08F"/></svg>';
    const label=document.createElement('span');label.className='kggPainVerticalLabel';
    const current=document.createElement('span');current.className='kggPainVerticalCurrent';
    const compact=document.createElement('span');compact.className='kggPainCompactText';compact.setAttribute('aria-hidden','true');
    const chevron=document.createElement('span');chevron.className='kggPainVerticalChevron';chevron.textContent='⌄';chevron.setAttribute('aria-hidden','true');
    toggle.append(icon,label,current,compact,chevron);wrap.appendChild(toggle);root.appendChild(wrap);
    const state={ei,s:setIndex,wrap,toggle,label,current,compact,selected:false,committed:0,row:null,oldLabel:null,labelHidden:false,rowHidden:false,rowAria:null,rowInert:false,rowDisplay:'',rowDisplayPriority:''};
    states.set(root,state);
    toggle.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();toggleModal(root)});
    wrap.addEventListener('click',event=>event.stopPropagation());return state
  }
  function refreshState(root,state){
    const stored=readStored(state.ei,state.s);setText(state.label,labelText(state.s));updateCompact(state,stored.selected,stored.value)
  }
  function teardown(root){
    const state=states.get(root);if(!state)return;
    if(activeRoot===root)closeModal({returnFocus:false});restoreOriginal(state);state.wrap.remove();root.classList.remove(ROOT_CLASS);states.delete(root)
  }
  function exercisePainMode(ei){
    const ex=safe(()=>p&&Array.isArray(p.ex)?p.ex[ei]:null);
    const runtimeMode=String(ex&&ex.painMode||'').toLowerCase();
    if(runtimeMode)return runtimeMode;
    const settings=safe(()=>JSON.parse(localStorage.getItem('kggPatientExerciseSettingsV1')||'{}'))||{};
    const planId=String(safe(()=>p.id)||'plan'),name=String(ex&&ex.n||'exercise');
    const saved=settings[(planId+'|'+name).toLowerCase()];
    return String(saved&&saved.painMode||'exercise').toLowerCase()
  }
  function mountRoot(root,ei){
    const card=root.closest('.ex');
    const setMode=exercisePainMode(ei)==='set'||Boolean(card&&card.querySelector('.kggSetPain'))||root.classList.contains('kggHiddenGlobalPain')||root.style.display==='none';
    if(setMode){teardown(root);return}
    if(!originalReady(root)||typeof setPain!=='function'||!ensureModal())return;
    let state=states.get(root);if(!state){state=buildCompact(root,ei);root.classList.add(ROOT_CLASS)}else state.ei=ei;
    if(!hideOriginal(root,state)){teardown(root);return}refreshState(root,state)
  }
  function mountSetRoot(root,ei,setIndex){
    if(!originalReady(root)||!ensureModal())return;
    let state=states.get(root);if(!state){state=buildCompact(root,ei,setIndex);root.classList.add(ROOT_CLASS)}else{state.ei=ei;state.s=setIndex}
    if(!hideOriginal(root,state)){teardown(root);return}refreshState(root,state)
  }
  function mountAll(){
    ensureStyle();ensureModal();
    const cards=[...document.querySelectorAll('#list .ex')];
    cards.forEach((card,ei)=>{const root=card.querySelector(':scope > .pain');if(root)mountRoot(root,ei);card.querySelectorAll(':scope > .set > .kggSetPain').forEach(setRoot=>{const scale=setRoot.querySelector(':scope > .kggPainScale');const setIndex=Number(scale&&scale.dataset.s);if(Number.isInteger(setIndex)&&setIndex>0)mountSetRoot(setRoot,ei,setIndex)})});
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
```
