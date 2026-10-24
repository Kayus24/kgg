(function(){
  function safeParse(text, fallback){
    try { return JSON.parse(text); } catch (err) { return fallback; }
  }

  if (!window.KGGNativeSync && window.KGGAndroidSync) {
    var asyncBridge=window.KGGAndroidSyncAsync,capabilities=null,pending=new Map(),sequence=0;
    try{if(asyncBridge&&asyncBridge.getAsyncVersion()===1)capabilities=JSON.parse(asyncBridge.getCapabilities());}catch(err){}
    var hasAsync=!!(capabilities&&capabilities.version===1&&Array.isArray(capabilities.operations));
    var documentToken=hasAsync?((window.crypto&&typeof window.crypto.randomUUID==='function')?window.crypto.randomUUID():'doc-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2)):'';
    function supports(operation){return hasAsync&&capabilities.operations.indexOf(operation)!==-1;}
    function generation(){return Number(asyncBridge.getConfigurationGeneration());}
    function failure(code,unknown){var error=new Error(code);if(unknown)error.outcomeUnknown=true;return error;}
    function retire(id,error,value){var job=pending.get(id);if(!job)return;pending.delete(id);clearTimeout(job.timer);if(error)job.reject(error);else job.resolve(value);}
    function mutation(operation){return operation==='configureOwnDriveFile'||operation==='selectDrivePeerFiles'||operation==='disconnectDrive';}
    function response(event){
      var value=typeof event.detail==='string'?safeParse(event.detail,null):event.detail;
      if(!value||value.kind!=='kgg_sync_async_result'||value.version!==1||value.documentToken!==documentToken)return;
      var job=pending.get(value.requestId);if(!job||value.operation!==job.operation||value.configurationGeneration!==job.generation)return;
      if(generation()!==job.generation&&!mutation(job.operation)){retire(value.requestId,failure('configuration_changed',job.operation==='write'));return;}
      if(value.ok!==true){retire(value.requestId,failure(typeof value.error==='string'?value.error:'operation_failed',false));return;}
      var result=value.result;
      if(job.operation==='read'){
        if(result&&result.kind==='kgg_sync_transport_error'){retire(value.requestId,failure(result.error||'read_failed',false));return;}
        if(!result||typeof result!=='object'){retire(value.requestId,failure('invalid_payload',false));return;}
      }else if(typeof result!=='boolean'){retire(value.requestId,failure('invalid_result',job.operation==='write'));return;}
      retire(value.requestId,null,result);
      if(mutation(job.operation)&&result)window.dispatchEvent(new CustomEvent('kgg:native-sync-ready',{detail:driveStatus()}));
    }
    function changed(){
      if(!hasAsync)return;
      var current=generation();pending.forEach(function(job,id){if(job.generation!==current&&!mutation(job.operation))retire(id,failure('configuration_changed',job.operation==='write'));});
    }
    function detached(){
      pending.forEach(function(job,id){retire(id,failure('document_detached',job.operation==='write'));});
      window.removeEventListener('kgg:native-sync-result',response);window.removeEventListener('kgg:native-sync-ready',changed);window.removeEventListener('pagehide',detached);
    }
    if(hasAsync){window.addEventListener('kgg:native-sync-result',response);window.addEventListener('kgg:native-sync-ready',changed);window.addEventListener('pagehide',detached);}
    function request(operation,payload){
      return new Promise(function(resolve,reject){
        var id=String(++sequence),current=generation();
        var job={operation:operation,generation:current,resolve:resolve,reject:reject};
        job.timer=setTimeout(function(){retire(id,failure('native_sync_timeout',operation==='write'));},45000);pending.set(id,job);
        try{
          // The potentially large payload crosses JNI once, separately. Native
          // admission parses only this bounded identity header, never image JSON.
          var accepted=asyncBridge.requestSyncJson(JSON.stringify({documentToken:documentToken,requestId:id,operation:operation,configurationGeneration:current}),payload);
          if(accepted!==true)retire(id,failure('native_queue_busy',false));
        }catch(err){retire(id,failure('native_enqueue_failed',operation==='write'));}
      });
    }
    function driveStatus(){
      if(hasAsync){return safeParse(asyncBridge.getStatusSnapshot(),{transport:'initializing',initialized:false,driveConfigured:true,pending:true,providerAccepted:false,lastError:'status_failed'});}
      if (!window.KGGAndroidDriveSync) return {transport:'local',driveConfigured:false,pending:false,providerAccepted:false,lastError:''};
      try {
        var status = JSON.parse(window.KGGAndroidDriveSync.getStatus());
        if (!status || typeof status.driveConfigured !== 'boolean') throw new Error('invalid_status');
        return status;
      } catch (err) {
        return {transport:'saf-document',driveConfigured:true,pending:true,providerAccepted:false,lastError:'status_failed'};
      }
    }
    function readDrive(){
      var document;
      try { document = JSON.parse(window.KGGAndroidDriveSync.readSyncJson()); }
      catch (err) { throw new Error('read_failed'); }
      if (!document || document.kind === 'kgg_sync_transport_error') throw new Error(document && document.error || 'read_failed');
      if (document.kind !== 'kgg_cross_data_safe_sync_mesh' || !Array.isArray(document.peers) || typeof document.roomId !== 'string') throw new Error('invalid_payload');
      return document;
    }
    window.KGGNativeSync = {
      available: true,
      platform: 'android',
      status: function(){
        var status = driveStatus();
        if(hasAsync)return status;
        if (status.driveConfigured) return Object.assign({available:true, platform:'android'}, status);
        var local = safeParse(window.KGGAndroidSync.getStatus(), {available:true, platform:'android'});
        return Object.assign({}, local, status);
      },
      read: function(){
        if(supports('read'))return request('read','');
        if (driveStatus().driveConfigured) return readDrive();
        return safeParse(window.KGGAndroidSync.readSyncJson(), null);
      },
      write: function(syncDocument){
        var payload = JSON.stringify(syncDocument || {});
        if(supports('write'))return request('write',payload);
        if (window.KGGAndroidDriveSync) {
          var configured = driveStatus().driveConfigured;
          var accepted = window.KGGAndroidDriveSync.writeSyncJson(payload);
          if (configured) return !!accepted;
        }
        return window.KGGAndroidSync.writeSyncJson(payload);
      },
      listPeers: function(){
        if(hasAsync){var cached=safeParse(asyncBridge.getPeerSnapshot(),null);if(!cached||!Array.isArray(cached.peers))throw new Error('invalid_peer_snapshot');return cached;}
        if (driveStatus().driveConfigured) return readDrive();
        if (typeof window.KGGAndroidSync.listPeerSyncJson !== 'function') {
          return {kind:'kgg_cross_data_safe_sync_mesh', peers:[]};
        }
        return safeParse(window.KGGAndroidSync.listPeerSyncJson(), {kind:'kgg_cross_data_safe_sync_mesh', peers:[]});
      },
      getFollowConfig: function(){
        if(hasAsync&&typeof asyncBridge.getFollowConfigSnapshot==='function')return safeParse(asyncBridge.getFollowConfigSnapshot(),{therapistId:'',syncRoomId:'',followedTherapists:[]});
        return safeParse(window.KGGAndroidSync.readFollowConfig(), {therapistId:'', syncRoomId:'', followedTherapists:[]});
      },
      setFollowConfig: function(config){
        if(hasAsync&&typeof asyncBridge.writeFollowConfig==='function')return !!asyncBridge.writeFollowConfig(JSON.stringify(config||{}));
        return window.KGGAndroidSync.writeFollowConfig(JSON.stringify(config || {}));
      },
      configureOwnDriveFile: function(options){
        return !!(window.KGGAndroidDriveSync && window.KGGAndroidDriveSync.configureOwnDriveFile(JSON.stringify(options || {})));
      },
      selectDrivePeerFiles: function(options){
        return !!(window.KGGAndroidDriveSync && window.KGGAndroidDriveSync.selectDrivePeerFiles(JSON.stringify(options || {})));
      },
      disconnectDrive: function(){
        return !!(window.KGGAndroidDriveSync && window.KGGAndroidDriveSync.disconnectDrive());
      },
      configureOwnDriveFileAsync: function(options){
        return supports('configureOwnDriveFile')?request('configureOwnDriveFile',JSON.stringify(options||{})):Promise.resolve(window.KGGNativeSync.configureOwnDriveFile(options));
      },
      selectDrivePeerFilesAsync: function(options){
        return supports('selectDrivePeerFiles')?request('selectDrivePeerFiles',JSON.stringify(options||{})):Promise.resolve(window.KGGNativeSync.selectDrivePeerFiles(options));
      },
      disconnectDriveAsync: function(){
        return supports('disconnectDrive')?request('disconnectDrive',''):Promise.resolve(window.KGGNativeSync.disconnectDrive());
      }
    };
  }

  if (!window.KGGNativeCamera && window.KGGAndroidApp) {
    window.KGGNativeCamera = {
      available: true,
      getCapabilities: function(){
        if (typeof window.KGGAndroidApp.getCameraCapabilities !== 'function') {
          return {available:true, platform:'android', webVideoCapture:false, webVideoCaptureVersion:0};
        }
        return safeParse(window.KGGAndroidApp.getCameraCapabilities(), {
          available:true,
          platform:'android',
          webVideoCapture:false,
          webVideoCaptureVersion:0
        });
      },
      setNextPickerMode: function(mode){
        try {
          window.KGGAndroidApp.setNextFileChooserMode(mode === 'camera' ? 'camera' : 'file');
          return true;
        } catch (err) {
          return false;
        }
      }
    };
  }

  if (!window.KGGNativePdf && window.KGGAndroidPdf) {
    window.KGGNativePdf = {
      available: true,
      open: function(filename, base64){
        try { return !!window.KGGAndroidPdf.openPdfBase64(filename || 'kgg_trainingsplan.pdf', base64 || ''); }
        catch (err) { return false; }
      },
      download: function(filename, base64){
        try { return !!window.KGGAndroidPdf.downloadPdfBase64(filename || 'kgg_trainingsplan.pdf', base64 || ''); }
        catch (err) { return false; }
      },
      print: function(filename, base64){
        try { return !!window.KGGAndroidPdf.printPdfBase64(filename || 'kgg_trainingsplan.pdf', base64 || ''); }
        catch (err) { return false; }
      }
    };
  }

  if (!window.KGGNativeAppUpdate && window.KGGAndroidApp) {
    window.KGGNativeAppUpdate = {
      available: true,
      status: function(){
        if (typeof window.KGGAndroidApp.updateStatus !== 'function') {
          return {available:true};
        }
        return safeParse(window.KGGAndroidApp.updateStatus(), {available:true});
      },
      checkNow: function(){
        if (typeof window.KGGAndroidApp.checkForAppUpdate !== 'function') {
          return false;
        }
        return !!window.KGGAndroidApp.checkForAppUpdate();
      }
    };
  }

  try {
    if (window.KGGAndroidApp && typeof window.KGGAndroidApp.markWebAppReady === 'function') {
      window.KGGAndroidApp.markWebAppReady();
    }
  } catch (err) {}

  if (window.KGGNativeSync && window.KGGNativeSync.status().initialized!==false) {
    window.dispatchEvent(new CustomEvent('kgg:native-sync-ready', {
      detail: window.KGGNativeSync.status()
    }));
  }
})();
