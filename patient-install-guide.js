(()=>{
  const VERSION='install-guide-v1';
  if(window.__kggInstallGuide===VERSION)return;
  window.__kggInstallGuide=VERSION;
  const $=id=>document.getElementById(id);
  const ua=navigator.userAgent||'';
  const isIOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  const isSamsung=/SamsungBrowser/i.test(ua);
  const isEdge=/EdgA|EdgiOS|Edg\//i.test(ua);
  const isFirefox=/Firefox|FxiOS/i.test(ua);
  const isChrome=/Chrome|CriOS/i.test(ua)&&!isEdge&&!isSamsung;
  const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone;
  function text(){
    if(standalone())return '<b>App ist installiert.</b><br>Du kannst den Plan ueber das App-Symbol oeffnen.';
    if(isIOS)return '<b>iPhone/iPad Safari:</b><br>Teilen-Symbol antippen → <b>Zum Home-Bildschirm</b> → <b>Hinzufuegen</b>.<br><br>Wenn der QR-Scan nicht klappt: QR mit der normalen iPhone-Kamera oeffnen oder Plan-Link einfuegen.';
    if(isSamsung)return '<b>Samsung Internet:</b><br>Menue <b>☰</b> oder <b>⋮</b> → <b>Seite hinzufuegen zu</b> → <b>Startbildschirm</b>.';
    if(isChrome||isEdge)return '<b>Chrome/Edge:</b><br>Wenn angeboten <b>Installieren</b> tippen. Sonst Menue <b>⋮</b> → <b>Zum Startbildschirm hinzufuegen</b>.';
    if(isFirefox)return '<b>Firefox:</b><br>Menue oeffnen → <b>Installieren</b> oder <b>Zum Startbildschirm hinzufuegen</b>. Falls das fehlt, Safari/Chrome verwenden.';
    return '<b>Installation:</b><br>Browser-Menue oeffnen und <b>Zum Startbildschirm hinzufuegen</b> waehlen.';
  }
  function show(){const box=$('installBox'),hint=$('installHint');if(box)box.classList.remove('hide');if(hint){hint.classList.remove('hide');hint.innerHTML=text();}}
  function patch(){if(typeof window.installApp==='function'&&!window.__kggInstallGuidePatched){const old=window.installApp;window.installApp=async function(){if(window.installPrompt){return old.apply(this,arguments)}show()};window.__kggInstallGuidePatched=1}const b=$('installSmall');if(b)b.classList.remove('hide')}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',patch):patch();
  setTimeout(patch,500);
})();
