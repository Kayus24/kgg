#!/usr/bin/env node
"use strict";
// Real v082 browser script in two independent synthetic VM devices; no IO to provider.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const fflate=require("../vendor/fflate-0.8.3.js"),proto=require("./kgg_cockpit_v2_codec_prototype.js");
const html=fs.readFileSync(path.join(__dirname,"../kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const script=html.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i)?.[1];
assert(script,"real v082 script present");
const bank=[
 {id:"custom_1762940000000_abcd",cockpitId:"zZ",name:"Kabelzug Spezial",sets:3,metricUnit:"Wdh",loadUnit:"kg",unit:"Wdh",weightUnit:"kg",measure:"wdh",media:[],progressionVariants:[]},
 {id:"custom_1762940000000_efgh",cockpitId:"zY",name:"Brustpresse Spezial",sets:2,metricUnit:"Wdh",loadUnit:"kg",unit:"Wdh",weightUnit:"kg",measure:"wdh",media:[],progressionVariants:[]}
];
const clone=x=>JSON.parse(JSON.stringify(x));
function device(rows,registerBankNames=true){
 const w={fflate,location:{href:"https://example.test/"},KGG_PATCHES:{},addEventListener(){},dispatchEvent(){}};
 const d={readyState:"loading",body:null,title:"SYNTHETIC",addEventListener(){},getElementById(){return null}};
 const ctx={window:w,document:d,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,
   btoa:v=>Buffer.from(v,"binary").toString("base64"),atob:v=>Buffer.from(v,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
 vm.createContext(ctx);vm.runInContext(script,ctx,{filename:"v082-therapy-cockpit.html"});
 const api=w.KGGTherapyCockpit;
 if(registerBankNames)(rows||[]).forEach(b=>{if(!api.registry.lookup(b.name))api.registry.register(b.name,b.cockpitId,{sets:b.sets,metricUnit:b.metricUnit,loadUnit:b.loadUnit});});
 if(rows)w.KGGSharedBank={exportPayload(){return {exercises:clone(rows)};}};
 return api;
}
const a=device(bank),b=device(bank);
assert.equal(typeof a.encodeV2,"function","RED: real browser API must expose encodeV2");
assert.equal(typeof b.decodeV2,"function","RED: real browser API must expose decodeV2");
const plan={planId:"synthetic-123",name:"Private synthetic name NOT IN V2",date:"2026-11-12",
 notes:"synthetic only",notesManual:true,editedAt:1794474000000,removedIds:["AA"],
 exercises:[
 {id:"zZ",name:"Kabelzug Spezial",bankId:bank[0].id,sets:3,side:"LR",loadUnit:"kg",metricUnit:"Wdh",
 previous:[["10","12"],["11","11"],["12","10"]],today:[["11","12"],["12","11"],["13","9"]],
 manual:[[true,false],[false,true],[false,false]],manualFields:["startLoad"],startLoad:"11",
 videoUrl:"https://example.test/demo",videoLabel:"Demo",media:[{id:"synthetic-media-1",type:"image",downloadUrl:"https://example.test/media"}],progressionGroupId:"pull",activeProgressionId:"p2",
 progressionVariants:[{id:"p1",groupId:"pull",name:"Leicht"},{id:"p2",groupId:"pull",name:"Schwer"}]},
 {id:"zY",name:"Brustpresse Spezial",bankId:bank[1].id,sets:2,side:"BI",loadUnit:"kg",metricUnit:"Wdh",
 previous:[["20","12"],["21","10"]],today:[["22","11"],["23","9"]],
 manual:[[false,true],[false,false]],manualFields:[]}
 ]};
const legacy=a.encode(plan),old=b.decode(legacy);
assert.equal(old.version,1);assert.equal(old.name,plan.name);
const compact=a.encodeV2(plan);
assert.equal(a.isV2(compact),true);assert.equal(a.isV2(legacy),false);
assert.match(compact,/^KGGTC1:z[A-Za-z0-9_-]+$/);assert(compact.length<=30000);
const envelope=JSON.parse(Buffer.from(fflate.inflateSync(Buffer.from(compact.slice(8),"base64url"))).toString("utf8"));
assert.equal(envelope.b.v,2);assert.equal(Object.prototype.hasOwnProperty.call(envelope.b,"n"),false);
assert.equal(JSON.stringify(envelope).includes(plan.name),false,"V2 must not contain patient name");
const result=b.decodeV2(compact);
assert.equal(result.name,"Plan ohne Patientendaten");assert.equal(result.planId,plan.planId);
assert.equal(result.notes,plan.notes);assert.equal(result.notesManual,true);
assert.deepEqual([...result.removedIds],plan.removedIds);
assert.equal(result.exercises[0].bankId,bank[0].id);
assert.equal(result.exercises[0].side,"LR");
for(const field of ["previous","today","manual","manualFields"]){
 assert.deepEqual(JSON.parse(JSON.stringify(result.exercises[0][field])),plan.exercises[0][field],field);
}
assert.equal(result.exercises[0].progressionVariants[1].name,"Schwer");
assert.equal(result.exercises[0].activeProgressionId,"p2");
assert.equal(result.exercises[0].videoUrl,"https://example.test/demo");
assert.equal(result.exercises[0].media[0].id,"synthetic-media-1");
assert.equal(result.exercises[0].media[0].downloadUrl,"https://example.test/media");
assert.deepEqual(JSON.parse(JSON.stringify(result.exercises[1].today)),plan.exercises[1].today);
assert.deepEqual(JSON.parse(JSON.stringify(proto.decode(compact,bank).exercises[0].manual)),plan.exercises[0].manual);
assert.equal(b.decodeV2(proto.encode(plan,bank)).exercises[0].bankId,bank[0].id);
const dynamicBank=[{id:"custom_stable_dynamic_1",name:"Synthetische freie Übung",sets:2,loadUnit:"kg",metricUnit:"Wdh"}];
const dynamicSender=device(dynamicBank,false),dynamicId=dynamicSender.registry.derive(dynamicBank[0].name).id;
const dynamicPlan={planId:"synthetic-dynamic",date:"2026-11-12",exercises:[{id:dynamicId,name:dynamicBank[0].name,sets:2,side:"BI",previous:[["1","2"],["3","4"]],today:[["2","3"],["4","5"]]}]};
const dynamicCode=dynamicSender.encodeV2(dynamicPlan),dynamicReceiver=device(dynamicBank,false);
assert.equal(dynamicReceiver.decodeV2(dynamicCode).exercises[0].bankId,dynamicBank[0].id,"new device must derive verified cockpit mapping from own bank");
assert.throws(()=>b.decode(compact),/invalid_payload/,"old v1 decoder does not silently treat v2 as v1");
assert.throws(()=>b.decodeV2(legacy),/invalid_format|invalid_payload/);
const invalidBanks=[
 [bank[1]],[{...bank[0],name:"Renamed other exercise"},bank[1]],
 [{...bank[0],cockpitId:"zQ"},bank[1]],[bank[0],{...bank[0]},bank[1]],
 [{...bank[0],id:"other_stable_id"},bank[1]]
];
invalidBanks.forEach((rows,i)=>{
 const target=device(rows);
 assert.throws(()=>target.decodeV2(compact),/bank_id_not_found|bank_identity_mismatch|cockpit_id_mismatch|duplicate_bank_id|exercise_id_conflict|exercise_id_collision/,"identity negative "+i);
});
assert.throws(()=>a.encodeV2({...plan,exercises:[{...plan.exercises[0],bankId:"unknown"}]}),/bank_id_not_found/);
const missing=device([]);assert.throws(()=>missing.decodeV2(compact),/bank_id_not_found/);
assert.throws(()=>device(null).decodeV2(compact),/bank_provider_missing/);
assert.throws(()=>device([{...bank[0],id:""},bank[1]]).decodeV2(compact),/invalid_bank_entry/);
const nameMismatch=device(bank);
assert.throws(()=>nameMismatch.encodeV2({...plan,exercises:[{...plan.exercises[0],name:"Unknown"}]}),/bank_identity_mismatch/);
const tampered=clone(envelope);tampered.b.e[0][1]="corrupt";
const tamperedCode="KGGTC1:z"+Buffer.from(fflate.deflateSync(Buffer.from(JSON.stringify(tampered)))).toString("base64url");
assert.throws(()=>b.decodeV2(tamperedCode),/integrity_failed/);
const altered=clone(envelope);altered.b.e[0][0]=bank[1].id;
let hash=2166136261;
for(const byte of Buffer.from(JSON.stringify(altered.b),"utf8")){hash^=byte;hash=Math.imul(hash,16777619)>>>0;}
altered.h=(hash>>>0).toString(36);
const alteredCode="KGGTC1:z"+Buffer.from(fflate.deflateSync(Buffer.from(JSON.stringify(altered)))).toString("base64url");
assert.throws(()=>b.decodeV2(alteredCode),/bank_identity_mismatch|duplicate_exercise/,"recomputed checksum must not bypass identity");
const nameInjected=clone(envelope);nameInjected.b.n="synthetic forbidden patient name";
let nameHash=2166136261;
for(const byte of Buffer.from(JSON.stringify(nameInjected.b),"utf8")){nameHash^=byte;nameHash=Math.imul(nameHash,16777619)>>>0;}
nameInjected.h=(nameHash>>>0).toString(36);
const injectedCode="KGGTC1:z"+Buffer.from(fflate.deflateSync(Buffer.from(JSON.stringify(nameInjected)))).toString("base64url");
assert.throws(()=>b.decodeV2(injectedCode),/invalid_payload/,"unknown patient name field must be rejected even with valid checksum");
assert.throws(()=>b.decodeV2("KGGTC1:z%%%"),/invalid_base64|invalid_payload|invalid_format/);
assert.throws(()=>b.decodeV2("KGGTC1:z"+Buffer.from(fflate.deflateSync(Buffer.alloc(100001,65))).toString("base64url")) ,/invalid_payload/);
assert.throws(()=>b.decodeV2("KGGTC1:z"+"a".repeat(30001)),/invalid_format/);
assert.throws(()=>a.encodeV2({...plan,exercises:[{...plan.exercises[0],today:[["hack","1"],["1","1"],["1","1"]]}]}),/value_out_of_range/);
assert.equal(a.encode(plan).startsWith("KGGTC1:"),true,"v1 remains default");
console.log(JSON.stringify({status:"B10_BROWSER_V2_PASS",tests:["2_device_roundtrip","legacy_v1","bank_id_name_short_id","all_cockpit_fields","tamper","size","native_envelope","node_interop","no_default_switch"],chars:compact.length}));
