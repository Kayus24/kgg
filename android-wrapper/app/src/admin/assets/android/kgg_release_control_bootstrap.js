(function(){
  if (!window.KGGReleaseControl || window.KGGReleaseCenter) return;
  var MOBILE_INBOX_URL='https://github.com/Kayus24/kgg/upload/mobile-inbox/mobile-inbox';
  var MOBILE_PROMOTE_URL='https://github.com/Kayus24/kgg/actions/workflows/promote-latest-admin-beta.yml';
  function safeParse(text,fallback){try{return JSON.parse(text);}catch(err){return fallback;}}
  function status(){return safeParse(window.KGGReleaseControl.status(),{available:false});}
  function ensureModal(){
    var existing=document.getElementById('kggReleaseCenterModal');
    if(existing)return existing;
    var modal=document.createElement('div');
    modal.id='kggReleaseCenterModal';
    modal.style.cssText='display:none;position:fixed;inset:0;z-index:2147483000;background:rgba(7,16,39,.48);padding:16px;overflow:auto';
    modal.innerHTML='<section style="width:min(680px,96vw);margin:3vh auto;background:#fff;color:#071027;border-radius:22px;padding:16px;font-family:system-ui;box-shadow:0 24px 80px rgba(0,0,0,.3)">'
      +'<div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2 style="margin:0">KGG Update-Zentrale</h2><button id="kggReleaseClose" type="button">Schliessen</button></div>'
      +'<p>Standard: HTML speichern und per GitHub-Mobile-Inbox hochladen. Direktupload bleibt Komfortweg.</p>'
      +'<pre id="kggReleaseStatus" style="white-space:pre-wrap;background:#f3f6fa;border-radius:12px;padding:10px"></pre>'
      +'<div style="display:grid;gap:8px"><button id="kggReleaseDownloadHtml" type="button">Aktuelle HTML speichern</button>'
      +'<button id="kggReleaseMobileInbox" type="button">GitHub-Mobile-Inbox oeffnen</button>'
      +'<button id="kggReleasePromoteLatest" type="button">Kolleg:innen-Freigabe in GitHub oeffnen</button>'
      +'<button id="kggReleaseLogin" type="button">Komfort: Mit GitHub verbinden</button>'
      +'<input id="kggReleaseId" placeholder="Release-ID, z. B. r0390"><input id="kggReleaseVersion" placeholder="Versionsname"><textarea id="kggReleaseNotes" placeholder="Kurze Patch-Notiz; keine Patientendaten oder Secrets"></textarea>'
      +'<button id="kggReleaseUpload" type="button">Komfort: HTML direkt aus App hochladen</button>'
      +'<button id="kggReleasePromote" type="button">Komfort: Release-ID fuer Kolleg:innen freigeben</button>'
      +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><button id="kggReleaseRollbackAdmin" type="button">Admin-Rollback</button><button id="kggReleaseRollbackColleague" type="button">Kolleg:innen-Rollback</button></div></div>'
      +'</section>';
    document.body.appendChild(modal);
    function value(id){return (document.getElementById(id).value||'').trim();}
    function refresh(){document.getElementById('kggReleaseStatus').textContent=JSON.stringify(status(),null,2);}
    document.getElementById('kggReleaseClose').onclick=function(){modal.style.display='none';};
    document.getElementById('kggReleaseLogin').onclick=function(){window.KGGReleaseControl.beginLogin();refresh();};
    document.getElementById('kggReleaseDownloadHtml').onclick=function(){window.KGGReleaseControl.downloadCurrentHtml();refresh();};
    document.getElementById('kggReleaseMobileInbox').onclick=function(){if(typeof window.KGGReleaseControl.openMobileInbox==='function')window.KGGReleaseControl.openMobileInbox();else window.open(MOBILE_INBOX_URL,'_blank');refresh();};
    document.getElementById('kggReleasePromoteLatest').onclick=function(){if(typeof window.KGGReleaseControl.openPromoteLatest==='function')window.KGGReleaseControl.openPromoteLatest();else window.open(MOBILE_PROMOTE_URL,'_blank');refresh();};
    document.getElementById('kggReleaseUpload').onclick=function(){window.KGGReleaseControl.chooseAndUploadBeta(value('kggReleaseId'),value('kggReleaseVersion'),value('kggReleaseNotes'));refresh();};
    document.getElementById('kggReleasePromote').onclick=function(){window.KGGReleaseControl.confirmPromotion(value('kggReleaseId'));};
    document.getElementById('kggReleaseRollbackAdmin').onclick=function(){window.KGGReleaseControl.confirmRollback('admin',value('kggReleaseId'));};
    document.getElementById('kggReleaseRollbackColleague').onclick=function(){window.KGGReleaseControl.confirmRollback('colleague',value('kggReleaseId'));};
    modal.addEventListener('click',function(ev){if(ev.target===modal)modal.style.display='none';});
    modal._refresh=refresh;
    return modal;
  }
  function open(){var modal=ensureModal();modal.style.display='block';modal._refresh();}
  window.KGGReleaseCenter={open:open,status:status};
  var button=document.createElement('button');
  button.type='button';button.textContent='Update-Zentrale';button.onclick=open;
  button.className='tabletSideMenuAction mutedBtn';button.id='kggReleaseCenterOpen';
  var tabletAnchor=document.getElementById('tabletMenuAdminConfigBtn');
  var adminTools=document.querySelector('.adminCodePackageTools');
  if(tabletAnchor&&tabletAnchor.parentNode)tabletAnchor.parentNode.insertBefore(button,tabletAnchor.nextSibling);
  else if(adminTools)adminTools.appendChild(button);
})();
