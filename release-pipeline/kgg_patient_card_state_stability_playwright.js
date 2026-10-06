#!/usr/bin/env node
"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(v,m){if(!v)throw new Error(m)}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(new URL(url,"http://x").pathname).replace(/^\/+/,"")||"index.html";const p=path.resolve(ROOT,rel);return p.startsWith(ROOT)&&fs.existsSync(p)&&fs.statSync(p).isFile()?p:null}
const PLAN={i:"card-owner-regression",t:"Card owner regression",v:1,d:6,e:[["Adduction Machine",3,"B","kg","Wdh"],["Backextensions",3,"B","kg","Wdh"],["Third",3,"B","kg","Wdh"]]};
const CODE="KGGH2:"+Buffer.from(JSON.stringify(PLAN),"utf8").toString("base64url");
(async()=>{
 const server=http.createServer((req,res)=>{
   const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}
   let body=fs.readFileSync(f);
   if(f.endsWith("collapse-cards.js")){
     let s=body.toString("utf8");
     s=s.replace("document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();})();","window.__kggLegacyCollapseApply=apply;document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();})();");
     body=Buffer.from(s);
   }
   res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(body);
 });
 await new Promise(r=>server.listen(0,"127.0.0.1",r));
 const browser=await chromium.launch({headless:true}),ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage();
 try{
   await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1";localStorage.kggPatientSetViewModeV1="compact"});
   await page.goto("http://127.0.0.1:"+server.address().port+"/?plan="+encodeURIComponent(CODE),{waitUntil:"domcontentloaded",timeout:30000});
   await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed")&&typeof window.__kggLegacyCollapseApply==="function",{timeout:10000});
   const card=page.locator("#list .ex").nth(1);
   await card.click({position:{x:100,y:34}});
   await page.waitForFunction(()=>document.querySelectorAll("#list .ex")[1]?.classList.contains("kggOpen"),{timeout:4000});
   const before=await page.evaluate(()=>{const c=document.querySelectorAll("#list .ex")[1];return{open:c.classList.contains("kggOpen"),h:c.getBoundingClientRect().height}});
   const during=await page.evaluate(()=>{
     const c=document.querySelectorAll("#list .ex")[1],events=[];
     const mo=new MutationObserver(()=>events.push({t:performance.now(),open:c.classList.contains("kggOpen"),h:c.getBoundingClientRect().height}));
     mo.observe(c,{attributes:true,attributeFilter:["class"]});
     window.__kggLegacyCollapseApply();
     const immediate={open:c.classList.contains("kggOpen"),h:c.getBoundingClientRect().height};
     return new Promise(resolve=>setTimeout(()=>{mo.disconnect();resolve({immediate,events,final:{open:c.classList.contains("kggOpen"),h:c.getBoundingClientRect().height}})},50));
   });
   assert(before.open,"fixture card was not open");
   assert(during.immediate.open,"legacy collapse owner closed the active always-collapsed card: "+JSON.stringify({before,during}));
   assert(!during.events.some(x=>!x.open),"active card lost kggOpen transiently: "+JSON.stringify(during.events));
   console.log("Patient card-state single-owner Playwright: PASS "+JSON.stringify({before,during}));
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error("Patient card-state single-owner Playwright FAIL: "+(e.stack||e));process.exitCode=1});