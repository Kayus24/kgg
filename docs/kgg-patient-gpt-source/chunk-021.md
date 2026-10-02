# KGG Patient Source Chunk 021

- Source file: `patient-pain-vertical-scale.js`
- Characters: 24001-26299
- Full source SHA-256: `7badcbef42a306879ff15b198075d6dbd3ced561653bbb3977f8093fe804c73a`

```
lassList.add(ROOT_CLASS)}else state.ei=ei;
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
