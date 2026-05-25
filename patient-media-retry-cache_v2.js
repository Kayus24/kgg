(()=>{
  const VERSION='v3_media_prefetch_all';
  const STYLE='kggPatientMediaStyle';
  const DB='kgg_patient_media_v1';
  const STORE='images';
  const PLAN_KEY='kggCurrentPlanV1';
  const RETRY_MS=240000;
  const STEP_MS=4000;
  const loading=new Set();
  const objectUrls=new Map();
  let patched=false;
  let scheduled=false;
  let observeTimer=null;
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const safe=fn=>{try{return fn()}catch(err){return null}};

  function ensureStyle(){
    if($(STYLE))return;
    const style=document.createElement('style');
    style.id=STYLE;
    style.textContent=`
      .kggMediaList{display:grid;gap:8px;margin-top:12px}
      .kggMediaBox{border:1px solid #dbe3ef;border-radius:14px;background:#f8fafc;padding:10px;color:#334155;font-weight:800}
      .kggMediaBox small{display:block;margin-top:4px;color:#64748b;font-size:12px;line-height:1.35}
      .kggMediaBox img{display:block;width:100%;max-height:320px;object-fit:contain;border-radius:12px;background:#fff}
      .kggMediaBox.ready{background:#fff}.kggMediaBox.error{background:#fffbeb;border-color:#fde68a;color:#92400e}
      body.kggAlwaysCollapsed .ex:not(.kggOpen) .kggMediaList{display:none!important}
    `;
    document.head.appendChild(style);
  }
  function b64Bytes(value){
    let text=String(value||'').replace(/-/g,'+').replace(/_/g,'/');
    while(text.length%4)text+='=';
    const bin=atob(text);
    const bytes=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    return bytes;
  }
  function decodeKggH2Payload(){
    const hash=String(location.hash||'').slice(1);
    if(!hash.startsWith('KGGH2:'))return null;
    const encoded=hash.slice(6).replace(/-/g,'+').replace(/_/g,'/');
    const padded=encoded+'='.repeat((4-encoded.length%4)%4);
    return JSON.parse(decodeURIComponent(escape(atob(padded))));
  }
  function rawExerciseToRuntime(item){
    if(!Array.isArray(item))return item||{};
    const media=Array.isArray(item[7])?item[7]:(item[7]?[item[7]]:[]);
    return {
      n:item[0]||'Uebung',
      sets:Number(item[1])||3,
      side:item[2]||'BI',
      u:item[3]||'kg',
      m:item[4]||'Wdh',
      sl:item[5]||'',
      sm:item[6]||'',
      media
    };
  }
  function storedPlan(){
    const saved=safe(()=>JSON.parse(localStorage.getItem(PLAN_KEY)||'null'));
    return saved&&saved.plan?saved.plan:null;
  }
  function planExercises(){
    const runtime=safe(()=>typeof p!=='undefined'&&p&&Array.isArray(p.ex)?p.ex:null);
    if(runtime)return runtime;
    const custom=safe(()=>window.KGGPatientPlan&&typeof window.KGGPatientPlan.getExercises==='function'?window.KGGPatientPlan.getExercises():null);
    if(Array.isArray(custom))return custom;
    const raw=decodeKggH2Payload()||storedPlan();
    if(raw&&Array.isArray(raw.e))return raw.e.map(rawExerciseToRuntime);
    if(raw&&Array.isArray(raw.ex))return raw.ex;
    if(raw&&Array.isArray(raw.plan))return raw.plan;
    return [];
  }
  function openDb(){
    return new Promise((resolve,reject)=>{
      if(!('indexedDB' in window)){reject(new Error('Lokaler Bildspeicher nicht verfuegbar'));return;}
      const req=indexedDB.open(DB,1);
      req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'});};
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Lokaler Bildspeicher nicht verfuegbar'));
    });
  }
  async function getCached(id){
    const db=await openDb();
    return new Promise(resolve=>{
      const tx=db.transaction(STORE,'readonly');
      const req=tx.objectStore(STORE).get(id);
      req.onsuccess=()=>resolve(req.result||null);
      req.onerror=()=>resolve(null);
    });
  }
  async function putCached(record){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readwrite');
      tx.objectStore(STORE).put(record);
      tx.oncomplete=()=>resolve(record);
      tx.onerror=()=>reject(tx.error||new Error('Bild konnte nicht lokal gespeichert werden'));
    });
  }
  function mediaList(ex){
    const media=ex&&ex.media;
    if(Array.isArray(media))return media.filter(item=>item&&item.type!=='video');
    if(media&&typeof media==='object')return [media];
    return [];
  }
  function mediaId(item,exerciseIndex,mediaIndex){
    return String(item&&item.id||'media_'+exerciseIndex+'_'+mediaIndex);
  }
  function mediaBox(id){
    const target=String(id);
    return [...document.querySelectorAll('[data-kgg-media-id]')].find(node=>node.getAttribute('data-kgg-media-id')===target)||null;
  }
  function setBox(id,html,cls){
    const box=mediaBox(id);
    if(!box)return;
    box.className='kggMediaBox '+(cls||'');
    box.innerHTML=html;
  }
  function objectUrl(id,blob){
    const old=objectUrls.get(id);
    if(old)URL.revokeObjectURL(old);
    const url=URL.createObjectURL(blob);
    objectUrls.set(id,url);
    return url;
  }
  async function fetchEncrypted(item){
    if(window.KGGPatientMediaFetchAdapter&&typeof window.KGGPatientMediaFetchAdapter.fetch==='function')return window.KGGPatientMediaFetchAdapter.fetch(item);
    if(!item.downloadUrl)throw new Error('Bild ist noch nicht bereit');
    const res=await fetch(item.downloadUrl,{cache:'no-store'});
    if(!res.ok)throw new Error('Bild konnte nicht geladen werden');
    return res.blob();
  }
  async function decryptMedia(item,encryptedBlob){
    if(!window.crypto||!crypto.subtle)throw new Error('Verschluesselung wird von diesem Browser nicht unterstuetzt');
    const info=item.crypto||{};
    if(!info.key||!info.iv)throw new Error('Bildschluessel fehlt');
    const key=await crypto.subtle.importKey('raw',b64Bytes(info.key),{name:'AES-GCM'},false,['decrypt']);
    const encrypted=await encryptedBlob.arrayBuffer();
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64Bytes(info.iv)},key,encrypted);
    return new Blob([plain],{type:item.mime||'image/jpeg'});
  }
  async function loadMedia(item,exerciseIndex,mediaIndex){
    const id=mediaId(item,exerciseIndex,mediaIndex);
    const cached=await getCached(id).catch(()=>null);
    if(cached&&cached.blob){
      const url=objectUrl(id,cached.blob);
      setBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
      return true;
    }
    const encrypted=await fetchEncrypted(item);
    const blob=await decryptMedia(item,encrypted);
    await putCached({id,blob,mime:item.mime||'image/jpeg',savedAt:new Date().toISOString()}).catch(()=>null);
    const url=objectUrl(id,blob);
    setBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
    return true;
  }
  function retryMedia(item,exerciseIndex,mediaIndex){
    const id=mediaId(item,exerciseIndex,mediaIndex);
    if(loading.has(id))return;
    loading.add(id);
    const retryMs=Math.max(10000,Number(item.retrySeconds||0)*1000||RETRY_MS);
    const until=Date.now()+retryMs;
    const tick=async()=>{
      try{await loadMedia(item,exerciseIndex,mediaIndex);loading.delete(id);}
      catch(err){
        if(Date.now()<until){
          setBox(id,'<span>Bild wird geladen ...</span><small>Die App versucht es automatisch erneut.</small>','loading');
          setTimeout(tick,STEP_MS);
        }else{
          loading.delete(id);
          setBox(id,'<span>Bild konnte nicht geladen werden.</span><small>Der Trainingsplan bleibt ohne Bild nutzbar. Bitte bei Bedarf neuen QR-Code erstellen lassen.</small>','error');
        }
      }
    };
    tick();
  }
  function prefetchAllMedia(){
    const exercises=planExercises();
    let found=false;
    exercises.forEach((ex,exerciseIndex)=>{
      mediaList(ex).forEach((item,mediaIndex)=>{
        found=true;
        retryMedia(item,exerciseIndex,mediaIndex);
      });
    });
    return found;
  }
  function renderMedia(){
    ensureStyle();
    const exercises=planExercises();
    const hasPrefetch=prefetchAllMedia();
    const cards=[...document.querySelectorAll('#list .ex')];
    if(!cards.length||!exercises.length)return hasPrefetch;
    cards.forEach((card,exerciseIndex)=>{
      const media=mediaList(exercises[exerciseIndex]);
      const ids=media.map((item,mediaIndex)=>mediaId(item,exerciseIndex,mediaIndex)).join('|');
      const existing=card.querySelector('.kggMediaList');
      if(!media.length){
        if(existing)existing.remove();
        delete card.dataset.kggMediaIds;
        return;
      }
      if(existing&&card.dataset.kggMediaIds===ids){
        media.forEach((item,mediaIndex)=>retryMedia(item,exerciseIndex,mediaIndex));
        return;
      }
      if(existing)existing.remove();
      card.dataset.kggMediaIds=ids;
      const wrap=document.createElement('div');
      wrap.className='kggMediaList';
      wrap.innerHTML=media.map((item,mediaIndex)=>{
        const id=mediaId(item,exerciseIndex,mediaIndex);
        return '<div class="kggMediaBox loading" data-kgg-media-id="'+esc(id)+'"><span>Bild wird geladen ...</span><small>Verschluesselte Datei wird geholt und lokal gespeichert.</small></div>';
      }).join('');
      const firstSet=card.querySelector('.set');
      if(firstSet)card.insertBefore(wrap,firstSet); else card.appendChild(wrap);
      media.forEach((item,mediaIndex)=>retryMedia(item,exerciseIndex,mediaIndex));
    });
    return true;
  }
  function scheduleRender(delay){
    if(scheduled)return;
    scheduled=true;
    setTimeout(()=>{scheduled=false;renderMedia();},delay||40);
  }
  function patchRender(){
    if(patched||typeof render!=='function')return false;
    patched=true;
    window.__kggPatientMediaPatch=VERSION;
    const old=render;
    render=function(){const result=old.apply(this,arguments);scheduleRender(30);return result;};
    return true;
  }
  function observeList(){
    const list=$('list');
    if(!list||!('MutationObserver' in window))return;
    const observer=new MutationObserver(()=>scheduleRender(60));
    observer.observe(list,{childList:true,subtree:false});
  }
  function init(){
    ensureStyle();
    patchRender();
    observeList();
    [60,300,900,1800,3200].forEach(delay=>setTimeout(()=>{patchRender();prefetchAllMedia();renderMedia();},delay));
    observeTimer=setInterval(()=>{
      if(patchRender()||prefetchAllMedia()||renderMedia())clearInterval(observeTimer);
    },1200);
    setTimeout(()=>{if(observeTimer)clearInterval(observeTimer);},12000);
  }
  window.KGGPatientMediaRetryCache={version:VERSION,render:renderMedia,prefetch:prefetchAllMedia,planExercises};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
