'use strict';
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../kgg-update/src/patches/v061-cross-app-live-qr-camera.html'),'utf8');
const begin=source.indexOf('  async function preferMinimumCameraZoom(stream){');
const end=source.indexOf('\n  function ensureUi(){',begin);
assert(begin>=0&&end>begin,'camera zoom helper missing');
const snippet=source.slice(begin,end).trim();
const zoomFn=vm.runInNewContext('('+snippet+')');
assert(source.includes('await video.play();\n      void preferMinimumCameraZoom(stream);'),'zoom helper not called after video start');
assert(source.includes('object-fit:contain'),'camera preview should retain full-frame fit');
assert(!source.includes('zoom:{exact:'),'zoom must not be required at getUserMedia start');
async function check(name,capabilities,settings,expected,reject=false){
  const calls=[];
  const track={
    getCapabilities(){if(capabilities instanceof Error)throw capabilities;return capabilities;},
    getSettings(){return settings;},
    async applyConstraints(input){const normalized=JSON.parse(JSON.stringify(input));calls.push(normalized);if(reject)throw Error('denied');}
  };
  await zoomFn({getVideoTracks(){return [track];}});
  assert.equal(calls.length,expected===null?0:1,name+' call count');
  if(expected!==null)assert.deepEqual(calls[0],{advanced:[{zoom:expected}]},name+' target');
  process.stdout.write('PASS '+name+'\n');
}
(async()=>{
  await check('3x to 1x',{zoom:{min:1,max:8,step:0.1}},{zoom:3},1);
  await check('1x to 0.5x',{zoom:{min:0.5,max:4,step:0.1}},{zoom:1},0.5);
  await check('minimum already active',{zoom:{min:1,max:8}},{zoom:1},null);
  await check('unsupported zoom',{width:{min:640,max:1920}},{zoom:2},null);
  await check('missing zoom setting',{zoom:{min:1,max:8}},{width:1280},null);
  await check('invalid minimum',{zoom:{min:-1,max:8}},{zoom:2},null);
  await check('capabilities throw',new Error('unsupported'),{zoom:2},null);
  await check('permission denied is nonfatal',{zoom:{min:1,max:8}},{zoom:2},1,true);
  await zoomFn({getVideoTracks(){return [];}});
  await zoomFn(null);
  process.stdout.write('PASS no track and null stream are nonfatal\n');
  process.stdout.write('PASS source and no mandatory zoom invariants\n');
})().catch(e=>{console.error('FAIL',e);process.exitCode=1;});
