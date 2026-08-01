# KGG Source Chunk 069

- Source: `kgg-update/src` modular source
- Lines: 28981-29034

```html
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
```
