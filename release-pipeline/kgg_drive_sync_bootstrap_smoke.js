'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
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
console.log('Native SAF bootstrap PASS: routing, negative errors, optional legacy compatibility; no device provider exercised');
