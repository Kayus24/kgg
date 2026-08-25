'use strict';

const assert=require('node:assert/strict');
global.KGG_LIVE_SYNC_MODE='test';
global.KGG_LIVE_TEST_SIMULATOR=true;
const live=require('./kgg-live-sync-client.js');

async function rejects(promise,code){
  await assert.rejects(promise,error=>!code||error.code===code);
}

async function main(){
  const material=live.createPairingMaterial();
  const parsed=live.parsePairingQr(material.qr);
  assert.deepEqual(parsed,material.payload);
  assert.deepEqual(Object.keys(parsed).sort(),['createdAt','keyVersion','pairingId','pairingSecret','v']);
  assert.equal(live.isPairingQr('KGGH2:synthetic-old-format'),false);
  assert.equal(typeof global.KGGLiveSyncTest.createSimulator,'function');
  assert.equal((await global.KGGLiveSyncTest.hash({synthetic:true})).length,64);

  const store=live.makeKeyStore({allowMemory:true});
  const stored=await live.importPairingQr(material.qr,store,{planRef:'synthetic-plan'});
  assert.equal(stored.storage,'memory');
  assert.equal((await store.get(stored.pairingId)).key.extractable,false);
  await rejects(Promise.resolve().then(()=>live.parsePairingQr('KGGLIVEPAIR1:eyJ2IjoxfQ')),'PAIRING_FIELDS');

  const wrongPeerStore=live.makeKeyStore({allowMemory:true});
  const wrongPeerMaterial=live.createPairingMaterial();
  await live.importPairingQr(wrongPeerMaterial.qr,wrongPeerStore);
  const signedKey=live.canonicalBytes({v:1,sessionId:'synthetic-session',role:'patient',publicKey:'synthetic-public-key'});
  const peerSignature=await store.sign(stored.pairingId,signedKey);
  const wrongPeerSignature=await wrongPeerStore.sign(wrongPeerMaterial.payload.pairingId,signedKey);
  assert.notDeepEqual(Array.from(peerSignature),Array.from(wrongPeerSignature));

  const simulator=await live.createTestSimulator();
  assert.match(simulator.expiresAt,/^\d{4}-\d\d-\d\dT/);
  const fixtures=live.testFixtures();
  const plan=fixtures.planSnapshot;
  await simulator.sendSyntheticPlanSnapshot(plan);
  const changedPlan={...plan,planRevision:'2'.repeat(64),exercises:[
    {...plan.exercises[1],order:0,archived:true},
    {id:'exercise-stable-c',order:1,name:'Synthetische Übung C',sets:1,side:'BI',unit:'kg',measure:'Wdh',archived:false}
  ]};
  assert.equal(live.validatePlanSnapshot(changedPlan),true);
  await rejects(Promise.resolve().then(()=>live.validatePlanSnapshot({...changedPlan,exercises:[{...changedPlan.exercises[0],order:1},{...changedPlan.exercises[1],order:1}]})),'PLAN_INVALID');
  const patientMessages=await simulator.receive('patient');
  assert.equal(patientMessages.length,1);
  assert.equal(patientMessages[0].exercises[0].id,'exercise-stable-a');
  await simulator.sendSyntheticTrainingEvents(fixtures.trainingEvents,plan.planRevision);
  const therapistMessages=await simulator.receive('therapist');
  assert.equal(therapistMessages[0].events[0].value,77);
  assert.equal(therapistMessages[0].events[0].pain,4);
  const frame=simulator.relayFrames()[0];
  assert.equal(JSON.stringify(frame).includes('Synthetische'),false);
  assert.equal(JSON.stringify(frame).includes('"value"'),false);
  assert.equal(await simulator.tamper(frame,{sequence:2}),true);
  assert.equal(await simulator.tamper(frame,{ciphertext:frame.ciphertext.slice(0,-1)+'A'}),true);

  const aesKey=await global.crypto.subtle.importKey('raw',live.randomBytes(32),{name:'AES-GCM'},false,['encrypt','decrypt']);
  const wrongAesKey=await global.crypto.subtle.importKey('raw',live.randomBytes(32),{name:'AES-GCM'},false,['encrypt','decrypt']);
  const encrypted=await live.encryptEnvelope(aesKey,'synthetic-session','therapist',1,{type:'receipt',synthetic:true,cursor:1,appliedIds:[]});
  await rejects(live.decryptEnvelope(wrongAesKey,'synthetic-session','therapist',encrypted,new live.ReplayGuard()),'AUTH_FAILED');

  const guard=new live.ReplayGuard();
  guard.check(frame);guard.commit(frame,'therapist|1|'+frame.messageId+'|'+frame.nonce);
  await rejects(Promise.resolve().then(()=>guard.check(frame)),'REPLAY');
  await rejects(Promise.resolve().then(()=>guard.check({...frame,sequence:2,messageId:material.payload.pairingId})),'REPLAY');
  const queue=new live.CiphertextQueue({allowMemory:true});
  await queue.put('session-synthetic',frame,Date.now()+10000);
  assert.equal((await queue.list('session-synthetic')).length,1);
  await queue.clearExpired(Date.now()+20000);
  assert.equal((await queue.list('session-synthetic')).length,0);

  const production=live.config({mode:'production',productionApproved:true});
  assert.equal(production.mode,'off');
  const approvedProduction=live.config({mode:'production',productionApproved:true,endpoint:'https://127.0.0.1'});
  assert.equal(approvedProduction.mode,'production');
  assert.doesNotThrow(()=>live.makeHttpRelay(approvedProduction));
  assert.equal(live.config({mode:'off'}).mode,'off');
  global.KGG_LIVE_SYNC_MODE='off';
  await rejects(live.createTestSimulator(),'MODE_OFF');

  console.log(JSON.stringify({status:'PASS',checks:['pairing','test-api','non-exportable-key','crypto-roundtrip','aad-tamper','replay','plan-reorder-archive','ciphertext-queue','production-lock','no-plaintext']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
