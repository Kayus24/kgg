package de.kgg.app;

import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.provider.Settings;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.time.Instant;
import java.util.Locale;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;


/** Admin-only bridge for the same GitHub workflows used by Codex/GPT. */
public final class KggReleaseBridge implements KggReleaseController {
    private static final String OWNER = "Kayus24";
    private static final String REPO = "kgg";
    private static final String REPO_ID = "1235504789";
    private static final String API = "https://api.github.com/repos/" + OWNER + "/" + REPO;
    private static final String PREFS = "kgg_release_control_v2";
    private static final String KEY_ALIAS = "kgg_release_github_token_v2";
    private static final String ACCESS = "access_token";
    private static final String REFRESH = "refresh_token";
    private static final String EXPIRES = "expires_at";
    private static final int MAX_HTML_BYTES = 5_500_000;

    private final MainActivity activity;
    private final SharedPreferences prefs;
    private volatile JSONObject state = new JSONObject();
    private volatile String pendingReleaseId = "";
    private volatile String pendingVersionName = "";
    private volatile String pendingNotes = "";

    public KggReleaseBridge(MainActivity activity) {
        this.activity = activity;
        this.prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        setState("idle", "Bereit", null);
    }

    @JavascriptInterface
    public boolean isAvailable() {
        return activity.isAdminProfileForReleaseControl() && !BuildConfig.KGG_GITHUB_CLIENT_ID.trim().isEmpty();
    }

    @JavascriptInterface
    public String status() {
        JSONObject snapshot;
        synchronized (this) {
            try {
                snapshot = new JSONObject(state.toString());
            } catch (Exception ignored) {
                snapshot = new JSONObject();
            }
        }
        try {
            snapshot.put("available", isAvailable());
            snapshot.put("authenticated", hasUsableToken());
            snapshot.put("repository", OWNER + "/" + REPO);
        } catch (Exception ignored) {
        }
        return snapshot.toString();
    }

    @JavascriptInterface
    public boolean beginLogin() {
        if (!isAvailable()) {
            setState("blocked", "GitHub App Client-ID fehlt im Admin-Build", null);
            return false;
        }
        new Thread(this::runDeviceLogin, "kgg-github-device-login").start();
        return true;
    }

    @JavascriptInterface
    public boolean chooseAndUploadBeta(String releaseId, String versionName, String notes) {
        if (!isAvailable() || !releaseId.matches("r[0-9]{4,8}") || versionName.trim().isEmpty() || notes.trim().isEmpty()) {
            setState("error", "Release-ID, Versionsname oder Notiz ungueltig", null);
            return false;
        }
        pendingReleaseId = releaseId;
        pendingVersionName = versionName.trim();
        pendingNotes = notes.trim();
        activity.openReleaseHtmlPicker();
        return true;
    }

    @JavascriptInterface
    public boolean testConnection() {
        if (!isAvailable()) {
            setState("blocked", "GitHub App Client-ID fehlt im Admin-Build", null);
            return false;
        }
        setState("testing", "GitHub-Verbindung wird getestet", null);
        new Thread(this::runConnectionTest, "kgg-release-connection-test").start();
        return true;
    }

    @JavascriptInterface
    public boolean confirmPromotion(String releaseId) {
        return confirmControl("promote", "colleague", releaseId, "Beta fuer Kolleg:innen freigeben?");
    }

    @JavascriptInterface
    public boolean confirmRollback(String channel, String releaseId) {
        if (!"admin".equals(channel) && !"colleague".equals(channel)) {
            return false;
        }
        return confirmControl("rollback", channel, releaseId, "Kanal " + channel + " auf " + releaseId + " zuruecksetzen?");
    }

    @Override
    public void onHtmlSelected(Uri uri) {
        if (uri == null) {
            setState("idle", "Upload abgebrochen", null);
            return;
        }
        new Thread(() -> uploadCandidate(uri), "kgg-release-upload").start();
    }

    private boolean confirmControl(String operation, String channel, String releaseId, String message) {
        if (!releaseId.matches("[rv][0-9]{3,8}")) {
            return false;
        }
        activity.runOnUiThread(() -> new AlertDialog.Builder(activity)
                .setTitle("KGG Release bestaetigen")
                .setMessage(message + "\n\nDie Aktion erstellt einen geprueften Branch und Pull Request.")
                .setNegativeButton("Abbrechen", null)
                .setPositiveButton("Freigeben", (dialog, which) -> new Thread(
                        () -> dispatchControl(operation, channel, releaseId),
                        "kgg-release-control"
                ).start())
                .show());
        return true;
    }

