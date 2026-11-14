#!/usr/bin/env node
"use strict";
// Synthetic fault-injection at real KGG Core/IndexedDB/localStorage boundaries.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const KEY="kgg_html_app_v2_custom_exercise_bank",TOMB="kgg_html_app_v2_deleted_exercise_bank_ids";
async function payloadWithMedia(a,id){
  a.create("Synthetic media import source");
  const ex=a.core.bank.find(x=>x.name==="Synthetic media import source");
  const bytes=Buffer.from([137,80,78,71,13,10,26,10,1,2,3]);
  const encrypted=await a.core.encryptMediaBlob(new Blob([bytes],{type:"image/png"}));
  const media={id,type:"image",mime:"image/png",width:1,height:1,crypto:{alg:"AES-GCM",iv:encrypted.iv,key:encrypted.key}};
  await a.core.putEncryptedMediaBlob({id,blob:encrypted.blob,manifest:media});
  ex.media=[media];a.core.persistCustomBank();
  return a.ctx.window.KGGNativeExerciseSync.buildTransport();
}
async function expectFailedMerge(b,payload,failKey){
  const original=b.storage.setItem.bind(b.storage);
  b.storage.setItem=(key,value)=>{if(key===failKey)throw Error("synthetic_failure_"+failKey);return original(key,value);};
  try{await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(payload));}
  finally{b.storage.setItem=original;}
}
async function stageMediaCase(){
  const a=client("a"),b=client("b"),id="synthetic_stage_only_image";
  const payload=await payloadWithMedia(a,id);
  b.core.bank.push({id:"local_stage_only",name:"Local progression reference",custom:true,media:[],
    progressionVariants:[{id:"local_variant",name:"Variant",media:[{id,type:"image",mime:"image/png"}]}]});
  assert.equal(b.core.persistCustomBank(),true);
  const before=JSON.stringify(b.core.bank);
  assert.equal(await b.core.getEncryptedMediaBlob(id),null);
  await expectFailedMerge(b,payload,KEY);
  assert.equal(JSON.stringify(b.core.bank),before,"bank must be restored after failed merge");
  const found=await b.core.getEncryptedMediaBlob(id);
  console.log("STAGE_ONLY_REFERENCE_RETAINED="+Boolean(found));
  assert(found,"new media referenced by existing progression stage must not be deleted");
}
async function tombstoneCase(){
  const a=client("a"),b=client("b");
  // A previously persisted custom bank makes restoration use setItem, not removeItem.
  b.core.bank.push({id:"synthetic_existing_custom",name:"Existing custom exercise",custom:true,sets:2});
  assert.equal(b.core.persistCustomBank(),true);
  assert.notEqual(b.storage.getItem(KEY),null);
  const id=b.core.bank[0].id;
  const payload=await a.ctx.window.KGGNativeExerciseSync.buildTransport();
  payload.tombstones.exerciseBank=[{id,deleted:true,updatedAt:"2026-11-12T11:00:00.000Z"}];
  const beforeBank=JSON.stringify(b.core.bank),beforeDeleted=b.storage.getItem(TOMB);
  let attemptedTombstoneWrite=false;
  const priorSet=b.storage.setItem.bind(b.storage);
  b.storage.setItem=(key,value)=>{
    if(key===TOMB&&value!==beforeDeleted)attemptedTombstoneWrite=true;
    return priorSet(key,value);
  };
  try{await expectFailedMerge(b,payload,KEY);}finally{b.storage.setItem=priorSet;}
  assert.equal(attemptedTombstoneWrite,true,"test must reach tombstone persistence before its failure");
  assert.equal(JSON.stringify(b.core.bank),beforeBank,"bank must recover in memory");
  const afterDeleted=b.storage.getItem(TOMB);
  console.log("TOMBSTONE_RESTORED="+(beforeDeleted===afterDeleted));
  assert.equal(afterDeleted,beforeDeleted,"persisted tombstone must be restored independently of bank store failure");
  const reloaded=client("b",new Map(),b.storage);
  assert(reloaded.core.bank.some(ex=>ex.id===id),"reload must not lose exercise after failed tombstone import");
  assert(reloaded.core.bank.some(ex=>ex.id==="synthetic_existing_custom"),"preexisting custom exercise must survive reload");
  console.log("TOMBSTONE_RELOAD_PRESERVED=true");
}
async function snapshotReadFailureCase(){
  const a=client("a"),b=client("b"),id="synthetic_snapshot_read_abort_image";
  const payload=await payloadWithMedia(a,id);
  const before=JSON.stringify(b.core.bank),priorGet=b.storage.getItem.bind(b.storage);
  let getFailureTriggered=false;
  b.storage.getItem=key=>{
    if(key===KEY){getFailureTriggered=true;throw Error("synthetic_snapshot_read_failure");}
    return priorGet(key);
  };
  try{await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(payload),/synthetic_snapshot_read_failure/);}
  finally{b.storage.getItem=priorGet;}
  assert.equal(getFailureTriggered,true);
  assert.equal(JSON.stringify(b.core.bank),before);
  const leaked=await b.core.getEncryptedMediaBlob(id);
  console.log("SNAPSHOT_READ_NO_ORPHAN="+(!leaked));
  assert.equal(leaked,null,"snapshot read error may not leave orphan IDB media");
}
async function lateSnapshotReadFailureCase(){
  const a=client("a"),b=client("b"),id="synthetic_late_snapshot_image";
  const payload=await payloadWithMedia(a,id);
  const oldGet=b.storage.getItem.bind(b.storage);
  let reads=0;
  b.storage.getItem=key=>{
    if(key===KEY&&++reads===2)throw Error("synthetic_second_snapshot_read_failure");
    return oldGet(key);
  };
  try{await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(payload),/synthetic_second_snapshot_read_failure/);}
  finally{b.storage.getItem=oldGet;}
  assert.equal(reads,2,"test must fail after async media preparation, not preflight");
  assert.equal(await b.core.getEncryptedMediaBlob(id),null,"second snapshot read must clean newly imported media");
  console.log("LATE_SNAPSHOT_NO_ORPHAN=true");
}
async function main(){await stageMediaCase();await tombstoneCase();await snapshotReadFailureCase();await lateSnapshotReadFailureCase();console.log("EDGE_ROLLBACK_PASS");}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
