#!/usr/bin/env node
// CLI: actual Core scheduler + preview setup + common Bootstrap; only Java/OS boundaries are doubled.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {client}=require('./kgg_drive_sync_core_smoke.js');
const ROOT=path.resolve(__dirname,'..');
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
const pendingKey='kgg_library_sync_pending_v1';
const followKey='kgg_sync_pair_follow_config_v1';

function device(stored){
  const a=client('a',new Map(),stored);
  delete a.ctx.window.KGGNativeSync;
  const state={configured:false,readFailure:false,writeFailure:false,privateWrites:[],providerWrites:[],reads:0,events:[]};
  a.ctx.CustomEvent=class {constructor(type,options){this.type=type;this.detail=options&&options.detail;}};
  a.ctx.window.dispatchEvent=event=>{state.events.push(event.type);void a.event(event.type);};
  // No legacy interface or station/job/update bridges exist in this test context.
  a.ctx.window.KGGAndroidDriveSync={
    getStatus:()=>JSON.stringify({transport:state.configured?'saf-document':'local',driveConfigured:state.configured,pending:!state.configured||state.readFailure||state.writeFailure,providerAccepted:state.configured&&!state.readFailure&&!state.writeFailure,lastError:state.configured?'':'not_configured'}),
    readSyncJson:()=>{
      state.reads++;
      return JSON.stringify(state.readFailure?{kind:'kgg_sync_transport_error',error:'read_failed'}:{kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[]});
    },
    writeSyncJson:text=>{
      const document=JSON.parse(text);state.privateWrites.push(document);
      if(!state.configured||state.writeFailure)return false;
      state.providerWrites.push(document);return true;
    },
    configureOwnDriveFile:()=>true,selectDrivePeerFiles:()=>true,
    disconnectDrive:()=>{state.configured=false;return true;}
  };
  return {a,state,inject(){
    vm.runInContext(read('android-wrapper/app/src/preview/assets/android/kgg_isolated_preview_sync_setup.js'),a.ctx);
    vm.runInContext(read('android-wrapper/app/src/main/assets/android/kgg_android_sync_bootstrap.js'),a.ctx);
  }};
}

async function main(){
  const results=[];
  async function test(name,fn){await fn();results.push(name);}
  await test('late injection activates the actual Core scheduler and keeps pre-SAF writes pending',async()=>{
    const {a,state,inject}=device();a.core.initNativeExerciseBankSync();
    a.create('Isolated late bridge creation');await a.tick(500);
    assert.equal(state.privateWrites.length,0,'native I/O before bridge injection');
    assert.equal(state.providerWrites.length,0);
    inject();await a.tick(500);
    assert(state.events.includes('kgg:native-sync-ready'),'real Bootstrap ready event missing');
    assert(state.privateWrites.some(doc=>doc.exerciseBank.some(ex=>ex.name==='Isolated late bridge creation')),'ready event did not activate real scheduler/builder');
    assert.equal(state.reads,0,'unconfigured read reached provider instead of private empty mesh');
    assert.equal(state.providerWrites.length,0);
    assert.equal(a.storage.getItem(pendingKey),'1');
    state.configured=true;
    a.ctx.window.dispatchEvent(new a.ctx.CustomEvent('kgg:native-sync-ready'));
    await a.tick(500);
    assert(state.reads>0);
    assert(state.providerWrites.some(doc=>doc.exerciseBank.some(ex=>ex.name==='Isolated late bridge creation')),'configuration did not automatically flush existing change');
    assert.equal(a.storage.getItem(pendingKey),'0');
    assert.equal(a.transport.reads,0,'old fixture transport was used');
    assert.equal(a.transport.writes,0,'old fixture transport was used');
  });
  await test('private Followconfig persists across script reload and storage failures are not acknowledged',async()=>{
    const {a,inject}=device();inject();
    const next={therapistId:'a',syncRoomId:'audit_room',followedTherapists:[{deviceId:'b',roomId:'audit_room',autoDownload:true}],displayName:'Synthetic private config'};
    assert.equal(a.ctx.window.KGGNativeSync.setFollowConfig(next),true);
    assert.equal(JSON.parse(a.storage.getItem(followKey)).displayName,next.displayName);
    // Reload only the setup with the same private WebView storage, without client() reseeding it.
    const window={};vm.runInNewContext(read('android-wrapper/app/src/preview/assets/android/kgg_isolated_preview_sync_setup.js'),{window,localStorage:a.storage});
    assert.deepEqual(JSON.parse(window.KGGAndroidSync.readFollowConfig()),next);
    assert.equal(JSON.parse(window.KGGAndroidSync.listPeerSyncJson()).roomId,'audit_room');
    assert.equal(window.KGGAndroidSync.writeSyncJson('{}'),false);
    const set=a.storage.setItem;a.storage.setItem=()=>{throw Error('private_storage_failed');};
    assert.equal(a.ctx.window.KGGNativeSync.setFollowConfig({...next,displayName:'Not persisted'}),false);
    a.storage.setItem=set;
    assert.equal(JSON.parse(a.storage.getItem(followKey)).displayName,next.displayName);
  });
  await test('configured write/read failures retain the real Core pending state and recover automatically',async()=>{
    const {a,state,inject}=device();a.core.initNativeExerciseBankSync();inject();state.configured=true;state.writeFailure=true;
    a.create('Isolated provider recovery');await a.tick(500);
    assert.equal(state.providerWrites.length,0);assert.equal(a.storage.getItem(pendingKey),'1');
    state.writeFailure=false;await a.tick(3000);
    assert(state.providerWrites.some(doc=>doc.exerciseBank.some(ex=>ex.name==='Isolated provider recovery')));
    assert.equal(a.storage.getItem(pendingKey),'0');
    state.readFailure=true;await a.event('kgg:native-sync-resume');await a.tick(500);
    assert.equal(a.storage.getItem(pendingKey),'1','provider read error became empty successful mesh');
    const before=state.providerWrites.length;state.readFailure=false;await a.tick(3000);
    assert(state.providerWrites.length>before);assert.equal(a.storage.getItem(pendingKey),'0');
  });
  await test('setup cannot replace an existing legacy bridge or start any network/station operation',async()=>{
    const setup=read('android-wrapper/app/src/preview/assets/android/kgg_isolated_preview_sync_setup.js');
    assert.throws(()=>vm.runInNewContext(setup,{window:{KGGAndroidSync:{}},localStorage:{}}),/unexpected_local_bridge/);
    const forbidden=()=>{throw Error('unexpected external operation');};
    const window={fetch:forbidden,setTimeout:forbidden,KGGDeviceTestStationNative:{beginSession:forbidden},KGGPreviewWebUpdateNative:{requestPreviewWebUpdate:forbidden}};
    const localStorage={getItem:()=>null,setItem:()=>{}};
    vm.runInNewContext(setup,{window,localStorage,fetch:forbidden,setTimeout:forbidden,XMLHttpRequest:forbidden});
    assert.equal(JSON.parse(window.KGGAndroidSync.readSyncJson()).peers.length,0);
    assert.equal(window.KGGAndroidSync.writeSyncJson('{}'),false);
    assert.equal(JSON.parse(window.KGGAndroidSync.getStatus()).writeUsesSharedFolder,false);
  });
  console.log(JSON.stringify({ok:true,tests:results,scope:'real Core scheduler / private setup / common Bootstrap; Java boundary doubled; no device or provider claim'},null,2));
}
if(require.main===module)main().catch(err=>{console.error(err);process.exitCode=1;});
module.exports={main};
