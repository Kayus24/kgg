#!/usr/bin/env node
"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(v,m){if(!v)throw new Error(m)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".svg")?"image/svg+xml":f.endsWith(".webp")?"image/webp":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
async function openCard(card){if(await card.evaluate(e=>e.classList.contains("kggOpen")))return;await card.locator("h3").evaluate(el=>el.click());await card.page().waitForFunction(el=>el.classList.contains("kggOpen"),await card.elementHandle())}
async function main(){
 const registry=path.join(ROOT,"patient-exercise-media-sources.js");
 assert(fs.existsSync(registry),"patient exercise media source registry is missing");
 const source=fs.readFileSync(registry,"utf8");
 for(const required of ["RepDB","Workout Guide","Everkinetic","CC BY-SA 4.0","repdb.co"])assert(source.includes(required),"registry source/attribution missing: "+required);
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const port=server.address().port,browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage(),errors=[];page.on("pageerror",e=>errors.push(String(e)));
 const exercises=[
  ["Beinpresse",3,"B","kg","Wdh"],
  ["Rudern sitzend",3,"LR","kg","Wdh"],
  ["Brustpresse Maschine",3,"B","kg","Wdh"],
  ["Schulterdrücken",3,"B","kg","Wdh"],
  ["Latzug",3,"B","kg","Wdh"],
  ["Beinbeuger sitzend",3,"LR","kg","Wdh"],
  ["Plank",3,"B","keine","Sek."],
  ["Seitstütz mit Hüftsenken",3,"B","keine","Sek."],
  ["Rückenstrecker",3,"B","kg","Wdh"],
  ["Beinschwünge",3,"LR","keine","Wdh"]
 ];
 try{
  await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1"});
  const plan={i:"media-source-smoke",t:"Media source smoke",v:1,d:6,e:exercises};
  await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.KGGExerciseMediaSources&&window.KGGPatientMediaRetryCache,{timeout:10000});
  const audit=await page.evaluate(()=>window.KGGExerciseMediaSources.audit());
  assert(audit.repdb>=3&&audit.workoutGuide>=3&&audit.everkinetic>=1,"source mix is incomplete: "+JSON.stringify(audit));
  await page.waitForFunction(()=>document.querySelectorAll("#list .ex").length===10);
  for(let i=0;i<10;i++){
    const card=page.locator("#list .ex").nth(i);await openCard(card);
    await card.locator(".kggMediaBox.ready img").first().waitFor({state:"visible",timeout:30000});
    const result=await card.evaluate(el=>{
      const imgs=[...el.querySelectorAll(".kggMediaBox.ready img")],boxes=[...el.querySelectorAll(".kggMediaBox.ready")];
      const dims=imgs.map(img=>({w:img.naturalWidth,h:img.naturalHeight}));
      let nonBlank=0;
      for(const img of imgs){
        try{
          const c=document.createElement("canvas");c.width=64;c.height=64;const x=c.getContext("2d",{willReadFrequently:true}),bg=getComputedStyle(img).backgroundColor.match(/\d+/g)||[255,255,255];x.fillStyle="rgb("+bg[0]+","+bg[1]+","+bg[2]+")";x.fillRect(0,0,64,64);x.drawImage(img,0,0,64,64);const d=x.getImageData(0,0,64,64).data;let min=255,max=0;
          for(let p=0;p<d.length;p+=4){const lum=.2126*d[p]+.7152*d[p+1]+.0722*d[p+2];if(lum<min)min=lum;if(lum>max)max=lum}
          if(max-min>20)nonBlank++;
        }catch(_){}
      }
      return{dims,nonBlank,sources:boxes.map(b=>b.dataset.kggMediaSource||""),credits:boxes.map(b=>b.querySelector("small")?.textContent||"")};
    });
    assert(result.dims.length>=1&&result.dims.every(x=>x.w>0&&x.h>0),"image did not decode for exercise "+i+": "+JSON.stringify(result));
    assert(result.nonBlank>=1,"exercise image rendered as blank/white placeholder for exercise "+i+": "+JSON.stringify(result));
    assert(result.sources.every(Boolean),"source metadata missing for exercise "+i+": "+JSON.stringify(result));
    assert(result.credits.every(Boolean),"visible attribution missing for exercise "+i+": "+JSON.stringify(result));
  }
  assert(errors.length===0,"page errors: "+errors.join(" | "));
  console.log("Patient exercise media sources Playwright: PASS "+JSON.stringify(audit));
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error("Patient exercise media sources Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
