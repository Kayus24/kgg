#!/usr/bin/env node
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm"), assert = require("assert/strict");
const sourcePath = path.join(__dirname, "../kgg-update/src/patches/v082-therapy-cockpit.html");
const script = fs.readFileSync(sourcePath, "utf8").match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i)[1];
const memory = new Map();
function load() {
  const window = {location:{href:"https://example.test/admin.html"}, KGG_PATCHES:{}, addEventListener(){}, dispatchEvent(){}, localStorage:{getItem:key=>memory.get(key)||null,setItem:(key,value)=>memory.set(key,value)}};
  const document = {readyState:"loading",body:null,title:"Synthetic",addEventListener(){},getElementById(){return null;}};
  const context = {window,document,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,btoa:s=>Buffer.from(s,"binary").toString("base64"),atob:s=>Buffer.from(s,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
  vm.runInNewContext(script,context,{filename:sourcePath});return window.KGGTherapyCockpit;
}
const api=load();
assert.equal(typeof api.importPatientPlan,"function","successful patient QR must have a Cockpit importer");
const fixture = (planId="synthetic-a", first="10") => ({planId,name:"Synthetic A",date:"2026-10-26",notes:"QR note",exercises:[{id:"01",name:"Abduktion",sets:2,side:"BI",loadUnit:"kg",metricUnit:"Wdh",previous:[[first,"8"],["11","9"]],today:[[first,"8"],["11","9"]]}]});
// Pick the real registered ID rather than assuming a registry numbering scheme.
const id=api.registry.entries()[0].id;
const plan=(planId,first)=>{const p=fixture(planId,first);p.exercises[0].id=id;return p;};
const initial=api.importPatientPlan(plan("synthetic-a","10"));
assert.equal(initial.slot,0);assert(initial.link.includes("cockpit="));
const oldLink=initial.link;
let slot=api.getSlot(0);slot.exercises[0].today[0][0]="0";slot.notes="Manual <note>\nsecond line";
api.updateSlot(0,slot,"cockpit_manual_test");
const incoming=plan("synthetic-a","20");incoming.exercises[0].previous[0][1]="12";incoming.exercises[0].today[0][1]="12";
const merged=api.importPatientPlan(incoming);
assert.equal(merged.slot,0,"same plan must reuse its slot");assert.equal(api.getState().slotCount,1);
slot=api.getSlot(0);assert.equal(slot.exercises[0].today[0][0],"0","manual zero wins");assert.equal(slot.exercises[0].today[0][1],"12","untouched cell takes fresh QR");assert.equal(slot.notes,"Manual <note>\nsecond line");
const finished=api.finish(0);assert(finished.link);assert(finished.text.includes("Manual <note>"));
const again=load();again.importCode(oldLink);assert.equal(again.getSlot(0).exercises[0].today[0][0],"0","old link must not overwrite newer local manual value");assert.equal(again.getSlot(0).notes,"Manual <note>\nsecond line");
memory.clear();const portable=load();portable.importCode(finished.link);assert.equal(portable.getSlot(0).notes,"Manual <note>\nsecond line","new link carries notes across devices");portable.importPatientPlan(incoming);assert.equal(portable.getSlot(0).exercises[0].today[0][0],"0","manual provenance survives portable link");
portable.importPatientPlan(plan("synthetic-b","30"));portable.importPatientPlan(plan("synthetic-c","40"));assert.equal(portable.getState().slotCount,3);assert.equal(portable.importPatientPlan(incoming).slot,0,"matching plan can update with all slots full");
assert.equal(portable.getSlot(1).exercises[0].today[0][0],"30","different plan stays isolated");
const before=JSON.stringify(portable.getState());assert.throws(()=>portable.importPatientPlan(plan("","55")));assert.throws(()=>portable.importPatientPlan({...incoming,exercises:[{id:"??",name:"Bad",sets:1}]}));assert.equal(JSON.stringify(portable.getState()),before,"invalid import must not mutate slots");
// Explicit clearing also has priority over a later nonblank QR.
slot=portable.getSlot(0);slot.exercises[0].today[0][0]="";slot.notes="";portable.updateSlot(0,slot,"cockpit_manual_test");portable.importPatientPlan(incoming);assert.equal(portable.getSlot(0).exercises[0].today[0][0],"");assert.equal(portable.getSlot(0).notes,"");
console.log(JSON.stringify({status:"PASS",checks:["activation","per-cell precedence","manual zero and clearing","notes","portable link","old-link local resume","plan isolation","full-slot reuse","atomic invalid import"]},null,2));
