'use strict';

const assert=require('node:assert/strict');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

const PLAN_KEY='plan-synthetic-a';
const material=live.createPairingMaterial();
const pairingId=material.payload.pairingId;
const pairingSecret=live.base64UrlDecode(material.payload.pairingSecret);
const FIXTURE=live.testFixtures();

const text=value=>new TextEncoder().encode(String(value));
const concat=(...values)=>{const arrays=values.map(value=>value instanceof Uint8Array?value:new Uint8Array(value)),out=new Uint8Array(arrays.reduce((sum,value)=>sum+value.length,0));let offset=0;for(const value of arrays){out.set(value,offset);offset+=value.length;}return out;};
const b64=value=>live.base64UrlEncode(value);
const unb64=value=>live.base64UrlDecode(value);
const offerBytes=(role,sessionId,publicKey)=>concat(text('KGG-LIVE-ECDH-OFFER-V1'),unb64(pairingId),text(role),unb64(sessionId),unb64(publicKey));
const sessionInfo=(sessionId,expiresAt)=>concat(text('KGG-LIVE-SESSION-V1'),unb64(pairingId),unb64(sessionId),text(String(new Date(expiresAt).getTime())),text('therapist'),text('patient'));
async function hmac(value){const key=await global.crypto.subtle.importKey('raw',pairingSecret,{name:'HMAC',hash:'SHA-256'},false,['sign']);return new Uint8Array(await global.crypto.subtle.sign('HMAC',key,value));}
async function tokenHash(value){return b64(new Uint8Array(await global.crypto.subtle.digest('SHA-256',text(value))));}
async function waitFor(predicate){const deadline=Date.now()+3000;while(Date.now()<deadline){if(await predicate())return;await new Promise(resolve=>setTimeout(resolve,5));}throw new Error('synthetic e2e readiness timeout');}

function makeAndroidBridge(){
  const listeners=new Set(),state={pair:null,aesKey:null,sessionId:''};
  const emit=value=>setImmediate(()=>listeners.forEach(handler=>handler({data:JSON.stringify(value)})));
  const respond=(request,result)=>emit({version:1,requestId:request.requestId,ok:true,result});
  const fail=request=>emit({version:1,requestId:request.requestId,ok:false,error:'operation_failed'});
  const bridge={
    addEventListener(type,handler){assert.equal(type,'message');listeners.add(handler);},
    removeEventListener(type,handler){assert.equal(type,'message');listeners.delete(handler);},
    postMessage(raw){void dispatch(JSON.parse(raw));}
  };
  async function dispatch(request){
    try{
      assert.equal(request.version,1);assert.equal(request.args.planKey,PLAN_KEY);
      if(request.op==='computeJoinHmac'){respond(request,{ok:true,hmac:b64(await hmac(concat(text('KGG-LIVE-JOIN-V1'),unb64(request.args.sessionId),unb64(request.args.sessionSalt))))});return;}
      if(request.op==='createEphemeralKeyPair'){
        const keyPair=await global.crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},false,['deriveBits']),publicKey=b64(await global.crypto.subtle.exportKey('raw',keyPair.publicKey)),privateKeyHandle='native-handle-1';
        state.pair={keyPair,privateKeyHandle,role:request.args.role,sessionId:request.args.sessionId};state.sessionId=request.args.sessionId;
        respond(request,{curve:'P-256',sessionId:request.args.sessionId,role:request.args.role,pairingId,publicKey,pairingBinding:b64(await hmac(offerBytes(request.args.role,request.args.sessionId,publicKey))),privateKeyHandle});return;
      }
      if(request.op==='verifyPeerOffer'){const offer=JSON.parse(request.args.offer),expected=b64(await hmac(offerBytes(offer.role,offer.sessionId,offer.publicKey)));respond(request,expected===offer.mac);return;}
      if(request.op==='deriveSessionKey'){
        assert(state.pair&&state.pair.privateKeyHandle===request.args.privateKeyHandle);const peer=await global.crypto.subtle.importKey('raw',unb64(request.args.peerPublicKey),{name:'ECDH',namedCurve:'P-256'},false,[]),shared=await global.crypto.subtle.deriveBits({name:'ECDH',public:peer},state.pair.keyPair.privateKey,256),ikm=await global.crypto.subtle.importKey('raw',shared,'HKDF',false,['deriveKey']);
        state.aesKey=await global.crypto.subtle.deriveKey({name:'HKDF',hash:'SHA-256',salt:unb64(request.args.sessionSalt),info:sessionInfo(request.args.sessionId,request.args.expiresAt)},ikm,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);state.sessionId=request.args.sessionId;respond(request,{ok:true});return;
      }
      if(request.op==='encryptFrame'){
        const nonce=global.crypto.getRandomValues(new Uint8Array(12)),ciphertext=await global.crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:unb64(request.args.aad)},state.aesKey,unb64(request.args.plaintext));respond(request,{ok:true,nonce:b64(nonce),ciphertext:b64(ciphertext)});return;
      }
      if(request.op==='decryptFrame'){
        const plaintext=await global.crypto.subtle.decrypt({name:'AES-GCM',iv:unb64(request.args.nonce),additionalData:unb64(request.args.aad)},state.aesKey,unb64(request.args.ciphertext));respond(request,{ok:true,plaintext:b64(plaintext)});return;
      }
      if(request.op==='closeSession'){state.pair=null;state.aesKey=null;respond(request,true);return;}
      if(request.op==='getCapabilities'){respond(request,{available:true,protocolVersion:1});return;}
      fail(request);
    }catch(error){fail(request);}
  }
  return {bridge,state};
}

