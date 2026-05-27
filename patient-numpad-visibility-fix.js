(()=>{
  const VERSION='numpad-visibility-v1';
  if(window.__kggNumpadVisibility===VERSION)return;
  window.__kggNumpadVisibility=VERSION;
  const $=id=>document.getElementById(id);
  let activeInput=null;
  function padHeight(){const p=$('pad');return p&&!p.classList.contains('hide')?Math.max(260,p.getBoundingClientRect().height||0):0}
  function applyPadding(){const h=padHeight();const main=document.querySelector('main');if(main)main.style.paddingBottom=h?Math.ceil(h+28)+'px':'';document.body.classList.toggle('kggPadOpen',!!h)}
  function ensureVisible(){if(!activeInput)return;applyPadding();setTimeout(()=>{try{activeInput.scrollIntoView({block:'center',behavior:'smooth'})}catch(e){activeInput.scrollIntoView(false)}},30);setTimeout(()=>{try{activeInput.scrollIntoView({block:'center',behavior:'auto'})}catch(e){}},160)}
  function patch(){if(window.__kggNumpadVisibilityPatched)return;window.__kggNumpadVisibilityPatched=1;if(typeof window.openPad==='function'){const old=window.openPad;window.openPad=function(input,meta){activeInput=input||document.activeElement;const r=old.apply(this,arguments);ensureVisible();return r}}if(typeof window.closePad==='function'){const oldClose=window.closePad;window.closePad=function(){const r=oldClose.apply(this,arguments);setTimeout(()=>{const main=document.querySelector('main');if(main)main.style.paddingBottom='';document.body.classList.remove('kggPadOpen');activeInput=null},80);return r}}}
  document.addEventListener('focusin',e=>{if(e.target&&e.target.matches&&e.target.matches('input.num'))activeInput=e.target},true);
  if(window.visualViewport)visualViewport.addEventListener('resize',ensureVisible);
  addEventListener('orientationchange',()=>setTimeout(ensureVisible,250));
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',patch):patch();
  setTimeout(patch,500);setTimeout(patch,1500);
})();
