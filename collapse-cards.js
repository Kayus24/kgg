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
      @media(max-width:430px){#${BTN_ID}{width:52px;height:52px;font-size:22px;left:12px;bottom:12px}}
    `;
    document.head.appendChild(s);
  }

  function ensureButton(){
    if(document.getElementById(BTN_ID)) return;
    const b=document.createElement('button');
    b.id=BTN_ID;
    b.type='button';
    b.title='Übungen ein-/ausklappen';
    b.textContent='▤';
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
      btn.textContent=collapsed?'▥':'▤';
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

  function patchRender(){
    if(window.__kggCollapsePatchDone) return;
    window.__kggCollapsePatchDone=true;
    const oldRender=window.render;
    if(typeof oldRender==='function'){
      window.render=function(){
        const r=oldRender.apply(this,arguments);
        setTimeout(apply,0);
        return r;
      };
    }
  }

  function init(){
    injectStyle();
    ensureButton();
    patchRender();
    apply();
    setTimeout(apply,300);
    setTimeout(apply,1000);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
