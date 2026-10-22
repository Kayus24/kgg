#!/usr/bin/env node
'use strict';

// Synthetic, local transport/import checks. No camera, network, keys or browser.
// Removing provenance transport or matching by a mutable display name must fail.
const fs=require('fs'),path=require('path'),vm=require('vm'),cp=require('child_process'),assert=require('assert/strict');
const ROOT=path.resolve(__dirname,'..'),BASE='a237aa2a9737a5b83eb6bb069f820cb8ce8653fd';
const html=fs.readFileSync(path.join(ROOT,'index.html'),'utf8');
const inline=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(hit=>hit[1]).find(code=>code.includes('let p,d=1,v={}'));
assert.ok(inline,'patient inline application missing');
const clone=value=>JSON.parse(JSON.stringify(value));
const code=raw=>'KGGH2:'+Buffer.from(JSON.stringify(raw)).toString('base64url');
const returnCode=raw=>'KGGD1:'+Buffer.from(JSON.stringify(raw)).toString('base64url');
const decoded=payload=>JSON.parse(Buffer.from(payload.replace(/^KGGD1:/,''),'base64url').toString('utf8'));
const row=(name,media='')=>[name,1,'B','kg','Wdh','','',media,'','Video öffnen','exercise'];
function raw(names,map){const out={v:1,i:'synthetic-primary-plan',t:'Synthetic',d:6,e:names.map(name=>row(name))};if(map!==undefined)out.m={exercisePrimaryNames:map};return out;}

