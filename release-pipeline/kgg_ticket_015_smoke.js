#!/usr/bin/env node
'use strict';

// Ticket 015 contract smoke: deterministic variant wire format and patient rules.
// This test is local/static only. It does not open a browser, read secrets or write GitHub.

const fs=require('fs');
const path=require('path');
const vm=require('vm');

const ROOT=path.resolve(__dirname,'..');
const ADMIN_PATH=path.join(ROOT,'kgg-update','src','patches','v085-ticket-015-progressions.html');
const PATIENT_PATH=path.join(ROOT,'patient-set-summary-groups.js');
const MEDIA_PATH=path.join(ROOT,'patient-media-retry-cache_v2.js');

function fail(message){throw new Error(message)}
function assert(condition,message){if(!condition)fail(message)}
function scriptBody(file){return fs.readFileSync(file,'utf8').replace(/^[\s\S]*?<script[^>]*>/i,'').replace(/<\/script>[\s\S]*$/i,'')}

function runAdminSmoke(){
  const source=scriptBody(ADMIN_PATH);
  assert(!source.includes('KGG_PATIENT_AUTOMATION_TOKEN'),'forbidden patient automation token is referenced');
  assert(!source.includes('github.token'),'snapshot patch unexpectedly references github.token');
  const window={__KGG_TEST__:true};
  const document={readyState:'complete',head:null,getElementById(){return null},querySelector(){return null},addEventListener(){}};
  const context={window,document,console,setTimeout(){},clearTimeout(){},bank:[],state:{plan:[]},ensureExerciseMediaList(ex){return Array.isArray(ex&&ex.media)?ex.media:[]}};
  window.document=document;window.window=window;
  window.compactKggH2Exercise=ex=>[ex.name||'Basis','','','','','','','','','',ex.painMode||'exercise'];
  window.expandKggH2Exercise=item=>({name:item&&item[0]||'Basis'});
  window.buildPatientExercisePayload=ex=>({...ex});
  context.globalThis=context;
  vm.createContext(context);
  vm.runInContext(source,context,{filename:ADMIN_PATH});
  const api=window.__kggTicket015AdminTest;
  assert(api,'admin Ticket 015 test API missing');
  const exercise={localId:'ex-1',name:'Basis',media:[{id:'base-image',type:'image'}],progressionVariants:[
    {id:'base',name:'Basis',order:0,media:[{id:'base-image',type:'image'}]},
    {id:'hard',name:'Schwerer',order:1,media:[{id:'hard-image',type:'image'}]},
  ]};
  const normalized=api.normalizeVariants(exercise,false);
  assert(normalized.length===2,'admin normalization lost a progression stage');
  assert(normalized[0].order===0&&normalized[1].order===1,'admin progression order is not stable');
  const wire=api.wireVariants(exercise);
  assert(wire&&wire.g&&wire.v.length===2,'admin wire format is incomplete');
  assert(wire.v[1].i==='hard'&&wire.v[1].o===1,'admin wire format lost stable id/order');
  const row=window.compactKggH2Exercise(exercise);
  assert(row[10]==='exercise','existing painMode slot was overwritten');
  assert(row[11]&&row[11].g===wire.g,'KGGH2 optional progression field was not appended in the reserved-free slot');
  const expanded=window.expandKggH2Exercise(row);
  assert(expanded.progressionVariants&&expanded.progressionVariants.length===2,'KGGH2 roundtrip lost progressions');
  assert(window.buildPatientExercisePayload(exercise).progressionVariants.length===2,'patient payload omitted progressions');
  const used=new Set(['pv_group-1_0','pv_group-1_2']);
  assert(api.allocateVariantId('group-1','',2,used)!=='pv_group-1_2','progression id allocator recreated an existing id');
  const appCore=fs.readFileSync(path.join(ROOT,'kgg-update','src','runtime','app-core.html'),'utf8');
  assert(appCore.includes('allExerciseMediaList'),'progression media is not included in the shared media collector');
  assert(appCore.includes('progressionSelection'),'KGGD1 progression selection is not carried into therapist scan parsing');
}

function runPatientSmoke(){
  const source=fs.readFileSync(PATIENT_PATH,'utf8');
  const sum={textContent:''};
  const storage=new Map();
  const context={
    console,
    window:{__KGG_TEST__:true},
    document:{readyState:'complete',head:null,getElementById(id){return id==='sum'?sum:null},querySelectorAll(){return []},addEventListener(){}},
    localStorage:{getItem(key){return storage.has(key)?storage.get(key):null},setItem(key,value){storage.set(key,String(value))}},
    setTimeout(){return 0},clearTimeout(){},showQr(){},
  };
  context.window.window=context.window;context.window.document=context.document;context.window.localStorage=context.localStorage;context.globalThis=context;
  vm.createContext(context);vm.runInContext(source,context,{filename:PATIENT_PATH});
  const api=context.window.__kggTicket015PatientTest;
  assert(api,'patient Ticket 015 test API missing');
  const values=[
    api.normalizeVariant({id:'easy',name:'Leichter',order:0},0,'group-1',[]),
    api.normalizeVariant({id:'base',name:'Basis',order:1},1,'group-1',[]),
    api.normalizeVariant({id:'hard',name:'Schwerer',order:2},2,'group-1',[]),
  ];
  assert(api.dominant(values,{a:{id:'base'},b:{id:'hard'},c:{id:'hard'},d:{id:'base'}}).id==='hard','dominant stage did not choose the higher stage on a tie');
  assert(api.note('Basis','Basis','Übung')==='','documentation note was emitted without a real change');
  assert(api.note('Basis','Schwerer','Übung')==='Übung: Basis → Schwerer','real progression change was not documented');
}

function runMediaContract(){
  const source=fs.readFileSync(MEDIA_PATH,'utf8');
  assert(source.includes('loadMedia(item,exerciseIndex,mediaIndex,targetId)'),'media loader does not support progression targets');
  assert(source.includes('data-kgg-progression-media'),'progression media target selector is missing');
  assert(source.includes('loadMedia,retryMedia'),'media loader is not exposed for the progression gallery');
}

runAdminSmoke();
runPatientSmoke();
runMediaContract();
console.log('Ticket 015 progression smoke: OK');
