(function(){
  const STYLE_ID='kgg-numpad-ui-fix-style';
  let activeInput=null;
  let oldValue='';

  function $(id){return document.getElementById(id)}

  function injectStyle(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent=`
      .pad{background:transparent!important;align-items:flex-end!important}
      .padBox{box-shadow:0 -10px 34px rgba(15,23,42,.16)!important;border:1px solid #dbe3ef!important}
      .padVal{display:none!important}
      .padTitle{margin-bottom:10px!important;font-size:14px!important}
      .num.kggEditing{outline:4px solid #111827!important;outline-offset:2px;background:#f8fafc!important}
      body.kggPadOpen{scroll-padding-bottom:520px}
      @media(max-width:430px){body.kggPadOpen{scroll-padding-bottom:500px}}
    `;
    document.head.appendChild(s);
  }

  function getCurrentValue(){
    const v=$('padVal');
    return v ? (v.textContent || '0') : '0';
  }

  function setCurrentValue(x){
    x=String(x||'0');
    const v=$('padVal');
    if(v) v.textContent=x;
    if(activeInput) activeInput.value=x;
  }

  function scrollInputAbovePad(input){
    setTimeout(()=>{
      if(!input) return;
      const padBox=document.querySelector('.padBox');
      const padTop=padBox ? padBox.getBoundingClientRect().top : window.innerHeight*0.55;
      const r=input.getBoundingClientRect();
      const safeTop=84;
      const safeBottom=padTop-28;
      let delta=0;
      if(r.bottom>safeBottom) delta=r.bottom-safeBottom;
      if(r.top<safeTop) delta=r.top-safeTop;
      if(delta!==0) window.scrollBy({top:delta,behavior:'smooth'});
    },90);
  }

  function patch(){
    if(window.__kggNumpadUiFixDone) return;
    if(typeof window.openPad!=='function') return;
    window.__kggNumpadUiFixDone=true;

    const oldOpen=window.openPad;
    const oldClose=window.closePad;

    window.openPad=function(input,meta){
      injectStyle();
      if(activeInput) activeInput.classList.remove('kggEditing');
      activeInput=input;
      oldValue=input ? input.value : '';
      if(activeInput) activeInput.classList.add('kggEditing');
      document.body.classList.add('kggPadOpen');
      const result=oldOpen.apply(this,arguments);
      setCurrentValue(input && input.value ? input.value : '0');
      scrollInputAbovePad(input);
      return result;
    };

    window.padPress=function(x){
      let cur=getCurrentValue();
      if(cur==='0') cur='';
      if(x===',' && cur.includes(',')) return;
      if(cur.length>7) return;
      setCurrentValue((cur+x)||'0');
      scrollInputAbovePad(activeInput);
    };

    window.padBack=function(){
      let cur=getCurrentValue();
      cur=cur.slice(0,-1);
      setCurrentValue(cur||'0');
      scrollInputAbovePad(activeInput);
    };

    window.padUseLast=function(){
      const b=$('padLast');
      const x=b && b.dataset ? b.dataset.value : '';
      if(x) setCurrentValue(x);
      scrollInputAbovePad(activeInput);
    };

    window.closePad=function(ok){
      if(!ok && activeInput) activeInput.value=oldValue;
      const result=oldClose.apply(this,arguments);
      if(activeInput) activeInput.classList.remove('kggEditing');
      activeInput=null;
      oldValue='';
      document.body.classList.remove('kggPadOpen');
      return result;
    };
  }

  function init(){
    injectStyle();
    patch();
    setTimeout(patch,300);
    setTimeout(patch,1000);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
