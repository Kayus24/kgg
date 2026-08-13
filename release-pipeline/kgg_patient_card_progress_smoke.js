#!/usr/bin/env node
'use strict';

const fs=require('fs');
const path=require('path');
const vm=require('vm');

const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'patient-card-progress.js'),'utf8');

function fail(message){throw new Error(message)}
function assert(condition,message){if(!condition)fail(message)}

let lang='de';
const context={
  console,
  window:{__KGG_TEST__:true},
  document:{readyState:'loading',addEventListener(){},getElementById(){return null}},
  localStorage:{getItem(key){return key==='kggPatientLang'?lang:null}},
  setTimeout(){return 0},
  clearTimeout(){},
  MutationObserver:function(){}
};
context.window.window=context.window;
context.window.document=context.document;
context.window.localStorage=context.localStorage;
context.globalThis=context;
vm.createContext(context);
vm.runInContext(source,context,{filename:'patient-card-progress.js'});

const api=context.window.__kggCardProgressTest;
assert(api,'card progress test API missing');
assert(api.stateForCount(0)==='open','0 fields must be open');
assert(api.stateForCount(1,2)==='partial','one of two fields must be partial');
assert(api.stateForCount(2,2)==='done','all two fields must be done');
assert(api.stateForCount(2,6)==='partial','two of six fields must stay partial');
assert(api.stateForCount(6,6)==='done','all six fields must be done');
assert(api.labelForState('open','de')==='○ Offen','German open label mismatch');
assert(api.labelForState('partial','de')==='◐ Teilweise','German partial label mismatch');
assert(api.labelForState('done','de')==='✓ Bearbeitet','German done label mismatch');
assert(api.labelForState('open','en')==='○ Open','English open label mismatch');
assert(api.labelForState('partial','en')==='◐ Partial','English partial label mismatch');
assert(api.labelForState('done','en')==='✓ Done','English done label mismatch');

const normalInputs=[{value:'12'},{value:'  '},{value:'20'}];
const painInput={value:'7'};
const card={
  querySelectorAll(selector){
    if(selector==='.set input.num')return normalInputs;
    if(selector==='.pain input')return [painInput];
    return [];
  }
};
assert(api.filledCount(card)===2,'filled count must count only two normal non-empty values');
normalInputs[2].value='';
assert(api.filledCount(card)===1,'blank normal value must reduce count to one');
normalInputs[0].value='';
assert(api.filledCount(card)===0,'pain value must not affect card progress');

lang='en';
assert(api.labelForState('done')==='✓ Done','stored patient language was not respected');
const collapseSource=fs.readFileSync(path.join(ROOT,'collapse-cards.js'),'utf8');
assert(collapseSource.includes('function progress(c)'),'collapse fallback progress renderer missing');
assert(collapseSource.includes('function patchProgressPut()'),'collapse fallback does not refresh after canonical put/save');
assert(collapseSource.includes("tr('✓ Bearbeitet','✓ Done')"),'visible done label missing from collapse fallback');
assert(collapseSource.includes('display:inline-flex!important'),'closed-card badge visibility is not enforced');
assert(source.includes('body.kggAlwaysCollapsed .ex:not(.kggOpen)'),'real always-collapsed card state does not show progress badges');
assert(collapseSource.includes("total>0&&n>=total?'Done':'Partial'"),'collapse fallback can still mark a multi-set card done too early');
console.log('Patient card progress smoke: OK');
