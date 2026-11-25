#!/usr/bin/env node
"use strict";
/* Synthetic two-device identity probe; does not change production codec. */
const fs=require("fs"),path=require("path"),vm=require("vm"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(root,"kgg-update/src/patches/v082-therapy-cockpit.html"),"utf8");
const match=source.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i);
assert(match,"v082 runtime script");
const fflate=require(path.join(root,"vendor/fflate-0.8.3.js"));
const bankItem=(id,name)=>({id,name,sets:3,loadUnit:"kg",metricUnit:"Wdh"});
function device(exercises){
 const w={location:{href:"https://example.test/"},fflate,KGG_PATCHES:{},
   KGGSharedBank:{exportPayload:()=>({exercises}),merge:x=>x},
   addEventListener(){},dispatchEvent(){}};
 const d={readyState:"loading",body:null,title:"SYNTHETIC",addEventListener(){},getElementById(){return null}};
 const ctx={window:w,document:d,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,Array,Object,Number,String,Math,Date,JSON,Error,RegExp,unescape,encodeURIComponent,decodeURIComponent,
  btoa:v=>Buffer.from(v,"binary").toString("base64"),atob:v=>Buffer.from(v,"base64").toString("binary"),navigator:{},setTimeout,clearTimeout,console};
 vm.createContext(ctx);vm.runInContext(match[1],ctx);
 return {api:w.KGGTherapyCockpit,bank:exercises};
}
function validBankRef(ref,bank){
 const id=String(ref.bankId||"");
 if(!id)throw Error("missing_bank_id");
 const row=bank.find(x=>x.id===id);
 if(!row)throw Error("bank_id_not_found");
 // A fingerprint of name is a fail-closed guard, NOT a replacement for a persistent bankId.
 if(row.name!==ref.name)throw Error("bank_identity_mismatch");
 return row;
}
const sameA=device([bankItem("custom_1762940000000_abcd","Synthetischer Ausfallschritt")]);
const sameB=device([bankItem("custom_1762940000000_abcd","Synthetischer Ausfallschritt")]);
assert.equal(validBankRef({bankId:sameA.bank[0].id,name:sameA.bank[0].name},sameB.bank).id,sameA.bank[0].id);
const renamed=device([bankItem("custom_1762940000000_abcd","Ausfallschritt modifiziert")]);
assert.throws(()=>validBankRef({bankId:sameA.bank[0].id,name:sameA.bank[0].name},renamed.bank),/bank_identity_mismatch/);
const collision=device([bankItem("custom_1762940000000_abcd","Andere Übung")]);
assert.throws(()=>validBankRef({bankId:sameA.bank[0].id,name:sameA.bank[0].name},collision.bank),/bank_identity_mismatch/);
assert.throws(()=>validBankRef({bankId:sameA.bank[0].id,name:sameA.bank[0].name},[]),/bank_id_not_found/);
assert.throws(()=>validBankRef({name:sameA.bank[0].name},sameB.bank),/missing_bank_id/);
const legacyCollisionA=device([bankItem("custom_A","Synthetische Kollisionsuebung Nummer 18")]);
const legacyCollisionB=device([bankItem("custom_B","Synthetische Kollisionsuebung Nummer 100")]);
const refA=legacyCollisionA.api.registry.lookup("Synthetische Kollisionsuebung Nummer 18");
const refB=legacyCollisionB.api.registry.lookup("Synthetische Kollisionsuebung Nummer 100");
assert.equal(refA.id,refB.id);
const oldLink=legacyCollisionA.api.encode({planId:"synthetic-plan",name:"Fiktive Person",exercises:[{id:refA.id,name:refA.name,sets:1,previous:[["10","12"]],today:[["11","11"]]}]});
const decoded=legacyCollisionB.api.decode(oldLink);
assert.equal(decoded.exercises[0].id,refB.id);
assert.notEqual(decoded.exercises[0].name,refB.name);
assert.throws(()=>validBankRef({bankId:"custom_A",name:refA.name},legacyCollisionB.bank),/bank_id_not_found/);
console.log(JSON.stringify({status:"PASS",legacyRisk:"KGGTC1_ACCEPTS_SAME_SHORT_ID_WITH_DIFFERENT_REMOTE_BANK_ID",validated:"SAME_BANK_ID_AND_NAME_REQUIRED",scenarios:6},null,2));
