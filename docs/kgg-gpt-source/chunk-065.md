# KGG Source Chunk 065

- Source: `kgg-update/src` modular source
- Lines: 27301-27672

```html
    return {};
  }

  function fileName(value){
    var clean=String(value||"").split(/[?#]/)[0].replace(/\\/g,"/");
    var parts=clean.split("/").filter(Boolean);
    var last=parts.pop()||"";
    try{return decodeURIComponent(last);}catch(err){return last;}
  }

  function buildInfo(){
    try{if(typeof KGG_BUILD_INFO!=="undefined"&&KGG_BUILD_INFO)return KGG_BUILD_INFO;}catch(err){}
    if(window.KGG_BUILD_INFO)return window.KGG_BUILD_INFO;
    try{
      var source=document.getElementById("kgg-source-truth");
      var data=source?JSON.parse(source.textContent||"{}"):{};
      var current=data.currentVersion||{};
      var code=Number(current.versionCode);
      if(Number.isFinite(code))return {release:"v"+String(code).padStart(3,"0"),versionName:current.versionName||"",htmlFile:"kgg-update/index.html"};
    }catch(err){}
    return {};
  }

  function currentIdentity(){
    var native=nativeStatus();
    var info=buildInfo();
    var path=String((window.location&&window.location.pathname)||"");
    var release=String(native.releaseId||"").trim();
    var pathRelease=path.match(/\/releases\/web\/(r[0-9]+)\//i);
    if(!release&&pathRelease)release=pathRelease[1].toLowerCase();
    var build=info.release||"";
    var source=fileName(native.loadedHtmlSource)||fileName(path)||fileName(info.htmlFile)||"index.html";
    var parts=[];
    if(release)parts.push(release);
    if(build&&build!==release)parts.push(build);
    parts.push(source);
    return "HTML "+parts.join(" · ");
  }

  function render(){
    var label=document.getElementById("kggTabletHtmlReleaseLabel");
    if(!label)return;
    var text=currentIdentity();
    label.textContent=text;
    label.title=text;
  }

  function install(){
    var menu=document.getElementById("tabletSideMenu");
    if(!menu)return false;
    var label=document.getElementById("kggTabletHtmlReleaseLabel");
    if(!label){
      label=document.createElement("small");
      label.id="kggTabletHtmlReleaseLabel";
      label.setAttribute("aria-label","Aktuell geladene HTML-Version");
      menu.appendChild(label);
    }
    render();
    var button=document.getElementById("tabletMenuBtn");
    if(button&&!button.dataset.kggHtmlReleaseLabelBound){
      button.dataset.kggHtmlReleaseLabelBound="1";
      button.addEventListener("click",function(){window.setTimeout(render,0);});
    }
    return true;
  }

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  window.addEventListener("pageshow",render);
  document.addEventListener("visibilitychange",function(){if(!document.hidden)render();});

  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true,render:render,currentIdentity:currentIdentity};
})();
</script>
<!-- KGG PATCH END kgg-v060-tablet-html-release-label -->

<!-- SOURCE FILE: kgg-update/src/patches/v061-cross-app-live-qr-camera.html -->
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

<!-- SOURCE FILE: kgg-update/src/patches/v062-tablet-recent-package-shell-geometry.html -->
<!-- KGG PATCH START kgg-v062-tablet-recent-package-shell-geometry -->
<!-- Plan-Historie mit stabiler Hintergrund-Geometrie -->
<style id="kgg-v062-tablet-recent-package-shell-geometry-style">
.tabletRecentHost[hidden]{display:none!important;}
@media (min-width:760px){
  body.tabletLayoutCustom.tabletMenuOpen.tabletPackageOverlayOpen .app{
    width:calc(100vw - var(--kgg-tablet-sidebar-w,380px))!important;
    max-width:calc(100vw - var(--kgg-tablet-sidebar-w,380px))!important;
    transform:translateX(var(--kgg-tablet-sidebar-w,380px))!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay .tabletPackageSearch,
  body.tabletRecentOverlayMode #tabletPackageOverlay #tabletPackageCards{
    display:none!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #tabletRecentHost{
    display:grid!important;
    grid-template-columns:minmax(0,1fr);
    gap:12px;
    min-height:0;
    overflow:auto;
    padding:2px 2px 8px;
    overscroll-behavior:contain;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #recentList:not(.hidden){
    display:grid!important;
    gap:12px!important;
    position:static!important;
    inset:auto!important;
    left:auto!important;
    right:auto!important;
    top:auto!important;
    bottom:auto!important;
    width:100%!important;
    max-width:none!important;
    max-height:none!important;
    overflow:visible!important;
    z-index:auto!important;
    margin:0!important;
    padding:0!important;
    background:transparent!important;
    border:0!important;
    border-radius:0!important;
    box-shadow:none!important;
    transform:none!important;
    animation:none!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #recentList>.notice{margin:0!important;}
  body.tabletRecentOverlayMode #tabletMenuRecentBtn{background:#eef5ff!important;color:#071027!important;box-shadow:inset 3px 0 0 #0b63ce,0 8px 18px rgba(7,16,39,.08)!important;}
  body.tabletRecentOverlayMode #tabletMenuPackagesBtn{background:#fff!important;color:#0a1024!important;box-shadow:0 10px 22px rgba(10,16,36,.07),inset 0 1px 0 rgba(255,255,255,.82)!important;}
}
</style>
<script id="kgg-v062-tablet-recent-package-shell-geometry">
(function(){
  'use strict';
  var PATCH_ID='kgg-v062-tablet-recent-package-shell-geometry';
  var TABLET_QUERY='(min-width:760px)';
  var recentMode=false,allowPackageClick=false,returnFocusAfterClose=false,closeCleanupTimer=0,focusTimer=0,opener=null,originMarker=null,originParent=null,originNext=null,shellDefaults=null;
  function byId(id){return document.getElementById(id);}
  function isTablet(){return !!(window.matchMedia&&window.matchMedia(TABLET_QUERY).matches&&document.body&&document.body.classList.contains('tabletLayoutCustom'));}
  function shellParts(){var overlay=byId('tabletPackageOverlay');return {overlay:overlay,shade:byId('tabletPackageShade'),close:byId('tabletPackageClose'),search:overlay&&overlay.querySelector('.tabletPackageSearch'),cards:byId('tabletPackageCards'),titleIcon:overlay&&overlay.querySelector('.tabletPackageTitle span'),titleText:overlay&&overlay.querySelector('.tabletPackageTitle strong')};}
  function rememberShellDefaults(parts){if(shellDefaults||!parts.overlay)return;shellDefaults={overlayLabel:parts.overlay.getAttribute('aria-label')||'Uebungspakete',closeLabel:parts.close&&parts.close.getAttribute('aria-label')||'Uebungspakete schliessen',icon:parts.titleIcon&&parts.titleIcon.textContent||'📦',title:parts.titleText&&parts.titleText.textContent||'Übungspakete'};}
  function ensureRecentHost(){var parts=shellParts(),recent=byId('recentList');if(!parts.overlay||!recent)return null;rememberShellDefaults(parts);var host=byId('tabletRecentHost');if(!host){host=document.createElement('div');host.id='tabletRecentHost';host.className='tabletRecentHost';host.hidden=true;parts.overlay.appendChild(host);}if(!originMarker||!originMarker.parentNode){originParent=recent.parentNode;originNext=recent.nextSibling;originMarker=document.createComment('kgg-tablet-recent-origin');if(originParent)originParent.insertBefore(originMarker,recent);}return host;}
  function restoreRecentNode(){var recent=byId('recentList');if(!recent)return;if(originMarker&&originMarker.parentNode){originMarker.parentNode.insertBefore(recent,originMarker.nextSibling);return;}if(originParent){var next=originNext&&originNext.parentNode===originParent?originNext:null;originParent.insertBefore(recent,next);}}
  function setExpanded(id,value){var el=byId(id);if(el)el.setAttribute('aria-expanded',String(!!value));}
  function setRecentChrome(){var parts=shellParts();rememberShellDefaults(parts);if(parts.overlay)parts.overlay.setAttribute('aria-label','Plan-Historie');if(parts.close)parts.close.setAttribute('aria-label','Plan-Historie schliessen');if(parts.titleIcon)parts.titleIcon.textContent='🕘';if(parts.titleText)parts.titleText.textContent='Plan-Historie';setExpanded('tabletMenuRecentBtn',true);setExpanded('recentToggle',true);setExpanded('tabletMenuPackagesBtn',false);setExpanded('packageToggle',false);}
  function restorePackageChrome(keepOverlay){var parts=shellParts();if(shellDefaults){if(parts.overlay)parts.overlay.setAttribute('aria-label',shellDefaults.overlayLabel);if(parts.close)parts.close.setAttribute('aria-label',shellDefaults.closeLabel);if(parts.titleIcon)parts.titleIcon.textContent=shellDefaults.icon;if(parts.titleText)parts.titleText.textContent=shellDefaults.title;}setExpanded('tabletMenuRecentBtn',false);setExpanded('recentToggle',false);setExpanded('tabletMenuPackagesBtn',!!keepOverlay);setExpanded('packageToggle',!!keepOverlay);}
  function focusRecentEntry(){clearTimeout(focusTimer);focusTimer=setTimeout(function(){if(!recentMode)return;var recent=byId('recentList');var target=recent&&recent.querySelector('[data-recent-index]');if(!target)target=byId('tabletPackageClose');if(target&&target.focus)target.focus();},80);}
  function cleanupTabletRecentMode(options){options=options||{};if(!recentMode&&!document.body.classList.contains('tabletRecentOverlayMode'))return;clearTimeout(closeCleanupTimer);clearTimeout(focusTimer);var focusTarget=opener;var keepOverlay=!!options.keepOverlay&&document.body.classList.contains('tabletPackageOverlayOpen');recentMode=false;document.body.classList.remove('tabletRecentOverlayMode');var recent=byId('recentList');if(recent)recent.classList.add('hidden');restoreRecentNode();var host=byId('tabletRecentHost');if(host)host.hidden=true;restorePackageChrome(keepOverlay);opener=null;returnFocusAfterClose=false;if(options.focus&&focusTarget&&focusTarget.isConnected&&focusTarget.focus){setTimeout(function(){try{focusTarget.focus();}catch(err){}},0);}}
  function scheduleClosedCleanup(){clearTimeout(closeCleanupTimer);closeCleanupTimer=setTimeout(function(){if(recentMode&&!document.body.classList.contains('tabletPackageOverlayOpen'))cleanupTabletRecentMode({focus:returnFocusAfterClose});},240);}
  function openOriginalPackageShell(){if(document.body.classList.contains('tabletPackageOverlayOpen'))return true;var button=byId('tabletMenuPackagesBtn')||byId('packageToggle');if(!button)return false;allowPackageClick=true;try{button.click();}finally{allowPackageClick=false;}return document.body.classList.contains('tabletPackageOverlayOpen');}
  function openTabletRecentInPackageShell(source){if(!isTablet())return false;if(recentMode){returnFocusAfterClose=true;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:true});return true;}var host=ensureRecentHost(),recent=byId('recentList');if(!host||!recent)return false;opener=source||byId('tabletMenuRecentBtn')||byId('recentToggle');recent.classList.add('hidden');['--kgg-overlay-width','--kgg-overlay-left','--kgg-overlay-top','--kgg-overlay-max-height','--kgg-overlay-origin'].forEach(function(name){recent.style.removeProperty(name);});if(!openOriginalPackageShell())return false;document.body.classList.add('tabletRecentOverlayMode');recentMode=true;returnFocusAfterClose=false;host.hidden=false;host.appendChild(recent);recent.classList.remove('hidden');setRecentChrome();focusRecentEntry();return true;}
  function switchToPackages(){if(!recentMode)return false;cleanupTabletRecentMode({keepOverlay:true,focus:false});clearTimeout(focusTimer);focusTimer=setTimeout(function(){var input=byId('tabletPackageSearch');if(input&&input.focus)input.focus();},60);return true;}
  function closeAfterRecentRestore(){setTimeout(function(){if(!recentMode)return;returnFocusAfterClose=false;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:false});},0);}
  function captureTabletClicks(ev){var target=ev.target&&ev.target.closest?ev.target.closest('button,#tabletPackageShade'):null;if(!target)return;if(recentMode){var restore=ev.target.closest&&ev.target.closest('#tabletRecentHost [data-recent-index]');if(restore){returnFocusAfterClose=false;closeAfterRecentRestore();return;}if((target.id==='tabletMenuPackagesBtn'||target.id==='packageToggle')&&!allowPackageClick){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();switchToPackages();return;}if(target.id==='tabletMenuRecentBtn'||target.id==='recentToggle'){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();returnFocusAfterClose=true;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:true});return;}if(target.id==='tabletPackageClose'||target.id==='tabletPackageShade'){returnFocusAfterClose=true;return;}if(target.id==='tabletMenuClose'||target.id==='tabletMenuBtn'||target.id==='tabletSideBackdrop'||target.closest('.tabletSideMenuAction'))returnFocusAfterClose=false;}if(!isTablet()||allowPackageClick)return;if(target.id==='tabletMenuRecentBtn'||target.id==='recentToggle'){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();openTabletRecentInPackageShell(target);}}
  function install(){if(!document.body)return;ensureRecentHost();document.addEventListener('click',captureTabletClicks,true);document.addEventListener('keydown',function(ev){if(recentMode&&ev.key==='Escape')returnFocusAfterClose=true;},true);new MutationObserver(function(){if(recentMode&&!document.body.classList.contains('tabletPackageOverlayOpen'))scheduleClosedCleanup();}).observe(document.body,{attributes:true,attributeFilter:['class']});var recent=byId('recentList');if(recent)new MutationObserver(function(){if(recentMode&&recent.classList.contains('hidden')&&document.body.classList.contains('tabletPackageOverlayOpen'))closeAfterRecentRestore();}).observe(recent,{attributes:true,attributeFilter:['class']});var cleanupViewport=function(){if(recentMode&&!isTablet())cleanupTabletRecentMode({focus:false});};window.addEventListener('resize',function(){setTimeout(cleanupViewport,40);},{passive:true});window.addEventListener('orientationchange',function(){setTimeout(cleanupViewport,140);},{passive:true});window.addEventListener('pageshow',cleanupViewport,{passive:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
  window.KGG_TABLET_RECENT_PACKAGE_SHELL={patchId:PATCH_ID,open:openTabletRecentInPackageShell,cleanup:cleanupTabletRecentMode,switchToPackages:switchToPackages};
  window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true,kind:'kgg-tablet-recent-package-shell-geometry'};
})();
</script>
<!-- KGG PATCH END kgg-v062-tablet-recent-package-shell-geometry -->

<!-- SOURCE FILE: kgg-update/src/footer.html -->

</body>
</html>
```
