'use strict';

const assert=require('node:assert/strict');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

const planKey='synthetic-plan-a';
const sessionId=live.base64UrlEncode(new Uint8Array(16).fill(3));
const sessionSalt=live.base64UrlEncode(new Uint8Array(32).fill(4));
const pairingId=live.base64UrlEncode(new Uint8Array(16).fill(5));
const publicKey=live.base64UrlEncode(new Uint8Array(65).fill(6));
const pairingBinding=live.base64UrlEncode(new Uint8Array(32).fill(7));

function later(callback){setImmediate(callback);}
function fakeBridge(reply){
  const listeners=new Set(),posted=[];
  const bridge={
    posted,
    addEventListener(type,handler){assert.equal(type,'message');listeners.add(handler);},
    removeEventListener(type,handler){assert.equal(type,'message');listeners.delete(handler);},
    postMessage(raw){const request=JSON.parse(raw);posted.push(request);reply({bridge,request,emit(value){later(()=>listeners.forEach(handler=>handler({data:typeof value==='string'?value:JSON.stringify(value)})));}});}
  };
  return bridge;
}
function ok(request,result){return {version:1,requestId:request.requestId,ok:true,result};}
async function rejectsCode(promise,code){await assert.rejects(promise,error=>error&&error.code===code);}

async function main(){
  const bridge=fakeBridge(({bridge,request,emit})=>{
    if(request.op==='getCapabilities')emit(ok(request,{available:true,protocolVersion:1}));
    else if(request.op==='computeJoinHmac')emit(ok(request,{ok:true,hmac:live.base64UrlEncode(new Uint8Array(32).fill(8))}));
    else if(request.op==='createEphemeralKeyPair')emit(ok(request,{curve:'P-256',sessionId,role:'therapist',pairingId,publicKey,pairingBinding,privateKeyHandle:'native-handle-1'}));
    else if(request.op==='deriveSessionKey')emit(ok(request,{ok:true}));
    else if(request.op==='encryptFrame')emit(ok(request,{ok:true,nonce:live.base64UrlEncode(new Uint8Array(12).fill(9)),ciphertext:live.base64UrlEncode(new Uint8Array(16).fill(10))}));
    else if(request.op==='decryptFrame')emit(ok(request,{ok:true,plaintext:live.base64UrlEncode(new Uint8Array([123,125]))}));
    else if(request.op==='closeSession')emit(ok(request,true));
  });
  const adapter=live.createAndroidCryptoAdapter(bridge,{planKey});
  const capabilities=await adapter.getCapabilities();assert.equal(capabilities.available,true);
  assert.deepEqual(Object.keys(bridge.posted[0]).sort(),['args','op','requestId','version']);assert.deepEqual(bridge.posted[0].args,{});
  const hmac=await adapter.computeJoinHmac({sessionId,sessionSalt});assert.equal(hmac.length,32);
  const pair=await adapter.createEphemeralKeyPair({curve:'P-256',sessionId,role:'therapist'});assert.equal(pair.privateKeyHandle,'native-handle-1');assert.equal('privateKey' in pair,false);
  await adapter.deriveSessionKey({curve:'P-256',sessionId,sessionSalt,pairingId,pairingBinding,privateKeyHandle:pair.privateKeyHandle,peerPublicKey:publicKey,role:'therapist',expiresAt:'2026-08-25T12:34:56.789Z'});
  const encrypted=await adapter.encryptFrame({sessionId,aad:live.base64UrlEncode(new Uint8Array([1])),plaintext:live.base64UrlEncode(new Uint8Array([2]))});assert.equal(encrypted.nonce.length>0,true);
  const decrypted=await adapter.decryptFrame({sessionId,nonce:encrypted.nonce,aad:live.base64UrlEncode(new Uint8Array([1])),ciphertext:encrypted.ciphertext});assert.equal(decrypted.plaintext,'e30');
  await adapter.closeSession();assert.equal(bridge.posted.at(-1).op,'closeSession');

  const unknownBridge=fakeBridge(({emit})=>emit({version:1,requestId:'unknown-id',ok:true,result:{}}));
  const unknownAdapter=live.createAndroidCryptoAdapter(unknownBridge,{planKey});
  await rejectsCode(unknownAdapter.getCapabilities(),'NATIVE_BRIDGE_PROTOCOL');
  await rejectsCode(unknownAdapter.getCapabilities(),'NATIVE_BRIDGE_PROTOCOL');

  let duplicateResponse=null;
  const duplicateBridge=fakeBridge(({request,emit})=>{duplicateResponse=()=>emit(ok(request,{available:true}));duplicateResponse();setTimeout(duplicateResponse,10);});
  const duplicateAdapter=live.createAndroidCryptoAdapter(duplicateBridge,{planKey});
  await duplicateAdapter.getCapabilities();
  await new Promise(resolve=>setTimeout(resolve,30));
  await rejectsCode(duplicateAdapter.getCapabilities(),'NATIVE_BRIDGE_PROTOCOL');

  const malformedBridge=fakeBridge(({emit})=>emit('{"version":1}'));
  const malformedAdapter=live.createAndroidCryptoAdapter(malformedBridge,{planKey});
  await rejectsCode(malformedAdapter.getCapabilities(),'NATIVE_BRIDGE_PROTOCOL');

  let lateEmit=null;
  const timeoutBridge=fakeBridge(({request,emit})=>{lateEmit=()=>emit(ok(request,{available:true}));setTimeout(lateEmit,35);});
  const timeoutAdapter=live.createAndroidCryptoAdapter(timeoutBridge,{planKey,timeoutMs:10});
  await rejectsCode(timeoutAdapter.getCapabilities(),'NATIVE_BRIDGE_TIMEOUT');
  await new Promise(resolve=>setTimeout(resolve,45));
  await rejectsCode(timeoutAdapter.getCapabilities(),'NATIVE_BRIDGE_TIMEOUT');

  const rawKeyBridge=fakeBridge(({request,emit})=>emit(ok(request,{curve:'P-256',sessionId,role:'therapist',pairingId,publicKey,pairingBinding,privateKey:'must-not-cross'})));
  const rawKeyAdapter=live.createAndroidCryptoAdapter(rawKeyBridge,{planKey});
  await rejectsCode(rawKeyAdapter.createEphemeralKeyPair({curve:'P-256',sessionId,role:'therapist'}),'NATIVE_BRIDGE_PROTOCOL');

  const expiry=new Date(Date.now()+60000).toISOString(),left=await live.createEphemeralKeyPair(),right=await live.createEphemeralKeyPair(),session={sessionId,sessionSalt,pairingId,expiresAt:expiry};
  const leftKey=await live.deriveSessionKey(left.privateKey,right.publicKey,session),rightKey=await live.deriveSessionKey(right.privateKey,left.publicKey,session);
  const encryptedFrame=await live.encryptEnvelope(leftKey,sessionId,'therapist',1,{type:'receipt',synthetic:true,cursor:1,appliedIds:[]});
  const decryptedFrame=await live.decryptEnvelope(rightKey,sessionId,'therapist',encryptedFrame,new live.ReplayGuard());assert.equal(decryptedFrame.payload.type,'receipt');

  console.log(JSON.stringify({status:'PASS',checks:['exact-web-message-request','single-response','bounded-response-validation','unknown-duplicate-late-fail-closed','raw-private-key-rejected','documented-operations','shared-hkdf-context']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
