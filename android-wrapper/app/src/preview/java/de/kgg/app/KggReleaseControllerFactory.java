package de.kgg.app;

import android.webkit.WebView;

final class KggReleaseControllerFactory {
    private KggReleaseControllerFactory() {
    }

    static KggReleaseController attach(MainActivity activity, WebView webView) {
        return null;
    }

    static void onPageFinished(MainActivity activity) {
        // Preview builds never expose release-control actions.
    }
}