function patient(plan,progressions=false){
  const elements=new Map(),events={alerts:[],status:[],reloads:0};
  function element(id){if(!elements.has(id))elements.set(id,{id,textContent:'',innerHTML:'',dataset:{},style:{},classList:{add(){},remove(){},contains(){return false},toggle(){}},scrollIntoView(){},querySelector(){return null},querySelectorAll(){return []},setAttribute(){},appendChild(){}});return elements.get(id);}
  const storage={getItem(key){return Object.hasOwn(this,key)?this[key]:null},setItem(key,value){this[key]=String(value)},removeItem(key){delete this[key]}};
  storage.setItem('kggCurrentPlanV1',JSON.stringify({plan:clone(plan)}));
  const context={console,Buffer,URL,URLSearchParams,TextEncoder,TextDecoder,Uint8Array,Date,Math,JSON,Array,Object,String,Number,Map,Set,Error,RegExp,unescape,escape,encodeURIComponent,decodeURIComponent,
    localStorage:storage,navigator:{},location:{origin:'https://synthetic.test',pathname:'/',href:'https://synthetic.test/',search:'',hash:'',reload(){events.reloads++}},
    document:{readyState:'loading',head:null,body:null,getElementById:element,querySelector(){return null},querySelectorAll(){return []},addEventListener(){}},
    setTimeout(){return 0},clearTimeout(){},setInterval(){return 0},clearInterval(){},matchMedia(){return {matches:false}},addEventListener(){},dispatchEvent(){},
    btoa:value=>Buffer.from(value,'binary').toString('base64'),atob:value=>Buffer.from(value,'base64').toString('binary'),alert:value=>events.alerts.push(String(value)),confirm:()=>true};
  context.window=context;context.globalThis=context;
  vm.createContext(context);
  vm.runInContext(inline.replace(/load\(\);\s*$/,''),context,{filename:'index.html#actual-inline'});
  context.fixture=clone(plan);
  vm.runInContext("p={id:fixture.i,title:fixture.t,version:fixture.v,days:fixture.d,extendDays:true,stepDays:6,ex:fixture.e.map(exObj)};v={'1|0|1|B|a':'17','1|0|1|B|b':'9'};done=[1];d=2;",context);
  const scanner=fs.readFileSync(path.join(ROOT,'patient-start-scan.js'),'utf8');
  // Expose closure functions only in this test's VM; production gets no test-only API.
  vm.runInContext(scanner.replace('  window.__kggPatientStartScanTest=',
    '  window.__primaryNamesSmoke={mergePlanUpdate,handlePlanText};\n  window.__kggPatientStartScanTest='),context,{filename:'patient-start-scan.js#actual-module'});
  if(progressions){context.document.readyState='complete';vm.runInContext(fs.readFileSync(path.join(ROOT,'patient-set-summary-groups.js'),'utf8'),context,{filename:'patient-set-summary-groups.js#actual-wrappers'});context.document.readyState='loading';}
  return {context,storage,elements,events,run:source=>vm.runInContext(source,context),stored:()=>JSON.parse(storage.getItem('kggCurrentPlanV1')).plan};
}
function oldParser(){
  const source=cp.execFileSync('git',['show',BASE+':kgg-update/src/runtime/app-core.html'],{cwd:ROOT,encoding:'utf8',maxBuffer:3000000});
  function fn(name){const start=source.indexOf('  function '+name+'(');assert.ok(start>=0,name);const next=source.indexOf('\n  function ',start+12);return source.slice(start,next<0?source.length:next);}
  const context={window:{},URL,JSON,String,Array,decodeURIComponent,escape,atob:value=>Buffer.from(value,'base64').toString('binary')};vm.createContext(context);
  for(const name of ['safeJsonRepair','parseLooseJson','safeBase64JsonDecode','parseScannedQrRaw'])vm.runInContext(fn(name),context,{filename:'app-core@'+BASE+':'+name});
  return context.parseScannedQrRaw;
}
const tests=[];function test(name,run){tests.push({name,run});}
test('unchanged old KGGD1 parser keeps optional primary-name provenance including selection names',()=>{
  const object={v:1,i:'synthetic-primary-plan',d:2,e:[['Einbeinstand',1,'B','kg','Wdh',[['17','9']],'0',{k:'kgg015',g:'synthetic-group',s:[{s:1,i:'easy',n:'Leicht'}]}]],final:false,m:{exercisePrimaryNames:{Einbeinstand:'Single-leg stance',Leicht:'Easy'}}};
  const parse=oldParser();assert.deepEqual(clone(parse(returnCode(object)).json),object);assert.equal(parse(returnCode(object)).type,'KGGD1');
});
test('legacy return with no map keeps exact KGGD1 bytes',()=>{
  const env=patient(raw(['Kniebeuge']),true);env.run('showQr(false)');
  assert.equal(env.elements.get('qr').dataset.payload,returnCode({v:1,i:'synthetic-primary-plan',d:2,e:[['Kniebeuge',1,'B','kg','Wdh',[['','']],'0']],final:false}));
});
test('base return carries only provenance for actual returned German names',()=>{
  const plan=raw(['Einbeinstand'],{Einbeinstand:'Single-leg stance',NichtImReturn:'Unused primary'});plan.e[0][11]={g:'synthetic-group',v:[{i:'unused',n:'NichtImReturn',o:0}]};
  const env=patient(plan);env.run('showQr(false)');
  assert.deepEqual(decoded(env.elements.get('qr').dataset.payload).m,{exercisePrimaryNames:{Einbeinstand:'Single-leg stance'}});
});
test('active progression wrapper carries only actual selected German stage provenance',()=>{
  const plan=raw(['Einbeinstand'],{Einbeinstand:'Single-leg stance',Leicht:'Easy',Schwer:'Hard',NichtImReturn:'Unused primary'});
  plan.e[0][11]={k:'kgg015',g:'synthetic-group',a:'easy',v:[{i:'easy',n:'Leicht',o:0,m:[]},{i:'hard',n:'Schwer',o:1,m:[]},{i:'unused',n:'NichtImReturn',o:2,m:[]}]};
  const env=patient(plan,true);env.run('showQr(false)');const payload=decoded(env.elements.get('qr').dataset.payload);
  assert.equal(payload.e[0][7].s[0].n,'Leicht');assert.equal(payload.e[0][7].s[0].i,'easy');
  assert.deepEqual(payload.m,{exercisePrimaryNames:{Einbeinstand:'Single-leg stance',Leicht:'Easy'}});
});
test('legacy English primary to first German name updates same index and keeps state',()=>{
  const initial=raw(['Single-leg stance']);initial.e[0][7]=[{id:'synthetic-image',type:'image'}];initial.e[0][11]={g:'synthetic-group',v:[{i:'easy',n:'Easy',o:0}]};
  const env=patient(initial),before=env.run('JSON.stringify({v,done,d})');env.context.incoming=raw(['Einbeinstand'],{Einbeinstand:'Single-leg stance'});
  assert.equal(env.run('__primaryNamesSmoke.mergePlanUpdate(incoming)'),true);assert.equal(env.stored().e.length,1,'mutable DE name created a second card');
  assert.equal(env.stored().e[0][0],'Einbeinstand');assert.deepEqual(env.stored().e[0][7],initial.e[0][7]);assert.deepEqual(env.stored().e[0][11],initial.e[0][11]);assert.equal(env.run('JSON.stringify({v,done,d})'),before);
});
test('German DE1 to DE2 partial update preserves retained row metadata and values',()=>{
  const initial=raw(['Einbeinstand','Ziehen'],{Einbeinstand:'Single-leg stance',Ziehen:'Pull'});initial.m.exerciseNamesEn={Einbeinstand:'Single-leg stance',Ziehen:'Pull'};
  const env=patient(initial),before=env.run('JSON.stringify({v,done,d})');env.context.incoming=raw(['Einbeiniger Stand'],{'Einbeiniger Stand':'Single-leg stance'});env.context.incoming.m.exerciseNamesEn={'Einbeiniger Stand':'Single-leg stance'};
  env.run('__primaryNamesSmoke.mergePlanUpdate(incoming)');assert.equal(env.stored().e.length,2,'DE rename appended a duplicate');assert.equal(env.stored().e[0][0],'Einbeiniger Stand');assert.equal(env.stored().e[1][0],'Ziehen');
  assert.deepEqual(env.stored().m.exercisePrimaryNames,{'Einbeiniger Stand':'Single-leg stance',Ziehen:'Pull'});assert.deepEqual(env.stored().m.exerciseNamesEn,{'Einbeiniger Stand':'Single-leg stance',Ziehen:'Pull'});assert.equal(env.run('JSON.stringify({v,done,d})'),before);
});
for(const [name,map] of [['invalid explicit value',{Einbeinstand:12}],['ambiguous primary',{Einbeinstand:'Single-leg stance',Ziehen:'Single-leg stance'}]])test(name+' is handled before any import mutation or reload fallback',()=>{
  const env=patient(raw(['Single-leg stance']));const beforeStorage=JSON.stringify(env.storage),beforeState=env.run('JSON.stringify({p,v,done,d})');const next=raw(['Einbeinstand','Ziehen'],map);
  env.context.input=code(next);env.run('__primaryNamesSmoke.handlePlanText(input)');
  assert.equal(JSON.stringify(env.storage),beforeStorage,'rejected metadata mutated storage');assert.equal(env.run('JSON.stringify({p,v,done,d})'),beforeState,'rejected metadata mutated state');assert.equal(env.context.location.href,'https://synthetic.test/','rejected metadata entered location fallback');assert.equal(env.events.reloads,0);assert.ok(env.events.alerts.length||env.elements.get('status')?.textContent,'rejection should be visible');
});
test('invalid provenance rejection uses the selected German or English UI language',()=>{
  const messages=[];
  for(const language of ['de','en']){
    const env=patient(raw(['Single-leg stance']));env.storage.setItem('kggPatientLang',language);env.context.input=code(raw(['Einbeinstand'],{Einbeinstand:12}));env.run('__primaryNamesSmoke.handlePlanText(input)');
    const message=env.events.alerts.join(' ')+' '+String(env.elements.get('status')?.textContent||'');assert.ok(message.trim(),'rejected import must have a visible message');messages.push(message);
  }
  assert.notEqual(messages[0],messages[1],'new import rejection ignores English UI selection');assert.match(messages[1],/invalid|ambiguous|conflict|cannot|could not|inconsistent|duplicate|unable/i,'English UI received no understandable English rejection');
});
test('unused incoming primary/English entries never rebind a retained card',()=>{
  const initial=raw(['Einbeinstand','Ziehen'],{Einbeinstand:'Single-leg stance',Ziehen:'Pull'});initial.m.exerciseNamesEn={Ziehen:'Authored pull'};
  const env=patient(initial);env.context.incoming=raw(['Einbeinstand'],{Einbeinstand:'Single-leg stance',Ziehen:'Unrelated stale mapping'});env.context.incoming.m.exerciseNamesEn={Ziehen:'Unrelated stale English'};
  env.run('__primaryNamesSmoke.mergePlanUpdate(incoming)');assert.equal(env.stored().m.exercisePrimaryNames.Ziehen,'Pull');assert.equal(env.stored().m.exerciseNamesEn.Ziehen,'Authored pull');
});
test('partial update colliding with a retained normalized display is rejected before save',()=>{
  const env=patient(raw(['Ziehen'],{Ziehen:'Pull'})),before=JSON.stringify(env.storage),state=env.run('JSON.stringify({p,v,done,d})');env.context.input=code(raw(['Ziehen!'],{'Ziehen!':'Different primary'}));env.run('__primaryNamesSmoke.handlePlanText(input)');assert.equal(JSON.stringify(env.storage),before);assert.equal(env.run('JSON.stringify({p,v,done,d})'),state);assert.ok(env.events.alerts.length);
});
let failures=0;for(const entry of tests){try{entry.run();console.log('PASS '+entry.name)}catch(error){failures++;console.error('FAIL '+entry.name+'\n  '+String(error.message).split('\n')[0])}}
console.log(JSON.stringify({suite:'exercise-primary-names',base:BASE,total:tests.length,passed:tests.length-failures,failed:failures}));
if(failures)process.exitCode=1;
