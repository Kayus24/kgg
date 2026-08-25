# KGG Patient Source Chunk 023

- Source file: `patient-pain-vertical-scale.js`
- Characters: 24001-25077
- Full source SHA-256: `9001b6b24ce5f5b5e2b09e18ee17e6dde436426d9580f577bc33f75ee3c8cbcc`

```
untAll()},0)},true);
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
