(function(){
  function safeParse(text, fallback){
    try { return JSON.parse(text); } catch (err) { return fallback; }
  }

  if (!window.KGGNativeSync && window.KGGAndroidSync) {
    function driveStatus(){
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
        if (status.driveConfigured) return Object.assign({available:true, platform:'android'}, status);
        var local = safeParse(window.KGGAndroidSync.getStatus(), {available:true, platform:'android'});
        return Object.assign({}, local, status);
      },
      read: function(){
        if (driveStatus().driveConfigured) return readDrive();
        return safeParse(window.KGGAndroidSync.readSyncJson(), null);
      },
      write: function(syncDocument){
        var payload = JSON.stringify(syncDocument || {});
        if (window.KGGAndroidDriveSync) {
          var configured = driveStatus().driveConfigured;
          var accepted = window.KGGAndroidDriveSync.writeSyncJson(payload);
          if (configured) return !!accepted;
        }
        return window.KGGAndroidSync.writeSyncJson(payload);
      },
      listPeers: function(){
        if (driveStatus().driveConfigured) return readDrive();
        if (typeof window.KGGAndroidSync.listPeerSyncJson !== 'function') {
          return {kind:'kgg_cross_data_safe_sync_mesh', peers:[]};
        }
        return safeParse(window.KGGAndroidSync.listPeerSyncJson(), {kind:'kgg_cross_data_safe_sync_mesh', peers:[]});
      },
      getFollowConfig: function(){
        return safeParse(window.KGGAndroidSync.readFollowConfig(), {therapistId:'', syncRoomId:'', followedTherapists:[]});
      },
      setFollowConfig: function(config){
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

  if (window.KGGNativeSync) {
    window.dispatchEvent(new CustomEvent('kgg:native-sync-ready', {
      detail: window.KGGNativeSync.status()
    }));
  }
})();
