(()=>{
  const VERSION='install-guide-v4-query-update-daystart';
  if(window.__kggInstallGuide===VERSION)return;
  window.__kggInstallGuide=VERSION;
  const KEY='kggCurrentPlanV1';
  const $=id=>document.getElementById(id);
  const ua=navigator.userAgent||'';
  const isIOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  const isSamsung=/SamsungBrowser/i.test(ua);
  const isEdge=/EdgA|EdgiOS|Edg\//i.test(ua);
  const isFirefox=/Firefox|FxiOS/i.test(ua);
  const isChrome=/Chrome|CriOS/i.test(ua)&&!isEdge&&!isSamsung;
  const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone;
  function b64dec(s){s=String(s||'').replace(/^KGGH2:/,'').replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';return decodeURIComponent(escape(atob(s)))}
  function b64enc(s){return btoa(unescape(encodeURIComponent(s))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
  function qPlan(){const q=new URLSearchParams(location.search);return q.get('plan')||q.get('kgg')||''}
  function storedWrap(){try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){return null}}
  function storedPlan(){const x=storedWrap();return x&&x.plan?x.plan:null}
  function savePlan(raw){localStorage.setItem(KEY,JSON.stringify({plan:raw,importedAt:new Date().toISOString(),source:'query-plan'}))}
  function planLink(raw){const payload='KGGH2:'+b64enc(JSON.stringify(raw));return location.origin+location.pathname+'?plan='+encodeURIComponent(payload)}
  function currentPlanLink(){const raw=storedPlan();return raw?planLink(raw):''}
  function importQueryPlan(){const qp=qPlan();if(!qp)return false;try{const raw=JSON.parse(b64dec(qp));savePlan(raw);if(!location.hash.startsWith('#KGGH2:')){location.replace(location.origin+location.pathname+'#KGGH2:'+b64enc(JSON.stringify(raw)));return true}return true}catch(e){return false}}
  if(importQueryPlan())return;
  function iosText(){const link=currentPlanLink();return '<b>iPhone/iPad:</b><br>1. Erst den Plan-Link unten oeffnen.<br>2. Dann in Safari auf <b>Teilen</b> tippen.<br>3. <b>Zum Home-Bildschirm</b> waehlen.<br>4. <b>Hinzufuegen</b> tippen.<br><br><b>Wichtig:</b> Nicht nur als Favorit speichern.'+(link?'<br><br><a class="btn" href="'+link+'">iPhone-Planlink oeffnen</a>':'')}
  function text(){if(standalone())return '<b>App ist installiert.</b><br>Wenn kein Plan erscheint, den QR-Code oder iPhone-Planlink noch einmal in Safari oeffnen.';if(isIOS)return iosText();if(isSamsung)return '<b>Samsung Internet:</b><br>Menue <b>☰</b> oder <b>⋮</b> → <b>Seite hinzufuegen zu</b> → <b>Startbildschirm</b>.';if(isChrome||isEdge)return '<b>Chrome/Edge:</b><br>Wenn angeboten <b>Installieren</b> tippen. Sonst Menue <b>⋮</b> → <b>Zum Startbildschirm hinzufuegen</b>.';if(isFirefox)return '<b>Firefox:</b><br>Menue oeffnen → <b>Installieren</b> oder <b>Zum Startbildschirm hinzufuegen</b>. Falls das fehlt, Safari/Chrome verwenden.';return '<b>Installation:</b><br>Browser-Menue oeffnen und <b>Zum Startbildschirm hinzufuegen</b> waehlen.'}
  function recover(){if(!standalone())return;const st=$('status');if(st&&/Kein Plan gefunden/i.test(st.textContent||'')){st.innerHTML='Kein Plan gefunden. Bitte den iPhone-Planlink oder QR-Code erneut in Safari oeffnen.';st.className='status warn'}}
  function show(){const box=$('installBox'),hint=$('installHint');if(box)box.classList.remove('hide');if(hint){hint.classList.remove('hide');hint.innerHTML=text()}}
  function updateBanner(){if($('kggUpdateGate'))return;const d=document.createElement('div');d.id='kggUpdateGate';d.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:10020;max-width:720px;margin:auto;background:#fff;border:1px solid #93c5fd;border-radius:18px;padding:14px;box-shadow:0 18px 46px #0f172a33;font-weight:850';d.innerHTML='<b>Neue Version verfuegbar.</b><br><span style="color:#64748b">Bitte aktualisieren, damit der Plan richtig funktioniert.</span><button id="kggUpdateNow" style="width:100%;min-height:48px;margin-top:10px;border-radius:14px;border:0;background:#111827;color:#fff;font-size:16px;font-weight:950">Jetzt aktualisieren</button>';document.body.appendChild(d);$('kggUpdateNow').onclick=()=>location.reload()}
  function listenUpdates(){if(!('serviceWorker'in navigator)||window.__kggUpdateGateListen)return;window.__kggUpdateGateListen=1;navigator.serviceWorker.addEventListener('message',e=>{if(e&&e.data&&e.data.type==='APP_UPDATE_READY')updateBanner()})}
  function autoDay(){if(window.__kggAutoDayRan)return;window.__kggAutoDayRan=1;try{if(typeof p==='undefined'||!p||typeof d==='undefined'||!Array.isArray(done))return;let target=done.length?Math.max(...done)+1:d;if(target<1)target=1;if(target>p.days&&p.extendDays){p.days+=Number(p.stepDays)||6;const w=storedWrap();if(w&&w.plan){w.plan.d=p.days;localStorage.setItem(KEY,JSON.stringify(w))}}if(target<=p.days&&target!==d){d=target;if(typeof save==='function')save();if(typeof render==='function')render();if(typeof setStatus==='function')setStatus('Aktuelles Training: Tag '+d+'.','ok')}}catch(e){}}
  function patch(){recover();listenUpdates();if(typeof window.installApp==='function'&&!window.__kggInstallGuidePatched){const old=window.installApp;window.installApp=async function(){if(!isIOS&&window.installPrompt){return old.apply(this,arguments)}show()};window.__kggInstallGuidePatched=1}const b=$('installSmall');if(b)b.classList.remove('hide')}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',patch):patch();
  setTimeout(patch,500);setTimeout(patch,1500);setTimeout(autoDay,900);setTimeout(autoDay,2200);
})();