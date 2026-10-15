#!/usr/bin/env node
"use strict";

// Synthetic patient settings parity. No network, account, device, or real patient data.
const fs=require("node:fs"),http=require("node:http"),path=require("node:path");
const {chromium,webkit}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const ENGINE=process.env.KGG_SETTINGS_BROWSER||"chromium";
const MODES=["legacy","react-p7","react-p8"];
const assert=(condition,message)=>{if(!condition)throw new Error(message)};
const encode=value=>Buffer.from(JSON.stringify(value),"utf8").toString("base64url");
const types={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",
  ".css":"text/css; charset=utf-8",".json":"application/json; charset=utf-8"};
function server(){
  return http.createServer((request,response)=>{
    const pathname=new URL(request.url,"http://localhost").pathname;
    const name=decodeURIComponent(pathname==="/"?"/index.html":pathname);
    const file=path.resolve(ROOT,"."+name);
    if(!file.startsWith(ROOT+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){
      response.writeHead(404).end("missing");return;
    }
    response.setHeader("Content-Type",types[path.extname(file)]||"application/octet-stream");
    response.setHeader("Cache-Control","no-store");
    fs.createReadStream(file).pipe(response);
  });
}
async function openCard(page,index=0){
  const card=page.locator("#list .ex").nth(index);
  for(let attempt=0;attempt<5;attempt++){
    if(await card.evaluate(node=>node.classList.contains("kggOpen")))return card;
    await card.locator("h3").evaluate(node=>node.click());
    try{
      await page.waitForFunction(i=>document.querySelectorAll("#list .ex")[i]?.classList.contains("kggOpen"),
        index,{timeout:850});return card;
    }catch{await page.waitForTimeout(90)}
  }
  throw new Error("exercise card not opening: "+index);
}
async function edit(page,options){
  const card=await openCard(page);
  await card.locator(".kggCardDots").click();
  const sheet=page.locator("#kggSettingsSheet");
  await sheet.waitFor({state:"visible"});
  if(options.side)await sheet.locator("#kggSetSide").selectOption(options.side);
  if(options.unitA!==undefined)await sheet.locator("#kggSetUnitA").fill(options.unitA);
  if(options.unitB!==undefined)await sheet.locator("#kggSetUnitB").fill(options.unitB);
  if(options.pain)await sheet.locator("#kggSetPainMode").selectOption(options.pain);
  await sheet.locator(options.cancel?"#kggSetCancel":"#kggSetSave").click();
  await page.waitForFunction(()=>document.getElementById("kggSettingsSheet")?.hidden===true);
  await page.waitForTimeout(160); // existing legacy apply/render is scheduled after save
}
async function read(page){
  return page.evaluate(()=>{
    const at=(ei,set,side,key,day)=>String(v[k(ei,set,side,key,day)]??"");
    const stored=JSON.parse(localStorage.getItem("kggCurrentPlanV1")||"null");
    const settings=JSON.parse(localStorage.getItem("kggPatientExerciseSettingsV1")||"{}");
    const card=document.querySelector("#list .ex");
    const firstRows=rows(1);
    return {
      side:p.ex[0].side,otherSide:p.ex[1].side,
      unitA:p.ex[0].u,unitB:p.ex[0].m,pain:p.ex[0].painMode,
      planSide:stored?.plan?.e?.[0]?.[2],
      settings:settings["settings-side-parity|transfer"]||{},
      b1a:at(0,1,"B","a",1),b1b:at(0,1,"B","b",1),
      b2a:at(0,2,"B","a",1),b2b:at(0,2,"B","b",1),
      l1a:at(0,1,"L","a",1),l1b:at(0,1,"L","b",1),
      r1a:at(0,1,"R","a",1),r1b:at(0,1,"R","b",1),
      l2a:at(0,2,"L","a",1),r2a:at(0,2,"R","a",1),
      day2B:at(0,1,"B","a",2),day2L:at(0,1,"L","a",2),
      day2R:at(0,1,"R","a",2),day3B:at(0,2,"B","a",3),
      day3L:at(0,2,"L","a",3),day3R:at(0,2,"R","a",3),
      other:at(1,1,"B","a",1),
      perSet:card?.querySelectorAll(".kggSetPain").length||0,
      inactiveCount:card?.querySelectorAll("input.num.kggUnitInactive").length||0,
      effectiveA:String(firstRows?.[0]?.[5]?.[0]?.[0]??""),
      effectiveB:String(firstRows?.[0]?.[5]?.[0]?.[1]??"")
    };
  });
}
async function runCase(browser,base,mode){
  const context=await browser.newContext({viewport:{width:390,height:844},
    isMobile:true,hasTouch:true,serviceWorkers:"block"});
  const page=await context.newPage(),errors=[];
  page.setDefaultTimeout(6500);
  page.on("pageerror",e=>errors.push(String(e)));
  const plan={i:"settings-side-parity",t:"Synthetic settings parity",v:1,d:6,e:[
    ["Transfer",2,"B","kg","Wdh"],["Unchanged",1,"B","kg","Wdh"]
  ]};
  const url=base+"/?kggReactPad="+(mode==="legacy"?"0":"1")+
    (mode==="react-p8"?"&kggReactGrid=1":"")+
    "&plan="+encodeURIComponent("KGGH2:"+encode(plan));
  try{
    await page.addInitScript(()=>{localStorage.kggInstallAsked="1"});
    await page.goto(url,{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.__kggPatientCardSettings&&
      document.querySelectorAll("#list .ex").length===2&&
      document.body.classList.contains("kggAlwaysCollapsed"));
    await page.evaluate(()=>{
      const put=(ei,set,side,key,day,value)=>{v[k(ei,set,side,key,day)]=String(value)};
      put(0,1,"B","a",1,20);put(0,1,"B","b",1,10);
      put(0,2,"B","a",1,25);put(0,2,"B","b",1,12);
      put(0,1,"B","a",2,30);put(0,1,"B","b",2,15);
      put(0,1,"R","a",1,91); // existing opposite-side value must never be overwritten
      put(1,1,"B","a",1,70); // another exercise must remain untouched
      save();render();
    });
    const card=await openCard(page);
    await card.locator(".kggCompactTapProxy").first().click();
    if(mode!=="legacy"){
      await page.waitForFunction(()=>document.body.classList.contains("kggReactNumpadHeaderV1"));
      if(mode==="react-p8")await page.waitForFunction(()=>
        document.body.classList.contains("kggReactNumpadGridV1")&&
        document.querySelectorAll(".kgg-react-numpad-grid__key").length===12);
      else assert(!(await page.evaluate(()=>document.body.classList.contains("kggReactNumpadGridV1"))),
        "P7-only unexpectedly mounted P8 grid");
    }
    await page.locator("#pad .padCancel").click();
    const initial=await read(page);
    assert(initial.side==="B"&&initial.b1a==="20"&&initial.r1a==="91"&&
      initial.other==="70","incorrect synthetic fixture: "+JSON.stringify(initial));

    await edit(page,{side:"LR",cancel:true});
    assert((await read(page)).side==="B","Cancel changed side");
    await edit(page,{side:"LR"});
    const split=await read(page);
    assert(split.side==="LR"&&split.planSide==="LR","B-to-LR side not stored");
    assert(split.l1a==="20"&&split.l1b==="10"&&split.r1a==="91"&&
      split.r1b==="10"&&split.l2a==="25"&&split.r2a==="25",
      "B-to-LR incorrectly copied or overwritten values: "+JSON.stringify(split));
    assert(split.day2B==="30"&&split.day2L==="30"&&split.day2R==="30"&&
      split.b1a==="20"&&split.other==="70"&&split.otherSide==="B",
      "other day/exercise modified during side split: "+JSON.stringify(split));

    await page.reload({waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.__kggPatientCardSettings&&
      document.querySelectorAll("#list .ex").length===2);
    const restored=await read(page);
    assert(restored.side==="LR"&&restored.l1a==="20"&&restored.r1a==="91"&&
      restored.other==="70","reload did not restore LR mode and values: "+JSON.stringify(restored));
    await page.evaluate(()=>{
      v[k(0,2,"L","a",3)]="17";v[k(0,2,"R","a",3)]="19";save();
    });
    await edit(page,{side:"BI",cancel:true});
    assert((await read(page)).side==="LR","Cancel unexpectedly collapsed LR");
    await edit(page,{side:"BI"});
    const collapsed=await read(page);
    assert(collapsed.side==="BI"&&collapsed.planSide==="BI"&&
      collapsed.b1a==="20"&&collapsed.b2a==="25"&&collapsed.day3B==="17"&&
      collapsed.day3L==="17"&&collapsed.day3R==="19"&&collapsed.other==="70",
      "LR-to-B overwrite/copy rule failed: "+JSON.stringify(collapsed));

    await edit(page,{unitA:"keine",unitB:"Sek.",pain:"set"});
    await page.waitForFunction(()=>document.querySelector("#list .ex .kggSetPain"));
    const units=await read(page);
    assert(units.unitA==="keine"&&units.unitB==="Sek."&&units.pain==="set"&&
      units.settings.unitA==="keine"&&units.settings.unitB==="Sek."&&
      units.settings.painMode==="set"&&units.perSet===2&&units.inactiveCount>0,
      "settings/pain/inactive field not saved: "+JSON.stringify(units));
    assert(units.b1a==="20"&&units.effectiveA===""&&units.effectiveB==="10",
      "inactive unit unexpectedly deleted or counted: "+JSON.stringify(units));

    await page.reload({waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.__kggPatientCardSettings&&
      document.querySelectorAll("#list .ex").length===2);
    const final=await read(page);
    assert(final.side==="BI"&&final.unitA==="keine"&&final.unitB==="Sek."&&
      final.pain==="set"&&final.day3B==="17"&&final.b1a==="20"&&
      final.other==="70","reloaded settings/values changed: "+JSON.stringify(final));
    assert(errors.length===0,"page errors in "+mode+": "+errors.join(" | "));
    console.log("KGG_PATIENT_SETTINGS_PARITY_PASS "+JSON.stringify({
      engine:ENGINE,mode,cancel:true,split:true,day2:true,
      existingRightPreserved:true,collapse:true,reload:true,
      unitInactivePreservesHistory:true,perSetPain:true,
      sourceSha:process.env.KGG_SETTINGS_HEAD_SHA||"local"
    }));
  }finally{await context.close()}
}
async function main(){
  assert(ENGINE==="chromium"||ENGINE==="webkit","unsupported settings browser");
  const web=server();await new Promise(ok=>web.listen(0,"127.0.0.1",ok));
  let browser;
  try{
    browser=await (ENGINE==="webkit"?webkit:chromium).launch({headless:true});
    const base="http://127.0.0.1:"+web.address().port;
    for(const mode of MODES)await runCase(browser,base,mode);
    console.log("KGG patient settings-side parity: PASS "+ENGINE+" ("+MODES.length+" modes)");
  }finally{if(browser)await browser.close();await new Promise(ok=>web.close(ok))}
}
const timeout=setTimeout(()=>{
  console.error("KGG patient settings parity: bounded 150-second timeout");
  process.exit(124);
},150000);
main().then(()=>clearTimeout(timeout)).catch(err=>{
  clearTimeout(timeout);console.error("KGG patient settings parity: FAIL "+(err.stack||err));
  process.exitCode=1;
});
