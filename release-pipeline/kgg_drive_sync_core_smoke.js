#!/usr/bin/env node
// CLI only: real library persistence and serializers; fake only OS storage, clock and native transport.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const cp=require('node:child_process');
const {webcrypto,createHash}=require('node:crypto');
const zlib=require('node:zlib');
const {crc32}=require('./kgg_drive_sync_e2e');
const ROOT=path.resolve(__dirname,'..');
const smoke=fs.readFileSync(path.join(__dirname,'kgg_html_logic_smoke.js'),'utf8').replace(/^#!.*\r?\n/,'');
const helpers=new Function('require','__dirname',smoke.slice(0,smoke.lastIndexOf('\ntry {'))+'\nreturn {createContext,readMainAppScript};')(require,__dirname);
const clone=x=>JSON.parse(JSON.stringify(x));
const settle=async()=>{for(let i=0;i<12;i++)await new Promise(setImmediate);};
function client(id,files=new Map(),stored=null,blobStore=new Map(),mainScript=null){
  const ctx=helpers.createContext(),timers=new Map(),listeners=new Map();let time=0,seq=0;
  const warnings=[];ctx.console={...console,warn(message){warnings.push(typeof message==='string'?message:'warning');}};
  if(stored)ctx.localStorage=ctx.window.localStorage=stored;
  const storage=ctx.localStorage;
  storage.setItem('kgg_sync_pair_device_id_v1',id);
  storage.setItem('kgg_sync_pair_follow_config_v1',JSON.stringify({therapistId:id,syncRoomId:'audit_room',followedTherapists:['a','b','c'].filter(x=>x!==id).map(deviceId=>({deviceId,therapistId:deviceId,roomId:'audit_room',autoDownload:true}))}));
  const transport={readFailure:false,writeFailure:false,blobFailure:false,writes:0,reads:0,inflight:0,maxInflight:0};
  ctx.window.KGGNativeSync={available:true,platform:'test',status:()=>({transport:'saf-document',driveConfigured:true,pending:transport.writeFailure,providerAccepted:!transport.writeFailure}),async read(){transport.reads++;if(transport.readFailure)throw Error('synthetic read failure');return {kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[...files.values()].map(clone)};},async write(doc){transport.inflight++;transport.maxInflight=Math.max(transport.maxInflight,transport.inflight);await Promise.resolve();transport.inflight--;if(transport.writeFailure)return false;transport.writes++;files.set(id,clone(doc));return true;}};
  const on=(type,fn)=>{const list=listeners.get(type)||[];list.push(fn);listeners.set(type,list);};
  ctx.window.addEventListener=on;ctx.document.addEventListener=on;ctx.document.visibilityState='visible';ctx.document.hidden=false;
  ctx.setTimeout=(fn,delay=0)=>{const n=++seq;timers.set(n,{fn,at:time+delay});return n;};ctx.clearTimeout=n=>timers.delete(n);
  ctx.Blob=Blob;ctx.crypto=ctx.window.crypto=webcrypto;
  // IDB boundary double keeps the real production put/get transaction path.
  const db={objectStoreNames:{contains:()=>true},createObjectStore(){},transaction(){const tx={};tx.objectStore=()=>({get(key){const req={};queueMicrotask(()=>{req.result=blobStore.get(key)||null;if(req.onsuccess)req.onsuccess();});return req;},put(value){if(transport.blobFailure){tx.error=Error('synthetic IDB write failure');queueMicrotask(()=>tx.onerror&&tx.onerror());return;}blobStore.set(value.id,value);queueMicrotask(()=>tx.oncomplete&&tx.oncomplete());},delete(key){blobStore.delete(key);queueMicrotask(()=>tx.oncomplete&&tx.oncomplete());}});return tx;}};
  ctx.indexedDB=ctx.window.indexedDB={open(){const req={};queueMicrotask(()=>{req.result=db;req.onsuccess&&req.onsuccess();});return req;}};
  vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(ROOT,'patient-qr-format.js'),'utf8'),ctx);
  vm.runInContext((mainScript||helpers.readMainAppScript())+`
    render=function(){};
    load();
    window.__core={get bank(){return bank;},get state(){return state;},get running(){return typeof nativeExerciseSyncRunning==='undefined'?null:nativeExerciseSyncRunning;},get dirty(){return nativeExerciseSyncDirty;},get syncPairCode(){return lastSyncPairCode;},save,persistCustomBank,deleteBankExercise,confirmExerciseInput,upsertLiveExerciseFromText,applySelectedExerciseToText,openEditor,saveEditedExercise,openSyncPairModal,closeSyncPairModal,buildNativeSyncQrPayload,configureNativeDriveSync:typeof configureNativeDriveSync==='function'?configureNativeDriveSync:null,applyNativeSyncInvite:typeof applyNativeSyncInvite==='function'?applyNativeSyncInvite:null,initNativeExerciseBankSync,buildNativeExerciseBankSyncDocument,mergeNativeExerciseBankSyncDocument,mergeSharedExerciseBank,putEncryptedMediaBlob,getEncryptedMediaBlob,encryptMediaBlob,patientDecryptMedia};
  })();`,ctx);
  return {ctx,core:ctx.window.__core,transport,files,storage,blobStore,warnings,eval(code){return vm.runInContext(code,ctx);},async tick(ms=400){const target=time+ms;for(let guard=0;guard<100;guard++){await settle();if(ctx.window.__core.running)await ctx.window.__core.running;let found=null;for(const [key,timer]of timers)if(timer.at<=target&&(!found||timer.at<found[1].at))found=[key,timer];if(!found)break;timers.delete(found[0]);time=found[1].at;found[1].fn();}time=target;await settle();if(ctx.window.__core.running)await ctx.window.__core.running;},async event(type){for(const fn of listeners.get(type)||[])fn({type});await settle();},create(name){ctx.document.getElementById('exerciseInput').value=name;this.core.confirmExerciseInput();},edit(ex,name){this.core.openEditor(ex);ctx.document.getElementById('editName').value=name;this.core.saveEditedExercise();}};
}
// Deterministic, valid PNG pixels keep the image fixture substantial without
// downloads or a browser. CRC uses the existing integration-test helper.
function richPng(seed){
  const side=256,pixels=Buffer.alloc(side*(1+side*3));let value=seed;
  for(let y=0;y<side;y++)for(let x=0;x<side*3;x++){
    value=(Math.imul(value,1664525)+1013904223)>>>0;
    pixels[y*(1+side*3)+1+x]=value>>>24;
  }
  function chunk(type,data){const tag=Buffer.from(type),length=Buffer.alloc(4),crc=Buffer.alloc(4);length.writeUInt32BE(data.length);crc.writeUInt32BE(crc32(Buffer.concat([tag,data])));return Buffer.concat([length,tag,data,crc]);}
  const header=Buffer.alloc(13);header.writeUInt32BE(side);header.writeUInt32BE(side,4);header[8]=8;header[9]=2;
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(pixels)),chunk('IEND',Buffer.alloc(0))]);
}
async function storeRichPicture(a,id,seed){
  const bytes=richPng(seed),encrypted=await a.core.encryptMediaBlob(new Blob([bytes],{type:'image/png'}));
  const media={id,type:'image',mime:'image/png',width:256,height:256,storage:'indexeddb-local',crypto:{alg:'AES-GCM',key:encrypted.key,iv:encrypted.iv}};
  await a.core.putEncryptedMediaBlob({id,blob:encrypted.blob,manifest:media});
  return {media,sha256:createHash('sha256').update(bytes).digest('hex')};
}
async function richLibraryClient(){
  const blobs=new class extends Map{constructor(){super();this.reads=0;}get(key){this.reads++;return super.get(key);}}();
  const a=client('a',new Map(),null,blobs),expectedImages=new Map();
  for(let i=0;i<300;i++){
    const ex={id:'rich_library_'+i,name:'Audit rich library '+i,custom:true,sets:3,unit:'Wdh',weightUnit:'kg',media:[]};
    if(i<8){const picture=await storeRichPicture(a,'rich_image_'+i,i+1);ex.media=[picture.media];expectedImages.set(picture.media.id,picture.sha256);}
    a.core.bank.push(ex);
  }
  assert.equal(a.core.persistCustomBank(),true);
  a.core.initNativeExerciseBankSync();await a.tick();
  const published=a.files.get('a');assert.equal(published.exerciseBank.filter(ex=>ex.id.startsWith('rich_library_')).length,300);
  assert.equal(published.mediaBlobs.length,8);assert(Buffer.byteLength(JSON.stringify(published))>2000000,'fixture must exercise substantial encrypted image transport');
  for(const image of published.mediaBlobs)assert.equal(image.sha256,expectedImages.get(image.id));
  assert.equal(a.core.dirty,false);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
  return {a,expectedImages};
}
// Exercise the actual embedded production QR generator, not the older npm test
// dependency. Only the existing DOM boundary remains fake in this CLI suite;
// real browser image decoding/scanning is a separate integration gate.
function syncQrClient(kind='invite'){
  const a=client('a'),instant=Date.parse('2026-10-23T12:00:00Z');
  a.ctx.Date=class extends Date{constructor(...args){super(...(args.length?args:[instant]));}static now(){return instant;}};
  const source=fs.readFileSync(path.join(ROOT,'kgg-update/src/runtime/qrcode-generator.html'),'utf8');
  assert.match(source,/qrcode-generator 1\.5\.2 \| MIT License/,'test must use the actual embedded production generator');
  const scripts=[...source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)];assert.equal(scripts.length,1);
  vm.runInContext(scripts[0][1],a.ctx,{filename:'kgg-update/src/runtime/qrcode-generator.html#production-1.5.2'});
  const factory=a.eval('qrcode');assert.equal(typeof factory,'function');
  const exercise={id:'sync_qr_names',name:'Audit Rückenübung',nameDe:'Audit Rückenübung',nameEn:'Audit back exercise',sets:3,unit:'Wdh',weightUnit:'kg',media:kind==='invite'?[{id:'sync_qr_image',type:'image',mime:'image/png',width:1,height:1}]:[]};
  a.core.bank.splice(0,a.core.bank.length,exercise);
  const expected=a.core.buildNativeSyncQrPayload();assert.equal(expected.type,kind);assert.match(expected.code,kind==='invite'?/^KGGSYNC1:/:/^KGGSYNC2:/);
  const calls={factory:[],payloads:[],make:0,svg:0,gif:0,svgArgs:[],gifArgs:[]};
  a.ctx.window.qrcode=(...args)=>{
    calls.factory.push(args);const qr=factory(...args),add=qr.addData,make=qr.make,svg=qr.createSvgTag,gif=qr.createDataURL;
    qr.addData=(value,...rest)=>{calls.payloads.push(value);return add.call(qr,value,...rest);};
    qr.make=(...args)=>{calls.make++;return make.apply(qr,args);};
    qr.createSvgTag=(...args)=>{calls.svg++;calls.svgArgs.push(args);return svg.apply(qr,args);};
    qr.createDataURL=(...args)=>{calls.gif++;calls.gifArgs.push(args);return gif.apply(qr,args);};
    return qr;
  };
  return {a,factory,expected,calls,exercise};
}
function renderedSyncImage(a){
  assert(a.ctx.document.getElementById('syncPairModal').classList.contains('open'));
  const image=a.ctx.document.getElementById('syncPairQrBox').children.at(-1);
  assert(image&&image.id==='img','real Sync renderer did not append the existing image element');
  assert.equal(image.alt,'Sync-QR fuer Uebungsdatenbank');return image;
}
async function main(){
  const results=[];let failures=0;
  async function test(name,fn){try{await fn();results.push({name,ok:true});}catch(err){failures++;results.push({name,ok:false,error:err.message});}}
  for(const kind of ['invite','bundle'])await test('Sync QR '+kind+' prefers embedded SVG without GIF work and preserves the exact existing payload',()=>{
    const {a,factory,expected,calls,exercise}=syncQrClient(kind),names=clone({name:exercise.name,nameDe:exercise.nameDe,nameEn:exercise.nameEn});
    a.core.openSyncPairModal();const image=renderedSyncImage(a);
    assert.equal(a.core.syncPairCode,expected.code,'rendering changed the existing Sync code');
    assert.deepEqual(calls.payloads,[expected.code],'QR generator received a different payload');
    assert.deepEqual(calls.factory,[[0,'L']]);assert.equal(calls.make,1);
    assert.deepEqual({svg:calls.svg,gif:calls.gif},{svg:1,gif:0},'Sync QR must use the available SVG renderer without pixelwise GIF work');
    assert.deepEqual(calls.svgArgs,[[10,4]],'cell size or quiet margin changed');
    assert.match(image.src,/^data:image\/svg\+xml[^,]*,/);
    const actualSvg=decodeURIComponent(image.src.slice(image.src.indexOf(',')+1)),reference=factory(0,'L');reference.addData(expected.code);reference.make();
    assert.equal(actualSvg,reference.createSvgTag(10,4),'image does not contain the unchanged production QR matrix/geometry');
    assert.deepEqual(clone({name:exercise.name,nameDe:exercise.nameDe,nameEn:exercise.nameEn}),names);
  });
  await test('Sync QR retains the actual GIF renderer when an older QR object has no SVG method',()=>{
    const {a,factory,expected,calls}=syncQrClient(),wrapped=a.ctx.window.qrcode;
    a.ctx.window.qrcode=(...args)=>{const qr=wrapped(...args);delete qr.createSvgTag;return qr;};
    a.core.openSyncPairModal();const image=renderedSyncImage(a);
    assert.equal(a.core.syncPairCode,expected.code);assert.deepEqual(calls.payloads,[expected.code]);
    assert.deepEqual({svg:calls.svg,gif:calls.gif},{svg:0,gif:1});assert.deepEqual(calls.gifArgs,[[10,4]]);
    const reference=factory(0,'L');reference.addData(expected.code);reference.make();assert.equal(image.src,reference.createDataURL(10,4));
  });
  await test('Sync QR preserves KGGQrCore priority and its unchanged payload/options without the fallback factory',()=>{
    const {a,factory,expected,calls}=syncQrClient(),coreCalls=[];
    a.ctx.window.KGGQrCore={renderQrToImg(value,options){coreCalls.push({value,options:clone(options)});const qr=factory(0,'L');qr.addData(value);qr.make();return qr.createDataURL(options.cellSize,options.margin);}};
    a.ctx.window.qrcode=()=>{throw Error('preferred KGGQrCore must not enter fallback factory');};
    a.core.openSyncPairModal();const image=renderedSyncImage(a);
    assert.equal(a.core.syncPairCode,expected.code);assert.deepEqual(coreCalls,[{value:expected.code,options:{cellSize:10,margin:4}}]);
    assert.equal(calls.factory.length,0);assert.match(image.src,/^data:image\/gif;base64,/);
  });
  await test('loaded input listeners commit Enter and delimiters while blur only finalizes the plan',async()=>{
    for(const delimiter of ['\n',',',';']){
      const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const input=a.ctx.document.getElementById('exerciseInput'),name='Audit event '+(delimiter==='\n'?'newline':delimiter===','?'comma':'semicolon');
      input.value=name;input.selectionStart=input.value.length;input.dispatchEvent({type:'input'});await a.tick();assert(!a.core.bank.some(ex=>ex.name===name));
      if(delimiter==='\n'){input.dispatchEvent({type:'keydown',key:'Enter',isComposing:false,preventDefault(){throw Error('Enter default must remain available');}});assert(a.core.bank.some(ex=>ex.name===name),'real Enter keydown listener missing');}
      input.value+=delimiter;input.selectionStart=input.value.length;input.dispatchEvent({type:'input',inputType:delimiter==='\n'?'insertLineBreak':'insertText',data:delimiter});await a.tick();assert(a.core.bank.some(ex=>ex.name===name),'loaded listener did not persist '+JSON.stringify(delimiter));assert(a.files.get('a').exerciseBank.some(ex=>ex.name===name));
      input.value+='Audit partial';input.selectionStart=input.value.length;input.dispatchEvent({type:'input',inputType:'insertText',data:'Audit partial'});await a.tick();assert(!a.core.bank.some(ex=>ex.name==='Audit partial'),'partial second segment entered library');
      input.dispatchEvent({type:'change'});await a.tick();assert(!a.core.bank.some(ex=>ex.name==='Audit partial'),'blur published an unconfirmed segment');assert(a.core.state.plan.some(ex=>ex.name==='Audit partial'),'existing change plan finalization was lost');
    }
  });
  await test('search fragment blur followed by an existing-bank selection never publishes the fragment',async()=>{
    const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const input=a.ctx.document.getElementById('exerciseInput'),before=a.core.bank.length;input.value='Bein';input.selectionStart=4;input.dispatchEvent({type:'input',inputType:'insertText',data:'Bein'});input.dispatchEvent({type:'change'});a.core.applySelectedExerciseToText(a.core.bank.find(ex=>ex.name==='Beinpresse'),{mode:'replaceActive'});await a.tick();assert.equal(a.core.bank.length,before);assert(!a.core.bank.some(ex=>ex.name==='Bein'));assert(!a.files.get('a').exerciseBank.some(ex=>ex.name==='Bein'));assert(a.core.state.plan.some(ex=>ex.name==='Beinpresse'));
  });
  await test('confirmed creation persists and writes, partial typing does neither',async()=>{const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const before=a.transport.writes;a.ctx.document.getElementById('exerciseInput').value='Audit incomplete';a.core.upsertLiveExerciseFromText();await a.tick();assert(!a.core.bank.some(x=>x.name==='Audit incomplete'));assert.equal(a.transport.writes,before);a.create('Audit created');await a.tick();assert(a.core.bank.some(x=>x.name==='Audit created'),'confirmed creation missing in bank');assert(a.files.get('a').exerciseBank.some(x=>x.name==='Audit created'));const reload=client('a',a.files,a.storage);assert(reload.core.bank.some(x=>x.name==='Audit created'));});
  await test('ID rename and built-in changes persist across reload',async()=>{const a=client('a');const ex=a.core.bank[0],id=ex.id;a.core.mergeNativeExerciseBankSyncDocument({kind:'kgg_cross_data_safe_sync',version:2,roomId:'audit_room',origin:{deviceId:'b',roomId:'audit_room'},exerciseBank:[{id,name:'Audit renamed built-in',sets:4,updatedAt:'2099-01-01T00:00:00Z'}],packages:[],tombstones:{exerciseBank:[]} });assert.equal(a.core.bank.filter(x=>x.id===id).length,1);const reload=client('a',a.files,a.storage);assert.equal(reload.core.bank.find(x=>x.id===id).name,'Audit renamed built-in');});
  await test('distinct exercise IDs with equal names survive reload',async()=>{const a=client('a'),doc=clone(a.core.buildNativeExerciseBankSyncDocument());doc.origin.deviceId='b';doc.exerciseBank=[{id:'same_name_a',name:'Audit equal name'},{id:'same_name_b',name:'Audit equal name'}];await a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc);const reload=client('a',a.files,a.storage);assert.equal(reload.core.bank.filter(x=>x.name==='Audit equal name').length,2);});
  await test('local tombstones survive stale import and reload',async()=>{const a=client('a');const ex=a.core.bank[0];a.core.deleteBankExercise(ex.id);const old={kind:'kgg_cross_data_safe_sync',version:2,roomId:'audit_room',origin:{deviceId:'b',roomId:'audit_room'},exerciseBank:[{id:ex.id,name:ex.name,updatedAt:'2099-01-01T00:00:00Z'}],tombstones:{exerciseBank:[]}};a.core.mergeNativeExerciseBankSyncDocument(old);assert(!a.core.bank.some(x=>x.id===ex.id),'stale snapshot resurrected deleted ID');const reload=client('a',a.files,a.storage);reload.core.mergeNativeExerciseBankSyncDocument(old);assert(!reload.core.bank.some(x=>x.id===ex.id));});
  await test('write failure retries without another edit; foreground pulls automatically',async()=>{const files=new Map(),a=client('a',files),b=client('b',files);a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();a.transport.writeFailure=true;a.create('Audit retry');await a.tick();a.transport.writeFailure=false;await a.tick(3000);assert(files.get('a').exerciseBank.some(x=>x.name==='Audit retry'),'pending write was lost');await b.event('kgg:native-sync-resume');await b.tick();assert(b.core.bank.some(x=>x.name==='Audit retry'),'resume did not pull');assert.equal(a.transport.maxInflight,1);});
  await test('auto export excludes patient packages, plan values and configured secrets',async()=>{const a=client('a');a.core.state.patient.name='PRIVATE_PATIENT_SENTINEL';a.core.state.plan=[{name:'Audit plan',today:[['PRIVATE_PLAN_SENTINEL']]}];a.core.state.packages=[{id:'private',name:'PRIVATE_PATIENT_SENTINEL',exercises:['Audit plan']}];a.create('Audit library');await a.tick();const text=JSON.stringify(a.files.get('a'));assert(text&&!text.includes('PRIVATE_PATIENT_SENTINEL'));assert(!text.includes('PRIVATE_PLAN_SENTINEL'));assert.equal(a.files.get('a').packages.length,0);});
  await test('whole-document validation prevents partial mutation',async()=>{const a=client('a');assert.equal(typeof a.ctx.window.KGGNativeExerciseSync.mergeTransport,'function');const before=JSON.stringify(a.core.bank),doc=clone(a.core.buildNativeExerciseBankSyncDocument());doc.origin.deviceId='b';doc.exerciseBank=[{id:'valid',name:'First valid'},{id:'bad',name:'Bad media',media:[{id:'missing',type:'image',mime:'image/png'}]}];await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc),/Bildbytes fehlen/);assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');});
  await test('mesh accepts multiple bounded files above 8 MB but rejects aggregate above 32 MB',async()=>{const a=client('a'),seed=clone(a.core.buildNativeExerciseBankSyncDocument()),bytes=Buffer.alloc(1600000,1),digest=createHash('sha256').update(bytes).digest('hex'),base64=bytes.toString('base64');function peer(id){const doc=clone(seed);doc.origin.deviceId=id;doc.origin.therapistId=id;doc.exerciseBank=[{id:'sized_'+id,name:'Sized '+id,media:[{id:id+'_1',type:'image',mime:'image/png',width:1,height:1},{id:id+'_2',type:'image',mime:'image/png',width:1,height:1}]}];doc.mediaBlobs=[1,2].map(n=>({id:id+'_'+n,mime:'image/png',sha256:digest,base64}));return doc;}const mesh={kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[peer('b'),peer('c')]};assert(Buffer.byteLength(JSON.stringify(mesh))>8000000);await a.ctx.window.KGGNativeExerciseSync.mergeTransport(mesh);assert(a.core.bank.some(x=>x.id==='sized_b'));assert(a.core.bank.some(x=>x.id==='sized_c'));const before=JSON.stringify(a.core.bank);await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport({kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[],padding:'x'.repeat(32000001)}),/32 MB/);assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');const tooLarge=peer('b');tooLarge.mediaBlobs[0].base64='a'.repeat(8000001);await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport({kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[peer('c'),tooLarge]}),/8 MB/);assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');});
  await test('manual legacy import preserves absent rich fields and accepts a fresh edit',async()=>{const a=client('a');a.create('Audit legacy');const ex=a.core.bank.find(x=>x.name==='Audit legacy');ex.media=[{id:'retained',mime:'image/png'}];ex.videoUrl='https://example.invalid/video';ex.progressionVariants=[{id:'retained_stage',name:'Retained',media:[]}];a.core.persistCustomBank();a.core.mergeSharedExerciseBank({exercises:[{id:ex.id,name:ex.name,nameEn:'Legacy fresh',sets:4,unit:'Wdh',weightUnit:'kg',updatedAt:'2099-01-01T00:00:00Z'}]});assert.equal(ex.media[0].id,'retained');assert.equal(ex.progressionVariants[0].id,'retained_stage');assert.equal(ex.videoUrl,'https://example.invalid/video');assert.equal(ex.nameEn,'Legacy fresh');a.core.mergeSharedExerciseBank({exercises:[{id:ex.id,name:ex.name,media:[],progressionVariants:[],videoUrl:'',updatedAt:'2099-01-02T00:00:00Z'}]});assert.equal(ex.media.length,0);assert.equal(ex.progressionVariants.length,0);assert.equal(ex.videoUrl,'');});
  await test('visibility, online and polling pull without echo writes',async()=>{const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const writes=a.transport.writes,reads=a.transport.reads;for(const event of ['visibilitychange','pageshow','online','kgg:native-sync-resume']){await a.event(event);await a.tick();}assert.equal(a.transport.reads,reads+4);assert.equal(a.transport.writes,writes);await a.tick(16000);assert(a.transport.reads>reads+4);assert.equal(a.transport.writes,writes);a.ctx.document.visibilityState='hidden';const hiddenReads=a.transport.reads;await a.tick(16000);assert.equal(a.transport.reads,hiddenReads);});
  await test('opening unchanged rich library sync repeatedly never dirties or republishes image bytes',async()=>{
    const {a}=await richLibraryClient(),writes=a.transport.writes,blobReads=a.blobStore.reads;
    const pendingAfterOpen=[],dirtyAfterOpen=[];
    for(let i=0;i<3;i++){
      a.core.openSyncPairModal();assert(a.ctx.document.getElementById('syncPairModal').classList.contains('open'));
      pendingAfterOpen.push(a.storage.getItem('kgg_library_sync_pending_v1'));dirtyAfterOpen.push(a.core.dirty);
      await a.tick(400);a.core.closeSyncPairModal();assert(!a.ctx.document.getElementById('syncPairModal').classList.contains('open'));
    }
    assert.deepEqual({extraWrites:a.transport.writes-writes,extraImageReads:a.blobStore.reads-blobReads,pendingAfterOpen,dirtyAfterOpen},
      {extraWrites:0,extraImageReads:0,pendingAfterOpen:['0','0','0'],dirtyAfterOpen:[false,false,false]},
      'displaying an unchanged persisted library must not create dirty work or read/re-export encrypted images');
  });
  await test('rich library edit and image retry stay durable while unchanged lifecycle polls never echo',async()=>{
    const {a,expectedImages}=await richLibraryClient(),ex=a.core.bank.find(item=>item.id==='rich_library_0'),before=a.transport.writes;
    a.edit(ex,'Audit rich renamed');await a.tick();assert.equal(a.transport.writes,before+1);
    assert.equal(a.files.get('a').exerciseBank.find(item=>item.id===ex.id).name,'Audit rich renamed');
    const oldImage=ex.media[0].id,replacement=await storeRichPicture(a,'rich_image_replacement',99);
    ex.media=[replacement.media];a.transport.writeFailure=true;a.core.persistCustomBank();await a.tick();
    assert.equal(a.transport.writes,before+1);assert.equal(a.core.dirty,true);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');
    assert.equal(a.files.get('a').exerciseBank.find(item=>item.id===ex.id).media[0].id,oldImage);
    a.core.openSyncPairModal();assert.equal(a.core.dirty,true);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');a.core.closeSyncPairModal();
    a.transport.writeFailure=false;await a.tick(3000);assert.equal(a.transport.writes,before+2);
    const published=a.files.get('a');assert.equal(published.mediaBlobs.length,8);
    assert.equal(published.mediaBlobs.find(image=>image.id===replacement.media.id).sha256,replacement.sha256);
    for(const image of published.mediaBlobs)if(image.id!==replacement.media.id)assert.equal(image.sha256,expectedImages.get(image.id));
    assert.equal(a.core.dirty,false);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
    const revision=clone(a.core.bank.find(item=>item.id===ex.id).syncRevision),writes=a.transport.writes,reads=a.transport.reads;
    for(const event of ['visibilitychange','pageshow','online','kgg:native-sync-resume']){await a.event(event);await a.tick();}
    await a.tick(16000);assert(a.transport.reads>=reads+5,'lifecycle handlers and the periodic pull must remain active');assert.equal(a.transport.writes,writes);
    assert.deepEqual(clone(a.core.bank.find(item=>item.id===ex.id).syncRevision),revision);assert.equal(a.transport.maxInflight,1);
    const reload=client('a',a.files,a.storage,a.blobStore),restored=reload.core.bank.find(item=>item.id===ex.id);
    assert.equal(restored.name,'Audit rich renamed');assert.equal(restored.media[0].id,replacement.media.id);
    const record=await reload.core.getEncryptedMediaBlob(replacement.media.id),plain=await reload.core.patientDecryptMedia(restored.media[0],record.blob);
    assert.equal(createHash('sha256').update(Buffer.from(await plain.arrayBuffer())).digest('hex'),replacement.sha256);
  });
  await test('received changes update own snapshot once without revision or replay echo',async()=>{const files=new Map(),a=client('a',files),b=client('b',files);a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();a.create('Audit shared snapshot');await a.tick();const before=b.transport.writes;await b.event('pageshow');await b.tick();const original=files.get('a').exerciseBank.find(ex=>ex.name==='Audit shared snapshot'),received=files.get('b').exerciseBank.find(ex=>ex.id===original.id);assert(received,'own snapshot remains stale after pull');assert.deepEqual(received.syncRevision,original.syncRevision);assert.equal(b.transport.writes,before+1);await b.tick(16000);assert.equal(b.transport.writes,before+1);});
  await test('wrong room, unknown peer, malformed and protected documents leave bank untouched',async()=>{const a=client('a'),base=clone(a.core.buildNativeExerciseBankSyncDocument());base.origin.deviceId='b';base.exerciseBank=[{id:'incoming',name:'Incoming'}];const before=JSON.stringify(a.core.bank);for(const change of [doc=>{doc.roomId='wrong';},doc=>{doc.exerciseBank[0].patientName='PRIVATE';},doc=>{doc.exerciseBank.push(clone(doc.exerciseBank[0]));},doc=>{doc.exerciseBank[0].sets=[];}]){const doc=clone(base);change(doc);await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc));assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');}const stranger=clone(base);stranger.origin.deviceId='unknown';stranger.origin.therapistId='unknown';await a.ctx.window.KGGNativeExerciseSync.mergeTransport(stranger);assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport(null));await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport('{'));});
  await test('read failure remains pending and recovers without another edit',async()=>{const a=client('a');a.transport.readFailure=true;a.core.initNativeExerciseBankSync();await a.tick();assert.equal(a.transport.writes,0);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');a.transport.readFailure=false;await a.tick(3000);assert(a.files.has('a'));assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');});
  await test('failed local bank persistence retries before provider success and survives reload',async()=>{
    const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const set=a.storage.setItem.bind(a.storage);let blocked=true;a.storage.setItem=(key,value)=>{if(blocked&&key==='kgg_html_app_v2_custom_exercise_bank')throw Error('synthetic local persistence fault');return set(key,value);};a.create('Audit storage recovery');await a.tick();assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');blocked=false;await a.event('online');await a.tick(3500);assert(a.files.get('a').exerciseBank.some(ex=>ex.name==='Audit storage recovery'),'provider snapshot omitted recovered local edit');const reload=client('a',a.files,a.storage);assert(reload.core.bank.some(ex=>ex.name==='Audit storage recovery'),'recovered local edit lost on reload');assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
  });
  await test('failed tombstone persistence stays pending until both local stores succeed and deletion survives reload',async()=>{
    for(const oneShot of [true,false]){
      const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();const id=a.core.bank[0].id,set=a.storage.setItem.bind(a.storage),writes=a.transport.writes;let blocked=true,failed=false;
      a.storage.setItem=(key,value)=>{if(blocked&&key==='kgg_html_app_v2_deleted_exercise_bank_ids'&&(!oneShot||!failed)){failed=true;throw Error('synthetic tombstone store fault');}return set(key,value);};a.core.deleteBankExercise(id);await a.tick();
      if(!oneShot){assert.equal(a.transport.writes,writes,'provider success preceded durable tombstone');assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');}
      blocked=false;a.storage.setItem=set;await a.event('online');await a.tick(3500);const reload=client('a',a.files,a.storage);assert(!reload.core.bank.some(ex=>ex.id===id),'failed tombstone write was cleared by successful bank persistence');assert(a.files.get('a').tombstones.exerciseBank.some(item=>item.id===id));assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
    }
  });
  await test('actual Main v2 local builder and empty bridge migrate without patient packages; SAF rejects legacy form',async()=>{
    const html=cp.execFileSync('git',['show','a237aa2:kgg-update/index.html'],{cwd:ROOT,encoding:'utf8',maxBuffer:3000000});
    const source=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(match=>match[1]).find(script=>script.includes("const VERSION='KGG_GITHUB_UPDATE")).replace(/\r\n/g,'\n');
    const legacy=client('b',new Map(),null,new Map(),source.slice(0,source.indexOf('  /* KGG_LOGIC_SMOKE_BOOT_BOUNDARY */')));
    legacy.core.state.packages=[{id:'private',name:'PRIVATE_PATIENT_LEGACY',exercises:['Beinpresse']}];legacy.core.bank.push({id:'legacy_added',name:'Legacy imported exercise',custom:true,sets:3,unit:'Wdh',weightUnit:'kg'});
    const old=clone(legacy.core.buildNativeExerciseBankSyncDocument());
    function local(a,payload){a.ctx.window.KGGNativeSync.platform='android';a.ctx.window.KGGNativeSync.status=()=>({platform:'android',transport:'local',driveConfigured:false});a.ctx.window.KGGNativeSync.read=()=>payload;}
    const empty={kind:'kgg_cross_data_safe_sync',version:2,roomId:'audit_room',schema:'exercise-bank-packages-v2',privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},scopes:['exerciseBank','packages'],exerciseBank:[],packages:[],tombstones:{exerciseBank:[]},exportedAt:''};
    const mesh={kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',generatedAt:'2026-10-15T00:00:00Z',peers:[old],followConfig:{therapistId:'a',syncRoomId:'audit_room',followedTherapists:[]}};
    for(const payload of [old,empty,mesh]){
      const a=client('a');local(a,payload);a.core.initNativeExerciseBankSync();await a.tick();assert(a.files.has('a'),'legacy local bootstrap blocked first write');assert.equal(a.files.get('a').packages.length,0);assert(!JSON.stringify(a.files.get('a')).includes('PRIVATE_PATIENT_LEGACY'));
      if(payload!==empty)assert(a.core.bank.some(ex=>ex.id==='legacy_added'),'legacy exercise was not imported');a.create('Audit legacy creation');await a.tick();assert(client('a',a.files,a.storage).core.bank.some(ex=>ex.name==='Audit legacy creation'));
      const saf=client('a');saf.ctx.window.KGGNativeSync.read=()=>payload;saf.core.initNativeExerciseBankSync();await saf.tick();assert(!saf.files.has('a'),'legacy payload entered configured SAF transport');assert.equal(saf.storage.getItem('kgg_library_sync_pending_v1'),'1');
    }
    for(const mutate of [doc=>{delete doc.origin;},doc=>{doc.packages[0].apiKey='SECRET_SENTINEL';},doc=>{doc.packages[0].unexpected='PRIVATE_SENTINEL';},doc=>{doc.origin.roomId='wrong_room';}]){
      const a=client('a'),payload=clone(old);mutate(payload);const before=JSON.stringify(a.core.bank);local(a,payload);a.core.initNativeExerciseBankSync();await a.tick();assert(!a.files.has('a'),'invalid legacy document was projected into success');assert(JSON.stringify(a.core.bank)===before,'invalid legacy document mutated bank');
    }
    const a=client('a'),unknown=clone(old);unknown.origin.deviceId='unknown';unknown.origin.therapistId='unknown';local(a,unknown);a.core.initNativeExerciseBankSync();await a.tick();assert(!a.core.bank.some(ex=>ex.id==='legacy_added'),'unfollowed legacy origin imported');
  });
  await test('remote bank edit preserves active patient plan identity and values through reload',async()=>{const a=client('a'),id=a.core.bank[0].id;a.core.state.patient={name:'PRIVATE_PATIENT_SENTINEL',notes:'PRIVATE_NOTES_SENTINEL'};a.core.state.plan=[{id:'local_plan_identity',localId:'local_plan_identity',sourceId:id,bankId:id,name:a.core.bank[0].name,today:[['21','13','4']],previous:[['19','12','3']],startLoad:'21',startMetric:'13'}];a.core.save();const before=JSON.stringify({patient:a.core.state.patient,plan:a.core.state.plan});const doc=clone(a.core.buildNativeExerciseBankSyncDocument());doc.origin.deviceId='b';const entry=doc.exerciseBank.find(x=>x.id===id);entry.name='Remote library label';entry.syncRevision={counter:100,deviceId:'b'};await a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc);assert.equal(a.core.bank.find(x=>x.id===id).name,'Remote library label');assert.equal(JSON.stringify({patient:a.core.state.patient,plan:a.core.state.plan}),before);const reload=client('a',a.files,a.storage);assert.equal(JSON.stringify({patient:reload.core.state.patient,plan:reload.core.state.plan}),before);});
  await test('two clients converge on revision conflict and permanent deletion in either peer order',async()=>{const files=new Map(),a=client('a',files),b=client('b',files);a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();const id=a.core.bank[0].id;a.edit(a.core.bank[0],'Audit A edit');b.edit(b.core.bank[0],'Audit B edit');await a.tick();await b.tick();const stale=clone(files.get('b'));await a.event('pageshow');await a.tick();await b.event('pageshow');await b.tick();assert.equal(a.core.bank.find(x=>x.id===id).name,'Audit B edit');assert.equal(b.core.bank.find(x=>x.id===id).name,'Audit B edit');a.core.deleteBankExercise(id);await a.tick();const deletion=clone(files.get('a'));for(const peers of [[stale,deletion],[deletion,stale]]){const c=client('c');await c.ctx.window.KGGNativeExerciseSync.mergeTransport({kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers});assert(!c.core.bank.some(x=>x.id===id));const reload=client('c',new Map(),c.storage);await reload.ctx.window.KGGNativeExerciseSync.mergeTransport(stale);assert(!reload.core.bank.some(x=>x.id===id));}await b.event('online');await b.tick();assert(!b.core.bank.some(x=>x.id===id));a.create('Audit B edit');const recreated=a.core.bank.find(x=>x.name==='Audit B edit');assert(recreated&&recreated.id!==id);});
  await test('image echo reuses verified original ciphertext and survives equal revision replay and reload',async()=>{
    const files=new Map(),a=client('a',files),b=client('b',files);a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();
    a.create('Audit echo image');await a.tick();const ex=a.core.bank.find(x=>x.name==='Audit echo image'),plain=new Blob([Buffer.from([137,80,78,71,13,10,26,10,1,2,3])],{type:'image/png'}),encrypted=await a.core.encryptMediaBlob(plain);
    const media={id:'echo_original',type:'image',mime:'image/png',width:1,height:1,encrypted:true,storage:'indexeddb-local',crypto:{alg:'AES-GCM',key:encrypted.key,iv:encrypted.iv}};await a.core.putEncryptedMediaBlob({id:media.id,blob:encrypted.blob,manifest:media});ex.media=[media];a.core.persistCustomBank();await a.tick();
    const originalRecord=await a.core.getEncryptedMediaBlob(media.id),planReference=clone(media),revision=clone(ex.syncRevision);
    await b.event('pageshow');await b.tick();await a.event('pageshow');await a.tick();
    const current=a.core.bank.find(x=>x.id===ex.id),after=await a.core.getEncryptedMediaBlob(media.id);assert(after===originalRecord,'echo overwrote original ciphertext');assert.deepEqual(clone(current.syncRevision),revision);assert.equal((await a.core.patientDecryptMedia(current.media[0],after.blob)).size,11);assert.equal((await a.core.patientDecryptMedia(planReference,after.blob)).size,11);
    await a.event('pageshow');await a.tick();assert((await a.core.getEncryptedMediaBlob(media.id))===originalRecord,'replay overwrote original ciphertext');const reload=client('a',files,a.storage,a.blobStore),restored=reload.core.bank.find(x=>x.id===ex.id),stored=await reload.core.getEncryptedMediaBlob(media.id);assert.equal((await reload.core.patientDecryptMedia(restored.media[0],stored.blob)).size,11);
  });
  await test('cached media hash markers never replace verification of actual local bytes',async()=>{
    const a=client('a');a.create('Audit hash marker');const ex=a.core.bank.find(x=>x.name==='Audit hash marker'),plain=new Blob([Buffer.from([137,80,78,71,13,10,26,10,1,2,3])],{type:'image/png'}),encrypted=await a.core.encryptMediaBlob(plain);
    const media={id:'marker_image',type:'image',mime:'image/png',width:1,height:1,crypto:{alg:'AES-GCM',key:encrypted.key,iv:encrypted.iv}};await a.core.putEncryptedMediaBlob({id:media.id,blob:encrypted.blob,manifest:media});ex.media=[media];a.core.persistCustomBank();const doc=await a.ctx.window.KGGNativeExerciseSync.buildTransport();doc.origin.deviceId='b';doc.origin.therapistId='b';
    const record=await a.core.getEncryptedMediaBlob(media.id);record.manifest.syncSha256='f'.repeat(64);await a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc);assert((await a.core.getEncryptedMediaBlob(media.id))===record,'incorrect marker caused ciphertext rewrite');
    const bad=await a.core.encryptMediaBlob(new Blob([Buffer.from([137,80,78,71,13,10,26,10,9,9,9])],{type:'image/png'}));const badManifest={...media,crypto:{alg:'AES-GCM',key:bad.key,iv:bad.iv},syncSha256:doc.mediaBlobs[0].sha256};await a.core.putEncryptedMediaBlob({id:media.id,blob:bad.blob,manifest:badManifest});a.core.bank.find(item=>item.id===ex.id).media=[badManifest];const badRecord=await a.core.getEncryptedMediaBlob(media.id),before=JSON.stringify(a.core.bank);await assert.rejects(a.ctx.window.KGGNativeExerciseSync.mergeTransport(doc),/Bild-ID|Bildhash/);assert((await a.core.getEncryptedMediaBlob(media.id))===badRecord,'conflicting bytes were overwritten');assert(JSON.stringify(a.core.bank)===before,'bank mutated before valid import');
  });
  await test('rich variants and actual image bytes import, reload, replace and remove',async()=>{
    const files=new Map(),a=client('a',files),b=client('b',files);
    a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();
    a.create('Audit rich');const ex=a.core.bank.find(x=>x.name==='Audit rich');assert(ex,'creation missing');
    async function picture(id,bytes){
      const encrypted=await a.core.encryptMediaBlob(new Blob([Buffer.from(bytes)],{type:'image/png'}));
      const media={id,type:'image',mime:'image/png',width:1,height:1,encrypted:true,storage:'indexeddb-local',crypto:{alg:'AES-GCM',key:encrypted.key,iv:encrypted.iv},deleteToken:'SECRET_DELETE_SENTINEL'};
      await a.core.putEncryptedMediaBlob({id,blob:encrypted.blob,manifest:media});return media;
    }
    async function imageHex(target,exercise){const record=await target.core.getEncryptedMediaBlob(exercise.media[0].id),plain=await target.core.patientDecryptMedia(exercise.media[0],record.blob);return Buffer.from(await plain.arrayBuffer()).toString('hex');}
    const media=await picture('image_a',[137,80,78,71,13,10,26,10,1,2,3]);
    ex.media=[media];ex.progressionGroupId='group_a';ex.progressionMainId='variant_a';ex.progressionVariants=[{id:'variant_a',name:'Variant',nameEn:'Stage',order:0,media:[media]}];
    a.core.persistCustomBank();await a.tick();const wire=files.get('a');assert.equal(wire.mediaBlobs.length,1);assert(!JSON.stringify(wire).includes('SECRET_DELETE_SENTINEL'));
    const before=JSON.stringify(b.core.bank),bad=clone(wire);bad.mediaBlobs[0].sha256='0'.repeat(64);
    await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(bad),/Bildhash/);assert(JSON.stringify(b.core.bank)===before,'bank mutated before valid import');
    const missing=clone(wire);missing.mediaBlobs=[];await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(missing),/Bildbytes fehlen/);assert(JSON.stringify(b.core.bank)===before,'bank mutated before valid import');
    b.transport.blobFailure=true;await assert.rejects(b.ctx.window.KGGNativeExerciseSync.mergeTransport(wire),/IDB/);assert(JSON.stringify(b.core.bank)===before,'bank mutated before valid import');b.transport.blobFailure=false;
    await b.event('pageshow');await b.tick();let imported=b.core.bank.find(x=>x.id===ex.id);assert.equal(imported.progressionVariants[0].nameEn,'Stage');assert.equal(await imageHex(b,imported),'89504e470d0a1a0a010203');
    const reloaded=client('b',files,b.storage,b.blobStore);assert.equal(await imageHex(reloaded,reloaded.core.bank.find(x=>x.id===ex.id)),'89504e470d0a1a0a010203');
    const replacement=await picture('image_replaced',[137,80,78,71,13,10,26,10,4,5,6]);ex.media=[replacement];ex.progressionVariants[0].media=[replacement];
    a.transport.writeFailure=true;a.core.persistCustomBank();await a.tick();assert.equal(files.get('a').mediaBlobs[0].id,'image_a');a.transport.writeFailure=false;await a.tick(3000);await b.event('online');await b.tick();imported=b.core.bank.find(x=>x.id===ex.id);assert.equal(await imageHex(b,imported),'89504e470d0a1a0a040506');
    ex.media=[];ex.progressionVariants[0].media=[];a.transport.writeFailure=true;a.core.persistCustomBank();await a.tick();a.transport.writeFailure=false;await a.tick(3000);await b.event('online');await b.tick();assert.equal(b.core.bank.find(x=>x.id===ex.id).media.length,0);assert.equal(b.core.bank.find(x=>x.id===ex.id).progressionVariants[0].media.length,0);
  });
  await test('save during an accepted pending write survives the old ACK and publishes the newest revision',async()=>{
    const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();
    const deferred=[];
    a.ctx.window.KGGNativeSync.write=doc=>new Promise(resolve=>deferred.push({doc:clone(doc),finish(value){if(value)a.files.set('a',clone(doc));resolve(value);}}));
    a.create('Audit async first');const ex=a.core.bank.find(item=>item.name==='Audit async first');assert(ex);
    const firstTick=a.tick();await settle();assert.equal(deferred.length,1);assert(a.core.running,'accepted write must remain in flight');
    a.edit(ex,'Audit async newest');const latestRevision=clone(ex.syncRevision);await settle();
    assert.equal(a.core.dirty,true);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');
    assert.equal(deferred[0].doc.exerciseBank.find(item=>item.id===ex.id).name,'Audit async first','in-flight snapshot changed after the newer Save');
    deferred[0].finish(true);await firstTick;
    assert.equal(a.files.get('a').exerciseBank.find(item=>item.id===ex.id).name,'Audit async first');
    assert.equal(a.core.dirty,true,'old provider ACK cleared a newer Save');
    assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1','old ACK cleared newer durable pending marker');
    const nextTick=a.tick();await settle();assert.equal(deferred.length,2);
    assert.equal(deferred[1].doc.exerciseBank.find(item=>item.id===ex.id).name,'Audit async newest');
    assert.deepEqual(deferred[1].doc.exerciseBank.find(item=>item.id===ex.id).syncRevision,latestRevision);
    deferred[1].finish(true);await nextTick;assert.equal(a.core.dirty,false);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
    assert.equal(a.files.get('a').exerciseBank.find(item=>item.id===ex.id).name,'Audit async newest');
  });
  await test('rejected native queue keeps confirmed library changes durable and pending for retry',async()=>{
    const a=client('a');a.core.initNativeExerciseBankSync();await a.tick();
    const originalWrite=a.ctx.window.KGGNativeSync.write;
    a.ctx.window.KGGNativeSync.write=async()=>{throw Error('native_queue_busy');};
    a.create('Audit queue recovery');await a.tick();assert.equal(a.core.dirty,true);
    assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');
    const reload=client('a',a.files,a.storage);assert(reload.core.bank.some(item=>item.name==='Audit queue recovery'));
    a.ctx.window.KGGNativeSync.write=originalWrite;await a.tick(3000);
    assert(a.files.get('a').exerciseBank.some(item=>item.name==='Audit queue recovery'));
    assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'0');
  });
  for(const [action,method]of [['own','configureOwnDriveFile'],['peers','selectDrivePeerFiles'],['disconnect','disconnectDrive']])await test('configuration action '+action+' does not announce success before async native completion',async()=>{
    const a=client('a'),status=a.ctx.document.getElementById('syncPairStatus');status.textContent='Synthetic previous status';
    let finish;a.ctx.window.KGGNativeSync[method]=()=>{throw Error('new consumer must explicitly opt into the async method');};
    a.ctx.window.KGGNativeSync[method+'Async']=()=>new Promise(resolve=>{finish=resolve;});
    const result=a.core.configureNativeDriveSync(action);await settle();
    assert.equal(status.textContent,'Synthetic previous status','configuration was announced before native completion');
    assert(result&&typeof result.then==='function','configuration consumer must await the native operation');
    finish(false);assert.equal(await result,false);assert.equal(a.storage.getItem('kgg_library_sync_pending_v1'),'1');
    assert(!status.textContent.includes('Verbindung geloest'),'failed async disconnect was reported successful');
  });
  await test('actual synchronous pairing chain retains room and peer while native read is pending',async()=>{
    const a=client('a'),writes=[];let config={therapistId:'a',syncRoomId:'audit_room',followedTherapists:[]},finish;
    a.ctx.window.KGGNativeSync.getFollowConfig=()=>clone(config);
    a.ctx.window.KGGNativeSync.setFollowConfig=value=>{config=clone(value);writes.push(clone(value));return true;};
    a.ctx.window.KGGNativeSync.read=()=>new Promise(resolve=>{finish=resolve;});
    a.core.initNativeExerciseBankSync();const pending=a.tick();await settle();assert.equal(typeof finish,'function');
    const before=writes.length;
    const entry=a.core.applyNativeSyncInvite({kind:'kgg_sync_invite',version:2,deviceId:'paired-peer',therapistId:'paired-peer',displayName:'Synthetic peer',roomId:'paired-room'});
    assert.equal(entry.deviceId,'paired-peer');assert.equal(writes.length-before,2,'actual pairing must complete both synchronous config writes');
    assert.equal(config.syncRoomId,'paired-room');assert.equal(config.followedTherapists[0].deviceId,'paired-peer');
    assert.equal(config.followedTherapists[0].roomId,'paired-room');
    finish({kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'audit_room',peers:[]});await pending;
  });
  console.log(JSON.stringify({ok:failures===0,tests:results},null,2));if(failures)process.exitCode=1;
}
if(require.main===module)main().catch(err=>{console.error(err);process.exitCode=1;});
module.exports={client,settle};
