"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(x,m){if(!x)throw new Error(m)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".png")?"image/png":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
async function openCard(card){for(let attempt=0;attempt<4;attempt++){if(await card.evaluate(e=>e.classList.contains("kggOpen")))return;const header=card.locator("h3");await header.evaluate(el=>el.click());await card.page().waitForTimeout(80)}throw new Error("card open state did not stabilize")}
async function clickKey(page,label){await page.locator("#pad .padGrid").getByRole("button",{name:label,exact:true}).click()}
async function enter(page,input,value){await input.click();for(const c of String(value))await clickKey(page,c==="."?",":c);await page.locator("#pad .padOk").click()}
async function loadPage(browser,port,{width=390,height=844,rootFont=16,userAgent,lang="de"}={}){
 const ctx=await browser.newContext({viewport:{width,height},hasTouch:true,isMobile:width<760,userAgent:userAgent||undefined});
 const page=await ctx.newPage(),errors=[];page.on("pageerror",e=>errors.push(String(e)));
 const plan={i:"adaptive-view-smoke",t:"Adaptive Patient UI",v:1,d:6,e:[
  ["LR3 kg",3,"LR","kg","Wdh","15","12"],
  ["No load",1,"B","keine","Sek."],
  ["Bar",1,"B","bar","Wdh"],
  ["Watt time",1,"B","Watt","Sek."],
  ["Long custom",3,"LR","Theraband-Stufe","Wiederholungen"],
  ["LR no load",3,"LR","keine","Sek."],
  ["Pain only",1,"B","keine","none"]
 ]};
 await page.addInitScript(lang=>{localStorage.removeItem("kggPatientSetViewModeV1");localStorage.kggInstallAsked="1";localStorage.setItem("kggPatientLang",lang)},lang);
 await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"networkidle"});
 await page.evaluate(rootFont=>{document.documentElement.style.fontSize=rootFont+"px"},rootFont);
 await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed"));await page.waitForTimeout(1250);
 return{ctx,page,errors};
}
async function geometryContract(page,width){
 const card=page.locator("#list .ex").nth(0);await openCard(card);
 const g=await card.evaluate(el=>{
  const sets=[...el.querySelectorAll(":scope > .set")].map(s=>{const r=s.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,width:r.width}});
  const inputs=[...el.querySelectorAll(":scope > .set input.num")].filter(x=>getComputedStyle(x).display!=="none").map(x=>{const r=x.getBoundingClientRect();return{w:r.width,left:r.left,right:r.right}});
  const cr=el.getBoundingClientRect();
  return{sets,inputs,card:{left:cr.left,right:cr.right},docW:document.documentElement.scrollWidth,clientW:document.documentElement.clientWidth};
 });
 assert(g.sets.length===3,"expected 3 sets");
 assert(Math.max(...g.sets.map(x=>x.top))-Math.min(...g.sets.map(x=>x.top))<=1,"3 sets are not on one row @"+width+": "+JSON.stringify(g.sets));
 assert(g.sets[0].left<g.sets[1].left&&g.sets[1].left<g.sets[2].left,"3 set order wrong");
 assert(g.sets[2].right<=g.card.right+1,"third set clips card @"+width);
 assert(g.docW<=g.clientW+1,"page overflow @"+width);
 const minInput=Math.min(...g.inputs.map(x=>x.w));
 assert(minInput>=28,"compact numeric fields too narrow @"+width+": "+minInput.toFixed(1)+"px");
}
async function unitContract(page){
 const noLoad=page.locator("#list .ex").nth(1);await openCard(noLoad);
 const diag=await noLoad.locator("input.num").evaluateAll(nodes=>({unit:window.p&&p.ex&&p.ex[1]?p.ex[1].u:null,items:nodes.map(n=>({display:getComputedStyle(n).display,inline:n.style.display,value:n.value,ph:n.placeholder}))}));
 const visible=diag.items.filter(n=>n.display!=="none").length;
 assert(visible===1,"no-load exercise exposes "+visible+" numeric fields: "+JSON.stringify(diag));
 const unitTexts=await noLoad.locator(".kggCompactUnit").allTextContents();
 assert(unitTexts.filter(Boolean).length===1&&/Sek\.?/i.test(unitTexts.join(" ")),"no-load unit display wrong: "+unitTexts.join("|"));
 const hit=await noLoad.locator("input.num").nth(1).evaluate(el=>{const r=el.getBoundingClientRect(),p=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return{rect:{left:r.left,top:r.top,width:r.width,height:r.height},hit:p?{tag:p.tagName,cls:p.className}:null}});assert(hit.hit&&hit.hit.tag==="INPUT","single active field is covered: "+JSON.stringify(hit));await enter(page,noLoad.locator("input.num").nth(1),"30");
 const progress=await noLoad.locator(".kggCardProgress").evaluate(el=>({expected:el.dataset.kggExpectedCount,filled:el.dataset.kggFilledCount,state:el.dataset.kggProgress}));
 assert(progress.expected==="1","no-load progress expects phantom field: "+JSON.stringify(progress));
 const summary=await page.evaluate(()=>typeof text==="function"?text(1):"");
 assert(!/\?\s*keine|keine\s*@/i.test(summary),"summary exposes phantom load field: "+summary);
}
async function lrSingleFieldContract(page){
 const card=page.locator("#list .ex").nth(5);await openCard(card);
 const counts=await card.evaluate(el=>{const inputs=[...el.querySelectorAll("input.num")];return{total:inputs.length,visible:inputs.filter(x=>getComputedStyle(x).display!=="none").length,re:el.querySelectorAll(".kggSideR").length,li:el.querySelectorAll(".kggSideL").length,units:[...el.querySelectorAll(".kggCompactUnit")].map(x=>x.textContent||"")}});
 assert(counts.total===12&&counts.visible===6&&counts.re===3&&counts.li===3,"LR single-field visibility wrong: "+JSON.stringify(counts));
 assert(counts.units.length===6&&counts.units.every(x=>/Sek\.?/i.test(x)),"LR single-field units wrong: "+JSON.stringify(counts.units));
 const progress=await card.locator(".kggCardProgress").evaluate(el=>({expected:el.dataset.kggExpectedCount,filled:el.dataset.kggFilledCount}));
 assert(progress.expected==="6","LR single-field progress expects phantom fields: "+JSON.stringify(progress));
 const active=card.locator("input.num:not(.kggUnitInactive)").first();await active.click();const labels=await page.locator("#kggPadPair button > span:first-child").allTextContents();
 assert(labels.length===1&&/Sek\.?/i.test(labels[0]),"LR single-field pad pair wrong: "+labels.join("|"));await page.locator("#pad .padCancel").click();
}
async function noValuesContract(page){
 const card=page.locator("#list .ex").nth(6);await openCard(card);
 const state=await card.evaluate(el=>({visible:[...el.querySelectorAll("input.num")].filter(x=>getComputedStyle(x).display!=="none").length,rowVisible:[...el.querySelectorAll(".bi,.lr")].filter(x=>getComputedStyle(x).display!=="none").length,rows:[...el.querySelectorAll(".bi,.lr")].map(x=>({cls:x.className,display:getComputedStyle(x).display,inline:x.style.display,inputs:[...x.querySelectorAll("input.num")].map(i=>({cls:i.className,display:getComputedStyle(i).display,ph:i.placeholder}))}))}));
 assert(state.visible===0&&state.rowVisible===0,"no-values exercise exposes numeric UI: "+JSON.stringify(state));
 const progress=await card.locator(".kggCardProgress").evaluate(el=>({expected:el.dataset.kggExpectedCount,state:el.dataset.kggProgress}));
 assert(progress.expected==="0"&&progress.state==="open","no-values progress contract wrong: "+JSON.stringify(progress));
 assert(await card.locator(".kggPainVerticalToggle").isVisible(),"no-values exercise lost pain control");
}
async function bilateralSingleCapsuleContract(page){
 const card=page.locator("#list .ex").nth(2);await openCard(card);
 const ui=await card.locator(":scope > .set").first().evaluate(set=>{
  const inner=set.querySelector(":scope > .bi"),os=getComputedStyle(set),s=getComputedStyle(inner);
  return{outerBorder:os.borderTopWidth,innerBorder:s.borderTopWidth,innerBackground:s.backgroundColor,padding:[s.paddingTop,s.paddingRight,s.paddingBottom,s.paddingLeft],visibleInputs:[...inner.querySelectorAll("input.num")].filter(x=>getComputedStyle(x).display!=="none").length};
 });
 assert(ui.outerBorder!=="0px","bilateral set lost its outer capsule");
 assert(ui.visibleInputs===2,"bilateral two-field set lost a value field: "+JSON.stringify(ui));
 assert(ui.innerBorder==="0px","bilateral set still has the redundant inner capsule border: "+JSON.stringify(ui));
 assert(ui.innerBackground==="rgba(0, 0, 0, 0)","bilateral inner wrapper is still visually boxed: "+JSON.stringify(ui));
 assert(ui.padding.every(x=>x==="0px"),"bilateral inner wrapper still adds capsule padding: "+JSON.stringify(ui));
}
async function barContract(page){
 const bar=page.locator("#list .ex").nth(2);await openCard(bar);await bar.locator("input.num").nth(0).click();
 const labels=await page.locator("#kggPadPair button > span:first-child").allTextContents();
 assert(labels.some(x=>x.trim()==="bar")&&labels.some(x=>/^Wdh$/i.test(x.trim())),"bar/Wdh pair labels wrong: "+labels.join("|"));
 await page.locator("#pad .padCancel").click();
}
async function englishUnitContract(page){
 const noLoad=page.locator("#list .ex").nth(1);await openCard(noLoad);
 const compact=await noLoad.locator(".kggCompactUnit").allTextContents();
 assert(compact.some(x=>/^sec$/i.test(x.trim())),"English compact seconds label wrong: "+compact.join("|"));
 await noLoad.locator("input.num").nth(1).click();const labels=await page.locator("#kggPadPair button > span:first-child").allTextContents();
 assert(labels.length===1&&/^sec$/i.test(labels[0].trim()),"English single-field pair label wrong: "+labels.join("|"));await page.locator("#pad .padCancel").click();
}
async function englishBarContract(page){
 const bar=page.locator("#list .ex").nth(2);await openCard(bar);await bar.locator("input.num").nth(0).click();const labels=await page.locator("#kggPadPair button > span:first-child").allTextContents();
 assert(labels.some(x=>x.trim()==="bar")&&labels.some(x=>/^reps$/i.test(x.trim())),"English bar/reps pair labels wrong: "+labels.join("|"));await page.locator("#pad .padCancel").click();
}
async function longUnitContract(page){
 const card=page.locator("#list .ex").nth(4);await openCard(card);
 const units=await card.locator(".kggCompactUnit").evaluateAll(nodes=>nodes.map(el=>{const r=el.getBoundingClientRect(),row=el.closest(".lr,.bi")?.getBoundingClientRect(),s=getComputedStyle(el);return{text:el.textContent||"",title:el.title||"",right:r.right,rowRight:row?row.right:0,overflow:s.overflow,whiteSpace:s.whiteSpace}}));
 assert(units.some(x=>x.title==="Theraband-Stufe")&&units.some(x=>x.title==="Wiederholungen"),"custom unit labels lost full semantic text: "+JSON.stringify(units));
 assert(units.every(x=>x.right<=x.rowRight+1&&x.overflow==="hidden"&&x.whiteSpace==="nowrap"),"custom compact unit overlaps row: "+JSON.stringify(units));
 const geom=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));assert(geom.doc<=geom.client+1,"custom units cause page overflow");
 await card.locator("input.num").first().click();const labels=await page.locator("#kggPadPair button > span:first-child").allTextContents();
 assert(labels.some(x=>x.trim()==="Theraband-Stufe")&&labels.some(x=>x.trim()==="Wiederholungen"),"custom pair labels truncated semantically: "+labels.join("|"));
 await page.locator("#pad .padCancel").click();
}
async function compactFieldPresentationContract(page){
 const card=page.locator("#list .ex").nth(0);await openCard(card);
 const input=card.locator("input.num").first(),unit=card.locator(".kggCompactUnit[data-kgg-key=\"a\"]").first();
 const initial=await Promise.all([
  input.evaluate(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,color:s.color,placeholder:getComputedStyle(el,"::placeholder").color,value:el.value,ph:el.placeholder}}),
  unit.evaluate(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,color:s.color}})
 ]);
 assert(initial[1].left>=initial[0].left-1&&initial[1].right<=initial[0].right+1&&initial[1].top>=initial[0].top-1&&initial[1].bottom<=initial[0].bottom+1,"compact unit is not inside its numeric field: "+JSON.stringify(initial));
 await enter(page,input,"20");await page.waitForTimeout(100);
 const committed=await Promise.all([input.evaluate(el=>getComputedStyle(el).color),unit.evaluate(el=>getComputedStyle(el).color)]);
 assert(committed[0]===committed[1],"committed number/unit colors diverge: "+JSON.stringify(committed));
 await card.locator(".kggPainVerticalToggle").waitFor({state:"visible"});
 const spacing=await card.evaluate(el=>{const c=el.getBoundingClientRect(),b=el.querySelector(".kggPainVerticalToggle").getBoundingClientRect(),p=el.querySelector(":scope > .pain").getBoundingClientRect();return{bottomGap:c.bottom-b.bottom,painTopGap:p.top-[...el.querySelectorAll(":scope > .set")].reduce((m,n)=>Math.max(m,n.getBoundingClientRect().bottom),0)}});
 assert(spacing.bottomGap<=20,"compact card keeps too much empty space below pain button: "+JSON.stringify(spacing));
 assert(spacing.painTopGap<=12,"compact card keeps too much empty space above pain button: "+JSON.stringify(spacing));
}
async function securityContract(page){
 await page.evaluate(()=>{p.ex[0].u="<b>unit-test</b>";render()});await page.waitForTimeout(180);
 const card=page.locator("#list .ex").first();await openCard(card);
 await card.locator("input.num").first().click();await page.waitForTimeout(80);
 assert(await page.locator("#kggPadPair b").count()===0,"unit text was interpreted as HTML");
 const label=await page.locator("#kggPadPair button > span:first-child").first().textContent();
 assert(label==="<b>unit-test</b>","unit markup was not rendered as literal text: "+label);
 await page.locator("#pad .padCancel").click();
}
async function normalCompactContract(page){
 const first=page.locator("#list .ex").nth(0);await openCard(first);const source=first.locator("input.num").first();await source.click();await page.waitForTimeout(120);
 assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi"))),"normal UI incorrectly classified large");
 const pair=page.locator("#kggPadPair button").first();const h=await pair.evaluate(el=>el.getBoundingClientRect().height);
 assert(h<80,"normal Compact pair unexpectedly large: "+h);
 await page.waitForTimeout(260);const focusColors=await Promise.all([source.evaluate(el=>getComputedStyle(el).borderTopColor),pair.evaluate(el=>getComputedStyle(el).borderTopColor)]);
 assert(focusColors[0]===focusColors[1],"active source field border does not match active pair border: "+JSON.stringify({source:focusColors[0],pair:focusColors[1]}));
 await page.locator("#pad .padCancel").click();
}
async function largeCompactContract(page){
 const first=page.locator("#list .ex").nth(0);await openCard(first);await first.locator("input.num").first().click();await page.waitForTimeout(160);
 assert(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi")),"Large UI class not active");
 assert(await page.locator(".kggPadZoomInput").count()===0,"Compact Large UI still shows redundant zoom box");
 const metrics=await page.locator("#kggPadPair button").first().evaluate(el=>({h:el.getBoundingClientRect().height,font:parseFloat(getComputedStyle(el.querySelector(".kggPairValue")).fontSize)}));
 assert(metrics.h>=84&&metrics.font>=36,"Large UI pair not promoted: "+JSON.stringify(metrics));
 await page.locator("#pad .padCancel").click();
 const sw=page.locator("#kggSetViewSwitch");await sw.click();
 await first.locator("input.num").first().click();await page.waitForTimeout(160);
 assert(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi")),"Legacy Large UI lost classification");
 assert(await page.locator(".kggPadZoomInput").count()===1,"Legacy Large UI lost zoom copy");
 await page.locator("#pad .padCancel").click();
}
async function largeSingleFieldContract(page){
 const single=page.locator("#list .ex").nth(1);await openCard(single);await single.locator("input.num").nth(1).click();await page.waitForTimeout(160);
 assert(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi")),"single-field fixture is not Large UI");
 assert(await page.locator("#kggPadPair").getAttribute("data-single")==="1","single-field Large UI did not collapse pair");
 const metric=await page.locator("#kggPadPair button").evaluate(el=>({h:el.getBoundingClientRect().height,w:el.getBoundingClientRect().width,parent:el.parentElement.getBoundingClientRect().width,label:el.querySelector("span")?.textContent||""}));
 assert(metric.h>=84&&metric.w>=metric.parent-2&&/Sek\.?/i.test(metric.label),"single-field Large UI geometry wrong: "+JSON.stringify(metric));
 assert(await page.locator(".kggPadZoomInput").count()===0,"single-field Compact Large UI created zoom box");
 await page.locator("#pad .padCancel").click();
}
async function adaptiveTransitionContract(page){
 const first=page.locator("#list .ex").nth(0);await openCard(first);await first.locator("input.num").first().click();await page.waitForTimeout(120);
 assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi"))),"transition fixture did not start normal");
 await page.evaluate(()=>{document.documentElement.style.fontSize="18px";if(window.visualViewport)visualViewport.dispatchEvent(new Event("resize"));window.dispatchEvent(new Event("orientationchange"))});await page.waitForTimeout(420);
 assert(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi")),"normal→Large transition failed");
 assert(await page.locator(".kggPadZoomInput").count()===0,"normal→Large Compact transition created zoom copy");
 const big=await page.locator("#kggPadPair button").first().evaluate(el=>el.getBoundingClientRect().height);assert(big>=84,"normal→Large pair did not grow");
 await page.evaluate(()=>{document.documentElement.style.fontSize="16px";if(window.visualViewport)visualViewport.dispatchEvent(new Event("resize"));window.dispatchEvent(new Event("orientationchange"))});await page.waitForTimeout(520);
 assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("kggPadLargeUi"))),"Large→normal transition stuck in Large UI");
 const normal=await page.locator("#kggPadPair button").first().evaluate(el=>el.getBoundingClientRect().height);assert(normal<80,"Large→normal pair stayed enlarged: "+normal);
 await page.locator("#pad .padCancel").click();
}
async function iosForceOnlyContract(browser,port){
 const ua="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
 const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:800,rootFont:16,userAgent:ua});
 try{
  const first=page.locator("#list .ex").nth(0);await openCard(first);await first.locator("input.num").first().click();await page.waitForTimeout(700);
  const cls=await page.locator("#pad").evaluate(el=>({module:!!window.__kggIosPadForce,ios:el.classList.contains("kggIosPadForce"),large:el.classList.contains("kggPadLargeUi")}));
  if(cls.module)assert(cls.ios,"loaded iOS force module did not activate in force-only scenario: "+JSON.stringify(cls));
  assert(!cls.large,"iOS force-only scenario incorrectly became kggPadLargeUi: "+JSON.stringify(cls));
  assert(errors.length===0,"iOS scenario page errors: "+errors.join(" | "));
 }finally{await ctx.close()}
}
async function iosLargeContract(browser,port){
 const ua="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
 const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:650,rootFont:16,userAgent:ua});
 try{
  const first=page.locator("#list .ex").nth(0);await openCard(first);await first.locator("input.num").first().click();await page.waitForTimeout(700);
  const cls=await page.locator("#pad").evaluate(el=>({module:!!window.__kggIosPadForce,ios:el.classList.contains("kggIosPadForce"),large:el.classList.contains("kggPadLargeUi")}));
  assert(cls.large,"iOS combined scenario did not activate Large UI: "+JSON.stringify(cls));
  if(cls.module)assert(cls.ios,"iOS combined scenario lost iOS force class: "+JSON.stringify(cls));
  assert(await page.locator(".kggPadZoomInput").count()===0,"iOS + Compact Large UI created redundant zoom box");
  const metric=await page.locator("#kggPadPair button").first().evaluate(el=>({h:el.getBoundingClientRect().height,font:parseFloat(getComputedStyle(el.querySelector(".kggPairValue")).fontSize)}));
  assert(metric.h>=84&&metric.font>=36,"iOS + Large pair not promoted: "+JSON.stringify(metric));
  assert(errors.length===0,"iOS Large page errors: "+errors.join(" | "));
 }finally{await ctx.close()}
}
async function main(){
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const port=server.address().port,browser=await chromium.launch({headless:true});
 try{
  for(const width of [320,360,390,430]){const {ctx,page,errors}=await loadPage(browser,port,{width,height:844,rootFont:16});try{await geometryContract(page,width);assert(errors.length===0,"page errors @"+width+": "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await compactFieldPresentationContract(page);await normalCompactContract(page);await securityContract(page);assert(errors.length===0,"normal page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await unitContract(page);assert(errors.length===0,"unit page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await lrSingleFieldContract(page);assert(errors.length===0,"LR single-field page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await noValuesContract(page);assert(errors.length===0,"no-values page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await bilateralSingleCapsuleContract(page);await barContract(page);assert(errors.length===0,"bar page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16,lang:"en"});try{await englishUnitContract(page);assert(errors.length===0,"English seconds page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16,lang:"en"});try{await englishBarContract(page);assert(errors.length===0,"English reps page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:320,height:844,rootFont:16});try{await longUnitContract(page);assert(errors.length===0,"custom-unit page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:18});try{await largeCompactContract(page);assert(errors.length===0,"large page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:18});try{await largeSingleFieldContract(page);assert(errors.length===0,"large single-field page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  {const {ctx,page,errors}=await loadPage(browser,port,{width:390,height:844,rootFont:16});try{await adaptiveTransitionContract(page);assert(errors.length===0,"transition page errors: "+errors.join(" | "))}finally{await ctx.close()}}
  await iosForceOnlyContract(browser,port);await iosLargeContract(browser,port);
  console.log(JSON.stringify({status:"PASS",geometry:[320,360,390,430],normal:true,large:true,transition:true,iosForceOnly:true,iosLarge:true,units:true,customUnits:true}));
 }finally{await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error("KGG adaptive set-view smoke FAIL: "+(e.stack||e.message));process.exitCode=1});