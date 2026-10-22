#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict'),cp=require('child_process');
const source=fs.readFileSync(path.join(__dirname,'../kgg-update/src/runtime/app-core.html'),'utf8');
function realFunction(name,text=source){const start=text.indexOf('  function '+name+'(');assert(start>=0,'real production function missing: '+name);const end=text.indexOf('\n  function ',start+12);return text.slice(start,end<0?text.length:end)}
const context={window:{},URL,lastPatientMediaBundleManifest:null,MEDIA_UPLOAD_TTL_SECONDS:900,MEDIA_RETRY_SECONDS:300,ensureExerciseMediaList:ex=>ex.media||[]};
vm.createContext(context);
for(const name of ['patientExerciseDisplayName','patientPrimaryNames','buildPatientPrimaryNames','normalizeSideMode','normalizeSetCount','buildExerciseMediaManifestForPatient','compactKggH2Exercise','buildKggH2PayloadFromPlan','buildKggH3PayloadFromPlan'])vm.runInContext(realFunction(name),context);
if(source.includes('function buildPatientEnglishNames('))vm.runInContext(realFunction('buildPatientEnglishNames'),context);
const ex={name:'Eigene Übung (links)',nameEn:'My exercise (left)',sets:3,side:'LR',weightUnit:'kg',unit:'Wdh',startLoad:'20',startMetric:'12',media:[],painMode:'set',progressionVariants:[{name:'Eigene Stufe',nameEn:'My stage'}]};
const raw=context.buildKggH2PayloadFromPlan({id:'synthetic',title:'Synthetic',days:6},[ex],{},null);
assert.ok(raw.m.exerciseNamesEn,'authored English labels missing from compatible metadata');
assert.deepEqual(JSON.parse(JSON.stringify(raw.m.exerciseNamesEn)),{'Eigene Übung (links)':'My exercise (left)','Eigene Stufe':'My stage'},'authored English labels are missing from compatible metadata');
assert.deepEqual(Array.from(raw.e[0]),['Eigene Übung (links)',3,'LR','kg','Wdh','20','12','','','Video öffnen','set'],'English metadata changed existing canonical tuple');
assert.equal(raw.m.schema,'KGGH2');assert.equal(context.buildKggH3PayloadFromPlan({},[ex],{},null).m.schema,'KGGH3');
assert.throws(()=>context.buildKggH2PayloadFromPlan({},[ex,{...ex,nameEn:'Conflicting label'}],{},null),/englisch|Englisch/,'conflicting names must stop export clearly');
const old=context.buildKggH2PayloadFromPlan({},[{...ex,nameEn:'',progressionVariants:[]}],{},null);assert.equal(old.m.exerciseNamesEn,undefined,'empty optional map should not change old payloads');
const invalid=context.buildKggH2PayloadFromPlan({},[{...ex,nameEn:123,progressionVariants:[]}],{},null);assert.equal(invalid.m.exerciseNamesEn,undefined,'non-string metadata must not become display labels');
console.log('English metadata smoke: PASS (exact DE identity, authored EN, conflicting export blocked, old tuple/schema preserved)');
// Actual shared-bank sender/receiver: absence is legacy, empty string is an explicit clear.
Object.assign(context,{bank:[{id:'custom',name:'Eigene Übung',nameEn:'Old label',aliases:'Eigene Übung',sets:3,unit:'Wdh',weightUnit:'kg',updatedAt:'2026-10-13T00:00:00Z'}],compact:s=>String(s).toLowerCase().replace(/\s+/g,''),normalizeLoadUnit:s=>s,deletedBankIds:new Set(),persistDeletedBankIds(){return true;},persistCustomBank(){return true;},render(){}});
for(const name of ['normalizeMeasureMode','nativeSyncMediaRefs','nativeSyncVideoUrl','nativeSyncLibraryFields','nativeSyncRevision','nativeLibraryFingerprint','compareNativeLibraryRevision','sanitizeSharedBankExercise','parseSharedExerciseBankPayload','mergeSharedExerciseBank','syncTimestamp'])vm.runInContext(realFunction(name),context);
const shared={id:'custom',name:'Eigene Übung',aliases:'Eigene Übung',sets:3,unit:'Wdh',weightUnit:'kg',updatedAt:'2026-10-14T00:00:00Z'};
context.mergeSharedExerciseBank({exercises:[shared]});assert.equal(context.bank[0].nameEn,'Old label','legacy absence must preserve English label');
const clear=context.sanitizeSharedBankExercise({...shared,nameEn:'',updatedAt:'2026-10-15T00:00:00Z'});assert.equal(clear.nameEn,'','explicit English clear disappeared on export');context.mergeSharedExerciseBank({exercises:[clear]});assert.equal(context.bank[0].nameEn,'','shared-bank receiver retained explicitly cleared label');
assert.equal(context.bank[0].name,shared.name);assert.equal(context.bank[0].unit,'Wdh');assert.equal(context.bank[0].weightUnit,'kg');
context.mergeSharedExerciseBank({exercises:[{...shared,nameEn:'New label',updatedAt:'2026-10-16T00:00:00Z'}]});assert.equal(context.bank[0].nameEn,'New label');
console.log('English shared-bank smoke: PASS (explicit clear vs legacy absence, canonical fields preserved)');
context.bank[0].nameDe='Gepflegter deutscher Name';
context.mergeSharedExerciseBank({exercises:[shared]});assert.equal(context.bank[0].nameDe,'Gepflegter deutscher Name','legacy absence cleared German label');
for(const invalid of [123,null,{},'x'.repeat(201),'bad\nlabel']){context.mergeSharedExerciseBank({exercises:[{...shared,nameDe:invalid,updatedAt:'2026-10-17T00:00:00Z'}]});assert.equal(context.bank[0].nameDe,'Gepflegter deutscher Name','invalid DE metadata cleared label');}
context.mergeSharedExerciseBank({exercises:[{...shared,nameDe:'Neuer deutscher Name',updatedAt:'2026-10-18T00:00:00Z'}]});assert.equal(context.bank[0].nameDe,'Neuer deutscher Name','shared/native sanitizer lost DE');
context.mergeSharedExerciseBank({exercises:[{...shared,nameDe:'',updatedAt:'2026-10-19T00:00:00Z'}]});assert.equal(context.bank[0].nameDe,'','explicit DE clear was lost');
console.log('German shared-bank smoke: PASS (new/absent/empty/invalid, canonical name preserved)');
Object.assign(context,{document:{readyState:'loading',addEventListener(){},getElementById(){return null}},setTimeout(){return 0}});
context.window.KGGTicket015PatientMedia={manifest:context.buildExerciseMediaManifestForPatient};
for(const file of ['v085-ticket-015-progressions.html','v090-ticket-015-admin-stage-gallery-drag-motion.html']){const html=fs.readFileSync(path.join(__dirname,'../kgg-update/src/patches',file),'utf8');vm.runInContext(html.match(/<script[^>]*>([\s\S]*?)<\/script>/)[1],context)}
const legacy=cp.execFileSync('git',['show','f59bc55:kgg-update/src/runtime/app-core.html'],{cwd:path.join(__dirname,'..'),encoding:'utf8',maxBuffer:3000000});vm.runInContext(realFunction('compactKggH2Exercise',legacy).replace('function compactKggH2Exercise(','function legacyCompact('),context);
const noVariants={...ex,progressionVariants:[]};assert.equal(JSON.stringify(context.compactKggH2Exercise(noVariants)),JSON.stringify(context.legacyCompact(noVariants)),'no-variant tuple changed baseline bytes');
const stages={...ex,progressionGroupId:'exact-g',progressionMainId:'stage-2',progressionVariants:[{id:'stage-1',name:'Eigene Stufe',nameEn:'My stage',media:[]},{id:'stage-2',name:'Andere Stufe',media:[]}]},row=context.compactKggH2Exercise(stages);assert.equal(JSON.stringify(row.slice(0,11)),JSON.stringify(context.legacyCompact(stages)),'companion changed existing tuple0..10');assert.equal(row[11].g,'exact-g');assert.equal(row[11].a,'stage-2');assert.equal(row[11].v[0].n,'Eigene Stufe');assert.equal(row[11].v[0].i,'stage-1');assert.equal(row[11].v[0].nameEn,undefined,'English label leaked into progression wire');
const fallback=context.compactKggH2Exercise({...stages,progressionMainId:'invalid-id'});assert.equal(fallback[11].a,'stage-1','main fallback must use existing transmitted ID');
const germanStages={...stages,nameDe:'Eigene Übung Deutsch',progressionVariants:[{...stages.progressionVariants[0],nameDe:'Eigene Stufe Deutsch'},stages.progressionVariants[1]]};assert.equal(context.window.KGGTicket015Admin.normalizeVariants(germanStages,false)[0].nameDe,'Eigene Stufe Deutsch');assert.equal(context.window.KGGTicket015AdminGallery.normalizeVariants(germanStages,false)[0].nameDe,'Eigene Stufe Deutsch');
console.log('English fresh-tuple companion smoke: PASS (existing serializer reused, no-variant byte identity, tuple0..10 unchanged, DE g/a/v and valid fallback)');
