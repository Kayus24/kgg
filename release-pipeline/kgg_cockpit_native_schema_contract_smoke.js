#!/usr/bin/env node
"use strict";
// Real native validator + existing cockpit wrapper, entirely synthetic.
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const {client}=require("./kgg_drive_sync_core_smoke.js");
const html=fs.readFileSync(path.join(__dirname,"../kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const script=html.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i)?.[1];
assert(script,"cockpit v082 source unavailable");
function attach(c){
 c.ctx.window.location={href:"https://example.test/kgg-update/index.html"};
 c.ctx.document.readyState="loading";
 vm.runInContext(script,c.ctx);
 assert(c.ctx.window.KGGTherapyCockpit);
}
const a=client("a"),b=client("b");
a.create("Native valid legacy exercise");
const doc=a.ctx.window.KGGNativeExerciseSync.build();
assert(doc.exerciseBank.length>0,"synthetic native source must contain exerciseBank");
assert(!("cockpitId" in doc.exerciseBank[0]),"native format contains forbidden field in input");
attach(b);
const result=b.ctx.window.KGGNativeExerciseSync.merge(doc);
assert(result&&result.bank&&result.bank.added>0,"actual native merge must succeed");
const ex=b.core.bank.find(e=>e.name==="Native valid legacy exercise");
assert(ex,"actual native merge did not import exercise");
assert(b.ctx.window.KGGTherapyCockpit.registry.lookup(ex.name),"imported legal native exercise not registered");
console.log("REAL_NATIVE_SCHEMA_CONTRACT_PASS=true");
