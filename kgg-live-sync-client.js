/* KGG-TICKET-034 Live-Sync client.  The relay sees only the outer envelope. */
(function installKggLiveSync(global){
  'use strict';

  const PROTOCOL_VERSION=1;
  const PAIRING_PREFIX='KGGLIVEPAIR1:';
  const JOIN_CONTEXT='KGG-LIVE-JOIN-V1';
  const OFFER_CONTEXT='KGG-LIVE-ECDH-OFFER-V1';
  const KEY_CONTEXT='KGG-LIVE-SESSION-V1';
  const BINDING_CONTEXT='KGG-LIVE-PAIRING-BIND-V1';
  const MAX_FRAME_BYTES=64*1024;
  const MAX_QUEUE_BYTES=5*1024*1024;
  const MAX_DATA_FRAMES=400;
  const MAX_EVENTS=400;
  const SESSION_MS=2*60*60*1000;
  const KEY_DB='kgg-live-sync-keys-v1';
  const QUEUE_DB='kgg-live-sync-ciphertext-v1';
  const KEY_STORE='pairingKeys';
  const QUEUE_STORE='frames';
  const ROLE_THERAPIST='therapist';
  const ROLE_PATIENT='patient';
  const TEST_RELAY_HOSTS=new Set(['localhost','127.0.0.1','[::1]']);
  const CONTROL_TYPES=new Set(['auth_ok','peer_joined','peer_left','key_hello','error']);
  const INNER_TYPES=new Set(['plan_snapshot','training_events','receipt','close']);
  const OPAQUE_HANDLE_RE=/^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/;
  const ANDROID_BRIDGE_VERSION=1;
  const ANDROID_BRIDGE_TIMEOUT_MS=5000;
  const ANDROID_BRIDGE_REQUEST_ID_RE=/^[A-Za-z0-9][A-Za-z0-9._~-]{0,63}$/;
  const ANDROID_BRIDGE_OPERATIONS=Object.freeze({
    getCapabilities:[],hasPairing:['planKey'],createPairing:['planKey'],rotatePairing:['planKey'],deletePairing:['planKey'],
    computeJoinHmac:['planKey','sessionId','sessionSalt'],verifyPeerOffer:['planKey','localRole','sessionId','offer'],
    createEphemeralKeyPair:['curve','planKey','sessionId','role'],
    deriveSessionKey:['curve','planKey','sessionId','sessionSalt','pairingId','pairingBinding','privateKeyHandle','peerPublicKey','role','expiresAt'],
    encryptFrame:['planKey','sessionId','aad','plaintext'],decryptFrame:['planKey','sessionId','nonce','aad','ciphertext'],closeSession:[],
    enableBlackout:[],disableBlackout:[]
  });

  function failure(code,message){const err=new Error(message||code);err.code=code;return err;}
  function assert(condition,code,message){if(!condition)throw failure(code,message);}
  function cryptoObject(){
    const value=global.crypto||(typeof globalThis!=='undefined'?globalThis.crypto:null);
    if(!value||!value.subtle||typeof value.getRandomValues!=='function')throw failure('CRYPTO_UNAVAILABLE','Sichere Web-Crypto ist nicht verfügbar.');
    return value;
  }
  function encoder(){return new TextEncoder();}
  function decoder(){return new TextDecoder('utf-8',{fatal:true});}
  function utf8(value){return encoder().encode(String(value));}
  function decodeUtf8(value){try{return decoder().decode(value)}catch(err){throw failure('INVALID_UTF8','Ungültige UTF-8-Daten.');}}
  function concatBytes(){
    const arrays=Array.from(arguments).map(value=>value instanceof Uint8Array?value:new Uint8Array(value));
    const total=arrays.reduce((sum,value)=>sum+value.length,0),out=new Uint8Array(total);
    let offset=0;arrays.forEach(value=>{out.set(value,offset);offset+=value.length;});return out;
  }
  function randomBytes(length){const out=new Uint8Array(length);cryptoObject().getRandomValues(out);return out;}
  function bytesFrom(value){return value instanceof Uint8Array?new Uint8Array(value):new Uint8Array(value||[]);}
  function base64UrlEncode(value){
    const bytes=bytesFrom(value);let binary='';
    for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function base64UrlDecode(value){
    const text=String(value||'');
    assert(/^[A-Za-z0-9_-]+$/.test(text)&&text.length%4!==1,'INVALID_BASE64','Ungültige Base64URL-Daten.');
    let normalized=text.replace(/-/g,'+').replace(/_/g,'/');while(normalized.length%4)normalized+='=';
    let binary;try{binary=atob(normalized)}catch(err){throw failure('INVALID_BASE64','Ungültige Base64URL-Daten.');}
    const out=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)out[i]=binary.charCodeAt(i);return out;
  }
  function equalBytes(a,b){
    const left=bytesFrom(a),right=bytesFrom(b);let diff=left.length^right.length;
    const length=Math.max(left.length,right.length);for(let i=0;i<length;i++)diff|=(left[i%Math.max(1,left.length)]||0)^(right[i%Math.max(1,right.length)]||0);return diff===0;
  }
  function canonicalJson(value){
    if(value===null)return 'null';
    if(typeof value==='string')return JSON.stringify(value);
    if(typeof value==='boolean')return value?'true':'false';
    if(typeof value==='number'){assert(Number.isFinite(value),'INVALID_JSON','Nur endliche Zahlen sind erlaubt.');return JSON.stringify(value);}
    if(Array.isArray(value))return '['+value.map(canonicalJson).join(',')+']';
    assert(value&&typeof value==='object','INVALID_JSON','JSON-Wert muss ein Objekt sein.');
    return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+canonicalJson(value[key])).join(',')+'}';
  }
  function canonicalBytes(value){return utf8(canonicalJson(value));}
  function iso(value){const date=new Date(value);assert(Number.isFinite(date.getTime()),'INVALID_TIME','Ungültiger Zeitpunkt.');return date.toISOString();}
  function strictIso(value){const normalized=iso(value);assert(normalized===String(value),'INVALID_TIME','Zeitpunkt ist nicht kanonisch.');return normalized;}
  async function sha256(value){
    const result=await cryptoObject().subtle.digest('SHA-256',bytesFrom(value));return new Uint8Array(result);
  }
  async function sha256Hex(value){const bytes=await sha256(typeof value==='string'?utf8(value):value);return Array.from(bytes).map(byte=>byte.toString(16).padStart(2,'0')).join('');}
  async function importHmacKey(raw){
    return cryptoObject().subtle.importKey('raw',bytesFrom(raw),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
  }
  async function hmac(key,value){
    const crypto=cryptoObject(),material=key&&key.type==='secret'?key:await importHmacKey(key);
    return new Uint8Array(await crypto.subtle.sign('HMAC',material,bytesFrom(value)));
  }
  async function importAesKey(raw){return cryptoObject().subtle.importKey('raw',bytesFrom(raw),{name:'AES-GCM'},false,['encrypt','decrypt']);}

  function exactKeys(value,keys){const actual=Object.keys(value||{}).sort(),expected=keys.slice().sort();return actual.length===expected.length&&actual.every((key,index)=>key===expected[index]);}
  function validateId(value,bytes,message){const decoded=base64UrlDecode(value);assert(decoded.length===bytes,'INVALID_ID',message||'Ungültige Kennung.');return decoded;}
  function validatePlanKey(value){const text=String(value||'');assert(/^[A-Za-z0-9][A-Za-z0-9._~-]{0,127}$/.test(text),'NATIVE_CRYPTO_REQUIRED','Native Planbindung ist ungültig.');return text;}

  function rejectRawPrivateKey(value,seen,depth){
    if(value===null||typeof value!=='object')return;
    assert(depth<8,'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist zu tief verschachtelt.');
    const visited=seen||new Set();if(visited.has(value))return;visited.add(value);
    Object.keys(value).forEach(key=>{assert(!['privateKey','rawPrivateKey','privateKeyRaw'].includes(key),'NATIVE_BRIDGE_PROTOCOL','Native Antwort enthält ein verbotenes Schlüsselalias.');rejectRawPrivateKey(value[key],visited,depth+1);});
  }
  function nativeResult(value){
    rejectRawPrivateKey(value,new Set(),0);
    if(value&&typeof value==='object'&&!Array.isArray(value)&&Object.prototype.hasOwnProperty.call(value,'ok')){
      assert(value.ok===true,'NATIVE_BRIDGE_OPERATION','Native Operation wurde abgelehnt.');const copy={...value};delete copy.ok;return copy;
    }
    return value;
  }
  function parseAndroidBridgeResponse(event){
    const raw=event&&Object.prototype.hasOwnProperty.call(event,'data')?event.data:event;
    assert(typeof raw==='string'&&raw.length>0&&raw.length<=128*1024,'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');
    let value;try{value=JSON.parse(raw)}catch(err){throw failure('NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');}
    assert(value&&typeof value==='object'&&!Array.isArray(value),'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');
    assert(value.version===ANDROID_BRIDGE_VERSION&&typeof value.requestId==='string'&&ANDROID_BRIDGE_REQUEST_ID_RE.test(value.requestId),'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');
    assert(typeof value.ok==='boolean','NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');
    if(value.ok){assert(exactKeys(value,['version','requestId','ok','result']),'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');}
    else{assert(exactKeys(value,['version','requestId','ok','error'])&&typeof value.error==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(value.error),'NATIVE_BRIDGE_PROTOCOL','Native Antwort ist ungültig.');}
    return value;
  }
  function makeAndroidCryptoAdapter(bridge,options){
    assert(bridge&&typeof bridge.postMessage==='function','NATIVE_CRYPTO_REQUIRED','KGGLiveKey-WebMessage-Bridge fehlt.');
    const planKey=validatePlanKey(options&&options.planKey),timeoutMs=Number.isFinite(Number(options&&options.timeoutMs))?Math.min(ANDROID_BRIDGE_TIMEOUT_MS,Math.max(1,Math.floor(Number(options.timeoutMs)))):ANDROID_BRIDGE_TIMEOUT_MS;let sequence=0,closed=false,fatal=null,listenerAttached=false,previousOnMessage=null;
    const pending=new Map(),settledIds=new Set(),settledOrder=[];
    function remember(id){settledIds.add(id);settledOrder.push(id);while(settledOrder.length>256)settledIds.delete(settledOrder.shift());}
    function cleanup(){if(!listenerAttached)return;try{if(typeof bridge.removeEventListener==='function')bridge.removeEventListener('message',onMessage);else if(bridge.onmessage===onMessage)bridge.onmessage=previousOnMessage;}catch(err){}listenerAttached=false;}
    function rejectPending(error){for(const entry of pending.values()){clearTimeout(entry.timer);try{entry.reject(error)}catch(err){}}pending.clear();cleanup();}
    function trip(code){if(!fatal)fatal=failure(code,'KGGLiveKey-Bridge wurde sicher geschlossen.');closed=true;rejectPending(fatal);}
    function onMessage(event){if(closed)return;let response;try{response=parseAndroidBridgeResponse(event);}catch(err){trip('NATIVE_BRIDGE_PROTOCOL');return;}const entry=pending.get(response.requestId);if(!entry||settledIds.has(response.requestId)){trip('NATIVE_BRIDGE_PROTOCOL');return;}pending.delete(response.requestId);clearTimeout(entry.timer);remember(response.requestId);if(response.ok){try{const result=response.result;rejectRawPrivateKey(result,new Set(),0);entry.resolve(result);}catch(err){entry.reject(err);trip('NATIVE_BRIDGE_PROTOCOL');}}else entry.reject(failure('NATIVE_BRIDGE_OPERATION','Native Operation wurde abgelehnt.'));}
    try{if(typeof bridge.addEventListener==='function')bridge.addEventListener('message',onMessage);else{previousOnMessage=bridge.onmessage||null;bridge.onmessage=onMessage;}listenerAttached=true;}catch(err){throw failure('NATIVE_CRYPTO_REQUIRED','KGGLiveKey-WebMessage-Bridge konnte nicht registriert werden.');}
    async function call(op,args){
      if(fatal)throw fatal;if(closed)throw failure('NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge ist geschlossen.');assert(Object.prototype.hasOwnProperty.call(ANDROID_BRIDGE_OPERATIONS,op),'NATIVE_BRIDGE_PROTOCOL','Native Operation ist nicht erlaubt.');
      const expected=ANDROID_BRIDGE_OPERATIONS[op];assert(args&&typeof args==='object'&&!Array.isArray(args)&&exactKeys(args,expected),'NATIVE_BRIDGE_PROTOCOL','Native Argumente sind ungültig.');
      if(sequence>=Number.MAX_SAFE_INTEGER)throw failure('NATIVE_BRIDGE_PROTOCOL','Native Request-ID konnte nicht erzeugt werden.');const requestId='kgg-live-'+(++sequence).toString(36);assert(ANDROID_BRIDGE_REQUEST_ID_RE.test(requestId),'NATIVE_BRIDGE_PROTOCOL','Native Request-ID ist ungültig.');
      const request=JSON.stringify({version:ANDROID_BRIDGE_VERSION,requestId,op,args});
      return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{remember(requestId);trip('NATIVE_BRIDGE_TIMEOUT');},timeoutMs);pending.set(requestId,{resolve,reject,timer});try{bridge.postMessage(request);}catch(err){pending.delete(requestId);remember(requestId);trip('NATIVE_BRIDGE_PROTOCOL');}});
    }
    const adapter={
      planKey,
      call,
      async getCapabilities(){return nativeResult(await call('getCapabilities',{}));},
      async hasPairing(){return await call('hasPairing',{planKey})===true;},
      async createPairingQr(){const value=nativeResult(await call('createPairing',{planKey}));assert(value&&typeof value.pairing==='string','NATIVE_BRIDGE_PROTOCOL','Native Kopplungs-QR fehlt.');return {qr:value.pairing};},
      async rotatePairing(){const value=nativeResult(await call('rotatePairing',{planKey}));assert(value&&typeof value.pairing==='string','NATIVE_BRIDGE_PROTOCOL','Native Kopplungs-QR fehlt.');return {qr:value.pairing};},
      async deletePairing(){return await call('deletePairing',{planKey})===true;},
      async computeJoinHmac(args){const value=nativeResult(await call('computeJoinHmac',{planKey,sessionId:String(args&&args.sessionId||''),sessionSalt:String(args&&args.sessionSalt||'')}));return validateId(value&&value.hmac,32,'Native Join-HMAC fehlt.');},
      async verifyPeerOffer(args){const value=await call('verifyPeerOffer',{planKey,localRole:String(args&&args.localRole||''),sessionId:String(args&&args.sessionId||''),offer:canonicalJson(args&&args.offer||{})});return value===true;},
      async createEphemeralKeyPair(args){const value=nativeResult(await call('createEphemeralKeyPair',{curve:String(args&&args.curve||''),planKey,sessionId:String(args&&args.sessionId||''),role:String(args&&args.role||'')}));assert(value&&exactKeys(value,['curve','sessionId','role','pairingId','publicKey','pairingBinding','privateKeyHandle']),'NATIVE_BRIDGE_PROTOCOL','Native ECDH-Antwort ist ungültig.');assert(value.curve==='P-256', 'NATIVE_BRIDGE_PROTOCOL','Native Kurve ist ungültig.');validateId(value.pairingId,16,'Native Kopplungs-ID ist ungültig.');validateId(value.publicKey,65,'Native Public-Key ist ungültig.');validateId(value.pairingBinding,32,'Native Peer-Bindung ist ungültig.');opaqueHandle(value.privateKeyHandle);return value;},
      async deriveSessionKey(args){return nativeResult(await call('deriveSessionKey',{curve:String(args&&args.curve||''),planKey,sessionId:String(args&&args.sessionId||''),sessionSalt:String(args&&args.sessionSalt||''),pairingId:String(args&&args.pairingId||''),pairingBinding:String(args&&args.pairingBinding||''),privateKeyHandle:String(args&&args.privateKeyHandle||''),peerPublicKey:String(args&&args.peerPublicKey||''),role:String(args&&args.role||''),expiresAt:String(args&&args.expiresAt||'')}));},
      async encryptFrame(args){const value=nativeResult(await call('encryptFrame',{planKey,sessionId:String(args&&args.sessionId||''),aad:String(args&&args.aad||''),plaintext:String(args&&args.plaintext||'')}));assert(value&&exactKeys(value,['nonce','ciphertext']),'NATIVE_BRIDGE_PROTOCOL','Native Verschlüsselungsantwort ist ungültig.');validateId(value.nonce,12,'Native Nonce ist ungültig.');assert(base64UrlDecode(value.ciphertext).length>=16,'NATIVE_BRIDGE_PROTOCOL','Native Ciphertext ist ungültig.');return value;},
      async decryptFrame(args){const value=nativeResult(await call('decryptFrame',{planKey,sessionId:String(args&&args.sessionId||''),nonce:String(args&&args.nonce||''),aad:String(args&&args.aad||''),ciphertext:String(args&&args.ciphertext||'')}));assert(value&&exactKeys(value,['plaintext']),'NATIVE_BRIDGE_PROTOCOL','Native Entschlüsselungsantwort ist ungültig.');base64UrlDecode(value.plaintext);return value;},
      async closeSession(){if(closed)return true;const result=await call('closeSession',{});assert(result===true,'NATIVE_BRIDGE_PROTOCOL','Native Sitzung konnte nicht geschlossen werden.');closed=true;cleanup();return true;},
      close(){closed=true;cleanup();rejectPending(failure('NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge ist geschlossen.'));}
    };
    return Object.freeze(adapter);
  }

  function createPairingMaterial(){
    const pairingId=base64UrlEncode(randomBytes(16));
    const pairingSecret=base64UrlEncode(randomBytes(32));
    const createdAt=new Date().toISOString();
    const payload={v:PROTOCOL_VERSION,pairingId,pairingSecret,keyVersion:1,createdAt};
    return {payload,qr:createPairingQr(payload)};
  }
  function createPairingQr(payload){
    const value=payload||{};
    assert(exactKeys(value,['v','pairingId','pairingSecret','keyVersion','createdAt']),'PAIRING_FIELDS','Kopplungsdaten enthalten unerlaubte Felder.');
    assert(value.v===PROTOCOL_VERSION&&value.keyVersion===1,'PAIRING_VERSION','Nicht unterstützte Kopplungsversion.');
    validateId(value.pairingId,16,'Kopplungs-ID ist ungültig.');
    validateId(value.pairingSecret,32,'Kopplungsschlüssel ist ungültig.');
    strictIso(value.createdAt);
    return PAIRING_PREFIX+base64UrlEncode(utf8(canonicalJson(value)));
  }
  function parsePairingQr(value){
    const text=String(value||'').trim();assert(text.startsWith(PAIRING_PREFIX),'PAIRING_PREFIX','Kein KGGLIVEPAIR1-QR.');
    const json=decodeUtf8(base64UrlDecode(text.slice(PAIRING_PREFIX.length)));let parsed;
    try{parsed=JSON.parse(json)}catch(err){throw failure('PAIRING_JSON','Kopplungs-QR ist beschädigt.');}
    assert(canonicalJson(parsed)===json,'PAIRING_CANONICAL','Kopplungs-QR ist nicht kanonisch.');
    createPairingQr(parsed);
    return {...parsed};
  }
  function isPairingQr(value){return String(value||'').trim().startsWith(PAIRING_PREFIX);}

  function openIndexedDb(name,storeName,keyPath){
    if(!global.indexedDB)return Promise.reject(failure('SECURE_STORAGE_UNAVAILABLE','IndexedDB ist nicht verfügbar.'));
    return new Promise((resolve,reject)=>{
      const request=global.indexedDB.open(name,1);
      request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(storeName))db.createObjectStore(storeName,{keyPath});};
      request.onsuccess=()=>resolve(request.result);
      request.onerror=()=>reject(request.error||failure('SECURE_STORAGE_UNAVAILABLE','Lokaler sicherer Speicher konnte nicht geöffnet werden.'));
    });
  }
  function makeKeyStore(options){
    const allowMemory=!!(options&&options.allowMemory),memory=new Map();let dbPromise=null;
    function db(){return dbPromise||(dbPromise=openIndexedDb((options&&options.name)||KEY_DB,KEY_STORE,'id'));}
    async function write(record){
      if(global.indexedDB){const database=await db();await new Promise((resolve,reject)=>{const tx=database.transaction(KEY_STORE,'readwrite');tx.objectStore(KEY_STORE).put(record);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||failure('SECURE_STORAGE_UNAVAILABLE','Kopplung konnte nicht gespeichert werden.'));});return 'indexeddb';}
      assert(allowMemory,'SECURE_STORAGE_UNAVAILABLE','Nicht exportierbarer Schlüssel-Speicher fehlt.');memory.set(record.id,record);return 'memory';
    }
    async function read(id){
      if(global.indexedDB){const database=await db();return new Promise((resolve,reject)=>{const request=database.transaction(KEY_STORE,'readonly').objectStore(KEY_STORE).get(id);request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error||failure('SECURE_STORAGE_UNAVAILABLE','Kopplung konnte nicht gelesen werden.'));});}
      return allowMemory?(memory.get(id)||null):null;
    }
    async function remove(id){
      if(global.indexedDB){const database=await db();return new Promise((resolve,reject)=>{const tx=database.transaction(KEY_STORE,'readwrite');tx.objectStore(KEY_STORE).delete(id);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||failure('SECURE_STORAGE_UNAVAILABLE','Kopplung konnte nicht gelöscht werden.'));});}
      memory.delete(id);
    }
    return {
      async putSecret(payload){
        const parsed=payload&&payload.payload?payload.payload:payload||{};createPairingQr(parsed);
        const key=await importHmacKey(base64UrlDecode(parsed.pairingSecret));
        const record={id:String(parsed.pairingId),key,keyVersion:1,createdAt:parsed.createdAt,planRef:String(payload&&payload.planRef||''),storedAt:new Date().toISOString()};
        const storage=await write(record);return {pairingId:record.id,keyVersion:1,createdAt:record.createdAt,storage};
      },
      async putKey(id,key,metadata){assert(key&&key.type==='secret','KEY_REQUIRED','Kein nicht exportierbarer Schlüssel.');return write({id:String(id),key,keyVersion:1,createdAt:metadata&&metadata.createdAt||new Date().toISOString(),planRef:String(metadata&&metadata.planRef||''),storedAt:new Date().toISOString()});},
      async get(id){const record=await read(String(id));if(!record||!record.key)throw failure('PAIRING_NOT_FOUND','Kopplung ist auf diesem Gerät nicht gespeichert.');return record;},
      async sign(id,data){const record=await this.get(id);return hmac(record.key,data);},
      async verify(id,data,signature){return equalBytes(await this.sign(id,data),signature);},
      remove,
      async available(){try{if(global.indexedDB){await db();return true;}return allowMemory;}catch(err){return false;}},
      storageMode:()=>global.indexedDB?'indexeddb':(allowMemory?'memory':'none')
    };
  }

  function activeConfig(input){
    const source={...(global.__KGG_LIVE_SYNC_CONFIG||{}),...(input||{})};
    let mode=String(source.mode||global.KGG_LIVE_SYNC_MODE||'off').toLowerCase();
    if(!['off','test','production'].includes(mode))mode='off';
    const simulator=source.simulator===true||global.KGG_LIVE_TEST_SIMULATOR===true;
    const endpoint=String(source.endpoint||'').trim();
    if(mode==='production')return {mode:'off',requestedMode:'production',reason:'production_locked',simulator:false,endpoint:'',productionApproved:false};
    return {mode,requestedMode:mode,reason:'configured',simulator,endpoint,productionApproved:false};
  }
  function assertMode(config,needed){const state=activeConfig(config);assert(state.mode===needed||state.mode==='production'&&needed==='live'||state.mode==='test'&&needed==='live','MODE_OFF','Live-Sync ist deaktiviert.');return state;}
  function assertSynthetic(config,value){const state=activeConfig(config);if(state.mode==='test'){assert(value&&value.synthetic===true,'TEST_DATA_REQUIRED','Der Testmodus akzeptiert ausschließlich synthetische Daten.');if(value.type==='plan_snapshot'||value.type==='training_events')assertTestFixture(value);}}
  function opaqueHandle(value){assert(typeof value==='string'&&OPAQUE_HANDLE_RE.test(value),'NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge lieferte kein gültiges opakes Handle.');return value;}
  function deepFreeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.freeze(value);Object.keys(value).forEach(key=>deepFreeze(value[key]));}return value;}
  const TEST_PLAN_FIXTURE=deepFreeze({type:'plan_snapshot',synthetic:true,planRevision:'1'.repeat(64),title:'Synthetischer Plan',days:2,extendDays:false,stepDays:2,exercises:[{id:'exercise-stable-a',order:0,name:'Synthetische Übung A',sets:3,side:'BI',unit:'kg',measure:'Wdh',archived:false},{id:'exercise-stable-b',order:1,name:'Synthetische Übung B',sets:2,side:'LR',unit:'kg',measure:'Wdh',archived:false}]});
  const TEST_EVENTS_FIXTURE=deepFreeze([{eventId:'event-stable-01',exerciseId:'exercise-stable-a',day:1,set:1,side:'B',metric:'reps',value:77,pain:4,recordedAt:'2026-01-01T00:00:00.000Z'}]);
  function cloneTestValue(value){return JSON.parse(JSON.stringify(value));}
  function assertTestFixture(value){const expected=value&&value.type==='plan_snapshot'?TEST_PLAN_FIXTURE:value&&value.type==='training_events'?{type:'training_events',synthetic:true,basePlanRevision:TEST_PLAN_FIXTURE.planRevision,events:TEST_EVENTS_FIXTURE}:null;assert(expected&&canonicalJson(value)===canonicalJson(expected),'TEST_DATA_REQUIRED','Der Testmodus akzeptiert nur die feste synthetische Fixture.');return true;}
  function testFixtures(config){const state=activeConfig(config);assert(state.mode==='test','MODE_OFF','Testschnittstelle ist nur im expliziten Testmodus aktiv.');return {planSnapshot:cloneTestValue(TEST_PLAN_FIXTURE),trainingEvents:cloneTestValue(TEST_EVENTS_FIXTURE),planRevision:TEST_PLAN_FIXTURE.planRevision};}

  async function buildJoinProof(pairingSigner,sessionId,sessionSalt){
    const id=base64UrlDecode(String(sessionId||'')),salt=base64UrlDecode(String(sessionSalt||''));
    assert(id.length===16&&salt.length===32,'SESSION_FIELDS','Sitzungs-Challenge ist ungültig.');
    return base64UrlEncode(await pairingSigner(concatBytes(utf8(JOIN_CONTEXT),id,salt)));
  }
  function peerOfferBytes(pairingId,role,sessionId,publicKey){return concatBytes(utf8(OFFER_CONTEXT),base64UrlDecode(String(pairingId||'')),utf8(String(role||'')),base64UrlDecode(String(sessionId||'')),base64UrlDecode(String(publicKey||'')));}
  async function buildPairingBinding(pairingSigner,pairingId){return pairingSigner(concatBytes(utf8(BINDING_CONTEXT),base64UrlDecode(pairingId)));}

  async function createEphemeralKeyPair(){
    const keyPair=await cryptoObject().subtle.generateKey({name:'ECDH',namedCurve:'P-256'},false,['deriveBits']);
    const publicKey=await cryptoObject().subtle.exportKey('raw',keyPair.publicKey);
    return {privateKey:keyPair.privateKey,publicKey:base64UrlEncode(publicKey)};
  }
  async function deriveSessionKey(privateKey,peerPublicKey,session){
    const crypto=cryptoObject(),peer=await crypto.subtle.importKey('raw',base64UrlDecode(peerPublicKey),{name:'ECDH',namedCurve:'P-256'},false,[]);
    const shared=await crypto.subtle.deriveBits({name:'ECDH',public:peer},privateKey,256);
    const ikm=await crypto.subtle.importKey('raw',shared,'HKDF',false,['deriveKey']);
    const expiresAt=strictIso(session.expiresAt),expiresAtEpochMillis=new Date(expiresAt).getTime();assert(Number.isSafeInteger(expiresAtEpochMillis),'SESSION_FIELDS','Sitzungsablauf ist ungültig.');
    const info=concatBytes(utf8(KEY_CONTEXT),base64UrlDecode(String(session.pairingId||'')),base64UrlDecode(String(session.sessionId||'')),utf8(String(expiresAtEpochMillis)),utf8(ROLE_THERAPIST),utf8(ROLE_PATIENT));
    return crypto.subtle.deriveKey({name:'HKDF',hash:'SHA-256',salt:base64UrlDecode(session.sessionSalt),info},ikm,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
  }
  function frameAad(sessionId,frame){return canonicalBytes({v:frame.v,sessionId:String(sessionId),messageId:frame.messageId,sender:frame.sender,sequence:frame.sequence});}
  function validateEnvelopeShape(frame,expectedSender){
    assert(frame&&typeof frame==='object'&&!Array.isArray(frame),'INVALID_FRAME','Frame ist ungültig.');
    assert(exactKeys(frame,['v','messageId','sender','sequence','nonce','ciphertext','createdAt']),'INVALID_FRAME','Frame-Felder sind ungültig.');
    assert(frame.v===PROTOCOL_VERSION&&(!expectedSender||frame.sender===expectedSender),'INVALID_FRAME','Frame-Version oder Rolle ist ungültig.');
    assert(Number.isSafeInteger(frame.sequence)&&frame.sequence>0&&frame.sequence<=MAX_DATA_FRAMES,'INVALID_FRAME','Frame-Sequenz ist ungültig.');
    validateId(frame.messageId,16,'Nachrichten-ID ist ungültig.');validateId(frame.nonce,12,'Nonce ist ungültig.');
    const ciphertext=base64UrlDecode(frame.ciphertext);assert(ciphertext.length>=16&&ciphertext.length<=MAX_FRAME_BYTES,'INVALID_FRAME','Ciphertext ist ungültig.');strictIso(frame.createdAt);return frame;
  }
  function validateInner(value){
    assert(value&&typeof value==='object'&&!Array.isArray(value),'INVALID_MESSAGE','Nachricht ist ungültig.');
    assert(INNER_TYPES.has(String(value.type)),'INVALID_MESSAGE_TYPE','Nachrichtentyp ist nicht erlaubt.');
    assert(canonicalBytes(value).length<=MAX_FRAME_BYTES,'FRAME_TOO_LARGE','Nachricht ist zu groß.');return value;
  }
  async function encryptEnvelope(key,sessionId,sender,sequence,payload){
    const inner=validateInner(payload),messageId=base64UrlEncode(randomBytes(16)),nonce=base64UrlEncode(randomBytes(12));
    const frame={v:PROTOCOL_VERSION,messageId,sender,sequence,nonce,ciphertext:'',createdAt:new Date().toISOString()};
    const encrypted=await cryptoObject().subtle.encrypt({name:'AES-GCM',iv:base64UrlDecode(nonce),additionalData:frameAad(sessionId,frame)},key,canonicalBytes(inner));
    frame.ciphertext=base64UrlEncode(encrypted);assert(canonicalBytes(frame).length<=MAX_FRAME_BYTES,'FRAME_TOO_LARGE','Verschlüsselter Frame ist zu groß.');return frame;
  }
  class ReplayGuard{
    constructor(){this.highest=0;this.ids=new Set();this.nonces=new Set();}
    check(frame){
      const id=String(frame.sender)+'|'+String(frame.sequence)+'|'+String(frame.messageId)+'|'+String(frame.nonce);
      assert(!this.ids.has(id)&&!this.nonces.has(frame.nonce),'REPLAY','Replay oder Nonce-Duplikat erkannt.');
      assert(Number(frame.sequence)===this.highest+1,'REPLAY','Sequenz ist nicht die unmittelbar nächste.');return id;
    }
    commit(frame,id){this.ids.add(id);this.nonces.add(frame.nonce);this.highest=Number(frame.sequence);}
  }
  async function decryptEnvelope(key,sessionId,expectedSender,frame,guard){
    validateEnvelopeShape(frame,expectedSender);const ciphertext=base64UrlDecode(frame.ciphertext);const id=guard.check(frame);let plain;
    try{plain=await cryptoObject().subtle.decrypt({name:'AES-GCM',iv:base64UrlDecode(frame.nonce),additionalData:frameAad(sessionId,frame)},key,ciphertext);}catch(err){throw failure('AUTH_FAILED','Frame-Authentifizierung fehlgeschlagen.');}
    const value=JSON.parse(decodeUtf8(new Uint8Array(plain)));validateInner(value);guard.commit(frame,id);return {frame,payload:value};
  }

  function normalizeSession(details,code){
    const session={...details,code:String(code||details&&details.code||'')};
    assert(/^[0-9]{8}$/.test(session.code),'SESSION_FIELDS','Sitzungscode ist ungültig.');
    validateId(session.sessionId,16,'Sitzungs-ID ist ungültig.');validateId(session.sessionSalt,32,'Sitzungssalz ist ungültig.');
    session.expiresAt=strictIso(session.expiresAt);const expiresAt=new Date(session.expiresAt).getTime();assert(expiresAt>Date.now(),'SESSION_EXPIRED','Sitzung ist abgelaufen.');assert(expiresAt<=Date.now()+SESSION_MS+5*60*1000,'SESSION_TOO_LONG','Sitzung überschreitet die Zwei-Stunden-Grenze.');return session;
  }
  function endpointUrl(endpoint,path,config){
    const url=new URL(endpoint);const host=url.hostname.toLowerCase();const privateHost=TEST_RELAY_HOSTS.has(host)||/^10\.(?:\d{1,3}\.){2}\d{1,3}$/.test(host)||/^172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}$/.test(host)||/^192\.168\.(?:\d{1,3}\.)\d{1,3}$/.test(host);
    assert(!url.username&&!url.password&&!url.search&&!url.hash,'ENDPOINT_BLOCKED','Live-Sync-Endpunkt ist nicht erlaubt.');
    assert(url.protocol==='https:'||(url.protocol==='http:'&&config&&config.mode==='test'&&privateHost),'ENDPOINT_BLOCKED','Live-Sync-Endpunkt ist nicht erlaubt.');return new URL(path,url).toString();
  }
  function makeHttpRelay(config){
    const state=activeConfig(config);assert(state.endpoint,'ENDPOINT_MISSING','Kein Live-Sync-Endpunkt konfiguriert.');
    async function request(path,options){
      const response=await fetch(endpointUrl(state.endpoint,path,state),{cache:'no-store',...options,headers:{'Content-Type':'application/json',...(options&&options.headers||{})}});
      const value=await response.json().catch(()=>({}));if(!response.ok)throw failure('RELAY_ERROR','Live-Sync-Verbindung konnte nicht hergestellt werden.');return value;
    }
    return {
      async reserve(tokenHash){return request('/v1/sessions/reserve',{method:'POST',body:JSON.stringify({therapistTokenHash:tokenHash})});},
      async arm(code,token,joinProof){return request('/v1/sessions/'+encodeURIComponent(code)+'/arm',{method:'POST',headers:{Authorization:'Bearer '+token},body:JSON.stringify({joinProof})});},
      async challenge(code){return request('/v1/sessions/'+encodeURIComponent(code)+'/challenge',{method:'GET'});},
      async join(code,joinProof,patientTokenHash){return request('/v1/sessions/'+encodeURIComponent(code)+'/join',{method:'POST',body:JSON.stringify({joinProof,patientTokenHash})});},
      async close(code,token){return request('/v1/sessions/'+encodeURIComponent(code),{method:'DELETE',headers:{Authorization:'Bearer '+token}});},
      async openSocket(session,role,token){
        const url=new URL(endpointUrl(state.endpoint,'/v1/sessions/'+encodeURIComponent(session.code)+'/socket',state));url.protocol=url.protocol==='https:'?'wss:':'ws:';
        return new Promise((resolve,reject)=>{const socket=new WebSocket(url.toString());const onOpen=()=>{socket.removeEventListener('open',onOpen);resolve(socket);};socket.addEventListener('open',onOpen);socket.addEventListener('error',()=>reject(failure('RELAY_SOCKET','Live-Sync-Socket konnte nicht geöffnet werden.')));});
      }
    };
  }

  class CiphertextQueue{
    constructor(options){this.allowMemory=!!(options&&options.allowMemory);this.memory=[];this.dbPromise=null;}
    db(){return this.dbPromise||(this.dbPromise=openIndexedDb(QUEUE_DB,QUEUE_STORE,'id'));}
    async put(sessionId,frame,expiresAt){
      const value={id:String(sessionId)+'|'+String(frame.sender)+'|'+String(frame.sequence),sessionId:String(sessionId),frame,expiresAt};
      assert(canonicalBytes(value.frame).length<=MAX_FRAME_BYTES,'FRAME_TOO_LARGE','Ciphertext-Queue-Frame ist zu groß.');
      if(global.indexedDB){const existing=await this.list(sessionId);const total=existing.filter(item=>item.id!==value.id).reduce((sum,item)=>sum+canonicalBytes(item.frame).length,0)+canonicalBytes(value.frame).length;assert(total<=MAX_QUEUE_BYTES,'QUEUE_FULL','Offline-Queue ist voll.');const db=await this.db();await new Promise((resolve,reject)=>{const tx=db.transaction(QUEUE_STORE,'readwrite');tx.objectStore(QUEUE_STORE).put(value);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||failure('QUEUE_ERROR','Offline-Queue konnte nicht geschrieben werden.'));});return;}
      assert(this.allowMemory,'QUEUE_ERROR','Sicherer Offline-Speicher fehlt.');this.memory=this.memory.filter(item=>item.id!==value.id);this.memory.push(value);assert(this.memory.reduce((sum,item)=>sum+canonicalBytes(item.frame).length,0)<=MAX_QUEUE_BYTES,'QUEUE_FULL','Offline-Queue ist voll.');
    }
    async list(sessionId){
      if(global.indexedDB){const db=await this.db();return new Promise((resolve,reject)=>{const out=[];const request=db.transaction(QUEUE_STORE,'readonly').objectStore(QUEUE_STORE).openCursor();request.onsuccess=()=>{const cursor=request.result;if(!cursor){out.sort((a,b)=>Number(a.frame.sequence)-Number(b.frame.sequence));resolve(out);return;}if(cursor.value.sessionId===String(sessionId))out.push(cursor.value);cursor.continue();};request.onerror=()=>reject(request.error||failure('QUEUE_ERROR','Offline-Queue konnte nicht gelesen werden.'));});}
      return this.memory.filter(item=>item.sessionId===String(sessionId)).sort((a,b)=>Number(a.frame.sequence)-Number(b.frame.sequence));
    }
    async remove(id){
      if(global.indexedDB){const db=await this.db();return new Promise((resolve,reject)=>{const tx=db.transaction(QUEUE_STORE,'readwrite');tx.objectStore(QUEUE_STORE).delete(id);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||failure('QUEUE_ERROR','Offline-Queue konnte nicht bereinigt werden.'));});}
      this.memory=this.memory.filter(item=>item.id!==id);
    }
    async clear(sessionId){
      const items=await this.list(sessionId);for(const item of items)await this.remove(item.id);
    }
    async clearExpired(now){
      if(global.indexedDB){const db=await this.db();const items=[];await new Promise((resolve,reject)=>{const request=db.transaction(QUEUE_STORE,'readonly').objectStore(QUEUE_STORE).openCursor();request.onsuccess=()=>{const cursor=request.result;if(!cursor){resolve();return;}if(Number(cursor.value.expiresAt)<=now)items.push(cursor.value);cursor.continue();};request.onerror=()=>reject(request.error);});for(const item of items)await this.remove(item.id);return items.length;}
      const before=this.memory.length;this.memory=this.memory.filter(item=>Number(item.expiresAt)>now);return before-this.memory.length;
    }
  }

  class LiveSession{
    constructor(options){
      const value=options||{};this.config=activeConfig(value);this.role=value.role;assert(this.role===ROLE_THERAPIST||this.role===ROLE_PATIENT,'ROLE_INVALID','Rolle ist ungültig.');
      this.planKey=String(value.planKey||'');this.pairingId=String(value.pairingId||'');this.pairingSigner=value.pairingSigner;this.cryptoBridge=value.cryptoBridge&&typeof value.cryptoBridge.postMessage==='function'?makeAndroidCryptoAdapter(value.cryptoBridge,{planKey:this.planKey}):value.cryptoBridge||null;this.nativePrivateHandle=null;this.nativePairingBinding='';this.nativeSession=null;this.keyStore=value.keyStore||makeKeyStore({allowMemory:this.config.mode==='test'&&this.config.simulator});this.relay=value.relay||makeHttpRelay(this.config);this.transport=value.transport||this.relay;this.onStatus=typeof value.onStatus==='function'?value.onStatus:()=>{};this.onMessage=typeof value.onMessage==='function'?value.onMessage:()=>{};this.onReady=typeof value.onReady==='function'?value.onReady:()=>{};this.queue=value.queue||new CiphertextQueue({allowMemory:this.config.mode==='test'&&this.config.simulator});this.socket=null;this.session=null;this.token='';this.sendSequence=0;this.acceptedFrames=0;this.key=null;this.privateKey=null;this.publicKey='';this.peerRole=this.role===ROLE_PATIENT?ROLE_THERAPIST:ROLE_PATIENT;this.peerHello=null;this.peerJoined=false;this.guard=new ReplayGuard();this.receivedEvents=[];this.eventIds=new Set();this.sentNonces=new Set();this.closed=false;this.statusValue='idle';this.timer=0;this.receiveChain=Promise.resolve();}
    assertSessionActive(){
      assert(this.session&&!this.closed,'SESSION_REQUIRED','Keine aktive Sitzung.');
      const expiresAt=new Date(this.session.expiresAt).getTime();
      if(!Number.isFinite(expiresAt)||Date.now()>=expiresAt){this.failClosed('SESSION_EXPIRED');throw failure('SESSION_EXPIRED','Sitzung ist abgelaufen.');}
      return this.session;
    }
    status(){return {mode:this.config.mode,role:this.role,sessionCode:this.session&&this.session.code||'',expiresAt:this.session&&this.session.expiresAt||'',connected:!!this.socket&&this.statusValue==='connected',keyReady:!!this.key||!!this.nativeSession,queued:null,status:this.statusValue};}
    setStatus(status,extra){this.statusValue=status;try{this.onStatus({...this.status(),...(extra||{})});}catch(err){}return this.status();}
    async sign(data){
      if(typeof this.pairingSigner==='function')return bytesFrom(await this.pairingSigner(bytesFrom(data)));
      assert(this.pairingId,'PAIRING_REQUIRED','Keine Kopplung ausgewählt.');return this.keyStore.sign(this.pairingId,data);
    }
    async joinProof(){
      this.assertSessionActive();
      if(this.cryptoBridge){const signature=await this.cryptoBridge.computeJoinHmac({sessionId:this.session.sessionId,sessionSalt:this.session.sessionSalt});this.assertSessionActive();return base64UrlEncode(signature);}
      return buildJoinProof(data=>this.sign(data),this.session.sessionId,this.session.sessionSalt);
    }
    async keyHelloSignature(publicKey){
      this.assertSessionActive();
      if(this.cryptoBridge){validateId(this.nativePairingBinding,32,'Native Peer-Bindung ist ungültig.');return this.nativePairingBinding;}
      return base64UrlEncode(await this.sign(peerOfferBytes(this.pairingId,this.role,this.session.sessionId,publicKey)));
    }
    async verifyPeerHello(value){
      if(this.cryptoBridge){const offer={v:PROTOCOL_VERSION,pairingId:this.pairingId,role:value.role,sessionId:value.sessionId,publicKey:value.publicKey,mac:value.signature};return this.cryptoBridge.verifyPeerOffer({localRole:this.role,sessionId:this.session.sessionId,offer});}
      const expected=await this.sign(peerOfferBytes(this.pairingId,value.role,value.sessionId,value.publicKey));return equalBytes(expected,base64UrlDecode(value.signature));
    }
    async reserve(){
      assertMode(this.config,'live');assert(this.role===ROLE_THERAPIST,'ROLE_INVALID','Nur Therapeut:innen reservieren Sitzungen.');assert(this.pairingId,'PAIRING_REQUIRED','Zuerst Kopplungs-QR erzeugen.');
      this.closed=false;this.token=base64UrlEncode(randomBytes(32));const tokenHash=base64UrlEncode(await sha256(utf8(this.token)));const reserved=await this.relay.reserve(tokenHash);const code=String(reserved.code||reserved.session&&reserved.session.code||'').replace(/\D/g,'');assert(/^\d{8}$/.test(code),'SESSION_FIELDS','Relay lieferte keine gültige Sitzungsroute.');const challenge=await this.relay.challenge(code);const details=normalizeSession(challenge,code);this.session={...details,pairingId:this.pairingId};
      this.assertSessionActive();const proof=await this.joinProof();this.assertSessionActive();await this.relay.arm(this.session.code,this.token,proof);this.assertSessionActive();this.armExpiry();await this.connect();return this.session;
    }
    async join(code){
      assertMode(this.config,'live');assert(this.role===ROLE_PATIENT,'ROLE_INVALID','Nur Patient:innen treten Sitzungen bei.');assert(this.pairingId,'PAIRING_REQUIRED','Zuerst Kopplungs-QR scannen.');
      this.closed=false;const challenge=await this.relay.challenge(String(code).replace(/\D/g,''));const details=normalizeSession(challenge,String(code).replace(/\D/g,''));this.session={...details,pairingId:this.pairingId};this.assertSessionActive();const proof=await this.joinProof();this.assertSessionActive();this.token=base64UrlEncode(randomBytes(32));const patientTokenHash=base64UrlEncode(await sha256(utf8(this.token)));const joined=await this.relay.join(this.session.code,proof,patientTokenHash);assert(joined&&joined.joined===true,'RELAY_AUTH','Patienten-Sitzung konnte nicht autorisiert werden.');this.assertSessionActive();this.armExpiry();await this.connect();return this.session;
    }
    async connect(){
      this.assertSessionActive();
      const socket=await this.transport.openSocket(this.session,this.role,this.token);try{this.assertSessionActive();}catch(err){try{if(socket&&socket.close)socket.close();}catch(closeErr){}throw err;}this.socket=socket;this.peerJoined=false;this.bindSocket(socket);this.setStatus('connected');this.sendRaw({type:'auth',role:this.role,token:this.token});
      return this.status();
    }
    bindSocket(socket){
      const message=event=>this.receiveRaw(typeof event==='string'?event:event&&event.data);const close=()=>{if(this.closed)return;this.socket=null;this.setStatus('disconnected');};const error=()=>{if(!this.closed)this.failClosed('SOCKET_ERROR');};
      if(typeof socket.addEventListener==='function'){socket.addEventListener('message',message);socket.addEventListener('close',close);socket.addEventListener('error',error);}else{socket.onmessage=message;socket.onclose=close;socket.onerror=error;}
    }
    sendRaw(value){this.assertSessionActive();assert(this.socket&&this.socket.readyState!==3,'SOCKET_CLOSED','Socket ist geschlossen.');const text=JSON.stringify(value);assert(text.length<=MAX_FRAME_BYTES,'FRAME_TOO_LARGE','Control-Frame ist zu groß.');this.socket.send(text);}
    async beginKeyExchange(){
      this.assertSessionActive();let pair;
      if(!this.publicKey){
        if(this.cryptoBridge){
          assert(typeof this.cryptoBridge.createEphemeralKeyPair==='function','NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge unterstützt kein flüchtiges ECDH.');
          pair=await this.cryptoBridge.createEphemeralKeyPair({curve:'P-256',sessionId:this.session.sessionId,role:this.role});
          this.assertSessionActive();this.nativePrivateHandle=opaqueHandle(pair&&pair.privateKeyHandle);this.nativePairingBinding=String(pair&&pair.pairingBinding||'');this.publicKey=String(pair&&pair.publicKey||'');assert(String(pair&&pair.pairingId||'')===this.pairingId,'NATIVE_CRYPTO_REQUIRED','Native Kopplungs-ID passt nicht zur Sitzung.');validateId(this.nativePairingBinding,32,'Native Peer-Bindung ist ungültig.');validateId(this.publicKey,65,'ECDH-Public-Key ist ungültig.');
        }else{pair=await createEphemeralKeyPair();this.privateKey=pair.privateKey;this.publicKey=pair.publicKey;}
      }
      this.assertSessionActive();const body={v:PROTOCOL_VERSION,type:'key_hello',sessionId:this.session.sessionId,role:this.role,publicKey:this.publicKey};const signature=await this.keyHelloSignature(this.publicKey);this.assertSessionActive();this.sendRaw({...body,signature});
    }
    async receiveRaw(raw){
      const task=this.receiveChain.then(()=>this.receiveRawSerial(raw),()=>this.receiveRawSerial(raw));this.receiveChain=task.catch(()=>{});return task;
    }
    async receiveRawSerial(raw){
      if(!raw)return;
      try{this.assertSessionActive();let value;try{value=typeof raw==='string'?JSON.parse(raw):raw;}catch(err){throw failure('INVALID_FRAME','Frame ist ungültig.');}
        if(value&&typeof value.type==='string'){await this.receiveControl(value);return;}
        assert(this.key||this.nativeSession,'KEY_NOT_READY','Sitzungsschlüssel fehlt.');assert(this.acceptedFrames<MAX_DATA_FRAMES,'QUOTA','Sitzungs-Frame-Limit erreicht.');
        if(this.nativeSession){validateEnvelopeShape(value,this.peerRole);const guardId=this.guard.check(value);this.assertSessionActive();const result=await this.cryptoBridge.decryptFrame({sessionId:this.session.sessionId,nonce:value.nonce,aad:base64UrlEncode(frameAad(this.session.sessionId,value)),ciphertext:value.ciphertext});this.assertSessionActive();const payload=JSON.parse(decodeUtf8(base64UrlDecode(result.plaintext)));validateInner(payload);this.guard.commit(value,guardId);this.acceptedFrames+=1;await this.receiveInner(payload,value);}else{this.assertSessionActive();const result=await decryptEnvelope(this.key,this.session.sessionId,this.peerRole,value,this.guard);this.assertSessionActive();this.acceptedFrames+=1;await this.receiveInner(result.payload,result.frame);}
      }catch(err){this.failClosed(err.code||'FRAME_REJECTED');}
    }
    async receiveControl(value){
      this.assertSessionActive();assert(CONTROL_TYPES.has(value.type),'INVALID_CONTROL','Unbekannter Control-Frame.');
      if(value.type==='error'){assert(exactKeys(value,['type','error']),'INVALID_CONTROL','Relay-Fehlerframe ist ungültig.');this.failClosed('RELAY_ERROR');return;}
      if(value.type==='peer_left'){assert(exactKeys(value,['type','role']),'INVALID_CONTROL','Peer-Frame ist ungültig.');assert(value.role===this.peerRole,'INVALID_CONTROL','Peer-Rolle ist ungültig.');this.setStatus('disconnected');return;}
      if(value.type==='auth_ok'){assert(exactKeys(value,['type','role']),'INVALID_CONTROL','Auth-Bestätigung ist ungültig.');assert(value.role===this.role,'INVALID_CONTROL','Auth-Rolle ist ungültig.');return;}
      if(value.type==='peer_joined'){assert(exactKeys(value,['type','role']),'INVALID_CONTROL','Peer-Beitritt ist ungültig.');assert(value.role===this.peerRole,'INVALID_CONTROL','Peer-Rolle ist ungültig.');this.peerJoined=true;await this.beginKeyExchange();return;}
      if(value.type!=='key_hello')return;
      assert(exactKeys(value,['v','type','sessionId','role','publicKey','signature']),'KEY_PEER_INVALID','Peer-Schlüssel-Frame ist ungültig.');
      assert(value.v===PROTOCOL_VERSION&&value.sessionId===this.session.sessionId&&value.role===this.peerRole,'KEY_PEER_INVALID','Peer-Schlüssel ist nicht für diese Sitzung.');
      validateId(value.publicKey,65,'ECDH-Public-Key ist ungültig.');validateId(value.signature,32,'Peer-HMAC ist ungültig.');
      this.assertSessionActive();assert(await this.verifyPeerHello(value),'KEY_PEER_HMAC','Peer-HMAC ist ungültig.');
      if(this.peerHello&&this.peerHello.publicKey!==value.publicKey)throw failure('KEY_REPLAY','Peer-Schlüssel wurde ausgetauscht.');this.peerHello=value;
      if(!this.privateKey&&!this.nativePrivateHandle)await this.beginKeyExchange();
      if(!this.key&&!this.nativeSession){this.assertSessionActive();if(this.cryptoBridge){assert(typeof this.cryptoBridge.deriveSessionKey==='function','NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge unterstützt keine Sitzungsschlüsselableitung.');await this.cryptoBridge.deriveSessionKey({curve:'P-256',sessionId:this.session.sessionId,sessionSalt:this.session.sessionSalt,pairingId:this.pairingId,pairingBinding:value.signature,privateKeyHandle:this.nativePrivateHandle,peerPublicKey:value.publicKey,role:this.role,expiresAt:this.session.expiresAt});this.assertSessionActive();this.nativeSession=opaqueHandle('native-session');}else{this.assertSessionActive();this.key=await deriveSessionKey(this.privateKey,value.publicKey,this.session);this.assertSessionActive();}this.setStatus('ready',{keyReady:true});await this.flushQueue();this.assertSessionActive();await this.onReady(this.status());}
    }
    async send(type,payload){
      this.assertSessionActive();assert(this.key||this.nativeSession,'KEY_NOT_READY','Sitzungsschlüssel ist noch nicht bereit.');assert(INNER_TYPES.has(type),'INVALID_MESSAGE_TYPE','Nachrichtentyp ist nicht erlaubt.');
      const inner={type,...(payload||{})};assertSynthetic(this.config,inner);if(type!=='close')assert(this.sendSequence<MAX_DATA_FRAMES,'QUOTA','Sitzungs-Frame-Limit erreicht.');const sequence=++this.sendSequence;let frame;this.assertSessionActive();if(this.nativeSession){assert(typeof this.cryptoBridge.encryptFrame==='function','NATIVE_CRYPTO_REQUIRED','KGGLiveKey-Bridge unterstützt keine Frame-Verschlüsselung.');const messageId=base64UrlEncode(randomBytes(16)),aadFrame={v:PROTOCOL_VERSION,messageId,sender:this.role,sequence},result=await this.cryptoBridge.encryptFrame({sessionId:this.session.sessionId,aad:base64UrlEncode(frameAad(this.session.sessionId,aadFrame)),plaintext:base64UrlEncode(canonicalBytes(inner))});this.assertSessionActive();frame={...aadFrame,nonce:result.nonce,ciphertext:result.ciphertext,createdAt:new Date().toISOString()};validateEnvelopeShape(frame,this.role);}else{this.assertSessionActive();frame=await encryptEnvelope(this.key,this.session.sessionId,this.role,sequence,inner);this.assertSessionActive();}assert(!this.sentNonces.has(frame.nonce),'NONCE_REUSE','Nonce wurde wiederverwendet.');this.sentNonces.add(frame.nonce);this.assertSessionActive();await this.queue.put(this.session.sessionId,frame,new Date(this.session.expiresAt).getTime());this.assertSessionActive();
      if(this.socket&&this.socket.readyState!==3){try{this.sendRaw(frame);this.assertSessionActive();await this.queue.remove(String(this.session.sessionId)+'|'+String(frame.sender)+'|'+String(frame.sequence));}catch(err){if(err.code==='SESSION_EXPIRED')throw err;this.setStatus('offline');}}
      else this.setStatus('offline');return {messageId:frame.messageId,sequence:frame.sequence};
    }
    async flushQueue(){if(!this.socket||this.socket.readyState===3||(!this.key&&!this.nativeSession)||!this.session)return;this.assertSessionActive();await this.queue.clearExpired(Date.now());this.assertSessionActive();const items=await this.queue.list(this.session.sessionId);this.assertSessionActive();for(const item of items){try{if(Number(item.expiresAt)<=Date.now()){this.assertSessionActive();await this.queue.remove(item.id);continue;}this.sendRaw(item.frame);this.assertSessionActive();await this.queue.remove(item.id);}catch(err){if(err.code==='SESSION_EXPIRED')throw err;this.setStatus('offline');break;}}}
    async receiveInner(value,frame){
      this.assertSessionActive();assertSynthetic(this.config,value);
      if(value.type==='plan_snapshot'){assert(this.role===ROLE_PATIENT,'MESSAGE_ROLE','Plan-Snapshot darf nur Patient:innen erreichen.');validatePlanSnapshot(value);await this.onMessage(value,{frame});return;}
      if(value.type==='training_events'){assert(this.role===ROLE_THERAPIST,'MESSAGE_ROLE','Trainingsergebnisse dürfen nur Therapeut:innen erreichen.');validateTrainingEvents(value);const fresh=value.events.filter(event=>!this.eventIds.has(event.eventId));fresh.forEach(event=>this.eventIds.add(event.eventId));this.receivedEvents.push(...fresh);if(this.receivedEvents.length>MAX_EVENTS)this.receivedEvents=this.receivedEvents.slice(-MAX_EVENTS);if(fresh.length)await this.onMessage({...value,events:fresh},{frame});await this.send('receipt',{synthetic:value.synthetic===true,cursor:frame.sequence,appliedIds:fresh.map(event=>event.eventId)});return;}
      if(value.type==='receipt'){assert(Number.isInteger(value.cursor)&&value.cursor>=0,'RECEIPT_INVALID','Receipt ist ungültig.');await this.onMessage(value,{frame});return;}
      if(value.type==='close'){await this.onMessage(value,{frame});await this.close({sendClose:false,reason:'peer_closed'});return;}
      throw failure('INVALID_MESSAGE_TYPE','Nachrichtentyp ist nicht erlaubt.');
    }
    async sendPlanSnapshot(snapshot){assert(this.role===ROLE_THERAPIST,'ROLE_INVALID','Nur Therapeut:innen senden Planstände.');validatePlanSnapshot(snapshot);return this.send('plan_snapshot',snapshot);}
    async sendTrainingEvents(events,basePlanRevision){assert(this.role===ROLE_PATIENT,'ROLE_INVALID','Nur Patient:innen senden Trainingsergebnisse.');const value={type:'training_events',synthetic:this.config.mode==='test',basePlanRevision:String(basePlanRevision||''),events:Array.isArray(events)?events:[]};validateTrainingEvents(value);return this.send('training_events',value);}
    failClosed(reason){if(this.closed)return;this.closed=true;clearTimeout(this.timer);if(this.cryptoBridge&&typeof this.cryptoBridge.closeSession==='function'&&(this.nativeSession||this.nativePrivateHandle))this.cryptoBridge.closeSession().catch(()=>{});try{if(this.socket&&this.socket.close)this.socket.close();}catch(err){}this.socket=null;this.key=null;this.nativeSession=null;this.nativePrivateHandle=null;this.nativePairingBinding='';this.privateKey=null;this.publicKey='';this.peerHello=null;this.peerJoined=false;this.queue.clear(this.session&&this.session.sessionId).catch(()=>{});this.setStatus('closed',{reason});}
    armExpiry(){clearTimeout(this.timer);if(!this.session)return;const delay=Math.max(1,new Date(this.session.expiresAt).getTime()-Date.now());this.timer=setTimeout(()=>this.failClosed('SESSION_EXPIRED'),delay);}
    async close(options){
      const value=options||{};if(this.closed)return;const reason=String(value.reason||'user_closed');
      if(value.sendClose!==false&&(this.key||this.nativeSession)){try{await this.send('close',{synthetic:this.config.mode==='test',reason});}catch(err){}}
      try{if(this.session&&this.token&&this.relay.close){this.assertSessionActive();await this.relay.close(this.session.code,this.token);this.assertSessionActive();}}catch(err){if(err.code==='SESSION_EXPIRED'){this.failClosed('SESSION_EXPIRED');return;}}
      if(this.cryptoBridge&&typeof this.cryptoBridge.closeSession==='function'&&(this.nativeSession||this.nativePrivateHandle)){try{await this.cryptoBridge.closeSession();}catch(err){}}
      clearTimeout(this.timer);try{if(this.session){this.assertSessionActive();await this.queue.clear(this.session.sessionId);}}catch(err){if(err.code==='SESSION_EXPIRED'){this.failClosed('SESSION_EXPIRED');return;}}try{if(this.socket&&this.socket.close)this.socket.close();}catch(err){}this.closed=true;this.socket=null;this.key=null;this.nativeSession=null;this.nativePrivateHandle=null;this.nativePairingBinding='';this.privateKey=null;this.publicKey='';this.peerJoined=false;this.setStatus('closed',{reason});
    }
    async reconnect(){this.assertSessionActive();await this.connect();return this.status();}
  }

  function validatePlanSnapshot(value){
    assert(value&&value.type==='plan_snapshot'&&typeof value.planRevision==='string'&&/^[a-f0-9]{64}$/.test(value.planRevision),'PLAN_INVALID','Plan-Snapshot ist ungültig.');
    assert(Array.isArray(value.exercises)&&value.exercises.length<=40,'PLAN_INVALID','Plan-Snapshot enthält zu viele Übungen.');
    const ids=new Set();value.exercises.forEach((exercise,index)=>{assert(exercise&&typeof exercise==='object'&&typeof exercise.id==='string'&&exercise.id.length>=4&&exercise.id.length<=128,'PLAN_INVALID','Übungs-ID fehlt.');assert(!ids.has(exercise.id),'PLAN_INVALID','Übungs-ID ist nicht eindeutig.');ids.add(exercise.id);assert(Number(exercise.order)===index,'PLAN_INVALID','Übungsreihenfolge ist ungültig.');assert(typeof exercise.archived==='boolean','PLAN_INVALID','Archivstatus fehlt.');});return true;
  }
  function validateTrainingEvents(value){
    assert(value&&value.type==='training_events'&&typeof value.basePlanRevision==='string','EVENTS_INVALID','Trainingsergebnisse sind ungültig.');assert(Array.isArray(value.events)&&value.events.length<=MAX_EVENTS,'EVENTS_INVALID','Zu viele Trainingsergebnisse.');
    const ids=new Set();value.events.forEach(event=>{assert(event&&typeof event==='object'&&typeof event.eventId==='string'&&event.eventId.length>=8,'EVENTS_INVALID','Ereignis-ID fehlt.');assert(!ids.has(event.eventId),'EVENTS_INVALID','Ereignis-ID ist nicht eindeutig.');ids.add(event.eventId);assert(typeof event.exerciseId==='string'&&Number.isInteger(Number(event.day))&&Number(event.day)>0,'EVENTS_INVALID','Ereignisbindung ist ungültig.');assert(typeof event.recordedAt==='string','EVENTS_INVALID','Erfassungszeitpunkt fehlt.');if(event.pain!==undefined)assert(Number.isInteger(Number(event.pain))&&Number(event.pain)>=0&&Number(event.pain)<=10,'EVENTS_INVALID','Schmerz-Wert ist ungültig.');});return true;
  }

  async function createTestSimulator(){
    const config=activeConfig({mode:global.KGG_LIVE_SYNC_MODE||'off',simulator:global.KGG_LIVE_TEST_SIMULATOR===true});assert(config.mode==='test'&&config.simulator,'MODE_OFF','Testschnittstelle ist nur im expliziten Testmodus aktiv.');const fixtures=testFixtures(config);global.KGGLiveSyncTest=global.KGGLiveSyncTest||{createSimulator:createTestSimulator,hash:async value=>sha256Hex(canonicalJson(value)),status:()=>({mode:'test',syntheticOnly:true,relayFrames:'ciphertext-only'})};const material=createPairingMaterial(),secret=base64UrlDecode(material.payload.pairingSecret),pairingKey=await importHmacKey(secret);
    const session={sessionId:base64UrlEncode(randomBytes(16)),sessionSalt:base64UrlEncode(randomBytes(32)),pairingId:material.payload.pairingId,code:String(Math.floor(10000000+Math.random()*90000000)),expiresAt:new Date(Date.now()+SESSION_MS).toISOString()};
    const sessionIdHash=await sha256Hex(session.sessionId),left=await createEphemeralKeyPair(),right=await createEphemeralKeyPair(),binding=await hmac(pairingKey,concatBytes(utf8(BINDING_CONTEXT),base64UrlDecode(session.pairingId)));session.pairingBinding=binding;
    const leftKey=await deriveSessionKey(left.privateKey,right.publicKey,session),rightKey=await deriveSessionKey(right.privateKey,left.publicKey,session);const leftGuard=new ReplayGuard(),rightGuard=new ReplayGuard();let leftSequence=0,rightSequence=0;const frames=[];const received={therapist:[],patient:[]};
    async function send(sender,key,guard,sequence,payload){const frame=await encryptEnvelope(key,session.sessionId,sender,sequence,payload);frames.push(JSON.parse(JSON.stringify(frame)));const target=sender===ROLE_THERAPIST?ROLE_PATIENT:ROLE_THERAPIST;const result=await decryptEnvelope(target===ROLE_PATIENT?rightKey:leftKey,session.sessionId,sender,frame,target===ROLE_PATIENT?rightGuard:leftGuard);received[target].push(result.payload);return result.payload;}
    return {
      pairingQr:material.qr,sessionCode:session.code,expiresAt:session.expiresAt,
      async sendSyntheticPlanSnapshot(snapshot){const value=snapshot===undefined?fixtures.planSnapshot:{...snapshot,type:'plan_snapshot',synthetic:true};validatePlanSnapshot(value);assertTestFixture(value);return send(ROLE_THERAPIST,leftKey,leftGuard,++leftSequence,value);},
      async sendSyntheticTrainingEvents(events,basePlanRevision){const value={type:'training_events',synthetic:true,basePlanRevision:basePlanRevision===undefined?fixtures.planRevision:String(basePlanRevision||''),events:events===undefined?fixtures.trainingEvents:events};validateTrainingEvents(value);assertTestFixture(value);return send(ROLE_PATIENT,rightKey,rightGuard,++rightSequence,value);},
      async receive(role){return received[role].slice();},
      async hash(value){return sha256Hex(canonicalJson(value));},
      status(){return {mode:'test',syntheticOnly:true,sessionCode:session.code,sessionIdHash,connected:true,keyReady:true,relayFrameCount:frames.length,plaintextFrames:0};},
      relayFrames(){return frames.map(frame=>({...frame}));},
      async tamper(frame,change){const copy={...(frame||frames[0]),...(change||{})};try{await decryptEnvelope(rightKey,session.sessionId,ROLE_THERAPIST,copy,new ReplayGuard());return false;}catch(err){return true;}}
    };
  }

  const api={
    version:PROTOCOL_VERSION,pairingPrefix:PAIRING_PREFIX,roles:{therapist:ROLE_THERAPIST,patient:ROLE_PATIENT},
    config:activeConfig,randomBytes,base64UrlEncode,base64UrlDecode,canonicalJson,canonicalBytes,sha256Hex,createPairingMaterial,createPairingQr,parsePairingQr,isPairingQr,makeKeyStore,makeHttpRelay,buildJoinProof,peerOfferBytes,createAndroidCryptoAdapter:makeAndroidCryptoAdapter,createEphemeralKeyPair,deriveSessionKey,encryptEnvelope,decryptEnvelope,ReplayGuard,validatePlanSnapshot,validateTrainingEvents,testFixtures,LiveSession,createTestSimulator,
    createClient:options=>new LiveSession(options||{}),CiphertextQueue,
    async importPairingQr(qr,store,metadata){const target=store||makeKeyStore({allowMemory:false});const parsed=parsePairingQr(qr);const result=await target.putSecret({payload:parsed,planRef:metadata&&metadata.planRef||''});return {pairingId:result.pairingId,keyVersion:result.keyVersion,createdAt:result.createdAt,storage:result.storage};},
    status:()=>{const value=activeConfig();return {mode:value.mode,requestedMode:value.requestedMode,reason:value.reason,syntheticOnly:value.mode==='test',productionConfigured:value.mode==='production'};}
  };
  global.KGGLiveSync=api;
  if(activeConfig().mode==='test'&&activeConfig().simulator){
    global.KGGLiveSyncTest={
      createSimulator:createTestSimulator,
      hash:async value=>sha256Hex(canonicalJson(value)),
      status:()=>({mode:'test',syntheticOnly:true,relayFrames:'ciphertext-only'})
    };
  }
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
