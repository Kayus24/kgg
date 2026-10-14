#!/usr/bin/env node
"use strict";
// Reuses the existing synthetic media-stability browser smoke. Parity is opt-in.
const fs=require("fs"),http=require("http"),path=require("path"),{chromium,webkit}=require("playwright");
const {execFileSync}=require("node:child_process");
const ROOT=path.resolve(__dirname,"..");
const PARITY=process.env.KGG_MEDIA_PARITY==="1";
const ENGINE=process.env.KGG_MEDIA_BROWSER||"chromium";
const OUT=process.env.KGG_PARITY_OUT?path.resolve(process.env.KGG_PARITY_OUT):null;
if(PARITY&&!["chromium","webkit"].includes(ENGINE))throw new Error("Unsupported media parity engine");
if(PARITY&&OUT&&path.basename(OUT)!=="patient-ui-parity")throw new Error("Invalid isolated evidence directory");
const SHA=PARITY?(process.env.KGG_PARITY_HEAD_SHA||
  execFileSync("git",["rev-parse","HEAD"],{cwd:ROOT,encoding:"utf8"}).trim()):null;
if(PARITY&&!/^[a-f0-9]{40}$/i.test(SHA))throw new Error("Media parity requires exact candidate SHA");
function assert(v,m){if(!v)throw new Error(m)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":
  f.endsWith(".js")?"text/javascript; charset=utf-8":
  f.endsWith(".json")?"application/json; charset=utf-8":
  f.endsWith(".css")?"text/css; charset=utf-8":
  f.endsWith(".png")?"image/png":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0])
 .replace(/^\\/+/, "")||"index.html",target=path.resolve(ROOT,rel);
 return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
function startServer(){const server=http.createServer((req,res)=>{
 const f=fileFor(req.url);
 if(!f){res.statusCode=404;return res.end("404")}
 res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");
 res.end(fs.readFileSync(f))});
 return new Promise(resolve=>server.listen(0,"127.0.0.1",
  ()=>resolve({server,port:server.address().port})))}
