#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict");
const {encode,decode}=require("./kgg_cockpit_v2_codec_prototype");
const bank=[
 {id:"custom_1762940000000_abcd",cockpitId:"zZ",name:"Kabelzug Spezial",sets:3,loadUnit:"kg",metricUnit:"Wdh",unit:"Wdh",weightUnit:"kg",measure:"wdh",videoLabel:"Video öffnen",progressionVariants:[],media:[]},
 {id:"custom_1762940000000_efgh",cockpitId:"zY",name:"Brustpresse Spezial",sets:2,loadUnit:"kg",metricUnit:"Wdh",unit:"Wdh",weightUnit:"kg",measure:"wdh",videoLabel:"Video öffnen",progressionVariants:[],media:[]}
];
const exercises=[
 {id:"zZ",name:"Kabelzug Spezial",sets:3,side:"LR",loadUnit:"kg",metricUnit:"Wdh",previous:[["10","12"],["11","11"],["12","10"]],today:[["11","12"],["12","11"],["13","9"]],manual:[[true,false],[false,true],[false,false]],manualFields:["startLoad"],startLoad:"11",activeProgressionId:"p2",progressionGroupId:"pull",progressionVariants:[{id:"p1",groupId:"pull",name:"Leicht"},{id:"p2",groupId:"pull",name:"Schwer"}]},
 {id:"zY",name:"Brustpresse Spezial",sets:2,side:"BI",loadUnit:"kg",metricUnit:"Wdh",previous:[["20","12"],["21","10"]],today:[["22","11"],["23","9"]],manual:[[false,true],[false,false]],manualFields:[]}
];
const plan={planId:"synthetic-cockpit-123",name:"Synthetische Person",date:"2026-11-12",notes:"Nur synthetische Notiz",notesManual:true,editedAt:1794474000000,removedIds:["ZZ"],exercises};
const v2=encode(plan,bank),result=decode(v2,bank);
assert.match(v2,/^KGGTC1:z[A-Za-z0-9_-]+$/);
assert.equal(result.name,"Plan ohne Patientendaten");
assert.equal(result.exercises.length,2);
assert.deepEqual(result.exercises[0].today,exercises[0].today);
assert.deepEqual(result.exercises[0].previous,exercises[0].previous);
assert.deepEqual(result.exercises[0].manual,exercises[0].manual);
assert.deepEqual(result.exercises[0].manualFields,exercises[0].manualFields);
assert.equal(result.exercises[0].activeProgressionId,"p2");
assert.equal(result.exercises[0].progressionVariants[1].name,"Schwer");
assert.equal(result.notes,plan.notes);
assert.deepEqual(result.removedIds,plan.removedIds);
assert.throws(()=>decode(v2,[{...bank[0],name:"Geänderte Übung"},bank[1]]),/bank_identity_mismatch/);
assert.throws(()=>decode(v2,[bank[1]]),/bank_id_not_found/);
assert.throws(()=>decode(v2,[{...bank[0],cockpitId:"zQ"},bank[1]]),/cockpit_id_mismatch/);
assert.throws(()=>decode(v2,[{...bank[0]},{...bank[0]},bank[1]]),/duplicate_bank_id/);
assert.throws(()=>encode({...plan,exercises:[{...exercises[0],bankId:"invalid"}]},bank),/bank_id_not_found/);
console.log(JSON.stringify({status:"PASS",count:exercises.length,v2Chars:v2.length,checks:["fields","manual","progression","notes","missing-bank","rename","wrong-short-id","duplicate-id"]},null,2));
// Roundtrip through the ACTUAL existing KGGTC1 encoder/decoder, not a mock legacy format.
const fs=require("fs"),path=require("path"),vm=require("vm");
const source=fs.readFileSync(path.join(__dirname,"../kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const script=source.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i)[1];
const w={fflate:require("../vendor/fflate-0.8.3.js"),location:{href:"https://example.test/"},KGG_PATCHES:{},addEventListener(){},dispatchEvent(){}};
const d={readyState:"loading",body:null,title:"SYNTHETIC",addEventListener(){},getElementById(){return null}};
const ctx={window:w,document:d,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,
 btoa:v=>Buffer.from(v,"binary").toString("base64"),atob:v=>Buffer.from(v,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
vm.createContext(ctx);vm.runInContext(script,ctx);
w.KGGTherapyCockpit.registry.register("Kabelzug Spezial","zZ",{sets:3,metricUnit:"Wdh",loadUnit:"kg"});
w.KGGTherapyCockpit.registry.register("Brustpresse Spezial","zY",{sets:2,metricUnit:"Wdh",loadUnit:"kg"});
const legacy=w.KGGTherapyCockpit.encode(plan),legacyData=w.KGGTherapyCockpit.decode(legacy);
const bridgeV2=encode(legacyData,bank),bridged=decode(bridgeV2,bank);
const legacyBack=w.KGGTherapyCockpit.decode(w.KGGTherapyCockpit.encode(bridged));
assert.equal(legacyBack.exercises.length,2);
assert.equal(legacyBack.exercises[0].activeProgressionId,legacyData.exercises[0].activeProgressionId);
assert.deepEqual([...legacyBack.exercises[0].today[2]],[...legacyData.exercises[0].today[2]]);
assert.deepEqual([...legacyBack.exercises[0].previous[2]],[...legacyData.exercises[0].previous[2]]);
assert.deepEqual([...legacyBack.exercises[0].manual[1]],[...legacyData.exercises[0].manual[1]]);
assert.equal(legacyBack.notes,legacyData.notes);
console.log(JSON.stringify({status:"PASS",kind:"ACTUAL_KGGTC1_TO_NODE_V2_TO_KGGTC1",legacyChars:legacy.length,compactChars:bridgeV2.length,fieldsPreserved:true},null,2));

// Drive fallback is a simulated callback. No real Drive access or mutations in this test.
(async()=>{
  const {decodeWithBankRefresh}=require("./kgg_cockpit_v2_codec_prototype");
  let stored=[bank[1]],pulls=0,calls=[];
  const got=await decodeWithBankRefresh(v2,async()=>stored,async reason=>{
    pulls++;calls.push(reason);stored=bank.slice();return true;
  });
  assert.equal(got.exercises[0].bankId,bank[0].id);
  assert.equal(pulls,1);assert.deepEqual(calls,["cockpit_missing_exercise"]);
  const noRefresh=await decodeWithBankRefresh(v2,async()=>bank,async()=>{throw Error("unexpected_remote_lookup");});
  assert.equal(noRefresh.exercises.length,2);
  let badCalls=0;
  await assert.rejects(decodeWithBankRefresh("NOT_KGGTC2",async()=>[],async()=>{badCalls++;return true;}),/invalid_format/);
  assert.equal(badCalls,0);
  await assert.rejects(decodeWithBankRefresh(v2,async()=>[],async()=>{badCalls++;return false;}),/bank_refresh_unavailable/);
  assert.equal(badCalls,1);
  await assert.rejects(decodeWithBankRefresh(v2,async()=>[],async()=>{badCalls++;return true;}),/bank_id_not_found/);
  assert.equal(badCalls,2);
  console.log(JSON.stringify({status:"PASS",kind:"SYNTHETIC_SINGLE_EXISTING_DRIVE_SYNC_REFRESH",pulls:1,tests:["one-shot-refresh","no-refresh-on-known","no-refresh-on-invalid","unavailable-fail-closed","no-match-fail-closed"]},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});


// Confirm a versioned body can traverse the UNCHANGED native KGGTC1 link envelope.
const native=fs.readFileSync(path.join(__dirname,"../android-wrapper/app/src/main/java/de/kgg/app/MainActivity.java"),"utf8");
assert(native.includes('COCKPIT_DEEP_LINK_PREFIX = "KGGTC1:"'));
assert(native.includes('value != \'_\'')&&native.includes('value != \'-\''));
assert.match(v2,/^KGGTC1:z[A-Za-z0-9_-]+$/);
const inflated=w.fflate.inflateSync(new Uint8Array(Buffer.from(v2.slice("KGGTC1:z".length),"base64url")));
assert.equal(JSON.parse(Buffer.from(inflated).toString("utf8")).b.v,2);
assert.throws(()=>w.KGGTherapyCockpit.decode(v2),/invalid_payload/,"old HTML decoder must reject unknown inner v2 instead of guessing");
console.log(JSON.stringify({status:"PASS",kind:"NATIVE_V406_ENVELOPE_AND_FFLATE_COMPAT",nativeChangesRequiredForEnvelope:false,legacyWebDecoderCanDecodeV2:false},null,2));
