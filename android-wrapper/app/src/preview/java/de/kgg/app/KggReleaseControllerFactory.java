package de.kgg.app;

import android.webkit.WebView;

final class KggReleaseControllerFactory {
    private KggReleaseControllerFactory() {
    }

    static KggReleaseController attach(MainActivity activity, WebView webView) {
        webView.addJavascriptInterface(new KggDeviceTestStationBridge(activity), "KGGDeviceTestStation");
        return null;
    }

    static void onPageFinished(MainActivity activity) {
        activity.injectAssetScript("android/kgg_preview_context.js");
        activity.injectAssetScript("android/kgg_dual_device_fixtures.js");
        activity.injectAssetScript("android/kgg_device_test_station.js");
    }
}