function inlineFixture(){
 const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="220"><rect width="320" height="220" fill="white"/><rect x="30" y="30" width="260" height="160" rx="20" fill="#334155"/><circle cx="160" cy="110" r="54" fill="#16a34a"/></svg>').toString("base64");
 const media={id:"media-stability-demo",type:"image",src:"data:image/svg+xml;base64,"+svg,mime:"image/svg+xml"};
 return {i:"media-stability",t:"Media stability",v:1,d:6,
  e:[["Stability Demo",1,"B","kg","Wdh","","",[media]]]}
}
async function runVariant(browser,port,mode){
 const ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"});
 const page=await ctx.newPage(),errors=[];
 page.on("pageerror",e=>errors.push(String(e)));
 try{
  await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1"});
  const flag=mode===null?"":"kggReactPad="+(mode==="react"?"1":"0")+"&";
  await page.goto("http://127.0.0.1:"+port+"/?"+flag+"plan="+
   encodeURIComponent("KGGH2:"+enc(inlineFixture())),
   {waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.KGGPatientMediaRetryCache&&
    document.querySelector(".kggMediaBox.ready img")?.complete,{timeout:15000});
  await page.waitForTimeout(120);
  const before=await page.evaluate(()=>{
   const card=document.querySelector("#list .ex"),
    box=card?.querySelector(".kggMediaBox.ready"),
    img=box?.querySelector("img"),thumb=card?.querySelector(".kggCardThumb img");
   return {src:img?.src||"",thumbSrc:thumb?.src||"",
    ready:!!img,thumbReady:!!thumb,
    complete:!!img?.complete,width:img?.naturalWidth||0,height:img?.naturalHeight||0};
  });
  assert(before.ready&&before.thumbReady,"fixture media did not reach ready state: "+JSON.stringify(before));
  assert(before.complete&&before.width>0&&before.height>0&&
   before.src.startsWith("data:image/svg+xml;base64,"),
   "synthetic media failed decoding: "+JSON.stringify(before));
  const direct=await page.evaluate(()=>{
   const card=document.querySelector("#list .ex"),thumbBefore=card.querySelector(".kggCardThumb img"),
    boxBefore=card.querySelector(".kggMediaBox.ready"),imgBefore=boxBefore?.querySelector("img"),
    src=imgBefore?.src;
   window.KGGPatientMediaRetryCache.render();
   const thumbAfter=card.querySelector(".kggCardThumb img"),
    boxAfter=card.querySelector(".kggMediaBox"),
    imgAfter=boxAfter?.querySelector("img");
   return {sameThumbNode:thumbAfter===thumbBefore,
    sameImageNode:imgAfter===imgBefore,ready:!!boxAfter?.classList.contains("ready"),
    loading:!!boxAfter?.classList.contains("loading"),sameSrc:!!imgAfter&&imgAfter.src===src};
  });
  assert(direct.sameThumbNode,"media render replaced unchanged thumbnail node: "+JSON.stringify(direct));
  assert(direct.ready&&!direct.loading&&direct.sameSrc,
   "media render regressed an already ready image: "+JSON.stringify(direct));
  const rerender=await page.evaluate(async()=>{
   const samples=[];
   const capture=()=>{const card=document.querySelector("#list .ex"),
     box=card?.querySelector(".kggMediaBox"),img=box?.querySelector("img");
     samples.push({ready:!!(box&&box.classList.contains("ready")&&img),
      loading:!!box?.classList.contains("loading"),src:img?.src||"",text:box?.textContent||""})};
   render();capture();
   for(let i=0;i<8;i++)await new Promise(resolve=>requestAnimationFrame(()=>{capture();resolve()}));
   return samples;
  });
  const bad=rerender.findIndex(x=>!x.ready||x.loading||/Bild wird geladen/i.test(x.text)||x.src!==before.src);
  assert(bad<0,"media disappeared or reloaded across app frames at "+bad+": "+JSON.stringify(rerender));
  if(PARITY){
   const card=page.locator("#list .ex").first();
   await card.locator("h3").click();
   await page.waitForFunction(()=>document.querySelector("#list .ex")?.classList.contains("kggOpen"),
    null,{timeout:8000});
   const proxy=card.locator(".kggCompactTapProxy[data-kgg-key='a']").first();
   await proxy.waitFor({state:"visible",timeout:8000});
   await proxy.click();
   await page.locator("#pad .padCancel").waitFor({state:"visible",timeout:8000});
   if(mode==="react")await page.locator("[data-kgg-react-numpad-header='v1']")
     .waitFor({state:"attached",timeout:8000});
   const mounted=await page.evaluate(()=>document.body.classList.contains("kggReactNumpadHeaderV1"));
   assert(mounted===(mode==="react"),"React/Legacy media-variant mount mismatch");
   await page.locator("#pad .padCancel").click();
   await page.locator("#pad").waitFor({state:"hidden",timeout:8000});
   if(OUT){
    fs.mkdirSync(OUT,{recursive:true});
    await page.screenshot({path:path.join(OUT,"media-"+mode+".png"),animations:"disabled"});
   }
  }
  assert(errors.length===0,"media page errors: "+errors.join(" | "));
  return {mode:mode??"standalone",src:before.src,thumbSrc:before.thumbSrc,
   dimensions:[before.width,before.height],ready:before.ready,
   thumbReady:before.thumbReady,direct,frames:rerender.length,
   states:rerender.map(x=>({ready:x.ready,loading:x.loading})),
   variantMounted:PARITY};
 }finally{await ctx.close()}
}
async function main(){
 const {server,port}=await startServer(),browser=await (PARITY?{chromium,webkit}[ENGINE]:chromium).launch({headless:true});
 try{
  if(!PARITY){
   const standalone=await runVariant(browser,port,null);
   console.log("Patient media stability Playwright: PASS "+JSON.stringify({
    direct:standalone.direct,frames:standalone.frames}));
   return;
  }
  const results=[];
  for(const mode of ["legacy","react"])results.push(await runVariant(browser,port,mode));
  const comparable=entry=>({src:entry.src,thumbSrc:entry.thumbSrc,
   dimensions:entry.dimensions,ready:entry.ready,thumbReady:entry.thumbReady,
   direct:entry.direct,frames:entry.frames,states:entry.states});
  assert(JSON.stringify(comparable(results[0]))===JSON.stringify(comparable(results[1])),
   "Media lifecycle semantics differ between Legacy and React");
  if(OUT)for(const entry of results){
   const proof={schema:1,status:"PASS",syntheticOnly:true,engine:ENGINE,
    mode:entry.mode,sourceSha:SHA,featureIds:["PAT-MEDIA-006","PAT-MEDIA-011"],
    assertions:{inlineImageDecoded:true,thumbnailReady:true,thumbnailNodeStable:true,
     readyCachePreserved:true,repeatedRerenderNoLoading:true,
     legacyReactMediaSemanticParity:true,reactOwnerVerified:true,noPageErrors:true},
    imageDimensions:entry.dimensions,frameSamples:entry.frames,
    limitation:"Inline synthetic SVG only. Does not certify external sources, licensing, visual lightbox, prefetch, hardware or network retry"};
   fs.writeFileSync(path.join(OUT,"media-"+entry.mode+".json"),JSON.stringify(proof,null,2)+"\\n");
  }
  console.log(JSON.stringify({status:"PASS",engine:ENGINE,syntheticOnly:true,
   sourceSha:SHA,modes:results.map(x=>({mode:x.mode,frames:x.frames,dimensions:x.dimensions}))}));
 }finally{
  await browser.close();
  if(typeof server.closeAllConnections==="function")server.closeAllConnections();
  await Promise.race([new Promise(resolve=>server.close(()=>resolve())),
   new Promise(resolve=>setTimeout(resolve,2000))]);
 }
}
const alarm=setTimeout(()=>{console.error("KGG media parity: bounded 120s timeout");process.exit(124)},120000);
main().then(()=>clearTimeout(alarm)).catch(e=>{clearTimeout(alarm);
 console.error("Patient media stability Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