class MemorySocket{
  constructor(relay,role){this.relay=relay;this.role=role;this.readyState=1;this.listeners=new Map();this.sent=[];}
  addEventListener(type,handler){if(!this.listeners.has(type))this.listeners.set(type,new Set());this.listeners.get(type).add(handler);}
  removeEventListener(type,handler){this.listeners.get(type)?.delete(handler);}
  send(raw){this.sent.push(raw);this.relay.receive(this,raw);}
  deliver(value){const raw=typeof value==='string'?value:JSON.stringify(value);for(const handler of this.listeners.get('message')||[])handler({data:raw});if(typeof this.onmessage==='function')this.onmessage({data:raw});}
  close(){this.readyState=3;for(const handler of this.listeners.get('close')||[])handler({});if(typeof this.onclose==='function')this.onclose({});}
}

class MemoryRelay{
  constructor(){this.record=null;this.sockets={};this.storage=[];this.authRoles=new Set();this.keyHelloCount=0;this.deleteAllCount=0;this.logs=[];}
  async reserve(therapistTokenHash){assert.match(therapistTokenHash,/^[A-Za-z0-9_-]{43}$/);this.record={code:'12345678',sessionId:b64(new Uint8Array(16).fill(31)),sessionSalt:b64(new Uint8Array(32).fill(32)),expiresAt:new Date(Date.now()+120000).toISOString(),therapistTokenHash,patientTokenHash:'',joinProof:'',armed:false,deleted:false};return {code:this.record.code};}
  async challenge(code){assert.equal(code,this.record.code);return {sessionId:this.record.sessionId,sessionSalt:this.record.sessionSalt,expiresAt:this.record.expiresAt,protocolVersion:'KGG-LIVE-V1'};}
  async arm(code,token,joinProof){assert.equal(code,this.record.code);assert.equal(this.record.therapistTokenHash,await tokenHash(token));this.record.joinProof=joinProof;this.record.armed=true;return {armed:true};}
  async join(code,joinProof,patientTokenHash){assert.equal(code,this.record.code);assert(this.record.armed);assert.equal(joinProof,this.record.joinProof);this.record.patientTokenHash=patientTokenHash;return {joined:true};}
  async openSocket(session,role){const socket=new MemorySocket(this,role);this.sockets[role]=socket;return socket;}
  async close(code,token){assert.equal(code,this.record.code);assert.equal(this.record.therapistTokenHash,await tokenHash(token));this.record.deleted=true;this.deleteAllCount+=1;this.sockets={};this.storage=[];return {deleted:true};}
  receive(socket,raw){
    let value;try{value=JSON.parse(raw);}catch(error){socket.close();return;}
    if(!socket.authenticated){
      if(!value||value.type!=='auth'||Object.keys(value).sort().join(',')!=='role,token,type'||value.role!==socket.role){socket.close();return;}
      const expected=socket.role==='therapist'?this.record.therapistTokenHash:this.record.patientTokenHash;
      void tokenHash(String(value.token)).then(hash=>{if(hash!==expected){socket.close();return;}socket.authenticated=true;this.authRoles.add(socket.role);socket.deliver({type:'auth_ok',role:socket.role});const peer=this.sockets[socket.role==='therapist'?'patient':'therapist'];if(peer&&peer.authenticated){peer.deliver({type:'peer_joined',role:socket.role});socket.deliver({type:'peer_joined',role:peer.role});}});return;
    }
    const peer=this.sockets[socket.role==='therapist'?'patient':'therapist'];
    if(value&&value.type==='key_hello'){this.keyHelloCount+=1;if(peer&&peer.authenticated)peer.deliver(value);return;}
    this.storage.push(value);this.logs.push(JSON.stringify({type:'ciphertext',bytes:raw.length}));if(peer&&peer.authenticated)peer.deliver(value);
  }
}

