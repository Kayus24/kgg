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
    const peerStateBefore=JSON.stringify(normalizeNativeSyncFollowConfig(nativeSyncFollowConfig()||{}));
    const total={bank:{added:0,updated:0,total:0},packages:{added:0,updated:0,total:0},tombstones:{removed:0,added:0,total:0},mesh:{seen:peers.length,merged:0,skipped:0}};
    peers.forEach(peer=>{
      if(!peer||peer.kind!=='kgg_cross_data_safe_sync'){total.mesh.skipped+=1;return;}
      upsertSyncPeerFromOrigin(peer.origin,false);
      if(!syncAutoDownloadAllowed(peer.origin,options)){total.mesh.skipped+=1;return;}
      const result=mergeNativeExerciseBankSyncDocument(peer,{...(options||{}),fromMesh:true});
      if(result&&result.bank){total.bank.added+=result.bank.added||0;total.bank.updated+=result.bank.updated||0;total.bank.total+=result.bank.total||0;}
      if(result&&result.packages){total.packages.added+=result.packages.added||0;total.packages.updated+=result.packages.updated||0;total.packages.total+=result.packages.total||0;}
      if(result&&result.tombstones){total.tombstones.removed+=result.tombstones.removed||0;total.tombstones.added+=result.tombstones.added||0;total.tombstones.total+=result.tombstones.total||0;}
      total.mesh.merged+=1;
    });
    if(peerStateBefore!==JSON.stringify(normalizeNativeSyncFollowConfig(nativeSyncFollowConfig()||{})))renderSyncPeerList();
    return total;
  }
  function mergeNativeExerciseBankSyncDocument(raw,options){
    const doc=assertCrossDataSafeSyncDocument(typeof raw==='string'?JSON.parse(raw):(raw||{}));
    validateNativeLibraryDocument(doc,options||{});
    if(doc.kind==='kgg_cross_data_safe_sync_mesh')return mergeNativeSyncMeshDocument(doc,options||{});
    if(!syncAutoDownloadAllowed(doc.origin,options||{}))return {bank:{added:0,updated:0,total:0},packages:{added:0,updated:0,total:0},tombstones:{removed:0,total:0},skipped:true};
    upsertSyncPeerFromOrigin(doc.origin,!!(options&&options.allowUnfollowed));
    const tombstoneResult=applyNativeSyncExerciseTombstones(doc.tombstones&&doc.tombstones.exerciseBank);
    const exercises=Array.isArray(doc.exerciseBank)?doc.exerciseBank:(Array.isArray(doc.exercises)?doc.exercises:[]);
    const filteredExercises=exercises.filter(ex=>!deletedBankIds.has(String(ex&&ex.id||'')));
    let bankResult={added:0,updated:0,total:0};
    const previousApplying=nativeExerciseSyncApplying;nativeExerciseSyncApplying=true;
    try{if(filteredExercises.length)bankResult=mergeSharedExerciseBank({exercises:filteredExercises},options);}finally{nativeExerciseSyncApplying=previousApplying;}
    const packageResult=options&&options.transport?{added:0,updated:0,total:0}:mergeNativeSyncPackages(doc.packages);
    if(packageResult.added||packageResult.updated){save(); render();}
    return {bank:bankResult,packages:packageResult,tombstones:tombstoneResult};
  }
  function nativeSyncAssertKeys(value,allowed,label){if(!value||typeof value!=='object'||Array.isArray(value))throw new Error(label+' ist ungueltig.');if(Object.keys(value).some(key=>!allowed.includes(key)))throw new Error(label+' enthaelt nicht erlaubte Felder.');}
  function validateNativeLibraryDocument(doc,options){
    const opts=options||{},strict=!!opts.transport;
    if(!doc||typeof doc!=='object')throw new Error('Sync-Dokument fehlt.');
    if(doc.kind==='kgg_cross_data_safe_sync_mesh'){
      if(!Array.isArray(doc.peers)||doc.peers.length>80)throw new Error('Sync-Peerliste ungueltig.');
      if(strict&&String(doc.roomId||'')!==syncPairRoomId())throw new Error('Sync-Raum stimmt nicht ueberein.');
      doc.peers.forEach(peer=>validateNativeLibraryDocument(peer,opts));return doc;
    }
    if(doc.kind!=='kgg_cross_data_safe_sync'||(doc.version!==undefined&&doc.version!==2))throw new Error('Sync-Datenformat ungueltig.');
    if(strict){
      if(new TextEncoder().encode(JSON.stringify(doc)).length>8000000)throw new Error('Bibliotheksdatei ist groesser als 8 MB.');
      nativeSyncAssertKeys(doc,['kind','version','appVersion','exportedAt','roomId','schema','scopes','privacy','origin','exerciseBank','packages','tombstones','mediaBlobs'],'Sync-Dokument');
      if(doc.version!==2||doc.schema!=='exercise-bank-packages-v2'||!Array.isArray(doc.packages)||doc.packages.length||!Array.isArray(doc.scopes)||doc.scopes.some(scope=>scope!=='exerciseBank'))throw new Error('Nur die Uebungsbibliothek darf automatisch uebertragen werden.');
      nativeSyncAssertKeys(doc.privacy,['patients','secrets','debugPayloads','rawData'],'Sync-Datenschutz');
      if(['patients','secrets','debugPayloads','rawData'].some(key=>doc.privacy[key]!==false))throw new Error('Sync-Datenschutz ungueltig.');
      nativeSyncAssertKeys(doc.origin,['deviceId','therapistId','displayName','roomId'],'Sync-Absender');
      if(!doc.origin.deviceId||doc.roomId!==syncPairRoomId()||doc.origin.roomId!==doc.roomId)throw new Error('Sync-Raum oder Absender stimmt nicht ueberein.');
    }else if(doc.roomId&&String(doc.roomId)!==syncPairRoomId()&&!(opts.allowUnfollowed))throw new Error('Sync-Raum stimmt nicht ueberein.');
    const exercises=doc.exerciseBank||doc.exercises;
    if(!Array.isArray(exercises)||exercises.length>2000)throw new Error('Sync-Bibliothek ungueltig.');
    const ids=new Set();
    const fieldKeys=['name','nameDe','nameEn','sets','unit','weightUnit','loadUnit','metricUnit','measure','side','videoUrl','videoLabel','media'];
    const checkFields=value=>{if(value.nameDe!==undefined&&(typeof value.nameDe!=='string'||value.nameDe.length>200||/[\x00-\x1f\x7f]/.test(value.nameDe)))throw new Error('Deutscher Name ungueltig.');for(const key of ['name','nameDe','nameEn','unit','weightUnit','loadUnit','metricUnit','measure','side','videoUrl','videoLabel'])if(value[key]!==undefined&&(typeof value[key]!=='string'||value[key].length>2000))throw new Error('Bibliotheksfeld ungueltig.');if(value.sets!==undefined&&(!Number.isInteger(value.sets)||value.sets<1||value.sets>6))throw new Error('Satzanzahl ungueltig.');};
    const checkMedia=value=>{if(value===undefined)return;if(!Array.isArray(value)||value.length>32)throw new Error('Bildliste ungueltig.');value.forEach(media=>{nativeSyncAssertKeys(media,['id','type','mime','width','height'],'Bildreferenz');if(typeof media.id!=='string'||!media.id||!['image/jpeg','image/png','image/webp'].includes(media.mime)||media.type!=='image')throw new Error('Bildreferenz ungueltig.');if(!opts.prepared)throw new Error('Bildbytes muessen vor dem Import vollstaendig geprueft werden.');});};
    exercises.forEach(ex=>{
      nativeSyncAssertKeys(ex,['id',...fieldKeys,'aliases','progressionGroupId','progressionMainId','progressionVariants','shared','createdAt','updatedAt','syncRevision'],'Bibliotheksuebung');
      if(typeof ex.id!=='string'||!ex.id||ex.id.length>96||ids.has(ex.id)||typeof ex.name!=='string'||!ex.name.trim()||ex.name.length>300)throw new Error('Uebungs-ID oder Name ungueltig.');ids.add(ex.id);
      checkFields(ex);
      if(ex.nameEn!==undefined&&typeof ex.nameEn!=='string')throw new Error('Englischer Name ungueltig.');
      if(ex.syncRevision!==undefined){nativeSyncAssertKeys(ex.syncRevision,['counter','deviceId'],'Bibliotheksrevision');if(!Number.isSafeInteger(ex.syncRevision.counter)||ex.syncRevision.counter<0||typeof ex.syncRevision.deviceId!=='string')throw new Error('Bibliotheksrevision ungueltig.');}
      checkMedia(ex.media);
      if(ex.progressionVariants!==undefined){if(!Array.isArray(ex.progressionVariants)||ex.progressionVariants.length>32)throw new Error('Variantenliste ungueltig.');const stages=new Set();ex.progressionVariants.forEach(stage=>{nativeSyncAssertKeys(stage,['id','groupId',...fieldKeys,'order','sourceId'],'Progressionsstufe');if(typeof stage.id!=='string'||!stage.id||stages.has(stage.id)||typeof stage.name!=='string'||!stage.name.trim())throw new Error('Progressionsstufe ungueltig.');stages.add(stage.id);checkFields(stage);checkMedia(stage.media);});}
    });
    if(doc.tombstones!==undefined){nativeSyncAssertKeys(doc.tombstones,['exerciseBank'],'Loeschliste');if(!Array.isArray(doc.tombstones.exerciseBank)||doc.tombstones.exerciseBank.length>10000)throw new Error('Loeschliste ungueltig.');doc.tombstones.exerciseBank.forEach(item=>{nativeSyncAssertKeys(item,['id','deleted','updatedAt'],'Loeschung');if(typeof item.id!=='string'||!item.id||item.deleted!==true)throw new Error('Loeschung ungueltig.');});}
    return doc;
  }
  function nativeSyncAllMedia(doc){const list=[];(doc.exerciseBank||[]).forEach(ex=>{(ex.media||[]).forEach(media=>list.push(media));(ex.progressionVariants||[]).forEach(stage=>(stage.media||[]).forEach(media=>list.push(media)));});return list;}
  async function nativeSyncDigest(bytes){if(!crypto.subtle)throw new Error('Bildpruefung ist nicht verfuegbar.');const digest=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,'0')).join('');}
  function nativeSyncEncodeBytes(bytes){let text='';for(let i=0;i<bytes.length;i+=0x8000)text+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));return btoa(text);}
  async function buildNativeExerciseBankSyncTransportDocument(){
    const doc=buildNativeExerciseBankSyncDocument(),blobs=new Map();
    for(const ref of nativeSyncAllMedia(doc)){
      if(blobs.has(ref.id))continue;
      const source=bank.flatMap(ex=>[...(ex.media||[]),...(ex.progressionVariants||[]).flatMap(stage=>stage.media||[])]).find(media=>media.id===ref.id);
      const record=await getEncryptedMediaBlob(ref.id);if(!record||!record.blob)throw new Error('Ein Bibliotheksbild fehlt lokal.');
      const plain=await patientDecryptMedia(source,record.blob),bytes=new Uint8Array(await plain.arrayBuffer());
      if(!bytes.length||bytes.length>2000000)throw new Error('Bibliotheksbild ist zu gross.');
      blobs.set(ref.id,{id:ref.id,mime:ref.mime,sha256:await nativeSyncDigest(bytes),base64:nativeSyncEncodeBytes(bytes)});
    }
    doc.mediaBlobs=[...blobs.values()];
    if(new TextEncoder().encode(JSON.stringify(doc)).length>8000000)throw new Error('Bibliotheksdatei ist groesser als 8 MB.');
    validateNativeLibraryDocument(doc,{transport:true,prepared:true});return doc;
  }
  async function prepareNativeLibraryImport(raw,options){
    const text=typeof raw==='string'?raw:JSON.stringify(raw);if(typeof text!=='string')throw new Error('Sync-Datei fehlt.');const bytesLength=new TextEncoder().encode(text).length;if(bytesLength>32000000)throw new Error('Sync-Peerliste ist groesser als 32 MB.');
    const doc=assertCrossDataSafeSyncDocument(JSON.parse(text)),opts={...(options||{}),transport:true,prepared:true};if(doc.kind!=='kgg_cross_data_safe_sync_mesh'&&bytesLength>8000000)throw new Error('Bibliotheksdatei ist groesser als 8 MB.');validateNativeLibraryDocument(doc,opts);
    const docs=doc.kind==='kgg_cross_data_safe_sync_mesh'?doc.peers:[doc],media=new Map(),prepared=[];
    for(const peer of docs){
      if(!syncAutoDownloadAllowed(peer.origin,opts))continue;
      const wire=new Map();if(peer.mediaBlobs!==undefined&&!Array.isArray(peer.mediaBlobs))throw new Error('Bildbytes ungueltig.');
      for(const item of peer.mediaBlobs||[]){nativeSyncAssertKeys(item,['id','mime','sha256','base64'],'Bildbytes');if(typeof item.id!=='string'||wire.has(item.id)||!['image/jpeg','image/png','image/webp'].includes(item.mime)||typeof item.base64!=='string'||item.base64.length>2666670||!item.base64.length||!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(item.base64)||typeof item.sha256!=='string'||!/^[a-f0-9]{64}$/.test(item.sha256))throw new Error('Bildbytes ungueltig.');const bytes=Uint8Array.from(atob(item.base64),char=>char.charCodeAt(0));if(!bytes.length||bytes.length>2000000||await nativeSyncDigest(bytes)!==item.sha256)throw new Error('Bildhash stimmt nicht ueberein.');wire.set(item.id,{item,bytes});}
      for(const ref of nativeSyncAllMedia(peer)){
        const blob=wire.get(ref.id);if(!blob||blob.item.mime!==ref.mime)throw new Error('Bildbytes fehlen oder stimmen nicht ueberein.');
        const known=media.get(ref.id);if(known&&known.syncSha256!==blob.item.sha256)throw new Error('Bild-ID hat widerspruechliche Bytes.');if(known)continue;
        const local=await getEncryptedMediaBlob(ref.id);
        if(local){
          const current=bank.flatMap(ex=>[...(ex.media||[]),...(ex.progressionVariants||[]).flatMap(stage=>stage.media||[])]).find(item=>item.id===ref.id&&item.crypto)||local.manifest;
          if(!local.blob||!current||current.mime!==ref.mime)throw new Error('Vorhandene Bild-ID kann nicht geprueft werden.');
          let existingBytes;
          try{existingBytes=new Uint8Array(await (await patientDecryptMedia(current,local.blob)).arrayBuffer());}catch(err){throw new Error('Vorhandene Bild-ID kann nicht entschluesselt werden.');}
          const existingHash=await nativeSyncDigest(existingBytes);
          if(existingHash!==blob.item.sha256)throw new Error('Vorhandene Bild-ID hat andere Bytes.');
          // Preserve the exact ciphertext/key pair, including original plan references.
          // A cached syncSha256 is only a hint and never substitutes byte verification.
          media.set(ref.id,{...current,syncSha256:existingHash});continue;
        }
        const encrypted=await encryptMediaBlob(new Blob([blob.bytes],{type:ref.mime}));
        const manifest=ensureMediaShape({...ref,crypto:{alg:'AES-GCM',iv:encrypted.iv,key:encrypted.key},encryptedSize:encrypted.encryptedSize,compressedSize:blob.bytes.length,storage:'indexeddb-local',status:'local-encrypted'});manifest.syncSha256=blob.item.sha256;media.set(ref.id,manifest);prepared.push({id:ref.id,blob:encrypted.blob,manifest,createdAt:manifest.createdAt});
      }
    }
    // All documents, references and hashes have passed before any persistent or bank mutation.
    for(const record of prepared)await putEncryptedMediaBlob(record);
    return {doc,options:{...opts,media}};
