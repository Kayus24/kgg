#!/usr/bin/env node
"use strict";
// Real Chromium UI import/finish of a synthetic V2 Cockpit link; no Android device.
const assert=require("node:assert/strict"),path=require("node:path");
const {pathToFileURL}=require("node:url"),{chromium}=require("playwright");
const root=path.resolve(__dirname,"..");
const url=pathToFileURL(path.join(root,"kgg-update","index.html")).href;
async function main(){
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1280,height:900},locale:"de-DE",serviceWorkers:"block"});
 await context.route(/^https?:\/\//,route=>route.fulfill({status:204,body:""}));
 const page=await context.newPage();page.setDefaultTimeout(10000);
 const errors=[];page.on("pageerror",e=>errors.push(e.message));
 try{
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>!!window.KGGTherapyCockpit&&!!window.KGGSharedBank);
  await page.waitForSelector("#adminSecretsModal.open",{state:"attached"});
  await page.locator("#closeAdminSecrets").evaluate(b=>b.click());
  const result=await page.evaluate(()=>{
    const bankId="custom_v2_ui_synthetic_20261112",name="Synthetische V2 Browserübung";
    const bank=window.KGGSharedBank;
    bank.merge({exercises:[{id:bankId,name,sets:2,loadUnit:"kg",metricUnit:"Wdh",weightUnit:"kg",unit:"Wdh",measure:"wdh",createdAt:"2026-11-12T10:00:00.000Z",updatedAt:"2026-11-12T10:00:00.000Z"}]});
    const exercise=bank.exportPayload().exercises.find(e=>e.id===bankId);
    if(!exercise)throw Error("synthetic bank fixture missing");
    const ref=window.KGGTherapyCockpit.registry.lookup(name);
    if(!ref)throw Error("synthetic cockpit id missing");
    const plan={planId:"synthetic-v2-ui-1",name:"Synthetic test name",date:"2026-11-12",notes:"Nur synthetische V2-Notiz",notesManual:true,editedAt:1794474000000,
      exercises:[{id:ref.id,bankId,name,sets:2,side:"BI",loadUnit:"kg",metricUnit:"Wdh",previous:[["20","12"],["21","10"]],today:[["22","11"],["23","9"]],manual:[[true,false],[false,true]],manualFields:["startLoad"],startLoad:"22"}]};
    return {code:window.KGGTherapyCockpit.encodeV2(plan),planId:plan.planId,notes:plan.notes};
  });
  assert.match(result.code,/^KGGTC1:z/);
  await page.evaluate(()=>window.KGGTherapyCockpit.open());
  await page.locator('#kggTherapyCockpitRoot [data-tc-action="import-open"]').first().click();
  await page.locator("#kggTherapyCockpitImportInput").fill(result.code);
  await page.locator('#kggTherapyCockpitRoot [data-tc-action="import-submit"]').click();
  await page.waitForFunction(()=>window.KGGTherapyCockpit.getState().slotCount===1);
  const imported=await page.evaluate(()=>window.KGGTherapyCockpit.getSlot(0));
  assert.equal(imported.planId,result.planId);
  assert.equal(imported.notes,result.notes);
  assert.equal(imported.exercises[0].today[0][0],"22");
  assert.equal(imported.exercises[0].bankId,"custom_v2_ui_synthetic_20261112");
  assert.equal(await page.locator("#kggTherapyCockpitRoot .kgg-tc-card").count(),1);
  await page.locator('#kggTherapyCockpitRoot [data-tc-action="finish"][data-tc-slot="0"]').click();
  await page.locator("#kggTherapyCockpitOutputModal").waitFor({state:"visible"});
  const output=await page.locator("#kggTherapyCockpitOutput").inputValue();
  const links=(output.match(/https?:\/\/[^\s]+/g)||[]).map(text=>{try{return new URL(text);}catch(_){return null;}}).filter(Boolean);
  const compact=links.find(url=>String(url.searchParams.get("cockpit")||"").startsWith("KGGTC1:z"));
  if(!compact)console.log("OUTPUT_TAIL="+output.slice(-650));
  assert(compact,"real finish output must include compact V2 link");
  assert.equal(await page.evaluate(()=>window.KGGTherapyCockpit.getState().slotCount),0);
  assert.equal(errors.length,0,errors.join("; "));
  console.log(JSON.stringify({status:"V2_UI_CHROMIUM_PASS",checks:["real admin boot","synthetic bank import","modal async V2 import","visible slot","preserved manual cells","finish produces compact V2","no page errors"],linkChars:compact.toString().length}));
 }finally{await context.close();await browser.close();}
}
main().catch(e=>{console.error(e.stack||e);process.exitCode=1;});
