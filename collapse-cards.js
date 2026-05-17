(function(){
  const STYLE_ID='kgg-collapse-cards-style';
  const BTN_ID='kgg-collapse-toggle';
  let collapsed=false;
  let openIndex=null;

  function injectStyle(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent=`
      #${BTN_ID}{position:fixed;left:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2500;width:56px;height:56px;border-radius:999px;border:1px solid #cbd5e1;background:#111827;color:#fff;box-shadow:0 12px 34px rgba(15,23,42,.28);font-size:24px;font-weight:950;display:flex;align-items:center;justify-content:center;touch-action:manipulation}
      #${BTN_ID}.on{background:#16a34a;border-color:#16a34a}
      body.kggCardsCollapsed .ex{cursor:pointer;transition:box-shadow .18s ease,transform .16s ease,background .18s ease}
      body.kggCardsCollapsed .ex:not(.kggOpen){padding:12px 14px;background:#fff}
      body.kggCardsCollapsed .ex:not(.kggOpen):active{transform:scale(.995)}
      body.kggCardsCollapsed .ex:not(.kggOpen) .set,body.kggCardsCollapsed .ex:not(.kggOpen) .pain{display:none!important}
      body.kggCardsCollapsed .ex:not(.kggOpen)::after{content:'Antippen zum Öffnen';display:block;margin-top:8px;color:#64748b;font-size:12px;font-weight:800}
      body.kggCardsCollapsed .ex.kggOpen{box-shadow:0 12px 32px rgba(15,23,42,.12);border-color:#111827}
      body.kggCardsCollapsed .ex.kggOpen::after{content:'Antippen zum Einklappen';display:block;margin-top:10px;color:#64748b;font-size:12px;font-weight:800}
      .pad{background:transparent!important;align-items:flex-end!important}
      .padBox{box-shadow:0 -10px 34px rgba(15,23,42,.16)!important;border:1px solid #dbe3ef!important}
      .padVal{display:none!important}
      .padTitle{margin-bottom:10px!important;font-size:14px!important}
      .num.kggEditing{outline:4px solid #111827!important;outline-offset:2px;background:#f8fafc!important}
      body.kggPadOpen{scroll-padding-bottom:520px}
      @media(max-width:430px){#${BTN_ID}{width:52px;height:52px;font-size:22px;left:12px;bottom:12px}.padGrid button,.padLast,.padOk,.padCancel{min-height:52px!important}body.kggPadOpen{scroll-padding-bottom:500px}}
    `;
    document.head.appendChild(s);
  }

  function ensureButton(){
    if(document.getElementById(BTN_ID)) return;
    const b=document.createElement('button');
    b.id=BTN_ID;
    b.type='button';
    b.title='Übungen ein-/ausklappen';
    b.textContent='☰';
    b.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      collapsed=!collapsed;
      if(!collapsed) openIndex=null;
      apply();
    });
    document.body.appendChild(b);
  }

  function getCards(){ return Array.from(document.querySelectorAll('#list .ex')); }

  function apply(){
    injectStyle();
    ensureButton();
    const btn=document.getElementById(BTN_ID);
    if(btn){
      btn.classList.toggle('on',collapsed);
      btn.textContent=collapsed?'▾':'☰';
      btn.setAttribute('aria-label',collapsed?'Alle Übungen ausklappen':'Übungen einklappen');
    }
    document.body.classList.toggle('kggCardsCollapsed',collapsed);
    getCards().forEach((card,idx)=>{
      card.dataset.kggExerciseIndex=String(idx);
      card.classList.toggle('kggOpen',collapsed && openIndex===idx);
      if(card.dataset.kggCollapseBound==='1') return;
      card.dataset.kggCollapseBound='1';
      card.addEventListener('click',function(ev){
        if(!collapsed) return;
        if(ev.target.closest('input,button,a,select,textarea')) return;
        const n=Number(card.dataset.kggExerciseIndex||idx);
        openIndex=openIndex===n?null:n;
        apply();
        if(openIndex===n) setTimeout(()=>card.scrollIntoView({behavior:'smooth',block:'start'}),30);
      });
    });
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

  function patchNumpad(){
    if(window.__kggNumpadUiFixDone) return;
    if(typeof window.openPad!=='function' || typeof window.closePad!=='function') return;
    window.__kggNumpadUiFixDone=true;

    let activeInput=null;
    let oldValue='';
    const oldOpen=window.openPad;
    const oldClose=window.closePad;

    const getVal=()=>{
      const v=document.getElementById('padVal');
      return v ? (v.textContent || '0') : '0';
    };
    const setVal=x=>{
      x=String(x||'0');
      const v=document.getElementById('padVal');
      if(v) v.textContent=x;
      if(activeInput) activeInput.value=x;
    };

    window.openPad=function(input,meta){
      injectStyle();
      if(activeInput) activeInput.classList.remove('kggEditing');
      activeInput=input;
      oldValue=input ? input.value : '';
      if(activeInput) activeInput.classList.add('kggEditing');
      document.body.classList.add('kggPadOpen');
      const result=oldOpen.apply(this,arguments);
      setVal(input && input.value ? input.value : '0');
      scrollInputAbovePad(input);
      return result;
    };

    window.padPress=function(x){
      let cur=getVal();
      if(cur==='0') cur='';
      if(x===',' && cur.includes(',')) return;
      if(cur.length>7) return;
      setVal((cur+x)||'0');
      scrollInputAbovePad(activeInput);
    };

    window.padBack=function(){
      let cur=getVal().slice(0,-1);
      setVal(cur||'0');
      scrollInputAbovePad(activeInput);
    };

    window.padUseLast=function(){
      const b=document.getElementById('padLast');
      const x=b && b.dataset ? b.dataset.value : '';
      if(x) setVal(x);
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

  function patchRender(){
    if(window.__kggCollapsePatchDone) return;
    window.__kggCollapsePatchDone=true;
    const oldRender=window.render;
    if(typeof oldRender==='function'){
      window.render=function(){
        const r=oldRender.apply(this,arguments);
        setTimeout(apply,0);
        setTimeout(patchNumpad,0);
        return r;
      };
    }
  }

  function init(){
    injectStyle();
    ensureButton();
    patchRender();
    patchNumpad();
    apply();
    setTimeout(apply,300);
    setTimeout(apply,1000);
    setTimeout(patchNumpad,300);
    setTimeout(patchNumpad,1000);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
