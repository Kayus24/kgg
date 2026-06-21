package de.kgg.app;

import android.webkit.WebView;

final class KggReleaseControllerFactory {
    private KggReleaseControllerFactory() {
    }

    static KggReleaseController attach(MainActivity activity, WebView webView) {
        return null;
    }

    static void onPageFinished(MainActivity activity) {
        // Intentionally empty: release control does not exist in this profile.
    }
}
