import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import crypto from "node:crypto";
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
      {viewport:"tablet",mode:"legacy"},{viewport:"tablet",mode:"react"},
      {viewport:"phone",mode:"react-grid"},{viewport:"tablet",mode:"react-grid"}
    ]};
  fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report));
  for(const group of GROUPS)for(const mode of (group.modes||["legacy","react"])){
    const result={schema:1,status:"PASS",engine:"chromium",mode,syntheticOnly:true,
      sourceSha:SHA,featureIds:group.ids,assertions:{clicks:true,storage:true}};
    if(group.requireExecution){
      result.assertions=Object.fromEntries(group.requiredAssertions.map(key=>[key,true]));
      const name=group.id+"-"+mode+".log",body="synthetic test fixture log";
      fs.writeFileSync(path.join(dir,name),body);
      result.execution={completed:true,exitCode:0,log:name,
        sha256:crypto.createHash("sha256").update(body).digest("hex")};
    }
    fs.writeFileSync(path.join(dir,group.id+"-"+mode+".json"),JSON.stringify(result));
  }
  const required=JSON.parse(fs.readFileSync(new URL('./patient-integrated-suites.json',import.meta.url))).requiredSteps;
  const log='fixture-execution.log',body='synthetic completed execution';fs.writeFileSync(path.join(dir,log),body);
  const digest=crypto.createHash('sha256').update(body).digest('hex');
  fs.writeFileSync(path.join(dir,'execution-index.json'),JSON.stringify({schema:1,sourceSha:SHA,
    engine:'chromium',fingerprint:'c'.repeat(64),candidateDirty:false,complete:true,requiredSteps:required,
    steps:required.map(id=>({id,status:'PASS',completed:true,exitCode:0,log,sha256:digest}))}));
  return {dir,root,cleanup:()=>fs.rmSync(root,{recursive:true,force:true})};
}
function withFixture(fn){const f=buildFixture();try{return fn(f)}finally{f.cleanup()}}
test("six-variant pinned candidate with proven extra flows remains final-device-pending",()=>
  withFixture(({dir})=>{
    const result=summarizeAcceptance(dir);
    assert.equal(result.status,"AUTOMATED_SCOPE_PASS_FINAL_PENDING");
    assert.equal(result.sourceSha,SHA);
    assert.equal(result.blocks.length,GROUPS.length+2);
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
    assert.ok(report.coverage.mapped>=50,"media lifecycle mapping must remain present");
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

test("adaptive responsive evidence is fail-closed for missing, stale and incorrect modes",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"adaptive-react.json");
    fs.unlinkSync(p);
    let result=summarizeAcceptance(dir);
    assert.equal(result.status,"REVIEW_REQUIRED");
    assert.equal(result.blocks.find(x=>x.id==="adaptive").status,"NOT_EVIDENCED");
    const proof={schema:1,status:"PASS",syntheticOnly:true,engine:"chromium",
      mode:"react",sourceSha:"b".repeat(40),
      featureIds:GROUPS.find(x=>x.id==="adaptive").ids,assertions:{viewport:true}};
    fs.writeFileSync(p,JSON.stringify(proof));
    result=summarizeAcceptance(dir);
    assert.equal(result.blocks.find(x=>x.id==="adaptive").variants[1].status,"STALE");
    proof.sourceSha=SHA;proof.assertions.viewport=false;
    fs.writeFileSync(p,JSON.stringify(proof));
    result=summarizeAcceptance(dir);
    assert.equal(result.blocks.find(x=>x.id==="adaptive").status,"REVIEW_REQUIRED");
    proof.assertions.viewport=true;proof.mode="legacy";
    fs.writeFileSync(p,JSON.stringify(proof));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="adaptive").variants[1].status,"INVALID");
  }));

test("media lifecycle proof requires same-engine, matching-SHA, two-mode evidence",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"media-react.json");
    fs.unlinkSync(p);
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="media").status,"NOT_EVIDENCED");
    const proof={schema:1,status:"PASS",syntheticOnly:true,engine:"chromium",
      mode:"react",sourceSha:"b".repeat(40),
      featureIds:["PAT-MEDIA-006","PAT-MEDIA-011"],
      assertions:{decoded:true,stable:true}};
    fs.writeFileSync(p,JSON.stringify(proof));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="media").variants[1].status,"STALE");
    proof.sourceSha=SHA;proof.assertions.stable=false;
    fs.writeFileSync(p,JSON.stringify(proof));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="media").status,"REVIEW_REQUIRED");
    proof.assertions.stable=true;proof.engine="webkit";
    fs.writeFileSync(p,JSON.stringify(proof));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="media").variants[1].status,"INVALID");
  }));