    private void runDeviceLogin() {
        try {
            setState("login", "GitHub-Anmeldung wird vorbereitet", null);
            String form = "client_id=" + enc(BuildConfig.KGG_GITHUB_CLIENT_ID) + "&repository_id=" + enc(REPO_ID);
            JSONObject device = new JSONObject(requestForm("https://github.com/login/device/code", form));
            String deviceCode = device.getString("device_code");
            String userCode = device.getString("user_code");
            String verificationUri = device.getString("verification_uri");
            String verificationUriComplete = device.optString("verification_uri_complete", verificationUri);
            int interval = Math.max(5, device.optInt("interval", 5));
            int expires = Math.max(60, device.optInt("expires_in", 900));
            JSONObject extra = new JSONObject();
            extra.put("userCode", userCode);
            extra.put("verificationUri", verificationUri);
            extra.put("verificationUriComplete", verificationUriComplete);
            setState("login_waiting", "Code " + userCode + " bei GitHub bestaetigen. Danach hierher zurueckwechseln.", extra);
            showDeviceLoginDialog(userCode, verificationUriComplete);

            long deadline = System.currentTimeMillis() + expires * 1000L;
            while (System.currentTimeMillis() < deadline) {
                Thread.sleep(interval * 1000L);
                String tokenForm = "client_id=" + enc(BuildConfig.KGG_GITHUB_CLIENT_ID)
                        + "&device_code=" + enc(deviceCode)
                        + "&grant_type=" + enc("urn:ietf:params:oauth:grant-type:device_code")
                        + "&repository_id=" + enc(REPO_ID);
                JSONObject token = new JSONObject(requestForm("https://github.com/login/oauth/access_token", tokenForm));
                String error = token.optString("error", "");
                if ("authorization_pending".equals(error)) {
                    continue;
                }
                if ("slow_down".equals(error)) {
                    interval += 5;
                    continue;
                }
                if (!error.isEmpty()) {
                    throw new IllegalStateException(error);
                }
                storeTokens(token);
                setState("ready", "GitHub verbunden", null);
                return;
            }
            throw new IllegalStateException("device_code_expired");
        } catch (Exception err) {
            setState("error", "GitHub-Anmeldung fehlgeschlagen: " + safeMessage(err), null);
        }
    }

    private void showDeviceLoginDialog(String userCode, String verificationUri) {
        activity.runOnUiThread(() -> {
            try {
                new AlertDialog.Builder(activity)
                        .setTitle("GitHub-Code")
                        .setMessage("Diesen Code bei GitHub eingeben:\n\n" + userCode
                                + "\n\nDer Code bleibt nur kurz gueltig. Nach der GitHub-Bestaetigung zur KGG-App zurueckwechseln.")
                        .setNegativeButton("Schliessen", null)
                        .setNeutralButton("Code kopieren", (dialog, which) -> copyDeviceLoginCode(userCode))
                        .setPositiveButton("GitHub oeffnen", (dialog, which) -> openDeviceLoginPage(verificationUri))
                        .show();
            } catch (Exception ignored) {
            }
        });
    }

