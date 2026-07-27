#!/usr/bin/env node
'use strict';

const fs=require('fs');
const path=require('path');
const vm=require('vm');

const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'patient-set-summary-groups.js'),'utf8');

function fail(message){throw new Error(message)}
function assert(condition,message){if(!condition)fail(message)}

let language='de';
const sum={textContent:''};
const context={
  console,
  window:{__KGG_TEST__:true},
  document:{
    readyState:'complete',
    getElementById(id){return id==='sum'?sum:null},
    addEventListener(){}
  },
  localStorage:{getItem(key){return key==='kggPatientLang'?language:null}},
  setTimeout(){return 0},
  clearTimeout(){},
  showQr(){}
};
context.window.window=context.window;
context.window.document=context.document;
context.window.localStorage=context.localStorage;
context.globalThis=context;
vm.createContext(context);
vm.runInContext(source,context,{filename:'patient-set-summary-groups.js'});

const api=context.window.__kggSetSummaryGroupsTest;
assert(api,'summary test API missing');

const compressed=api.compressText([
  'Kniebeuge',
  'Satz 1: 12 Wdh · 20 kg',
  'Satz 2: 12 Wdh · 20 kg',
  'Satz 3: 12 Wdh · 20 kg'
].join('\n'));
assert(compressed.includes('Satz 1–3: 12 Wdh · 20 kg'),'explicit identical sets were not grouped as Satz 1–3');

const plan={ex:[{n:'Kniebeuge',sets:3}]};
const identical={
  '1|0|1|B|m':'12','1|0|1|B|u':'20',
  '1|0|2|B|m':'12','1|0|2|B|u':'20',
  '1|0|3|B|m':'12','1|0|3|B|u':'20'
};
const base=['Kniebeuge','12 Wdh · 20 kg','Schmerz: 0/10'].join('\n');
const annotated=api.annotateUniformSetRanges(base,{plan,values:identical,day:1});
assert(annotated.includes('Kniebeuge\nSatz 1–3:\n12 Wdh · 20 kg'),'uniform compact output is missing Satz 1–3');
assert(api.annotateUniformSetRanges(annotated,{plan,values:identical,day:1})===annotated,'range annotation is not idempotent');

const different={...identical,'1|0|3|B|m':'10'};
assert(api.annotateUniformSetRanges(base,{plan,values:different,day:1})===base,'different sets were incorrectly labeled as one range');

language='en';
const english=api.annotateUniformSetRanges(['Kniebeuge','12 reps · 20 kg'].join('\n'),{plan,values:identical,day:1});
assert(english.includes('Set 1–3:'),'English output did not use Set 1–3');

console.log('Patient summary range smoke: OK');
