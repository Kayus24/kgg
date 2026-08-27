'use strict';

const assert=require('node:assert/strict');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

const sessionId=live.base64UrlEncode(new Uint8Array(16).fill(3));
const sessionSalt=live.base64UrlEncode(new Uint8Array(32).fill(4));
const pairingId=live.base64UrlEncode(new Uint8Array(16).fill(5));
const plan=live.testFixtures().planSnapshot;

function session(){return {sessionId,sessionSalt,pairingId,code:'12345678',expiresAt:new Date(Date.now()+60000).toISOString()};}
async function aesKey(){return global.crypto.subtle.importKey('raw',live.randomBytes(32),{name:'AES-GCM'},false,['encrypt','decrypt']);}
function relaySocket(){return {readyState:1,sent:[],send(value){this.sent.push(value);},close(){this.readyState=3;}};}
function client(onMessage){
  const socket={readyState:1,send(){},close(){this.readyState=3;}};
  const result=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,transport:{},relay:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:live.makeKeyStore({allowMemory:true}),onMessage});
  result.session=session();result.key=null;result.socket=socket;return result;
}
async function frame(key,sequence,payload=plan){return live.encryptEnvelope(key,sessionId,'therapist',sequence,payload);}
async function rejectsCode(promise,code){await assert.rejects(promise,error=>error&&error.code===code);}
async function withDelayedCrypto(method,delay,callback){
  const subtle=global.crypto.subtle,prototype=Object.getPrototypeOf(subtle),original=prototype[method];
  prototype[method]=async function(...args){await new Promise(resolve=>setTimeout(resolve,delay));return original.apply(this,args);};
  try{return await callback();}finally{prototype[method]=original;}
}

