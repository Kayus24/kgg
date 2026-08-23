#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');

function assert(condition,message){if(!condition)throw new Error(message)}
const root=path.resolve(__dirname,'..');
const helper=fs.readFileSync(path.join(root,'patient-plan-link-choice.js'),'utf8');
const index=fs.readFileSync(path.join(root,'index.html'),'utf8');
const ios=fs.readFileSync(path.join(root,'ios-start.html'),'utf8');
const worker=fs.readFileSync(path.join(root,'service-worker.js'),'utf8');
const scan=fs.readFileSync(path.join(root,'patient-start-scan.js'),'utf8');
const slots=fs.readFileSync(path.join(root,'patient-plan-replace-slot-fix.js'),'utf8');

for(const label of ['Als zusätzlichen Plan hinzufügen','Aktiven Plan ersetzen','Abbrechen'])assert(helper.includes(label),`choice label missing: ${label}`);
assert(helper.includes("const PENDING_KEY='kggPendingPlanLinkV1'"),'pending session key missing');
assert(helper.includes('const TTL_MS=5*60*1000'),'five-minute pending TTL missing');
assert(helper.includes("query.get('plan')||query.get('kgg')"),'query plan/kgg variants missing');
assert(helper.includes("source:'hash'"),'hash plan variant missing');
assert(!helper.includes('window.prompt')&&!helper.includes('window.confirm')&&!helper.includes('prompt(')&&!helper.includes('confirm('),'choice helper uses a native dialog');
assert((index.match(/patient-plan-link-choice\.js\?v=plan-link-choice-2-kgg-h3/g)||[]).length===1,'index loads choice helper not exactly once');
assert(index.indexOf('patient-plan-link-choice.js')<index.indexOf('load();</script>'),'choice helper is not loaded before patient boot');
assert((index.match(/patient-version-label\.js\?v=81/g)||[]).length===1,'index version label is not v81');
assert(!ios.includes('localStorage.setItem(K,JSON.stringify({plan:'),'ios-start still overwrites the current plan');
assert(ios.includes('./vendor/fflate-0.8.3.js?v=fflate-0.8.3')&&ios.includes('./patient-qr-format.js?v=v81-kgg-h3-plan-format'),'ios-start local KGGH3 codec assets missing');
assert(ios.includes('encodeKggH3')&&!ios.includes("go(String(x).replace(/^KGGH2:/,''))"),'ios-start does not forward through the KGGH3 hash path');
assert(worker.includes("const APP_VERSION = '81';")&&worker.includes("kgg-handyplan-v81-kgg-h3-qr"),'service worker is not v81');
assert(worker.includes("const PLAN_LINK_CHOICE_SCRIPT = './patient-plan-link-choice.js?v=plan-link-choice-2-kgg-h3';"),'service worker choice cache asset missing');
assert(worker.includes("url.pathname.endsWith('/patient-plan-link-choice.js')"),'service worker choice delivery route missing');
assert(slots.includes('function addPlan(raw)')&&slots.includes('addPlan'), 'existing add bridge is missing');
assert(scan.includes('replacePlan(nextRaw,options)')&&scan.includes('replaceConfirmed:nextRaw=>replacePlan(nextRaw,{confirmed:true})'),'existing replace bridge is missing');

class FakeStorage{
  constructor(){this.data=new Map()}
  getItem(key){return this.data.has(String(key))?this.data.get(String(key)):null}
  setItem(key,value){this.data.set(String(key),String(value))}
  removeItem(key){this.data.delete(String(key))}
}
const localStorage=new FakeStorage(),sessionStorage=new FakeStorage();
const window={__KGG_TEST__:true,localStorage,KGGPatientPlanSlots:null};
const context={window,localStorage,sessionStorage,location:{search:'',hash:'',pathname:'/kgg/'},history:{replaceState(){}},document:undefined,console,Date,JSON,TextDecoder,URLSearchParams,atob:global.atob,setTimeout};
window.window=window;
vm.createContext(context);
vm.runInContext(helper,context);
const api=window.__kggPatientPlanLinkChoiceTest;
assert(api,'choice helper test API missing');
const plan={i:'plan-b',t:'Plan B',e:[['Übung',3,'B','kg','Wdh']]};
const payload=Buffer.from(JSON.stringify(plan),'utf8').toString('base64url');
assert(api.decodePayload(`KGGH2:${payload}`).t==='Plan B','KGGH2 payload did not decode');
assert(api.planKey({i:'a',t:'A',e:[]})===api.planKey({i:'a',t:'anders',e:[]}),'stable plan key changed for the same plan id');
sessionStorage.setItem('kggPendingPlanLinkV1',JSON.stringify({raw:plan,expiresAt:Date.now()-1}));
assert(api.readPending()===null,'expired pending import was accepted');
assert(sessionStorage.getItem('kggPendingPlanLinkV1')===null,'expired pending import was not removed');

console.log('Patient plan-link choice smoke: PASS');
