(()=>{
  const VERSION='numpad-visibility-v2';
  if(window.__kggNumpadVisibility===VERSION)return;
  window.__kggNumpadVisibility=VERSION;
  const $=id=>document.getElementById(id);
  let activeInput=null;
  function pad(){return $('pad')}
  function box(){const p=pad();return p?p.querySelector('.padBox'):null}
  function open(){const p=pad();return !!(p&&!p.classList.contains('hide'))}
  function h(){const b=box();return open()&&b?Math.max(320,Math.ceil(b.getBoundingClientRect().height||0)):0}
  function css(){if($('kggNumpadVisibilityStyle'))return;const s=document.createElement('style');s.id='kggNumpadVisibilityStyle';s.textContent='body.kggPadOpen main{scroll-padding-bottom:55vh!important}#pad.kggPadPass{pointer-events:none!important;background:transparent!important}#pad.kggPadPass .padBox{pointer-events:auto!important}';document.head.appendChild(s)}
  function space(){css();const ph=h();const main=document.querySelector('main');if(main)main.style.paddingBottom=ph?Math.ceil(ph+120)+'px':'';document.body.classList.toggle('kggPadOpen',!!ph);const p=pad();if(p)p.classList.toggle('kggPadPass',!!ph)}
  function move(){if(!activeInput||!open())return;space();const ph=h();const r=activeInput.getBoundingClientRect();const vv=window.visualViewport;const bottom=(vv?vv.height+vv.offsetTop:window.innerHeight)-ph-28;let dy=0;if(r.bottom>bottom)dy=r.bottom-bottom;if(r.top<18)dy=r.top-18;if(Math.abs(dy)>1)window.scrollBy({top:dy,left:0,behavior:'smooth'})}
  function ensure(){[20,90,180,360,650].forEach(t=>setTimeout(move,t))}
  function clearSoon(){setTimeout(()=>{const main=document.querySelector('main');if(main)main.style.paddingBottom='';document.body.classList.remove('kggPadOpen');const p=pad();if(p)p.classList.remove('kggPadPass');activeInput=null},120)}
  function patch(){if(window.__kggNumpadVisibilityPatchedV2)return;window.__kggNumpadVisibilityPatchedV2=1;if(typeof window.openPad==='function'){const oldOpen=window.openPad;window.openPad=function(input,meta){if(open()&&input&&input!==activeInput&&typeof window.closePad==='function'){try{window.closePad(true)}catch(e){}}activeInput=input||document.activeElement;const r=oldOpen.apply(this,arguments);space();ensure();return r}}if(typeof window.closePad==='function'){const oldClose=window.closePad;window.closePad=function(){const r=oldClose.apply(this,arguments);clearSoon();return r}}}
  document.addEventListener('focusin',e=>{if(e.target&&e.target.matches&&e.target.matches('input.num')){activeInput=e.target;if(open())ensure()}},true);
  document.addEventListener('click',e=>{if(e.target&&e.target.matches&&e.target.matches('input.num')){activeInput=e.target;if(open())ensure()}},true);
  if(window.visualViewport)visualViewport.addEventListener('resize',ensure);
  addEventListener('orientationchange',()=>setTimeout(ensure,250));
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',patch):patch();
  setTimeout(patch,500);setTimeout(patch,1500);
})();
