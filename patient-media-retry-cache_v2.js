(()=>{
  const VERSION='v9_open_card_image_lightbox';
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
  let mediaBundlePromise=null;
  let lightboxBound=false;
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
      .ex.kggOpen .kggMediaBox img{cursor:zoom-in}
      .kggMediaBox.ready{background:#fff}.kggMediaBox.error{background:#fffbeb;border-color:#fde68a;color:#92400e}
      body.kggAlwaysCollapsed .ex:not(.kggOpen) .kggMediaList{display:none!important}
      #list .ex.kggHasThumb{position:relative;min-height:122px;padding-right:136px}
      #list .ex.kggHasThumb.kggOpen{padding-right:12px}
      #list .ex .kggCardThumb{position:absolute;right:12px;top:50%;width:104px;height:86px;transform:translateY(-50%);border:1px solid #dbe3ef;border-radius:16px;background:#f8fafc;box-shadow:0 7px 18px rgba(15,23,42,.08);overflow:hidden;display:none;pointer-events:none}
      #list .ex .kggCardThumb img{display:block;width:100%;height:100%;object-fit:cover;background:#fff;cursor:default}
      #list .ex:not(.kggOpen).kggThumbReady .kggCardThumb{display:block}
      #list .ex.kggOpen .kggCardThumb{display:none!important}
      .kggImageLightbox{position:fixed;inset:0;z-index:25000;background:rgba(15,23,42,.88);display:flex;align-items:center;justify-content:center;padding:18px;backdrop-filter:blur(2px)}
      .kggImageLightbox img{max-width:96vw;max-height:88vh;object-fit:contain;border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.35)}
      .kggImageLightbox button{position:fixed;top:calc(12px + env(safe-area-inset-top));right:14px;width:48px;height:48px;border:0;border-radius:999px;background:#fff;color:#111827;font-size:26px;font-weight:950;box-shadow:0 12px 32px rgba(0,0,0,.25)}
      @media(max-width:430px){#list .ex.kggHasThumb{padding-right:106px;min-height:112px}#list .ex .kggCardThumb{width:78px;height:68px;right:10px;border-radius:13px}.kggImageLightbox{padding:10px}.kggImageLightbox img{max-width:98vw;max-height:84vh;border-radius:14px}}
    `;
    document.head.appendChild(style);
  }
  function b64Bytes(value){let text=String(value||'').replace(/-/g,'+').replace(/_/g,'/');while(text.length%4)text+='=';const bin=atob(text);const bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return bytes;}
  function decodeKggH2Payload(){const hash=String(location.hash||'').slice(1);if(!hash.startsWith('KGGH2:'))return null;const encoded=hash.slice(6).replace(/-/g,'+').replace(/_/g,'/');const padded=encoded+'='.repeat((4-encoded.length%4)%4);return JSON.parse(decodeURIComponent(escape(atob(padded))));}
  function looksLikeMediaString(value){const s=String(value||'').trim();if(!s)return false;if(/^https?:\/\//i.test(s))return true;if(/^data:image\//i.test(s))return true;if(/^media[_-]/i.test(s))return true;if(/^img[_-]/i.test(s))return true;if(/^m[0-9a-z_-]{6,}$/i.test(s))return true;return false;}
  function isRealMediaItem(item){if(!item)return false;if(typeof item==='string')return looksLikeMediaString(item);if(typeof item!=='object')return false;if(item.type==='video')return false;if(item.downloadUrl||item.data||item.src||item.url||item.imageUrl||item.blobUrl)return true;if(item.id&&String(item.id).trim()&&(item.bundleRef||item.crypto||item.mime||item.type==='image'))return true;return false;}
  function rawExerciseToRuntime(item){
    if(!Array.isArray(item))return item||{};
    const raw=Array.isArray(item[7])?item[7]:(isRealMediaItem(item[7])?[item[7]]:[]);
    const media=raw.map(entry=>typeof entry==='string'?{id:entry,type:'image',bundleRef:true}:entry).filter(isRealMediaItem);
    return {n:item[0]||'Uebung',sets:Number(item[1])||3,side:item[2]||'BI',u:item[3]||'kg',m:item[4]||'Wdh',sl:item[5]||'',sm:item[6]||'',media};
  }
  function storedPlan(){const saved=safe(()=>JSON.parse(localStorage.getItem(PLAN_KEY)||'null'));return saved&&saved.plan?saved.plan:null;}
  function mediaBundleInfo(){const raw=decodeKggH2Payload()||storedPlan();const media=(raw&&raw.m&&raw.m.media)||(raw&&raw.meta&&raw.meta.media)||{};return media.b||media.bundle||null;}
  function normalizeMediaRef(item){if(typeof item==='string')return {id:item,type:'image',bundleRef:true};return item;}
  function planExercises(){const runtime=safe(()=>typeof p!=='undefined'&&p&&Array.isArray(p.ex)?p.ex:null);if(runtime)return runtime;const custom=safe(()=>window.KGGPatientPlan&&typeof window.KGGPatientPlan.getExercises==='function'?window.KGGPatientPlan.getExercises():null);if(Array.isArray(custom))return custom;const raw=decodeKggH2Payload()||storedPlan();if(raw&&Array.isArray(raw.e))return raw.e.map(rawExerciseToRuntime);if(raw&&Array.isArray(raw.ex))return raw.ex;if(raw&&Array.isArray(raw.plan))return raw.plan;return [];}
  function openDb(){return new Promise((resolve,reject)=>{if(!('indexedDB' in window)){reject(new Error('Lokaler Bildspeicher nicht verfuegbar'));return;}const req=indexedDB.open(DB,1);req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'});};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error||new Error('Lokaler Bildspeicher nicht verfuegbar'));});}
  async function getCached(id){const db=await openDb();return new Promise(resolve=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).get(id);req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>resolve(null);});}
  async function putCached(record){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(record);tx.oncomplete=()=>resolve(record);tx.onerror=()=>reject(tx.error||new Error('Bild konnte nicht lokal gespeichert werden'));});}
  function mediaList(ex){const media=ex&&ex.media;if(Array.isArray(media))return media.map(normalizeMediaRef).filter(isRealMediaItem);if(isRealMediaItem(media))return [normalizeMediaRef(media)];return [];}
  function mediaId(item,exerciseIndex,mediaIndex){if(typeof item==='string')return item;return String(item&&item.id||item&&item.url||item&&item.src||'media_'+exerciseIndex+'_'+mediaIndex);}
  function mediaBox(id){const target=String(id);return [...document.querySelectorAll('[data-kgg-media-id]')].find(node=>node.getAttribute('data-kgg-media-id')===target)||null;}
  function ensureThumb(card,id){if(!card)return null;let thumb=card.querySelector('.kggCardThumb');if(!thumb){thumb=document.createElement('div');thumb.className='kggCardThumb';thumb.setAttribute('aria-hidden','true');card.appendChild(thumb)}card.classList.add('kggHasThumb');card.dataset.kggThumbId=String(id||'');return thumb;}
  function syncThumbById(id){const box=mediaBox(id);if(!box)return;const img=box.querySelector('img');const card=box.closest('.ex');if(!img||!card)return;const thumb=ensureThumb(card,id);thumb.innerHTML='<img src="'+esc(img.src)+'" alt="">';card.classList.add('kggThumbReady');}
  function clearThumb(card){if(!card)return;card.classList.remove('kggHasThumb','kggThumbReady');delete card.dataset.kggThumbId;const t=card.querySelector('.kggCardThumb');if(t)t.remove();}
  function closeImageLightbox(){const lb=$('kggImageLightbox');if(lb)lb.remove();document.removeEventListener('keydown',lightboxKey,true);}
  function lightboxKey(e){if(e.key==='Escape')closeImageLightbox();}
  function openImageLightbox(src,alt){if(!src)return;closeImageLightbox();const lb=document.createElement('div');lb.id='kggImageLightbox';lb.className='kggImageLightbox';lb.innerHTML='<button type="button" aria-label="Bild schließen">×</button><img src="'+esc(src)+'" alt="'+esc(alt||'Uebungsbild')+'">';lb.addEventListener('click',e=>{if(e.target===lb)closeImageLightbox();});lb.querySelector('button').addEventListener('click',e=>{e.preventDefault();e.stopPropagation();closeImageLightbox();});document.body.appendChild(lb);document.addEventListener('keydown',lightboxKey,true);}
  function bindLightbox(){if(lightboxBound)return;lightboxBound=true;document.addEventListener('click',e=>{const img=e.target&&e.target.closest?e.target.closest('.ex.kggOpen .kggMediaBox img'):null;if(!img)return;e.preventDefault();e.stopPropagation();openImageLightbox(img.src,img.alt||'Uebungsbild');},true);}
  function setBox(id,html,cls){const box=mediaBox(id);if(!box)return;box.className='kggMediaBox '+(cls||'');box.innerHTML=html;if(cls==='ready'||box.querySelector('img'))setTimeout(()=>syncThumbById(id),0);}
  function objectUrl(id,blob){const old=objectUrls.get(id);if(old)URL.revokeObjectURL(old);const url=URL.createObjectURL(blob);objectUrls.set(id,url);return url;}
  async function fetchEncrypted(item){if(window.KGGPatientMediaFetchAdapter&&typeof window.KGGPatientMediaFetchAdapter.fetch==='function')return window.KGGPatientMediaFetchAdapter.fetch(item);if(item&&item.data)return new Blob([b64Bytes(item.data)],{type:'application/octet-stream'});if(item&&item.src&&String(item.src).startsWith('data:image/'))return await (await fetch(item.src)).blob();if(!item.downloadUrl)throw new Error('Bild ist noch nicht bereit');const res=await fetch(item.downloadUrl,{cache:'no-store'});if(!res.ok)throw new Error('Bild konnte nicht geladen werden');return res.blob();}
  async function decryptMedia(item,encryptedBlob){if(item&&(item.src||item.url||item.imageUrl||item.blobUrl)&&!item.crypto)return encryptedBlob;if(!window.crypto||!crypto.subtle)throw new Error('Verschluesselung wird von diesem Browser nicht unterstuetzt');const info=item.crypto||{};if(!info.key||!info.iv)throw new Error('Bildschluessel fehlt');const key=await crypto.subtle.importKey('raw',b64Bytes(info.key),{name:'AES-GCM'},false,['decrypt']);const encrypted=await encryptedBlob.arrayBuffer();const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64Bytes(info.iv)},key,encrypted);return new Blob([plain],{type:item.mime||'image/jpeg'});}
  function bundleCryptoInfo(bundle){return {key:bundle&&((bundle.crypto&&bundle.crypto.key)||bundle.k||bundle.key),iv:bundle&&((bundle.crypto&&bundle.crypto.iv)||bundle.i||bundle.iv)};}
  async function loadMediaBundle(){if(mediaBundlePromise)return mediaBundlePromise;mediaBundlePromise=(async()=>{const bundle=mediaBundleInfo();if(!bundle)return new Map();const downloadUrl=bundle.u||bundle.downloadUrl;const info=bundleCryptoInfo(bundle);if(!downloadUrl||!info.key||!info.iv)return new Map();const res=await fetch(downloadUrl,{cache:'no-store'});if(!res.ok)throw new Error('Medien-Bundle konnte nicht geladen werden');const encrypted=await res.blob();const plain=await decryptMedia({mime:'application/json',crypto:info},encrypted);const data=JSON.parse(await plain.text());const map=new Map();(Array.isArray(data.items)?data.items:[]).forEach(item=>{if(item&&item.id)map.set(String(item.id),item);});return map;})().catch(err=>{mediaBundlePromise=null;throw err;});return mediaBundlePromise;}
  async function resolveMediaItem(item){if(item&&item.downloadUrl)return item;const id=typeof item==='string'?item:String(item&&item.id||'');if(!id)return item;const bundle=await loadMediaBundle();return bundle.get(id)||normalizeMediaRef(item);}
  async function loadMedia(item,exerciseIndex,mediaIndex){const id=mediaId(item,exerciseIndex,mediaIndex);const cached=await getCached(id).catch(()=>null);if(cached&&cached.blob){const url=objectUrl(id,cached.blob);setBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');return true;}const resolved=await resolveMediaItem(item);if(!isRealMediaItem(resolved))throw new Error('Keine Bildquelle');const encrypted=await fetchEncrypted(resolved);const blob=await decryptMedia(resolved,encrypted);await putCached({id,blob,mime:resolved.mime||'image/jpeg',savedAt:new Date().toISOString()}).catch(()=>null);const url=objectUrl(id,blob);setBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');return true;}
  function retryMedia(item,exerciseIndex,mediaIndex){const id=mediaId(item,exerciseIndex,mediaIndex);if(loading.has(id))return;loading.add(id);const retryMs=Math.max(10000,Number(item.retrySeconds||0)*1000||RETRY_MS);const until=Date.now()+retryMs;const tick=async()=>{try{await loadMedia(item,exerciseIndex,mediaIndex);loading.delete(id);}catch(err){if(Date.now()<until){setBox(id,'<span>Bild wird geladen ...</span><small>Die App versucht es automatisch erneut.</small>','loading');setTimeout(tick,STEP_MS);}else{loading.delete(id);setBox(id,'<span>Bild konnte nicht geladen werden.</span><small>Der Trainingsplan bleibt ohne Bild nutzbar. Bitte bei Bedarf neuen QR-Code erstellen lassen.</small>','error');}}};tick();}
  function prefetchAllMedia(){const exercises=planExercises();let found=false;exercises.forEach((ex,exerciseIndex)=>{mediaList(ex).forEach((item,mediaIndex)=>{found=true;retryMedia(item,exerciseIndex,mediaIndex);});});return found;}
  function renderMedia(){ensureStyle();bindLightbox();const exercises=planExercises();const hasPrefetch=prefetchAllMedia();const cards=[...document.querySelectorAll('#list .ex')];if(!cards.length||!exercises.length)return hasPrefetch;cards.forEach((card,exerciseIndex)=>{const media=mediaList(exercises[exerciseIndex]);const ids=media.map((item,mediaIndex)=>mediaId(item,exerciseIndex,mediaIndex)).join('|');const existing=card.querySelector('.kggMediaList');if(!media.length){if(existing)existing.remove();delete card.dataset.kggMediaIds;clearThumb(card);return;}const firstId=mediaId(media[0],exerciseIndex,0);ensureThumb(card,firstId);if(existing&&card.dataset.kggMediaIds===ids){media.forEach((item,mediaIndex)=>{const id=mediaId(item,exerciseIndex,mediaIndex);retryMedia(item,exerciseIndex,mediaIndex);syncThumbById(id)});return;}if(existing)existing.remove();card.dataset.kggMediaIds=ids;const wrap=document.createElement('div');wrap.className='kggMediaList';wrap.innerHTML=media.map((item,mediaIndex)=>{const id=mediaId(item,exerciseIndex,mediaIndex);return '<div class="kggMediaBox loading" data-kgg-media-id="'+esc(id)+'"><span>Bild wird geladen ...</span><small>Verschluesselte Datei wird geholt und lokal gespeichert.</small></div>';}).join('');const firstSet=card.querySelector('.set');if(firstSet)card.insertBefore(wrap,firstSet); else card.appendChild(wrap);media.forEach((item,mediaIndex)=>retryMedia(item,exerciseIndex,mediaIndex));});return true;}
  function scheduleRender(delay){if(scheduled)return;scheduled=true;setTimeout(()=>{scheduled=false;renderMedia();},delay||40);}
  function patchRender(){if(patched||typeof render!=='function')return false;patched=true;window.__kggPatientMediaPatch=VERSION;const old=render;render=function(){const result=old.apply(this,arguments);scheduleRender(30);return result;};return true;}
  function observeList(){const list=$('list');if(!list||!('MutationObserver' in window))return;const observer=new MutationObserver(()=>scheduleRender(60));observer.observe(list,{childList:true,subtree:false});}
  function init(){ensureStyle();bindLightbox();patchRender();observeList();[60,300,900,1800,3200].forEach(delay=>setTimeout(()=>{patchRender();prefetchAllMedia();renderMedia();},delay));observeTimer=setInterval(()=>{if(patchRender()||prefetchAllMedia()||renderMedia())clearInterval(observeTimer);},1200);setTimeout(()=>{if(observeTimer)clearInterval(observeTimer);},12000);}
  window.KGGPatientMediaRetryCache={version:VERSION,render:renderMedia,prefetch:prefetchAllMedia,planExercises};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();