'use strict';

const assert=require('node:assert/strict');
const fs=require('node:fs');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

async function rejectsCode(promise,code){await assert.rejects(promise,error=>error&&error.code===code);}

async function main(){
  const fixtures=live.testFixtures();
  assert.equal(fixtures.trainingEvents[0].value,77);
  assert.equal(fixtures.trainingEvents[0].pain,4);
  const simulator=await live.createTestSimulator();
  await simulator.sendSyntheticPlanSnapshot(fixtures.planSnapshot);
  await simulator.sendSyntheticTrainingEvents(fixtures.trainingEvents,fixtures.planRevision);
  assert.equal((await simulator.receive('patient')).length,1);
  assert.equal((await simulator.receive('therapist'))[0].events[0].pain,4);
  await rejectsCode(simulator.sendSyntheticPlanSnapshot({...fixtures.planSnapshot,title:'Caller-Plan'}),'TEST_DATA_REQUIRED');
  await rejectsCode(simulator.sendSyntheticTrainingEvents([{...fixtures.trainingEvents[0],value:999}],fixtures.planRevision),'TEST_DATA_REQUIRED');
  const frames=JSON.stringify(simulator.relayFrames());
  assert.equal(frames.includes('Synthetische Übung'),false);
  assert.equal(frames.includes('"value"'),false);
  global.KGG_LIVE_SYNC_MODE='off';
  await rejectsCode(Promise.resolve().then(()=>live.testFixtures()),'MODE_OFF');
  global.KGG_LIVE_SYNC_MODE='test';

  const appCore=fs.readFileSync('kgg-update/src/runtime/app-core.html','utf8');
  const parserStart=appCore.indexOf("const livePair=findCode('KGGLIVEPAIR1');");
  const parserEnd=appCore.indexOf("const h3=findCode('KGGH3');",parserStart);
  assert(parserStart>=0&&parserEnd>parserStart);
  const parserBranch=appCore.slice(parserStart,parserEnd);
  assert.equal(parserBranch.includes('raw:text'),false);
  assert.equal(parserBranch.includes('pairingSecret'),false);
  const dispatchStart=appCore.indexOf("if(parsed&&parsed.type==='KGGLIVEPAIR1')");
  const dispatchEnd=appCore.indexOf("if(parsed&&(parsed.type==='KGGSYNC1'",dispatchStart);
  assert(dispatchStart>=0&&dispatchEnd>dispatchStart);
  const dispatchBranch=appCore.slice(dispatchStart,dispatchEnd);
  assert(dispatchBranch.includes('handleScannedText'));
  assert(dispatchBranch.includes('livePairingError'));
  assert.equal(dispatchBranch.includes("job.type='paper'"),false);
  const therapist=fs.readFileSync('kgg-update/src/runtime/kgg-live-sync.html','utf8');
  assert(therapist.includes("function handleScannedText(raw){if(!live.isPairingQr(raw))return false;status('Kopplungs-QR bitte in der Patienten-App scannen.','warn');return true;}"));
  assert.equal(therapist.includes("status(raw"),false);

  console.log(JSON.stringify({status:'PASS',checks:['fixed-test-fixtures','real-fixture-rejected','production-off','pairing-before-ocr','therapist-qr-termination','no-raw-pairing-parser']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
