#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'..','patient-install-prompt.js'),'utf8');
function assert(c,m){if(!c)throw new Error(m)}
let listener=null,fallbackCalls=0;
const context={console,window:{__KGG_TEST__:true,installApp:async()=>{fallbackCalls++;return 'fallback'},addEventListener(type,fn){if(type==='beforeinstallprompt')listener=fn}},document:{readyState:'complete',addEventListener(){},getElementById(){return null}},setTimeout(){return 0},clearTimeout(){}};
context.globalThis=context;context.window.window=context.window;context.window.document=context.document;
vm.createContext(context);vm.runInContext(source,context,{filename:'patient-install-prompt.js'});
const api=context.window.__kggInstallPromptTest;assert(api,'test API missing');assert(typeof listener==='function','beforeinstallprompt listener missing');
let prevented=0,promptCalls=0;
const event={preventDefault(){prevented++},prompt(){promptCalls++;return Promise.resolve()},userChoice:Promise.resolve({outcome:'accepted'})};
listener(event);assert(prevented===1,'event not prevented');assert(api.getPrompt()===event,'prompt not shared');
(async()=>{const result=await context.window.installApp();assert(result.handled,'button did not handle prompt');assert(promptCalls===1,'prompt must run exactly once');assert(api.getPrompt()===null,'prompt not cleared');const noPrompt=await context.window.installApp();assert(noPrompt==='fallback'&&fallbackCalls===1,'fallback without prompt failed');assert(promptCalls===1,'consumed prompt was reused');console.log('Patient install prompt smoke: OK')})().catch(err=>{console.error(err);process.exit(1)});
