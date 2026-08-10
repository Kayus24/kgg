#!/usr/bin/env node
'use strict';
const fs=require('fs');
const path=require('path');
const vm=require('vm');

function assert(condition,message){if(!condition)throw new Error(message)}
class FakeStorage{
  constructor(){this.data=new Map()}
  getItem(key){return this.data.has(String(key))?this.data.get(String(key)):null}
  setItem(key,value){this.data.set(String(key),String(value))}
}
const localStorage=new FakeStorage();
const window={localStorage};
const context={window,Storage:FakeStorage,console,Date,JSON,setTimeout,queueMicrotask};
context.p={id:'a',title:'Plan A',version:1,days:6,extendDays:true,stepDays:6,ex:[]};
context.v={'1|0|1|B|a':'10'};
context.done=[1];
context.d=4;
vm.createContext(context);
const source=fs.readFileSync(path.join(__dirname,'..','patient-plan-replace-slot-fix.js'),'utf8');
vm.runInContext(source,context);

const multiKey='kggPatientMultiPlansV1';
const currentKey='kggCurrentPlanV1';
const plan=(id,title)=>({i:id,t:title,e:[[title,1,'B','kg','Wdh']]});

const before={version:1,plans:[plan('a','Plan A'),plan('b','Plan B')],active:0,day:{0:4,1:2}};
localStorage.data.set(multiKey,JSON.stringify(before));
const replacement={...plan('new-rabc123','Neu'),sourcePlanId:'new'};
localStorage.setItem(multiKey,JSON.stringify({version:1,plans:[before.plans[0],before.plans[1],replacement],active:2,day:{0:4,1:2,2:1}}));
let after=JSON.parse(localStorage.getItem(multiKey));
assert(after.plans.length===2,'replacement increased plan count');
assert(after.active===0,'replacement changed active slot');
assert(after.plans[0].t==='Neu','active slot was not replaced');
assert(after.plans[1].t==='Plan B','inactive plan was modified');
assert(after.day[0]===1,'replacement day was not reset');

localStorage.data.delete(multiKey);
const firstReplacement={...plan('first-rdef456','Erster Ersatz'),sourcePlanId:'first'};
localStorage.setItem(multiKey,JSON.stringify({version:1,plans:[plan('old','Alt'),firstReplacement],active:1,day:{0:1,1:1}}));
after=JSON.parse(localStorage.getItem(multiKey));
assert(after.plans.length===1,'first replacement created two plans');
assert(after.active===0,'first replacement active slot is not zero');
assert(after.plans[0].t==='Erster Ersatz','first replacement was not stored');

localStorage.data.set(multiKey,JSON.stringify(before));
localStorage.data.set(currentKey,JSON.stringify({plan:before.plans[0]}));
assert(window.KGGPatientPlanSlots.nextPlanNumber()===3,'next plan number for two plans is not 3');
window.KGGPatientPlanSlots.beginAdd();
const incoming=plan('third','Plan C');
JSON.parse(JSON.stringify(incoming));
const merged=plan('a','Merged current plan');
localStorage.setItem(currentKey,JSON.stringify({plan:merged,source:'update'}));
localStorage.setItem(multiKey,JSON.stringify({version:1,plans:[merged,before.plans[1]],active:0,day:{0:4,1:2}}));
after=JSON.parse(localStorage.getItem(multiKey));
const current=JSON.parse(localStorage.getItem(currentKey));
assert(after.plans.length===3,'add mode did not append exactly one plan');
assert(after.active===2,'added plan is not the active slot');
assert(after.plans[0].t==='Plan A','add mode modified the source slot');
assert(after.plans[1].t==='Plan B','add mode modified an inactive slot');
assert(after.plans[2].t==='Plan C','added slot does not contain the scanned plan');
assert(after.plans[2].e.length===1&&after.plans[2].e[0][0]==='Plan C','added slot contains merged exercises');
assert(/-p[a-z0-9]+$/i.test(after.plans[2].i),'added plan did not receive an independent id');
assert(after.day[2]===1,'added plan did not start on day 1');
assert(current.source==='add'&&current.plan.i===after.plans[2].i,'current plan wrapper does not point to added slot');
assert(context.p.id===after.plans[2].i,'runtime did not switch to the added slot');
assert(Object.keys(context.v).length===0,'added plan reused previous values');
assert(context.done.length===0&&context.d===1,'added plan reused previous completion/day state');
assert(window.KGGPatientPlanSlots.nextPlanNumber()===4,'button number did not advance to 4 after adding');

const one={version:1,plans:[plan('only','Only')],active:0,day:{0:2}};
assert(window.KGGPatientPlanSlots.applyAddState(one,one.plans[0],plan('two','Two')).plans.length===2,'pure add contract failed for second plan');
const three={version:1,plans:[plan('1','1'),plan('2','2'),plan('3','3')],active:1,day:{0:1,1:2,2:3}};
const four=window.KGGPatientPlanSlots.applyAddState(three,three.plans[1],plan('4','4'));
assert(four.plans.length===4&&four.active===3&&four.day[3]===1,'pure add contract failed for fourth plan');
assert(four.plans[1].t==='2','pure add contract changed an existing plan');

console.log('Patient plan slot smoke: PASS');
