<script>
(function(){
  'use strict';
  function openSourceMediaDb(){
    return new Promise((resolve,reject)=>{
      const req=indexedDB.open('kgg_media_v1',1);
      req.onupgradeneeded=()=>{const db=req.result; if(!db.objectStoreNames.contains('encryptedBlobs'))db.createObjectStore('encryptedBlobs',{keyPath:'id'});};
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Admin-Test-Medien-Speicher nicht verfuegbar'));
    });
  }
  async function getSourceMediaBlob(id){
    const db=await openSourceMediaDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction('encryptedBlobs','readonly');
      const req=tx.objectStore('encryptedBlobs').get(id);
      req.onsuccess=()=>resolve(req.result&&req.result.blob||null);
      req.onerror=()=>reject(req.error||new Error('Admin-Test-Bild nicht gefunden'));
    });
  }
  window.KGGMediaUploadAdapter={
    name:'admin-test-mock-upload-adapter',
    isMock:true,
    async upload(blob,context){
      const manifest=context&&context.manifest||{};
      const id=manifest.id||('test_'+Date.now());
      const ttlSeconds=Number(context&&context.ttlSeconds)||300;
      return {
        downloadUrl:'https://admin-test.invalid/kgg-media/'+encodeURIComponent(id)+'.bin',
        storage:'admin-test-indexeddb',
        expiresAt:new Date(Date.now()+ttlSeconds*1000).toISOString()
      };
    },
    scheduleDelete(media,options){
      const delayMs=Number(options&&options.delayMs)||300000;
      setTimeout(()=>{console.info('ADMIN TEST media expired',media&&media.id);},delayMs);
    },
    delete(media){console.info('ADMIN TEST media deleted',media&&media.id);}
  };
  window.KGGPatientMediaFetchAdapter={
    async fetch(media){
      const blob=await getSourceMediaBlob(media&&media.id);
      if(!blob)throw new Error('Admin-Test-Bild nicht im lokalen Speicher gefunden');
      return blob;
    }
  };
})();
</script>

