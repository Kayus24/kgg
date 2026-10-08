#!/usr/bin/env node
"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const TMP=path.join(ROOT,".tmp");fs.mkdirSync(TMP,{recursive:true});
function assert(v,m){if(!v)throw new Error(m)}
function enc(x){return Buffer.from(JSON.stringify(x),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".png")?"image/png":f.endsWith(".svg")?"image/svg+xml":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(new URL(url,"http://x").pathname).replace(/^\/+/,"")||"index.html";const p=path.resolve(ROOT,rel);return p.startsWith(ROOT)&&fs.existsSync(p)&&fs.statSync(p).isFile()?p:null}
function media(id,label){const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="500" height="420"><rect width="500" height="420" fill="#eef2ff"/><rect x="30" y="30" width="440" height="360" rx="28" fill="#cbd5e1"/><text x="250" y="220" font-size="38" text-anchor="middle" fill="#111827">'+label+'</text></svg>').toString("base64");return{id,type:"image",src:"data:image/svg+xml;base64,"+svg,mime:"image/svg+xml"}}
const PLAN={i:"flicker-blackbox",t:"Flicker Root Cause",v:1,d:6,e:[
 ["Adduction Machine",3,"B","kg","Wdh","","",[media("adduct","ADDUCTION")]],
 ["Backextensions",3,"B","kg","Wdh","","",[media("backext","BACKEXTENSIONS")]],
 ["Add15 15 Add",3,"B","Add","Wdh","15","15",[]]
]};
const TARGET=1;
const CODE="KGGH2:"+enc(PLAN);

async function openCard(page,index){
 const card=page.locator("#list .ex").nth(index);
 for(let i=0;i<4;i++){
   if(await card.evaluate(e=>e.classList.contains("kggOpen")))return card;
   await card.locator("h3").click();
   await page.waitForTimeout(80);
 }
 throw new Error("card did not open");
}
async function inputs(page,cardIndex,setIndex){
 return page.locator("#list .ex").nth(cardIndex).locator(":scope > .set").nth(setIndex).locator("input.num");
}
async function clickInput(page,input){
 const compact=await page.evaluate(()=>document.body.classList.contains("kggSetViewCompact"));
 if(!compact){await input.click();return}
 const proxyIndex=await input.evaluate(el=>[...el.parentElement.querySelectorAll(".kggCompactTapProxy")].findIndex(proxy=>proxy.__kggInput===el));
 assert(proxyIndex>=0,"compact input proxy missing");
 await input.locator("xpath=..").locator(".kggCompactTapProxy").nth(proxyIndex).click();
}
async function main(){
 const server=http.createServer((req,res)=>{
   const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}
   res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f));
 });
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const port=server.address().port;
 const browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,serviceWorkers:"block"});
 await ctx.tracing.start({screenshots:true,snapshots:true,sources:true});
 const page=await ctx.newPage();const pageErrors=[];page.on("pageerror",e=>pageErrors.push(String(e)));
 try{
   await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1";localStorage.kggPatientSetViewModeV1="compact"});
   await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent(CODE),{waitUntil:"domcontentloaded",timeout:30000});
   await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed")&&document.querySelectorAll("#list .ex").length>=3,{timeout:15000});
   await page.evaluate(idx=>{const set=(s,key,value)=>{v[k(idx,s,'B',key,1)]=String(value)};set(1,'a',12);set(1,'b',20);set(2,'a',1);set(2,'b',20);set(3,'a',1);set(3,'b',20);save();render()},TARGET);
   const card=await openCard(page,TARGET);
   await page.waitForFunction(idx=>{const c=document.querySelectorAll("#list .ex")[idx];return c&&c.classList.contains("kggOpen")},TARGET,{timeout:4000});
   await page.waitForTimeout(350);

   await page.evaluate(()=>{
     const D=window.__kggFlickerBlackBox={events:[],transitions:[],seq:0};
     const stamp=(type,data={})=>D.events.push({seq:++D.seq,t:performance.now(),type,...data});
     const shortStack=()=>String(new Error().stack||"").split("\n").slice(2,9).map(x=>x.trim());
     const ownerOfList=t=>{
       try{
         if(t===document.body)return{kind:"body"};
         const cards=[...document.querySelectorAll("#list .ex")];
         for(let i=0;i<cards.length;i++)if(cards[i].classList===t)return{kind:"card",index:i,title:cards[i].querySelector("h3")?.textContent||""};
       }catch(e){}
       return null;
     };
     const proto=DOMTokenList.prototype;
     for(const name of ["add","remove","toggle"]){
       const orig=proto[name];
       proto[name]=function(...args){
         const relevant=args.some(x=>x==="kggOpen"||x==="kggCardsCollapsed"||x==="kggAlwaysCollapsed");
         if(relevant)stamp("classList."+name,{args,owner:ownerOfList(this),stack:shortStack()});
         return orig.apply(this,args);
       };
     }
     const desc=Object.getOwnPropertyDescriptor(Element.prototype,"innerHTML");
     if(desc&&desc.set&&desc.get){
       Object.defineProperty(Element.prototype,"innerHTML",{configurable:true,enumerable:desc.enumerable,get:desc.get,set:function(v){
         if(this.id==="list"||this.closest?.("#list"))stamp("innerHTML",{id:this.id||"",className:this.className||"",length:String(v).length,stack:shortStack()});
         return desc.set.call(this,v);
       }});
     }
     for(const name of ["replaceChildren","append","prepend"]){
       const orig=Element.prototype[name];if(typeof orig!=="function")continue;
       Element.prototype[name]=function(...args){
         if(this.id==="list"||this.closest?.("#list"))stamp("dom."+name,{id:this.id||"",className:this.className||"",stack:shortStack()});
         return orig.apply(this,args);
       };
     }
     const wrapFn=name=>{
       try{
         const orig=window[name];if(typeof orig!=="function")return;
         window[name]=function(...args){stamp("fn."+name,{stack:shortStack(),arg0:args[0]?.className||args[0]||null});return orig.apply(this,args)};
       }catch(e){}
     };
     ["render","put","openPad","closePad"].forEach(wrapFn);
     for(const name of ["scrollBy","scrollTo"]){const orig=window[name];if(typeof orig==='function')window[name]=function(...args){stamp('window.'+name,{args,scrollY:window.scrollY,stack:shortStack()});return orig.apply(this,args)}}
     if(typeof Element.prototype.scrollIntoView==='function'){const orig=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(...args){stamp('element.scrollIntoView',{id:this.id||'',className:this.className||'',title:this.closest?.('.ex')?.querySelector('h3')?.textContent||'',args,scrollY:window.scrollY,stack:shortStack()});return orig.apply(this,args)}}
     addEventListener('scroll',()=>stamp('scroll-event',{scrollY:window.scrollY}),{passive:true});
     const nativeFocus=HTMLElement.prototype.focus;
     HTMLElement.prototype.focus=function(...args){
       const isNum=!!this.matches?.('input.num'),padOpen=!document.getElementById('pad')?.classList.contains('hide');
       stamp('element.focus',{isNum,padOpen,args,scrollY:window.scrollY,stack:shortStack()});
       if(isNum&&padOpen){const y=window.scrollY;requestAnimationFrame(()=>{stamp('sim.android-focus-jump',{from:y,to:y+460});window.scrollTo(0,y+460);requestAnimationFrame(()=>window.scrollTo(0,y))})}
       return nativeFocus.apply(this,args);
     };
     try{
       const api=window.KGGPatientMediaRetryCache;
       if(api&&typeof api.render==="function"){const orig=api.render.bind(api);api.render=function(...args){stamp("fn.mediaRender",{stack:shortStack()});return orig(...args)}}
     }catch(e){}
     const list=document.querySelector("#list");
     const mo=new MutationObserver(ms=>{
       for(const m of ms){
         if(m.type==="attributes"){
           const el=m.target,card=el.closest?.(".ex");
           if(card)stamp("mutation.class",{index:[...document.querySelectorAll("#list .ex")].indexOf(card),old:m.oldValue,new:el.className,title:card.querySelector("h3")?.textContent||""});
           else if(el===document.body)stamp("mutation.bodyClass",{old:m.oldValue,new:el.className});
         }else if(m.type==="childList"){
           const parent=m.target;
           if(parent===list||parent.closest?.("#list"))stamp("mutation.childList",{parent:parent.id||parent.className||parent.tagName,added:m.addedNodes.length,removed:m.removedNodes.length});
         }
       }
     });
     mo.observe(document.body,{subtree:true,childList:true,attributes:true,attributeOldValue:true,attributeFilter:["class"]});
     try{
       const po=new PerformanceObserver(entries=>{
         for(const e of entries.getEntries())stamp("layout-shift",{value:e.value,hadRecentInput:e.hadRecentInput,sources:(e.sources||[]).map(s=>({node:s.node?.className||s.node?.id||s.node?.tagName||"",prev:s.previousRect,current:s.currentRect}))});
       });po.observe({type:"layout-shift",buffered:true});D.performanceObserver=true;
     }catch(e){D.performanceObserver=false;stamp("layout-shift-unavailable",{message:String(e)})}

     window.__kggArmTransition=function(label,cardIndex=0,duration=260){
       const rec={label,cardIndex,start:performance.now(),frames:[],startEvent:D.events.length};
       D.transitions.push(rec);
       const sample=()=>{
         const cards=[...document.querySelectorAll("#list .ex")],c=cards[cardIndex],box=c?.querySelector(".kggMediaBox"),img=box?.querySelector("img"),r=c?.getBoundingClientRect(),active=document.activeElement;
         rec.frames.push({t:performance.now(),open:!!c?.classList.contains("kggOpen"),h:r?.height??0,top:r?.top??0,bottom:r?.bottom??0,scrollY:window.scrollY,img:!!img,imgVisible:!!(img&&img.getBoundingClientRect().height>0&&getComputedStyle(img).visibility!=="hidden"&&getComputedStyle(img).display!=="none"),mediaClass:box?.className||"",active:active?.className||active?.id||active?.tagName||""});
       };
       sample();
       let raf=0,done=false;
       const tick=()=>{sample();if(!done)raf=requestAnimationFrame(tick)};raf=requestAnimationFrame(tick);
       return new Promise(resolve=>setTimeout(()=>{done=true;cancelAnimationFrame(raf);sample();rec.end=performance.now();rec.endEvent=D.events.length;resolve(rec)},duration));
     };
   });

   const baseline=await page.evaluate(idx=>{const c=document.querySelectorAll("#list .ex")[idx],r=c.getBoundingClientRect();return{open:c.classList.contains("kggOpen"),h:r.height,top:r.top}},TARGET);
   assert(baseline.open&&baseline.h>200,"baseline card not open: "+JSON.stringify(baseline));

   const kg0=(await inputs(page,TARGET,0)).nth(0),wdh0=(await inputs(page,TARGET,0)).nth(1);
   await clickInput(page,kg0);await page.waitForFunction(()=>!document.getElementById("pad").classList.contains("hide"),{timeout:4000});await page.waitForTimeout(850);

   const transitions=[];
   async function transition(label,target,sameRow=false){
     const box=await target.boundingBox();assert(box&&box.x>=0&&box.y>=0&&box.x+box.width<=390&&box.y+box.height<=844,'tap target not visible: '+label+' '+JSON.stringify(box));
     const p=page.evaluate(([label,idx])=>window.__kggArmTransition(label,idx,320),[label,TARGET]);
     await page.touchscreen.tap(box.x+box.width/2,box.y+box.height/2);
     const rec=await p;
     const bad=rec.frames.filter(f=>!f.open||f.h<baseline.h*0.6);
     const scrollRange=Math.max(...rec.frames.map(f=>f.scrollY))-Math.min(...rec.frames.map(f=>f.scrollY));
     transitions.push({label,sameRow,badFrames:bad.length,minH:Math.min(...rec.frames.map(f=>f.h)),maxH:Math.max(...rec.frames.map(f=>f.h)),scrollRange,imgLoss:rec.frames.filter(f=>!f.imgVisible).length,tap:{x:box.x+box.width/2,y:box.y+box.height/2}});
   }
   await transition("set1 kg->wdh",wdh0,true);
   await transition("set1 wdh->kg",kg0,true);
   await transition("set1 kg->wdh repeat",wdh0,true);
   await transition("set1 wdh->kg repeat",kg0,true);
   const s2=await inputs(page,TARGET,1),kg1=s2.nth(0),wdh1=s2.nth(1);
   await transition("set1 kg->set2 kg",kg1);
   await transition("set2 kg->wdh",wdh1);
   await transition("set2 wdh->kg",kg1);
   await transition("set2 kg->set1 wdh",wdh0);

   const data=await page.evaluate(()=>window.__kggFlickerBlackBox);
   fs.writeFileSync(path.join(TMP,"patient-flicker-blackbox.json"),JSON.stringify({baseline,transitions,data,pageErrors},null,2));
   const failTransitions=transitions.filter(x=>x.badFrames>0||(x.sameRow&&x.scrollRange>4));
   const destructive=data.events.filter(e=>e.type==="innerHTML"||e.type==="classList.remove"||e.type==="classList.toggle"||e.type==="mutation.childList"||e.type==="window.scrollBy"||e.type==="window.scrollTo"||e.type==="element.scrollIntoView"||e.type==="scroll-event");
   console.log("BLACKBOX_SUMMARY "+JSON.stringify({baseline,transitions,eventCount:data.events.length,destructiveCount:destructive.length,performanceObserver:data.performanceObserver,pageErrors}));
   if(failTransitions.length){const relevant=data.events.filter(e=>/^window\.scroll|^element\.focus|^sim\.android|^scroll-event$|^fn\.openPad$|^fn\.closePad$/.test(e.type));console.log("BLACKBOX_FAILURE_EVENTS "+JSON.stringify(relevant.slice(-60)))}
   assert(pageErrors.length===0,"page errors: "+pageErrors.join(" | "));
   assert(failTransitions.length===0,"TRANSIENT_SCROLL_FLICKER detected: "+JSON.stringify(failTransitions));
   console.log("Patient transient flicker black-box: PASS");
 }finally{
   await ctx.tracing.stop({path:path.join(TMP,"patient-flicker-blackbox-trace.zip")}).catch(()=>{});
   await ctx.close();await browser.close();await new Promise(r=>server.close(r));
 }
}
main().catch(e=>{console.error("Patient transient flicker black-box FAIL: "+(e.stack||e));process.exitCode=1});