    private void copyDeviceLoginCode(String userCode) {
        try {
            ClipboardManager clipboard = (ClipboardManager) activity.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                clipboard.setPrimaryClip(ClipData.newPlainText("KGG GitHub Code", userCode));
                Toast.makeText(activity, "GitHub-Code kopiert", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception ignored) {
        }
    }

    private void openDeviceLoginPage(String verificationUri) {
        try {
            activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(verificationUri)));
        } catch (Exception err) {
            setState("error", "GitHub-Seite konnte nicht geoeffnet werden: " + safeMessage(err), null);
        }
    }

    private void uploadCandidate(Uri uri) {
        try {
            String token = requireToken();
            byte[] html = readLimited(uri, MAX_HTML_BYTES);
            String text = new String(html, StandardCharsets.UTF_8);
            if (!text.toLowerCase(Locale.ROOT).startsWith("<!doctype html>") || text.contains("document.write(")) {
                throw new IllegalStateException("HTML-Vertrag verletzt");
            }
            setState("uploading", "Branch und Pull Request werden erstellt", null);
            String suffix = String.valueOf(System.currentTimeMillis());
            String branch = "mobile/admin-" + pendingReleaseId + "-" + suffix;
            JSONObject ref = api("GET", "/git/ref/heads/main", null, token);
            String baseSha = ref.getJSONObject("object").getString("sha");
            JSONObject createRef = new JSONObject();
            createRef.put("ref", "refs/heads/" + branch);
            createRef.put("sha", baseSha);
            api("POST", "/git/refs", createRef, token);

            putFile("release-inbox/admin.html", html, branch, "upload Admin beta " + pendingReleaseId, token);
            JSONObject release = new JSONObject();
            release.put("releaseId", pendingReleaseId);
            release.put("versionName", pendingVersionName);
            release.put("notes", pendingNotes);
            putFile("release-inbox/release.json", (release.toString(2) + "\n").getBytes(StandardCharsets.UTF_8), branch,
                    "add release metadata " + pendingReleaseId, token);

            JSONObject pr = new JSONObject();
            pr.put("title", "[admin-beta] " + pendingReleaseId + " " + pendingVersionName);
            pr.put("head", branch);
            pr.put("base", "main");
            pr.put("body", "Admin-Beta aus der nativen KGG Update-Zentrale. CI erzeugt und prueft beide Profile vor dem Merge.");
            JSONObject created = api("POST", "/pulls", pr, token);
            JSONObject extra = new JSONObject();
            extra.put("pullRequest", created.optString("html_url"));
            extra.put("number", created.optInt("number"));
            setState("submitted", "Beta-PR erstellt; Tests und Auto-Merge laufen", extra);
        } catch (Exception err) {
            setState("error", "Beta-Upload fehlgeschlagen: " + safeMessage(err), null);
        }
    }

    private void runConnectionTest() {
        try {
            String token = requireToken();
            JSONObject ref = api("GET", "/git/ref/heads/main", null, token);
            String sha = ref.optJSONObject("object") == null
                    ? ""
                    : ref.optJSONObject("object").optString("sha", "");
            JSONObject extra = new JSONObject();
            extra.put("repository", OWNER + "/" + REPO);
            extra.put("mainSha", sha.length() > 12 ? sha.substring(0, 12) : sha);
            setState("ready", "GitHub-Test erfolgreich: Repo erreichbar, Token gueltig", extra);
        } catch (Exception err) {
            setState("error", "GitHub-Test fehlgeschlagen: " + safeMessage(err), null);
        }
    }

    private void dispatchControl(String operation, String channel, String releaseId) {
        try {
            String token = requireToken();
            JSONObject inputs = new JSONObject();
            inputs.put("operation", operation);
            inputs.put("release_id", releaseId);
            inputs.put("channel", channel);
            JSONObject body = new JSONObject();
            body.put("ref", "main");
            body.put("inputs", inputs);
            api("POST", "/actions/workflows/release-control.yml/dispatches", body, token);
            setState("submitted", "Release-Control gestartet: " + operation + " " + releaseId, null);
        } catch (Exception err) {
            setState("error", "Release-Control fehlgeschlagen: " + safeMessage(err), null);
        }
    }

    private void putFile(String path, byte[] bytes, String branch, String message, String token) throws Exception {
        JSONObject body = new JSONObject();
        body.put("message", message);
        body.put("branch", branch);
        body.put("content", Base64.encodeToString(bytes, Base64.NO_WRAP));
        api("PUT", "/contents/" + path, body, token);
    }

    private JSONObject api(String method, String path, JSONObject body, String token) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(API + path).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(10_000);
        connection.setReadTimeout(20_000);
        connection.setRequestProperty("Accept", "application/vnd.github+json");
        connection.setRequestProperty("Authorization", "Bearer " + token);
        connection.setRequestProperty("X-GitHub-Api-Version", "2022-11-28");
        connection.setRequestProperty("User-Agent", "KGG-Admin-Release-Control/2");
        if (body != null) {
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            try (OutputStream out = connection.getOutputStream()) {
                out.write(body.toString().getBytes(StandardCharsets.UTF_8));
            }
        }
        int code = connection.getResponseCode();
        InputStream stream = code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream();
        String response = readStream(stream, 2_000_000);
        connection.disconnect();
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("GitHub " + code + ": " + response.substring(0, Math.min(300, response.length())));
        }
        return response.trim().isEmpty() ? new JSONObject() : new JSONObject(response);
    }

    private String requireToken() throws Exception {
        String access = decrypt(prefs.getString(ACCESS, ""));
        long expiresAt = prefs.getLong(EXPIRES, 0L);
        if (!access.isEmpty() && (expiresAt == 0L || expiresAt - System.currentTimeMillis() > 60_000L)) {
            return access;
        }
        String refresh = decrypt(prefs.getString(REFRESH, ""));
        if (refresh.isEmpty()) {
            throw new IllegalStateException("GitHub-Anmeldung erforderlich");
        }
        String form = "client_id=" + enc(BuildConfig.KGG_GITHUB_CLIENT_ID)
                + "&grant_type=refresh_token&refresh_token=" + enc(refresh);
        JSONObject token = new JSONObject(requestForm("https://github.com/login/oauth/access_token", form));
        if (!token.optString("error", "").isEmpty()) {
            throw new IllegalStateException(token.getString("error"));
        }
        storeTokens(token);
        return decrypt(prefs.getString(ACCESS, ""));
    }

    private boolean hasUsableToken() {
        try {
            return !decrypt(prefs.getString(ACCESS, "")).isEmpty() || !decrypt(prefs.getString(REFRESH, "")).isEmpty();
        } catch (Exception err) {
            return false;
        }
    }

    private void storeTokens(JSONObject token) throws Exception {
        long expiresAt = token.has("expires_in")
                ? System.currentTimeMillis() + token.optLong("expires_in", 28_800L) * 1000L
                : 0L;
        SharedPreferences.Editor editor = prefs.edit()
                .putString(ACCESS, encrypt(token.getString("access_token")))
                .putLong(EXPIRES, expiresAt);
        if (token.has("refresh_token")) {
            editor.putString(REFRESH, encrypt(token.getString("refresh_token")));
        }
        editor.apply();
    }

    private String requestForm(String url, String form) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setConnectTimeout(10_000);
        connection.setReadTimeout(20_000);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        try (OutputStream out = connection.getOutputStream()) {
            out.write(form.getBytes(StandardCharsets.UTF_8));
        }
        int code = connection.getResponseCode();
        String response = readStream(code < 400 ? connection.getInputStream() : connection.getErrorStream(), 1_000_000);
        connection.disconnect();
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("GitHub OAuth " + code);
        }
        return response;
    }

    private byte[] readLimited(Uri uri, int maxBytes) throws Exception {
        try (InputStream in = activity.getContentResolver().openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            if (in == null) throw new IllegalStateException("Datei nicht lesbar");
            byte[] buffer = new byte[16_384];
            int read;
            while ((read = in.read(buffer)) != -1) {
                if (out.size() + read > maxBytes) throw new IllegalStateException("HTML zu gross");
                out.write(buffer, 0, read);
            }
            return out.toByteArray();
        }
    }

    private String readStream(InputStream stream, int maxBytes) throws Exception {
        if (stream == null) return "";
        try (InputStream in = stream; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                if (out.size() + read > maxBytes) throw new IllegalStateException("Antwort zu gross");
                out.write(buffer, 0, read);
            }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    private String encrypt(String plain) throws Exception {
        if (plain == null || plain.isEmpty()) return "";
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] ciphertext = cipher.doFinal(plain.getBytes(StandardCharsets.UTF_8));
        return Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + ":"
                + Base64.encodeToString(ciphertext, Base64.NO_WRAP);
    }

    private String decrypt(String encoded) throws Exception {
        if (encoded == null || encoded.isEmpty()) return "";
        String[] parts = encoded.split(":", 2);
        if (parts.length != 2) return "";
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), StandardCharsets.UTF_8);
    }

    private SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(KEY_ALIAS)) {
            return ((KeyStore.SecretKeyEntry) store.getEntry(KEY_ALIAS, null)).getSecretKey();
        }
        KeyGenerator generator = KeyGenerator.getInstance("AES", "AndroidKeyStore");
        generator.init(new android.security.keystore.KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                android.security.keystore.KeyProperties.PURPOSE_ENCRYPT | android.security.keystore.KeyProperties.PURPOSE_DECRYPT
        ).setBlockModes(android.security.keystore.KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(android.security.keystore.KeyProperties.ENCRYPTION_PADDING_NONE)
                .build());
        return generator.generateKey();
    }

    private synchronized void setState(String phase, String message, JSONObject extra) {
        JSONObject next = new JSONObject();
        if (extra != null) {
            try {
                next = new JSONObject(extra.toString());
            } catch (Exception ignored) {
            }
        }
        try {
            next.put("phase", phase);
            next.put("message", message);
            next.put("updatedAt", Instant.now().toString());
        } catch (Exception ignored) {
        }
        state = next;
    }

    private String enc(String value) throws Exception {
        return URLEncoder.encode(value, StandardCharsets.UTF_8.name());
    }

    private String safeMessage(Exception err) {
        String message = err.getMessage();
        return message == null || message.trim().isEmpty() ? err.getClass().getSimpleName() : message;
    }
}
