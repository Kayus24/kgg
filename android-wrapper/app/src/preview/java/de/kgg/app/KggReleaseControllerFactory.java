package de.kgg.app;

import android.webkit.WebView;

final class KggReleaseControllerFactory {
    private KggReleaseControllerFactory() {
    }

    static KggReleaseController attach(MainActivity activity, WebView webView) {
        if (BuildConfig.KGG_ISOLATED_PREVIEW_TEST) {
            return null; // No job/remote-update bridges in this isolated manual proof.
        }
        webView.addJavascriptInterface(new KggDeviceTestStationBridge(activity), "KGGDeviceTestStationNative");
        webView.addJavascriptInterface(new KggPreviewWebUpdateBridge(activity), "KGGPreviewWebUpdateNative");
        return null;
    }

    static void onPageFinished(MainActivity activity) {
        if (BuildConfig.KGG_ISOLATED_PREVIEW_TEST) {
            return; // Do not start fixtures, runtime updater, or station jobs.
        }
        activity.injectAssetScript("android/kgg_preview_context.js");
        activity.injectAssetScript("android/kgg_dual_device_fixtures.js");
        activity.injectAssetScript("android/kgg_device_test_runtime_guard.js");
        activity.injectAssetScript("android/kgg_device_test_station.js");
    }
}
