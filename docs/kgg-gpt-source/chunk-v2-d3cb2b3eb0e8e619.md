<!-- KGG PATCH START kgg-v061-cross-app-live-qr-camera -->
<!-- PAT Live-QR-Kamera fuer Admin -->
<style id="kgg-v061-cross-app-live-qr-camera-style">
.kggLiveQrCamera{position:fixed;inset:0;z-index:100120;display:grid;grid-template-rows:auto minmax(0,1fr) auto;background:#05070b;color:#fff}.kggLiveQrCamera[hidden]{display:none}.kggLiveQrHead,.kggLiveQrActions{display:flex;align-items:center;gap:12px;padding:12px 14px;background:#05070bf2}.kggLiveQrHead{justify-content:space-between}.kggLiveQrHead b{font-size:16px}.kggLiveQrClose{width:42px;height:42px;border:1px solid #ffffff55;border-radius:50%;background:#ffffff1f;color:#fff;font-size:25px}.kggLiveQrStage{position:relative;min-height:0;display:grid;place-items:center;overflow:hidden;background:#000}.kggLiveQrVideo{width:100%;height:100%;object-fit:contain;background:#000}.kggLiveQrGuide{position:absolute;inset:9% 8%;border:3px solid #fff;border-radius:18px;box-shadow:0 0 0 9999px #00000024;pointer-events:none}.kggLiveQrStatus{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);max-width:92%;padding:8px 12px;border-radius:999px;background:#000c;text-align:center;font-size:13px;font-weight:850}.kggLiveQrActions{display:grid;grid-template-columns:1fr auto 1fr;padding-bottom:max(18px,env(safe-area-inset-bottom,0px))}.kggLiveQrFallback{justify-self:start;border:1px solid #ffffff66;border-radius:12px;background:transparent;color:#fff;padding:10px 12px;font-weight:850}.kggLiveQrShutter{width:74px;height:74px;border:6px solid #fff;border-radius:50%;background:#fff;box-shadow:inset 0 0 0 5px #111}.kggLiveQrHint{justify-self:end;max-width:130px;color:#dbe5f1;font-size:12px;font-weight:750;text-align:right}@media(max-width:430px){.kggLiveQrGuide{inset:14% 5%}.kggLiveQrActions{padding-left:10px;padding-right:10px}.kggLiveQrHint{max-width:90px}}
</style>
<script id="kgg-v061-cross-app-live-qr-camera-script">
(function(){
  'use strict';
  const PATCH_ID='kgg-v061-cross-app-live-qr-camera';
  const LIVE_VARIANTS=[
    {crop:1,max:1280},
    {crop:.82,max:1280,upscale:1.5},
    {crop:.62,max:1280,upscale:2},
    {crop:1,max:1280,contrast:1.35},
    {crop:.82,max:1280,upscale:1.5,contrast:1.35},
    {crop:.62,max:1280,upscale:2,contrast:1.35}
  ];
  let session=null;
  function getScan(){return window.KGGScan||null;}
  function nativeCapabilities(){
    try{return window.KGGNativeCamera&&typeof window.KGGNativeCamera.getCapabilities==='function'?window.KGGNativeCamera.getCapabilities():null;}
    catch(err){return null;}
  }
  function supportsLiveCamera(){
    if(!navigator.mediaDevices||typeof navigator.mediaDevices.getUserMedia!=='function')return false;
    const caps=nativeCapabilities();
    return !caps||caps.platform!=='android'||(caps.webVideoCapture===true&&Number(caps.webVideoCaptureVersion)>=1);
  }
  function ensureUi(){
    let root=document.getElementById(PATCH_ID+'-camera');
    if(root)return root;
    root=document.createElement('div');
    root.id=PATCH_ID+'-camera';
    root.className='kggLiveQrCamera';
    root.hidden=true;
    root.innerHTML='<div class="kggLiveQrHead"><b>Plan-QR automatisch scannen</b><button type="button" class="kggLiveQrClose" aria-label="Kamera schliessen">&times;</button></div><div class="kggLiveQrStage"><video class="kggLiveQrVideo" autoplay playsinline muted></video><div class="kggLiveQrGuide" aria-hidden="true"></div><div class="kggLiveQrStatus" role="status">Kamera wird gestartet ...</div></div><div class="kggLiveQrActions"><button type="button" class="kggLiveQrFallback">Systemkamera</button><button type="button" class="kggLiveQrShutter" aria-label="Papierfoto aufnehmen"></button><span class="kggLiveQrHint">QR automatisch, Papier manuell</span></div>';
    document.body.appendChild(root);
    root.querySelector('.kggLiveQrClose').addEventListener('click',closeCamera);
    root.querySelector('.kggLiveQrShutter').addEventListener('click',capturePaperPhoto);
    return root;
  }
  function setStatus(text){
    const node=document.querySelector('#'+PATCH_ID+'-camera .kggLiveQrStatus');
    if(node)node.textContent=text;
  }
  function stopSession(){
    const current=session;
    session=null;
    if(!current)return;
    current.active=false;
    clearTimeout(current.timer);
    try{current.stream&&current.stream.getTracks().forEach(function(track){track.stop();});}catch(err){}
    try{current.video.srcObject=null;}catch(err){}
  }
  function closeCamera(){
    stopSession();
    const root=document.getElementById(PATCH_ID+'-camera');
    if(root)root.hidden=true;
  }
  function sourceSize(source){return {w:Number(source.videoWidth||source.width)||0,h:Number(source.videoHeight||source.height)||0};}
  function renderVariant(source,variant){
    const size=sourceSize(source);
    if(!size.w||!size.h)return null;
    const crop=variant.crop||1;
    const sw=Math.max(1,Math.round(size.w*crop));
    const sh=Math.max(1,Math.round(size.h*crop));
    const sx=Math.round((size.w-sw)/2);
    const sy=Math.round((size.h-sh)/2);
    const scale=Math.min(variant.upscale||1,(variant.max||1280)/Math.max(sw,sh));
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(sw*scale));
    canvas.height=Math.max(1,Math.round(sh*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.imageSmoothingEnabled=true;
    ctx.imageSmoothingQuality='high';
    if(variant.contrast)ctx.filter='contrast('+variant.contrast+')';
    ctx.drawImage(source,sx,sy,sw,sh,0,0,canvas.width,canvas.height);
    return canvas;
  }
  async function createDetector(){
    if(!('BarcodeDetector' in window))return null;
    try{
      if(typeof BarcodeDetector.getSupportedFormats==='function'){
        const formats=await BarcodeDetector.getSupportedFormats();
        if(Array.isArray(formats)&&!formats.includes('qr_code'))return null;
      }
      return new BarcodeDetector({formats:['qr_code']});
    }catch(err){return null;}
  }
  async function detectFrame(current){
    if(current.detector){
      try{
        const hits=await current.detector.detect(current.video);
        if(hits&&hits[0])return {raw:hits[0].rawValue||'',decoder:'barcode-detector'};
      }catch(err){current.detector=null;}
    }
    if(typeof window.jsQR!=='function')return {raw:'',decoder:'none'};
    const variant=LIVE_VARIANTS[current.variant%LIVE_VARIANTS.length];
    current.variant++;
    const canvas=renderVariant(current.video,variant);
    if(!canvas)return {raw:'',decoder:'jsqr'};
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const image=ctx.getImageData(0,0,canvas.width,canvas.height);
    const hit=window.jsQR(image.data,canvas.width,canvas.height,{inversionAttempts:'attemptBoth'});
    return {raw:hit&&hit.data||'',decoder:'jsqr'};
  }
  async function scanLoop(current){
    if(!current.active||session!==current)return;
    if(current.busy){current.timer=setTimeout(function(){scanLoop(current);},220);return;}
    if(Date.now()-current.startedAt>30000){
      setStatus('Noch kein KGG-QR erkannt. Naeher herangehen oder Systemkamera verwenden.');
      current.timer=setTimeout(function(){scanLoop(current);},600);
      return;
    }
    current.busy=true;
    try{
      if(current.video.readyState>=2){
        const hit=await detectFrame(current);
        if(hit.raw){
          setStatus('QR erkannt, Inhalt wird geprueft ...');
          const scan=getScan();
          const result=scan&&typeof scan.handleQrRaw==='function'?await scan.handleQrRaw(hit.raw,'live-camera:'+hit.decoder):null;
          if(result&&result.type!=='invalidQr'){
            closeCamera();
            return;
          }
          setStatus('QR erkannt, aber kein lesbarer KGG-Code. Suche weiter ...');
        }else{
          setStatus('Suche KGG-Plan-QR ...');
        }
      }
    }catch(err){setStatus('Bild wird weiter geprueft ...');}
    finally{current.busy=false;}
    if(current.active&&session===current)current.timer=setTimeout(function(){scanLoop(current);},220);
  }
  function frameFile(video){
    if(!video||!video.videoWidth||!video.videoHeight)return Promise.reject(new Error('Kamerabild noch nicht bereit.'));
    const canvas=document.createElement('canvas');
    canvas.width=video.videoWidth;
    canvas.height=video.videoHeight;
    canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
    return new Promise(function(resolve,reject){
      canvas.toBlob(function(blob){
        if(!blob)return reject(new Error('Foto konnte nicht erstellt werden.'));
        resolve(new File([blob],'Kamera-Foto-'+Date.now()+'.jpg',{type:'image/jpeg',lastModified:Date.now()}));
      },'image/jpeg',.92);
    });
  }
  async function capturePaperPhoto(){
    const current=session;
    if(!current||current.busy)return;
    current.busy=true;
    try{
      setStatus('Papierfoto wird verarbeitet ...');
      const file=await frameFile(current.video);
      closeCamera();
      const scan=getScan();
      if(!scan||typeof scan.handleInput!=='function')throw new Error('Scan-Verarbeitung nicht bereit.');
      await scan.handleInput({files:[file],value:''},'camera');
    }catch(err){
      if(session===current){current.busy=false;setStatus(err&&err.message||'Aufnahme fehlgeschlagen.');}
    }
  }
  async function openCamera(originalPick){
    closeCamera();
    if(!supportsLiveCamera()){originalPick('camera');return;}
    const root=ensureUi();
    root.hidden=false;
    root.querySelector('.kggLiveQrFallback').onclick=function(){closeCamera();originalPick('camera');};
    setStatus('Kamera wird gestartet ...');
    try{
      const stream=await navigator.mediaDevices.getUserMedia({
        audio:false,
        video:{facingMode:{ideal:'environment'},width:{ideal:1920},height:{ideal:1080},frameRate:{ideal:10,max:15}}
      });
      const video=root.querySelector('video');
      const current={active:true,busy:false,stream:stream,video:video,detector:null,variant:0,startedAt:Date.now(),timer:0};
      session=current;
      video.srcObject=stream;
      await video.play();
      current.detector=await createDetector();
      setStatus(current.detector||typeof window.jsQR==='function'?'Suche KGG-Plan-QR ...':'Automatische QR-Erkennung fehlt. Papierfoto ist weiter moeglich.');
      if(current.detector||typeof window.jsQR==='function')scanLoop(current);
    }catch(err){
      closeCamera();
      originalPick('camera');
    }
  }
  function install(){
    const scan=getScan();
    if(!scan||typeof scan.pick!=='function'||typeof scan.handleQrRaw!=='function'||scan.__kggLiveQrCameraInstalled)return false;
    const originalPick=scan.pick.bind(scan);
    scan.openLiveCamera=function(){return openCamera(originalPick);};
    scan.closeLiveCamera=closeCamera;
    scan.pick=function(kind){return kind==='file'?originalPick('file'):openCamera(originalPick);};
    scan.__kggLiveQrCameraInstalled=true;
    window.KGG_PATCHES=window.KGG_PATCHES||{};
    window.KGG_PATCHES[PATCH_ID]={installed:true,kind:'cross-app-camera-qr'};
    return true;
  }
  if(!install())window.addEventListener('load',install,{once:true});
  document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')closeCamera();});
  window.addEventListener('pagehide',closeCamera);
})();
</script>
<!-- KGG PATCH END kgg-v061-cross-app-live-qr-camera -->
