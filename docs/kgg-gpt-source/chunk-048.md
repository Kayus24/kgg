# KGG Source Chunk 048

- Source: `kgg-update/src` modular source
- Lines: 20161-20580

```html
  async function buildKggEncryptedConfigTransferForQr(options){
    const plain=buildKggConfigTransferPlain();
    if(!kggConfigTransferHasCodes(plain)){
      openAdminSecretsModal();
      return null;
    }
    const passCode=kggConfigTransferPassCode();
    const encrypted=await encryptKggConfigTransferPlain(plain,passCode);
    if((options&&options.requireEncrypted)!==false&&!encrypted.encrypted){
      alert('API-Key-QR kann auf diesem Geraet nur verschluesselt erstellt werden.');
      return null;
    }
    return {payloadCode:encrypted.payloadCode,passCode,encrypted:encrypted.encrypted,plain};
  }
  async function openKggConfigTransferQr(){
    const transfer=await buildKggEncryptedConfigTransferForQr({requireEncrypted:true});
    if(!transfer)return;
    openKggAdminMenuQr({
      title:'Konfig-Transfer QR',
      hint:'Verschluesselt, 10 Minuten gueltig. Transfer-Code: '+transfer.passCode,
      text:transfer.payloadCode
    });
  }
  function parseKggConfigTransferCode(code){
    const raw=String(code||'').trim();
    if(raw.indexOf('KGGCFG2:')===0)return {type:'KGGCFG2',json:safeBase64JsonDecode(raw.slice(8)),raw};
    if(raw.indexOf('KGGCFG1:')===0)return {type:'KGGCFG1',json:safeBase64JsonDecode(raw.slice(8)),raw};
    return null;
  }
  function buildKggTherapistSetupUrl(appUrl,configTransferCode){
    const payload={kind:'kgg_therapist_setup_v1',version:1,appUrl:String(appUrl||''),configTransfer:String(configTransferCode||''),createdAt:new Date().toISOString()};
    const sep=String(appUrl||'').includes('#')?'&':'#';
    return String(appUrl||'')+sep+'kggsetup='+safeBase64JsonEncode(payload);
  }
  async function tryApplyKggSetupFromHash(){
    const hash=String(location.hash||'');
    const match=hash.match(/[#!&]kggsetup=([^&]+)/);
    if(!match)return false;
    const setup=safeBase64JsonDecode(match[1]);
    if(!setup||setup.kind!=='kgg_therapist_setup_v1')return false;
    const parsed=parseKggConfigTransferCode(setup.configTransfer);
    if(parsed)await applyKggConfigTransferParsed(parsed);
    try{history.replaceState(null,'',location.pathname+location.search);}catch(err){}
    return true;
  }
  async function applyKggConfigTransferParsed(parsed){
    if(!parsed||!(parsed.type==='KGGCFG2'||parsed.type==='KGGCFG1'))return false;
    let plain=parsed.json;
    if(parsed.type==='KGGCFG2'){
      const passCode=(prompt('Transfer-Code eingeben')||'').trim();
      if(!passCode)return false;
      plain=await decryptKggConfigTransferEnvelope(parsed.json,passCode);
    }
    applyKggConfigTransferPlain(plain);
    setScanStatus('API-Key / Konfig lokal gespeichert. Scan/OCR kann die lokalen Daten nutzen.');
    alert('API-Key / Konfig lokal gespeichert.');
    return true;
  }
  function syncPairDeviceId(){
    try{
      let id=localStorage.getItem(syncPairDeviceIdKey);
      if(!id){
        const rand=(crypto&&crypto.getRandomValues)?Array.from(crypto.getRandomValues(new Uint32Array(2))).map(v=>v.toString(36)).join(''):Math.random().toString(36).slice(2);
        id='kgg_'+Date.now().toString(36)+'_'+rand;
        localStorage.setItem(syncPairDeviceIdKey,id);
      }
      return id;
    }catch(err){return 'kgg_'+Date.now().toString(36);}
  }
  function normalizeNativeSyncFollowConfig(config){
    const normalized=config&&typeof config==='object'?{...config}:{};
    normalized.therapistId=String(normalized.therapistId||'').trim();
    normalized.syncRoomId=String(normalized.syncRoomId||'').trim();
    normalized.followedTherapists=Array.isArray(normalized.followedTherapists)?normalized.followedTherapists:[];
    return normalized;
  }
  function nativeSyncFollowConfig(){
    try{
      if(window.KGGNativeSync&&typeof window.KGGNativeSync.getFollowConfig==='function'){
        return normalizeNativeSyncFollowConfig(window.KGGNativeSync.getFollowConfig()||{therapistId:'',followedTherapists:[]});
      }
    }catch(err){}
    try{return normalizeNativeSyncFollowConfig(JSON.parse(localStorage.getItem(syncPairFallbackConfigKey)||'{"therapistId":"","syncRoomId":"","followedTherapists":[]}'));}catch(err){}
    return {therapistId:'',syncRoomId:'',followedTherapists:[]};
  }
  function writeNativeSyncFollowConfig(config){
    try{
      if(window.KGGNativeSync&&typeof window.KGGNativeSync.setFollowConfig==='function'){
        return !!window.KGGNativeSync.setFollowConfig(config||{});
      }
    }catch(err){}
    try{localStorage.setItem(syncPairFallbackConfigKey,JSON.stringify(config||{}));return true;}catch(err){return false;}
  }
  function syncPairRoomId(){
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    if(config.syncRoomId)return config.syncRoomId;
    let roomId='';
    try{roomId=localStorage.getItem(syncPairRoomIdKey)||'';}catch(err){}
    if(!roomId){
      const rand=(crypto&&crypto.getRandomValues)?Array.from(crypto.getRandomValues(new Uint32Array(2))).map(v=>v.toString(36)).join(''):Math.random().toString(36).slice(2);
      roomId='room_'+Date.now().toString(36)+'_'+rand;
      try{localStorage.setItem(syncPairRoomIdKey,roomId);}catch(err){}
    }
    config.syncRoomId=roomId;
    if(!config.therapistId)config.therapistId=syncPairDeviceId();
    writeNativeSyncFollowConfig(config);
    return roomId;
  }
  function buildNativeSyncInvite(){
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig()||{});
    const deviceId=syncPairDeviceId();
    const therapistName=String(($('therapistName')&&$('therapistName').value)||state.patient.therapist||'').trim();
    const therapistId=String(config.therapistId||deviceId).trim()||deviceId;
    const roomId=syncPairRoomId();
    return {
      kind:'kgg_sync_invite',
      version:2,
      appVersion:VERSION,
      createdAt:new Date().toISOString(),
      expiresAt:new Date(Date.now()+5*60*1000).toISOString(),
      roomId,
      deviceId,
      therapistId,
      displayName:therapistName||'KGG Geraet',
      scopes:['exerciseBank','packages'],
      transport:'android-native-sync-folder-mesh',
      peerMode:'host-and-client',
      autoDownload:true
    };
  }
  function nativeSyncPayloadCode(prefix,value){return prefix+':'+safeBase64JsonEncode(value);}
  function buildNativeSyncQrPayload(){
    const invite=buildNativeSyncInvite();
    let syncDoc=null;
    try{syncDoc=buildNativeExerciseBankSyncDocument();}catch(err){syncDoc=null;}
    if(syncDoc){
      const bundle={kind:'kgg_sync_bundle',version:2,appVersion:VERSION,createdAt:invite.createdAt,expiresAt:invite.expiresAt,roomId:invite.roomId,peerMode:'host-and-client',invite,sync:syncDoc};
      const bundleCode=nativeSyncPayloadCode('KGGSYNC2',bundle);
      if(bundleCode.length<=nativeSyncQrMaxLength){
        return {code:bundleCode,type:'bundle',syncIncluded:true,length:bundleCode.length,invite,sync:syncDoc};
      }
      return {code:nativeSyncPayloadCode('KGGSYNC1',invite),type:'invite',syncIncluded:false,length:bundleCode.length,invite,sync:syncDoc,tooLarge:true};
    }
    return {code:nativeSyncPayloadCode('KGGSYNC1',invite),type:'invite',syncIncluded:false,length:0,invite,sync:null};
  }
  function renderQrIntoBox(targetId,value,alt){
    const box=$(targetId);
    if(!box)return false;
    box.innerHTML='';
    try{
      let imgData='';
      if(window.KGGQrCore&&typeof window.KGGQrCore.renderQrToImg==='function'){
        imgData=window.KGGQrCore.renderQrToImg(value,{cellSize:10,margin:4});
      }else if(typeof window.qrcode==='function'){
        const qr=window.qrcode(0,'L');
        qr.addData(value);
        qr.make();
        imgData=qr.createDataURL(10,4);
      }
      if(imgData){
        const img=document.createElement('img');
        img.alt=alt||'QR-Code';
        img.src=imgData;
        box.appendChild(img);
        return true;
      }
    }catch(err){console.warn('Sync-QR konnte nicht gerendert werden:',err);}
    box.innerHTML='<span class="qrStatus">QR konnte nicht erzeugt werden. Code kopieren.</span>';
    return false;
  }
  function nativeSyncTransportStatusText(){
    try{
      if(!window.KGGNativeSync||typeof window.KGGNativeSync.status!=='function')return '';
      const status=window.KGGNativeSync.status()||{};
      if(status.usingSharedFolder||status.writeUsesSharedFolder){
        return ' Android-Sync-Raum: KGG Sync / '+syncPeerIdShort(status.syncRoomId||syncPairRoomId())+'.';
      }
      if(status.sharedWritable===false){
        return ' Android nutzt privaten Rueckfall-Speicher; gemeinsamen KGG Sync-Ordner/Dateizugriff pruefen.';
      }
      return ' Android-Sync-Datei: '+(status.syncFile||'Cross-Data-Safe-Datei')+'.';
    }catch(err){
      return '';
    }
  }
  function nativeSyncPeerMesh(){
    try{
      if(window.KGGNativeSync&&typeof window.KGGNativeSync.listPeers==='function'){
        return window.KGGNativeSync.listPeers()||{peers:[]};
      }
    }catch(err){}
    return {kind:'kgg_cross_data_safe_sync_mesh',peers:[]};
  }
  function syncPeerDisplayEntries(){
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const map=new Map();
    const add=(entry,source)=>{
      if(!entry)return;
      const deviceId=String(entry.deviceId||entry.therapistId||'').trim();
      const therapistId=String(entry.therapistId||deviceId).trim();
      if(!deviceId||deviceId===syncPairDeviceId())return;
      const key=deviceId||therapistId;
      const existing=map.get(key)||{};
      const inferredAutoDownload=source==='follow';
      map.set(key,{
        ...existing,
        ...entry,
        deviceId,
        therapistId,
        displayName:String(entry.displayName||existing.displayName||'KGG Geraet'),
        roomId:String(entry.roomId||existing.roomId||config.syncRoomId||syncPairRoomId()),
        autoDownload:existing.autoDownload!==undefined?existing.autoDownload:(entry.autoDownload!==undefined?entry.autoDownload:inferredAutoDownload),
        source:existing.source||source
      });
    };
    (config.followedTherapists||[]).forEach(entry=>add(entry,'follow'));
    const mesh=nativeSyncPeerMesh();
    (Array.isArray(mesh.peers)?mesh.peers:[]).forEach(doc=>{
      const origin=doc&&doc.origin||{};
      if(!origin||syncOriginIsSelf(origin))return;
      add({therapistId:origin.therapistId,deviceId:origin.deviceId,displayName:origin.displayName,roomId:origin.roomId||mesh.roomId,autoDownload:false,lastSeenAt:doc.exportedAt},'room');
    });
    return Array.from(map.values()).sort((a,b)=>String(a.displayName||'').localeCompare(String(b.displayName||'')));
  }
  function syncDiagnosticStatus(){
    let status={available:false,platform:'web'};
    try{
      if(window.KGGNativeSync&&typeof window.KGGNativeSync.status==='function')status=window.KGGNativeSync.status()||status;
    }catch(err){status={available:false,platform:'web',error:'status_failed'};}
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const roomId=String(status.syncRoomId||config.syncRoomId||syncPairRoomId());
    const native=!!(window.KGGNativeSync&&window.KGGNativeSync.available);
    const shared=status.writeUsesSharedFolder===true||status.usingSharedFolder===true;
    const privateFallback=native&&status.sharedWritable===false&&!shared;
    return {status,config,roomId,native,shared,privateFallback};
  }
  function renderSyncDiagnostics(){
    const box=$('syncDiagnostics');
    if(!box)return;
    const info=syncDiagnosticStatus();
    const status=info.status||{};
    const peerCount=Number(status.peerCount)||syncPeerDisplayEntries().length||0;
    const mode=!info.native?'Web-Modus / keine Android-Bridge':(info.shared?'Gemeinsamer Android-Sync-Ordner aktiv':'Privater Rueckfall-Speicher');
    const warn=info.privateFallback?' <span class="warn">Privater Speicher synchronisiert nicht automatisch zwischen Geraeten.</span>':'';
    const path=String(status.writePath||status.syncPath||status.sharedSyncPath||status.privateSyncPath||'').replace(/\\/g,'/');
    const shortPath=path.length>88?'...'+path.slice(-85):path;
    const parts=[
      '<div><b>Modus:</b> '+escapeHtml(mode)+warn+'</div>',
      '<div><b>Raum:</b> '+escapeHtml(syncPeerIdShort(info.roomId))+' · <b>Peers:</b> '+peerCount+'</div>',
      nativeSyncLastStatus?'<div><b>Letzter Test:</b> '+escapeHtml(nativeSyncLastStatus)+'</div>':'',
      shortPath?'<div><b>Pfad:</b> '+escapeHtml(shortPath)+'</div>':''
    ].filter(Boolean);
    box.innerHTML=parts.join('');
    box.classList.remove('hidden');
  }
  function setSyncPeerAutoDownload(deviceId,enabled){
    const entries=syncPeerDisplayEntries();
    const selected=entries.find(entry=>String(entry.deviceId)===String(deviceId));
    if(!selected)return;
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig()||{});
    const list=Array.isArray(config.followedTherapists)?config.followedTherapists.slice():[];
    const idx=list.findIndex(item=>String(item.deviceId||'')===String(selected.deviceId)||String(item.therapistId||'')===String(selected.therapistId));
    const next={...selected,autoDownload:!!enabled,scopes:['exerciseBank','packages'],lastSeenAt:new Date().toISOString()};
    if(idx>=0)list[idx]={...list[idx],...next};
    else list.push(next);
    config.followedTherapists=list;
    if(next.roomId)config.syncRoomId=next.roomId;
    if(!config.therapistId)config.therapistId=syncPairDeviceId();
    writeNativeSyncFollowConfig(config);
    const status=$('syncPairStatus');
    if(status)status.textContent=(enabled?'Auto-Download aktiv fuer ':'Auto-Download pausiert fuer ')+next.displayName+'.'+nativeSyncTransportStatusText();
    if(enabled)pullNativeExerciseBankSync('sync_peer_enabled').finally(()=>queueNativeExerciseBankSync('sync_peer_enabled'));
    renderSyncPeerList();
    renderSyncDiagnostics();
  }
  function renderSyncPeerList(){
    const box=$('syncPeerList');
    if(!box)return;
    const roomId=syncPairRoomId();
    const entries=syncPeerDisplayEntries();
    box.classList.remove('hidden');
    box.innerHTML='';
    const head=document.createElement('div');
    head.className='syncPeerHead';
    const title=document.createElement('span');
    title.textContent='Automatisch laden von';
    const room=document.createElement('small');
    room.textContent='Raum '+syncPeerIdShort(roomId);
    head.appendChild(title);
    head.appendChild(room);
    box.appendChild(head);
    if(!entries.length){
      const empty=document.createElement('div');
      empty.className='syncPeerEmpty';
      empty.textContent='Noch keine anderen Geraete im Sync-Ordner gefunden.';
      box.appendChild(empty);
      return;
    }
    entries.forEach(entry=>{
      const row=document.createElement('label');
      row.className='syncPeerRow';
      const checkbox=document.createElement('input');
      checkbox.type='checkbox';
      checkbox.checked=entry.autoDownload!==false;
      checkbox.dataset.deviceId=entry.deviceId;
      checkbox.addEventListener('change',()=>setSyncPeerAutoDownload(entry.deviceId,checkbox.checked));
      const text=document.createElement('span');
      const name=document.createElement('span');
      name.className='syncPeerName';
      name.textContent=entry.displayName||'KGG Geraet';
      const meta=document.createElement('span');
      meta.className='syncPeerMeta';
      meta.textContent='Geraet '+syncPeerIdShort(entry.deviceId)+' · '+(entry.autoDownload!==false?'Auto':'pausiert');
      text.appendChild(name);
      text.appendChild(meta);
      row.appendChild(checkbox);
      row.appendChild(text);
      box.appendChild(row);
    });
  }
  function openSyncPairModal(){
    try{queueNativeExerciseBankSync('sync_pair_modal_open');}catch(err){}
    const payload=buildNativeSyncQrPayload();
    lastSyncPairCode=payload.code;
    const modal=$('syncPairModal');
    renderQrIntoBox('syncPairQrBox',lastSyncPairCode,'Sync-QR fuer Uebungsdatenbank');
    const status=$('syncPairStatus');
    const transportStatus=nativeSyncTransportStatusText();
    if(status)status.textContent=(payload.syncIncluded
      ?'Kopplung plus aktuelle Uebungsdatenbank/Pakete im QR. Gueltig ca. 5 Minuten.'
      :'Kopplung im QR. Datenbank/Pakete sind fuer einen QR zu gross; Android nutzt die lokale Cross-Data-Safe-Sync-Datei.')+transportStatus;
    renderSyncPeerList();
    renderSyncDiagnostics();
    if(modal)modal.classList.add('open');
  }
  function closeSyncPairModal(){const modal=$('syncPairModal'); if(modal)modal.classList.remove('open');}
  async function copySyncPairCode(){
    const status=$('syncPairStatus');
    const ok=await copyTextValue(lastSyncPairCode||'');
    if(status)status.textContent=ok?'Sync-Code kopiert.':'Kopieren blockiert. Code bitte ueber QR einlesen.';
  }
  async function testNativeSyncRoundtrip(){
    const status=$('syncPairStatus');
    try{
      const doc=buildNativeExerciseBankSyncDocument();
      if(!nativeExerciseSyncAvailable()){
        nativeSyncLastStatus='Datenformat OK, aber keine Android-Bridge aktiv.';
        if(status)status.textContent=nativeSyncLastStatus;
        renderSyncDiagnostics();
        return {native:false,doc};
      }
      const writeOk=!!(await resolveNativeSyncValue(window.KGGNativeSync.write(doc)));
      let mesh=null,result=null;
      if(typeof window.KGGNativeSync.listPeers==='function')mesh=await resolveNativeSyncValue(window.KGGNativeSync.listPeers());
      if(!mesh&&typeof window.KGGNativeSync.read==='function')mesh=await resolveNativeSyncValue(window.KGGNativeSync.read());
      if(mesh)result=mergeNativeExerciseBankSyncDocument(mesh);
      const peers=result&&result.mesh?result.mesh.seen:((mesh&&Array.isArray(mesh.peers))?mesh.peers.length:0);
      nativeSyncLastStatus=(writeOk?'Schreiben OK':'Schreiben fehlgeschlagen')+' · Peers '+peers;
      if(status)status.textContent='Sync-Test: '+nativeSyncLastStatus+'. '+nativeSyncTransportStatusText();
      renderSyncPeerList();
      renderSyncDiagnostics();
      return {native:true,writeOk,mesh,result};
    }catch(err){
      nativeSyncLastStatus='Fehler: '+(err&&err.message?err.message:'Sync-Test fehlgeschlagen');
      if(status)status.textContent=nativeSyncLastStatus;
      renderSyncDiagnostics();
      return null;
    }
  }
  function downloadNativeSyncFile(){
    const status=$('syncPairStatus');
    try{
      const doc=buildNativeExerciseBankSyncDocument();
      const blob=new Blob([JSON.stringify(doc,null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');
      const stamp=new Date().toISOString().slice(0,19).replace(/[-:T]/g,'');
      a.href=url;
      a.download='kgg_sync_'+syncPeerIdShort(doc.roomId||'room')+'_'+stamp+'.json';
      a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1200);
      nativeSyncLastStatus='Sync-Datei gespeichert.';
      if(status)status.textContent=nativeSyncLastStatus;
      renderSyncDiagnostics();
      return true;
    }catch(err){
      nativeSyncLastStatus='Sync-Datei konnte nicht gespeichert werden.';
      if(status)status.textContent=nativeSyncLastStatus;
      renderSyncDiagnostics();
      return false;
    }
  }
  async function importNativeSyncFile(file){
    const status=$('syncPairStatus');
    try{
      if(!file)throw new Error('Keine Datei ausgewaehlt.');
      const text=await file.text();
      const payload=JSON.parse(text);
      const result=mergeNativeExerciseBankSyncDocument(payload,{allowUnfollowed:true});
      try{await pushNativeExerciseBankSync('sync_file_import');}catch(err){}
      const bankResult=result&&result.bank?result.bank:{added:0,updated:0,total:0};
      const packageResult=result&&result.packages?result.packages:{added:0,updated:0,total:0};
      nativeSyncLastStatus='Import OK · DB +'+bankResult.added+'/'+bankResult.updated+' · Pakete +'+packageResult.added+'/'+packageResult.updated;
      if(status)status.textContent=nativeSyncLastStatus;
      renderSyncPeerList();
      renderSyncDiagnostics();
      return result;
    }catch(err){
      nativeSyncLastStatus='Import fehlgeschlagen: '+(err&&err.message?err.message:'ungueltige Datei');
      if(status)status.textContent=nativeSyncLastStatus;
      renderSyncDiagnostics();
      return null;
    }
  }
  function isNativeSyncInvitePayload(payload){
    return payload&&payload.kind==='kgg_sync_invite'&&(payload.version===1||payload.version===2)&&payload.deviceId;
  }
  function isNativeSyncBundlePayload(payload){
    return payload&&payload.kind==='kgg_sync_bundle'&&(payload.version===1||payload.version===2)&&(payload.invite||payload.sync);
  }
```
