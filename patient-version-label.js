(()=>{
  const ID='kggAppVersion';

  function fallbackVersion(){
    try{
      const src=document.currentScript&&document.currentScript.src?document.currentScript.src:'';
      const raw=new URL(src||location.href,location.href).searchParams.get('v')||'';
      return raw?'v'+String(raw).replace(/^v/i,''):'v?';
    }catch(e){
      return 'v?';
    }
  }

  async function resolveVersion(){
    const fallback=fallbackVersion();
    if(!('caches' in window)) return fallback;
    try{
      const keys=await caches.keys();
      let best=0;
      for(const key of keys){
        const match=String(key).match(/^kgg-handyplan-v(\d+)(?:-|$)/i);
        const n=match?Number(match[1]):0;
        if(n>best) best=n;
      }
      return best?'v'+best:fallback;
    }catch(e){
      return fallback;
    }
  }

  function mount(version){
    let el=document.getElementById(ID);
    if(!el){
      el=document.createElement('div');
      el.id=ID;
      const main=document.querySelector('main');
      if(main) main.insertAdjacentElement('afterend',el);
      else document.body.appendChild(el);
    }
    el.textContent=version;
    el.title='KGG App-Version '+version;
    el.setAttribute('aria-label','KGG App-Version '+version);
    el.style.cssText='max-width:760px;margin:-4px auto 0;padding:0 14px calc(10px + env(safe-area-inset-bottom));text-align:right;font:500 10px/1.2 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#94a3b8;letter-spacing:.02em;user-select:text;';
  }

  async function init(){
    mount(await resolveVersion());
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
