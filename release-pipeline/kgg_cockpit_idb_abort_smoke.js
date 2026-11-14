#!/usr/bin/env node
"use strict";
// Synthetic IndexedDB transaction-abort harness against the actual KGG Core.
const assert=require("node:assert/strict");
const {client}=require("./kgg_drive_sync_core_smoke.js");
async function main(){
  const b=client("b");
  const request=b.ctx.window.indexedDB.open();
  const db=await new Promise((resolve,reject)=>{
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
  db.transaction=()=>{
    const tx={error:Error("synthetic_idb_aborted")};
    tx.objectStore=()=>({
      put(){queueMicrotask(()=>tx.onabort?.());},
      delete(){queueMicrotask(()=>tx.onabort?.());}
    });
    return tx;
  };
  const bounded=async(promise)=>Promise.race([
    Promise.resolve(promise).then(value=>({status:"resolved",value}),error=>({status:"rejected",message:String(error.message||error)})),
    new Promise(resolve=>setTimeout(()=>resolve({status:"timeout"}),80))
  ]);
  const put=await bounded(b.core.putEncryptedMediaBlob({id:"synthetic_abort_media"}));
  const del=await bounded(b.core.deleteEncryptedMediaBlob("synthetic_abort_media"));
  console.log(JSON.stringify({put,delete:del}));
  assert.equal(put.status,"rejected","aborted IDB put must settle with error, not hang");
  assert.equal(del.status,"resolved","aborted IDB delete must settle without hanging");
  assert.equal(del.value,false,"aborted IDB delete must not report success");
  // READ transaction can abort without a request.onerror; it must also settle.
  db.transaction=()=>{
    const tx={error:Error("synthetic_idb_read_aborted")};
    tx.objectStore=()=>({get(){queueMicrotask(()=>tx.onabort?.());return {};}});
    return tx;
  };
  const read=await bounded(b.core.getEncryptedMediaBlob("synthetic_abort_media"));
  console.log("READ_ABORT="+JSON.stringify(read));
  assert.equal(read.status,"rejected","aborted IDB read must reject instead of hanging");
  console.log("IDB_ABORT_GATE_PASS");
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
