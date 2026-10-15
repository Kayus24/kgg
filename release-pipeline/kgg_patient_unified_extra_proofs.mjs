#!/usr/bin/env node
// Consolidates existing synthetic browser logs into fail-closed, SHA-bound proof files.
// This is a test-evidence adapter, not a patient application or a second feature implementation.
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

const MODES=["legacy","react-p7","react-p8"];
const SHA=/^[a-f0-9]{40}$/i;
export const DEFINITIONS=[
  {id:"settings",file:"settings-parity.log",prefix:"KGG_PATIENT_SETTINGS_PARITY_PASS ",
   featureIds:["PAT-SETTINGS-001","PAT-SETTINGS-002","PAT-UNIT-007"],
   required:["cancel","split","day2","existingRightPreserved","collapse","reload",
     "unitInactivePreservesHistory","perSetPain"]},
  {id:"progression",file:"progression-parity.log",prefix:"KGG_PROGRESSION_PARITY_PASS ",
   featureIds:["PAT-PROGRESSION-001","PAT-PROGRESSION-002"],
   required:["threeStages","thumbnailSelection","swipeAndClick","zeroValue",
     "dominance","qrMarker","historyNote"]},
  {id:"scannerfallback",file:"scanner-fallback-parity.log",prefix:"KGG_SCAN_FALLBACK_PARITY_PASS ",
   featureIds:["PAT-SCAN-001","PAT-SCAN-003","PAT-SCAN-004"],
   required:["denied","retry","photoChooser","invalidCodeSafe",
     "validLinkUpdate","reload","noPlanRescue"]},
  {id:"firstload",file:"firstload-parity.log",jsonLine:true,
   featureIds:["PAT-PWA-002","PAT-THUMB-001","PAT-MEDIA-009"],
   required:["serviceWorkerBlocked","freshRootNoReload","scannerLoadedOnce",
     "progressCheckedForAllFields","redXPlanDeletionChecked",
     "localThumbnailGeometryChecked","mediaLightboxChecked"]}
];
function required(ok,message){if(!ok)throw new Error(message)}
function boundedText(file){
  const stat=fs.lstatSync(file);
  required(stat.isFile()&&!stat.isSymbolicLink()&&stat.size>0&&stat.size<=2_000_000,
    "Invalid synthetic log: "+path.basename(file));
  return fs.readFileSync(file,"utf8");
}
function structuredRows(def,content){
  const lines=content.split(/\r?\n/);
  if(def.jsonLine){
    return lines.filter(line=>line.startsWith("{")).map(line=>{
      const value=JSON.parse(line);
      return value && value.status==="PASS" && value.mode ? value : null;
    }).filter(Boolean);
  }
  return lines.filter(line=>line.startsWith(def.prefix)).map(line=>JSON.parse(line.slice(def.prefix.length)));
}
export function collectProofs(output,definitions=DEFINITIONS){
  const dir=path.resolve(output);
  required(path.basename(dir)==="patient-ui-parity","Evidence output must end in patient-ui-parity");
  const report=JSON.parse(boundedText(path.join(dir,"report.json")));
  const engine=report.engine,sha=report.candidateSha;
  required(report.syntheticOnly===true&&["chromium","webkit"].includes(engine)&&SHA.test(String(sha||"")),
    "Missing valid synthetic core parity report/engine/candidate SHA");
  const proofs=[];
  for(const def of definitions){
    const file=path.join(dir,def.file);
    const values=structuredRows(def,boundedText(file));
    required(values.length===MODES.length,def.id+" expected exactly 3 browser mode successes, got "+values.length);
    for(const mode of MODES){
      const matches=values.filter(v=>v?.mode===mode);
      required(matches.length===1,def.id+" missing/duplicate PASS for "+mode);
      const item=matches[0];
      required(item.engine===engine&&item.sourceSha===sha,
        def.id+" wrong browser or stale source SHA: "+mode);
      if(def.jsonLine)required(item.status==="PASS",def.id+" status not PASS for "+mode);
      const assertions={};
      for(const key of def.required){
        required(item[key]===true,def.id+" nonpassing assertion "+key+" in "+mode);
        assertions[key]=true;
      }
      if(def.id==="firstload"){
        required(Number.isInteger(item.directFirstLoadModules)&&item.directFirstLoadModules>=27,
          "First-load module count missing/invalid for "+mode);
        assertions.directModulesAtLeast27=true;
      }
      proofs.push({name:def.id+"-"+mode+".json",data:{
        schema:1,syntheticOnly:true,sourceSha:sha,engine,mode,
        status:"PASS",featureIds:def.featureIds,assertions
      }});
    }
  }
  return {engine,sha,proofs,groupCount:definitions.length};
}
export function writeProofs(output){
  const {engine,sha,proofs,groupCount}=collectProofs(output);
  // Only write after *all* individual proofs have been validated.
  for(const proof of proofs){
    fs.writeFileSync(path.join(output,proof.name),JSON.stringify(proof.data,null,2)+"\n");
  }
  fs.writeFileSync(path.join(output,"additional-proofs-index.json"),
    JSON.stringify({schema:1,syntheticOnly:true,sourceSha:sha,engine,
      groups:groupCount,modes:MODES,proofFiles:proofs.map(x=>x.name)},null,2)+"\n");
  return {engine,sha,groups:groupCount,proofFiles:proofs.length};
}
const current=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(current){
  try{
    required(process.argv.length===3,"Usage: kgg_patient_unified_extra_proofs.mjs PATH_TO_patient-ui-parity");
    console.log("KGG extra browser proofs PASS "+JSON.stringify(writeProofs(path.resolve(process.argv[2]))));
  }catch(error){
    console.error("KGG extra browser proofs FAIL: "+(error.stack||error));
    process.exitCode=1;
  }
}
