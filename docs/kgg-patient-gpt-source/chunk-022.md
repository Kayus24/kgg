# KGG Patient Source Chunk 022

- Source file: `patient-pain-vertical-scale.js`
- Characters: 24001-27768
- Full source SHA-256: `aeb8d022a6630c76de16e9d4ddb4a2d5f241e65ac86225667d4fce817f3dcc8c`

```
ropagation();toggleModal(root)});
    wrap.addEventListener('click',event=>event.stopPropagation());return state
  }
  function refreshState(root,state){
    const stored=readStored(state.ei);setText(state.label,labelText());updateCompact(state,stored.selected,stored.value)
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
```
