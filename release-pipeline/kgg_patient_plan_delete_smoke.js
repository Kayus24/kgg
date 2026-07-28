#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.resolve(__dirname,'..','patient-plan-delete.js'),'utf8');
function assert(c,m){if(!c)throw new Error(m)}
const context={window:{__KGG_TEST__:true},document:{readyState:'loading',addEventListener(){},getElementById(){return null}},localStorage:{getItem(){return null}},setTimeout(){},setInterval(){},clearTimeout(){},console};context.window.window=context.window;context.window.document=context.document;context.globalThis=context;vm.createContext(context);vm.runInContext(source,context);
const api=context.window.__kggPlanDeleteTest;assert(api,'test api missing');
const A={i:'a',t:'A',e:[['A',1,'BI','kg','Wdh','','',[{id:'shared'},{id:'a-only'}]]]},B={i:'b',t:'B',e:[['B',1,'BI','kg','Wdh','','',[{id:'shared'},{id:'b-only'}]]]},C={i:'c',t:'C',e:[]};
let r=api.removePlanState({plans:[A,B,C],active:1,day:{x:1}},0);assert(r.ok&&r.state.plans.length===2&&r.state.active===0,'inactive before active failed');assert(r.state.plans[0].i==='b'&&r.state.plans[1].i==='c','remaining plans changed');
r=api.removePlanState({plans:[A,B,C],active:1},1);assert(r.ok&&r.activeRemoved&&r.state.active===1&&r.state.plans[1].i==='c','active delete fallback failed');
r=api.removePlanState({plans:[A],active:0},0);assert(!r.ok&&r.state.plans.length===1,'last plan was deletable');
r=api.removePlanState({plans:[A,B],active:0},9);assert(!r.ok&&r.state.plans.length===2,'invalid index changed state');
const ids=[...api.mediaIds(A)].sort();assert(ids.join(',')==='a-only,shared','media ids mismatch');
const keys=api.planStorageKeys(A);assert(keys.length===3&&keys.every(k=>/^kgg-a-/.test(k)),'plan keys not isolated');
assert(!source.includes('localStorage.clear('),'global localStorage.clear found');assert(!source.includes('indexedDB.deleteDatabase'),'global indexedDB delete found');
console.log('Patient plan delete smoke: OK');
