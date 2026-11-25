"use strict";
/* Node-only contract prototype, not shipped to KGG. Tests a bank-referenced data format. */
const assert=require("node:assert/strict");
const zlib=require("zlib");
const PREFIX="KGGTC1:z";
function identity(value){return String(value??"").normalize("NFKC").trim().toLocaleLowerCase("de-DE");}
function fnv(text){let hash=2166136261;for(const ch of Buffer.from(text,"utf8")){hash^=ch;hash=Math.imul(hash,16777619)>>>0;}return (hash>>>0).toString(36);}
function signature(bank){return fnv(String(bank.id)+"\0"+identity(bank.name));}
function indexBank(exercises){
  const ids=new Map(),names=new Map();
  for(const item of exercises){
    const id=String(item?.id||"").trim(),name=String(item?.name||"").trim();
    if(!id||!name||id.length>80)throw Error("invalid_bank_entry");
    if(ids.has(id))throw Error("duplicate_bank_id");
    ids.set(id,item);
    const key=identity(name);names.set(key,(names.get(key)||[]).concat(item));
  }
  return {ids,names};
}
function resolveForEncode(ex,index){
  const id=String(ex.bankId||ex.sourceId||"");
  let row=id?index.ids.get(id):null;
  if(id&&!row)throw Error("bank_id_not_found");
  if(!row){
    const matches=index.names.get(identity(ex.name))||[];
    if(matches.length!==1)throw Error("bank_ref_missing_or_ambiguous");
    row=matches[0];
  }
  if(identity(row.name)!==identity(ex.name))throw Error("bank_identity_mismatch");
  if(String(row.cockpitId||"")!==String(ex.id||""))throw Error("cockpit_id_mismatch");
  return row;
}
function manualBits(manual,sets){
  let bits=0;
  for(let i=0;i<sets;i++)for(let j=0;j<2;j++)if(manual?.[i]?.[j])bits|=(1<<(i*2+j));
  return bits;
}
function unfoldBits(bits,sets){return Array.from({length:sets},(_,i)=>[!!(bits&(1<<(i*2))),!!(bits&(1<<(i*2+1)))]);}
const bankFields=["name","nameDe","nameEn","loadUnit","metricUnit","unit","weightUnit","measure","startLoad","startMetric","videoUrl","videoLabel","media","progressionGroupId","progressionVariants","activeProgressionId"];
function changes(ex,bank){
  const diff={};
  for(const field of bankFields)if(ex[field]!==undefined&&JSON.stringify(ex[field])!==JSON.stringify(bank[field]))diff[field]=ex[field];
  return diff;
}
function encode(plan,bankItems){
  const bank=indexBank(bankItems),items=plan.exercises;
  if(!Array.isArray(items)||items.length<1||items.length>40)throw Error("exercise_count_invalid");
  const ids=new Set();
  const e=items.map(ex=>{
    const b=resolveForEncode(ex,bank),sid=String(b.id);
    if(ids.has(sid))throw Error("duplicate_exercise");ids.add(sid);
    const sets=Number(ex.sets||0);
    if(!Number.isInteger(sets)||sets<1||sets>8)throw Error("sets_invalid");
    for(const list of [ex.previous,ex.today])if(!Array.isArray(list)||list.length!==sets||list.some(x=>!Array.isArray(x)||x.length!==2))throw Error("values_invalid");
    return [sid,signature(b),String(ex.id),sets,ex.side==="LR"?1:0,ex.previous,ex.today,manualBits(ex.manual,sets),ex.manualFields||[],changes(ex,b)];
  });
  const body={v:2,p:String(plan.planId||""),d:String(plan.date||""),c:[String(plan.notes||""),!!plan.notesManual,Number(plan.editedAt||0),plan.removedIds||[]],e};
  const serialized=JSON.stringify(body),h=fnv(serialized);
  return PREFIX+zlib.deflateRawSync(Buffer.from(JSON.stringify({b:body,h}),"utf8"),{level:6}).toString("base64url");
}
function decode(code,bankItems){
  if(!String(code).startsWith(PREFIX)||code.length>30000)throw Error("invalid_format");
  const bytes=Buffer.from(code.slice(PREFIX.length),"base64url");
  const content=zlib.inflateRawSync(bytes,{maxOutputLength:100000});
  const {b,h}=JSON.parse(content.toString("utf8"));
  if(!b||b.v!==2||fnv(JSON.stringify(b))!==h)throw Error("integrity_failed");
  const index=indexBank(bankItems),ids=new Set();
  if(!Array.isArray(b.e)||b.e.length<1||b.e.length>40)throw Error("exercise_count_invalid");
  const exercises=b.e.map(row=>{
    if(!Array.isArray(row)||row.length!==10)throw Error("invalid_row");
    const [id,sig,shortId,sets,side,previous,today,bits,manualFields,overrides]=row;
    const bank=index.ids.get(id);
    if(!bank)throw Error("bank_id_not_found");
    if(signature(bank)!==sig)throw Error("bank_identity_mismatch");
    if(bank.cockpitId!==shortId)throw Error("cockpit_id_mismatch");
    if(ids.has(id))throw Error("duplicate_exercise");ids.add(id);
    if(!Number.isInteger(sets)||sets<1||sets>8||![0,1].includes(side))throw Error("set_structure_invalid");
    if(!Array.isArray(previous)||!Array.isArray(today)||previous.length!==sets||today.length!==sets)throw Error("values_invalid");
    for(const values of [previous,today])for(const pair of values)if(!Array.isArray(pair)||pair.length!==2)throw Error("values_invalid");
    const ex={...bank,id:shortId,bankId:id,sets,side:side?"LR":"BI",previous,today,manual:unfoldBits(bits,sets),manualFields};
    for(const field of Object.keys(overrides||{})){if(!bankFields.includes(field))throw Error("unknown_override");ex[field]=overrides[field];}
    return ex;
  });
  return {planId:b.p,date:b.d,notes:b.c?.[0]||"",notesManual:!!b.c?.[1],editedAt:Number(b.c?.[2]||0),removedIds:b.c?.[3]||[],exercises,name:"Plan ohne Patientendaten"};
}
module.exports={encode,decode,signature,identity,indexBank};

// Import controller contract: at most one *configured* existing bank-sync refresh.
// The callback MUST NOT receive plan IDs, names, training values or the portable link.
async function decodeWithBankRefresh(code,readBank,refreshBank){
  if(typeof readBank!=="function")throw Error("bank_provider_missing");
  let initial;
  try{return decode(code,await readBank());}
  catch(error){
    if(!["bank_id_not_found","bank_identity_mismatch","cockpit_id_mismatch"].includes(error.message))throw error;
    initial=error;
  }
  if(typeof refreshBank!=="function")throw initial;
  const refreshed=await refreshBank("cockpit_missing_exercise");
  if(refreshed===false)throw Error("bank_refresh_unavailable");
  // Re-read the actual local merged library; never trust a guessed search match.
  return decode(code,await readBank());
}
module.exports.decodeWithBankRefresh=decodeWithBankRefresh;
