# KGG Source Chunk 047

- Source: `kgg-update/index.html`
- Lines: 19741-20160

```html
  function renderPackages(){
    const el=$('packageList');
    if(el){
      el.innerHTML=(state.packages||[]).map(p=>'<div class="notice"><b>'+escapeHtml(p.name)+'</b><br><small>'+(p.exercises||[]).map(escapeHtml).join(', ')+'</small><br><button class="mutedBtn" data-pkg="'+p.id+'">Paket in Plan uebernehmen</button></div>').join('');
      el.querySelectorAll('[data-pkg]').forEach(b=>b.onclick=()=>applyPackageToPlan(b.dataset.pkg));
    }
    renderTabletPackageOverlay();
  }
  function sanitizeSharedBankExercise(ex){
    return {
      id:String(ex.id||ex.sourceId||('shared_'+compact(ex.name))).slice(0,80),
      name:String(ex.name||'').trim(),
      aliases:String(ex.aliases||ex.name||'').trim(),
      sets:normalizeSetCount(ex.sets||3),
      unit:String(ex.unit||'Wdh'),
      weightUnit:normalizeLoadUnit(ex.weightUnit||'kg'),
      shared:true,
      createdAt:String(ex.createdAt||ex.updatedAt||new Date().toISOString()),
      updatedAt:String(ex.updatedAt||new Date().toISOString())
    };
  }
  function buildSharedExerciseBankPayload(){
    const exercises=bank.map(sanitizeSharedBankExercise).filter(ex=>ex.name);
    return {kind:'kgg-shared-exercise-bank',version:1,appVersion:VERSION,exportedAt:new Date().toISOString(),exercises};
  }
  function parseSharedExerciseBankPayload(raw){
    const payload=typeof raw==='string'?JSON.parse(raw):raw;
    const exercises=Array.isArray(payload)?payload:(Array.isArray(payload&&payload.exercises)?payload.exercises:(Array.isArray(payload&&payload.exerciseBank)?payload.exerciseBank:[]));
    if(!exercises.length)throw new Error('Keine Übungen im Import gefunden.');
    return exercises.map(sanitizeSharedBankExercise).filter(ex=>ex.name);
  }
  function mergeSharedExerciseBank(raw){
    const incoming=parseSharedExerciseBankPayload(raw);
    let added=0,updated=0;
    incoming.forEach(ex=>{
      const existing=bank.find(item=>compact(item.name)===compact(ex.name));
      if(existing){
        if(syncTimestamp(ex.updatedAt)>=syncTimestamp(existing.updatedAt||existing.createdAt)){
          existing.aliases=ex.aliases||existing.aliases;
          existing.sets=ex.sets||existing.sets;
          existing.unit=ex.unit||existing.unit;
          existing.weightUnit=ex.weightUnit||existing.weightUnit;
          existing.shared=true;
          existing.updatedAt=ex.updatedAt||new Date().toISOString();
          updated+=1;
        }
      }else{
        bank.push({...ex,id:ex.id||('shared_'+Date.now()+'_'+added),custom:true,shared:true});
        added+=1;
      }
      deletedBankIds.delete(String(ex.id||''));
    });
    persistDeletedBankIds();
    persistCustomBank();
    render();
    return {added,updated,total:incoming.length};
  }
  function openSharedBankModal(){
    const text=$('sharedBankText'), status=$('sharedBankStatus');
    if(text)text.value=JSON.stringify(buildSharedExerciseBankPayload(),null,2);
    if(status)status.textContent='Bereit.';
    $('sharedBankModal').classList.add('open');
  }
  function closeSharedBankModal(){$('sharedBankModal').classList.remove('open');}
  async function copySharedBankPayload(){
    const text=$('sharedBankText'), status=$('sharedBankStatus');
    if(!text)return;
    try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text.value); if(status)status.textContent='Export kopiert.'; return;}}catch(err){console.warn('DB-Export konnte nicht kopiert werden:',err);}
    text.focus(); text.select(); if(status)status.textContent='Export markiert.';
  }
  function applySharedBankFromText(){
    const status=$('sharedBankStatus');
    try{const result=mergeSharedExerciseBank($('sharedBankText').value); if(status)status.textContent='Import übernommen: '+result.added+' neu, '+result.updated+' aktualisiert.';}
    catch(err){if(status)status.textContent='Import nicht übernommen: '+(err&&err.message||'unbekannter Fehler');}
  }
  function handleSharedBankFile(ev){
    const file=ev.target.files&&ev.target.files[0];
    ev.target.value='';
    if(!file)return;
    const reader=new FileReader();
    reader.onload=()=>{if($('sharedBankText'))$('sharedBankText').value=String(reader.result||''); if($('sharedBankStatus'))$('sharedBankStatus').textContent='Import geladen.';};
    reader.readAsText(file);
  }
  window.KGGSharedBank={exportPayload:buildSharedExerciseBankPayload,merge:mergeSharedExerciseBank,open:openSharedBankModal};
  let nativeExerciseSyncTimer=null;
  let nativeExerciseSyncApplying=false;
  function nativeExerciseSyncAvailable(){
    return !!(window.KGGNativeSync&&window.KGGNativeSync.available&&typeof window.KGGNativeSync.read==='function'&&typeof window.KGGNativeSync.write==='function');
  }
  function syncTimestamp(value){const t=Date.parse(value||''); return Number.isFinite(t)?t:0;}
  function assertCrossDataSafeSyncDocument(doc){
    const allowedPolicyKeys=new Set(['patients','secrets','debugPayloads','rawData']);
    const blockedKeyPattern=new RegExp(['patient','gemini','api'+'key','api'+'_'+'key','secret','token','raw'+'payload','base64'+'payload','qrraw'].join('|'));
    const blocked=[];
    const visit=(value,path)=>{
      if(!value||typeof value!=='object')return;
      Object.keys(value).forEach(key=>{
        const lower=String(key).toLowerCase();
        const policyKey=(path==='sync.privacy'||path.endsWith('.privacy'))&&allowedPolicyKeys.has(key);
        if(policyKey){
          if(value[key]!==false)blocked.push(path+'.'+key);
        }else if(blockedKeyPattern.test(lower)){
          blocked.push(path+'.'+key);
        }
        visit(value[key],path+'.'+key);
      });
    };
    visit(doc,'sync');
    if(blocked.length)throw new Error('Sync-Safe blockiert geschuetzte Felder: '+blocked.slice(0,3).join(', '));
    return doc;
  }
  function syncSafeOrigin(){
    let deviceId='';
    try{deviceId=syncPairDeviceId();}catch(err){deviceId='web_'+Date.now().toString(36);}
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const displayName=String(($('therapistName')&&$('therapistName').value)||state.patient.therapist||'KGG Geraet').trim();
    return {deviceId,therapistId:String(config.therapistId||deviceId),displayName,roomId:syncPairRoomId()};
  }
  function syncSafeTombstones(exportedAt){
    return [...deletedBankIds].map(id=>({id:String(id),deleted:true,updatedAt:exportedAt}));
  }
  function sanitizeNativeSyncPackage(pkg){
    return {
      id:String(pkg&&pkg.id||('pkg_'+compact(pkg&&pkg.name||''))).slice(0,96),
      name:String(pkg&&pkg.name||'').trim(),
      exercises:Array.isArray(pkg&&pkg.exercises)?pkg.exercises.map(name=>String(name||'').trim()).filter(Boolean):[],
      createdAt:String(pkg&&pkg.createdAt||new Date().toISOString()),
      updatedAt:String(pkg&&pkg.updatedAt||pkg&&pkg.createdAt||new Date().toISOString()),
      source:String(pkg&&pkg.source||'exercise-package')
    };
  }
  function buildNativeExerciseBankSyncDocument(){
    const exportedAt=new Date().toISOString();
    return assertCrossDataSafeSyncDocument({
      kind:'kgg_cross_data_safe_sync',
      version:2,
      appVersion:VERSION,
      exportedAt,
      roomId:syncPairRoomId(),
      schema:'exercise-bank-packages-v2',
      scopes:['exerciseBank','packages'],
      privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},
      origin:syncSafeOrigin(),
      exerciseBank:buildSharedExerciseBankPayload().exercises,
      packages:(state.packages||[]).map(sanitizeNativeSyncPackage).filter(pkg=>pkg.name&&pkg.exercises.length),
      tombstones:{exerciseBank:syncSafeTombstones(exportedAt)}
    });
  }
  function applyNativeSyncExerciseTombstones(rawTombstones){
    const incoming=Array.isArray(rawTombstones)?rawTombstones:[];
    let removed=0;
    incoming.forEach(item=>{
      const id=String(item&&item.id||'').trim();
      if(!id)return;
      const idx=bank.findIndex(ex=>String(ex&&ex.id)===id);
      if(idx>=0){bank.splice(idx,1);removed+=1;}
      deletedBankIds.add(id);
    });
    if(incoming.length){persistDeletedBankIds();persistCustomBank();render();}
    return {removed,total:incoming.length,ids:new Set(incoming.map(item=>String(item&&item.id||'')).filter(Boolean))};
  }
  function mergeNativeSyncPackages(rawPackages){
    const incoming=(Array.isArray(rawPackages)?rawPackages:[]).map(sanitizeNativeSyncPackage).filter(pkg=>pkg.name&&pkg.exercises.length);
    if(!incoming.length)return {added:0,updated:0,total:0};
    state.packages=Array.isArray(state.packages)?state.packages:[];
    let added=0,updated=0;
    incoming.forEach(pkg=>{
      const existing=state.packages.find(item=>String(item&&item.id)===pkg.id||compact(item&&item.name)===compact(pkg.name));
      if(existing){
        if(syncTimestamp(pkg.updatedAt)>=syncTimestamp(existing.updatedAt||existing.createdAt)){
          Object.assign(existing,pkg);
          updated+=1;
        }
      }else{
        state.packages.push(pkg);
        added+=1;
      }
    });
    return {added,updated,total:incoming.length};
  }
  function syncPeerIdShort(value){const text=String(value||''); return text.length>8?text.slice(-8):text;}
  function syncOriginIsSelf(origin){
    if(!origin)return false;
    const selfId=syncPairDeviceId();
    return String(origin.deviceId||'')===selfId;
  }
  function syncFollowEntryForOrigin(origin){
    if(!origin)return null;
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const list=Array.isArray(config.followedTherapists)?config.followedTherapists:[];
    return list.find(item=>String(item.deviceId||'')===String(origin.deviceId||'')||String(item.therapistId||'')===String(origin.therapistId||''));
  }
  function upsertSyncPeerFromOrigin(origin,autoDownloadDefault){
    if(!origin||syncOriginIsSelf(origin))return null;
    const now=new Date().toISOString();
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const list=Array.isArray(config.followedTherapists)?config.followedTherapists.slice():[];
    const entry={
      therapistId:String(origin.therapistId||origin.deviceId||''),
      deviceId:String(origin.deviceId||origin.therapistId||''),
      displayName:String(origin.displayName||'KGG Geraet'),
      roomId:String(origin.roomId||config.syncRoomId||syncPairRoomId()),
      scopes:['exerciseBank','packages'],
      autoDownload:!!autoDownloadDefault,
      pairedAt:now,
      lastSeenAt:now
    };
    const idx=list.findIndex(item=>String(item.deviceId||'')===entry.deviceId||String(item.therapistId||'')===entry.therapistId);
    if(idx>=0){
      list[idx]={...list[idx],...entry,autoDownload:autoDownloadDefault?true:list[idx].autoDownload!==false,pairedAt:list[idx].pairedAt||now,lastSeenAt:now};
    }else{
      list.push(entry);
    }
    config.followedTherapists=list;
    if(entry.roomId&&!config.syncRoomId)config.syncRoomId=entry.roomId;
    if(!config.therapistId)config.therapistId=syncPairDeviceId();
    writeNativeSyncFollowConfig(config);
    return idx>=0?list[idx]:entry;
  }
  function syncAutoDownloadAllowed(origin,options){
    if(options&&options.allowUnfollowed)return true;
    if(!origin)return true;
    if(syncOriginIsSelf(origin))return false;
    const entry=syncFollowEntryForOrigin(origin);
    return !!entry&&entry.autoDownload!==false;
  }
  function mergeNativeSyncMeshDocument(doc,options){
    const peers=Array.isArray(doc.peers)?doc.peers:[];
    const total={bank:{added:0,updated:0,total:0},packages:{added:0,updated:0,total:0},tombstones:{removed:0,total:0},mesh:{seen:peers.length,merged:0,skipped:0}};
    peers.forEach(peer=>{
      if(!peer||peer.kind!=='kgg_cross_data_safe_sync'){total.mesh.skipped+=1;return;}
      upsertSyncPeerFromOrigin(peer.origin,false);
      if(!syncAutoDownloadAllowed(peer.origin,options)){total.mesh.skipped+=1;return;}
      const result=mergeNativeExerciseBankSyncDocument(peer,{...(options||{}),fromMesh:true});
      if(result&&result.bank){total.bank.added+=result.bank.added||0;total.bank.updated+=result.bank.updated||0;total.bank.total+=result.bank.total||0;}
      if(result&&result.packages){total.packages.added+=result.packages.added||0;total.packages.updated+=result.packages.updated||0;total.packages.total+=result.packages.total||0;}
      if(result&&result.tombstones){total.tombstones.removed+=result.tombstones.removed||0;total.tombstones.total+=result.tombstones.total||0;}
      total.mesh.merged+=1;
    });
    renderSyncPeerList();
    return total;
  }
  function mergeNativeExerciseBankSyncDocument(raw,options){
    const doc=assertCrossDataSafeSyncDocument(typeof raw==='string'?JSON.parse(raw):(raw||{}));
    if(doc.kind==='kgg_cross_data_safe_sync_mesh')return mergeNativeSyncMeshDocument(doc,options||{});
    if(!syncAutoDownloadAllowed(doc.origin,options||{}))return {bank:{added:0,updated:0,total:0},packages:{added:0,updated:0,total:0},tombstones:{removed:0,total:0},skipped:true};
    upsertSyncPeerFromOrigin(doc.origin,!!(options&&options.allowUnfollowed));
    const tombstoneResult=applyNativeSyncExerciseTombstones(doc.tombstones&&doc.tombstones.exerciseBank);
    const exercises=Array.isArray(doc.exerciseBank)?doc.exerciseBank:(Array.isArray(doc.exercises)?doc.exercises:[]);
    const filteredExercises=exercises.filter(ex=>!tombstoneResult.ids.has(String(ex&&ex.id||'')));
    let bankResult={added:0,updated:0,total:0};
    if(filteredExercises.length)bankResult=mergeSharedExerciseBank({exercises:filteredExercises});
    const packageResult=mergeNativeSyncPackages(doc.packages);
    if(packageResult.added||packageResult.updated){save(); render();}
    return {bank:bankResult,packages:packageResult,tombstones:tombstoneResult};
  }
  async function resolveNativeSyncValue(value){return value&&typeof value.then==='function'?await value:value;}
  async function pullNativeExerciseBankSync(reason){
    if(!nativeExerciseSyncAvailable())return null;
    nativeExerciseSyncApplying=true;
    try{return mergeNativeExerciseBankSyncDocument(await resolveNativeSyncValue(window.KGGNativeSync.read()));}
    catch(err){console.warn('Native Sync konnte nicht gelesen werden:',err);return null;}
    finally{nativeExerciseSyncApplying=false;}
  }
  async function pushNativeExerciseBankSync(reason){
    if(!nativeExerciseSyncAvailable())return false;
    try{return !!(await resolveNativeSyncValue(window.KGGNativeSync.write(buildNativeExerciseBankSyncDocument())));}
    catch(err){console.warn('Native Sync konnte nicht geschrieben werden:',err);return false;}
  }
  function queueNativeExerciseBankSync(reason){
    if(nativeExerciseSyncApplying||!nativeExerciseSyncAvailable())return;
    clearTimeout(nativeExerciseSyncTimer);
    nativeExerciseSyncTimer=setTimeout(()=>pushNativeExerciseBankSync(reason),350);
  }
  function initNativeExerciseBankSync(){
    const activate=()=>{pullNativeExerciseBankSync('native_ready').finally(()=>queueNativeExerciseBankSync('native_ready'));};
    if(nativeExerciseSyncAvailable())activate();
    window.addEventListener('kgg:native-sync-ready',activate,{once:true});
  }
  window.KGGNativeExerciseSync={build:buildNativeExerciseBankSyncDocument,merge:mergeNativeExerciseBankSyncDocument,pull:pullNativeExerciseBankSync,push:pushNativeExerciseBankSync};
  const syncPairDeviceIdKey='kgg_sync_pair_device_id_v1';
  const syncPairFallbackConfigKey='kgg_sync_pair_follow_config_v1';
  const syncPairRoomIdKey='kgg_sync_room_id_v1';
  const nativeSyncQrMaxLength=2400;
  let lastSyncPairCode='';
  let nativeSyncLastStatus='';
  function safeBase64JsonEncode(value){
    const json=JSON.stringify(value||{});
    const bytes=new TextEncoder().encode(json);
    let binary='';
    for(let i=0;i<bytes.length;i+=0x8000){
      binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    }
    return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function kggConfigTransferBytesToBase64Url(bytes){
    let binary='';
    for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function kggConfigTransferBase64UrlToBytes(value){
    const body=String(value||'').replace(/-/g,'+').replace(/_/g,'/');
    const padded=body+'='.repeat((4-body.length%4)%4);
    const binary=atob(padded);
    const bytes=new Uint8Array(binary.length);
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
```
