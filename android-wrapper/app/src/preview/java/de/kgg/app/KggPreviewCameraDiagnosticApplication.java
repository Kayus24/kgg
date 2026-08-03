package de.kgg.app;

import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.Toast;

public final class KggPreviewCameraDiagnosticApplication extends Application {
    private static final int BUTTON_ID = 0x4b474743;

    @Override
    public void onCreate() {
        super.onCreate();
        registerActivityLifecycleCallbacks(new ActivityLifecycleCallbacks() {
            @Override
            public void onActivityResumed(Activity activity) {
                attachDiagnosticButton(activity);
            }

            @Override public void onActivityCreated(Activity activity, Bundle state) {}
            @Override public void onActivityStarted(Activity activity) {}
            @Override public void onActivityPaused(Activity activity) {}
            @Override public void onActivityStopped(Activity activity) {}
            @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {}
            @Override public void onActivityDestroyed(Activity activity) {}
        });
    }

    private void attachDiagnosticButton(Activity activity) {
        if (!(activity instanceof MainActivity)) {
            return;
        }
        View decor = activity.getWindow() == null ? null : activity.getWindow().getDecorView();
        if (!(decor instanceof ViewGroup)) {
            return;
        }
        ViewGroup root = (ViewGroup) decor;
        if (root.findViewById(BUTTON_ID) != null) {
            return;
        }

        Button button = new Button(activity);
        button.setId(BUTTON_ID);
        button.setText("Native Kamera-Test");
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(23, 37, 84));
        button.setBackgroundColor(Color.rgb(219, 234, 254));
        button.setContentDescription("Native Kamera-Diagnose öffnen");
        button.setElevation(dp(activity, 10));
        button.setOnClickListener(view -> launchDiagnostic(activity, button, root));

        if (root instanceof FrameLayout) {
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    dp(activity, 48)
            );
            params.gravity = Gravity.END | Gravity.BOTTOM;
            params.setMargins(dp(activity, 10), dp(activity, 10), dp(activity, 10), dp(activity, 58));
            root.addView(button, params);
        } else {
            root.addView(button, new ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    dp(activity, 48)
            ));
        }
    }

    private void launchDiagnostic(Activity activity, Button button, ViewGroup root) {
        button.setEnabled(false);
        WebView webView = findWebView(root);
        Runnable open = () -> {
            try {
                activity.startActivity(new Intent(activity, KggNativeCameraDiagnosticActivity.class));
            } catch (Exception error) {
                Toast.makeText(activity, "Native Kamera-Diagnose nicht verfügbar", Toast.LENGTH_SHORT).show();
            } finally {
                button.setEnabled(true);
            }
        };
        if (webView == null) {
            open.run();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{if(window.KGGScan&&typeof window.KGGScan.closeLiveCamera==='function'){window.KGGScan.closeLiveCamera();}return true;}catch(e){return false;}})();",
                ignored -> open.run()
        );
    }

    private WebView findWebView(View view) {
        if (view instanceof WebView) {
            return (WebView) view;
        }
        if (!(view instanceof ViewGroup)) {
            return null;
        }
        ViewGroup group = (ViewGroup) view;
        for (int i = 0; i < group.getChildCount(); i++) {
            WebView found = findWebView(group.getChildAt(i));
            if (found != null) {
                return found;
            }
        }
        return null;
    }

    private int dp(Activity activity, int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
