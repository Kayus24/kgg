#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'..','patient-install-prompt.js'),'utf8');
function assert(c,m){if(!c)throw new Error(m)}
let listener=null,fallbackCalls=0;
const context={console,window:{__KGG_TEST__:true,installApp:async()=>{fallbackCalls++;return 'fallback'},addEventListener(type,fn){if(type==='beforeinstallprompt')listener=fn}},document:{readyState:'loading',addEventListener(){},getElementById(){return null}},setTimeout(){return 0},clearTimeout(){}};
context.globalThis=context;context.window.window=context.window;context.window.document=context.document;
vm.createContext(context);vm.runInContext(source,context,{filename:'patient-install-prompt.js'});
const api=context.window.__kggInstallPromptTest;assert(api,'test API missing');
let prevented=0,promptCalls=0;
const event={preventDefault(){prevented++},prompt(){promptCalls++;return Promise.resolve()},userChoice:Promise.resolve({outcome:'accepted'})};
api.capturePrompt(event);assert(prevented===1,'event not prevented');assert(api.getPrompt()===event,'prompt not shared');
(async()=>{const result=await api.consumePrompt();assert(result.handled,'prompt not handled');assert(promptCalls===1,'prompt must run exactly once');assert(api.getPrompt()===null,'prompt not cleared');const second=await api.consumePrompt();assert(!second.handled,'consumed prompt reused');assert(promptCalls===1,'prompt called twice');const noPrompt=await context.window.installApp();assert(noPrompt==='fallback'&&fallbackCalls===1,'fallback without prompt failed');console.log('Patient install prompt smoke: OK')})().catch(err=>{console.error(err);process.exit(1)});