test("database evidence is required for both Legacy and React and must match engine",()=>
  withFixture(({dir})=>{
    const p=path.join(dir,"db-react.json");
    fs.unlinkSync(p);
    let report=summarizeAcceptance(dir);
    assert.equal(report.status,"REVIEW_REQUIRED");
    assert.equal(report.blocks.find(x=>x.id==="db").status,"NOT_EVIDENCED");
    const invalid={schema:1,status:"PASS",syntheticOnly:true,
      engine:"webkit",mode:"react",sourceSha:SHA,
      featureIds:["PAT-DB-001","PAT-DB-002"],
      assertions:{searchFilters:true,importsFromStoredPlan:true}};
    fs.writeFileSync(p,JSON.stringify(invalid));
    report=summarizeAcceptance(dir);
    assert.equal(report.blocks.find(x=>x.id==="db").status,"REVIEW_REQUIRED");
    invalid.engine="chromium";
    invalid.assertions.duplicateRejected=false;
    fs.writeFileSync(p,JSON.stringify(invalid));
    assert.equal(summarizeAcceptance(dir).blocks.find(x=>x.id==="db").status,
      "REVIEW_REQUIRED");
  }));

const CHILD_MODES=["legacy","react-p7","react-p8"];
const CHILD_IDS=["settings","progression","scan-fallback","firstload"];
test("integrated report requires all four child suites, not separate green PRs",()=>{
 for(const id of CHILD_IDS){const g=GROUPS.find(g=>g.id===id);
  assert.ok(g,"missing mandatory integrated suite "+id);
  assert.deepEqual(g.modes,CHILD_MODES);
  assert.ok(g.requiredAssertions.length>2);
 }
});
test("P8 phone and tablet recordings are mandatory",()=>withFixture(({dir})=>{
 const p=path.join(dir,"report.json"),r=JSON.parse(fs.readFileSync(p));
 r.variants=r.variants.filter(v=>v.mode!=="react-grid");fs.writeFileSync(p,JSON.stringify(r));
 assert.equal(summarizeAcceptance(dir).blocks[0].status,"FAIL");
}));
test("duplicate core variants cannot substitute for unique evidence",()=>withFixture(({dir})=>{
 const p=path.join(dir,"report.json"),r=JSON.parse(fs.readFileSync(p));r.variants.push(r.variants[0]);
 fs.writeFileSync(p,JSON.stringify(r));assert.equal(summarizeAcceptance(dir).blocks[0].status,"FAIL");
}));
for(const id of CHILD_IDS){
 test("integrated "+id+" requires actual P8 proof",()=>withFixture(({dir})=>{
  fs.rmSync(path.join(dir,id+"-react-p8.json"),{force:true});
  assert.notEqual(summarizeAcceptance(dir).status,"AUTOMATED_SCOPE_PASS_FINAL_PENDING");
 }));
}
test("child PASS flags cannot override a failed process exit",()=>withFixture(({dir})=>{
 const p=path.join(dir,"settings-react-p8.json");
 const proof=fs.existsSync(p)?JSON.parse(fs.readFileSync(p)):{};
 proof.execution={completed:true,exitCode:1,log:"fixture.log",sha256:"b".repeat(64)};
 fs.writeFileSync(p,JSON.stringify(proof));
 assert.notEqual(summarizeAcceptance(dir).status,"AUTOMATED_SCOPE_PASS_FINAL_PENDING");
}));

test('missing integrated execution ledger must not pass',()=>withFixture(({dir})=>{
 fs.unlinkSync(path.join(dir,'execution-index.json'));
 assert.notEqual(summarizeAcceptance(dir).status,'AUTOMATED_SCOPE_PASS_FINAL_PENDING');
}));
for(const defect of ['exit','sha','duplicate','log','dirty'])test('execution ledger rejects '+defect,()=>withFixture(({dir})=>{
 const p=path.join(dir,'execution-index.json'),r=JSON.parse(fs.readFileSync(p));
 if(defect==='exit')r.steps[0].exitCode=1;
 if(defect==='sha')r.sourceSha='b'.repeat(40);
 if(defect==='duplicate')r.steps.push(r.steps[0]);
 if(defect==='log')fs.writeFileSync(path.join(dir,r.steps[0].log),'modified after execution');
 if(defect==='dirty')r.candidateDirty=true;
 fs.writeFileSync(p,JSON.stringify(r));
 assert.notEqual(summarizeAcceptance(dir).status,'AUTOMATED_SCOPE_PASS_FINAL_PENDING');
}));

test('offline group requires all modes and actual serviceworker evidence',()=>{
 const g=GROUPS.find(g=>g.id==='offline');assert.ok(g,'missing real offline group');
 assert.deepEqual(g.modes,CHILD_MODES);
 assert.ok(g.requiredAssertions.includes('offlineChecked'));
 assert.ok(g.requiredAssertions.includes('cacheOptInVerified'));
});
