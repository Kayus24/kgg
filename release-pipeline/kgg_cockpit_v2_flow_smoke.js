#!/usr/bin/env node
"use strict";
// Actual v082 import/export flow in isolated synthetic browser contexts.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const fflate=require("../vendor/fflate-0.8.3.js");
const source=fs.readFileSync(path.join(__dirname,"../kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const script=source.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i)?.[1];
assert(script,"missing real v082 cockpit script");
const clone=x=>JSON.parse(JSON.stringify(x));
const BANK=[
 {id:"custom_1762940000000_abcd",cockpitId:"zZ",name:"Kabelzug Spezial",sets:3,loadUnit:"kg",metricUnit:"Wdh",unit:"Wdh",weightUnit:"kg",media:[],progressionVariants:[]},
 {id:"custom_1762940000000_efgh",cockpitId:"zY",name:"Brustpresse Spezial",sets:2,loadUnit:"kg",metricUnit:"Wdh",unit:"Wdh",weightUnit:"kg",media:[],progressionVariants:[]}
];
function device(initialBank){
 let catalog=clone(initialBank),refreshes=0,refreshImpl=async()=>false,writes=0;
 const persisted=new Map(),w={fflate,location:{href:"https://example.test/"},KGG_PATCHES:{},addEventListener(){},dispatchEvent(){}};
 w.localStorage={getItem:k=>persisted.has(k)?persisted.get(k):null,setItem(k,v){writes++;persisted.set(k,String(v));},removeItem:k=>persisted.delete(k)};
 w.KGGSharedBank={exportPayload(){return {exercises:clone(catalog)};}};
 w.KGGNativeExerciseSync={refreshForCockpit:async reason=>{refreshes++;return refreshImpl(reason);}};
 const d={readyState:"loading",body:null,title:"SYNTHETIC",addEventListener(){},getElementById(){return null}};
 const ctx={window:w,document:d,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,
  btoa:v=>Buffer.from(v,"binary").toString("base64"),atob:v=>Buffer.from(v,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
 vm.createContext(ctx);vm.runInContext(script,ctx);
 const api=w.KGGTherapyCockpit;
 catalog.forEach(ex=>{if(!api.registry.lookup(ex.name))api.registry.register(ex.name,ex.cockpitId,{sets:ex.sets,loadUnit:ex.loadUnit,metricUnit:ex.metricUnit});});
 return {api,get refreshes(){return refreshes;},get writes(){return writes;},persisted,setBank:rows=>{catalog=clone(rows);},
  onRefresh:fn=>{refreshImpl=fn;}};
}
const plan={planId:"synthetic-flow",name:"Synthetic user name",date:"2026-11-12",notes:"synthetic only",
 notesManual:true,editedAt:1794474000000,exercises:[
 {id:"zZ",bankId:BANK[0].id,name:BANK[0].name,sets:3,side:"LR",loadUnit:"kg",metricUnit:"Wdh",
 previous:[["10","12"],["11","11"],["12","10"]],today:[["11","12"],["12","11"],["13","9"]],
 manual:[[true,false],[false,true],[false,false]],manualFields:["startLoad"],startLoad:"11"},
 {id:"zY",bankId:BANK[1].id,name:BANK[1].name,sets:2,side:"BI",loadUnit:"kg",metricUnit:"Wdh",
 previous:[["20","12"],["21","10"]],today:[["22","11"],["23","9"]],manual:[[false,true],[false,false]],manualFields:[]}
]};
async function main(){
 const a=device(BANK),compact=a.api.encodeV2(plan);
 const local=device(BANK);
 assert.equal(typeof local.api.importCodeAsync,"function","RED: V2 import flow not wired to existing cockpit");
 const accepted=await local.api.importCodeAsync(compact);
 assert.equal(accepted.slot,0);
 assert.equal(local.api.getState().slotCount,1);
 const slot=local.api.getSlot(0);
 assert.equal(slot.name,"Plan ohne Patientendaten");
 assert.equal(slot.exercises[0].bankId,BANK[0].id,"stable bank ID must survive slot normalization");
 assert.deepEqual(clone(slot.exercises[0].today),plan.exercises[0].today);
 assert.equal(local.refreshes,0,"known bank must not refresh");
 const result=local.api.finish(0);
 assert(result,"real finish must produce a portable link");
 assert.equal(new URL(result.link).searchParams.get("cockpit")?.startsWith("KGGTC1:"),true);
 assert.equal(local.api.isV2(new URL(result.link).searchParams.get("cockpit")),true,"bank-resolved finish should prefer compact V2");
 console.log("KNOWN_V2_IMPORTED_AND_FINISHED=true");
 const missing=device([BANK[1]]);
 let reasons=[];
 missing.onRefresh(async reason=>{reasons.push(reason);missing.setBank(BANK);return true;});
 const recovered=await missing.api.importCodeAsync(compact);
 assert.equal(recovered.slot,0);
 assert.equal(missing.refreshes,1,"exactly one configured SAF read");
 assert.deepEqual(reasons,["cockpit_missing_exercise"],"refresh must not receive values or plan IDs");
 assert.equal(missing.api.getSlot(0).exercises[0].bankId,BANK[0].id);
 console.log("ONE_SHOT_BANK_REFRESH=true");
 const unavailable=device([BANK[1]]);
 unavailable.onRefresh(async()=>false);
 const before=JSON.stringify(unavailable.api.getState()),writes=unavailable.writes;
 await assert.rejects(unavailable.api.importCodeAsync(compact));
 assert.equal(unavailable.refreshes,1);
 assert.equal(JSON.stringify(unavailable.api.getState()),before,"failed V2 must not change slot state");
 assert.equal(unavailable.writes,writes,"failed V2 must not change storage");
 const wrong=device([BANK[1]]);
 wrong.onRefresh(async()=>{wrong.setBank([{...BANK[0],name:"Wrong remote name"},BANK[1]]);return true;});
 await assert.rejects(wrong.api.importCodeAsync(compact),/bank_identity_mismatch|exercise_id_collision/);
 assert.equal(wrong.refreshes,1);assert.equal(wrong.api.getState().slotCount,0);
 const corrupt=compact.slice(0,-2)+"xx";
 const rejected=device(BANK);
 const prev=JSON.stringify(rejected.api.getState()),prevWrites=rejected.writes;
 await assert.rejects(rejected.api.importCodeAsync(corrupt));
 assert.equal(rejected.api.getState().slotCount,0);
 assert.equal(JSON.stringify(rejected.api.getState()),prev);
 assert.equal(rejected.writes,prevWrites);
 assert.equal(rejected.refreshes,0,"corrupt V2 must not trigger Drive read");
 console.log("ATOMIC_FAILURES_NO_WRITES=true");
 const legacy=device(BANK),oldCode=a.api.encode(plan);
 const prior=legacy.api.importCode(oldCode);
 assert.equal(prior.slot,0,"V1 synchronous import must remain");
 legacy.setBank([]);
 const oldFinish=legacy.api.finish(0);
 assert(oldFinish&&oldFinish.link,"legacy fallback finish must remain available");
 assert.equal(a.api.isV2(new URL(oldFinish.link).searchParams.get("cockpit")),false);
 console.log("V1_LEGACY_FALLBACK_PRESERVED=true");
 console.log(JSON.stringify({status:"V2_FLOW_PASS",checks:["known V2 import+finish","one SAF refresh","bad identity rejects after refresh","tamper no refresh","no slot/storage partial state","legacy v1 sync import+finish fallback"]}));
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
