#!/usr/bin/env node
"use strict";
// Lost-update gate: concurrent persisted local edit must outlive failed imported merge.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const KEY="kgg_html_app_v2_custom_exercise_bank";
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function payloadWithMedia(source,id){
  source.create("Synthetic remote source");
  const ex=source.core.bank.find(e=>e.name==="Synthetic remote source");
  assert(ex);
  const bytes=Buffer.from([137,80,78,71,13,10,26,10,3,4,5]);
  const cipher=await source.core.encryptMediaBlob(new Blob([bytes],{type:"image/png"}));
  const media={id,type:"image",mime:"image/png",width:1,height:1,
    crypto:{alg:"AES-GCM",iv:cipher.iv,key:cipher.key}};
  await source.core.putEncryptedMediaBlob({id,blob:cipher.blob,manifest:media});
  ex.media=[media];
  assert.equal(source.core.persistCustomBank(),true);
  return source.ctx.window.KGGNativeExerciseSync.buildTransport();
}
async function main(){
  const a=client("a"),b=client("b"),imageId="synthetic_concurrent_image";
  const doc=await payloadWithMedia(a,imageId);
  const open=b.ctx.window.indexedDB.open();
  const db=await new Promise(resolve=>{open.onsuccess=()=>resolve(open.result);});
  const oldTransaction=db.transaction.bind(db);
  let enteredResolve,releaseGet;
  const entered=new Promise(resolve=>{enteredResolve=resolve;});
  db.transaction=(name,mode)=>{
    const tx=oldTransaction(name,mode);
    if(mode!=="readonly")return tx;
    const originalStore=tx.objectStore.bind(tx);
    tx.objectStore=()=>{
      const store=originalStore(),oldGet=store.get.bind(store);
      store.get=key=>{
        if(key!==imageId)return oldGet(key);
        const request={};
        releaseGet=()=>{request.result=null;queueMicrotask(()=>request.onsuccess?.());};
        enteredResolve();
        return request;
      };
      return store;
    };
    return tx;
  };
  const outcome=b.ctx.window.KGGNativeExerciseSync.mergeTransport(doc).then(
    ()=>({status:"resolved"}),error=>({status:"rejected",error:String(error.message||error)})
  );
  await Promise.race([entered,sleep(1200).then(()=>{throw Error("IDB_PREPARE_GATE_TIMEOUT");})]);
  const localName="Concurrent local edit – keep this";
  b.create(localName);
  assert(b.core.bank.some(e=>e.name===localName),"local edit not in memory");
  assert(String(b.storage.getItem(KEY)||"").includes(localName),"local edit not persisted during prepare");
  let failedOnce=false;
  const originalSet=b.storage.setItem.bind(b.storage);
  b.storage.setItem=(key,value)=>{
    if(key===KEY&&!failedOnce){failedOnce=true;throw Error("synthetic_merge_write_failure");}
    return originalSet(key,value);
  };
  releaseGet();
  const result=await Promise.race([outcome,sleep(1200).then(()=>{throw Error("MERGE_GATE_TIMEOUT");})]);
  b.storage.setItem=originalSet;
  assert.equal(result.status,"rejected","test must exercise failed merge");
  assert(failedOnce,"test did not inject merge write failure");
  const afterMem=b.core.bank.some(e=>e.name===localName);
  const afterStorage=String(b.storage.getItem(KEY)||"").includes(localName);
  const reload=client("b",new Map(),b.storage);
  const afterReload=reload.core.bank.some(e=>e.name===localName);
  const output={status:(afterMem&&afterStorage&&afterReload)?"PASS":"RED_LOCAL_EDIT_LOST",
    importedRejected:true,failedOnce,inMemory:afterMem,inStorage:afterStorage,afterReload};
  console.log(JSON.stringify(output));
  assert(afterMem&&afterStorage&&afterReload,"concurrent persisted edit was erased by stale import rollback");
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
