# KGG Source Chunk 067

- Source: `kgg-update/src` modular source
- Lines: 28141-28560

```html
                if (rolloutCode <= currentVersion) {
                    return;
                }
                String htmlUrl = latest.optString("url");
                if (!isTrustedHtmlUrl(htmlUrl)) {
                    return;
                }
                byte[] bytes = downloadBytes(htmlUrl, MAX_HTML_UPDATE_BYTES);
                String html = new String(bytes, StandardCharsets.UTF_8);
                if (!isSafeHtmlUpdate(html)) {
                    return;
                }
                String expectedSha256 = latest.optString("sha256", "").toLowerCase(Locale.ROOT);
                if (!expectedSha256.isEmpty() && !expectedSha256.equals(sha256Hex(bytes))) {
                    return;
                }
                backupCurrentWebApp();
                writeTextAtomically(localWebAppFile(), html);
                prefs.edit()
                        .putInt(PREF_PREVIOUS_ROLLOUT, currentVersion)
                        .putString(PREF_PREVIOUS_RELEASE, prefs.getString(PREF_RELEASE_ID, "preview-bundled"))
                        .putInt(PREF_WEB_VERSION, rolloutCode)
                        .putInt(PREF_ROLLOUT_CODE, rolloutCode)
                        .putString(PREF_RELEASE_ID, latest.optString("requestId", "preview"))
                        .putBoolean(PREF_PENDING_HEALTH, true)
                        .apply();
                runOnUiThread(() -> {
                    Toast.makeText(this, "KGG Preview geladen", Toast.LENGTH_SHORT).show();
                    webView.loadUrl(localWebAppUrl());
                });
            } catch (Exception ignored) {
            }
        }, "kgg-preview-update").start();
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
                if (latestShellVersion <= ANDROID_SHELL_VERSION) {
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
                String versionLabel = "v" + latestShellVersion;
                if (force) {
                    runOnUiThread(() -> installApkFile(apkFile, versionLabel));
                } else {
                    rememberPendingApkFile(apkFile, versionLabel, false);
                }
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

    private void rememberPendingApkFile(File file, String versionLabel, boolean installRequested) {
        if (file == null) {
            return;
        }
        getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE)
                .edit()
                .putString(PREF_PENDING_APK_PATH, file.getAbsolutePath())
                .putString(PREF_PENDING_APK_VERSION, versionLabel == null ? "" : versionLabel)
                .putBoolean(PREF_PENDING_APK_INSTALL_REQUESTED, installRequested)
                .apply();
    }

    private boolean installApkFile(File file, String versionLabel) {
        try {
            if (file == null || !file.exists() || file.length() <= 0) {
                return false;
            }
            SharedPreferences prefs = getSharedPreferences(UPDATE_PREFS, MODE_PRIVATE);
            rememberPendingApkFile(file, versionLabel, true);
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
                    .remove(PREF_PENDING_APK_INSTALL_REQUESTED)
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
            boolean installRequested = prefs.getBoolean(PREF_PENDING_APK_INSTALL_REQUESTED, false);
            if (!installRequested || path == null || path.trim().isEmpty() || !canRequestApkInstalls()) {
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
            status.put("currentShellVersion", ANDROID_SHELL_VERSION);
            status.put("buildTime", BUILD_TIME);
            status.put("buildCode", BUILD_CODE);
            status.put("packageName", getPackageName());
            status.put("profile", isPreviewProfile() ? "preview" : (isAdminProfile() ? "admin" : "kollegen"));
            status.put("previewChannel", isPreviewProfile());
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
            status.put("pendingApkInstallRequested", prefs.getBoolean(PREF_PENDING_APK_INSTALL_REQUESTED, false));
        } catch (Exception ignored) {
        }
        return status.toString();
    }

    private boolean isTrustedHtmlUrl(String url) {
        if (url == null || !url.endsWith(".html")) {
            return false;
        }
        String trustedPrefix = isPreviewProfile() ? TRUSTED_PREVIEW_PREFIX : TRUSTED_UPDATE_PREFIX;
        return url.startsWith(trustedPrefix);
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
```
