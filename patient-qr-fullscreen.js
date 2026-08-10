(()=>{
  const VERSION='qr-fullscreen-v1-high-contrast';
  if(window.__kggQrFullscreen===VERSION)return;
  window.__kggQrFullscreen=VERSION;
  let wakeLock=null;
  const $=id=>document.getElementById(id);
  function ensureStyle(){
    if($('kggQrFullscreenStyle'))return;
    const s=document.createElement('style');
    s.id='kggQrFullscreenStyle';
    s.textContent=`
      #qr img{cursor:zoom-in}
      .kggQrFull{position:fixed;inset:0;z-index:30000;background:#fff;color:#000;display:flex;align-items:center;justify-content:center;padding:8px;box-sizing:border-box;touch-action:manipulation}
      .kggQrFull img{width:min(96vw,96vh);height:min(96vw,96vh);object-fit:contain;background:#fff;image-rendering:pixelated;image-rendering:crisp-edges;filter:contrast(120%)}
      .kggQrFull button{position:fixed;top:calc(10px + env(safe-area-inset-top));right:10px;width:46px;height:46px;border:3px solid #000;border-radius:999px;background:#fff;color:#000;font-size:28px;font-weight:950;line-height:1}
      .kggQrFull .hint{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom));text-align:center;font-size:14px;font-weight:900;color:#000;background:#fff;padding:4px 8px}
      @media(max-width:430px){.kggQrFull{padding:4px}.kggQrFull img{width:min(98vw,92vh);height:min(98vw,92vh)}}
    `;
    document.head.appendChild(s);
  }
  async function lockScreen(){
    try{if('wakeLock'in navigator)wakeLock=await navigator.wakeLock.request('screen')}catch(e){}
  }
  async function unlockScreen(){
    try{if(wakeLock&&wakeLock.release)await wakeLock.release()}catch(e){}
    wakeLock=null;
  }
  function close(){
    const el=$('kggQrFull');
    if(el)el.remove();
    unlockScreen();
    document.removeEventListener('keydown',onKey,true);
    try{if(document.fullscreenElement)document.exitFullscreen()}catch(e){}
  }
  function onKey(e){if(e.key==='Escape')close()}
  function open(src){
    if(!src)return;
    ensureStyle();
    close();
    const el=document.createElement('div');
    el.id='kggQrFull';
    el.className='kggQrFull';
    el.innerHTML='<button type="button" aria-label="Schließen">×</button><img src="'+String(src).replace(/"/g,'&quot;')+'" alt="QR-Code"><div class="hint">QR groß anzeigen · Zum Schließen tippen</div>';
    el.addEventListener('click',e=>{if(e.target===el)close()});
    el.querySelector('button').addEventListener('click',e=>{e.preventDefault();e.stopPropagation();close()});
    document.body.appendChild(el);
    document.addEventListener('keydown',onKey,true);
    lockScreen();
    try{if(el.requestFullscreen)el.requestFullscreen().catch(()=>{})}catch(e){}
  }
  function bind(){
    ensureStyle();
    if(window.__kggQrFullscreenBound)return;
    window.__kggQrFullscreenBound=1;
    document.addEventListener('click',e=>{
      const img=e.target&&e.target.closest?e.target.closest('#qr img'):null;
      if(!img)return;
      e.preventDefault();
      e.stopPropagation();
      open(img.src);
    },true);
  }
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',bind):bind();
})();
