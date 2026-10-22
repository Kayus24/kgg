'use strict';
// Actual production persistence/serializers/crypto, only storage/native boundary doubled.
const assert=require('node:assert/strict'),fs=require('node:fs');
const {client}=require('./kgg_drive_sync_core_smoke');
const {createHash}=require('node:crypto');
const clone=x=>JSON.parse(JSON.stringify(x));
(async()=>{
 const files=new Map(),a=client('a',files),b=client('b',files);
 a.core.initNativeExerciseBankSync();b.core.initNativeExerciseBankSync();await a.tick();await b.tick();
 a.create('Single-leg stance');await a.tick();const ex=a.core.bank.find(x=>x.name==='Single-leg stance');assert(ex);
 const primary=ex.name,id=ex.id;
 const bytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64');
 const encrypted=await a.core.encryptMediaBlob(new Blob([bytes],{type:'image/png'}));
 const media={id:'bilingual-image',type:'image',mime:'image/png',width:1,height:1,encrypted:true,storage:'indexeddb-local',crypto:{alg:'AES-GCM',key:encrypted.key,iv:encrypted.iv}};
 await a.core.putEncryptedMediaBlob({id:media.id,blob:encrypted.blob,manifest:media});
 ex.nameEn='Authored English';ex.nameDe='Einbeinstand';ex.media=[media];ex.progressionGroupId='bilingual-group';ex.progressionVariants=[{id:'bilingual-stage',name:'Easy stance',nameDe:'Leichter Stand',nameEn:'Authored stage',order:0,media:[media]}];
 a.core.persistCustomBank();await a.tick();const wire=clone(files.get('a')),sent=wire.exerciseBank.find(x=>x.id===id);
 assert.equal(sent.name,primary);assert.equal(sent.nameEn,'Authored English');assert.equal(sent.nameDe,'Einbeinstand','catalog serializer dropped German alias');
 assert.equal(sent.progressionVariants[0].nameDe,'Leichter Stand');
 if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(wire));
 await b.event('pageshow');await b.tick();let peer=b.core.bank.find(x=>x.id===id);
 assert.equal(peer.name,primary);assert.equal(peer.nameDe,'Einbeinstand');assert.equal(peer.nameEn,'Authored English');assert.equal(peer.progressionVariants[0].nameDe,'Leichter Stand');
 async function imageHash(c,x){const record=await c.core.getEncryptedMediaBlob(x.media[0].id),plain=await c.core.patientDecryptMedia(x.media[0],record.blob);return createHash('sha256').update(Buffer.from(await plain.arrayBuffer())).digest('hex');}
 assert.equal(await imageHash(b,peer),createHash('sha256').update(bytes).digest('hex'));
 const reloaded=client('b',files,b.storage,b.blobStore);assert.equal(reloaded.core.bank.find(x=>x.id===id).nameDe,'Einbeinstand');assert.equal(await imageHash(reloaded,reloaded.core.bank.find(x=>x.id===id)),await imageHash(b,peer));
 a.core.openEditor(ex);a.ctx.document.getElementById('editNameDe').value='Einbeiniger Stand';a.core.saveEditedExercise();await a.tick();await b.event('online');await b.tick();peer=b.core.bank.find(x=>x.id===id);
 assert.equal(peer.name,primary,'name-assistance/sync renamed primary');assert.equal(peer.nameDe,'Einbeiniger Stand','German-only edit did not cause sync revision/write');assert.equal(b.core.bank.filter(x=>x.id===id).length,1);assert.equal(peer.nameEn,'Authored English');
 delete ex.nameDe;a.core.persistCustomBank();await a.tick();await b.event('online');await b.tick();assert.equal(b.core.bank.find(x=>x.id===id).nameDe,'Einbeiniger Stand','absent label cleared authored value');
 ex.nameDe=42;a.core.persistCustomBank();await a.tick();await b.event('online');await b.tick();assert.equal(b.core.bank.find(x=>x.id===id).nameDe,'Einbeiniger Stand','invalid label cleared authored value');
 ex.nameDe='';a.core.persistCustomBank();await a.tick();await b.event('online');await b.tick();assert.equal(b.core.bank.find(x=>x.id===id).nameDe,'','explicit empty label was not carried');
 assert.equal(await imageHash(b,b.core.bank.find(x=>x.id===id)),createHash('sha256').update(bytes).digest('hex'));
 console.log('Library names roundtrip PASS: primary/DE/EN/stages, real image bytes, reload and absent-invalid-empty semantics');
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
