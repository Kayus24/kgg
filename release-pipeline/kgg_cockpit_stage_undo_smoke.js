"use strict";
const path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true}),failures=[];
 try {for(const preexisting of [false,true]){
  const context=await browser.newContext({viewport:{width:820,height:1180}}),page=await context.newPage();page.setDefaultTimeout(4000);
  try {
   await context.route(/^https?:/,route=>route.abort());
   await page.addInitScript(()=>localStorage.setItem('kgg_pwa_install_prompt_seen_v1','synthetic-undo'));
   await page.goto(pathToFileURL(path.resolve(__dirname,'../kgg-update/index.html')).href);
   await page.locator('#closeAdminSecrets').click();
   await page.evaluate(preexisting=>{
    const api=KGGTherapyCockpit,id=api.registry.entries()[0].id;
    api.importCode(api.encode({planId:'synthetic-stage-undo',name:'Synthetic',exercises:[{id,name:api.registry.lookup(id).name,sets:1,progressionGroupId:'synthetic-group',progressionVariants:[{id:'stage-a',name:'Stufe A',nameEn:'Stage A',order:0,media:[]},{id:'stage-b',name:'Stufe B',nameEn:'Stage B',order:1,media:[]}],activeProgressionId:'stage-a'}]}));
    if(preexisting){KGGSharedUndo.show('Synthetic prior action',()=>{});KGGSharedUndo.hide();}
   },preexisting);
   await page.locator('[data-tce-action="edit"][data-tce-slot="0"]').first().click();
   await page.locator('[data-cockpit-stage-remove="0"]').click();
   await page.locator('[data-cockpit-stage-name]').fill('Neue Stufe B');
   await page.locator('[data-cockpit-stage-name-en]').fill('New Stage B');
   await page.locator('#kggSharedUndoToast button').click();
   assert.equal(await page.locator('[data-cockpit-stage-name]').count(),2);
   assert.equal(await page.locator('[data-cockpit-stage-name]').nth(1).inputValue(),'Neue Stufe B','Undo discarded unsaved German stage name');
   assert.equal(await page.locator('[data-cockpit-stage-name-en]').nth(1).inputValue(),'New Stage B','Undo discarded unsaved English stage name');
   await page.locator('#saveExercise').click();await page.locator('[data-tce-action="edit"][data-tce-slot="0"]').first().click();
   assert.equal(await page.locator('[data-cockpit-stage-name-en]').nth(1).inputValue(),'New Stage B');
   const state=await page.evaluate(()=>KGGTherapyCockpit.getSlot(0).exercises[0]);
   assert.equal(state.activeProgressionId,'stage-a');assert.equal(state.progressionVariants[0].nameEn,'Stage A');
   console.log('PASS stage Undo, preexisting toast='+preexisting);
  } catch(error){failures.push({preexisting,message:error.message});console.error('FAIL stage Undo, preexisting toast='+preexisting+': '+error.message);}
  finally {await context.close();}
 }} finally {await browser.close();}
 if(failures.length)process.exitCode=1;
})().catch(error=>{console.error(error.stack);process.exitCode=1});
