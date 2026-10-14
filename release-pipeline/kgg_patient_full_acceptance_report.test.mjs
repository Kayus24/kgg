import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {GROUPS,summarizeAcceptance,renderAcceptanceHtml} from "./kgg_patient_full_acceptance_report.mjs";

const SHA="a".repeat(40);
function buildFixture(){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),"kgg-acceptance-"));
  const dir=path.join(root,"patient-ui-parity");
  fs.mkdirSync(dir);
  const report={schema:2,syntheticOnly:true,status:"PASS",engine:"chromium",
    candidateSha:SHA,checks:Array.from({length:352},()=>({pass:true})),
    unexpectedDifferences:[],variants:[
      {viewport:"phone",mode:"legacy"},{viewport:"phone",mode:"react"},
      {viewport:"tablet",mode:"legacy"},{viewport:"tablet",mode:"react"}
    ]};
  fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report));
  for(const group of GROUPS)for(const mode of ["legacy","react"]){
    const result={schema:1,status:"PASS",engine:"chromium",mode,syntheticOnly:true,
      sourceSha:SHA,featureIds:group.ids,assertions:{clicks:true,storage:true}};
    fs.writeFileSync(path.join(dir,group.id+"-"+mode+".json"),JSON.stringify(result));
  }
  return {dir,root,cleanup:()=>fs.rmSync(root,{recursive:true,force:true})};
}
function withFixture(fn){const f=buildFixture();try{return fn(f)}finally{f.cleanup()}}
test("four-mode signed candidate with proven extra flows remains final-device-pending",()=>
  withFixture(({dir})=>{
    const result=summarizeAcceptance(dir);
    assert.equal(result.status,"AUTOMATED_SCOPE_PASS_FINAL_PENDING");
    assert.equal(result.sourceSha,SHA);
    assert.equal(result.blocks.length,7);
    assert.ok(result.blocks.every(x=>x.status==="PASS"));
    assert.ok(result.pending.length>=4);
    assert.match(renderAcceptanceHtml(result),/kgg/ig);
  }));
test("missing React unit evidence blocks combined green",()=>
  withFixture(({dir})=>{
    fs.unlinkSync(path.join(dir,"unit-react.json"));
    const result=summarizeAcceptance(dir);
    assert.equal(result.status,"REVIEW_REQUIRED");
    assert.equal(result.blocks.find(x=>x.id==="unit").status,"NOT_EVIDENCED");
  }));
test("stale day evidence never passes",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"days-react.json");
    const x=JSON.parse(fs.readFileSync(p));
    x.sourceSha="b".repeat(40);fs.writeFileSync(p,JSON.stringify(x));
    const result=summarizeAcceptance(dir);
    assert.equal(result.blocks.find(x=>x.id==="days").status,"REVIEW_REQUIRED");
    assert.equal(result.blocks.find(x=>x.id==="days").variants[1].status,"STALE");
  }));
test("explicitly false assertion never passes",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"unit-legacy.json");
    const x=JSON.parse(fs.readFileSync(p));x.assertions.storage=false;
    fs.writeFileSync(p,JSON.stringify(x));
    assert.equal(summarizeAcceptance(dir).blocks[1].variants[0].status,"FAIL");
  }));
test("wrong engine, missing proof IDs or missing tablet variant are rejected",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"unit-react.json");
    const x=JSON.parse(fs.readFileSync(p));x.engine="webkit";x.featureIds=[];
    fs.writeFileSync(p,JSON.stringify(x));
    assert.equal(summarizeAcceptance(dir).blocks[1].variants[1].status,"INVALID");
    const rp=path.join(dir,"report.json");const r=JSON.parse(fs.readFileSync(rp));
    r.variants.splice(3,1);fs.writeFileSync(rp,JSON.stringify(r));
    assert.equal(summarizeAcceptance(dir).blocks[0].status,"FAIL");
  }));
test("Gemini advisory alert prevents automated-scope green",()=>
  withFixture(({dir})=>{
    fs.writeFileSync(path.join(dir,"gemini-web-review.json"),JSON.stringify({
      advisoryOnly:true,sourceSha:SHA,status:"REVIEW_REQUIRED",findings:[{step:"remaining-kg"}]
    }));
    const result=summarizeAcceptance(dir);
    assert.equal(result.status,"REVIEW_REQUIRED");
    assert.equal(result.advisory.status,"REVIEW_REQUIRED");
  }));
test("old Gemini verdict is STALE, not PASS",()=>
  withFixture(({dir})=>{
    fs.writeFileSync(path.join(dir,"gemini-web-review.json"),JSON.stringify({
      advisoryOnly:true,sourceSha:"b".repeat(40),status:"PASS",findings:[]
    }));
    assert.equal(summarizeAcceptance(dir).advisory.status,"STALE_OR_INVALID");
  }));
