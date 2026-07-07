# KGG Source Chunk 052

- Source: `kgg-update/index.html`
- Lines: 21841-22260

```html
    if(window.KGGPatientMediaFetchAdapter&&typeof window.KGGPatientMediaFetchAdapter.fetch==='function')return window.KGGPatientMediaFetchAdapter.fetch(media);
    if(!media.downloadUrl)throw new Error('Bild ist noch nicht bereit');
    const res=await fetch(media.downloadUrl,{cache:'no-store'});
    if(!res.ok)throw new Error('Bild konnte nicht geladen werden');
    return res.blob();
  }
  async function patientDecryptMedia(media,encryptedBlob){
    if(!window.crypto||!crypto.subtle)throw new Error('Web Crypto nicht verfuegbar');
    const info=media.crypto||{};
    if(!info.key||!info.iv)throw new Error('Medienschluessel fehlt');
    const key=await crypto.subtle.importKey('raw',base64UrlToBytes(info.key),{name:'AES-GCM'},false,['decrypt']);
    const encrypted=await encryptedBlob.arrayBuffer();
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:base64UrlToBytes(info.iv)},key,encrypted);
    return new Blob([plain],{type:media.mime||'image/jpeg'});
  }
  function updatePatientMediaBox(id,html,kind){
    const selector='[data-patient-media-id="'+String(id).replace(/"/g,'\\"')+'"]';
    const box=document.querySelector(selector);
    if(!box)return;
    box.className='patientMedia patientMedia_'+(kind||'loading');
    box.innerHTML=html;
  }
  async function loadPatientMediaItem(media){
    const id=String(media&&media.id||'');
    if(!id)return false;
    const cached=await patientGetCachedMedia(id);
    if(cached&&cached.blob){
      const url=URL.createObjectURL(cached.blob);
      updatePatientMediaBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
      return true;
    }
    const encrypted=await patientFetchEncryptedMedia(media);
    const imageBlob=await patientDecryptMedia(media,encrypted);
    await patientPutCachedMedia({id,blob:imageBlob,mime:media.mime||'image/jpeg',savedAt:new Date().toISOString()});
    const url=URL.createObjectURL(imageBlob);
    updatePatientMediaBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
    return true;
  }
  function retryPatientMediaItem(media){
    const id=String(media&&media.id||'');
    if(!id)return;
    const retryMs=Math.max(10,Number(media.retrySeconds)||MEDIA_RETRY_SECONDS)*1000;
    const until=Date.now()+retryMs;
    const tick=async()=>{
      try{
        await loadPatientMediaItem(media);
      }catch(err){
        if(Date.now()<until){
          updatePatientMediaBox(id,'<span>Bild wird geladen ...</span><small>Die App versucht es automatisch erneut.</small>','loading');
          setTimeout(tick,4000);
        }else{
          updatePatientMediaBox(id,'<span>Bild konnte nicht geladen werden.</span><small>Der Plan bleibt ohne Bild nutzbar. Bitte bei Bedarf neuen QR-Code erstellen lassen.</small>','error');
        }
      }
    };
    tick();
  }
  function patientMediaMarkup(ex){
    const media=ensureExerciseMediaList(ex).filter(item=>item.type==='image');
    if(!media.length)return '';
    return '<div class="patientMediaList">'+media.map(item=>'<div class="patientMedia patientMedia_loading" data-patient-media-id="'+escapeHtml(item.id)+'"><span>Bild wird geladen ...</span><small>Verschluesselte Datei wird geholt und lokal gespeichert.</small></div>').join('')+'</div>';
  }
  function initPatientMediaDownloads(exercises){
    (exercises||[]).forEach(ex=>ensureExerciseMediaList(ex).filter(item=>item.type==='image').forEach(retryPatientMediaItem));
  }

  function patientExerciseLine(ex,index){
    const name=escapeHtml(ex&&ex.name||'Übung '+(index+1));
    const sets=escapeHtml(ex&&ex.sets||3);
    const metric=escapeHtml(ex&&ex.startMetric||ex&&ex.metric||'');
    const metricUnit=escapeHtml(ex&&ex.unit||ex&&ex.metricUnit||'Wdh');
    const load=escapeHtml(ex&&ex.startLoad||ex&&ex.load||ex&&ex.weight||'');
    const loadUnit=escapeHtml(ex&&ex.weightUnit||ex&&ex.loadUnit||'kg');
    const side=sideModeLabel(ex&&ex.side||ex&&ex.laterality||'BI');
    const details=[sets+' Sätze'];
    if(metric)details.push(metric+' '+metricUnit);
    if(load)details.push(load+' '+loadUnit);
    details.push(side);
    return '<article class="patientExercise"><b>'+(index+1)+'. '+name+'</b><small>'+details.map(escapeHtml).join(' · ')+'</small>'+patientMediaMarkup(ex)+'</article>';
  }

  function renderPatientHashView(){
    const payload=decodePatientPayloadFromHash();
    if(!payload)return false;
    const plan=Array.isArray(payload.plan)?payload.plan:(Array.isArray(payload.exercises)?payload.exercises:[]);
    const patient=payload.patient||{};
    const displayName=escapeHtml(patient.name||patient.initials||patient.id||'Patient/in');
    const date=escapeHtml(patient.date||patient.startDate||'');
    const exercises=plan.filter(Boolean);
    document.body.innerHTML='<main class="patientAppView">'+
      '<header><h1>KGG Trainingsplan</h1><p>'+displayName+(date?' · '+date:'')+'</p></header>'+
      (payload.error?'<section class="patientNotice">Dieser Patienten-Link konnte nicht gelesen werden.</section>':'')+
      '<section class="patientExercises">'+
      (exercises.length?exercises.map(patientExerciseLine).join(''):'<p class="patientNotice">Keine Übungen im Plan gefunden.</p>')+
      '</section>'+
      '<footer>Bitte trainiere nach Rücksprache mit deiner Praxis. Schmerzen und Auffälligkeiten dort melden.</footer>'+
      '</main>';
    const style=document.createElement('style');
    style.textContent='body{display:block;background:#e8eef6;color:#071027}.patientAppView{width:min(100%,520px);min-height:100vh;margin:0 auto;padding:18px 14px 34px;background:#e8eef6}.patientAppView header{background:#fff;border:2px solid #1b2230;border-radius:22px;padding:16px;box-shadow:0 4px 14px rgba(7,16,39,.08)}.patientAppView h1{font-size:28px;line-height:1.05;margin:0 0 8px}.patientAppView p{margin:0;color:#657386;font-weight:800}.patientExercises{display:grid;gap:10px;margin-top:14px}.patientExercise{background:#fff;border:1px solid #dce3eb;border-radius:16px;padding:14px;box-shadow:0 4px 14px rgba(7,16,39,.08)}.patientExercise b{display:block;font-size:20px}.patientExercise small{display:block;margin-top:7px;color:#38475b;font-size:15px;font-weight:850}.patientMediaList{display:grid;gap:8px;margin-top:12px}.patientMedia{border:1px solid #dce3eb;border-radius:14px;background:#f6f8fb;padding:10px;color:#38475b;font-weight:850}.patientMedia span{display:block}.patientMedia small{font-size:13px;color:#657386}.patientMedia img{display:block;width:100%;max-height:320px;object-fit:contain;border-radius:12px;background:#fff}.patientMedia_ready{background:#fff}.patientMedia_error{background:#fff8e8;border-color:#f2d38a}.patientNotice{background:#fff8e8;border:1px solid #f2d38a;border-radius:16px;padding:14px;margin-top:14px;font-weight:800}.patientAppView footer{margin-top:18px;color:#657386;font-size:13px;font-weight:800}';
    document.head.appendChild(style);
    initPatientMediaDownloads(exercises);
    return true;
  }

  function renderRuntimeVersionInUi(){
    const el=document.querySelector('.topbar small');
    if(!el)return;
    const marker=' · '+VERSION+' · TEMPLATE_MATCH_V1_RUNTIME_GUARD';
    if(!el.textContent.includes('TEMPLATE_MATCH_V1_RUNTIME_GUARD'))el.textContent=(el.textContent||'')+marker;
  }
  function androidBuildStatus(){
    try{
      if(!(window.KGGAndroidApp&&typeof window.KGGAndroidApp.updateStatus==='function'))return null;
      return JSON.parse(window.KGGAndroidApp.updateStatus()||'{}');
    }catch(err){return null;}
  }
  function renderBuildIdentityInUi(){
    const el=$('kggBuildBadge');
    if(!el)return;
    const native=androidBuildStatus()||{};
    const parts=[
      'App-Version '+VERSION,
      'Build-Zeit '+KGG_BUILD_INFO.buildTime,
      'Build-Code '+KGG_BUILD_INFO.buildCode,
      'HTML '+KGG_BUILD_INFO.htmlFile
    ];
    if(native.versionName||native.versionCode)parts.push('Android '+(native.versionName||'')+' ('+(native.versionCode||'?')+')');
    if(native.packageName)parts.push('Package '+native.packageName);
    if(native.currentWebVersion)parts.push('WebStore v'+native.currentWebVersion);
    el.textContent=parts.join(' · ');
  }
  /* v295 SINGLE KGGScan REBUILD
     Architekturentscheidung: genau ein aktiver Scan-Controller.
     QR wird lokal zuerst gelesen; Gemini ist nur Papierplan-Fallback.
     Keine zweite scanJobsState-Wahrheit, keine Beta-Parallel-Scanlogik.
  */
  /* kgg-mini-patch-v400-09-qr-photo-upload-decode
     Robustere QR-Erkennung fuer Bilder aus Galerie/Foto-Datenbank.
     Kamera-Scan bleibt unveraendert; nur Datei-/Bild-Decoding wird verbessert.
  */
  function scanReadFileAsDataUrl(file){
    return new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(String(reader.result||''));
      reader.onerror=()=>reject(reader.error||new Error('Bild konnte nicht gelesen werden'));
      reader.readAsDataURL(file);
    });
  }
  function scanCanvasFromImageSource(source,width,height,maxSide){
    const srcW=Math.max(1,Math.round(width||source.naturalWidth||source.videoWidth||source.width||1));
    const srcH=Math.max(1,Math.round(height||source.naturalHeight||source.videoHeight||source.height||1));
    const limit=Math.max(320,Number(maxSide)||2200);
    const scale=Math.min(1,limit/Math.max(1,srcW,srcH));
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(srcW*scale));
    canvas.height=Math.max(1,Math.round(srcH*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=true;
    ctx.imageSmoothingQuality='high';
    ctx.drawImage(source,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanImageElementFromUrl(url){
    return new Promise((resolve,reject)=>{
      const img=new Image();
      img.onload=()=>resolve(img);
      img.onerror=()=>reject(new Error('Bild konnte nicht gelesen werden'));
      img.decoding='async';
      img.src=url;
    });
  }
  async function scanImageCanvasFromFile(file,maxSide){
    const limit=Math.max(320,Number(maxSide)||2200);
    if(window.createImageBitmap){
      try{
        const bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
        try{return scanCanvasFromImageSource(bitmap,bitmap.width,bitmap.height,limit);}
        finally{try{bitmap.close();}catch(closeErr){}}
      }catch(bitmapErr){
        console.warn('QR-Dateibild: createImageBitmap fehlgeschlagen, fallback auf Image/FileReader.',bitmapErr);
      }
    }
    let url='';
    try{
      url=URL.createObjectURL(file);
      const img=await scanImageElementFromUrl(url);
      return scanCanvasFromImageSource(img,img.naturalWidth||img.width,img.naturalHeight||img.height,limit);
    }catch(objectUrlErr){
      console.warn('QR-Dateibild: ObjectURL fehlgeschlagen, fallback auf DataURL.',objectUrlErr);
      try{
        const dataUrl=await scanReadFileAsDataUrl(file);
        const img=await scanImageElementFromUrl(dataUrl);
        return scanCanvasFromImageSource(img,img.naturalWidth||img.width,img.naturalHeight||img.height,limit);
      }catch(dataUrlErr){
        throw dataUrlErr||objectUrlErr||new Error('Bild konnte nicht gelesen werden');
      }
    }finally{
      if(url){try{URL.revokeObjectURL(url);}catch(revokeErr){}}
    }
  }
  function scanCloneCanvas(src){
    const canvas=document.createElement('canvas');
    canvas.width=src.width;
    canvas.height=src.height;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(src,0,0);
    return canvas;
  }
  function scanCropCanvas(src,box){
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(64,Math.round(src.width*box.w));
    canvas.height=Math.max(64,Math.round(src.height*box.h));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(src,src.width*box.x,src.height*box.y,src.width*box.w,src.height*box.h,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanRotateCanvas(src,rotation){
    const rot=((Number(rotation)||0)%360+360)%360;
    if(!rot)return src;
    const flip=rot===90||rot===270;
    const canvas=document.createElement('canvas');
    canvas.width=flip?src.height:src.width;
    canvas.height=flip?src.width:src.height;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.save();
    if(rot===90){ctx.translate(canvas.width,0);ctx.rotate(Math.PI/2);}
    else if(rot===180){ctx.translate(canvas.width,canvas.height);ctx.rotate(Math.PI);}
    else if(rot===270){ctx.translate(0,canvas.height);ctx.rotate(-Math.PI/2);}
    ctx.drawImage(src,0,0);
    ctx.restore();
    return canvas;
  }
  function scanScaleCanvas(src,minSide,maxSide){
    const shortest=Math.max(1,Math.min(src.width,src.height));
    const longest=Math.max(1,Math.max(src.width,src.height));
    const minTarget=Math.max(120,Number(minSide)||0);
    const maxTarget=Math.max(minTarget,Number(maxSide)||2600);
    let scale=1;
    if(minTarget&&shortest<minTarget)scale=minTarget/shortest;
    if(longest*scale>maxTarget)scale=maxTarget/longest;
    if(Math.abs(scale-1)<0.03)return src;
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(src.width*scale));
    canvas.height=Math.max(1,Math.round(src.height*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=scale<1;
    ctx.imageSmoothingQuality='high';
    ctx.drawImage(src,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanFilteredCanvas(src,mode){
    if(mode==='normal')return src;
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(mode==='contrast'){
      ctx.save();
      ctx.filter='contrast(2.05) brightness(1.12) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='softContrast'){
      ctx.save();
      ctx.filter='contrast(1.45) brightness(1.05) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='threshold'||mode==='thresholdLow'||mode==='thresholdHigh'||mode==='invert'){
      const img=ctx.getImageData(0,0,canvas.width,canvas.height);
      const d=img.data;
      const threshold=mode==='thresholdLow'?118:(mode==='thresholdHigh'?178:148);
      for(let i=0;i<d.length;i+=4){
        let g=(d[i]*.299+d[i+1]*.587+d[i+2]*.114)>threshold?255:0;
        if(mode==='invert')g=255-g;
        d[i]=d[i+1]=d[i+2]=g;
      }
      ctx.putImageData(img,0,0);
      return canvas;
    }
    return canvas;
  }
  /* kgg-mini-patch-v400-10-qr-gallery-bitmap-debug
     Galerie-/Fotodatenbank-QR-Fix:
     Einige Android WebViews erkennen QR-Codes per BarcodeDetector auf Kamera-Bildern,
     aber nicht zuverlässig auf Canvas-Crops aus Galerie-Dateien. Deshalb wird jeder
     Canvas-Versuch zusätzlich als PNG-Blob -> ImageBitmap dekodiert und dann erneut
     an BarcodeDetector gegeben. Außerdem bleiben Warnungen in der Scan-Vorschau sichtbar.
  */
  function scanCanvasToBlob(canvas,type,quality){
    return new Promise(resolve=>{
      try{
        canvas.toBlob(blob=>resolve(blob),type||'image/png',quality||.92);
      }catch(err){resolve(null);}
    });
  }
  async function scanDetectQrViaBitmapFromCanvas(canvas,detector){
    if(!detector||!window.createImageBitmap||!canvas||!canvas.toBlob)return '';
    let blob=null,bitmap=null;
    try{
      blob=await scanCanvasToBlob(canvas,'image/png',.92);
      if(!blob)return '';
      bitmap=await createImageBitmap(blob);
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length){
        return hits[0].rawValue||hits[0].rawData||'';
      }
    }catch(err){
      return '';
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function detectQrOnCanvas(canvas,detector){
    if(detector){
      try{
        const hits=await detector.detect(canvas).catch(()=>[]);
        if(hits&&hits.length){
          const raw=hits[0].rawValue||hits[0].rawData||'';
          if(raw)return raw;
        }
      }catch(err){}
      const bitmapRaw=await scanDetectQrViaBitmapFromCanvas(canvas,detector);
      if(bitmapRaw)return bitmapRaw;
    }
    if(window.jsQR){
      try{
        const ctx=canvas.getContext('2d',{willReadFrequently:true});
        const img=ctx.getImageData(0,0,canvas.width,canvas.height);
        const code=window.jsQR(img.data,canvas.width,canvas.height,{inversionAttempts:'attemptBoth'});
        if(code&&code.data)return code.data;
      }catch(err){}
    }
    return '';
  }
  async function scanDetectQrDirectFromFile(file,detector){
    if(!detector||!window.createImageBitmap)return '';
    let bitmap=null;
    try{
      bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length)return hits[0].rawValue||hits[0].rawData||'';
    }catch(err){
      console.warn('QR-Dateibild: Direkt-BarcodeDetector fehlgeschlagen.',err);
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function scanQrFromImageFile(file){
    const fileName=String(file&&file.name||'Bild');
    const fileType=String(file&&file.type||'unbekannter Typ');
    const fileSize=Number(file&&file.size||0);
    const heicHint=/heic|heif/i.test(fileName+' '+fileType);
    let detector=null;
    if('BarcodeDetector' in window){
      try{detector=new BarcodeDetector({formats:['qr_code']});}catch(err){detector=null;}
    }
    if(!detector&&!window.jsQR){
      return {
        raw:'',
        attempts:0,
        reason:'QR-Erkennung ist in diesem WebView nicht verfügbar. BarcodeDetector/jsQR fehlt.',
        debug:{fileName,fileType,fileSize,barcodeDetector:false,jsQR:false}
      };
    }

    const direct=await scanDetectQrDirectFromFile(file,detector);
    if(direct)return {raw:direct,attempts:1,hit:{source:'direct-bitmap',mode:'native'},debug:{fileName,fileType,fileSize}};

    const crops=[
      {id:'full',x:0,y:0,w:1,h:1},
      {id:'center',x:.08,y:.08,w:.84,h:.84},
      {id:'center-tight',x:.20,y:.20,w:.60,h:.60},
      {id:'wide-center',x:.03,y:.15,w:.94,h:.70},
      {id:'tall-center',x:.15,y:.03,w:.70,h:.94},
      {id:'top-left',x:0,y:0,w:.62,h:.62},
      {id:'top-right',x:.38,y:0,w:.62,h:.62},
      {id:'bottom-left',x:0,y:.38,w:.62,h:.62},
      {id:'bottom-right',x:.38,y:.38,w:.62,h:.62},
      {id:'top-band',x:0,y:0,w:1,h:.48},
      {id:'bottom-band',x:0,y:.52,w:1,h:.48},
      {id:'left-band',x:0,y:0,w:.48,h:1},
      {id:'right-band',x:.52,y:0,w:.48,h:1},
      {id:'top-third-left',x:0,y:0,w:.54,h:.44},
      {id:'top-third-right',x:.46,y:0,w:.54,h:.44},
      {id:'mid-third-left',x:0,y:.28,w:.54,h:.44},
      {id:'mid-third-right',x:.46,y:.28,w:.54,h:.44},
      {id:'bottom-third-left',x:0,y:.56,w:.54,h:.44},
      {id:'bottom-third-right',x:.46,y:.56,w:.54,h:.44}
    ];
    const modes=['normal','softContrast','contrast','thresholdLow','threshold','thresholdHigh','invert'];
    const maxSides=[4096,3200,2600,1800,1200];
    const rotations=[0,90,180,270];
    const seenBases=new Set();
    let attempts=1;
    let lastReason='';
    let lastCanvas='';
    for(const maxSide of maxSides){
      let base=null;
      try{
        base=await scanImageCanvasFromFile(file,maxSide);
      }catch(err){
        lastReason=err&&err.message||String(err);
        continue;
      }
      const key=base.width+'x'+base.height;
      lastCanvas=key;
      if(seenBases.has(key))continue;
```
