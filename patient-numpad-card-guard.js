(()=>{
  const VERSION='numpad-card-guard-v2-input-switch';
  if(window.__kggNumpadCardGuard===VERSION)return;
  window.__kggNumpadCardGuard=VERSION;
  let closedAt=0;
  const $=id=>document.getElementById(id);
  const pad=()=>$('pad');
  const open=()=>{const p=pad();return !!(p&&!p.classList.contains('hide'))};
  function mark(){document.body.classList.toggle('kggPadOpen',open())}
  function closePadOnly(){
    closedAt=Date.now();
    window.__kggPadClosedAt=closedAt;
    try{if(typeof closePad==='function')closePad(false)}catch(e){}
    setTimeout(mark,0);
  }
  function recent(){return Date.now()-(window.__kggPadClosedAt||closedAt||0)<450}
  function isNumInput(t){return !!(t&&t.closest&&t.closest('input.num'))}
  function guard(e){
    const p=pad();
    const t=e.target;
    if(!p||!t)return;
    if(isNumInput(t))return;
    if(t===p&&open()){
      e.preventDefault();
      e.stopPropagation();
      if(e.type==='click')closePadOnly();
      return;
    }
    if(t.closest&&t.closest('.ex')&&(open()||recent())){
      e.preventDefault();
      e.stopPropagation();
    }
  }
  function patch(){
    if(window.__kggNumpadCardGuardPatched)return;
    if(typeof openPad!=='function'||typeof closePad!=='function')return;
    window.__kggNumpadCardGuardPatched=1;
    const oldOpen=openPad,oldClose=closePad;
    window.openPad=function(){const r=oldOpen.apply(this,arguments);setTimeout(mark,0);return r};
    window.closePad=function(){const r=oldClose.apply(this,arguments);closedAt=Date.now();window.__kggPadClosedAt=closedAt;setTimeout(mark,0);return r};
  }
  function init(){
    patch();mark();
    document.addEventListener('pointerdown',guard,true);
    document.addEventListener('click',guard,true);
    setTimeout(patch,300);
    setTimeout(patch,1000);
  }
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
