# KGG Source Chunk 066

- Source: `kgg-update/src` modular source
- Lines: 27721-28140

```html
                                0,
                                0
                        );
                    } catch (IntentSender.SendIntentException err) {
                        documentScannerLaunchStarted = false;
                        startLegacyScannerFallback();
                    }
                })
                .addOnFailureListener(err -> {
                    documentScannerLaunchStarted = false;
                    startLegacyScannerFallback();
                });
    }

    private void clearDocumentScannerInstallListener() {
        ModuleInstallClient moduleClient = documentScannerModuleClient;
        InstallStatusListener listener = documentScannerInstallListener;
        documentScannerModuleClient = null;
        documentScannerInstallListener = null;
        if (moduleClient != null && listener != null) {
            moduleClient.unregisterListener(listener);
        }
    }

    private void startLegacyScannerFallback() {
        if (documentScannerFallbackStarted || documentScannerLaunchStarted || filePathCallback == null) {
            return;
        }
        clearDocumentScannerInstallListener();
        documentScannerFallbackStarted = true;
        WebChromeClient.FileChooserParams params = pendingDocumentScannerParams;
        boolean forceCamera = pendingDocumentScannerForceCamera;
        pendingDocumentScannerParams = null;
        pendingDocumentScannerForceCamera = false;
        if (params == null || !startCurrentFileChooserFlow(params, forceCamera)) {
            completeFileChooserResult(null);
        }
    }

    private void completeFileChooserResult(Uri[] result) {
        ValueCallback<Uri[]> callback = filePathCallback;
        filePathCallback = null;
        pendingFileChooserParams = null;
        pendingForceCamera = false;
        pendingDocumentScannerParams = null;
        pendingDocumentScannerForceCamera = false;
        documentScannerFallbackStarted = false;
        documentScannerLaunchStarted = false;
        clearDocumentScannerInstallListener();
        cameraCaptureUri = null;
        if (callback != null) {
            callback.onReceiveValue(result);
        }
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
        boolean forceCamera = pendingForceCamera;
        pendingFileChooserParams = null;
        pendingForceCamera = false;
        if (filePathCallback == null || params == null) {
            completeFileChooserResult(null);
            return;
        }
        if (grantResults.length == 0 || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
            completeFileChooserResult(null);
            Toast.makeText(this, "Kamera-Berechtigung fehlt", Toast.LENGTH_SHORT).show();
            return;
        }
        Intent intent = createCameraCaptureIntent();
        if (intent == null && !forceCamera) {
            intent = params.createIntent();
        } else if (intent == null) {
            completeFileChooserResult(null);
            Toast.makeText(this, "Kamera konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            startActivityForResult(intent, FILE_CHOOSER_REQUEST);
        } catch (Exception err) {
            completeFileChooserResult(null);
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

    boolean downloadCurrentWebHtml(String filename) {
        try {
            String html = localWebAppFile().exists()
                    ? new String(Files.readAllBytes(localWebAppFile().toPath()), StandardCharsets.UTF_8)
                    : readAssetText(bundledAppAsset());
            saveTextToDownloads(safeHtmlFilename(filename), html, "text/html");
            runOnUiThread(() -> Toast.makeText(this, "Aktuelle HTML gespeichert", Toast.LENGTH_SHORT).show());
            return true;
        } catch (Exception err) {
            runOnUiThread(() -> Toast.makeText(this, "HTML konnte nicht gespeichert werden", Toast.LENGTH_SHORT).show());
            return false;
        }
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

    private boolean isPreviewProfile() {
        return getPackageName().toLowerCase(Locale.ROOT).contains(".preview");
    }

    boolean isAdminProfileForReleaseControl() {
        return isAdminProfile() && !isPreviewProfile();
    }

    private String bundledAppAsset() {
        if (isPreviewProfile()) {
            return BUNDLED_PREVIEW_APP_ASSET;
        }
        return isAdminProfile() ? BUNDLED_ADMIN_APP_ASSET : BUNDLED_COLLEAGUE_APP_ASSET_V2;
    }

    private void checkForWebAppUpdate() {
        if (isPreviewProfile()) {
            checkForPreviewWebAppUpdate();
            return;
        }
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

    private void checkForPreviewWebAppUpdate() {
        new Thread(() -> {
            try {
                JSONObject manifest = new JSONObject(downloadText(PREVIEW_MANIFEST_URL, 512_000));
                if (!"kgg_gpt_preview_manifest".equals(manifest.optString("kind"))) {
                    return;
                }
                JSONObject latest = manifest.optJSONObject("latest");
                if (latest == null) {
                    return;
                }
                int rolloutCode = latest.optInt("rolloutCode", 0);
                SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
                int currentVersion = prefs.getInt(PREF_ROLLOUT_CODE, BUNDLED_WEB_VERSION);
```
