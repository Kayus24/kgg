#!/usr/bin/env node
"use strict";
// Transactional peer-config rollback against real KGG Core and synthetic storage.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const KEY="kgg_html_app_v2_custom_exercise_bank";
const PEERS="kgg_sync_pair_follow_config_v1";
const clone=x=>JSON.parse(JSON.stringify(x));
async function remotePayload(){
  const a=client("a");a.create("Synthetic remote peer import");
  assert(a.core.persistCustomBank());
  return a.ctx.window.KGGNativeExerciseSync.buildTransport();
}
async function failedMerge(b,payload,options){
  const original=b.storage.setItem.bind(b.storage);let injected=false;
  b.storage.setItem=(k,v)=>{
    if(k===KEY&&!injected){injected=true;throw Error("synthetic_bank_write_failed");}
    return original(k,v);
  };
  let error;
  try{await b.ctx.window.KGGNativeExerciseSync.mergeTransport(payload,options);}
  catch(e){error=e;}
  finally{b.storage.setItem=original;}
  assert(error,"merge must reject");
  assert(injected,"must reach bank store failure");
  return error;
}
async function checkExistingPeer(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="New remote name after failed merge";
  const before=b.storage.getItem(PEERS),bankBefore=JSON.stringify(b.core.bank);
  const cfg=clone(JSON.parse(before));assert(cfg.followedTherapists.some(e=>e.deviceId==="a"));
  await failedMerge(b,doc);
  const after=b.storage.getItem(PEERS);
  console.log("EXISTING_PEER_ROLLBACK="+(after===before));
  assert.equal(JSON.stringify(b.core.bank),bankBefore,"bank state must be restored");
  assert.equal(after,before,"failed import must not persist changed peer name");
}
async function checkNewPeer(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.deviceId="peer_new",doc.origin.therapistId="peer_new";
  doc.origin.displayName="Synthetic not yet paired peer";
  const before=b.storage.getItem(PEERS);
  await failedMerge(b,doc,{allowUnfollowed:true});
  const after=b.storage.getItem(PEERS);
  console.log("NEW_PEER_ROLLBACK="+(after===before));
  assert.equal(after,before,"failed import must not persist newly discovered peer");
}
async function checkSuccessfulDiscovery(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="Legitimate successful rename";
  const before=b.storage.getItem(PEERS);
  const result=await b.ctx.window.KGGNativeExerciseSync.mergeTransport(doc);
  assert(result,"successful merge must return result");
  const after=b.storage.getItem(PEERS);
  console.log("SUCCESSFUL_PEER_DISCOVERY_PRESERVED="+(after!==before));
  assert.notEqual(after,before,"successful import must preserve existing discovery behavior");
}
async function checkNativeProviderRollback(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="Changed native peer label";
  const initial=clone(JSON.parse(b.storage.getItem(PEERS)));
  let nativeConfig=clone(initial),nativeWrites=0;
  b.ctx.window.KGGNativeSync.getFollowConfig=()=>clone(nativeConfig);
  b.ctx.window.KGGNativeSync.setFollowConfig=value=>{nativeWrites++;nativeConfig=clone(value);return true;};
  await failedMerge(b,doc);
  assert.deepEqual(nativeConfig,initial,"native follow config must be restored");
  assert.equal(nativeWrites,2,"native setter called for discovery and rollback");
  console.log("NATIVE_PEER_ROLLBACK=true");
}
async function checkRollbackFailureVisible(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="One-way native peer change";
  let nativeConfig=clone(JSON.parse(b.storage.getItem(PEERS))),writes=0;
  b.ctx.window.KGGNativeSync.getFollowConfig=()=>clone(nativeConfig);
  b.ctx.window.KGGNativeSync.setFollowConfig=value=>{
    writes++;
    if(writes>1)return false;
    nativeConfig=clone(value);
    return true;
  };
  const error=await failedMerge(b,doc);
  assert.match(String(error.message||error),/Rollback unvollstaendig/,"failed native restore must not masquerade as success");
  console.log("NATIVE_RESTORE_FAILURE_REPORTED=true");
}
async function checkNativeRestoreThrows(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="Native throw rollback failure";
  const initial=clone(JSON.parse(b.storage.getItem(PEERS)));
  let nativeConfig=clone(initial),writes=0;
  b.ctx.window.KGGNativeSync.getFollowConfig=()=>clone(nativeConfig);
  b.ctx.window.KGGNativeSync.setFollowConfig=value=>{
    writes++;
    if(writes===2)throw Error("synthetic_native_restore_throw");
    nativeConfig=clone(value);
    return true;
  };
  const error=await failedMerge(b,doc);
  assert.equal(writes,2,"must exercise native restore exception");
  assert.notDeepEqual(nativeConfig,initial,"native restore truly failed");
  const reported=/Rollback unvollstaendig/.test(String(error.message||error));
  console.log("NATIVE_RESTORE_THROW_REPORTED="+reported);
  assert(reported,"native setter exception cannot masquerade as successful rollback");
}
async function checkNativeGetterThrows(){
  const doc=await remotePayload(),b=client("b");
  doc.origin.displayName="Synthetic unreadable native state";
  const beforeBank=JSON.stringify(b.core.bank),beforeStorage=b.storage.getItem(PEERS);
  let getterCalls=0,setterCalls=0;
  b.ctx.window.KGGNativeSync.getFollowConfig=()=>{getterCalls++;throw Error("synthetic_native_getter_failure");};
  b.ctx.window.KGGNativeSync.setFollowConfig=()=>{setterCalls++;return true;};
  let error;
  try{await b.ctx.window.KGGNativeExerciseSync.mergeTransport(doc);}
  catch(err){error=err;}
  console.log("NATIVE_GETTER_FAIL_CLOSED="+Boolean(error&&/synthetic_native_getter_failure/.test(String(error.message||error))&&setterCalls===0));
  assert(error&&/synthetic_native_getter_failure/.test(String(error.message||error)),"unreadable native config must block import before peer mutation");
  assert(getterCalls>=1,"must exercise throwing native getter");
  assert.equal(setterCalls,0,"unreadable native config may not mutate native peer settings");
  assert.equal(JSON.stringify(b.core.bank),beforeBank);
  assert.equal(b.storage.getItem(PEERS),beforeStorage);
}
async function main(){
  await checkNativeGetterThrows();
  await checkNativeRestoreThrows();
  await checkExistingPeer();
  await checkNewPeer();
  await checkSuccessfulDiscovery();
  await checkNativeProviderRollback();
  await checkRollbackFailureVisible();
  console.log("PEER_ROLLBACK_GATE_PASS");
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
