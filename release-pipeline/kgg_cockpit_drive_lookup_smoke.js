#!/usr/bin/env node
"use strict";
// Real editable KGG Core sync/merge source. Only OS/SAF provider is simulated.
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const html=fs.readFileSync(path.join(__dirname,"../kgg-update/src/runtime/app-core.html"),"utf8");
const source=html.match(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/i)?.[1];
assert(source?.includes("KGG_LOGIC_SMOKE_BOOT_BOUNDARY"),"editable core must contain test boot boundary");
const mainScript=source.slice(0,source.indexOf("  /* KGG_LOGIC_SMOKE_BOOT_BOUNDARY */"));
function device(name,files){return client(name,files,null,new Map(),mainScript);}
async function main(){
  const files=new Map(),sender=device("b",files),receiver=device("a",files);
  const exercise={id:"custom_1762940000000_a1b2",name:"Synthetische Bankübung",sets:3,
    unit:"Wdh",weightUnit:"kg",loadUnit:"kg",metricUnit:"Wdh",media:[],custom:true};
  sender.core.bank.push(exercise);
  files.set("b",sender.core.buildNativeExerciseBankSyncDocument());
  const lookup=receiver.ctx.window.KGGNativeExerciseSync.refreshForCockpit;
  assert.equal(typeof lookup,"function","reuse native sync via isolated Cockpit read");
  const original=receiver.ctx.window.KGGNativeSync.status;
  receiver.ctx.window.KGGNativeSync.status=()=>({transport:"local",driveConfigured:false});
  assert.equal(await lookup(),false,"do not invoke a local-only provider as Drive");
  assert.equal(receiver.transport.reads,0);assert.equal(receiver.transport.writes,0);
  receiver.ctx.window.KGGNativeSync.status=original;
  assert.equal(await lookup(),true);
  const shared=receiver.ctx.window.KGGSharedBank.exportPayload().exercises;
  assert.equal(shared.filter(x=>x.id===exercise.id).length,1,"stable bank ID must be retained");
  assert.equal(receiver.transport.reads,1);
  assert.equal(receiver.transport.writes,0,"lookup must not write to remote Drive");
  assert.equal(await lookup(),true,"repeat read remains idempotent");
  assert.equal(receiver.ctx.window.KGGSharedBank.exportPayload().exercises.filter(x=>x.id===exercise.id).length,1);
  assert.equal(receiver.transport.writes,0);
  receiver.transport.readFailure=true;
  const prior=JSON.stringify(receiver.ctx.window.KGGSharedBank.exportPayload().exercises);
  assert.equal(await lookup(),false,"provider failure must be explicit");
  assert.equal(JSON.stringify(receiver.ctx.window.KGGSharedBank.exportPayload().exercises),prior);
  assert.equal(receiver.transport.writes,0);
  receiver.transport.readFailure=false;
  receiver.core.bank.push({id:"local_synthetic_unsynced",name:"Synthetische lokale Übung",custom:true,sets:3});
  receiver.core.persistCustomBank();
  receiver.eval("nativeExerciseSyncDirty=true");
  assert.equal(await lookup(),true);
  assert.equal(receiver.core.dirty,true);
  assert.equal(receiver.transport.writes,0);
  const blocked=device("c",files);
  blocked.storage.setItem("kgg_sync_pair_follow_config_v1",JSON.stringify({therapistId:"c",syncRoomId:"audit_room",followedTherapists:[]}));
  assert.equal(await blocked.ctx.window.KGGNativeExerciseSync.refreshForCockpit(),true);
  assert.equal(blocked.ctx.window.KGGSharedBank.exportPayload().exercises.some(x=>x.id===exercise.id),false,"unfollowed peers must not import");
  assert.equal(blocked.transport.writes,0);
  // A normal push must never enter the provider while Cockpit's async read is still in flight.
  const raceFiles=new Map(),raceSender=device("b",raceFiles),raceReceiver=device("a",raceFiles);
  raceSender.core.bank.push({...exercise,id:"custom_synthetic_race"});
  raceFiles.set("b",raceSender.core.buildNativeExerciseBankSyncDocument());
  const readOriginal=raceReceiver.ctx.window.KGGNativeSync.read;
  let releaseRead;
  raceReceiver.ctx.window.KGGNativeSync.read=async()=>{await new Promise(resolve=>{releaseRead=resolve;});return readOriginal();};
  const pendingLookup=raceReceiver.ctx.window.KGGNativeExerciseSync.refreshForCockpit();
  for(let i=0;i<12&&!releaseRead;i++)await Promise.resolve();
  assert.equal(typeof releaseRead,"function","lookup must enter the async SAF read");
  const queuedPush=raceReceiver.ctx.window.KGGNativeExerciseSync.push("cockpit-concurrent-write");
  for(let i=0;i<12;i++)await Promise.resolve();
  assert.equal(raceReceiver.transport.writes,0,"ordinary sync must not write during Cockpit lookup");
  releaseRead();assert.equal(await pendingLookup,true);
  await queuedPush;
  assert.equal(raceReceiver.transport.writes,1,"normal pending push must finish after lookup");
  // Rejected SAF read must release the gate: the waiting push still completes.
  const failedReceiver=device("a",raceFiles);
  const readAfterFailure=failedReceiver.ctx.window.KGGNativeSync.read;
  let rejectRead;
  failedReceiver.ctx.window.KGGNativeSync.read=()=>new Promise((resolve,reject)=>{rejectRead=reject;});
  const failedLookup=failedReceiver.ctx.window.KGGNativeExerciseSync.refreshForCockpit();
  for(let i=0;i<12&&!rejectRead;i++)await Promise.resolve();
  assert.equal(typeof rejectRead,"function","failed-read test must enter the held SAF read");
  const pendingAfterFailure=failedReceiver.ctx.window.KGGNativeExerciseSync.push("cockpit-read-failure");
  for(let i=0;i<12;i++)await Promise.resolve();
  assert.equal(failedReceiver.transport.writes,0,"push must wait even when SAF read will fail");
  rejectRead(new Error("synthetic SAF read failure"));
  assert.equal(await failedLookup,false,"read failure must be reported");
  assert.equal(await pendingAfterFailure,true,"waiting push must complete after read failure");
  assert.equal(failedReceiver.transport.writes,1,"pending push must not be lost after failure");
  failedReceiver.ctx.window.KGGNativeSync.read=readAfterFailure;
  assert.equal(await failedReceiver.ctx.window.KGGNativeExerciseSync.refreshForCockpit(),true,"read gate must be released for a later lookup");
  console.log(JSON.stringify({status:"PASS",checks:["SAF_only","stable_id","remote_no_write","idempotence","provider_error","pending_write_not_flushed","unfollowed_peer_ignored","no_async_write_collision","failed_read_releases_pending_push"]}));
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
