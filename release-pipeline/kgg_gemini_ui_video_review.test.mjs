import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';

const script=fileURLToPath(new URL('./kgg_gemini_ui_video_review.mjs',import.meta.url));
const sha='a'.repeat(40);
const success={verdict:'no_unexpected_difference',confidence:'high',expectedDifferences:['New header style'],findings:[]};
function run({key='',approved=false,response=success,report={},http=200,throwNetwork=false}={}){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'kgg-gemini-unit-'));
 const base={schema:2,syntheticOnly:true,status:'PASS',engine:'chromium',candidateSha:sha,gitSha:sha,checks:[{pass:true}],...report};
 fs.writeFileSync(path.join(dir,'report.json'),JSON.stringify(base));
 for(const name of ['phone-legacy.webm','phone-react.webm'])fs.writeFileSync(path.join(dir,name),Buffer.from([26,69,223,163,0,1,2,3]));
 const mock=path.join(dir,'mock-fetch.mjs');
 fs.writeFileSync(mock,`import fs from 'node:fs';
 globalThis.fetch=async (url,options)=>{
  fs.writeFileSync(${JSON.stringify(path.join(dir,'request-called'))},'yes');
  if(${JSON.stringify(throwNetwork)})throw new Error('secret-token-must-not-appear');
  const body=JSON.parse(options.body);const videos=body.contents[0].parts.filter(p=>p.inlineData);
  if(videos.length!==2||videos.some(p=>p.videoMetadata?.fps!==5))throw new Error('expected 5 FPS for both videos');
  return {ok:${http>=200&&http<300},status:${http},json:async()=>({candidates:[{content:{parts:[{text:${JSON.stringify(JSON.stringify(response))}}]}}]})};
 };`);
 const env={...process.env,GEMINI_API_KEY:key,KGG_GEMINI_VIDEO_UPLOAD_APPROVED:approved?'true':'false',KGG_GEMINI_EXPECTED_SOURCE_SHA:sha};
 delete env.GITHUB_STEP_SUMMARY;delete env.GOOGLE_API_KEY;
 const child=spawnSync(process.execPath,['--import',pathToFileURL(mock).href,script,dir],{env,encoding:'utf8',timeout:12000});
 const result=fs.existsSync(path.join(dir,'gemini-review.json'))?JSON.parse(fs.readFileSync(path.join(dir,'gemini-review.json'),'utf8')):{};
 const called=fs.existsSync(path.join(dir,'request-called'));fs.rmSync(dir,{recursive:true,force:true});
 return {result,called,code:child.status,output:child.stdout+child.stderr};
}

test('no key is NOT_CONFIGURED and never sends a request',()=>{
 const r=run();assert.equal(r.result.status,'NOT_CONFIGURED');assert.equal(r.called,false);assert.equal(r.code,0);
});
test('a key alone never authorizes an upload',()=>{
 const r=run({key:'fake-unit-key'});assert.equal(r.result.status,'UPLOAD_NOT_APPROVED');assert.equal(r.called,false);
});
test('approved valid request sends two 5-FPS videos and records real reviewer result',()=>{
 const r=run({key:'fake-unit-key',approved:true});assert.equal(r.result.status,'REVIEWED');assert.equal(r.result.verdict,'no_unexpected_difference');assert.equal(r.result.samplingFps,5);assert.equal(r.called,true);assert.equal(r.code,0);
});
test('source mismatch is rejected before network',()=>{
 const r=run({key:'fake-unit-key',approved:true,report:{candidateSha:'b'.repeat(40)}});assert.equal(r.result.status,'ERROR');assert.equal(r.called,false);assert.notEqual(r.code,0);
});
test('failed parity cannot be sent to Gemini as an acceptance pass',()=>{
 const r=run({key:'fake-unit-key',approved:true,report:{status:'FAIL'}});assert.equal(r.result.status,'ERROR');assert.equal(r.called,false);
});
test('no-difference verdict contradicting a major finding is rejected',()=>{
 const r=run({key:'fake-unit-key',approved:true,response:{...success,findings:[{step:'pair-wdh',timestampLegacy:'00:03',timestampReact:'00:04',severity:'major',description:'NumPad closed'}]}});assert.equal(r.result.status,'ERROR');assert.notEqual(r.code,0);
});
test('malformed finding cannot silently become a minor issue',()=>{
 const r=run({key:'fake-unit-key',approved:true,response:{...success,verdict:'suspected_regression',findings:[null]}});assert.equal(r.result.status,'ERROR');assert.notEqual(r.code,0);
});
test('HTTP error is not a visual pass and does not include response body',()=>{
 const r=run({key:'fake-unit-key',approved:true,http:429});assert.equal(r.result.status,'ERROR');assert.notEqual(r.code,0);assert.match(r.output,/429/);
});
test('transport errors never echo potentially secret-bearing messages',()=>{
 const r=run({key:'fake-unit-key',approved:true,throwNetwork:true});assert.equal(r.result.status,'ERROR');assert.ok(!JSON.stringify(r).includes('secret-token-must-not-appear'));
});
