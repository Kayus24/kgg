# KGG Patient Source Chunk 016

- Source file: `patient-live-sync-security-b.test.js`
- Characters: 1-6446
- Full source SHA-256: `b0cacebb8615e0cbb756fae58aeb9636e63fac46f42248cba2379f1082144b48`

```
'use strict';

const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function makeStorage(){
  const values=new Map();
  return {get length(){return values.size;},key(index){return Array.from(values.keys())[index]||null;},getItem(key){return values.has(String(key))?values.get(String(key)):null;},setItem(key,value){values.set(String(key),String(value));},removeItem(key){values.delete(String(key));},_values:values};
}
function makeElement(id){return {id,textContent:'',dataset:{},hidden:false,disabled:false,value:'',classList:{toggle(){}},setAttribute(){},insertAdjacentElement(){},addEventListener(){}};}
function exactValuesKey(plan){
  const exercises=(plan.e||[]).map(raw=>({n:raw[0]||'Übung',sets:Number(raw[1])||3,side:raw[2]||'LR',u:raw[3]||'kg',m:raw[4]||'Wdh'}));
  const raw=JSON.stringify({i:plan.i,t:plan.t,e:exercises.map(exercise=>[exercise.n,exercise.sets,exercise.side,exercise.u,exercise.m])});
  let hash=2166136261;for(let i=0;i<raw.length;i++){hash^=raw.charCodeAt(i);hash=Math.imul(hash,16777619);}
  return 'kgg-'+plan.i+'-'+(hash>>>0).toString(36)+'-values';
}

async function main(){
  const localStorage=makeStorage(),elements={};
  ['status','plan','kggLiveTestHint','kggLivePairScan','kggLiveJoin','kggLiveLeave','kggLiveSessionCode','kggLiveSyncPatientStatus'].forEach(id=>{elements[id]=makeElement(id);});
  const records=new Map();let client=null,replaceCount=0,runtimeMode='test';
  const store={
    async available(){return true;},
    async putSecret(payload){const parsed=payload.payload;records.set(parsed.pairingId,{id:parsed.pairingId,key:{type:'secret'},planRef:payload.planRef});return {pairingId:parsed.pairingId,keyVersion:1,createdAt:parsed.createdAt,storage:'memory'};},
    async get(id){const record=records.get(id);if(!record)throw Object.assign(new Error('missing'),{code:'PAIRING_NOT_FOUND'});return record;},
    async sign(){return new Uint8Array(32);},
    async remove(id){records.delete(id);},
    async removeByPlanRef(planRef){for(const [id,record] of records.entries())if(record.planRef===String(planRef))records.delete(id);},
    async clearAll(){records.clear();}
  };
  const live={
    config:()=>({mode:runtimeMode}),
    makeKeyStore:()=>store,
    isPairingQr:value=>String(value||'').startsWith('KGGLIVEPAIR1:'),
    importPairingQr:async(qr,target,metadata)=>target.putSecret({payload:{pairingId:'pair-a',createdAt:'2026-01-01T00:00:00.000Z'},planRef:metadata.planRef}),
    canonicalJson:value=>JSON.stringify(value),
    sha256Hex:async()=> 'b'.repeat(64),
    testFixtures:()=>({planSnapshot:{type:'plan_snapshot',synthetic:true,planRevision:'b'.repeat(64),title:'Synthetischer Plan',days:2,extendDays:false,stepDays:2,exercises:[]},trainingEvents:[{eventId:'event-stable-01',exerciseId:'exercise-stable-a',day:1,set:1,side:'B',metric:'reps',value:77,pain:4,recordedAt:'2026-01-01T00:00:00.000Z'}],planRevision:'b'.repeat(64)}),
    createClient:options=>{
      client={pairingId:options.pairingId,key:{},closed:false,options,sends:[],joined:[],close:async function(){this.closed=true;},failClosed:function(){this.closed=true;this.failedClosed=true;},status:()=>({mode:'test',status:'ready'})};
      client.join=async code=>{client.joined.push(code);await options.onReady();};
      client.sendTrainingEvents=async(events,revision)=>{client.sends.push({events,revision});};
      return client;
    }
  };
  const window={KGGLiveSync:live,KGGPatientPlanImport:{replaceConfirmed(){replaceCount+=1;}},KGG_LIVE_TEST_SIMULATOR:true,KGG_LIVE_TEST_SYNTHETIC_DATA:true,addEventListener(){}};
  const document={readyState:'complete',getElementById:id=>elements[id]||null,createElement:()=>({id:'',className:'',style:{},setAttribute(){},insertAdjacentElement(){}}),addEventListener(){},body:{appendChild(){}}};
  const context={window,document,localStorage,console,setTimeout:()=>0,clearTimeout(){},Date,JSON,Map,Set,Array,Number,String,Object,Math,Promise};
  vm.runInNewContext(fs.readFileSync('patient-live-sync.js','utf8'),context,{filename:'patient-live-sync.js'});
  const api=window.KGGPatientLiveSync;
  const planA={i:'plan-a',t:'Plan A',e:[['Übung A',3,'BI','kg','Wdh']]};
  const planB={i:'plan-b',t:'Plan B',e:[['Übung B',3,'BI','kg','Wdh']]};
  localStorage.setItem('kggCurrentPlanV1',JSON.stringify({plan:planA}));
  const oldPlan={...planA,e:[['Alte Übung',3,'BI','kg','Wdh']]};
  localStorage.setItem(exactValuesKey(oldPlan),JSON.stringify({'1|0|1|B|reps':'12'}));
  const currentKey=exactValuesKey(planA);localStorage.setItem(currentKey,JSON.stringify({'1|0|1|B|reps':'999','1|0|1|P|pain':'9'}));
  const pairingQr='KGGLIVEPAIR1:synthetic-secret-never-rendered';
  assert.equal(await api.handleScannedText(pairingQr),true);
  elements.kggLiveSessionCode.value='12345678';await elements.kggLiveJoin.onclick();
  assert.equal(client.joined.length,1);
  assert.equal(client.sends.length,1);
  assert.equal(client.sends[0].events[0].value,77);
  assert.equal(client.sends[0].events[0].pain,4);
  assert.equal(elements.kggLiveSyncPatientStatus.textContent.includes('synthetic-secret'),false);

  await elements.kggLiveLeave.onclick();
  assert.equal(client.closed,true);
  assert.equal((await store.get('pair-a')).planRef,'plan-a');

  runtimeMode='production';
  localStorage.removeItem(currentKey);
  await api.handleScannedText(pairingQr);elements.kggLiveSessionCode.value='12345678';await elements.kggLiveJoin.onclick();
  assert.equal(client.sends.length,0);

  localStorage.setItem(currentKey,JSON.stringify({'1|0|1|B|reps':'77'}));
  localStorage.setItem('kggCurrentPlanV1',JSON.stringify({plan:planB}));
  await client.options.onReady();
  assert.equal(client.failedClosed,true);
  assert.equal(client.sends.length,0);
  assert.equal(records.has('pair-a'),false);
  assert.equal(api.status().pairingId,false);
  await elements.kggLiveJoin.onclick();
  assert.equal(client.joined.length,1);
  assert.equal(replaceCount,0);

  await api.handleScannedText(pairingQr);
  assert.equal(records.has('pair-a'),true);
  await api.reset();
  assert.equal(records.has('pair-a'),false);
  assert.equal(api.status().pairingId,false);

  console.log(JSON.stringify({status:'PASS',checks:['pairing-plan-ref','plan-a-to-b-fail-closed','explicit-detach-deletes-key','app-reset-deletes-key','exact-values-key','missing-exact-store','normal-close-retention']}));
}

main().catch(error=>{console.error(error);process.exitCode=1;});
```
