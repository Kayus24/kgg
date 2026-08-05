# KGG Patient Source Chunk 021

- Source file: `patient-pain-vertical-scale.js`
- Characters: 24001-24859
- Full source SHA-256: `42cfb5f6f2473265c4d7d4c17b71d978c2feb01c1f1ecca7c15316b26f73f3ac`

```
50].forEach(delay=>setTimeout(()=>{observe();mountAll()},delay));
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
