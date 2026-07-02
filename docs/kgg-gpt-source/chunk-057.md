# KGG Source Chunk 057

- Source: `kgg-update/index.html`
- Lines: 23941-24360

```html
    const modal=$('kggTherapistShareModal');
    if(!modal)return;
    modal.classList.add('isOpen');
    modal.setAttribute('aria-hidden','false');
  }
  function kggTherapistAppUrl(){
    const target=kggAdminMenuQrTargets&&kggAdminMenuQrTargets.android;
    return target&&target.url||'https://kayus24.github.io/kgg/therapist-app/latest-android.html';
  }
  function openKggTherapistAppOnlyQr(){
    closeKggTherapistShareModal();
    const url=kggTherapistAppUrl();
    openKggAdminMenuQr({title:'Kolleg:innen-App APK QR',hint:'Oeffnet die aktuelle Android-Download-Seite fuer Kolleg:innen. Keine API-Keys, keine Sync-Daten.',url});
  }
  async function openKggTherapistSetupQr(){
    const transfer=await buildKggEncryptedConfigTransferForQr({requireEncrypted:true});
    if(!transfer)return;
    closeKggTherapistShareModal();
    const url=buildKggTherapistSetupUrl(kggTherapistAppUrl(),transfer.payloadCode);
    openKggAdminMenuQr({title:'Therapeuten-App + API-Key',hint:'Setup-Link plus verschluesselter API-Key-Transfer. Transfer-Code: '+transfer.passCode,url});
  }
  async function openKggTherapistApiOnlyQr(){
    closeKggTherapistShareModal();
    await openKggConfigTransferQr();
  }
  function closeKggAdminMenuQrModal(){
    const modal=$('kggAdminMenuQrModal');
    if(!modal)return;
    modal.classList.remove('isOpen');
    modal.setAttribute('aria-hidden','true');
  }
  function renderKggAdminMenuQr(value){
    const box=$('kggAdminMenuQrBox');
    if(!box)return;
    box.innerHTML='';
    try{
      if(window.KGGQrCore&&typeof window.KGGQrCore.renderQrToImg==='function'){
        const img=document.createElement('img');
        img.alt='QR-Code';
        img.src=window.KGGQrCore.renderQrToImg(value,{cellSize:8,margin:4});
        box.appendChild(img);
        return;
      }
      if(typeof window.qrcode==='function'){
        const qr=window.qrcode(0,'M');
        qr.addData(value);
        qr.make();
        const img=document.createElement('img');
        img.alt='QR-Code';
        img.src=qr.createDataURL(8,4);
        box.appendChild(img);
        return;
      }
    }catch(err){
      console.warn('Admin-Menue-QR konnte nicht gerendert werden:',err);
    }
    box.textContent='QR konnte nicht erzeugt werden. Link nutzen.';
  }
  function openKggAdminMenuQr(target){
    const modal=$('kggAdminMenuQrModal'), title=$('kggAdminMenuQrTitle'), hint=$('kggAdminMenuQrHint'), link=$('kggAdminMenuQrLink');
    if(!modal||!title||!hint||!link)return;
    title.textContent=target.title;
    hint.textContent=target.hint;
    const value=target.url||target.text||'';
    window.KGG_ADMIN_MENU_QR_CURRENT={title:target.title||'KGG QR',hint:target.hint||'',value};
    link.value=value;
    if(value)renderKggAdminMenuQr(value);
    else if($('kggAdminMenuQrBox'))$('kggAdminMenuQrBox').textContent='';
    modal.classList.add('isOpen');
    modal.setAttribute('aria-hidden','false');
  }
  window.openKggAdminMenuQr=openKggAdminMenuQr;
  window.openKggTherapistAppOnlyQr=openKggTherapistAppOnlyQr;
  function wrapKggQrPrintText(text,maxChars){
    const words=String(text||'').replace(/\s+/g,' ').trim().split(' ').filter(Boolean);
    const lines=[];
    let line='';
    words.forEach(word=>{
      if(word.length>maxChars){
        if(line){lines.push(line);line='';}
        for(let i=0;i<word.length;i+=maxChars)lines.push(word.slice(i,i+maxChars));
        return;
      }
      const next=line?line+' '+word:word;
      if(next.length>maxChars&&line){lines.push(line);line=word;}
      else line=next;
    });
    if(line)lines.push(line);
    return lines.length?lines:[''];
  }
  function buildKggAdminMenuQrPrintPdf(){
    const current=window.KGG_ADMIN_MENU_QR_CURRENT||{};
    const value=String(current.value||($('kggAdminMenuQrLink')&&$('kggAdminMenuQrLink').value)||'').trim();
    if(!value)throw new Error('missing_qr_value');
    const JsPdfCtor=findJsPdfConstructor();
    if(!JsPdfCtor)throw new Error('missing_pdf_runtime');
    if(typeof window.qrcode!=='function')throw new Error('missing_qr_runtime');
    const doc=new JsPdfCtor({orientation:'portrait',unit:'mm',format:'a4'});
    try{doc.setProperties({title:'KGG Kolleg:innen-App QR',subject:'KGG APK QR',creator:VERSION});}catch(e){}
    const title=String(current.title||'Kolleg:innen-App APK QR');
    const hint=String(current.hint||'QR-Code scannen oder Link oeffnen.');
    try{doc.setFont('helvetica','bold');}catch(e){}
    doc.setFontSize(18); doc.setTextColor(7,16,39); doc.text(title,16,20);
    try{doc.setFont('helvetica','normal');}catch(e){}
    doc.setFontSize(10); doc.setTextColor(80,94,112);
    wrapKggQrPrintText(hint,92).slice(0,3).forEach((line,index)=>doc.text(line,16,29+(index*5)));
    const qr=window.qrcode(0,'M');
    qr.addData(value);
    qr.make();
    const count=qr.getModuleCount();
    const size=124;
    const x=(210-size)/2;
    const y=48;
    const cell=size/count;
    doc.setDrawColor(225,231,239);
    doc.setFillColor(255,255,255);
    doc.rect(x-5,y-5,size+10,size+10,'F');
    doc.rect(x-5,y-5,size+10,size+10,'S');
    doc.setFillColor(0,0,0);
    for(let row=0;row<count;row++){
      for(let col=0;col<count;col++){
        if(qr.isDark(row,col))doc.rect(x+(col*cell),y+(row*cell),cell+.03,cell+.03,'F');
      }
    }
    doc.setFontSize(8); doc.setTextColor(52,64,84);
    wrapKggQrPrintText(value,92).slice(0,5).forEach((line,index)=>doc.text(line,16,188+(index*4.5)));
    doc.setFontSize(9); doc.setTextColor(102,112,133);
    doc.text('Keine Admin-Funktionen, keine API-Keys, keine Patientendaten.',16,222);
    const filename='kgg_kolleginnen_app_qr_'+new Date().toISOString().slice(0,10)+'.pdf';
    const blob=pdfBlobFromDoc(doc);
    if(!blob)throw new Error('missing_pdf_blob');
    return {blob,filename};
  }
  async function printKggAdminMenuQr(){
    try{
      const result=buildKggAdminMenuQrPrintPdf();
      const bridge=nativePdfBridge();
      if(bridge&&typeof bridge.print==='function'){
        const base64=await pdfBlobToBase64(result.blob);
        if(bridge.print(result.filename,base64))return true;
      }
      const url=URL.createObjectURL(result.blob);
      if(openPdfUrlCrossBrowser(url)){
        setTimeout(()=>URL.revokeObjectURL(url),60000);
        return true;
      }
      URL.revokeObjectURL(url);
      downloadPdfBlob(result.blob,result.filename);
      return true;
    }catch(err){
      console.warn('QR-Druck konnte nicht gestartet werden:',err);
      alert('QR-Druck konnte nicht gestartet werden. Bitte Link kopieren oder erneut versuchen.');
      return false;
    }
  }
  if($('tabletMenuAdminConfigBtn'))$('tabletMenuAdminConfigBtn').onclick=()=>{setTabletSideMenuOpen(false); const btn=$('adminConfigBtn'); if(btn)btn.click();};
  if($('tabletMenuSharedBankBtn'))$('tabletMenuSharedBankBtn').onclick=()=>{setTabletSideMenuOpen(false); const btn=$('sharedBankBtn'); if(btn)btn.click();};
  if($('tabletMenuSyncQrBtn'))$('tabletMenuSyncQrBtn').onclick=()=>{setTabletSideMenuOpen(false); openSyncPairModal();};
  if($('tabletMenuConfigTransferBtn'))$('tabletMenuConfigTransferBtn').onclick=async()=>{setTabletSideMenuOpen(false); try{await openKggConfigTransferQr();}catch(err){console.warn('Konfig-Transfer QR fehlgeschlagen:',err); alert('Konfig-Transfer konnte nicht erstellt werden.');}};
  function toggleTabletSideMenuLayoutPanel(){
    const panel=$('tabletMenuLayoutPanel'), btn=$('tabletMenuLayoutBtn');
    if(!panel)return;
    const opening=!!panel.hidden;
    panel.hidden=!opening;
    if(btn)btn.setAttribute('aria-expanded',String(opening));
  }
  function toggleTabletMenuAnchoredPanel(kind){
    const cfg=tabletPanelConfig(kind);
    const panel=cfg&&$(cfg.panelId);
    if(!panel)return;
    if(panel.classList.contains('hidden'))openTabletAnchoredPanel(kind);
    else closeTabletAnchoredPanel(kind);
  }
  if($('tabletMenuRecentBtn'))$('tabletMenuRecentBtn').onclick=()=>{closeTabletPackageOverlay(false);setTabletLayoutEditMode(false);toggleTabletMenuAnchoredPanel('recent');};
  if($('tabletMenuPackagesBtn'))$('tabletMenuPackagesBtn').onclick=toggleTabletPackageOverlay;
  if($('tabletMenuTherapistShareBtn'))$('tabletMenuTherapistShareBtn').onclick=()=>{closeTabletPackageOverlay(false);setTabletLayoutEditMode(false);setTabletSideMenuOpen(false); openKggTherapistAppOnlyQr();};
  if($('tabletMenuLayoutBtn'))$('tabletMenuLayoutBtn').onclick=toggleTabletLayoutEditMode;
  if($('tabletPackageClose'))$('tabletPackageClose').onclick=()=>closeTabletPackageOverlay(false);
  if($('tabletPackageShade'))$('tabletPackageShade').onclick=()=>closeTabletPackageOverlay(false);
  if($('tabletPackageSearch'))$('tabletPackageSearch').addEventListener('input',renderTabletPackageOverlay);
  function bindV399TabletMenuAction(id,handler,tabletOnly){
    const el=$(id);
    if(!el||el.dataset.kggV399ActionBound==='1')return;
    el.dataset.kggV399ActionBound='1';
    el.onclick=null;
    el.addEventListener('click',ev=>{
      if(tabletOnly!==false&&!isTabletLayout())return;
      ev.preventDefault();
      ev.stopPropagation();
      if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
      handler(ev);
    },true);
  }
  bindV399TabletMenuAction('tabletMenuRecentBtn',()=>{closeTabletPackageOverlay(false);setTabletLayoutEditMode(false);toggleTabletMenuAnchoredPanel('recent');});
  bindV399TabletMenuAction('tabletMenuPackagesBtn',()=>toggleTabletPackageOverlay());
  bindV399TabletMenuAction('tabletMenuTherapistShareBtn',()=>{closeTabletPackageOverlay(false);setTabletLayoutEditMode(false);setTabletSideMenuOpen(false);openKggTherapistAppOnlyQr();});
  bindV399TabletMenuAction('tabletMenuLayoutBtn',()=>toggleTabletLayoutEditMode());
  bindV399TabletMenuAction('tabletPackageClose',()=>closeTabletPackageOverlay(false),false);
  bindV399TabletMenuAction('tabletPackageShade',()=>closeTabletPackageOverlay(false),false);
  if($('kggTherapistShareModal'))$('kggTherapistShareModal').addEventListener('click',ev=>{if(ev.target===$('kggTherapistShareModal'))closeKggTherapistShareModal();});
  if($('therapistShareCancel'))$('therapistShareCancel').onclick=closeKggTherapistShareModal;
  if($('therapistShareAppOnly'))$('therapistShareAppOnly').onclick=openKggTherapistAppOnlyQr;
  if($('therapistShareSetup'))$('therapistShareSetup').onclick=()=>openKggTherapistSetupQr().catch(err=>{console.warn('Therapeuten-Setup-QR fehlgeschlagen:',err); alert('Setup-QR konnte nicht erstellt werden.');});
  if($('therapistShareApiOnly'))$('therapistShareApiOnly').onclick=()=>openKggTherapistApiOnlyQr().catch(err=>{console.warn('API-Key-QR fehlgeschlagen:',err); alert('API-Key-QR konnte nicht erstellt werden.');});
  document.querySelectorAll('[data-kgg-admin-menu-qr]').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const target=kggAdminMenuQrTargets[btn.getAttribute('data-kgg-admin-menu-qr')];
      if(target){setTabletSideMenuOpen(false); openKggAdminMenuQr(target);}
    });
  });
  if($('kggAdminMenuQrClose'))$('kggAdminMenuQrClose').onclick=closeKggAdminMenuQrModal;
  if($('kggAdminMenuQrModal'))$('kggAdminMenuQrModal').addEventListener('click',ev=>{if(ev.target===$('kggAdminMenuQrModal'))closeKggAdminMenuQrModal();});
  if($('kggAdminMenuQrCopy'))$('kggAdminMenuQrCopy').onclick=async()=>{const link=$('kggAdminMenuQrLink'); if(!link)return; const ok=await copyTextValue(link.value); if(!ok){link.focus(); link.select();}};
  if($('kggAdminMenuQrOpen'))$('kggAdminMenuQrOpen').onclick=()=>{const link=$('kggAdminMenuQrLink'); if(link&&link.value&&/^https?:\/\//.test(link.value))window.open(link.value,'_blank','noopener');};
  if($('kggAdminMenuQrPrint'))$('kggAdminMenuQrPrint').onclick=()=>printKggAdminMenuQr();
  $('dismissInstallPrompt').onclick=()=>{localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString()); closeInstallPrompt();};
  $('acceptInstallPrompt').onclick=acceptInstallPrompt;
  $('installPromptModal').addEventListener('click',ev=>{if(ev.target===$('installPromptModal')){$('dismissInstallPrompt').click();}});
  $('printPdfPreview').onclick=printCurrentPdfPreview;
  $('downloadPdfPreview').onclick=downloadCurrentPdfPreview;
  $('openPdfPreviewTab').onclick=openCurrentPdfPreviewTab;
  $('openPdfPreviewFallback').onclick=openCurrentPdfPreviewTab;
  $('openPdfPreviewMobileBridge').onclick=openCurrentPdfPreviewTab;
  $('closePdfPreview').onclick=closePdfPreview;
  $('pdfPreviewModal').addEventListener('click',ev=>{if(ev.target===$('pdfPreviewModal'))closePdfPreview();});
  $('savePackageBtn').onclick=openPackageSaveModal;
  $('cancelPackageSave').onclick=closePackageSaveModal;
  $('confirmPackageSave').onclick=confirmPackageSave;
  $('packageSaveModal').addEventListener('click',ev=>{if(ev.target===$('packageSaveModal'))closePackageSaveModal();});
  $('packageNameInput').addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();confirmPackageSave();} if(ev.key==='Escape'){ev.preventDefault();closePackageSaveModal();}});
  $('cancelBankDelete').onclick=closeBankDeleteModal;
  $('confirmBankDelete').onclick=confirmBankDelete;
  $('bankDeleteModal').addEventListener('click',ev=>{if(ev.target===$('bankDeleteModal'))closeBankDeleteModal();});
  function installKggV383UiFlowStability(){
    let phoneTapSuppressUntil=0;
    let phoneBankBrowseMode=false;
    const pointFromEvent=ev=>{
      const point=ev&&ev.touches&&ev.touches[0]||ev&&ev.changedTouches&&ev.changedTouches[0]||ev||{};
      return {x:Number(point.clientX)||0,y:Number(point.clientY)||0};
    };
    trackPhoneTouchStart=function(ev){
      if(!isPhoneLayout())return;
      const point=pointFromEvent(ev);
      phoneTapSuppressUntil=0;
      kggPhoneTouchStart={x:point.x,y:point.y,moved:false};
    };
    trackPhoneTouchMove=function(ev){
      if(!isPhoneLayout())return;
      const point=pointFromEvent(ev);
      if(kggPhoneTouchStart){
        const dx=Math.abs(point.x-kggPhoneTouchStart.x);
        const dy=Math.abs(point.y-kggPhoneTouchStart.y);
        if(dx>7||dy>7)kggPhoneTouchStart.moved=true;
      }
      if(kggPhoneTouchStart&&kggPhoneTouchStart.moved)markPhoneUserScrolling();
    };
    trackPhoneTouchEnd=function(){
      if(kggPhoneTouchStart&&kggPhoneTouchStart.moved){
        phoneTapSuppressUntil=Date.now()+170;
        markPhoneUserScrolling();
      }
      kggPhoneTouchStart=null;
    };
    shouldIgnorePhoneScrollToggle=function(){
      return isPhoneLayout()&&Date.now()<phoneTapSuppressUntil;
    };
    guardPhoneScrollToggle=function(ev){
      if(!shouldIgnorePhoneScrollToggle())return false;
      if(ev){ev.preventDefault();ev.stopPropagation();}
      return true;
    };
    initPhoneScrollGuard=function(){
      if(window.__kggPhoneScrollGuardBound)return;
      window.__kggPhoneScrollGuardBound=true;
      window.addEventListener('scroll',markPhoneUserScrolling,{passive:true});
      if(window.PointerEvent){
        document.addEventListener('pointerdown',ev=>{if(ev.pointerType==='touch')trackPhoneTouchStart(ev);},{passive:true});
        document.addEventListener('pointermove',ev=>{if(ev.pointerType==='touch')trackPhoneTouchMove(ev);},{passive:true});
        document.addEventListener('pointerup',ev=>{if(ev.pointerType==='touch')trackPhoneTouchEnd(ev);},{passive:true});
        document.addEventListener('pointercancel',ev=>{if(ev.pointerType==='touch')trackPhoneTouchEnd(ev);},{passive:true});
      }else{
        document.addEventListener('touchstart',trackPhoneTouchStart,{passive:true});
        document.addEventListener('touchmove',trackPhoneTouchMove,{passive:true});
        document.addEventListener('touchend',trackPhoneTouchEnd,{passive:true});
        document.addEventListener('touchcancel',trackPhoneTouchEnd,{passive:true});
      }
    };
    markPhoneButtonFloat=function(){};
    const blurPhoneComposerForBrowse=()=>{
      if(!isPhoneLayout())return;
      phoneBankBrowseMode=true;
      document.body.classList.add('kggPhoneDbBrowseMode');
      const input=$('exerciseInput');
      if(input&&document.activeElement===input){
        try{input.blur();}catch(err){}
      }
      document.body.classList.remove('phoneTextFocus');
      updatePhoneKeyboardInset();
    };
    const openOrCloseBankFromBrowseTap=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      if(isPhoneLayout())blurPhoneComposerForBrowse();
      const opening=!state.bankOpen;
      if(opening&&isTabletLayout())openTabletExclusivePanel('bank');
      state.bankOpen=opening;
      render();
      setTabletOverlayActiveFlag();
    };
    const input=$('exerciseInput');
    if(input){
      input.addEventListener('focus',()=>{phoneBankBrowseMode=false;document.body.classList.remove('kggPhoneDbBrowseMode');});
      input.addEventListener('input',()=>{phoneBankBrowseMode=false;document.body.classList.remove('kggPhoneDbBrowseMode');});
    }
    const oldApplySelectedExerciseToText=applySelectedExerciseToText;
    applySelectedExerciseToText=function(ex,options){
      const next={...(options||{})};
      if(isPhoneLayout()&&phoneBankBrowseMode)next.keepFocus=false;
      return oldApplySelectedExerciseToText(ex,next);
    };
    if($('bankToggle'))$('bankToggle').onclick=openOrCloseBankFromBrowseTap;
    if($('dbTitle')){
      $('dbTitle').onclick=openOrCloseBankFromBrowseTap;
      $('dbTitle').onkeydown=null;
      $('dbTitle').addEventListener('keydown',ev=>{
        if(ev.key==='Enter'||ev.key===' '){
          ev.preventDefault();
          ev.stopImmediatePropagation();
          openOrCloseBankFromBrowseTap(ev);
        }
      },true);
    }
    if($('baseToggle'))$('baseToggle').onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      const base=$('baseFields');
      const opening=base.classList.contains('hidden');
      if(isTabletLayout()){
        if(opening)openTabletAnchoredPanel('base'); else closeTabletAnchoredPanel('base');
      }else{
        base.classList.toggle('hidden',!opening);
        setTabletOverlayActiveFlag();
        updateToggleCarets();
      }
    };
    if($('recentToggle'))$('recentToggle').onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      const recent=$('recentList');
      const opening=recent.classList.contains('hidden');
      if(isTabletLayout()){
        if(opening)openTabletAnchoredPanel('recent'); else closeTabletAnchoredPanel('recent');
      }else{
        openPhoneFloatingDrawer('recent');
      }
    };
    const packageToggleBtn=$('packageToggle');
    if(packageToggleBtn)packageToggleBtn.onclick=ev=>{
      if(guardPhoneScrollToggle(ev))return;
      if(isTabletLayout())toggleTabletPackageOverlay();
      else openPhoneFloatingDrawer('package');
    };
    const modalClosers={
      editorModal:typeof closeEditor==='function'?closeEditor:null,
      shareModal:typeof closeFinishModal==='function'?closeFinishModal:null,
      largePdfModal:typeof closeLargePdfModal==='function'?closeLargePdfModal:null,
      longMediaConfirmModal:typeof closeLongMediaConfirmModal==='function'?closeLongMediaConfirmModal:null,
      adminSecretsModal:typeof closeAdminSecretsModal==='function'?closeAdminSecretsModal:null,
      sharedBankModal:typeof closeSharedBankModal==='function'?closeSharedBankModal:null,
      syncPairModal:typeof closeSyncPairModal==='function'?closeSyncPairModal:null
    };
    document.querySelectorAll('.modal').forEach(modal=>{
      if(modal.dataset.kggV383BackdropBound==='1')return;
      modal.dataset.kggV383BackdropBound='1';
      modal.addEventListener('pointerup',ev=>{
        if(ev.target!==modal)return;
        ev.preventDefault();
        ev.stopPropagation();
        const close=modalClosers[modal.id];
        if(typeof close==='function')close();
        else modal.classList.remove('open');
      });
    });
    const adminQrModal=$('kggAdminMenuQrModal');
    if(adminQrModal&&!adminQrModal.dataset.kggV383BackdropBound){
      adminQrModal.dataset.kggV383BackdropBound='1';
      adminQrModal.addEventListener('pointerup',ev=>{
        if(ev.target!==adminQrModal)return;
        ev.preventDefault();
        if(typeof closeKggAdminMenuQrModal==='function')closeKggAdminMenuQrModal();
      });
    }
    const oldApplyNativeSyncInvite=applyNativeSyncInvite;
    applyNativeSyncInvite=function(invite){
      setScanStatus('QR erkannt: Sync-Kopplung wird gelesen ...');
      try{
        const entry=oldApplyNativeSyncInvite(invite);
        const peers=syncPeerDisplayEntries().length;
        setScanStatus('Sync-Kopplung gespeichert. Dieses Geraet liest und schreibt im Sync-Raum. '+(peers?'Anderes Geraet gefunden: Synchronisation aktiv.':'Warte auf weitere Geraete mit diesem QR.'));
        return entry;
      }catch(err){
        setScanStatus('Fehler: ungueltige Sync-Daten.');
        throw err;
      }
    };
    const oldApplyNativeSyncBundle=applyNativeSyncBundle;
    applyNativeSyncBundle=async function(bundle){
      setScanStatus('QR erkannt: Sync-Datenpaket wird gelesen ...');
      try{
        const result=await oldApplyNativeSyncBundle(bundle);
        const peers=syncPeerDisplayEntries().length;
        setScanStatus('Sync-Datenpaket gespeichert. Verbindung und Daten wurden lokal uebernommen. '+(peers?'Synchronisation aktiv.':'Warte auf weitere Geraete mit diesem QR.'));
        return result;
      }catch(err){
        setScanStatus('Fehler: Sync-Verbindung nicht moeglich.');
        throw err;
      }
    };
  }
  function installKggV388AndroidFlowFixes(){
    let lastTabletMenuToggleAt=0;
    const menu=tabletMenuBtn;
    const toggle=ev=>{
```
