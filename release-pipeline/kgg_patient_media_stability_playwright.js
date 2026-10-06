#!/usr/bin/env node
"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(v,m){if(!v)throw new Error(m)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
async function main(){
  const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
  await new Promise(r=>server.listen(0,"127.0.0.1",r));
  const port=server.address().port,browser=await chromium.launch({headless:true});
  const ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage(),errors=[];
  page.on("pageerror",e=>errors.push(String(e)));
  try{
    await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1"});
    const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="220"><rect width="320" height="220" fill="white"/><rect x="30" y="30" width="260" height="160" rx="20" fill="#334155"/><circle cx="160" cy="110" r="54" fill="#16a34a"/></svg>').toString("base64");
    const media={id:"media-stability-demo",type:"image",src:"data:image/svg+xml;base64,"+svg,mime:"image/svg+xml"};
    const plan={i:"media-stability",t:"Media stability",v:1,d:6,e:[["Stability Demo",1,"B","kg","Wdh","","",[media]]]};
    await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"domcontentloaded",timeout:30000});
    await page.waitForFunction(()=>window.KGGPatientMediaRetryCache&&document.querySelector(".kggMediaBox.ready img")?.complete,{timeout:15000});
    await page.waitForTimeout(120);
    const before=await page.evaluate(()=>{
      const card=document.querySelector("#list .ex"),box=card?.querySelector(".kggMediaBox.ready"),img=box?.querySelector("img"),thumb=card?.querySelector(".kggCardThumb img");
      return{src:img?.src||"",thumbSrc:thumb?.src||"",ready:!!img,thumbReady:!!thumb};
    });
    assert(before.ready&&before.thumbReady,"fixture media did not reach ready state: "+JSON.stringify(before));

    const direct=await page.evaluate(()=>{
      const card=document.querySelector("#list .ex"),thumbBefore=card.querySelector(".kggCardThumb img"),boxBefore=card.querySelector(".kggMediaBox.ready"),imgBefore=boxBefore&&boxBefore.querySelector("img");
      const src=imgBefore&&imgBefore.src;
      window.KGGPatientMediaRetryCache.render();
      const thumbAfter=card.querySelector(".kggCardThumb img"),boxAfter=card.querySelector(".kggMediaBox"),imgAfter=boxAfter&&boxAfter.querySelector("img");
      return{sameThumbNode:thumbAfter===thumbBefore,sameImageNode:imgAfter===imgBefore,ready:boxAfter?.classList.contains("ready")||false,loading:boxAfter?.classList.contains("loading")||false,sameSrc:!!imgAfter&&imgAfter.src===src};
    });
    assert(direct.sameThumbNode,"media render replaced an unchanged thumbnail node: "+JSON.stringify(direct));
    assert(direct.ready&&!direct.loading&&direct.sameSrc,"media render regressed a ready image: "+JSON.stringify(direct));

    const rerender=await page.evaluate(async()=>{
      const samples=[];
      const capture=()=>{const card=document.querySelector("#list .ex"),box=card?.querySelector(".kggMediaBox"),img=box?.querySelector("img");samples.push({ready:!!(box&&box.classList.contains("ready")&&img),loading:!!(box&&box.classList.contains("loading")),src:img?.src||"",text:box?.textContent||""})};
      render();
      capture();
      for(let i=0;i<8;i++)await new Promise(resolve=>requestAnimationFrame(()=>{capture();resolve()}));
      return samples;
    });
    const bad=rerender.findIndex(x=>!x.ready||x.loading||/Bild wird geladen/i.test(x.text));
    assert(bad<0,"ready exercise image disappeared/re-entered loading during app render at sample "+bad+": "+JSON.stringify(rerender));

    assert(errors.length===0,"page errors: "+errors.join(" | "));
    console.log("Patient media stability Playwright: PASS "+JSON.stringify({direct,frames:rerender.length}));
  }finally{
    await ctx.close();await browser.close();await new Promise(r=>server.close(r));
  }
}
main().catch(e=>{console.error("Patient media stability Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
