'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const cp = require('node:child_process');
const source = fs.readFileSync(path.join(__dirname, '../android-wrapper/app/src/main/assets/android/kgg_android_sync_bootstrap.js'), 'utf8');
function boot(configured) {
  const calls = [];
  const driveStatus = {transport:configured?'saf-document':'local',driveConfigured:configured,pending:true,providerAccepted:false,lastError:'write_failed'};
  const local = {
    getStatus:()=>JSON.stringify({available:true,platform:'android',writeUsesSharedFolder:false}),
    readSyncJson:()=>{calls.push('local.read');return '{"kind":"local"}';},
    writeSyncJson:()=>{calls.push('local.write');return true;},
    listPeerSyncJson:()=>'{"kind":"local","peers":[]}',
    readFollowConfig:()=>'{"therapistId":"synthetic"}',writeFollowConfig:()=>true
  };
  const drive = {
    getStatus:()=>JSON.stringify(driveStatus),readSyncJson:()=>'{"kind":"kgg_sync_transport_error","error":"read_failed"}',
    writeSyncJson:()=>{calls.push('drive.write');return false;},
    configureOwnDriveFile:(json)=>{calls.push(JSON.parse(json));return true;},
    selectDrivePeerFiles:(json)=>{calls.push(JSON.parse(json));return true;},disconnectDrive:()=>true
  };
  const window = {KGGAndroidSync:local,KGGAndroidDriveSync:drive,dispatchEvent:()=>{}};
  vm.runInNewContext(source,{window,CustomEvent:class {constructor(name,options){this.type=name;this.detail=options.detail;}}});
  return {sync:window.KGGNativeSync,calls,driveStatus,drive,window};
}
let instance=boot(true);
instance.window.KGGAndroidSync.getStatus=()=>{throw new Error('configured Drive must not scan local mesh files');};
assert.equal(instance.sync.status().transport,'saf-document','native status must identify the actual document transport');
assert.equal(instance.sync.write({kind:'synthetic'}),false,'configured SAF failure must remain false');
assert.deepEqual(instance.calls,['drive.write'],'configured SAF failure must never fall back to local success');
assert.throws(()=>instance.sync.read(),/read_failed/,'complete SAF read failures must reach the automatic retry scheduler');
assert.throws(()=>instance.sync.listPeers(),/read_failed/,'peer listing must not turn provider error into an empty mesh');
assert.equal(instance.sync.configureOwnDriveFile({deviceId:'device-a',roomId:'room-one'}),true);
assert.equal(instance.sync.selectDrivePeerFiles({roomId:'room-one'}),true);
assert.equal(instance.sync.getFollowConfig().therapistId,'synthetic','follow config remains owned by the old bridge');
assert.deepEqual(instance.calls.slice(1),[{deviceId:'device-a',roomId:'room-one'},{roomId:'room-one'}]);
instance=boot(false);
assert.equal(instance.sync.status().transport,'local');
assert.equal(instance.sync.write({kind:'synthetic'}),true,'legacy local transport remains usable before document setup');
assert.deepEqual(instance.calls,['drive.write','local.write'],'local mode must retain a private pending outbox for later setup');
assert.equal(instance.sync.read().kind,'local');
assert.equal(instance.sync.disconnectDrive(),true);
instance=boot(false);
delete instance.window.KGGAndroidDriveSync;
assert.equal(instance.sync.status().driveConfigured,false,'old APK without the new bridge must stay usable');
assert.equal(instance.sync.write({kind:'synthetic'}),true);
console.log('Native SAF bootstrap legacy PASS: routing, negative errors, optional legacy compatibility; no device provider exercised');

