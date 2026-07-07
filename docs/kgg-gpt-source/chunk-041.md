# KGG Source Chunk 041

- Source: `kgg-update/index.html`
- Lines: 17221-17640

```html
  const kggAutoUpdateCheckMs=30*60*1000;
  const kggAutoUpdateSessionKey='kgg_auto_update_target_v1';
  const adminSecretsKey='kgg_admin_local_secrets_v1';
  let deferredInstallPrompt=null;
  let adminSecrets={geminiKeys:[],mediaDropzoneEndpoint:'',mediaDropzoneUploadToken:'',updatedAt:''};
  const norm=s=>String(s||'').toLowerCase().replace(/[ä]/g,'ae').replace(/[ö]/g,'oe').replace(/[ü]/g,'ue').replace(/[ß]/g,'ss').replace(/[^a-z0-9]+/g,' ').trim();
  const compact=s=>norm(s).replace(/\s+/g,'');
  const bank=[
    ['abd','Abduktion Maschine','abd,abduktion,abductor,abduktor,hüft abduktion',3,'Wdh','kg'],['add','Adduktion Maschine','add,adduktion,adduktor,adductor,hüft adduktion',3,'Wdh','kg'],['legpress','Beinpresse','beinpresse,bein presse,leg press,presse',3,'Wdh','kg'],['bridge','Bridging','bridge,bridging,beckenheben,glute bridge',3,'Wdh','kg'],['copenhagen','Copenhagen Plank','copenhagen,adduktoren plank',3,'Zeit','keine'],['bike','Ergometer / Bike','fahrrad,bike,ergometer,warmup,cardio,rad',1,'Zeit','Stufe/Watt'],['fire','Fire Hydrants','fire hydrant,hydrants,vierfüßler abduktion',3,'Wdh','kg'],['hipthrust','Hip Thrust','hip thrust,glute thrust',3,'Wdh','kg'],['legcurl','Kniebeuger Maschine','kniebeuger,leg curl,hamstring curl,beinbeuger',3,'Wdh','kg'],['kneeext','Kniestrecker Maschine','kniestrecker,knieextension,beinstrecker,leg extension,knei ext',3,'Wdh','kg'],['row','Rudern','rudern,seated row,kabelrudern,ruderzug',3,'Wdh','kg'],['lat','Latziehen','latziehen,latzug,lat pulldown,pulldown,lat',3,'Wdh','kg'],['pallof','Pallof Press','pallof,pallof press,anti rotation',3,'Wdh','kg'],['plank','Plank','plank,blank,unterarmstütz,stütz',3,'Zeit','keine'],['squat','Squat','squat,kniebeuge,kniebeugen',3,'Wdh','kg'],['rdl','Romanian Deadlift','romanian deadlift,rdl,dead lift',3,'Wdh','kg'],['deadlift','Wadenheben','wadenheben,calf raise',3,'Wdh','kg'],['shoulder','Schulterpresse','schulter presse,shoulder press',3,'Wdh','kg']
  ].map(a=>({id:a[0],name:a[1],aliases:a[2],sets:a[3],unit:a[4],weightUnit:a[5]}));
  let state={plan:[],recent:[],packages:[{id:'pkg1',name:'Knie Standard',exercises:['Beinpresse','Kniebeuger Maschine','Kniestrecker Maschine']},{id:'pkg2',name:'Rücken Standard',exercises:['Rudern','Latziehen','Pallof Press']}],patient:{},bankOpen:false,editId:null,sortMenuId:null,reorderSuppressClick:false,largePdfMode:false,textSyncing:false};
  let bankSelectMode='replaceActive';
  let deletedBankIds=new Set();
  let pendingBankDeleteId=null;
  let bankSwipeSuppressClickUntil=0;
  const MEDIA_UPLOAD_TTL_SECONDS=300;
  const MEDIA_UPLOAD_LONG_TTL_SECONDS=86400;
  const MEDIA_LONG_PRESS_MS=5000;
  const MEDIA_RETRY_SECONDS=240;
  const MEDIA_IMAGE_MAX_DIM=1280;
  const MEDIA_IMAGE_QUALITY=.78;
  const mediaDbName='kgg_media_v1';
  const mediaStoreName='encryptedBlobs';
  let mediaDbPromise=null;
  let patientShareTtlSeconds=MEDIA_UPLOAD_TTL_SECONDS;
  let lastPatientSharePlanSnapshot=null;
  let lastPatientMediaBundleManifest=null;
  let copyPatientLinkSuppressClickUntil=0;
  const mediaDropzoneRuntimeTokens={};

  // v2 Plan-State-Adapter: KGGDataStore.currentPlan ist die zentrale Planquelle.
  // state.plan bleibt als bestehender UI-/Legacy-Spiegel erhalten.
  function makeLocalId(){return 'p_'+Date.now()+'_'+Math.random().toString(36).slice(2,8)}
  function makeMediaId(){return 'media_'+Date.now()+'_'+Math.random().toString(36).slice(2,10)}
  function getMediaDropzoneSetting(key){
    try{return String(window[key]||localStorage.getItem(key)||'').trim();}catch(e){return String(window[key]||'').trim();}
  }
  function cleanMediaDropzoneEndpoint(value){return String(value||'').trim().replace(/\/+$/,'');}
  function cleanMediaDropzoneId(value){return String(value||'').replace(/[^a-zA-Z0-9._-]/g,'').slice(0,96);}
  function initMediaDropzoneUploadAdapter(){
    const endpoint=cleanMediaDropzoneEndpoint(getMediaDropzoneSetting('KGG_MEDIA_DROPZONE_ENDPOINT')||getMediaDropzoneSetting('kggMediaDropzoneEndpoint'));
    window.KGGMediaDropzone={
      setEndpoint(url){try{localStorage.setItem('kggMediaDropzoneEndpoint',cleanMediaDropzoneEndpoint(url));}catch(e){}},
      setUploadToken(token){try{localStorage.setItem('kggMediaDropzoneUploadToken',String(token||'').trim());}catch(e){}},
      clear(){try{localStorage.removeItem('kggMediaDropzoneEndpoint');localStorage.removeItem('kggMediaDropzoneUploadToken');}catch(e){}}
    };
    if(!endpoint)return;
    if(window.KGGMediaUploadAdapter&&!window.KGGMediaUploadAdapter.isMock)return;
    window.KGGMediaUploadAdapter={
      name:'kgg-media-dropzone-kv-v1',
      isMock:false,
      async upload(blob,context){
        const manifest=context&&context.manifest||{};
        const id=cleanMediaDropzoneId(manifest.id)||makeMediaId();
        const ttlSeconds=Math.max(60,Math.min(MEDIA_UPLOAD_LONG_TTL_SECONDS,Number(context&&context.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS));
        const token=getMediaDropzoneSetting('KGG_MEDIA_DROPZONE_UPLOAD_TOKEN')||getMediaDropzoneSetting('kggMediaDropzoneUploadToken');
        const headers={'Content-Type':'application/octet-stream','X-KGG-Media-Id':id,'X-KGG-Media-Mime':manifest.mime||'application/octet-stream','X-KGG-Media-Bytes':String(blob&&blob.size||0)};
        if(token)headers['X-KGG-Upload-Token']=token;
        const res=await fetch(endpoint+'/upload?ttl='+encodeURIComponent(ttlSeconds),{method:'POST',headers,body:blob,cache:'no-store'});
        if(!res.ok)throw new Error('Medien-Upload fehlgeschlagen ('+res.status+').');
        const data=await res.json();
        if(data&&data.id&&data.deleteToken)mediaDropzoneRuntimeTokens[data.id]=data.deleteToken;
        return data;
      },
      scheduleDelete(media,options){
        const delay=Math.max(1000,Number(options&&options.delayMs)||((Number(media&&media.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS)*1000));
        setTimeout(()=>{this.delete(media);},delay);
      },
      async delete(media){
        const id=cleanMediaDropzoneId(media&&media.id);
        if(!id)return false;
        const deleteToken=(media&&media.deleteToken)||mediaDropzoneRuntimeTokens[id]||'';
        const deleteUrl=(media&&media.deleteUrl)||endpoint+'/media/'+encodeURIComponent(id);
        try{
          const res=await fetch(deleteUrl,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({deleteToken}),cache:'no-store'});
          return res.ok||res.status===404||res.status===410;
        }catch(err){console.warn('Media delete fehlgeschlagen:',err);return false;}
      }
    };
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
```
