package de.kgg.app;

import android.webkit.JavascriptInterface;

import java.lang.reflect.Method;

/** Preview-only adapter that requests the existing preview web-update path without touching APK updates. */
final class KggPreviewWebUpdateBridge {
    private final MainActivity activity;

    KggPreviewWebUpdateBridge(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public boolean requestPreviewWebUpdate() {
        try {
            Method method = MainActivity.class.getDeclaredMethod("checkForPreviewWebAppUpdate");
            method.setAccessible(true);
            method.invoke(activity);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }
}
