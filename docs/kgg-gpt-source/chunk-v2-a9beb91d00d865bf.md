    for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
    return bytes;
  }
  function kggConfigTransferRandomBytes(length){
    const bytes=new Uint8Array(length);
    if(window.crypto&&crypto.getRandomValues)crypto.getRandomValues(bytes);
    else for(let i=0;i<bytes.length;i++)bytes[i]=Math.floor(Math.random()*256);
    return bytes;
  }
  function kggConfigTransferPassCode(){
    const bytes=kggConfigTransferRandomBytes(4);
    const value=((bytes[0]<<24)>>>0)+(bytes[1]<<16)+(bytes[2]<<8)+bytes[3];
    return String(100000+(value%900000));
  }
  function buildKggConfigTransferPlain(){
    loadAdminSecrets();
    return {
      kind:'kgg_config_transfer_v2',
      version:2,
      appVersion:VERSION,
      createdAt:new Date().toISOString(),
      expiresAt:new Date(Date.now()+10*60*1000).toISOString(),
      secrets:{
        geminiKeys:(adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean).slice(0,4),
        mediaDropzoneEndpoint:cleanSecret(adminSecrets.mediaDropzoneEndpoint),
        mediaDropzoneUploadToken:cleanSecret(adminSecrets.mediaDropzoneUploadToken)
      }
    };
  }
  function kggConfigTransferHasCodes(plain){
    const secrets=plain&&plain.secrets||{};
    return !!((Array.isArray(secrets.geminiKeys)&&secrets.geminiKeys.length)||secrets.mediaDropzoneEndpoint||secrets.mediaDropzoneUploadToken);
  }
  async function kggConfigTransferKey(passCode,saltBytes){
    const material=await crypto.subtle.importKey('raw',new TextEncoder().encode(String(passCode||'')),{name:'PBKDF2'},false,['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2',salt:saltBytes,iterations:140000,hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
  }
  async function encryptKggConfigTransferPlain(plain,passCode){
    if(!(window.crypto&&crypto.subtle&&window.TextEncoder))return {payloadCode:'KGGCFG1:'+safeBase64JsonEncode(plain),encrypted:false};
    const salt=kggConfigTransferRandomBytes(16);
    const iv=kggConfigTransferRandomBytes(12);
    const key=await kggConfigTransferKey(passCode,salt);
    const cipher=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,new TextEncoder().encode(JSON.stringify(plain)));
    const envelope={kind:'kgg_config_transfer_encrypted_v2',version:2,alg:'PBKDF2-SHA256-AES-GCM',salt:kggConfigTransferBytesToBase64Url(salt),iv:kggConfigTransferBytesToBase64Url(iv),ciphertext:kggConfigTransferBytesToBase64Url(new Uint8Array(cipher)),createdAt:plain.createdAt,expiresAt:plain.expiresAt};
    return {payloadCode:'KGGCFG2:'+safeBase64JsonEncode(envelope),encrypted:true};
  }
  async function decryptKggConfigTransferEnvelope(envelope,passCode){
    if(!(window.crypto&&crypto.subtle&&window.TextDecoder))throw new Error('Dieses Geraet kann den verschluesselten Transfer nicht lesen.');
    const salt=kggConfigTransferBase64UrlToBytes(envelope.salt);
    const iv=kggConfigTransferBase64UrlToBytes(envelope.iv);
    const cipher=kggConfigTransferBase64UrlToBytes(envelope.ciphertext);
    const key=await kggConfigTransferKey(passCode,salt);
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv},key,cipher);
    return JSON.parse(new TextDecoder().decode(plain));
  }
  function applyKggConfigTransferPlain(plain){
    if(!plain||plain.kind!=='kgg_config_transfer_v2')throw new Error('Kein KGG-Konfig-Transfer.');
    if(plain.expiresAt&&Date.parse(plain.expiresAt)<Date.now())throw new Error('Konfig-Transfer ist abgelaufen.');
    const secrets=plain.secrets||{};
    applyAdminCodePackageData({
      geminiKeys:Array.isArray(secrets.geminiKeys)?secrets.geminiKeys:[],
      mediaDropzoneEndpoint:secrets.mediaDropzoneEndpoint||'',
      mediaDropzoneUploadToken:secrets.mediaDropzoneUploadToken||''
    });
    return true;
  }
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
