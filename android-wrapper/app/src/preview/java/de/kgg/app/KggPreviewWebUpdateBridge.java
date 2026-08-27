package de.kgg.app;

import android.webkit.JavascriptInterface;

import java.lang.reflect.Method;

/** Preview-only adapter that requests the existing preview web-update path without touching APK updates. */
final class KggPreviewWebUpdateBridge {
    private static final String PREVIEW_UPDATE_THREAD_NAME = "kgg-preview-update";

    private final MainActivity activity;

    KggPreviewWebUpdateBridge(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public synchronized boolean requestPreviewWebUpdate() {
        if (hasRunningPreviewWebUpdateThread()) {
            return true;
        }
        try {
            Method method = MainActivity.class.getDeclaredMethod("checkForPreviewWebAppUpdate");
            method.setAccessible(true);
            method.invoke(activity);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    private boolean hasRunningPreviewWebUpdateThread() {
        for (Thread thread : Thread.getAllStackTraces().keySet()) {
            if (thread != null
                    && thread.isAlive()
                    && PREVIEW_UPDATE_THREAD_NAME.equals(thread.getName())) {
                return true;
            }
        }
        return false;
    }
}
