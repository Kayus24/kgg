'use strict';

const assert=require('node:assert/strict');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

const sessionId=live.base64UrlEncode(new Uint8Array(16).fill(3));
const sessionSalt=live.base64UrlEncode(new Uint8Array(32).fill(4));
const pairingId=live.base64UrlEncode(new Uint8Array(16).fill(5));
const plan={type:'plan_snapshot',synthetic:true,planRevision:'a'.repeat(64),title:'Synthetischer Plan',days:2,extendDays:false,stepDays:2,exercises:[{id:'exercise-a',order:0,name:'Synthetische Übung',sets:3,side:'BI',unit:'kg',measure:'Wdh',archived:false}]};

function session(){return {sessionId,sessionSalt,pairingId,code:'12345678',expiresAt:new Date(Date.now()+60000).toISOString()};}
async function aesKey(){return global.crypto.subtle.importKey('raw',live.randomBytes(32),{name:'AES-GCM'},false,['encrypt','decrypt']);}
function client(onMessage){
  const socket={readyState:1,send(){},close(){this.readyState=3;}};
  const result=live.createClient({role:'patient',mode:'test',simulator:true,pairingId,transport:{},relay:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:live.makeKeyStore({allowMemory:true}),onMessage});
  result.session=session();result.key=null;result.socket=socket;return result;
}
async function frame(key,sequence,payload=plan){return live.encryptEnvelope(key,sessionId,'therapist',sequence,payload);}
async function rejectsCode(promise,code){await assert.rejects(promise,error=>error&&error.code===code);}

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

  const expiredSend=client(()=>{});expiredSend.key=await aesKey();expiredSend.session.expiresAt=new Date(Date.now()-1).toISOString();
  await rejectsCode(expiredSend.send('receipt',{synthetic:true,cursor:0,appliedIds:[]}),'SESSION_EXPIRED');
  const expiredReceive=client(()=>{throw new Error('expired frame applied');});expiredReceive.key=await aesKey();expiredReceive.session.expiresAt=new Date(Date.now()-1).toISOString();
  await expiredReceive.receiveRaw(await frame(expiredReceive.key,1));
  assert.equal(expiredReceive.closed,true);

  const bridgePair=await live.createEphemeralKeyPair();
  const bridgeBase={role:'therapist',mode:'test',simulator:true,pairingId,relay:{},transport:{},queue:new live.CiphertextQueue({allowMemory:true}),keyStore:live.makeKeyStore({allowMemory:true}),pairingSigner:async()=>new Uint8Array(32).fill(9)};
  const rejectedBridge=live.createClient({...bridgeBase,cryptoBridge:{createEphemeralKeyPair:async()=>({privateKey:'raw-private-key',publicKey:bridgePair.publicKey})}});rejectedBridge.session=session();rejectedBridge.socket={readyState:1,send(){},close(){}};
  await rejectsCode(rejectedBridge.beginKeyExchange(),'NATIVE_CRYPTO_REQUIRED');
  const acceptedBridge=live.createClient({...bridgeBase,cryptoBridge:{createEphemeralKeyPair:async()=>({privateKeyHandle:'opaque-1',publicKey:bridgePair.publicKey})}});acceptedBridge.session=session();acceptedBridge.socket={readyState:1,send(){},close(){}};
  await acceptedBridge.beginKeyExchange();
  assert.equal(acceptedBridge.nativePrivateHandle,'opaque-1');

  console.log(JSON.stringify({status:'PASS',checks:['serialized-duplicate','contiguous-sequence','sequential-order','expiry-send-receive','browser-private-key','bridge-handle-contract']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
