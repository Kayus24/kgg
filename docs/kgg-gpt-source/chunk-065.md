# KGG Source Chunk 065

- Source: `kgg-update/src` modular source
- Lines: 27301-27720

```html
}

def stageAdminProfileAsset = tasks.register("stageAdminProfileAsset", Copy) {
    from("../../therapist-app/releases/web/r0419/admin.html")
    into(layout.buildDirectory.dir("generated/kggAssets/admin"))
}

def stageColleagueProfileAsset = tasks.register("stageColleagueProfileAsset", Copy) {
    from("../../therapist-app/releases/web/r0419/colleague.html")
    into(layout.buildDirectory.dir("generated/kggAssets/kollegen"))
}

def stagePreviewProfileAsset = tasks.register("stagePreviewProfileAsset", Copy) {
    from("../../kgg-update/index.html")
    into(layout.buildDirectory.dir("generated/kggAssets/preview"))
    rename { "preview.html" }
}

afterEvaluate {
    tasks.named("mergeAdminDebugAssets").configure { dependsOn(stageAdminProfileAsset) }
    tasks.named("mergeKollegenDebugAssets").configure { dependsOn(stageColleagueProfileAsset) }
    tasks.named("mergePreviewDebugAssets").configure { dependsOn(stagePreviewProfileAsset) }
}

dependencies {
    implementation "androidx.core:core:1.13.1"
    implementation("com.google.android.gms:play-services-mlkit-document-scanner:16.0.0") {
        exclude group: "org.jetbrains.kotlin", module: "kotlin-stdlib-jdk7"
        exclude group: "org.jetbrains.kotlin", module: "kotlin-stdlib-jdk8"
    }
}

<!-- SOURCE FILE: android-wrapper/app/src/main/AndroidManifest.xml -->
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="${appLabel}"
        android:theme="@style/AppTheme">
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/kgg_file_paths" />
        </provider>
        <activity
            android:name=".MainActivity"
            android:configChanges="keyboard|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>

<!-- SOURCE FILE: android-wrapper/app/src/main/java/de/kgg/app/MainActivity.java -->
package de.kgg.app;

import android.Manifest;
import android.app.Activity;
import android.app.Dialog;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.SharedPreferences;
import android.content.Intent;
import android.content.IntentSender;
import android.content.pm.ResolveInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Environment;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import android.provider.Settings;
import android.print.PageRange;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintDocumentInfo;
import android.print.PrintManager;
import android.util.Base64;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.JavascriptInterface;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.window.OnBackInvokedDispatcher;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import com.google.android.gms.common.moduleinstall.InstallStatusListener;
import com.google.android.gms.common.moduleinstall.ModuleInstall;
import com.google.android.gms.common.moduleinstall.ModuleInstallClient;
import com.google.android.gms.common.moduleinstall.ModuleInstallRequest;
import com.google.android.gms.common.moduleinstall.ModuleInstallStatusUpdate;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanner;
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanning;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanningResult;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 4201;
    private static final int CAMERA_PERMISSION_REQUEST = 4202;
    private static final int DOCUMENT_SCANNER_REQUEST = 4203;
    private static final int RELEASE_HTML_REQUEST = 4301;
    private static final int ANDROID_SHELL_VERSION = 401;
    private static final int BUNDLED_WEB_VERSION = 419;
    private static final String BUILD_TIME = "2026-07-01T00:00:00+02:00";
    private static final String BUILD_CODE = "v401-r0419-share-apk-provider";
    private static final int MAX_HTML_UPDATE_BYTES = 5_500_000;
    private static final int MAX_APK_UPDATE_BYTES = 80_000_000;
    private static final long APK_UPDATE_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000L;
    private static final String BUNDLED_COLLEAGUE_APP_ASSET =
            "www/KGG_APP_KOLLEGEN_v389_flow_stability.html";
    private static final String BUNDLED_ADMIN_APP_ASSET =
            "admin.html";
    private static final String BUNDLED_COLLEAGUE_APP_ASSET_V2 =
            "colleague.html";
    private static final String BUNDLED_PREVIEW_APP_ASSET =
            "preview.html";
    private static final String UPDATE_MANIFEST_URL =
            "https://kayus24.github.io/kgg/therapist-app/android_update_manifest.json";
    private static final String PREVIEW_MANIFEST_URL =
            "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/index.json";
    private static final String TRUSTED_UPDATE_PREFIX =
            "https://kayus24.github.io/kgg/therapist-app/";
    private static final String TRUSTED_PREVIEW_PREFIX =
            "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/";
    private static final String UPDATE_PREFS = "kgg_android_update_prefs";
    private static final String PREF_WEB_VERSION = "current_web_version";
    private static final String PREF_ROLLOUT_CODE = "current_rollout_code_v2";
    private static final String PREF_RELEASE_ID = "current_release_id_v2";
    private static final String PREF_PENDING_HEALTH = "pending_web_health_v2";
    private static final String PREF_PREVIOUS_ROLLOUT = "previous_rollout_code_v2";
    private static final String PREF_PREVIOUS_RELEASE = "previous_release_id_v2";
    private static final String PREF_LAST_APK_CHECK_AT = "last_apk_check_at";
    private static final String PREF_BUNDLED_BUILD_CODE = "bundled_build_code";
    private static final String PREF_BUNDLED_ASSET = "bundled_asset";
    private static final String PREF_PENDING_APK_PATH = "pending_apk_path";
    private static final String PREF_PENDING_APK_VERSION = "pending_apk_version";
    private static final String PREF_PENDING_APK_INSTALL_REQUESTED = "pending_apk_install_requested";
    private static final String LOCAL_WEB_FILE_NAME = "kgg_android_current.html";
    private static final String PREVIOUS_WEB_FILE_NAME = "kgg_android_previous.html";
    private static final String APK_MIME_TYPE = "application/vnd.android.package-archive";

    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;
    private WebChromeClient.FileChooserParams pendingFileChooserParams;
    private WebChromeClient.FileChooserParams pendingDocumentScannerParams;
    private Uri cameraCaptureUri;
    private String nextFileChooserMode = "";
    private boolean pendingForceCamera;
    private boolean pendingDocumentScannerForceCamera;
    private boolean documentScannerFallbackStarted;
    private boolean documentScannerLaunchStarted;
    private ModuleInstallClient documentScannerModuleClient;
    private InstallStatusListener documentScannerInstallListener;
    private KggReleaseController releaseController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        configureSystemBars();
        webView = new WebView(this);
        setContentView(webView);
        configureWebView();
        configureBackHandling();
        rollbackUnhealthyPendingUpdate();
        prepareLocalWebApp();
        webView.loadUrl(localWebAppUrl());
        checkForWebAppUpdate();
        if (!isPreviewProfile()) {
            checkForAndroidAppUpdate(false);
        }
    }

    private void configureBackHandling() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    this::handleAndroidBack
            );
        }
    }

    private void configureSystemBars() {
        Window window = getWindow();
        if (window == null) {
            return;
        }
        window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS | WindowManager.LayoutParams.FLAG_TRANSLUCENT_NAVIGATION);
        window.setStatusBarColor(Color.rgb(238, 244, 251));
        window.setNavigationBarColor(Color.rgb(238, 244, 251));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            int flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
            window.getDecorView().setSystemUiVisibility(flags);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        installPendingApkIfAllowed();
        checkForWebAppUpdate();
        if (!isPreviewProfile()) {
            checkForAndroidAppUpdate(false);
        }
    }

    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.addJavascriptInterface(new KggSyncBridge(this), "KGGAndroidSync");
        webView.addJavascriptInterface(new KggAppBridge(), "KGGAndroidApp");
        webView.addJavascriptInterface(new KggPdfBridge(), "KGGAndroidPdf");
        releaseController = KggReleaseControllerFactory.attach(this, webView);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                injectAssetScript("android/kgg_android_sync_bootstrap.js");
                KggReleaseControllerFactory.onPageFinished(MainActivity.this);
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(
                    WebView webView,
                    ValueCallback<Uri[]> filePathCallback,
                    FileChooserParams fileChooserParams
            ) {
                if (MainActivity.this.filePathCallback != null) {
                    completeFileChooserResult(null);
                }
                MainActivity.this.filePathCallback = filePathCallback;
                cameraCaptureUri = null;
                boolean forceCamera = consumeNextFileChooserMode().equals("camera");
                boolean wantsCamera = forceCamera || isCameraCaptureRequest(fileChooserParams);
                if (isPreviewProfile() && wantsCamera) {
                    pendingDocumentScannerParams = fileChooserParams;
                    pendingDocumentScannerForceCamera = forceCamera;
                    documentScannerFallbackStarted = false;
                    documentScannerLaunchStarted = false;
                    startDocumentScannerOrCameraFallback();
                    return true;
                }
                return startCurrentFileChooserFlow(fileChooserParams, forceCamera);
            }
        });
    }

    private boolean startCurrentFileChooserFlow(
            WebChromeClient.FileChooserParams fileChooserParams,
            boolean forceCamera
    ) {
        boolean wantsCamera = forceCamera || isCameraCaptureRequest(fileChooserParams);
        if (wantsCamera && !hasCameraPermission()) {
            pendingFileChooserParams = fileChooserParams;
            pendingForceCamera = forceCamera;
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
            return true;
        }
        Intent intent = wantsCamera ? createCameraCaptureIntent() : null;
        pendingFileChooserParams = null;
        pendingForceCamera = false;
        if (intent == null && !forceCamera) {
            intent = fileChooserParams.createIntent();
        } else if (intent == null) {
            completeFileChooserResult(null);
            Toast.makeText(this, "Kamera konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show();
            return false;
        }
        try {
            startActivityForResult(intent, FILE_CHOOSER_REQUEST);
            return true;
        } catch (Exception err) {
            if (wantsCamera && !forceCamera) {
                try {
                    cameraCaptureUri = null;
                    startActivityForResult(fileChooserParams.createIntent(), FILE_CHOOSER_REQUEST);
                    return true;
                } catch (ActivityNotFoundException fallbackErr) {
                    completeFileChooserResult(null);
                    return false;
                }
            }
            completeFileChooserResult(null);
            return false;
        }
    }

    private void startDocumentScannerOrCameraFallback() {
        GmsDocumentScannerOptions options = new GmsDocumentScannerOptions.Builder()
                .setGalleryImportAllowed(false)
                .setPageLimit(1)
                .setResultFormats(GmsDocumentScannerOptions.RESULT_FORMAT_JPEG)
                .setScannerMode(GmsDocumentScannerOptions.SCANNER_MODE_FULL)
                .build();
        GmsDocumentScanner scanner = GmsDocumentScanning.getClient(options);
        ModuleInstallClient moduleClient = ModuleInstall.getClient(this);
        moduleClient.areModulesAvailable(scanner)
                .addOnSuccessListener(response -> {
                    if (filePathCallback == null) {
                        return;
                    }
                    if (response.areModulesAvailable()) {
                        launchDocumentScanner(scanner);
                    } else {
                        installDocumentScannerModule(scanner, moduleClient);
                    }
                })
                .addOnFailureListener(err -> startLegacyScannerFallback());
    }

    private void installDocumentScannerModule(
            GmsDocumentScanner scanner,
            ModuleInstallClient moduleClient
    ) {
        documentScannerModuleClient = moduleClient;
        InstallStatusListener listener = new InstallStatusListener() {
            @Override
            public void onInstallStatusUpdated(ModuleInstallStatusUpdate update) {
                if (documentScannerInstallListener != this || filePathCallback == null) {
                    return;
                }
                int state = update.getInstallState();
                if (state == ModuleInstallStatusUpdate.InstallState.STATE_COMPLETED) {
                    clearDocumentScannerInstallListener();
                    launchDocumentScanner(scanner);
                } else if (state == ModuleInstallStatusUpdate.InstallState.STATE_CANCELED
                        || state == ModuleInstallStatusUpdate.InstallState.STATE_FAILED) {
                    clearDocumentScannerInstallListener();
                    startLegacyScannerFallback();
                }
            }
        };
        documentScannerInstallListener = listener;
        ModuleInstallRequest request = ModuleInstallRequest.newBuilder()
                .addApi(scanner)
                .setListener(listener)
                .build();
        moduleClient.installModules(request)
                .addOnSuccessListener(response -> {
                    if (response.areModulesAlreadyInstalled() && filePathCallback != null) {
                        clearDocumentScannerInstallListener();
                        launchDocumentScanner(scanner);
                    }
                })
                .addOnFailureListener(err -> {
                    clearDocumentScannerInstallListener();
                    startLegacyScannerFallback();
                });
    }

    private void launchDocumentScanner(GmsDocumentScanner scanner) {
        if (documentScannerLaunchStarted || documentScannerFallbackStarted || filePathCallback == null) {
            return;
        }
        clearDocumentScannerInstallListener();
        documentScannerLaunchStarted = true;
        scanner.getStartScanIntent(this)
                .addOnSuccessListener(intentSender -> {
                    try {
                        startIntentSenderForResult(
                                intentSender,
                                DOCUMENT_SCANNER_REQUEST,
                                null,
                                0,
```
