# KGG Source Chunk 041

- Source: `kgg-update/index.html`
- Lines: 17221-17640

```html
  }
  initMediaDropzoneUploadAdapter();
  function bytesToBase64Url(input){
    const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
    let binary='';
    for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function ensureMediaShape(media){
    const src=media||{};
    return {
      id:src.id||makeMediaId(),
      type:src.type||src.kind||'image',
      name:src.name||src.originalName||'uebungsbild.jpg',
      mime:src.mime||'image/jpeg',
      width:Number(src.width)||0,
      height:Number(src.height)||0,
      originalSize:Number(src.originalSize)||0,
      compressedSize:Number(src.compressedSize)||0,
      encryptedSize:Number(src.encryptedSize)||0,
      status:src.status||'local-encrypted',
      encrypted:src.encrypted!==false,
      storage:src.storage||'indexeddb-local',
      downloadUrl:src.downloadUrl||'',
      deleteUrl:src.deleteUrl||'',
      deleteToken:src.deleteToken||'',
      ttlSeconds:Number(src.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS,
      retrySeconds:Number(src.retrySeconds)||MEDIA_RETRY_SECONDS,
      createdAt:src.createdAt||new Date().toISOString(),
      crypto:src.crypto||null
    };
  }
  function ensureExerciseMediaList(ex){return Array.isArray(ex&&ex.media)?ex.media.map(ensureMediaShape):[];}
  function openMediaDb(){
    if(mediaDbPromise)return mediaDbPromise;
    mediaDbPromise=new Promise((resolve,reject)=>{
      if(!('indexedDB' in window)){reject(new Error('IndexedDB nicht verfuegbar'));return;}
      const req=indexedDB.open(mediaDbName,1);
      req.onupgradeneeded=()=>{const db=req.result; if(!db.objectStoreNames.contains(mediaStoreName))db.createObjectStore(mediaStoreName,{keyPath:'id'});};
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Media-DB konnte nicht geoeffnet werden'));
    });
    return mediaDbPromise;
  }
  function putEncryptedMediaBlob(record){
    return openMediaDb().then(db=>new Promise((resolve,reject)=>{
      const tx=db.transaction(mediaStoreName,'readwrite');
      tx.objectStore(mediaStoreName).put(record);
      tx.oncomplete=()=>resolve(record);
      tx.onerror=()=>reject(tx.error||new Error('Media-Blob konnte nicht gespeichert werden'));
    }));
  }
  function getEncryptedMediaBlob(id){
    return openMediaDb().then(db=>new Promise((resolve,reject)=>{
      const tx=db.transaction(mediaStoreName,'readonly');
      const req=tx.objectStore(mediaStoreName).get(id);
      req.onsuccess=()=>resolve(req.result||null);
      req.onerror=()=>reject(req.error||new Error('Media-Blob konnte nicht gelesen werden'));
    }));
  }
  function deleteEncryptedMediaBlob(id){
    return openMediaDb().then(db=>new Promise(resolve=>{
      const tx=db.transaction(mediaStoreName,'readwrite');
      tx.objectStore(mediaStoreName).delete(id);
      tx.oncomplete=()=>resolve(true);
      tx.onerror=()=>resolve(false);
    })).catch(()=>false);
  }
  function isMediaReferencedElsewhere(id,owner){
    const sid=String(id||'');
    if(!sid)return false;
    const ownerId=owner&&(owner.localId||owner.id);
    const lists=[...(state.plan||[]),...bank];
    return lists.some(ex=>{
      if(!ex)return false;
      if(owner&&String(ex.localId||ex.id)===String(ownerId))return false;
      return ensureExerciseMediaList(ex).some(media=>String(media.id)===sid);
    });
  }
  function deleteUnsharedMediaBlob(media,owner){
    if(media&&media.id&&!isMediaReferencedElsewhere(media.id,owner))deleteEncryptedMediaBlob(media.id);
  }
  function loadImageFromBlob(blob){
    return new Promise((resolve,reject)=>{
      const url=URL.createObjectURL(blob);
      const img=new Image();
      img.onload=()=>{URL.revokeObjectURL(url); resolve(img);};
      img.onerror=()=>{URL.revokeObjectURL(url); reject(new Error('Bild konnte nicht gelesen werden'));};
      img.src=url;
    });
  }
  async function compressImageFile(file){
    const img=await loadImageFromBlob(file);
    const maxSide=Math.max(img.naturalWidth||img.width,img.naturalHeight||img.height,1);
    const scale=Math.min(1,MEDIA_IMAGE_MAX_DIM/maxSide);
    const width=Math.max(1,Math.round((img.naturalWidth||img.width)*scale));
    const height=Math.max(1,Math.round((img.naturalHeight||img.height)*scale));
    const canvas=document.createElement('canvas');
    canvas.width=width; canvas.height=height;
    const ctx=canvas.getContext('2d',{alpha:false});
    ctx.fillStyle='#fff'; ctx.fillRect(0,0,width,height); ctx.drawImage(img,0,0,width,height);
    const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('Bild konnte nicht komprimiert werden')),'image/jpeg',MEDIA_IMAGE_QUALITY));
    return {blob,width,height,mime:'image/jpeg'};
  }
  async function encryptMediaBlob(blob){
    if(!window.crypto||!crypto.subtle)throw new Error('Web Crypto ist in diesem Browser nicht verfuegbar');
    const key=await crypto.subtle.generateKey({name:'AES-GCM',length:256},true,['encrypt','decrypt']);
    const iv=crypto.getRandomValues(new Uint8Array(12));
    const plain=await blob.arrayBuffer();
    const cipher=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,plain);
    const rawKey=await crypto.subtle.exportKey('raw',key);
    return {blob:new Blob([cipher],{type:'application/octet-stream'}),encryptedSize:cipher.byteLength,key:bytesToBase64Url(rawKey),iv:bytesToBase64Url(iv)};
  }
  async function prepareImageMediaFile(file){
    if(!file||!String(file.type||'').startsWith('image/'))throw new Error('Bitte ein Bild auswaehlen');
    const id=makeMediaId();
    const compressed=await compressImageFile(file);
    const encrypted=await encryptMediaBlob(compressed.blob);
    const now=new Date().toISOString();
    const manifest=ensureMediaShape({
      id,
      type:'image',
      name:file.name||'uebungsbild.jpg',
      mime:compressed.mime,
      width:compressed.width,
      height:compressed.height,
      originalSize:file.size||0,
      compressedSize:compressed.blob.size||0,
      encryptedSize:encrypted.encryptedSize,
      status:'local-encrypted',
      encrypted:true,
      storage:'indexeddb-local',
      ttlSeconds:MEDIA_UPLOAD_TTL_SECONDS,
      retrySeconds:MEDIA_RETRY_SECONDS,
      createdAt:now,
      crypto:{alg:'AES-GCM',iv:encrypted.iv,key:encrypted.key}
    });
    await putEncryptedMediaBlob({id,blob:encrypted.blob,manifest,createdAt:now});
    return manifest;
  }
  function mediaUploadAdapter(){
    const adapter=window.KGGMediaUploadAdapter;
    return adapter&&typeof adapter.upload==='function'?adapter:null;
  }
  function currentMediaShareTtlSeconds(){
    return Math.max(MEDIA_UPLOAD_TTL_SECONDS,Number(patientShareTtlSeconds)||MEDIA_UPLOAD_TTL_SECONDS);
  }
  function mediaItemsFromExercises(exercises){
    return (exercises||[]).flatMap(ex=>ensureExerciseMediaList(ex).map(media=>({ex,media})));
  }
  function allPlanMediaItems(exercises){
    return mediaItemsFromExercises(exercises||state.plan||[]);
  }
  function scheduleTemporaryMediaDelete(adapter,media){
    if(!adapter)return;
    const delay=Math.max(1,Number(media.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS)*1000;
    if(typeof adapter.scheduleDelete==='function'){
      try{adapter.scheduleDelete(media,{delayMs:delay});}catch(err){console.warn('Media scheduleDelete fehlgeschlagen:',err);}
      return;
    }
    if(typeof adapter.delete==='function'){
      setTimeout(()=>{try{adapter.delete(media);}catch(err){console.warn('Media delete fehlgeschlagen:',err);}},delay);
    }
  }
  async function uploadOneMediaItem(adapter,media,options){
    const ttlSeconds=Number(options&&options.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS;
    const force=!!(options&&options.force);
    if(media.downloadUrl&&media.status==='ready'&&!force&&(Number(media.ttlSeconds)||0)>=ttlSeconds)return media;
    const record=await getEncryptedMediaBlob(media.id);
    if(!record||!record.blob)throw new Error('Verschluesselte Bilddatei fehlt lokal.');
    const uploadManifest=ensureMediaShape({...media,ttlSeconds,retrySeconds:MEDIA_RETRY_SECONDS});
    const result=await adapter.upload(record.blob,{manifest:uploadManifest,ttlSeconds});
    if(!result||!result.downloadUrl)throw new Error('Upload lieferte keinen Download-Link.');
    const uploadedAt=new Date().toISOString();
    const expiresAt=result.expiresAt||new Date(Date.now()+ttlSeconds*1000).toISOString();
    const updated=ensureMediaShape({...media,downloadUrl:result.downloadUrl,deleteUrl:result.deleteUrl||media.deleteUrl||'',deleteToken:result.deleteToken||media.deleteToken||'',storage:result.storage||'temporary-web-encrypted',status:'ready',uploadedAt,expiresAt,ttlSeconds,retrySeconds:MEDIA_RETRY_SECONDS});
    scheduleTemporaryMediaDelete(adapter,updated);
    return updated;
  }
  function publicMediaBundleItem(media){
    return {
      id:media.id,
      type:'image',
      mime:media.mime,
      name:media.name,
      width:media.width,
      height:media.height,
      bytes:media.encryptedSize||0,
      encrypted:true,
      status:media.downloadUrl?'ready':'upload-pending',
      downloadUrl:media.downloadUrl||'',
      expiresInSeconds:media.ttlSeconds||MEDIA_UPLOAD_TTL_SECONDS,
      retrySeconds:media.retrySeconds||MEDIA_RETRY_SECONDS,
      crypto:media.crypto||null
    };
  }
  async function blobToBase64Url(blob){
    return bytesToBase64Url(await blob.arrayBuffer());
  }
  async function mediaItemsForBundle(exercises){
    const seen=new Set();
    const items=[];
    for(const ex of (exercises||[])){
      for(const media of ensureExerciseMediaList(ex)){
        if(media.type!=='image'||!media.id||seen.has(media.id))continue;
        seen.add(media.id);
        const record=await getEncryptedMediaBlob(media.id);
        if(!record||!record.blob)throw new Error('Verschluesselte Bilddatei fehlt lokal: '+(media.name||media.id));
        const item=publicMediaBundleItem(media);
        item.status='ready';
        item.downloadUrl='';
        item.dataEncoding='base64url';
        item.data=await blobToBase64Url(record.blob);
        item.encryptedBytes=record.blob.size||media.encryptedSize||0;
        items.push(item);
      }
    }
    return items;
  }
  async function uploadMediaBundle(adapter,exercises,ttlSeconds){
    const bundleItems=await mediaItemsForBundle(exercises);
    if(!bundleItems.length){lastPatientMediaBundleManifest=null; return null;}
    const plain={kind:'kgg-media-bundle-v1',version:1,createdAt:new Date().toISOString(),items:bundleItems};
    const encrypted=await encryptMediaBlob(new Blob([JSON.stringify(plain)],{type:'application/json'}));
    const bundleId='bundle_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
    const result=await adapter.upload(encrypted.blob,{manifest:{id:bundleId,type:'bundle',mime:'application/octet-stream'},ttlSeconds});
    if(!result||!result.downloadUrl)throw new Error('Medien-Bundle lieferte keinen Download-Link.');
    const bundle={
      id:result.id||bundleId,
      schema:'kgg-media-bundle-v1',
      count:bundleItems.length,
      downloadUrl:result.downloadUrl,
      deleteUrl:result.deleteUrl||'',
      deleteToken:result.deleteToken||'',
      expiresInSeconds:ttlSeconds,
      retrySeconds:MEDIA_RETRY_SECONDS,
      encrypted:true,
      crypto:{alg:'AES-GCM',iv:encrypted.iv,key:encrypted.key}
    };
    scheduleTemporaryMediaDelete(adapter,{id:bundle.id,deleteUrl:bundle.deleteUrl,deleteToken:bundle.deleteToken,ttlSeconds});
    lastPatientMediaBundleManifest=bundle;
    return bundle;
  }
  async function prepareMediaUploadsForPatientShare(options){
    lastPatientMediaBundleManifest=null;
    const sourcePlan=options&&options.plan;
    const exercises=sourcePlan&&Array.isArray(sourcePlan.exercises)?sourcePlan.exercises:state.plan;
    const items=allPlanMediaItems(exercises);
    if(!items.length)return {ok:true,count:0};
    const adapter=mediaUploadAdapter();
    if(!adapter)return {ok:false,count:items.length,message:'Medien-Upload fehlt. Plan bleibt offen.'};
    const ttlSeconds=Number(options&&options.ttlSeconds)||currentMediaShareTtlSeconds();
    let bundle=null;
    try{
      bundle=await uploadMediaBundle(adapter,exercises,ttlSeconds);
    }catch(err){
      console.warn('Medien-Bundle konnte nicht erstellt werden:',err);
      return {ok:false,count:items.length,message:err&&err.message?err.message:'Medien-Bundle fehlgeschlagen. Plan bleibt offen.'};
    }
    if(!sourcePlan){
      syncStatePlanToStore('ui_prepare_media_uploads_for_patient_share');
      save();
    }
    return {ok:true,count:items.length,uploaded:items.length,bundle};
  }
  function normalizeSideMode(value){
    const raw=String(value||'BI').trim().toUpperCase().replace(/\s+/g,'');
    if(['L','LI','LINKS','LEFT','R','RE','RECHTS','RIGHT'].includes(raw))return 'LR';
    if(['LR','L/R','LI/RE','LINKS/RECHTS','LINKSRECHTS','LEFT/RIGHT','BEIDSEITIGGETRENNT'].includes(raw))return 'LR';
    if((raw.includes('LINKS')&&raw.includes('RECHTS'))||(raw.includes('LI')&&raw.includes('RE')))return 'LR';
    if(['BI','BID','BEIDE','BEIDSEITIG','BILATERAL'].includes(raw))return 'BI';
    return 'BI';
  }
  function sideModeLabel(value){return ({BI:'beidseitig',LR:'links/rechts getrennt'})[normalizeSideMode(value)]||'beidseitig';}
  function normalizeSetCount(value){const n=Number(value)||3; return Math.max(1,Math.min(5,n));}
  function normalizeMeasureMode(value){
    const raw=String(value||'').trim().toLowerCase();
    if(['zeit','time','dauer','sek','sek.','sec','s'].includes(raw))return 'zeit';
    return 'wdh';
  }
  function measureUnitLabel(measure){return normalizeMeasureMode(measure)==='zeit'?'Sek.':'Wdh';}
  function cleanFreeUnitLabel(value){
    return String(value||'').trim().replace(/\s*\/\s*/g,'/').replace(/\s+/g,' ').replace(/^[.@:;,\-\s]+|[.@:;,\-\s]+$/g,'');
  }
  function normalizeLoadUnitInfo(value,fallback){
    const fallbackUnit=fallback||'kg';
    const raw=cleanFreeUnitLabel(value);
    if(!raw)return {unit:fallbackUnit,custom:false,explicit:false};
    const lower=raw.toLowerCase().replace(/\./g,'').replace(/\s+/g,' ');
    const compact=lower.replace(/\s+/g,'');
    if(['kg','kgs','kilo','kilos','kilogramm','kilogram'].includes(lower))return {unit:'kg',custom:false,explicit:true};
    if(['bw','bodyweight','body weight','koerpergewicht','körpergewicht','eigengewicht'].includes(lower)||compact==='bodyweight')return {unit:'BW',custom:false,explicit:true};
    if(['hub','huebe','hübe'].includes(lower))return {unit:'Hub',custom:false,explicit:true};
    if(['stufe'].includes(lower))return {unit:'Stufe',custom:false,explicit:true};
    if(['watt','w'].includes(lower))return {unit:'Watt',custom:false,explicit:true};
    if(['stufe/watt','stufe watt','stufe+watt','stufewatt'].includes(lower)||compact==='stufe/watt')return {unit:'Stufe/Watt',custom:false,explicit:true};
    if(['bar'].includes(lower))return {unit:'bar',custom:false,explicit:true};
    if(['keine','kein','none','ohne'].includes(lower))return {unit:'keine',custom:false,explicit:true};
    return {unit:raw,custom:true,explicit:true};
  }
  function normalizeLoadUnit(value){
    return normalizeLoadUnitInfo(value,'kg').unit;
  }
  function structuredNumberPattern(){return '-?\\d+(?:[,.]\\d+)?';}
  function structuredUnitPattern(){return '[A-Za-zÄÖÜäöüß%°/._-]+(?:\\s*/\\s*[A-Za-zÄÖÜäöüß%°/._-]+)?';}
  function normalizeStructuredNumber(value){return String(value||'').replace(',','.').trim();}
  function normalizeMetricToken(token){
    const raw=String(token||'').trim().replace('.','');
    const lower=raw.toLowerCase();
    if(['wdh','wh','rep','reps'].includes(lower))return {unit:'Wdh',metricUnit:'Wdh',time:false,label:'Wdh'};
    if(['min','minute','minutes','minuten','sek','sec','secs','s','zeit','time','dauer'].includes(lower))return {unit:'Zeit',metricUnit:'Zeit',time:true,label:raw||'Zeit'};
    return {unit:raw||'Wdh',metricUnit:raw||'Wdh',time:false,label:raw||'Wdh',custom:true};
  }
  function parseExerciseQuantityText(text){
    const body=String(text||'');
    const n=structuredNumberPattern(), u=structuredUnitPattern();
    const freeU='([^\\s\\d@,:;]+(?:\\s*/\\s*[^\\s\\d@,:;]+)?)';
    const out={startMetric:'',unit:'',metricUnit:'',startLoad:'',weightUnit:'',loadUnit:'',customLoadUnit:false,needsReview:false};
    const loadBeforeMetric=body.match(new RegExp('('+n+')\\s*'+freeU+'\\s*@\\s*('+n+')\\s*(wdh|wh|rep|reps)\\b','i'));
    if(loadBeforeMetric){
      const loadUnitInfo=normalizeLoadUnitInfo(loadBeforeMetric[2]||'kg','kg');
      out.startLoad=normalizeStructuredNumber(loadBeforeMetric[1]);
      out.weightUnit=loadUnitInfo.unit;
      out.loadUnit=loadUnitInfo.unit;
      out.customLoadUnit=!!loadUnitInfo.custom;
      out.startMetric=normalizeStructuredNumber(loadBeforeMetric[3]);
      out.unit='Wdh'; out.metricUnit='Wdh';
      if(loadUnitInfo.custom)out.needsReview=true;
      return out;
    }
    const compact=body.match(new RegExp('('+n+')\\s*x\\s*('+n+')(?:\\s*('+u+'))?','i'));
    const rep=body.match(new RegExp('('+n+')\\s*(wdh|wh|rep|reps)\\b','i'));
    const time=body.match(new RegExp('('+n+')\\s*(min|minute|minutes|minuten|sek\\.?|sec|secs|s|zeit|time|dauer)\\b','i'));
    if(rep){
      out.startMetric=normalizeStructuredNumber(rep[1]);
      out.unit='Wdh'; out.metricUnit='Wdh';
    }else if(time){
      const mt=normalizeMetricToken(time[2]);
      out.startMetric=normalizeStructuredNumber(time[1])+' '+mt.label;
      out.unit=mt.unit; out.metricUnit=mt.metricUnit;
    }else if(compact){
      out.startMetric=normalizeStructuredNumber(compact[1]);
      out.unit='Wdh'; out.metricUnit='Wdh';
    }
    let loadUnitInfo=null, loadMatch=null;
    loadMatch=body.match(new RegExp('@\\s*('+n+')\\s*('+u+')?','i'));
    if(loadMatch){
      out.startLoad=normalizeStructuredNumber(loadMatch[1]);
      loadUnitInfo=normalizeLoadUnitInfo(loadMatch[2]||'kg','kg');
    }else{
      loadMatch=body.match(new RegExp('@\\s*('+u+')\\s*('+n+')','i'));
      if(loadMatch){
        out.startLoad=normalizeStructuredNumber(loadMatch[2]);
        loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
      }else{
        loadMatch=body.match(new RegExp('@\\s*('+u+')\\b','i'));
        if(loadMatch)loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
      }
    }
    if(!loadUnitInfo&&compact){
      out.startLoad=normalizeStructuredNumber(compact[2]);
      loadUnitInfo=normalizeLoadUnitInfo(compact[3]||'kg','kg');
    }
    if(!loadUnitInfo){
      let rest=body;
      [compact,rep,time].forEach(m=>{if(m)rest=rest.replace(m[0],' ');});
      rest=rest.replace(new RegExp('@\\s*(?:'+n+'\\s*'+u+'?|'+u+'\\s*'+n+'|'+u+')','ig'),' ');
      loadMatch=rest.match(new RegExp('('+n+')\\s*('+u+')\\b','i'));
      if(loadMatch){
        out.startLoad=normalizeStructuredNumber(loadMatch[1]);
        loadUnitInfo=normalizeLoadUnitInfo(loadMatch[2],'kg');
      }else{
        loadMatch=rest.match(new RegExp('('+u+')\\s*('+n+')\\b','i'));
        if(loadMatch){
          out.startLoad=normalizeStructuredNumber(loadMatch[2]);
          loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
        }
      }
    }
    if(loadUnitInfo&&loadUnitInfo.explicit){
      out.weightUnit=loadUnitInfo.unit;
      out.loadUnit=loadUnitInfo.unit;
      out.customLoadUnit=!!loadUnitInfo.custom;
      if(loadUnitInfo.custom)out.needsReview=true;
    }
    return out;
  }
  function parseSideModeFromText(text){
    const raw=' '+String(text||'').toLowerCase().replace(/[.,;:]+/g,' ')+' ';
    if(/\b(lr|l\/r|li\/re|links\/rechts|li|re|links|rechts)\b/.test(raw))return 'LR';
    return 'BI';
  }
  function ensureKGGDataStore(){
    if(window.KGGDataStore && typeof window.KGGDataStore.getCurrentPlan==='function')return window.KGGDataStore;
    const store={currentPlan:{id:'plan_'+Date.now(),title:'KGG Plan',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),patient:{},exercises:[],source:'ui'}};
    window.KGGDataStore={
      init(meta){store.meta={...(store.meta||{}),...(meta||{})};return this;},
      setCurrentPlan(plan,reason){store.currentPlan={...(store.currentPlan||{}),...(plan||{}),updatedAt:new Date().toISOString(),lastReason:reason||''};return store.currentPlan;},
      getCurrentPlan(){return JSON.parse(JSON.stringify(store.currentPlan||{exercises:[]}));},
      getState(){return JSON.parse(JSON.stringify(store));}
    };
    return window.KGGDataStore;
  }
  function ensureUiExerciseShape(ex){
    const localId=ex.localId||ex.uiLocalId||(String(ex.id||'').startsWith('p_')?ex.id:makeLocalId());
    return {...ex, id:localId, localId, side:normalizeSideMode(ex.side||ex.sides||ex.laterality||'BI'), media:ensureExerciseMediaList(ex), sourceId:ex.sourceId||ex.bankId||(!String(ex.id||'').startsWith('p_')?ex.id:''), bankId:ex.bankId||(!String(ex.id||'').startsWith('p_')?ex.id:'')};
  }
  function currentPatientData(){return {name:state.patient&&state.patient.name||'',date:$('planDate')&&$('planDate').value||'',therapist:state.patient&&state.patient.therapist||'',notes:state.patient&&state.patient.notes||''};}
  function syncStatePlanToStore(reason){
    const ds=ensureKGGDataStore();
    state.plan=Array.isArray(state.plan)?state.plan.map(ensureUiExerciseShape):[];
    ds.setCurrentPlan({
      id:state.planId||'plan_'+(state.createdAt||Date.now()),
      title:state.planTitle||'KGG Plan',
      patient:{...(state.patient||{}),...currentPatientData()},
      exercises:state.plan.map(ex=>({...ex})),
      source:'ui-shell'
    },reason||'sync_state_to_store');
    return ds.getCurrentPlan();
  }
```
