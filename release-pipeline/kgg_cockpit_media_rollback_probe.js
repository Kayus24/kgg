#!/usr/bin/env node
"use strict";
// RED diagnostic: actual KGG Core import with synthetic source and IndexedDB double.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
async function main(){
  const a=client("a"),b=client("b");
  a.create("Synthetic orphan media probe");
  const exercise=a.core.bank.find(x=>x.name==="Synthetic orphan media probe");
  assert(exercise);
  const id="kgg_synthetic_orphan_media_probe";
  const plain=Buffer.from([137,80,78,71,13,10,26,10,1,2,3]);
  const encrypted=await a.core.encryptMediaBlob(new Blob([plain],{type:"image/png"}));
  const media={id,type:"image",mime:"image/png",width:1,height:1,
    encrypted:true,storage:"indexeddb-local",
    crypto:{alg:"AES-GCM",iv:encrypted.iv,key:encrypted.key}};
  await a.core.putEncryptedMediaBlob({id,blob:encrypted.blob,manifest:media});
  exercise.media=[media];
  a.core.persistCustomBank();
  const payload=await a.ctx.window.KGGNativeExerciseSync.buildTransport();
  assert.equal(payload.mediaBlobs.length,1);
  const before=JSON.stringify(b.core.bank);
  const oldSet=b.storage.setItem.bind(b.storage);
  let injectFailure=true;
  b.storage.setItem=(key,value)=>{
    if(injectFailure&&key==="kgg_html_app_v2_custom_exercise_bank")throw Error("synthetic_bank_persist_failure");
    return oldSet(key,value);
  };
  await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(payload),/Bibliothek konnte nicht gespeichert|synthetic_bank_persist_failure/);
  injectFailure=false;
  assert.equal(JSON.stringify(b.core.bank),before,"bank must be rolled back");
  const record=await b.core.getEncryptedMediaBlob(id);
  console.log(JSON.stringify({status:record?"RED_ORPHAN_MEDIA_AFTER_FAILED_MERGE":"GREEN_NO_ORPHAN",
    bankUntouched:true,mediaBlobPersists:!!record,mediaIdIsSynthetic:true}));
  if(record)process.exitCode=2; // The negative gate SHOULD fail until safe rollback exists.
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