async function main(){
  const relay=new MemoryRelay(),native=makeAndroidBridge(),patientStore=live.makeKeyStore({allowMemory:true});
  await live.importPairingQr(material.qr,patientStore,{planRef:'plan-synthetic-a'});
  const therapist=live.createClient({role:'therapist',mode:'test',simulator:true,pairingId,planKey:PLAN_KEY,cryptoBridge:native.bridge,relay,transport:relay,queue:new live.CiphertextQueue({allowMemory:true}),onMessage:()=>{}});
  let patientMessages=[],therapistMessages=[];
  const patient=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,pairingSigner:data=>patientStore.sign(pairingId,data),keyStore:patientStore,relay,transport:relay,queue:new live.CiphertextQueue({allowMemory:true}),onMessage:value=>patientMessages.push(value)});
  therapist.onMessage=value=>therapistMessages.push(value);
  await therapist.reserve();await patient.join('12345678');await waitFor(()=>therapist.status().keyReady&&patient.status().keyReady);
  assert.deepEqual([...relay.authRoles].sort(),['patient','therapist']);assert(relay.keyHelloCount>=2);assert.equal(relay.storage.length,0);

  await therapist.sendPlanSnapshot(FIXTURE.planSnapshot);await waitFor(()=>patientMessages.some(value=>value.type==='plan_snapshot'));
  await patient.sendTrainingEvents(FIXTURE.trainingEvents,FIXTURE.planRevision);await waitFor(()=>therapistMessages.some(value=>value.type==='training_events'));
  assert.equal(JSON.stringify(relay.storage).includes('Synthetischer Plan'),false);assert.equal(JSON.stringify(relay.storage).includes('event-stable-01'),false);assert.equal(JSON.stringify(relay.storage).includes(material.payload.pairingSecret),false);assert.equal(relay.logs.join('\n').includes('event-stable-01'),false);
  Object.values(FIXTURE.privacyCanaries).forEach(marker=>{assert.equal(JSON.stringify(relay.storage).includes(marker),false);assert.equal(relay.logs.join('\n').includes(marker),false);});
  assert(relay.storage.length>=2);

  if(relay.storage[0]){await patient.receiveRaw(relay.storage[0]);assert.equal(patient.closed,true);}
  const guard=new live.ReplayGuard(),ordered={...relay.storage[0]};guard.check(ordered);guard.commit(ordered,'therapist|1|'+ordered.messageId+'|'+ordered.nonce);assert.throws(()=>guard.check(ordered),/Replay/);
  const quota=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,transport:{},relay:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:patientStore});quota.session={...relay.record};quota.key=await global.crypto.subtle.importKey('raw',live.randomBytes(32),{name:'AES-GCM'},false,['encrypt','decrypt']);quota.sendSequence=400;await assert.rejects(quota.send('receipt',{synthetic:true,cursor:0,appliedIds:[]}),error=>error.code==='QUOTA');
  const expired=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,transport:{},relay:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:patientStore});expired.session={...relay.record,expiresAt:new Date(Date.now()-1).toISOString()};expired.key=quota.key;await assert.rejects(expired.send('receipt',{synthetic:true,cursor:0,appliedIds:[]}),error=>error.code==='SESSION_EXPIRED');assert.equal(expired.closed,true);

  const planB=live.createPairingMaterial(),storeB=live.makeKeyStore({allowMemory:true});await live.importPairingQr(planB.qr,storeB,{planRef:'plan-b'});const binding=live.canonicalBytes({type:'plan_snapshot',planRevision:'1'.repeat(64)});assert.equal(await patientStore.verify(pairingId,binding,await storeB.sign(planB.payload.pairingId,binding)),false);
  global.KGGDataStore={currentPlan:{marker:'KGG_SYNTHETIC_CURRENT_PLAN_MUST_NOT_CROSS'}};const simulator=await live.createTestSimulator();await simulator.sendSyntheticPlanSnapshot();assert.equal(JSON.stringify(simulator.relayFrames()).includes('KGG_SYNTHETIC_CURRENT_PLAN_MUST_NOT_CROSS'),false);

  await therapist.close({reason:'synthetic-end'});assert.equal(relay.deleteAllCount,1);assert.equal(relay.storage.length,0);assert.equal(relay.record.deleted,true);
  await patientStore.remove(pairingId);await assert.rejects(patientStore.get(pairingId));
  console.log(JSON.stringify({status:'PASS',checks:['reserve-challenge-arm-join-auth','bidirectional-key-hello','browser-android-hkdf-interoperability','encrypted-plan-and-events','ciphertext-only-storage-and-logs','replay-order-nonce-duplicate','expiry-and-quota-fail-closed','close-deleteAll','plan-isolation','test-mode-currentPlan-isolation']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
