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
const context={window,Storage:FakeStorage,console};
vm.createContext(context);
const source=fs.readFileSync(path.join(__dirname,'..','patient-plan-replace-slot-fix.js'),'utf8');
vm.runInContext(source,context);

const key='kggPatientMultiPlansV1';
const plan=(id,title)=>({i:id,t:title,e:[[title,1,'B','kg','Wdh']]});

const before={version:1,plans:[plan('a','Plan A'),plan('b','Plan B')],active:0,day:{0:4,1:2}};
localStorage.data.set(key,JSON.stringify(before));
const replacement={...plan('new-rabc123','Neu'),sourcePlanId:'new'};
localStorage.setItem(key,JSON.stringify({version:1,plans:[before.plans[0],before.plans[1],replacement],active:2,day:{0:4,1:2,2:1}}));
let after=JSON.parse(localStorage.getItem(key));
assert(after.plans.length===2,'replacement increased plan count');
assert(after.active===0,'replacement changed active slot');
assert(after.plans[0].t==='Neu','active slot was not replaced');
assert(after.plans[1].t==='Plan B','inactive plan was modified');
assert(after.day[0]===1,'replacement day was not reset');

localStorage.data.delete(key);
const firstReplacement={...plan('first-rdef456','Erster Ersatz'),sourcePlanId:'first'};
localStorage.setItem(key,JSON.stringify({version:1,plans:[plan('old','Alt'),firstReplacement],active:1,day:{0:1,1:1}}));
after=JSON.parse(localStorage.getItem(key));
assert(after.plans.length===1,'first replacement created two plans');
assert(after.active===0,'first replacement active slot is not zero');
assert(after.plans[0].t==='Erster Ersatz','first replacement was not stored');

const add={version:1,plans:[after.plans[0],plan('second','Zweiter Plan')],active:1,day:{0:1,1:1}};
localStorage.setItem(key,JSON.stringify(add));
after=JSON.parse(localStorage.getItem(key));
assert(after.plans.length===2,'normal add-plan operation was intercepted');
assert(after.active===1,'normal add-plan active index changed');

console.log('Patient plan replace active-slot smoke: PASS');