test("report HTML safely escapes untrusted evidence",()=>
  withFixture(({dir})=>{
    const result=summarizeAcceptance(dir);
    result.blocks[1].label="<img src=x onerror=alert(1)>";
    const html=renderAcceptanceHtml(result);
    assert.match(html,/&lt;img/);
    assert.doesNotMatch(html,/<img src=x onerror/);
  }));
test("reject malformed/non-synthetic/oversized evidence",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"report.json");
    fs.writeFileSync(p,JSON.stringify({syntheticOnly:false,candidateSha:SHA}));
    assert.equal(summarizeAcceptance(dir).status,"INCOMPLETE");
    fs.writeFileSync(p,"x".repeat(1000001));
    assert.throws(()=>summarizeAcceptance(dir),/Invalid report evidence/);
  }));

test("missing React pain proof prevents an overall scoped PASS",()=>
  withFixture(({dir})=>{
    fs.unlinkSync(path.join(dir,"pain-react.json"));
    const report=summarizeAcceptance(dir);
    assert.equal(report.status,"REVIEW_REQUIRED");
    assert.equal(report.blocks.find(b=>b.id==="pain").status,"NOT_EVIDENCED");
  }));
test("canonical Drive-feature snapshot stays explicit and incomplete",()=>
  withFixture(({dir})=>{
    const report=summarizeAcceptance(dir);
    assert.equal(report.coverage.status,"SNAPSHOT_ONLY");
    assert.equal(report.coverage.total,111);
    assert.ok(report.coverage.mapped>=32,"newly covered QR functions must remain mapped");
    assert.ok(report.coverage.notMapped<=79,"unmapped functions unexpectedly increased");
    assert.equal(report.coverage.mapped+report.coverage.notMapped,report.coverage.total);
    const html=renderAcceptanceHtml(report);
    assert.match(html,/111/);
    assert.match(html,new RegExp(String(report.coverage.notMapped)));
    assert.equal(report.manualAcceptancePending,true);
  }));

test("scan proof cannot be missing, stale or attributed to the wrong browser",()=>
  withFixture(({dir})=>{
    fs.unlinkSync(path.join(dir,"scan-react.json"));
    const absent=summarizeAcceptance(dir);
    assert.equal(absent.status,"REVIEW_REQUIRED");
    assert.equal(absent.blocks.find(x=>x.id==="scan").status,"NOT_EVIDENCED");
    const p=path.join(dir,"scan-react.json");
    const fake={schema:1,status:"PASS",engine:"webkit",mode:"react",
      syntheticOnly:true,sourceSha:SHA,featureIds:["PAT-IMPORT-001","PAT-IMPORT-002"],
      assertions:{h2Imported:true,h3Imported:true}};
    fs.writeFileSync(p,JSON.stringify(fake));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="scan").status,
      "REVIEW_REQUIRED");
  }));

test("new-plan link-choice proof cannot be missing, forged or stale",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"link-react.json");
    fs.unlinkSync(p);
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="link").status,
      "NOT_EVIDENCED");
    const fake={schema:1,status:"PASS",engine:"chromium",mode:"react",syntheticOnly:true,
      sourceSha:"b".repeat(40),featureIds:["PAT-LINK-001","PAT-MULTI-002","PAT-SCAN-002"],
      assertions:{cancelPreservesActive:true,addPreservesOldPlan:true,
        activeReplaceOnly:true,savedValuesPreserved:true}};
    fs.writeFileSync(p,JSON.stringify(fake));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="link").variants[1].status,
      "STALE");
    fake.sourceSha=SHA;
    fake.assertions.activeReplaceOnly=false;
    fs.writeFileSync(p,JSON.stringify(fake));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="link").status,
      "REVIEW_REQUIRED");
  }));

test("plan-management result does not pass with a missing or misattributed React proof",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"manage-react.json");
    fs.unlinkSync(p);
    let result=summarizeAcceptance(dir);
    assert.equal(result.status,"REVIEW_REQUIRED");
    assert.equal(result.blocks.find(x=>x.id==="manage").status,"NOT_EVIDENCED");
    fs.writeFileSync(p,JSON.stringify({schema:1,status:"PASS",
      syntheticOnly:true,engine:"webkit",mode:"react",sourceSha:SHA,
      featureIds:["PAT-MULTI-001","PAT-MULTI-004","PAT-MULTI-005",
        "PAT-MULTI-006","PAT-DEL-001"],
      assertions:{renamePersists:true,deleteActiveRestoresOther:true}}));
    result=summarizeAcceptance(dir);
    assert.equal(result.blocks.find(x=>x.id==="manage").status,"REVIEW_REQUIRED");
  }));
