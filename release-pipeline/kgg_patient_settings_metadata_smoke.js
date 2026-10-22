'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'kgg_exercise_primary_names_smoke.js'),'utf8').replace(/^#!.*\r?\n/,'');
const {patient,raw}=new Function('require','__dirname',source.slice(0,source.indexOf('const tests=[];'))+';return {patient,raw};')(require,__dirname);
const fixture=raw(['Einbeinstand'],{Einbeinstand:'Single-leg stance'});
fixture.m.exerciseNamesEn={Einbeinstand:'Authored English'};fixture.sourcePlanId='synthetic-source';
fixture.e[0][11]={k:'kgg015',g:'synthetic-stage-group',a:'easy',v:[{i:'easy',n:'Leicht',o:0}]};fixture.e[0][12]={syntheticFutureMetadata:'keep'};
const env=patient(fixture);env.run("p.ex[0].painMode='set';p.ex[0].u='keine';");
const settings=fs.readFileSync(path.join(__dirname,'../patient-card-settings.js'),'utf8');
function production(name){const start=settings.indexOf('  function '+name+'('),end=settings.indexOf('\n  function ',start+12);assert(start>=0);return settings.slice(start,end<0?settings.length:end);}
vm.runInContext("(()=>{const PLAN_KEY='kggCurrentPlanV1',safe=f=>f(),getPainMode=()=> 'exercise';"+production('rawPlan')+production('storePlan')+';window.__storeSettingsMetadata=storePlan;})()',env.context);
env.run('__storeSettingsMetadata()');const saved=env.stored();
assert.deepEqual(saved.m,fixture.m,'settings save dropped English/primary metadata');
assert.deepEqual(saved.e[0][11],fixture.e[0][11],'settings save dropped progression tuple');assert.deepEqual(saved.e[0][12],fixture.e[0][12],'settings save dropped future tuple tail');
assert.equal(saved.sourcePlanId,'synthetic-source');assert.equal(saved.e[0][10],'set');assert.equal(saved.e[0][3],'keine');
console.log('Patient settings metadata PASS: actual save preserves meta/tuple tails while applying pain/unit choices');
