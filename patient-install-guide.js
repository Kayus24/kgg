(()=>{
  const VERSION='install-guide-v82-prompt-only';
  if(window.__kggInstallGuide===VERSION)return;
  window.__kggInstallGuide=VERSION;
  const KEY='kggCurrentPlanV1';
  const $=id=>document.getElementById(id);
  const T=(de,en)=>{const i18n=window.KGGPatientI18n;if(i18n&&typeof i18n.t==='function')return i18n.t(de,en);try{return localStorage.getItem('kggPatientLang')==='en'?en:de}catch(e){return de}};
  const ua=navigator.userAgent||'';
  const isIOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  const isSamsung=/SamsungBrowser/i.test(ua);
  const isEdge=/EdgA|EdgiOS|Edg\//i.test(ua);
  const isFirefox=/Firefox|FxiOS/i.test(ua);
  const isChrome=/Chrome|CriOS/i.test(ua)&&!isEdge&&!isSamsung;
  const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone;
  function decodePlan(s){if(window.KGGPlanFormat&&typeof window.KGGPlanFormat.decodePlanText==='function')return window.KGGPlanFormat.decodePlanText(s).raw;s=String(s||'').replace(/^KGGH2:/,'').replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';return JSON.parse(decodeURIComponent(escape(atob(s))))}
  function b64enc(s){return btoa(unescape(encodeURIComponent(s))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
  function qPlan(){const q=new URLSearchParams(location.search);return q.get('plan')||q.get('kgg')||''}
  function storedWrap(){try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){return null}}
  function storedPlan(){const x=storedWrap();return x&&x.plan?x.plan:null}
  function savePlan(raw){localStorage.setItem(KEY,JSON.stringify({plan:raw,importedAt:new Date().toISOString(),source:'query-plan'}))}
  function dir(){return location.pathname.replace(/[^\/]*$/,'')}
  function planLink(raw){const payload=window.KGGPlanFormat&&typeof window.KGGPlanFormat.encodeKggH3==='function'?window.KGGPlanFormat.encodeKggH3(raw):'KGGH2:'+b64enc(JSON.stringify(raw));return location.origin+dir()+'ios-start.html?plan='+encodeURIComponent(payload)}
  function currentPlanLink(){const raw=storedPlan();return raw?planLink(raw):''}
  function importQueryPlan(){const qp=qPlan();if(!qp)return false;try{const raw=decodePlan(qp),payload=window.KGGPlanFormat&&typeof window.KGGPlanFormat.encodeKggH3==='function'?window.KGGPlanFormat.encodeKggH3(raw):'KGGH2:'+b64enc(JSON.stringify(raw));savePlan(raw);if(!/^#KGGH[23]:/i.test(location.hash)){location.replace(location.origin+dir()+'#'+payload);return true}return true}catch(e){return false}}
  if(importQueryPlan())return;
  function iosText(){const link=currentPlanLink();return T('<b>iPhone/iPad:</b><br>1. Unten den <b>iPhone-Planlink</b> oeffnen.<br>2. Auf dieser neuen Seite in Safari <b>Teilen</b> antippen.<br>3. <b>Zum Home-Bildschirm</b> waehlen.<br>4. <b>Hinzufuegen</b> tippen.<br><br><b>Wichtig:</b> Nicht als Favorit speichern.','<b>iPhone/iPad:</b><br>1. Open the <b>iPhone plan link</b> below.<br>2. On the new page in Safari, tap <b>Share</b>.<br>3. Select <b>Add to Home Screen</b>.<br>4. Tap <b>Add</b>.<br><br><b>Important:</b> Do not save it as a favourite.')+(link?'<br><br><a class="btn" href="'+link+'">'+T('iPhone-Planlink oeffnen','Open iPhone plan link')+'</a>':'')}
  function text(){if(standalone())return T('<b>App ist installiert.</b><br>Wenn kein Plan erscheint, den QR-Code oder iPhone-Planlink noch einmal in Safari oeffnen.','<b>The app is installed.</b><br>If no plan appears, open the QR code or iPhone plan link again in Safari.');if(isIOS)return iosText();if(isSamsung)return T('<b>Samsung Internet:</b><br>Menue <b>☰</b> oder <b>⋮</b> → <b>Seite hinzufuegen zu</b> → <b>Startbildschirm</b>.','<b>Samsung Internet:</b><br>Menu <b>☰</b> or <b>⋮</b> → <b>Add page to</b> → <b>Home screen</b>.');if(isChrome||isEdge)return T('<b>Chrome/Edge:</b><br>Wenn angeboten <b>Installieren</b> tippen. Sonst Menue <b>⋮</b> → <b>Zum Startbildschirm hinzufuegen</b>.','<b>Chrome/Edge:</b><br>Tap <b>Install</b> if offered. Otherwise, menu <b>⋮</b> → <b>Add to Home screen</b>.');if(isFirefox)return T('<b>Firefox:</b><br>Menue oeffnen → <b>Installieren</b> oder <b>Zum Startbildschirm hinzufuegen</b>. Falls das fehlt, Safari/Chrome verwenden.','<b>Firefox:</b><br>Open the menu → <b>Install</b> or <b>Add to Home screen</b>. If unavailable, use Safari/Chrome.');return T('<b>Installation:</b><br>Browser-Menue oeffnen und <b>Zum Startbildschirm hinzufuegen</b> waehlen.','<b>Installation:</b><br>Open the browser menu and select <b>Add to Home screen</b>.')}
  function recover(){if(!standalone())return;const st=$('status');if(st&&/Kein Plan gefunden|No plan found/i.test(st.textContent||'')){st.innerHTML=T('Kein Plan gefunden. Bitte den iPhone-Planlink oder QR-Code erneut in Safari oeffnen.','No plan found. Please open the iPhone plan link or QR code again in Safari.');st.className='status warn'}}
  function show(){const box=$('installBox'),hint=$('installHint');if(box)box.classList.remove('hide');if(hint){hint.classList.remove('hide');hint.innerHTML=text()}}
  function updateBanner(){if($('kggUpdateGate'))return;const d=document.createElement('div');d.id='kggUpdateGate';d.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:10020;max-width:720px;margin:auto;background:#fff;border:1px solid #93c5fd;border-radius:18px;padding:14px;box-shadow:0 18px 46px #0f172a33;font-weight:850';d.innerHTML='<b>'+T('Neue Version verfuegbar.','New version available.')+'</b><br><span style="color:#64748b">'+T('Bitte aktualisieren, damit der Plan richtig funktioniert.','Please update so the plan works correctly.')+'</span><button id="kggUpdateNow" style="width:100%;min-height:48px;margin-top:10px;border-radius:14px;border:0;background:#111827;color:#fff;font-size:16px;font-weight:950">'+T('Jetzt aktualisieren','Update now')+'</button>';document.body.appendChild(d);$('kggUpdateNow').onclick=()=>location.reload()}
  function listenUpdates(){if(!('serviceWorker'in navigator)||window.__kggUpdateGateListen)return;window.__kggUpdateGateListen=1;navigator.serviceWorker.addEventListener('message',e=>{if(e&&e.data&&e.data.type==='APP_UPDATE_READY')updateBanner()})}
  function autoDay(){if(window.__kggAutoDayRan)return;window.__kggAutoDayRan=1;try{if(typeof p==='undefined'||!p||typeof d==='undefined'||!Array.isArray(done))return;let target=done.length?Math.max(...done)+1:d;if(target<1)target=1;if(target>p.days&&p.extendDays){p.days+=Number(p.stepDays)||6;const w=storedWrap();if(w&&w.plan){w.plan.d=p.days;localStorage.setItem(KEY,JSON.stringify(w))}}if(target<=p.days&&target!==d){d=target;if(typeof save==='function')save();if(typeof render==='function')render();if(typeof setStatus==='function')setStatus(T('Aktuelles Training: Tag ','Current training: day ')+d+'.','ok')}}catch(e){}}
  function refreshLanguage(){
    recover();const hint=$('installHint'),banner=$('kggUpdateGate');if(hint&&hint.innerHTML&&!hint.classList.contains('hide'))hint.innerHTML=text();
    if(banner){const title=banner.querySelector('b'),message=banner.querySelector('span'),button=$('kggUpdateNow');if(title)title.textContent=T('Neue Version verfuegbar.','New version available.');if(message)message.textContent=T('Bitte aktualisieren, damit der Plan richtig funktioniert.','Please update so the plan works correctly.');if(button)button.textContent=T('Jetzt aktualisieren','Update now')}
  }
  if(typeof window.addEventListener==='function')window.addEventListener('kgg-patient-languagechange',refreshLanguage);
  function patch(){recover();listenUpdates();const box=$('installBox'),text=$('installOfferText'),button=$('installOfferBtn'),hint=$('installHint');if(!window.__kggInstallPrompt){if(box)box.classList.add('hide');if(text)text.classList.add('hide');if(button)button.classList.add('hide');if(hint){hint.classList.add('hide');hint.innerHTML=''}}}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',patch):patch();
  setTimeout(patch,500);setTimeout(patch,1500);setTimeout(autoDay,900);setTimeout(autoDay,2200);
})();
