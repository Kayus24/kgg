package de.kgg.app;

import android.webkit.WebView;

final class KggReleaseControllerFactory {
    private KggReleaseControllerFactory() {
    }

    static KggReleaseController attach(MainActivity activity, WebView webView) {
        KggReleaseBridge bridge = new KggReleaseBridge(activity);
        webView.addJavascriptInterface(bridge, "KGGReleaseControl");
        return bridge;
    }

    static void onPageFinished(MainActivity activity) {
        activity.injectAssetScript("android/kgg_release_control_bootstrap.js");
    }
}
