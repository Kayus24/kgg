package de.kgg.app;

import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.SharedPreferences;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
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
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.window.OnBackInvokedDispatcher;
import android.widget.Toast;

import androidx.core.content.FileProvider;

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
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 4201;
    private static final int CAMERA_PERMISSION_REQUEST = 4202;
    private static final int RELEASE_HTML_REQUEST = 4301;
    private static final int BUNDLED_WEB_VERSION = 390;
    private static final String BUILD_TIME = "2026-06-21T12:00:00+02:00";
    private static final String BUILD_CODE = "release-pipeline-v2";
    private static final int MAX_HTML_UPDATE_BYTES = 5_500_000;
    private static final int MAX_APK_UPDATE_BYTES = 80_000_000;
    private static final long APK_UPDATE_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000L;
    private static final String BUNDLED_COLLEAGUE_APP_ASSET =
            "www/KGG_APP_KOLLEGEN_v389_flow_stability.html";
    private static final String BUNDLED_ADMIN_APP_ASSET =
            "admin.html";
    private static final String BUNDLED_COLLEAGUE_APP_ASSET_V2 =
            "colleague.html";
    private static final String UPDATE_MANIFEST_URL =
            "https://kayus24.github.io/kgg/therapist-app/android_update_manifest.json";
    private static final String TRUSTED_UPDATE_PREFIX =
            "https://kayus24.github.io/kgg/therapist-app/";
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
    private static final String LOCAL_WEB_FILE_NAME = "kgg_android_current.html";
    private static final String PREVIOUS_WEB_FILE_NAME = "kgg_android_previous.html";
    private static final String APK_MIME_TYPE = "application/vnd.android.package-archive";

    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;
    private WebChromeClient.FileChooserParams pendingFileChooserParams;
    private Uri cameraCaptureUri;
    private String nextFileChooserMode = "";
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
        checkForAndroidAppUpdate(false);
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
        checkForAndroidAppUpdate(false);
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
                    MainActivity.this.filePathCallback.onReceiveValue(null);
                }
                MainActivity.this.filePathCallback = filePathCallback;
                cameraCaptureUri = null;
                boolean forceCamera = consumeNextFileChooserMode().equals("camera");
                boolean wantsCamera = forceCamera || isCameraCaptureRequest(fileChooserParams);
                if (wantsCamera && !hasCameraPermission()) {
                    pendingFileChooserParams = fileChooserParams;
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
                    return true;
                }
                Intent intent = wantsCamera ? createCameraCaptureIntent() : null;
                pendingFileChooserParams = null;
                if (intent == null) {
                    intent = fileChooserParams.createIntent();
                }
                try {
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                    return true;
                } catch (Exception err) {
                    if (wantsCamera) {
                        try {
                            cameraCaptureUri = null;
                            startActivityForResult(fileChooserParams.createIntent(), FILE_CHOOSER_REQUEST);
                            return true;
                        } catch (ActivityNotFoundException fallbackErr) {
                            MainActivity.this.filePathCallback = null;
                            return false;
                        }
                    }
                    MainActivity.this.filePathCallback = null;
                    return false;
                }
            }
        });
    }

    private boolean hasCameraPermission() {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.M
                || checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != CAMERA_PERMISSION_REQUEST) {
            return;
        }
        WebChromeClient.FileChooserParams params = pendingFileChooserParams;
        pendingFileChooserParams = null;
        if (filePathCallback == null || params == null) {
            return;
        }
        if (grantResults.length == 0 || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
            filePathCallback.onReceiveValue(null);
            filePathCallback = null;
            cameraCaptureUri = null;
            Toast.makeText(this, "Kamera-Berechtigung fehlt", Toast.LENGTH_SHORT).show();
            return;
        }
        Intent intent = createCameraCaptureIntent();
        if (intent == null) {
            intent = params.createIntent();
        }
        try {
            startActivityForResult(intent, FILE_CHOOSER_REQUEST);
        } catch (Exception err) {
            filePathCallback.onReceiveValue(null);
            filePathCallback = null;
            cameraCaptureUri = null;
            Toast.makeText(this, "Kamera konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show();
        }
    }

    private boolean isCameraCaptureRequest(WebChromeClient.FileChooserParams params) {
        if (params == null || !params.isCaptureEnabled()) {
            return false;
        }
        String[] acceptTypes = params.getAcceptTypes();
        if (acceptTypes == null || acceptTypes.length == 0) {
            return true;
        }
        for (String type : acceptTypes) {
            if (type == null || type.trim().isEmpty()) {
                continue;
            }
            String lower = type.toLowerCase(Locale.ROOT);
            if (lower.startsWith("image/") || lower.contains(".jpg") || lower.contains(".jpeg") || lower.contains(".png")) {
                return true;
            }
        }
        return false;
    }

    private synchronized String consumeNextFileChooserMode() {
        String mode = nextFileChooserMode == null ? "" : nextFileChooserMode;
        nextFileChooserMode = "";
        return mode;
    }

    private synchronized void setNextFileChooserMode(String mode) {
        if ("camera".equals(mode) || "file".equals(mode)) {
            nextFileChooserMode = mode;
        } else {
            nextFileChooserMode = "";
        }
    }

    private class KggAppBridge {
        @JavascriptInterface
        public boolean isAvailable() {
            return true;
        }

        @JavascriptInterface
        public void setNextFileChooserMode(String mode) {
            MainActivity.this.setNextFileChooserMode(mode);
        }

        @JavascriptInterface
        public String updateStatus() {
            return MainActivity.this.updateStatusJson();
        }

        @JavascriptInterface
        public boolean checkForAppUpdate() {
            MainActivity.this.checkForWebAppUpdate();
            MainActivity.this.checkForAndroidAppUpdate(true);
            return true;
        }

        @JavascriptInterface
        public void markWebAppReady() {
            MainActivity.this.markWebAppHealthy();
        }

        @JavascriptInterface
        public void hideKeyboard() {
            runOnUiThread(() -> {
                try {
                    InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
                    View view = getCurrentFocus();
                    if (view == null) {
                        view = webView;
                    }
                    if (imm != null && view != null) {
                        imm.hideSoftInputFromWindow(view.getWindowToken(), 0);
                    }
                    if (webView != null) {
                        webView.clearFocus();
                    }
                } catch (Exception ignored) {
                }
            });
        }
    }

    void openReleaseHtmlPicker() {
        if (releaseController == null) {
            return;
        }
        runOnUiThread(() -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("text/html");
            try {
                startActivityForResult(intent, RELEASE_HTML_REQUEST);
            } catch (Exception err) {
                Toast.makeText(this, "HTML-Dateiauswahl nicht verfuegbar", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private Intent createCameraCaptureIntent() {
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        intent.putExtra("android.intent.extra.USE_FRONT_CAMERA", false);
        intent.putExtra("android.intent.extra.USE_BACK_CAMERA", true);
        intent.putExtra("android.intent.extras.CAMERA_FACING", 0);
        intent.putExtra("android.intent.extras.LENS_FACING_BACK", 1);
        intent.putExtra("android.intent.extras.LENS_FACING_FRONT", 0);
        if (intent.resolveActivity(getPackageManager()) == null) {
            return null;
        }
        try {
            File picturesDirectory = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            if (picturesDirectory == null) {
                picturesDirectory = getFilesDir();
            }
            File directory = new File(picturesDirectory, "scan");
            if (!directory.exists() && !directory.mkdirs()) {
                return null;
            }
            File photo = File.createTempFile("kgg_scan_", ".jpg", directory);
            cameraCaptureUri = FileProvider.getUriForFile(
                    this,
                    getPackageName() + ".fileprovider",
                    photo
            );
            intent.putExtra(MediaStore.EXTRA_OUTPUT, cameraCaptureUri);
            intent.setClipData(ClipData.newUri(getContentResolver(), "KGG Scan", cameraCaptureUri));
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            grantCameraUriPermissions(intent, cameraCaptureUri);
            return intent;
        } catch (Exception err) {
            cameraCaptureUri = null;
            return null;
        }
    }

    private void grantCameraUriPermissions(Intent intent, Uri uri) {
        if (intent == null || uri == null) {
            return;
        }
        try {
            List<ResolveInfo> cameraApps = getPackageManager().queryIntentActivities(intent, 0);
            for (ResolveInfo app : cameraApps) {
                if (app.activityInfo != null && app.activityInfo.packageName != null) {
                    grantUriPermission(
                            app.activityInfo.packageName,
                            uri,
                            Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    );
                }
            }
        } catch (Exception ignored) {
        }
    }

    void injectAssetScript(String assetPath) {
        try {
            String js = readAssetText(assetPath);
            webView.evaluateJavascript(js, null);
        } catch (Exception err) {
            webView.evaluateJavascript(
                    "console.warn('KGG Android Sync bootstrap konnte nicht geladen werden');",
                    null
            );
        }
    }

    private String readAssetText(String assetPath) throws Exception {
        StringBuilder builder = new StringBuilder();
        try (InputStream stream = getAssets().open(assetPath);
             BufferedReader reader = new BufferedReader(
                     new InputStreamReader(stream, StandardCharsets.UTF_8)
             )) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line).append('\n');
            }
        }
        return builder.toString();
    }

    private void prepareLocalWebApp() {
        try {
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            File current = localWebAppFile();
            int currentVersion = prefs.getInt(PREF_WEB_VERSION, 0);
            String currentBuildCode = prefs.getString(PREF_BUNDLED_BUILD_CODE, "");
            String currentAsset = prefs.getString(PREF_BUNDLED_ASSET, "");
            String bundledAsset = bundledAppAsset();
            boolean bundledIdentityChanged = currentVersion <= BUNDLED_WEB_VERSION
                    && (!BUILD_CODE.equals(currentBuildCode) || !bundledAsset.equals(currentAsset));
            if (!current.exists() || currentVersion < BUNDLED_WEB_VERSION || bundledIdentityChanged) {
                writeTextAtomically(current, readAssetText(bundledAsset));
                prefs.edit()
                        .putInt(PREF_WEB_VERSION, BUNDLED_WEB_VERSION)
                        .putString(PREF_BUNDLED_BUILD_CODE, BUILD_CODE)
                        .putString(PREF_BUNDLED_ASSET, bundledAsset)
                        .apply();
            }
        } catch (Exception ignored) {
        }
    }

    private File localWebAppFile() {
        return new File(new File(getFilesDir(), "web"), LOCAL_WEB_FILE_NAME);
    }

    private File previousWebAppFile() {
        return new File(new File(getFilesDir(), "web"), PREVIOUS_WEB_FILE_NAME);
    }

    private String localWebAppUrl() {
        File current = localWebAppFile();
        if (current.exists()) {
            return Uri.fromFile(current).toString();
        }
        return "file:///android_asset/" + bundledAppAsset();
    }

    private boolean isAdminProfile() {
        return getPackageName().toLowerCase(Locale.ROOT).contains(".admin");
    }

    boolean isAdminProfileForReleaseControl() {
        return isAdminProfile();
    }

    private String bundledAppAsset() {
        return isAdminProfile() ? BUNDLED_ADMIN_APP_ASSET : BUNDLED_COLLEAGUE_APP_ASSET_V2;
    }

    private void checkForWebAppUpdate() {
        new Thread(() -> {
            try {
                JSONObject manifest = new JSONObject(downloadText(UPDATE_MANIFEST_URL, 512_000));
                if (!"kgg_android_web_update_manifest".equals(manifest.optString("kind"))) {
                    return;
                }
                JSONObject channels = manifest.optJSONObject("channels");
                JSONObject channel = channels == null ? null : channels.optJSONObject(isAdminProfile() ? "admin" : "colleague");
                int latestVersion = channel != null
                        ? channel.optInt("rolloutCode", 0)
                        : parseVersionNumber(manifest.optString("latestWebVersion"));
                SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
                int currentVersion = channel != null
                        ? prefs.getInt(PREF_ROLLOUT_CODE, BUNDLED_WEB_VERSION)
                        : prefs.getInt(PREF_WEB_VERSION, BUNDLED_WEB_VERSION);
                if (latestVersion <= currentVersion) {
                    return;
                }
                String htmlUrl = channel != null
                        ? channel.optString("url")
                        : manifest.optString(isAdminProfile() ? "adminHtmlUrl" : "colleagueHtmlUrl");
                if (!isTrustedHtmlUrl(htmlUrl)) {
                    return;
                }
                byte[] bytes = downloadBytes(htmlUrl, MAX_HTML_UPDATE_BYTES);
                String html = new String(bytes, StandardCharsets.UTF_8);
                if (!isSafeHtmlUpdate(html)) {
                    return;
                }
                String expectedSha256 = (channel != null
                        ? channel.optString("sha256")
                        : manifest.optString(isAdminProfile() ? "adminSha256" : "sha256"))
                        .toLowerCase(Locale.ROOT);
                if (!expectedSha256.isEmpty() && !expectedSha256.equals(sha256Hex(bytes))) {
                    return;
                }
                backupCurrentWebApp();
                writeTextAtomically(localWebAppFile(), html);
                prefs.edit()
                        .putInt(PREF_PREVIOUS_ROLLOUT, currentVersion)
                        .putString(PREF_PREVIOUS_RELEASE, prefs.getString(PREF_RELEASE_ID, "v389"))
                        .putInt(PREF_WEB_VERSION, latestVersion)
                        .putInt(PREF_ROLLOUT_CODE, latestVersion)
                        .putString(PREF_RELEASE_ID, channel != null ? channel.optString("releaseId") : manifest.optString("latestWebVersion"))
                        .putBoolean(PREF_PENDING_HEALTH, true)
                        .apply();
                runOnUiThread(() -> {
                    Toast.makeText(this, "KGG-Update geladen", Toast.LENGTH_SHORT).show();
                    webView.loadUrl(localWebAppUrl());
                });
            } catch (Exception ignored) {
            }
        }, "kgg-web-update").start();
    }

    private void backupCurrentWebApp() throws Exception {
        File current = localWebAppFile();
        if (!current.exists()) {
            return;
        }
        File previous = previousWebAppFile();
        File parent = previous.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }
        Files.copy(current.toPath(), previous.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
    }

    private void rollbackUnhealthyPendingUpdate() {
        try {
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            if (!prefs.getBoolean(PREF_PENDING_HEALTH, false)) {
                return;
            }
            File previous = previousWebAppFile();
            if (previous.exists()) {
                Files.copy(previous.toPath(), localWebAppFile().toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
            int previousRollout = prefs.getInt(PREF_PREVIOUS_ROLLOUT, BUNDLED_WEB_VERSION);
            prefs.edit()
                    .putInt(PREF_WEB_VERSION, previousRollout)
                    .putInt(PREF_ROLLOUT_CODE, previousRollout)
                    .putString(PREF_RELEASE_ID, prefs.getString(PREF_PREVIOUS_RELEASE, "v389"))
                    .putBoolean(PREF_PENDING_HEALTH, false)
                    .apply();
        } catch (Exception ignored) {
        }
    }

    private void markWebAppHealthy() {
        getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE)
                .edit()
                .putBoolean(PREF_PENDING_HEALTH, false)
                .apply();
    }

    private void checkForAndroidAppUpdate(boolean force) {
        SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
        long now = System.currentTimeMillis();
        long lastCheckAt = prefs.getLong(PREF_LAST_APK_CHECK_AT, 0L);
        if (!force && now - lastCheckAt < APK_UPDATE_CHECK_INTERVAL_MS) {
            return;
        }
        prefs.edit().putLong(PREF_LAST_APK_CHECK_AT, now).apply();
        new Thread(() -> {
            try {
                JSONObject manifest = new JSONObject(downloadText(UPDATE_MANIFEST_URL, 512_000));
                if (!"kgg_android_web_update_manifest".equals(manifest.optString("kind"))) {
                    return;
                }
                int latestShellVersion = parseVersionNumber(manifest.optString("latestAndroidShellVersion"));
                if (latestShellVersion <= BUNDLED_WEB_VERSION) {
                    return;
                }
                String apkUrl = manifestValue(manifest,
                        isAdminProfile()
                                ? new String[]{"adminAndroidApkUrl", "latestAdminAndroidApkUrl", "androidApkUrl", "latestAndroidApkUrl"}
                                : new String[]{"colleagueAndroidApkUrl", "latestColleagueAndroidApkUrl", "androidApkUrl", "latestAndroidApkUrl"}
                );
                if (!isTrustedApkUrl(apkUrl)) {
                    return;
                }
                byte[] apkBytes = downloadBytes(apkUrl, MAX_APK_UPDATE_BYTES);
                String expectedSha256 = manifestValue(manifest,
                        isAdminProfile()
                                ? new String[]{"adminAndroidApkSha256", "latestAdminAndroidApkSha256", "androidApkSha256", "latestAndroidApkSha256"}
                                : new String[]{"colleagueAndroidApkSha256", "latestColleagueAndroidApkSha256", "androidApkSha256", "latestAndroidApkSha256"}
                ).toLowerCase(Locale.ROOT);
                if (!expectedSha256.isEmpty() && !expectedSha256.equals(sha256Hex(apkBytes))) {
                    return;
                }
                File apkFile = writeApkCacheFile(latestShellVersion, apkBytes);
                runOnUiThread(() -> installApkFile(apkFile, "v" + latestShellVersion));
            } catch (Exception ignored) {
            }
        }, "kgg-apk-update").start();
    }

    private String manifestValue(JSONObject manifest, String[] keys) {
        for (String key : keys) {
            String value = manifest.optString(key, "");
            if (value != null && !value.trim().isEmpty()) {
                return value.trim();
            }
        }
        return "";
    }

    private boolean isTrustedApkUrl(String url) {
        return url != null
                && url.startsWith(TRUSTED_UPDATE_PREFIX)
                && url.endsWith(".apk");
    }

    private byte[] downloadBytes(String url, int maxBytes) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(6000);
        connection.setReadTimeout(15000);
        connection.setRequestProperty("Cache-Control", "no-cache");
        try (InputStream stream = connection.getInputStream();
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[32_768];
            int read;
            while ((read = stream.read(buffer)) != -1) {
                if (output.size() + read > maxBytes) {
                    throw new IllegalStateException("apk_update_too_large");
                }
                output.write(buffer, 0, read);
            }
            return output.toByteArray();
        } finally {
            connection.disconnect();
        }
    }

    private File writeApkCacheFile(int shellVersion, byte[] bytes) throws Exception {
        File directory = new File(getCacheDir(), "apk");
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IllegalStateException("apk_cache_unavailable");
        }
        File file = new File(directory, "kgg_update_v" + shellVersion + ".apk");
        writeBytesAtomically(file, bytes);
        return file;
    }

    private void writeBytesAtomically(File target, byte[] bytes) throws Exception {
        File parent = target.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }
        File temp = new File(parent, target.getName() + ".tmp");
        Files.write(temp.toPath(), bytes);
        try {
            Files.move(
                    temp.toPath(),
                    target.toPath(),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                    java.nio.file.StandardCopyOption.ATOMIC_MOVE
            );
        } catch (java.nio.file.AtomicMoveNotSupportedException err) {
            Files.move(
                    temp.toPath(),
                    target.toPath(),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING
            );
        }
    }

    private boolean canRequestApkInstalls() {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.O
                || getPackageManager().canRequestPackageInstalls();
    }

    private boolean installApkFile(File file, String versionLabel) {
        try {
            if (file == null || !file.exists() || file.length() <= 0) {
                return false;
            }
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            prefs.edit()
                    .putString(PREF_PENDING_APK_PATH, file.getAbsolutePath())
                    .putString(PREF_PENDING_APK_VERSION, versionLabel == null ? "" : versionLabel)
                    .apply();
            if (!canRequestApkInstalls()) {
                Toast.makeText(this, "Installation aus dieser App bitte erlauben", Toast.LENGTH_LONG).show();
                Intent settingsIntent = new Intent(
                        Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + getPackageName())
                );
                startActivity(settingsIntent);
                return false;
            }
            Uri uri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", file);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, APK_MIME_TYPE);
            intent.setClipData(ClipData.newUri(getContentResolver(), "KGG Update", uri));
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            prefs.edit()
                    .remove(PREF_PENDING_APK_PATH)
                    .remove(PREF_PENDING_APK_VERSION)
                    .apply();
            Toast.makeText(this, "KGG-Update wird installiert", Toast.LENGTH_SHORT).show();
            startActivity(intent);
            return true;
        } catch (Exception err) {
            Toast.makeText(this, "APK-Update konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    private void installPendingApkIfAllowed() {
        try {
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            String path = prefs.getString(PREF_PENDING_APK_PATH, "");
            if (path == null || path.trim().isEmpty() || !canRequestApkInstalls()) {
                return;
            }
            installApkFile(new File(path), prefs.getString(PREF_PENDING_APK_VERSION, ""));
        } catch (Exception ignored) {
        }
    }

    private String updateStatusJson() {
        JSONObject status = new JSONObject();
        try {
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            status.put("available", true);
            status.put("platform", "android");
            status.put("currentShellVersion", BUNDLED_WEB_VERSION);
            status.put("buildTime", BUILD_TIME);
            status.put("buildCode", BUILD_CODE);
            status.put("packageName", getPackageName());
            status.put("profile", isAdminProfile() ? "admin" : "kollegen");
            status.put("currentWebVersion", prefs.getInt(PREF_WEB_VERSION, BUNDLED_WEB_VERSION));
            status.put("rolloutCode", prefs.getInt(PREF_ROLLOUT_CODE, BUNDLED_WEB_VERSION));
            status.put("releaseId", prefs.getString(PREF_RELEASE_ID, "v389"));
            status.put("pendingHealthCheck", prefs.getBoolean(PREF_PENDING_HEALTH, false));
            status.put("hasRollbackFile", previousWebAppFile().exists());
            status.put("bundledAsset", bundledAppAsset());
            status.put("localWebFile", LOCAL_WEB_FILE_NAME);
            status.put("loadedHtmlSource", localWebAppFile().exists() ? LOCAL_WEB_FILE_NAME : bundledAppAsset());
            android.content.pm.PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            long versionCode = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                    ? info.getLongVersionCode()
                    : info.versionCode;
            status.put("versionCode", versionCode);
            status.put("versionName", info.versionName == null ? "" : info.versionName);
            status.put("canRequestPackageInstalls", canRequestApkInstalls());
            status.put("lastApkCheckAt", prefs.getLong(PREF_LAST_APK_CHECK_AT, 0L));
            status.put("pendingApkVersion", prefs.getString(PREF_PENDING_APK_VERSION, ""));
        } catch (Exception ignored) {
        }
        return status.toString();
    }

    private boolean isTrustedHtmlUrl(String url) {
        return url != null
                && url.startsWith(TRUSTED_UPDATE_PREFIX)
                && url.endsWith(".html");
    }

    private int parseVersionNumber(String value) {
        if (value == null) {
            return 0;
        }
        java.util.regex.Matcher matcher = java.util.regex.Pattern
                .compile("v(\\d+)", java.util.regex.Pattern.CASE_INSENSITIVE)
                .matcher(value);
        if (!matcher.find()) {
            return 0;
        }
        try {
            return Integer.parseInt(matcher.group(1));
        } catch (Exception err) {
            return 0;
        }
    }

    private boolean isSafeHtmlUpdate(String html) {
        if (html == null || html.length() < 10_000) {
            return false;
        }
        String lower = html.toLowerCase(Locale.ROOT);
        return lower.startsWith("<!doctype html>")
                && lower.contains("<html")
                && html.contains("KGGDataStore")
                && html.contains("currentPlan")
                && !html.contains("document.write(")
                && !html.contains("raw.githubusercontent.com/Kayus24/kgg/main/kgg-update")
                && !html.contains("AIza")
                && !lower.contains("private key")
                && !lower.contains("apikey")
                && !lower.contains("api_key");
    }

    private String downloadText(String url, int maxBytes) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(8000);
        connection.setRequestProperty("Cache-Control", "no-cache");
        try (InputStream stream = connection.getInputStream();
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[16_384];
            int read;
            while ((read = stream.read(buffer)) != -1) {
                if (output.size() + read > maxBytes) {
                    throw new IllegalStateException("update_too_large");
                }
                output.write(buffer, 0, read);
            }
            return output.toString(StandardCharsets.UTF_8.name());
        } finally {
            connection.disconnect();
        }
    }

    private void writeTextAtomically(File target, String text) throws Exception {
        File parent = target.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }
        File temp = new File(parent, target.getName() + ".tmp");
        Files.write(temp.toPath(), text.getBytes(StandardCharsets.UTF_8));
        try {
            Files.move(
                    temp.toPath(),
                    target.toPath(),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                    java.nio.file.StandardCopyOption.ATOMIC_MOVE
            );
        } catch (java.nio.file.AtomicMoveNotSupportedException err) {
            Files.move(
                    temp.toPath(),
                    target.toPath(),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING
            );
        }
    }

    private String sha256Hex(String value) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(value.getBytes(StandardCharsets.UTF_8));
        StringBuilder builder = new StringBuilder(hash.length * 2);
        for (byte b : hash) {
            builder.append(String.format(Locale.ROOT, "%02x", b));
        }
        return builder.toString();
    }

    private String sha256Hex(byte[] value) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(value);
        StringBuilder builder = new StringBuilder(hash.length * 2);
        for (byte b : hash) {
            builder.append(String.format(Locale.ROOT, "%02x", b));
        }
        return builder.toString();
    }

    private String safePdfFilename(String filename) {
        String safe = filename == null ? "" : filename.trim();
        safe = safe.replaceAll("[\\\\/:*?\"<>|]+", "_").replaceAll("\\s+", "_");
        if (safe.isEmpty()) {
            safe = "kgg_trainingsplan.pdf";
        }
        if (!safe.toLowerCase(Locale.ROOT).endsWith(".pdf")) {
            safe = safe + ".pdf";
        }
        return safe;
    }

    private byte[] decodePdfBase64(String base64) {
        byte[] bytes = Base64.decode(base64 == null ? "" : base64, Base64.DEFAULT);
        if (bytes.length < 4 || bytes[0] != '%' || bytes[1] != 'P' || bytes[2] != 'D' || bytes[3] != 'F') {
            throw new IllegalArgumentException("not_pdf");
        }
        return bytes;
    }

    private File writePdfCacheFile(String filename, byte[] bytes) throws Exception {
        File directory = new File(getCacheDir(), "pdf");
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IllegalStateException("pdf_cache_unavailable");
        }
        File file = new File(directory, safePdfFilename(filename));
        Files.write(file.toPath(), bytes);
        return file;
    }

    private boolean openPdfFile(File file) {
        try {
            Uri uri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", file);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(intent);
            return true;
        } catch (Exception err) {
            Toast.makeText(this, "Kein PDF-Viewer gefunden", Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    private Uri savePdfToDownloads(String filename, byte[] bytes) throws Exception {
        String safeName = safePdfFilename(filename);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, safeName);
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf");
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                throw new IllegalStateException("downloads_insert_failed");
            }
            try (OutputStream output = getContentResolver().openOutputStream(uri)) {
                if (output == null) {
                    throw new IllegalStateException("downloads_stream_failed");
                }
                output.write(bytes);
            }
            values.clear();
            values.put(MediaStore.MediaColumns.IS_PENDING, 0);
            getContentResolver().update(uri, values, null, null);
            return uri;
        }
        File directory = getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
        if (directory == null) {
            directory = getFilesDir();
        }
        File pdfDirectory = new File(directory, "pdf");
        if (!pdfDirectory.exists() && !pdfDirectory.mkdirs()) {
            throw new IllegalStateException("documents_unavailable");
        }
        File file = new File(pdfDirectory, safeName);
        Files.write(file.toPath(), bytes);
        return Uri.fromFile(file);
    }

    private class KggPdfBridge {
        @JavascriptInterface
        public boolean openPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                File file = writePdfCacheFile(filename, bytes);
                runOnUiThread(() -> openPdfFile(file));
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }

        @JavascriptInterface
        public boolean downloadPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                savePdfToDownloads(filename, bytes);
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF gespeichert", Toast.LENGTH_SHORT).show());
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF konnte nicht gespeichert werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }

        @JavascriptInterface
        public boolean printPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                String safeName = safePdfFilename(filename);
                runOnUiThread(() -> {
                    PrintManager printManager = (PrintManager) getSystemService(PRINT_SERVICE);
                    if (printManager != null) {
                        printManager.print("KGG " + safeName, new KggPdfPrintAdapter(safeName, bytes), new PrintAttributes.Builder().build());
                    }
                });
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Drucken konnte nicht gestartet werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }
    }

    private static class KggPdfPrintAdapter extends PrintDocumentAdapter {
        private final String filename;
        private final byte[] bytes;

        KggPdfPrintAdapter(String filename, byte[] bytes) {
            this.filename = filename;
            this.bytes = bytes;
        }

        @Override
        public void onLayout(
                PrintAttributes oldAttributes,
                PrintAttributes newAttributes,
                CancellationSignal cancellationSignal,
                LayoutResultCallback callback,
                Bundle extras
        ) {
            if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                callback.onLayoutCancelled();
                return;
            }
            PrintDocumentInfo info = new PrintDocumentInfo.Builder(filename)
                    .setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT)
                    .setPageCount(PrintDocumentInfo.PAGE_COUNT_UNKNOWN)
                    .build();
            callback.onLayoutFinished(info, true);
        }

        @Override
        public void onWrite(
                PageRange[] pages,
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback
        ) {
            if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                callback.onWriteCancelled();
                return;
            }
            try (FileOutputStream output = new FileOutputStream(destination.getFileDescriptor())) {
                output.write(bytes);
                callback.onWriteFinished(new PageRange[]{PageRange.ALL_PAGES});
            } catch (Exception err) {
                callback.onWriteFailed(err.getMessage());
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == RELEASE_HTML_REQUEST) {
            Uri selected = resultCode == RESULT_OK && data != null ? data.getData() : null;
            if (releaseController != null) {
                releaseController.onHtmlSelected(selected);
            }
            return;
        }
        if (requestCode != FILE_CHOOSER_REQUEST || filePathCallback == null) {
            return;
        }
        Uri[] result = null;
        if (resultCode == RESULT_OK) {
            result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
            if ((result == null || result.length == 0) && cameraCaptureUri != null) {
                result = new Uri[]{cameraCaptureUri};
            }
        }
        filePathCallback.onReceiveValue(result);
        filePathCallback = null;
        cameraCaptureUri = null;
    }

    @Override
    public void onBackPressed() {
        handleAndroidBack();
    }

    private void handleAndroidBack() {
        if (webView == null) {
            MainActivity.super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{var m=document.getElementById('syncPairModal');"
                        + "if(m&&(m.classList.contains('open')||getComputedStyle(m).display!=='none')){m.classList.remove('open');return true;}"
                        + "return !!(window.KGGHandleAndroidBack&&window.KGGHandleAndroidBack());}catch(e){return false;}})();",
                value -> {
                    if ("true".equals(value)) {
                        return;
                    }
                    if (webView.canGoBack()) {
                        webView.goBack();
                        return;
                    }
                    MainActivity.super.onBackPressed();
                });
    }
}
