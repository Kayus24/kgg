(function(){
  function safeParse(text, fallback){
    try { return JSON.parse(text); } catch (err) { return fallback; }
  }

  if (!window.KGGNativeSync && window.KGGAndroidSync) {
    window.KGGNativeSync = {
      available: true,
      platform: 'android',
      status: function(){
        return safeParse(window.KGGAndroidSync.getStatus(), {available:true, platform:'android'});
      },
      read: function(){
        return safeParse(window.KGGAndroidSync.readSyncJson(), null);
      },
      write: function(syncDocument){
        return window.KGGAndroidSync.writeSyncJson(JSON.stringify(syncDocument || {}));
      },
      listPeers: function(){
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
      }
    };
  }

  if (!window.KGGNativeCamera && window.KGGAndroidApp) {
    window.KGGNativeCamera = {
      available: true,
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
