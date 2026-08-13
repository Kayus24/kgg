#!/usr/bin/env node
'use strict';
const fs=require('fs');
const path=require('path');

function assert(condition,message){if(!condition)throw new Error(message)}
const root=path.resolve(__dirname,'..');
const index=fs.readFileSync(path.join(root,'index.html'),'utf8');
const history=fs.readFileSync(path.join(root,'patient-day-history.js'),'utf8');
const multi=fs.readFileSync(path.join(root,'patient-multiplan-db.js'),'utf8');
const del=fs.readFileSync(path.join(root,'patient-plan-delete.js'),'utf8');
const start=fs.readFileSync(path.join(root,'patient-start-values-day1.js'),'utf8');
const cardSettings=fs.readFileSync(path.join(root,'patient-card-settings.js'),'utf8');
const sw=fs.readFileSync(path.join(root,'service-worker.js'),'utf8');
const version=fs.readFileSync(path.join(root,'patient-version-label.js'),'utf8');
const recovery=fs.readFileSync(path.join(root,'update-recovery.html'),'utf8');

const requiredIndex=[
  'function isContinuousPlan(){return !!p&&p.extendDays!==false}',
  'function maxCompletedDay(list=done)',
  'function normalizeDoneDays(list)',
  "return isContinuousPlan()?candidate:Math.min(candidate,Number(p.days)||1)",
  'function resumeDay(){return Math.max(Number(d)||1,next())}',
  'o>=front&&!done.includes(o)',
  "done=normalizeDoneDays(read(dk(),'[]'))",
  "$('meta').textContent=dayPlanMeta()",
  "$('extendBtn').classList.add('hide')",
  'const qrDay=Number(d)||1,frontBefore=next()',
  'd:qrDay,e:rows(qrDay)',
  'if(finalize&&qrDay===frontBefore){d=next();save()}',
  'window.KGGPatientDayFlow={isContinuousPlan,maxCompletedDay,dayAllowed,normalizeDone:normalizeDoneDays,next,restoreDay,resumeDay}',
];
for(const token of requiredIndex)assert(index.includes(token),'index continuous-day contract missing: '+token);
assert(!index.includes('Math.min(Math.max(...done)+1,p.days)'),'legacy p.days cap still exists in next()');
assert(!index.includes('done.length?Math.max(...done):0'),'spread-based max completed day still exists');
assert(!index.includes("filter(n=>n>=1&&n<=p.days)"),'core still drops completed days above p.days');

assert(history.includes("const VERSION='v6_continuous_days_history'"),'day-history version not bumped');
assert(history.includes('let historyLimit=30'),'history paging limit missing');
assert(history.includes("const cur=Number(d)||1,total=Math.max(cur,today()),arr=multiPlans()"),'history still uses p.days as max');
assert(history.includes("id=\"kggHistoryMore\""),'older-history pagination control missing');
assert(history.includes('historyLimit+=30'),'older-history pagination does not expand');
assert(history.includes(".kggDayCard[data-day]"),'history paging button can collide with day-card navigation');

assert(multi.includes("flow&&typeof flow.normalizeDone==='function'?flow.normalizeDone"),'multi-plan does not preserve T13+ done entries');
assert(multi.includes("typeof restoreDay==='function'&&restoreDay()"),'multi-plan does not restore target plan day');
assert(del.includes("flow&&typeof flow.normalizeDone==='function'?flow.normalizeDone"),'plan delete does not preserve T13+ done entries');
assert(del.includes("typeof restoreDay==='function'&&restoreDay()"),'plan delete does not restore surviving plan day');
assert(start.includes("p.extendDays!==false||Number(p.days||0)>=2"),'start values cannot advance a continuous one-day horizon to T2');
assert(cardSettings.includes("const VERSION='v3_continuous_day_meta'"),'card settings continuous-day meta version missing');
assert(cardSettings.includes("continuous?T('fortlaufender Trainingsplan','continuous training plan')"),'card settings still overwrites continuous plan meta with p.days');

assert(sw.includes("const CACHE_NAME = 'kgg-handyplan-v75-continuous-days'"),'service worker cache is not v75 continuous-days');
assert(sw.includes("const APP_VERSION = '75'"),'service worker app version is not 75');
assert(version.includes("const RELEASE='75'"),'patient version label is not 75');
assert(recovery.includes("const RELEASE='75'"),'update recovery is not 75');

console.log(JSON.stringify({status:'PASS',continuousDayContract:true,historyPaging:30,patientVersion:75}));