async function main(){
  const pair=await live.createEphemeralKeyPair();
  assert.equal(pair.privateKey.extractable,false);
  await assert.rejects(global.crypto.subtle.exportKey('jwk',pair.privateKey));

  const duplicateKey=await aesKey();let duplicateApplications=0;const duplicateClient=client(()=>{duplicateApplications+=1;});duplicateClient.key=duplicateKey;
  const duplicateFrame=await frame(duplicateKey,1);
  await Promise.all([duplicateClient.receiveRaw(duplicateFrame),duplicateClient.receiveRaw(duplicateFrame)]);
  assert.equal(duplicateApplications,1);
  assert.equal(duplicateClient.closed,true);

  const orderKey=await aesKey();let orderApplications=0;const orderClient=client(()=>{orderApplications+=1;});orderClient.key=orderKey;
  const frame1=await frame(orderKey,1),frame2=await frame(orderKey,2);
  await orderClient.receiveRaw(frame2);
  await orderClient.receiveRaw(frame1);
  assert.equal(orderApplications,0);
  assert.equal(orderClient.closed,true);

  const sequentialKey=await aesKey();let sequentialApplications=0;const sequentialClient=client(()=>{sequentialApplications+=1;});sequentialClient.key=sequentialKey;
  await sequentialClient.receiveRaw(await frame(sequentialKey,1));
  await sequentialClient.receiveRaw(await frame(sequentialKey,2));
  assert.equal(sequentialApplications,2);

  const signing=async()=>new Uint8Array(32).fill(9),therapistSocket=relaySocket(),patientSocket=relaySocket();let reserveHash='',armBody=null,joinBody=null;
  const challengeBody={sessionId,sessionSalt,expiresAt:new Date(Date.now()+60000).toISOString(),protocolVersion:'KGG-LIVE-V1'};
  const therapistRelay={
    async reserve(value){reserveHash=value;return {code:'12345678',expiresAt:challengeBody.expiresAt,protocolVersion:'KGG-LIVE-V1'};},
    async challenge(){return challengeBody;},
    async arm(code,token,proof){armBody={code,token,proof};return {armed:true};},
    async openSocket(){return therapistSocket;},
    async close(){return {deleted:true};}
  };
  const therapist=live.createClient({role:'therapist',mode:'test',simulator:true,pairingId,pairingSigner:signing,relay:therapistRelay,transport:therapistRelay,queue:new live.CiphertextQueue({allowMemory:true})});
  await therapist.reserve();
  assert.match(reserveHash,/^[A-Za-z0-9_-]{43}$/);
  assert.equal(armBody.code,'12345678');
  assert.deepEqual(Object.keys(JSON.parse(therapistSocket.sent[0])).sort(),['role','token','type']);
  const patientRelay={
    async challenge(){return challengeBody;},
    async join(code,proof,patientTokenHash){joinBody={code,proof,patientTokenHash};return {joined:true};},
    async openSocket(){return patientSocket;},
    async close(){return {deleted:true};}
  };
  const patient=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,pairingSigner:signing,relay:patientRelay,transport:patientRelay,queue:new live.CiphertextQueue({allowMemory:true})});
  await patient.join('12345678');
  assert.equal(joinBody.code,'12345678');
  assert.match(joinBody.patientTokenHash,/^[A-Za-z0-9_-]{43}$/);
  assert.deepEqual(Object.keys(JSON.parse(patientSocket.sent[0])).sort(),['role','token','type']);

  const expiredSend=client(()=>{});expiredSend.key=await aesKey();expiredSend.session.expiresAt=new Date(Date.now()-1).toISOString();
  await rejectsCode(expiredSend.send('receipt',{synthetic:true,cursor:0,appliedIds:[]}),'SESSION_EXPIRED');
  const expiredReceive=client(()=>{throw new Error('expired frame applied');});expiredReceive.key=await aesKey();expiredReceive.session.expiresAt=new Date(Date.now()-1).toISOString();
  await expiredReceive.receiveRaw(await frame(expiredReceive.key,1));
  assert.equal(expiredReceive.closed,true);

  const delayedReceiveKey=await aesKey();let delayedApplications=0;const delayedReceive=client(()=>{delayedApplications+=1;});delayedReceive.key=delayedReceiveKey;delayedReceive.session.expiresAt=new Date(Date.now()+8).toISOString();
  await withDelayedCrypto('decrypt',30,async()=>delayedReceive.receiveRaw(await frame(delayedReceiveKey,1)));
  assert.equal(delayedApplications,0);
  assert.equal(delayedReceive.closed,true);
  const delayedSend=client(()=>{});delayedSend.key=await aesKey();delayedSend.session.expiresAt=new Date(Date.now()+8).toISOString();
  await rejectsCode(withDelayedCrypto('encrypt',30,()=>delayedSend.send('receipt',{synthetic:true,cursor:0,appliedIds:[]})),'SESSION_EXPIRED');
  assert.equal(delayedSend.closed,true);

  const contractClient=client(()=>{});contractClient.key=await aesKey();const sent=[];contractClient.socket.send=value=>sent.push(value);
  const contractFixtures=live.testFixtures();await contractClient.sendTrainingEvents(contractFixtures.trainingEvents,contractFixtures.planRevision);assert.equal(sent.length,1);

  const bridgePair=await live.createEphemeralKeyPair();
  const bridgeBase={role:'therapist',mode:'test',simulator:true,pairingId,relay:{},transport:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:live.makeKeyStore({allowMemory:true}),pairingSigner:async()=>new Uint8Array(32).fill(9)};
  const rejectedBridge=live.createClient({...bridgeBase,cryptoBridge:{createEphemeralKeyPair:async()=>({privateKey:'raw-private-key',publicKey:bridgePair.publicKey})}});rejectedBridge.session=session();rejectedBridge.socket={readyState:1,send(){},close(){}};
  await rejectsCode(rejectedBridge.beginKeyExchange(),'NATIVE_CRYPTO_REQUIRED');
  const acceptedBridge=live.createClient({...bridgeBase,cryptoBridge:{createEphemeralKeyPair:async()=>({privateKeyHandle:'opaque-1',pairingId, pairingBinding:live.base64UrlEncode(new Uint8Array(32).fill(8)),publicKey:bridgePair.publicKey})}});acceptedBridge.session=session();acceptedBridge.socket={readyState:1,send(){},close(){}};
  await acceptedBridge.beginKeyExchange();
  assert.equal(acceptedBridge.nativePrivateHandle,'opaque-1');

  console.log(JSON.stringify({status:'PASS',checks:['serialized-duplicate','contiguous-sequence','sequential-order','reserve-challenge-arm','join-token-hash','auth-frame-exact','expiry-send-receive','expiry-during-await','training-events-contract','browser-private-key','bridge-handle-contract']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
