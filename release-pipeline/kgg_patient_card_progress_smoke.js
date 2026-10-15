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
let storedPlan=null;
const context={
  console,
  window:{__KGG_TEST__:true},
  document:{readyState:'loading',addEventListener(){},getElementById(){return null}},
  localStorage:{getItem(key){return key==='kggPatientLang'?lang:key==='kggCurrentPlanV1'?JSON.stringify(storedPlan):null}},
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
assert(typeof api.ticket034FinishCopy==='function','finish dialog copy contract missing');
vm.runInContext(fs.readFileSync(path.join(ROOT,'patient-i18n.js'),'utf8'),context,{filename:'patient-i18n.js'});
lang='de';
let copy=api.ticket034FinishCopy('Wadenheben');
assert(copy.title==='Training beenden'&&copy.confirm==='Training beenden'&&copy.cancel==='Weiter trainieren','German finish controls changed');
assert(copy.message==='Sie haben noch die Übung „Wadenheben“ offen. Sicher, dass Sie das Training beenden wollen?','German finish message changed');
lang='en';copy=api.ticket034FinishCopy('Wadenheben');
assert(copy.title==='Finish training'&&copy.confirm==='Finish training'&&copy.cancel==='Continue training','English finish controls missing');
assert(copy.message==='You still have the exercise “Calf Raise” open. Are you sure you want to finish training?','known finish exercise was not translated');
const authored='Eigene Übung: Satz: A → Tag 2 — X',english='Own exercise: Set: A → Day 2 — Y';
storedPlan={plan:{m:{exerciseNamesEn:{[authored]:english}}}};
const storedBefore=JSON.stringify(storedPlan);
assert(api.ticket034FinishCopy(authored).message.includes('“'+english+'”'),'exact authored finish label was changed');
assert(api.ticket034FinishCopy('Unbekannt: Satz: A → Tag 2 — X').message.includes('“Unbekannt: Satz: A → Tag 2 — X”'),'unknown finish label must remain original');
lang='de';assert(api.ticket034FinishCopy(authored).message.includes('„'+authored+'“'),'German authored finish name changed');
lang='en';const provider=context.window.KGGPatientI18n;delete context.window.KGGPatientI18n;
assert(api.ticket034FinishCopy(authored).message.includes('“'+authored+'”'),'missing-provider finish name fallback changed');
context.window.KGGPatientI18n=provider;
assert(JSON.stringify(storedPlan)===storedBefore,'finish copy changed canonical metadata');
const collapseSource=fs.readFileSync(path.join(ROOT,'collapse-cards.js'),'utf8');
assert(collapseSource.includes('function progress(c)'),'collapse fallback progress renderer missing');
assert(collapseSource.includes('function patchProgressPut()'),'collapse fallback does not refresh after canonical put/save');
assert(collapseSource.includes("tr('✓ Bearbeitet','✓ Done')"),'visible done label missing from collapse fallback');
assert(collapseSource.includes('display:inline-flex!important'),'closed-card badge visibility is not enforced');
assert(source.includes('body.kggAlwaysCollapsed .ex:not(.kggOpen)'),'real always-collapsed card state does not show progress badges');
assert(collapseSource.includes("total>0&&n>=total?'Done':'Partial'"),'collapse fallback can still mark a multi-set card done too early');
console.log('Patient card progress smoke: OK');
