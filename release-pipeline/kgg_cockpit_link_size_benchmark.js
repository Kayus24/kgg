#!/usr/bin/env node
"use strict";
// Synthetischer, read-only Vergleich. Keine Produktdatei wird modifiziert.
const fs=require("fs"),path=require("path"),vm=require("vm"),assert=require("assert/strict");
const root=path.resolve(__dirname,"..");
const code=fs.readFileSync(path.join(root,"kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const match=code.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i);
assert(match,"cockpit module missing");
const window={fflate:require(path.join(root,"vendor/fflate-0.8.3.js")),location:{href:"https://example.test/"},KGG_PATCHES:{},addEventListener(){},dispatchEvent(){}};
const document={readyState:"loading",body:null,title:"Synthetischer Test",addEventListener(){},getElementById(){return null}};
const context={window,document,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,btoa:v=>Buffer.from(v,"binary").toString("base64"),atob:v=>Buffer.from(v,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
vm.createContext(context);vm.runInContext(match[1],context);
const api=window.KGGTherapyCockpit;assert(api,"cockpit API absent");
const B62="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
const idFor=i=>B62[Math.floor(i/62)]+B62[i%62];
const registry=api.registry.entries(),known=new Set(registry.map(x=>x.id));
for(let i=0;i<42;i++){const id=idFor(62+i);if(known.has(id))continue;api.registry.register("Synthetische Uebung "+i,id,{sets:3,metricUnit:"Wdh",loadUnit:"kg"});known.add(id);}
const syntheticIds=[...known].slice(0,40);
const URL_BASE="https://kayus24.github.io/kgg/kgg-update/index.html?cockpit=";
function exercise(id,i){
  const previous=[[String(10+i),"12"],[String(11+i),"11"],[String(12+i),"10"]];
  const today=[[String(10+i),"13"],[String(11+i),"12"],[String(12+i),"11"]];
  const manual=[[i===0,false],[false,i===1],[false,false]];
  return {id,sets:3,side:i%2?"LR":"BI",loadUnit:"kg",metricUnit:"Wdh",previous,today,manual};
}
function plan(count){
  return {planId:"synthetic-plan-20261112",name:"Synthetische Person",date:"2026-11-12",
    notes:"Synthetische Dokumentation",notesManual:true,editedAt:1794474000000,removedIds:[],
    exercises:syntheticIds.slice(0,count).map(exercise)};
}
function compact(p){
  return {v:2,p:p.planId,d:p.date,n:p.notes,nm:p.notesManual,u:p.editedAt,
    e:p.exercises.map(ex=>[ex.id,ex.side==="LR"?1:0,ex.previous,ex.today,
      ex.manual.reduce((mask,pair,index)=>mask|(pair[0]?1<<(index*2):0)|(pair[1]?1<<(index*2+1):0),0)])};
}
function decodeCompact(bytes){
  const obj=JSON.parse(Buffer.from(window.fflate.inflateSync(bytes)).toString("utf8"));
  assert.equal(obj.v,2);return obj;
}
const rows=[];
for(const count of [3,10,20,40]){
  const p=plan(count),old=api.encode(p),roundtrip=api.decode(old);
  assert.equal(roundtrip.exercises.length,count);
  assert.equal(roundtrip.exercises[0].today[0][1],"13");
  assert.equal(roundtrip.exercises[0].previous[0][1],"12");
  assert.equal(roundtrip.notes,p.notes);
  const minimal=compact(p),json=JSON.stringify(minimal),z=window.fflate.deflateSync(Buffer.from(json),{level:6});
  const minimalCode="KGGTC2:z"+Buffer.from(z).toString("base64url");
  const copy=decodeCompact(z);
  assert.equal(copy.e.length,count);
  assert.deepEqual(copy.e[0][2],p.exercises[0].previous);
  assert.deepEqual(copy.e[0][3],p.exercises[0].today);
  assert.equal(copy.e[0][4],1);
  assert.equal(copy.n,p.notes);
  rows.push({count,kggtc1Chars:old.length,compactPrototypeChars:minimalCode.length,
    kggtc1UrlChars:URL_BASE.length+old.length,prototypeUrlChars:URL_BASE.length+minimalCode.length,
    reductionPct:+((1-(URL_BASE.length+minimalCode.length)/(URL_BASE.length+old.length))*100).toFixed(1)});
}
console.log(JSON.stringify({status:"PASS",kind:"PROTOTYPE_ONLY_NOT_PRODUCTION_CODEC",rows},null,2));
// Zwei UNABHAENGIGE synthetische Geraetekontexte koennen dieselbe 2-stellige ID anders belegen.
const freshApi=()=>{const w={fflate:window.fflate,location:{href:"https://example.test/"},KGG_PATCHES:{},addEventListener(){},dispatchEvent(){}};const ctx={...context,window:w};vm.createContext(ctx);vm.runInContext(match[1],ctx);return w.KGGTherapyCockpit;};
function derivedId(name){
  const key=name.toLowerCase().replace(/[^a-z0-9]+/g," ").trim().replace(/\s+/g,"");
  let h=2166136261;for(const b of Buffer.from(key,"utf8")){h^=b;h=Math.imul(h,16777619)>>>0;}
  const i=(parseInt(h.toString(36),36)>>>0)%3844;return idFor(i);
}
const canonicalIds=new Set(freshApi().registry.entries().map(x=>x.id));
const seen=new Map();let collision=null;
for(let i=0;i<3000;i++){
  const name="Synthetische Kollisionsuebung Nummer "+i,id=derivedId(name);
  if(canonicalIds.has(id))continue;
  if(seen.has(id)){collision={id,first:seen.get(id),second:name};break;}
  seen.set(id,name);
}
assert(collision,"expected collision among 3000 synthetic labels");
const deviceA=freshApi(),deviceB=freshApi();
const a=deviceA.registry.derive(collision.first),b=deviceB.registry.derive(collision.second);
assert.equal(a.id,b.id);assert.notEqual(a.name,b.name);
assert.equal(deviceA.registry.lookup(a.id).name,collision.first);
assert.equal(deviceB.registry.lookup(b.id).name,collision.second);
assert.throws(()=>deviceA.registry.derive(collision.second),e=>e&&e.code==="exercise_id_collision");
console.log(JSON.stringify({status:"PASS",risk:"SAME_TWO_CHAR_ID_DIFFERENT_NAMES_ON_INDEPENDENT_DEVICES",collision},null,2));
// Worst-case-Naeherung: Alle Uebungen haben lange, mit der Bank synchronisierte custom_-IDs.
const robustRows=[];
for(const count of [3,10,20,40]){
  const p=plan(count),old=api.encode(p),minimal=compact(p);
  minimal.e=minimal.e.map((row,index)=>{
    const stableBankId="custom_1762940000000_"+index.toString(36).padStart(4,"0");
    return [stableBankId,...row.slice(1)];
  });
  const compressed=window.fflate.deflateSync(Buffer.from(JSON.stringify(minimal)),{level:6});
  const codeLen="KGGTC2:z".length+Buffer.from(compressed).toString("base64url").length;
  robustRows.push({count,kggtc1UrlChars:URL_BASE.length+old.length,
    stableBankIdPrototypeUrlChars:URL_BASE.length+codeLen,
    reductionPct:+(100*(1-(URL_BASE.length+codeLen)/(URL_BASE.length+old.length))).toFixed(1)});
}
console.log(JSON.stringify({status:"PASS",kind:"LONG_STABLE_BANK_IDS_SYNTHETIC_UPPER_BOUND_SCENARIO",robustRows},null,2));
