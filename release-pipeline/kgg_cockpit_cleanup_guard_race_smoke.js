#!/usr/bin/env node
"use strict";
// Real app-core client: failed incoming bank write, paused IDB media cleanup,
// confirmed local edit during the pause, then the ordinary sync queue.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const BANK_KEY="kgg_html_app_v2_custom_exercise_bank";
const PENDING_KEY="kgg_library_sync_pending_v1";
const timeout=(promise,label)=>Promise.race([
  promise,new Promise((_,reject)=>setTimeout(()=>reject(Error(label+"_TIMEOUT")),1500))
]);
async function mediaTransport(source,mediaId){
  source.create("Synthetic remote cleanup media");
  const ex=source.core.bank.find(item=>item.name==="Synthetic remote cleanup media");
  assert(ex,"remote exercise must be created through the real core");
  // Real 1x1 PNG (valid IHDR, compressed pixel row and CRCs), synthetic only.
  const bytes=Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC","base64");
  const encrypted=await source.core.encryptMediaBlob(new Blob([bytes],{type:"image/png"}));
  const manifest={id:mediaId,type:"image",mime:"image/png",width:1,height:1,
    encrypted:true,storage:"indexeddb-local",crypto:{alg:"AES-GCM",iv:encrypted.iv,key:encrypted.key}};
  await source.core.putEncryptedMediaBlob({id:mediaId,blob:encrypted.blob,manifest});
  ex.media=[manifest];
  assert.equal(source.core.persistCustomBank(),true);
  const doc=await source.ctx.window.KGGNativeExerciseSync.buildTransport();
  assert.equal(doc.mediaBlobs.length,1,"source must publish valid encrypted media");
  return doc;
}
async function main(){
  const mediaId="synthetic_b7_cleanup_media",localName="Synthetic local during cleanup";
  const a=client("a"),b=client("b");
  const doc=await mediaTransport(a,mediaId);
  b.core.initNativeExerciseBankSync();
  await b.tick();
  assert.equal(b.core.dirty,false,"baseline sync must be clean");
  assert.equal(b.storage.getItem(PENDING_KEY),"0","baseline must not be queued");
  const writesBefore=b.transport.writes;
  const open=b.ctx.window.indexedDB.open();
  const db=await new Promise(resolve=>{open.onsuccess=()=>resolve(open.result);});
  const originalTransaction=db.transaction.bind(db);
  let signalDelete,resumeDelete,deleteReached=false;
  const enteredDelete=new Promise(resolve=>{signalDelete=resolve;});
  db.transaction=(...args)=>{
    const tx=originalTransaction(...args),originalStore=tx.objectStore.bind(tx);
    tx.objectStore=(...storeArgs)=>{
      const store=originalStore(...storeArgs),originalDelete=store.delete.bind(store);
      store.delete=id=>{
        if(id===mediaId&&!deleteReached){
          deleteReached=true;resumeDelete=()=>originalDelete(id);signalDelete();return;
        }
        return originalDelete(id);
      };
      return store;
    };
    return tx;
  };
  let bankWriteFailed=false;
  const originalSet=b.storage.setItem.bind(b.storage);
  b.storage.setItem=(key,value)=>{
    if(key===BANK_KEY&&!bankWriteFailed){
      bankWriteFailed=true;throw Error("synthetic_b7_bank_write_failure");
    }
    return originalSet(key,value);
  };
  const importOutcome=b.ctx.window.KGGNativeExerciseSync.mergeTransport(doc).then(
    ()=>({status:"resolved"}),error=>({status:"rejected",error:String(error.message||error)})
  );
  await timeout(enteredDelete,"IDB_CLEANUP_DELETE_GATE");
  b.storage.setItem=originalSet;
  assert(bankWriteFailed,"one-shot merge bank failure was not injected");
  assert.equal(b.core.dirty,false,"import should not dirty a clean baseline");
  // The failed bank write may itself set pending=1 via the status display.
  // Track it separately; revision, dirty and the actual queue prove the local edit.
  const pendingBeforeCreate=b.storage.getItem(PENDING_KEY);
  b.create(localName); // actual confirmExerciseInput -> persistCustomBank
  const local=b.core.bank.find(item=>item.name===localName);
  const saved=JSON.parse(b.storage.getItem(BANK_KEY)||"[]").find(item=>item.name===localName);
  const during={inMemory:!!local,inStorage:!!saved,
    revision:local&&local.syncRevision,dirty:b.core.dirty,
    pending:b.storage.getItem(PENDING_KEY),writes:b.transport.writes};
  resumeDelete();
  const outcome=await timeout(importOutcome,"MERGE_AFTER_CLEANUP");
  assert.equal(outcome.status,"rejected","test must exercise a failed incoming merge");
  assert.equal(await b.core.getEncryptedMediaBlob(mediaId),null,"failed import media must be cleaned");
  const reload=client("b",b.files,b.storage,b.blobStore);
  const reloaded=reload.core.bank.find(item=>item.name===localName);
  await b.tick(500);
  const uploaded=b.files.get("b")?.exerciseBank.find(item=>item.name===localName);
  const after={inMemory:b.core.bank.some(item=>item.name===localName),
    inStorage:!!JSON.parse(b.storage.getItem(BANK_KEY)||"[]").find(item=>item.name===localName),
    afterReload:!!reloaded,queuedToProvider:!!uploaded,
    writes:b.transport.writes-writesBefore};
  console.log(JSON.stringify({status:"B7_CLEANUP_GUARD_RACE",injectedOnce:bankWriteFailed,
    deletePaused:deleteReached,pendingBeforeCreate,during,after,importRejected:true}));
  assert(during.inMemory&&during.inStorage,"local edit must persist while IDB delete is paused");
  assert(during.revision&&during.revision.counter>0&&during.revision.deviceId==="b",
    "RED: confirmed local edit was not given a new sync revision during cleanup");
  assert.equal(during.dirty,true,"RED: local edit did not set sync dirty");
  assert.equal(during.pending,"1","RED: local edit did not set durable pending marker");
  assert.equal(during.writes,writesBefore,"provider must not write before queued callback");
  assert(after.inMemory&&after.inStorage&&after.afterReload,"local edit was lost after cleanup");
  assert(after.queuedToProvider&&after.writes>=1,"queued local edit was not published by retry tick");
  assert.deepEqual(JSON.parse(JSON.stringify(uploaded.syncRevision)),
    JSON.parse(JSON.stringify(during.revision)),"published revision differs from confirmed local revision");
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
