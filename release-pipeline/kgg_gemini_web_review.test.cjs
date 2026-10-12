"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs");
const os=require("node:os"),path=require("node:path"),crypto=require("node:crypto");
const {spawnSync}=require("node:child_process");
const script=path.join(__dirname,"kgg_gemini_web_review.cjs");
const sha="a".repeat(40);
const STEPS=["pair-kg","pair-wdh","remaining-kg","pair-complete","manual-zero","cancelled","saved-zero","center-complete","lr-left","lr-right","seconds-complete","reloaded"];
const COUNTS={"independent-fixture":48,"state:day":24,"state:done":24,"state:values":24,"state:inputs":24,"state:padOpen":24,"state:field":24,"state:draft":24,"state:dirty":24,"state:transfer":24,"state:visibleMatchesLegacy":24,"state:fixture":24,"scroll-base:windowY":20,"scroll-base:mainTop":20,"geometry:keys":8,"pixel:keys":8,"geometry:actions":8,"pixel:actions":8,"scroll-jump:windowY":4,"scroll-jump:mainTop":4};
function fixture(){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),"kgg-gemini-web-proof-"));
  const steps=Object.fromEntries(STEPS.map((s,i)=>[s,{elapsedMs:i*400}]));
  const checks=Object.entries(COUNTS).flatMap(([kind,n])=>Array.from({length:n},()=>kind.startsWith("scroll-base:")?
    {kind,pass:null,policy:"OBSERVATION ONLY: different card phase"}:{kind,pass:true}));
  const variants=["phone:legacy","phone:react","tablet:legacy","tablet:react"].map(pair=>{
    const [viewport,mode]=pair.split(":");
    return {viewport,mode,steps,oracle:STEPS.map(step=>({step,pass:true})),consoleErrors:[]};
  });
  const report={schema:2,status:"PASS",syntheticOnly:true,engine:"chromium",
    candidateSha:sha,gitSha:"b".repeat(40),motionMode:"normal",
    steps:STEPS,recordings:["phone-legacy.webm","phone-react.webm","tablet-legacy.webm","tablet-react.webm"],
    unexpectedDifferences:[],variants,checks};
  fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report));
  const ebml=Buffer.alloc(128);Buffer.from([0x1a,0x45,0xdf,0xa3]).copy(ebml);
  fs.writeFileSync(path.join(dir,"phone-legacy.webm"),ebml);
  fs.writeFileSync(path.join(dir,"phone-react.webm"),Buffer.concat([ebml,Buffer.from([1,2,3])]));
  return {dir,report};
}
function call(cmd,dir,extra={}){
  const env={...process.env,...extra};
  delete env.KGG_GEMINI_EXPECTED_SOURCE_SHA;
  return spawnSync(process.execPath,[script,cmd,dir],{env:{...env,...extra},encoding:"utf8",timeout:5000});
}
const read=(dir,name)=>JSON.parse(fs.readFileSync(path.join(dir,name),"utf8"));
function observation(m,overrides={}){
  return {
    schema:1,provider:"gemini-web",status:"COMPLETE",nonce:m.nonce,
    scenario:m.scenario,sourceSha:m.sourceSha,reportSha256:m.reportSha256,
    videos:{legacySha256:m.videos[0].sha256,reactSha256:m.videos[1].sha256},
    pageUrl:"https://gemini.google.com/app",uploadsVerified:true,generationObserved:true,
    completionStable:true,modelLabel:"3.1 Pro Erweitert",
    modelVerified:true,thinkingVerified:true,
    responseText:JSON.stringify({
      verdict:"no_unexpected_difference",confidence:"medium",
      expectedDifferences:["React header"],findings:[]
    }),...overrides
  };
}
function withProof(fn){
  const {dir,report}=fixture();
  try{return fn(dir,report);}finally{fs.rmSync(dir,{recursive:true,force:true});}
}
test("trusted deterministic 352/40 report prepares but never uploads",()=>withProof(dir=>{
  const r=call("prepare",dir);assert.equal(r.status,0,r.stderr);
  const p=read(dir,"gemini-web-prepare.json");
  assert.equal(p.sourceSha,sha);
  assert.equal(p.checkoutSha,"b".repeat(40)); // checkout SHA is not candidate SHA
  assert.equal(p.hardPassCount,352);assert.equal(p.observedOnlyCount,40);
  assert.equal(p.uploadApproved,false);assert.equal(p.videos.length,2);
}));
test("single passing check cannot counterfeit a complete parity proof",()=>withProof((dir,report)=>{
  report.checks=[{kind:"independent-fixture",pass:true}];
  fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report));
  const r=call("prepare",dir);assert.notEqual(r.status,0);
  assert.equal(fs.existsSync(path.join(dir,"gemini-web-prepare.json")),false);
}));
test("requested SHA, observations and errors are fail-closed",()=>withProof((dir,report)=>{
  assert.notEqual(call("prepare",dir,{KGG_GEMINI_EXPECTED_SOURCE_SHA:"c".repeat(40)}).status,0);
  report.checks.find(x=>x.pass===null).pass=true;
  fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report));
  assert.notEqual(call("prepare",dir).status,0);
}));
test("missing login/upload/generation evidence never produces REVIEWED",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);
  const p=read(dir,"gemini-web-prepare.json");
  fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p,{uploadsVerified:false})));
  assert.notEqual(call("finalize",dir).status,0);
  assert.equal(read(dir,"gemini-web-review.json").status,"UNAVAILABLE");
}));
test("wrong nonce, candidate and video hashes are rejected",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);const p=read(dir,"gemini-web-prepare.json");
  for(const change of [{nonce:"fake"},{sourceSha:"e".repeat(40)},{videos:{legacySha256:"wrong",reactSha256:p.videos[1].sha256}}]){
    fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p,change)));
    assert.notEqual(call("finalize",dir).status,0);
  }
}));
test("real video bytes cannot drift after prepare",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);const p=read(dir,"gemini-web-prepare.json");
  fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p)));
  fs.appendFileSync(path.join(dir,"phone-react.webm"),Buffer.from([9]));
  assert.notEqual(call("finalize",dir).status,0);
}));
test("contradictory Gemini clean verdict is rejected",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);const p=read(dir,"gemini-web-prepare.json");
  const responseText=JSON.stringify({verdict:"no_unexpected_difference",confidence:"high",
    expectedDifferences:[],findings:[{step:"pair-wdh",severity:"major",
      timestampLegacy:"00:03",timestampReact:"00:04",description:"Pad vanished"}]});
  fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p,{responseText})));
  assert.notEqual(call("finalize",dir).status,0);
}));
test("untrusted page origin and unverifiable Pro selection are rejected",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);const p=read(dir,"gemini-web-prepare.json");
  for(const change of [{pageUrl:"https://example.com"},{modelLabel:"Flash",modelVerified:true},
    {thinkingVerified:false}]){
    fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p,change)));
    assert.notEqual(call("finalize",dir).status,0);
  }
}));
test("valid observed response creates ADVISORY reviewed result, never a release pass",()=>withProof(dir=>{
  assert.equal(call("prepare",dir).status,0);const p=read(dir,"gemini-web-prepare.json");
  fs.writeFileSync(path.join(dir,"gemini-web-response.json"),JSON.stringify(observation(p)));
  const r=call("finalize",dir);assert.equal(r.status,0,r.stderr);
  const review=read(dir,"gemini-web-review.json");
  assert.equal(review.status,"REVIEWED");
  assert.equal(review.verdict,"no_unexpected_difference");
  assert.equal(review.releaseApproved,false);
  assert.equal(review.advisoryOnly,true);
  assert.equal(review.sourceSha,sha);
}));
