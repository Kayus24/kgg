"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const assert=(v,m)=>{if(!v)throw new Error(m)};
const enc=plan=>Buffer.from(JSON.stringify(plan),"utf8").toString("base64url");
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".svg")?"image/svg+xml":f.endsWith(".webp")?"image/webp":"application/octet-stream"}
async function metric(page,width){
 await page.setViewportSize({width,height:844});await page.waitForTimeout(120);
 return page.locator("#list .ex").first().evaluate(el=>{
  const h=el.querySelector("h3"),t=el.querySelector(".kggCardThumb"),img=t&&t.querySelector("img"),r=el.getBoundingClientRect(),hr=h.getBoundingClientRect(),tr=t.getBoundingClientRect(),cs=getComputedStyle(el),ts=getComputedStyle(t),is=getComputedStyle(img);
  return{card:{left:r.left,right:r.right,width:r.width},title:{left:hr.left,right:hr.right,width:hr.width},thumb:{left:tr.left,right:tr.right,width:tr.width,height:tr.height},display:cs.display,columns:cs.gridTemplateColumns,position:ts.position,objectFit:is.objectFit,padRight:cs.paddingRight,gap:cs.columnGap};
 });
}
(async()=>{
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));
 const browser=await chromium.launch({headless:true}),ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage();
 try{
  await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1"});
  const plan={i:"thumb-layout",t:"Thumb layout",v:1,d:2,e:[["Beinpresse",3,"B","kg","Wdh","40","10"]]};
  await page.goto("http://127.0.0.1:"+server.address().port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"domcontentloaded"});
  await page.waitForFunction(()=>document.querySelector("#list .ex.kggThumbReady .kggCardThumb img")?.naturalWidth>0,{timeout:30000});
  await page.locator("#list .ex h3").evaluate(el=>el.textContent="Beinpresse mit sehr langem Übungsnamen");
  const widths=[320,390,430,720],rows=[];
  for(const width of widths){
    const m=await metric(page,width);rows.push(m);
    assert(m.display==="grid","closed thumbnail card must use a real grid @"+width+": "+JSON.stringify(m));
    assert(m.position!=="absolute","thumbnail is still absolute @"+width+": "+JSON.stringify(m));
    assert(m.title.right<=m.thumb.left-6,"title area overlaps/reserves too little gap before image @"+width+": "+JSON.stringify(m));
    assert(m.thumb.right<=m.card.right-8&&m.thumb.left>=m.card.left+8,"thumbnail escaped card padding @"+width+": "+JSON.stringify(m));
    assert(m.thumb.width>=90&&m.thumb.width<=170,"thumbnail width outside adaptive bounds @"+width+": "+JSON.stringify(m));
    assert(m.objectFit==="contain","thumbnail must preserve the whole exercise illustration @"+width+": "+JSON.stringify(m));
  }
  assert(rows[1].thumb.width>rows[0].thumb.width,"thumbnail did not grow from narrow to normal phone: "+JSON.stringify(rows.map(x=>x.thumb.width)));
  assert(rows[2].thumb.width>=rows[1].thumb.width,"thumbnail shrank on wider phone: "+JSON.stringify(rows.map(x=>x.thumb.width)));
  await page.evaluate(()=>document.documentElement.style.fontSize="19px");await page.waitForTimeout(120);
  const scaled=await metric(page,390);
  assert(scaled.title.right<=scaled.thumb.left-6,"large browser/UI text scaling caused title/image overlap: "+JSON.stringify(scaled));
  console.log("Patient adaptive thumbnail layout Playwright: PASS "+JSON.stringify({widths:rows.map(x=>x.thumb.width),scaled:scaled.thumb.width}));
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error("Patient adaptive thumbnail layout Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