// Exercise the actual bootstrap; fake only native completion and the clock.
// Regressions caught: ignoring advertised async capability, treating enqueue as
// provider success, and allowing stale/unmatched replies to settle a new job.
let documentSequence = 0;
function asyncBoot({ configured = true, generation = 7, accept = true,
  operations = ['read','write','configureOwnDriveFile','selectDrivePeerFiles','disconnectDrive'] } = {}) {
  const listeners = new Map(), timers = new Map(), requests = [], legacyCalls = [];
  let time = 0, timerSequence = 0, cancelCalls = 0;
  const status = { available:true, platform:'android', transport:configured?'saf-document':'local',
    driveConfigured:configured, pending:true, providerAccepted:false, lastError:'', configurationGeneration:generation };
  const peers = { kind:'kgg_cross_data_safe_sync_mesh', version:1, roomId:'synthetic-room',
    peers:[{origin:{deviceId:'peer-b',therapistId:'peer-b',displayName:'Synthetic peer',roomId:'synthetic-room'},exportedAt:'2026-10-23T12:00:00Z'}] };
  const event = (type, detail) => { for (const fn of [...(listeners.get(type) || [])]) fn({type, detail}); };
  const native = {
    getAsyncVersion:() => 1,
    getCapabilities:() => JSON.stringify({version:1,operations}),
    getConfigurationGeneration:() => status.configurationGeneration,
    getStatusSnapshot:() => JSON.stringify(status),
    getPeerSnapshot:() => JSON.stringify(peers),
    requestSyncJson(headerJson,payload) {
      assert(headerJson.length<=2048,'enqueue header must remain small');
      const header=JSON.parse(headerJson);assert.equal(header.payload,undefined,'payload must not be escaped inside the enqueue header');
      assert.equal(typeof payload,'string','native payload must be a separate immutable string');
      requests.push({...header,payload});return accept;
    },
    cancelSyncRequest(){cancelCalls++;return true;}
  };
  const legacy = {
    getStatus(){legacyCalls.push('status');return JSON.stringify(status);},
    readSyncJson(){legacyCalls.push('read');throw new Error('synchronous provider read was reached');},
    writeSyncJson(){legacyCalls.push('write');return false;},
    listPeerSyncJson(){legacyCalls.push('peers');throw new Error('synchronous peer scan was reached');},
    readFollowConfig:()=>'{}', writeFollowConfig:()=>true,
    configureOwnDriveFile:()=>{legacyCalls.push('configureOwnDriveFile');return true;},
    selectDrivePeerFiles:()=>{legacyCalls.push('selectDrivePeerFiles');return true;},
    disconnectDrive:()=>{legacyCalls.push('disconnectDrive');return true;}
  };
  const window = { KGGAndroidSync:legacy, KGGAndroidDriveSync:legacy, KGGAndroidSyncAsync:native,
    addEventListener(type, fn){const list=listeners.get(type)||[];list.push(fn);listeners.set(type,list);},
    removeEventListener(type, fn){listeners.set(type,(listeners.get(type)||[]).filter(value=>value!==fn));},
    dispatchEvent(value){event(value.type,value.detail);} };
  const schedule = (fn, delay=0) => { const id=++timerSequence;timers.set(id,{fn,at:time+delay});return id; };
  const cancel = id => timers.delete(id);
  const crypto = {randomUUID:()=> 'synthetic-document-' + (++documentSequence)};
  window.setTimeout=schedule;window.clearTimeout=cancel;window.crypto=crypto;
  vm.runInNewContext(source,{window,crypto,setTimeout:schedule,clearTimeout:cancel,
    CustomEvent:class {constructor(type,options){this.type=type;this.detail=options?.detail;}}});
  return {window,sync:window.KGGNativeSync,native,status,peers,requests,legacyCalls,timers,get cancelCalls(){return cancelCalls;},
    event,reply(request, overrides={}){event('kgg:native-sync-result', {kind:'kgg_sync_async_result',version:1,
      documentToken:request.documentToken,requestId:request.requestId,operation:request.operation,
      configurationGeneration:request.configurationGeneration,ok:true,result:true,...overrides});},
    async advance(ms){const target=time+ms;for(let n=0;n<100;n++){
      const next=[...timers].filter(([,value])=>value.at<=target).sort((a,b)=>a[1].at-b[1].at)[0];
      if(!next)break;timers.delete(next[0]);time=next[1].at;next[1].fn();await Promise.resolve();
    }time=target;await Promise.resolve();}
  };
}
function observe(value) {
  assert(value && typeof value.then==='function','async-capable native operation must return a completion Promise');
  const state={settled:false};
  value.then(result=>{state.settled=true;state.value=result;},error=>{state.settled=true;state.error=error;});
  return state;
}
const flush = async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
async function asyncTests() {
  const results=[];
  async function test(name, fn){try{await fn();results.push({name,ok:true});}catch(error){results.push({name,ok:false,error:error.message});}}
  await test('actual published v125 Boolean consumer cannot announce queued disconnect success',async()=>{
    const a=asyncBoot(),reading=observe(a.sync.read());
    a.window.KGGAndroidDriveSync.disconnectDrive=()=>false; // Owner is occupied by the accepted read.
    const old=cp.execFileSync('git',['show','b01f10f18f3e6accca40955dabae3fe6ddc0cfd1:kgg-update/src/runtime/app-core.html'],{cwd:path.join(__dirname,'..'),encoding:'utf8'});
    const consumer=old.match(/  function configureNativeDriveSync\(action\)\{[\s\S]*?\n  \}/)[0];
    const messages=[];
    const result=vm.runInNewContext(consumer+";configureNativeDriveSync('disconnect');",{window:a.window,nativeExerciseSyncDirty:false,
      syncPairDeviceId:()=> 'synthetic',syncPairRoomId:()=> 'synthetic-room',setNativeExerciseSyncStatus:text=>messages.push(text)});
    assert.equal(result,false,'published v125 consumer announced success while native read was pending');
    assert.equal(reading.settled,false);assert(!messages.some(text=>text.includes('Verbindung geloest')));
    assert.equal(a.requests.length,1,'old Boolean operation must not silently enqueue asynchronous completion');
  });
  await test('advertised async reads return before native completion and consume matching data',async()=>{
    const a=asyncBoot();let value;
    try{value=a.sync.read();}catch(error){assert.fail('advertised async capability was ignored: '+error.message);}
    const state=observe(value);await flush();assert.equal(state.settled,false,'enqueue must not finish a read');
    assert.equal(a.requests.length,1);assert.equal(a.requests[0].operation,'read');
    const request=a.requests[0];assert.equal(typeof request.documentToken,'string');assert(request.documentToken);
    assert(request.requestId!==undefined);assert.equal(request.configurationGeneration,7);
    a.reply(request,{result:a.peers});await flush();assert.equal(state.error,undefined);
    assert.equal(state.value.peers[0].origin.deviceId,'peer-b');assert.deepEqual(a.legacyCalls,[]);
  });
  await test('queued write resolves only after final provider result, not queue acceptance',async()=>{
    const a=asyncBoot(),state=observe(a.sync.write({kind:'synthetic',name:'Synthetische Übung'}));await flush();
    assert.equal(state.settled,false,'queue acceptance was reported as provider success');
    assert.equal(a.requests.length,1);const request=a.requests[0];assert.equal(request.operation,'write');
    assert.equal(JSON.parse(request.payload).name,'Synthetische Übung');
    a.reply(request,{result:true});await flush();assert.equal(state.value,true);assert.equal(a.timers.size,0);
    assert.deepEqual(a.legacyCalls,[]);
  });
  await test('status and peer display use snapshots while I/O is pending',async()=>{
    const a=asyncBoot();let value;try{value=a.sync.read();}catch(error){assert.fail('async read fell back to synchronous I/O: '+error.message);}
    observe(value);assert.equal(a.sync.status().pending,true);assert.equal(a.sync.status().providerAccepted,false);
    assert.equal(a.sync.listPeers().peers[0].origin.deviceId,'peer-b');assert.deepEqual(a.legacyCalls,[]);
  });
  await test('wrong document, request, operation and generation cannot settle a pending write',async()=>{
    const a=asyncBoot(),state=observe(a.sync.write({kind:'synthetic'})),request=a.requests[0];
    assert(request,'async request was not dispatched');
    for(const wrong of [{documentToken:'other-document'},{requestId:'other-request'},{operation:'read'},{configurationGeneration:6}]){
      a.reply(request,{...wrong,result:true});await flush();assert.equal(state.settled,false,'unmatched reply settled write');
    }
    a.reply(request,{result:false});await flush();assert.equal(state.value,false);
  });
  await test('duplicate completed response cannot settle the next write',async()=>{
    const a=asyncBoot(),first=observe(a.sync.write({kind:'first'})),one=a.requests[0];assert(one);
    a.reply(one,{result:true});await flush();assert.equal(first.value,true);
    const second=observe(a.sync.write({kind:'second'})),two=a.requests[1];assert(two);assert.notEqual(two.requestId,one.requestId);
    a.reply(one,{result:true});await flush();assert.equal(second.settled,false);
    a.reply(two,{result:false});await flush();assert.equal(second.value,false);
  });
  await test('queue rejection never falls back to local success or synchronous write',async()=>{
    const a=asyncBoot({accept:false}),state=observe(a.sync.write({kind:'synthetic'}));await flush();
    assert(state.error,'busy native queue must reject the Promise');assert.deepEqual(a.legacyCalls,[]);
    assert.equal(a.timers.size,0,'rejected queue request leaked its deadline');
  });
  await test('provider failure propagates and cannot trigger legacy local fallback',async()=>{
    const a=asyncBoot(),state=observe(a.sync.write({kind:'synthetic'})),request=a.requests[0];assert(request);
    a.reply(request,{ok:false,error:'write_failed'});await flush();assert(state.error);
    assert.match(state.error.message,/write_failed/);assert.deepEqual(a.legacyCalls,[]);assert.equal(a.timers.size,0);
  });
  await test('transport error payload does not masquerade as a successful peer mesh',async()=>{
    const a=asyncBoot();let result;try{result=a.sync.read();}catch(error){assert.fail('async capability ignored: '+error.message);}
    const state=observe(result),request=a.requests[0];assert(request);
    a.reply(request,{result:{kind:'kgg_sync_transport_error',error:'read_failed'}});await flush();
    assert(state.error,'transport error payload resolved successfully');assert.match(state.error.message,/read_failed/);
  });
  await test('missing native completion is bounded and late success cannot replace timeout',async()=>{
    const a=asyncBoot(),state=observe(a.sync.write({kind:'synthetic'})),request=a.requests[0];assert(request);
    await a.advance(45_000);await flush();assert(state.error,'missing completion must reject within 45 seconds');
    assert.match(state.error.message,/timeout|timed.out/i);const error=state.error;
    assert.equal(error.outcomeUnknown,true,'a timed-out accepted write is UNKNOWN, not cancelled or known failed');
    assert.equal(a.requests.length,1,'timeout must not automatically enqueue a duplicate write');
    assert.equal(a.cancelCalls,0,'UI timeout must not cancel an accepted native write');
    a.reply(request,{result:true});await flush();assert.equal(state.error,error);assert.equal(state.value,undefined);
    assert.equal(a.timers.size,0);
  });
  await test('reconfiguration invalidates old completion rather than accepting its ACK',async()=>{
    const a=asyncBoot(),state=observe(a.sync.write({kind:'old-room'})),request=a.requests[0];assert(request);
    a.status.configurationGeneration=8;
    a.event('kgg:native-sync-ready');a.reply(request,{result:true});await flush();
    assert.notEqual(state.value,true,'old configuration ACK was accepted');
    if(!state.settled)await a.advance(45_000);assert(state.error,'obsolete request must eventually reject');
    const next=observe(a.sync.write({kind:'new-room'})),newRequest=a.requests[1];assert(newRequest);
    assert.equal(newRequest.configurationGeneration,8);a.reply(newRequest,{result:true});await flush();assert.equal(next.value,true);
  });
  await test('a reloaded document cannot receive an old document completion',async()=>{
    const old=asyncBoot(),oldState=observe(old.sync.write({kind:'old'})),oldRequest=old.requests[0];assert(oldRequest);
    old.event('pagehide');await flush();const fresh=asyncBoot(),state=observe(fresh.sync.write({kind:'fresh'})),request=fresh.requests[0];assert(request);
    assert.notEqual(request.documentToken,oldRequest.documentToken,'document identity was reused after reload');
    fresh.reply(oldRequest,{result:true});await flush();assert.equal(state.settled,false);
    fresh.reply(request,{result:true});await flush();assert.equal(state.value,true);
    assert.notEqual(oldState.value,true,'pagehide accepted an old in-flight result');
    assert.equal(old.timers.size,0,'detached document retained a native deadline');
    assert.equal(oldState.error?.outcomeUnknown,true,'reload cannot cancel an already accepted provider write');
    assert.equal(old.cancelCalls,0,'UI reload must not cancel an accepted native write');
  });
  await test('async support is negotiated per operation and does not break mixed old bridges',async()=>{
    const a=asyncBoot({operations:['read']});let value;
    try{value=a.sync.read();}catch(error){assert.fail('advertised async read ignored: '+error.message);}
    const read=observe(value),request=a.requests[0];assert(request);a.reply(request,{result:a.peers});await flush();
    assert.equal(read.value.peers[0].origin.deviceId,'peer-b');
    assert.equal(a.sync.write({kind:'legacy-write'}),false,'unadvertised async write must retain its old final-result contract');
    assert.deepEqual(a.legacyCalls,['write']);
    assert.equal(a.sync.configureOwnDriveFile({deviceId:'a',roomId:'synthetic-room'}),true);
    assert.equal(a.legacyCalls.at(-1),'configureOwnDriveFile');assert.equal(a.requests.length,1);
  });
  for(const operation of ['configureOwnDriveFile','selectDrivePeerFiles','disconnectDrive'])await test(operation+' waits for its own native result and reports queue rejection',async()=>{
    const a=asyncBoot(),state=observe(a.sync[operation+'Async']({deviceId:'a',roomId:'synthetic-room'}));await flush();
    assert.equal(state.settled,false);const request=a.requests[0];assert(request);assert.equal(request.operation,operation);
    a.reply(request,{result:false});await flush();assert.equal(state.value,false);assert.deepEqual(a.legacyCalls,[]);
    const full=asyncBoot({accept:false}),rejected=observe(full.sync[operation+'Async']({deviceId:'a',roomId:'synthetic-room'}));await flush();
    assert(rejected.error,'full queue must reject '+operation);assert.deepEqual(full.legacyCalls,[]);
  });
  console.log(JSON.stringify({suite:'native-sync-bootstrap-async',ok:results.every(result=>result.ok),tests:results},null,2));
  if(results.some(result=>!result.ok))process.exitCode=1;
}
asyncTests().catch(error=>{console.error(error);process.exitCode=1;});
