import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {DEFINITIONS,collectProofs,writeProofs} from "./kgg_patient_unified_extra_proofs.mjs";

const SHA="a".repeat(40);
const MODES=["legacy","react-p7","react-p8"];
function createEvidence(){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),"kgg-extra-proofs-"));
 const dir=path.join(root,"patient-ui-parity");fs.mkdirSync(dir);
 fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify({
   schema:2,candidateSha:SHA,engine:"webkit",syntheticOnly:true,status:"PASS"
 }));
 for(const def of DEFINITIONS){
   const lines=MODES.map(mode=>{
     const row={engine:"webkit",mode,sourceSha:SHA};
     for(const key of def.required)row[key]=true;
     if(def.id==="firstload"){row.status="PASS";row.directFirstLoadModules=27;}
     return (def.prefix||"")+JSON.stringify(row);
   });
   fs.writeFileSync(path.join(dir,def.file),lines.join("\n")+"\n");
 }
 return {dir,cleanup:()=>fs.rmSync(root,{recursive:true,force:true})};
}
function withDir(cb){const {dir,cleanup}=createEvidence();try{return cb(dir)}finally{cleanup()}}
function alter(dir,file,fn){
 const p=path.join(dir,file);
 fs.writeFileSync(p,fn(fs.readFileSync(p,"utf8")));
}
test("all four existing suites produce 12 signed 3-mode proofs",()=>withDir(dir=>{
 const out=writeProofs(dir);
 assert.deepEqual({engine:out.engine,sha:out.sha,groups:out.groups,proofFiles:out.proofFiles},
   {engine:"webkit",sha:SHA,groups:4,proofFiles:12});
 for(const def of DEFINITIONS)for(const mode of MODES){
   const p=JSON.parse(fs.readFileSync(path.join(dir,def.id+"-"+mode+".json")));
   assert.equal(p.status,"PASS");assert.equal(p.mode,mode);assert.equal(p.sourceSha,SHA);
   assert.deepEqual(p.featureIds,def.featureIds);
   assert.ok(Object.values(p.assertions).every(value=>value===true));
 }
}));
test("missing mode fails closed, no proof artifacts written",()=>withDir(dir=>{
 alter(dir,"settings-parity.log",s=>s.split("\n").filter(x=>!x.includes('"mode":"react-p8"')).join("\n"));
 assert.throws(()=>writeProofs(dir),/expected exactly 3/);
 assert.equal(fs.existsSync(path.join(dir,"settings-legacy.json")),false);
}));
test("duplicate mode fails closed",()=>withDir(dir=>{
 alter(dir,"progression-parity.log",s=>s.replace('"mode":"react-p8"','"mode":"legacy"'));
 assert.throws(()=>collectProofs(dir),/missing\/duplicate/);
}));
test("false success fields never count as passing",()=>withDir(dir=>{
 alter(dir,"scanner-fallback-parity.log",s=>s.replace('"retry":true','"retry":false'));
 assert.throws(()=>collectProofs(dir),/nonpassing assertion retry/);
}));
test("wrong SHA or browser fails closed",()=>withDir(dir=>{
 alter(dir,"settings-parity.log",s=>s.replace('"sourceSha":"'+SHA+'"','"sourceSha":"'+("b".repeat(40))+'"'));
 assert.throws(()=>collectProofs(dir),/wrong browser or stale source SHA/);
}));
test("first-load must retain real module and lightbox checks",()=>withDir(dir=>{
 alter(dir,"firstload-parity.log",s=>s.replace('"directFirstLoadModules":27','"directFirstLoadModules":0'));
 assert.throws(()=>collectProofs(dir),/module count/);
}));
test("first-load must prove synthetic Lightbox path",()=>withDir(dir=>{
 alter(dir,"firstload-parity.log",s=>s.replace('"mediaLightboxChecked":true','"mediaLightboxChecked":false'));
 assert.throws(()=>collectProofs(dir),/nonpassing assertion mediaLightboxChecked/);
}));
test("invalid core report blocks all extra proofs",()=>withDir(dir=>{
 alter(dir,"report.json",s=>s.replace('"syntheticOnly":true','"syntheticOnly":false'));
 assert.throws(()=>collectProofs(dir),/Missing valid synthetic core/);
}));
