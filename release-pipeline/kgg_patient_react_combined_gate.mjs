#!/usr/bin/env node
"use strict";
// Fail-closed, SHA-bound synthetic Legacy/P7/P8 cross-feature acceptance.
// This validates actual independent browser evidence; it never grants a release.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const SCHEMA="kgg/patient-react-unified-parity/v1";
const SUITES=["settings","progression","scanner","firstload","video"];
const ENGINES=["chromium","webkit"];
const MODES=["legacy","react-p7","react-p8"];
const IDs={
  settings:["PAT-SETTINGS-001","PAT-SETTINGS-002","PAT-UNIT-007"],
  progression:["PAT-PROGRESSION-001","PAT-PROGRESSION-002"],
  scanner:["PAT-SCAN-001","PAT-SCAN-003","PAT-SCAN-004"],
  firstload:["PAT-PWA-002","PAT-THUMB-001","PAT-MEDIA-009"],
  video:[]
};
function verify(ok,message){if(!ok)throw new Error("KGG combined acceptance: "+message);}
function read(file){return JSON.parse(fs.readFileSync(file,"utf8"));}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function rows(log,suite){
  const lines=fs.readFileSync(log,"utf8").split(/\r?\n/);
  const prefix={
    settings:"KGG_PATIENT_SETTINGS_PARITY_PASS ",
    progression:"KGG_PROGRESSION_PARITY_PASS ",
    scanner:"KGG_SCAN_FALLBACK_PARITY_PASS "
  }[suite];
  if(suite==="firstload"){
    return lines.filter(x=>x.startsWith('{"status":"PASS",')).map(x=>JSON.parse(x));
  }
  verify(!!prefix,"unexpected log suite "+suite);
  return lines.filter(x=>x.startsWith(prefix)).map(x=>JSON.parse(x.slice(prefix.length)));
}
function checkEvidence(suite,engine,sha,log,videoDir){
  verify(SUITES.includes(suite)&&ENGINES.includes(engine),"unknown suite/browser");
  verify(/^[0-9a-f]{40}$/.test(sha),"expected exact 40-character Git SHA");
  let modes=MODES,checks=0,detail={};
  if(suite==="video"){
    const report=read(path.join(videoDir,"report.json"));
    verify(report.syntheticOnly===true&&report.status==="PASS","video recorder did not PASS");
    verify(report.candidateSha===sha&&report.engine===engine,"video source SHA/engine stale");
    verify((report.unexpectedDifferences||[]).length===0,"unexpected video differences");
    const variants=report.variants||[];
    verify(variants.length===6,"video recorder must cover all phone/tablet modes");
    for(const size of ["phone","tablet"])
      for(const mode of ["legacy","react","react-grid"])
        verify(variants.filter(v=>v.viewport===size&&v.mode===mode).length===1,
          "missing/duplicated video variant "+size+"/"+mode);
    const pixels=(report.checks||[]).filter(c=>c.kind?.startsWith("pixel:"));
    verify(pixels.length>0&&pixels.every(c=>c.pass===true),"pixel comparison was skipped or failed");
    verify((report.checks||[]).length>=760,"insufficient historical core parity check count");
    const files=report.recordings||[];
    verify(files.length===6&&new Set(files).size===6,"six distinct WebM videos required");
    files.forEach(file=>{
      verify(/^(phone|tablet)-(legacy|react|react-grid)\.webm$/.test(file),"unexpected video name");
      verify(fs.existsSync(path.join(videoDir,file)),"missing recorded video "+file);
    });
    checks=report.checks.length;
    detail={pixels:pixels.length,recordings:files.length,unexpectedDifferences:0,
      viewports:["phone","tablet"],reportedVariants:variants.length};
  }else{
    const proofs=rows(log,suite);
    verify(proofs.length===3,"expected three explicit mode PASS records, saw "+proofs.length);
    for(let i=0;i<MODES.length;i++){
      const v=proofs[i];
      verify(v.mode===MODES[i]&&v.engine===engine&&v.sourceSha===sha,
        "stale/reordered browser proof for "+suite+"/"+MODES[i]);
      if(suite==="firstload"){
        verify(v.status==="PASS"&&v.directFirstLoadModules===27&&
          v.freshRootNoReload===true&&v.serviceWorkerBlocked===true&&
          v.scannerLoadedOnce===true&&v.progressCheckedForAllFields===true&&
          v.redXPlanDeletionChecked===true&&v.localThumbnailGeometryChecked===true&&
          v.mediaLightboxChecked===true,"incomplete fresh preview/Lightbox proof");
      }else{
        const required=suite==="settings"
          ? ["cancel","split","day2","existingRightPreserved","collapse","reload",
              "unitInactivePreservesHistory","perSetPain"]
          :suite==="progression"
          ? ["threeStages","thumbnailSelection","swipeAndClick","zeroValue",
              "dominance","qrMarker","historyNote"]
          :["denied","retry","photoChooser","invalidCodeSafe",
              "validLinkUpdate","reload","noPlanRescue"];
        for(const key of required)verify(v[key]===true,"missing "+suite+" contract "+key);
      }
    }
    checks=proofs.length;
    detail={explicitPasses:proofs.length};
  }
  return {schema:SCHEMA,syntheticOnly:true,deviceAccepted:false,
    suite,engine,headSha:sha,status:"PASS",modes,checks,detail,
    scopedFeatureIds:IDs[suite]};
}
function combined(dir,sha){
  verify(/^[0-9a-f]{40}$/.test(sha),"invalid head SHA");
  const expected=SUITES.flatMap(s=>ENGINES.map(e=>s+"-"+e+".json")).sort();
  const found=fs.readdirSync(dir).filter(x=>x.endsWith(".json")).sort();
  verify(same(found,expected),"missing, duplicate or extra result files: "+JSON.stringify(found));
  const cases=expected.map(file=>read(path.join(dir,file)));
  for(const item of cases){
    verify(item.schema===SCHEMA&&item.syntheticOnly===true&&item.deviceAccepted===false&&
      item.status==="PASS"&&item.headSha===sha,"incompatible or stale evidence");
    verify(same(item.modes,MODES)&&
      same(item.scopedFeatureIds,IDs[item.suite]),"invalid mode/scope mapping");
    verify(item.checks>=3,"empty browser proof");
  }
  const covered=[...new Set(SUITES.flatMap(s=>IDs[s]))].sort();
  verify(covered.length===11,"expected 11 scoped/partial feature IDs");
  return {schema:SCHEMA,candidateSha:sha,status:"AUTOMATED_SCOPE_PASS_DEVICE_PENDING",
    syntheticOnly:true,manualAcceptancePending:true,realDeviceAccepted:false,
    all111FeaturesAccepted:false,baselineInventoryNotMerged:true,
    source:"P8 Draft #322 with unchanged child tests #324–#327",
    expectedEvidence:10,actualEvidence:cases.length,coveredFeatureIds:covered,
    modes:MODES,browsers:ENGINES,suites:SUITES,
    cases:cases.map(x=>({suite:x.suite,engine:x.engine,status:x.status,
      checks:x.checks,detail:x.detail})),
    pending:["real Oppo Android-Chrome","real iPhone Safari and camera",
      "issue #308 grey-frame evidence","unmapped patient features",
      "separately stacked older acceptance PRs #319/#320","explicit main/release review"]};
}
function selfTest(){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),"kgg-combined-self-"));
  const sha="a".repeat(40);
  try{
    for(const suite of SUITES)for(const engine of ENGINES){
      const item={schema:SCHEMA,syntheticOnly:true,deviceAccepted:false,
        suite,engine,headSha:sha,status:"PASS",modes:MODES,checks:3,
        scopedFeatureIds:IDs[suite],detail:{}};
      fs.writeFileSync(path.join(dir,suite+"-"+engine+".json"),JSON.stringify(item));
    }
    verify(combined(dir,sha).actualEvidence===10,"positive aggregation failed");
    const target=path.join(dir,"settings-webkit.json"),save=read(target);
    fs.writeFileSync(target,JSON.stringify({...save,headSha:"b".repeat(40)}));
    let blocked=false;try{combined(dir,sha)}catch{blocked=true}
    verify(blocked,"stale head was accepted");
    fs.writeFileSync(target,JSON.stringify({...save,status:"FAIL"}));
    blocked=false;try{combined(dir,sha)}catch{blocked=true}
    verify(blocked,"failed case was accepted");
    fs.unlinkSync(target);
    blocked=false;try{combined(dir,sha)}catch{blocked=true}
    verify(blocked,"missing case was accepted");
    console.log("KGG combined evidence self-test: PASS (10/10 + stale/fail/missing negative)");
  }finally{fs.rmSync(dir,{recursive:true,force:true})}
}
const [action,...args]=process.argv.slice(2);
try{
  if(action==="proof"){
    const [suite,engine,sha,log,output,videoDir]=args;
    verify(suite&&engine&&sha&&log&&output,"usage: proof suite engine SHA log output [video]");
    const result=checkEvidence(suite,engine,sha,log,videoDir);
    fs.mkdirSync(path.dirname(output),{recursive:true});
    fs.writeFileSync(output,JSON.stringify(result,null,2)+"\n");
    console.log("KGG combined proof PASS: "+suite+"/"+engine+" "+sha);
  }else if(action==="combine"){
    const [directory,sha,output]=args;
    verify(directory&&sha&&output,"usage: combine DIR SHA OUTPUT");
    const result=combined(directory,sha);
    fs.writeFileSync(output,JSON.stringify(result,null,2)+"\n");
    console.log("KGG combined acceptance: "+result.status+" ("+result.actualEvidence+"/10)");
  }else if(action==="self-test"){
    selfTest();
  }else{
    throw new Error("usage: proof | combine | self-test");
  }
}catch(error){console.error(error.stack||error.message);process.exitCode=1}
