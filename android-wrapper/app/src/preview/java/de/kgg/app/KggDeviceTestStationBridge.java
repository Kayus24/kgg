package de.kgg.app;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.res.Configuration;
import android.graphics.Point;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Display;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Preview-only native contract for the Tab S9 test station.
 *
 * The four JavaScript methods are deliberately small. The report input is
 * treated as untrusted: native code keeps only the fixed test ids, statuses,
 * durations and note codes before it persists or opens an issue draft.
 */
public final class KggDeviceTestStationBridge {
    private static final String PREFS = "kgg_device_test_station_v1";
    private static final String ACTIVE = "active";
    private static final String SESSION_ID = "session_id";
    private static final String STARTED_AT = "started_at";
    private static final String REQUEST_ID = "request_id";
    private static final String PATCH_HASH = "patch_hash";
    private static final String BASE_SHA = "base_sha";
    private static final String COMMIT_SHA = "commit_sha";
    private static final String PREVIEW_VERSION = "preview_version";
    private static final String APP_VERSION_CODE = "app_version_code";
    private static final String PREVIOUS_KEEP_SCREEN_ON = "previous_keep_screen_on";
    private static final String LAST_REPORT = "last_report";

    private static final String REPORT_ISSUE_URL =
            "https://github.com/Kayus24/kgg-device-test-reports/issues/new";
    private static final int REPORT_SCHEMA_VERSION = 1;
    private static final int MAX_REPORT_CHARS = 16_000;
    private static final int MAX_ISSUE_BODY_CHARS = 10_000;
    private static final long MAX_TEST_DURATION_MS = 24L * 60L * 60L * 1000L;
    private static final String NOT_EXECUTED_NOTE_CODE = "not_executed";
    private static final String[] TEST_IDS = {
            "admin-portrait",
            "admin-landscape",
            "admin-split-screen",
            "admin-package-button",
            "admin-touch-dialog-save",
            "admin-seven-exercises",
            "admin-reorder-save-reload",
            "patient-first-start",
            "patient-add-plan",
            "patient-replace-cancel",
            "patient-switch-plan",
            "patient-rename",
            "patient-values-reload",
            "patient-offline-restore",
            "qr-oppo-display",
            "qr-scan-7",
            "qr-scan-12",
            "qr-scan-20",
            "qr-angle-distance",
            "qr-weak-photo-fallback",
            "qr-camera-stop",
    };
    private static final Map<String, String> NOTE_CODES = createNoteCodes();
    private static final Set<String> OPTIONAL_TESTS =
            Collections.singleton("qr-oppo-display");

    private final MainActivity activity;
    private final SharedPreferences preferences;

    KggDeviceTestStationBridge(MainActivity activity) {
        this.activity = activity;
        this.preferences = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (isActive()) {
            setKeepScreenOn(true);
        }
    }

    @JavascriptInterface
    public String getDeviceInfo() {
        try {
            return deviceInfo().toString();
        } catch (Exception ignored) {
            return "{\"model\":\"unknown\",\"androidVersion\":\"unknown\","
                    + "\"webViewVersion\":\"unknown\",\"screen\":{\"width\":0,\"height\":0,"
                    + "\"orientation\":\"unknown\"}}";
        }
    }

    @JavascriptInterface
    public String beginSession() {
        synchronized (this) {
            try {
                if (isActive() && nonEmpty(preferences.getString(SESSION_ID, ""))) {
                    setKeepScreenOn(true);
                    return sessionSnapshot(true).toString();
                }
                JSONObject context = buildContext();
                String sessionId = "tab-s9-" + UUID.randomUUID().toString().replace("-", "");
                boolean previousKeepScreenOn = hasKeepScreenOnFlag();
                preferences.edit()
                        .putBoolean(ACTIVE, true)
                        .putString(SESSION_ID, sessionId)
                        .putString(STARTED_AT, utcNow())
                        .putString(REQUEST_ID, context.getString("requestId"))
                        .putString(PATCH_HASH, context.getString("patchHash"))
                        .putString(BASE_SHA, context.getString("baseSha"))
                        .putString(COMMIT_SHA, context.getString("commitSha"))
                        .putString(PREVIEW_VERSION, context.getString("previewVersion"))
                        .putInt(APP_VERSION_CODE, BuildConfig.VERSION_CODE)
                        .putBoolean(PREVIOUS_KEEP_SCREEN_ON, previousKeepScreenOn)
                        .apply();
                setKeepScreenOn(true);
                return sessionSnapshot(false).toString();
            } catch (Exception ignored) {
                return error("preview_context_invalid").toString();
            }
        }
    }

    @JavascriptInterface
    public String endSession(String reportJson) {
        synchronized (this) {
            if (!isActive()) {
                return error("no_active_session").toString();
            }
            if (reportJson == null || reportJson.length() > MAX_REPORT_CHARS) {
                return error("report_too_large").toString();
            }
            try {
                JSONObject report = sanitizeReport(new JSONObject(reportJson));
                boolean previousKeepScreenOn =
                        preferences.getBoolean(PREVIOUS_KEEP_SCREEN_ON, false);
                preferences.edit()
                        .putString(LAST_REPORT, report.toString())
                        .putBoolean(ACTIVE, false)
                        .remove(SESSION_ID)
                        .remove(STARTED_AT)
                        .remove(REQUEST_ID)
                        .remove(PATCH_HASH)
                        .remove(BASE_SHA)
                        .remove(COMMIT_SHA)
                        .remove(PREVIEW_VERSION)
                        .remove(APP_VERSION_CODE)
                        .remove(PREVIOUS_KEEP_SCREEN_ON)
                        .apply();
                restoreScreenState(previousKeepScreenOn);
                JSONObject result = new JSONObject();
                result.put("ok", true);
                result.put("sessionId", report.getString("sessionId"));
                result.put("overallStatus", report.getString("overallStatus"));
                return result.toString();
            } catch (Exception ignored) {
                return error("report_invalid").toString();
            }
        }
    }

    @JavascriptInterface
    public boolean openReportIssue() {
        final String reportText = preferences.getString(LAST_REPORT, "");
        if (!nonEmpty(reportText)) {
            return false;
        }
        try {
            JSONObject report = new JSONObject(reportText);
            String body = renderIssueBody(report);
            if (body.length() > MAX_ISSUE_BODY_CHARS) {
                return false;
            }
            String title = "KGG Tab S9 Testbericht " + safeText(
                    report.optString("sessionId", "unbekannt"), "unbekannt", 80
            );
            Uri uri = new Uri.Builder()
                    .scheme("https")
                    .authority("github.com")
                    .encodedPath("/Kayus24/kgg-device-test-reports/issues/new")
                    .appendQueryParameter("title", title)
                    .appendQueryParameter("body", body)
                    .build();
            if (!REPORT_ISSUE_URL.equals(
                    uri.getScheme() + "://" + uri.getAuthority() + uri.getPath())) {
                return false;
            }
            return launchIssue(uri);
        } catch (Exception ignored) {
            return false;
        }
    }

    private static Map<String, String> createNoteCodes() {
        Map<String, String> values = new HashMap<>();
        values.put("admin-portrait", "layout_portrait");
        values.put("admin-landscape", "layout_landscape");
        values.put("admin-split-screen", "layout_split_screen");
        values.put("admin-package-button", "package_button");
        values.put("admin-touch-dialog-save", "touch_dialog_save");
        values.put("admin-seven-exercises", "synthetic_exercise_set_7");
        values.put("admin-reorder-save-reload", "reorder_persistence");
        values.put("patient-first-start", "patient_first_start");
        values.put("patient-add-plan", "plan_add");
        values.put("patient-replace-cancel", "plan_replace_cancel");
        values.put("patient-switch-plan", "plan_switch");
        values.put("patient-rename", "plan_rename");
        values.put("patient-values-reload", "values_reload");
        values.put("patient-offline-restore", "offline_restore");
        values.put("qr-oppo-display", "oppo_display_only");
        values.put("qr-scan-7", "synthetic_kgg_plan_7");
        values.put("qr-scan-12", "synthetic_kgg_plan_12");
        values.put("qr-scan-20", "synthetic_kgg_plan_20");
        values.put("qr-angle-distance", "camera_angle_distance");
        values.put("qr-weak-photo-fallback", "weak_image_photo_fallback");
        values.put("qr-camera-stop", "camera_stream_cleanup");
        return Collections.unmodifiableMap(values);
    }

    private JSONObject buildContext() throws JSONException {
        JSONObject context = new JSONObject();
        String requestId = BuildConfig.KGG_PREVIEW_REQUEST_ID;
        String patchHash = BuildConfig.KGG_PREVIEW_PATCH_HASH;
        String baseSha = BuildConfig.KGG_PREVIEW_BASE_SHA;
        String commitSha = BuildConfig.KGG_PREVIEW_COMMIT_SHA;
        if (!requestId.matches("[a-z0-9][a-z0-9-]{5,63}")) {
            throw new IllegalStateException("request_id");
        }
        if (!baseSha.matches("[0-9a-f]{40}")
                || !commitSha.matches("[0-9a-f]{40}")
                || !patchHash.matches("[0-9a-f]{64}")) {
            throw new IllegalStateException("context_hash");
        }
        context.put("requestId", requestId);
        context.put("patchHash", patchHash);
        context.put("baseSha", baseSha);
        context.put("commitSha", commitSha);
        context.put("previewVersion", safeText(
                BuildConfig.VERSION_NAME, "unknown-preview", 80
        ));
        return context;
    }

    private JSONObject sessionSnapshot(boolean resumed) throws JSONException {
        JSONObject result = new JSONObject();
        result.put("ok", true);
        result.put("active", true);
        result.put("resumed", resumed);
        result.put("sessionId", preferences.getString(SESSION_ID, ""));
        result.put("startedAt", preferences.getString(STARTED_AT, ""));
        result.put("previewRequestId", preferences.getString(REQUEST_ID, ""));
        result.put("previewVersion", preferences.getString(PREVIEW_VERSION, ""));
        result.put("contextPinned", true);
        return result;
    }

    private JSONObject sanitizeReport(JSONObject input) throws JSONException {
        if (!input.has("tests") || input.optJSONArray("tests") == null) {
            throw new IllegalArgumentException("tests");
        }
        String sessionId = preferences.getString(SESSION_ID, "");
        String startedAt = preferences.getString(STARTED_AT, "");
        JSONArray supplied = input.optJSONArray("tests");
        Map<String, JSONObject> byId = new HashMap<>();
        for (int index = 0; index < supplied.length(); index++) {
            JSONObject candidate = supplied.optJSONObject(index);
            if (candidate == null) {
                continue;
            }
            String testId = candidate.optString("testId", "");
            if (!NOTE_CODES.containsKey(testId) || byId.containsKey(testId)) {
                continue;
            }
            byId.put(testId, candidate);
        }

        JSONArray tests = new JSONArray();
        boolean hasFailure = false;
        boolean hasBlock = false;
        for (String testId : TEST_IDS) {
            JSONObject candidate = byId.get(testId);
            String status = candidate == null
                    ? "blocked"
                    : candidate.optString("status", "blocked");
            if (!isStatus(status)) {
                status = "blocked";
            }
            if ("skipped".equals(status) && !OPTIONAL_TESTS.contains(testId)) {
                status = "blocked";
            }
            long duration = candidate == null
                    ? 0L
                    : candidate.optLong("durationMs", 0L);
            duration = Math.max(0L, Math.min(MAX_TEST_DURATION_MS, duration));
            JSONObject clean = new JSONObject();
            clean.put("testId", testId);
            clean.put("status", status);
            clean.put("durationMs", duration);
            clean.put(
                    "noteCode",
                    candidate == null ? NOT_EXECUTED_NOTE_CODE : NOTE_CODES.get(testId)
            );
            tests.put(clean);
            hasFailure |= "failed".equals(status);
            hasBlock |= "blocked".equals(status);
        }

        JSONObject context = new JSONObject();
        context.put("kind", "kgg_device_test_report");
        context.put("schemaVersion", REPORT_SCHEMA_VERSION);
        context.put("sessionId", sessionId);
        context.put("previewRequestId", preferences.getString(REQUEST_ID, ""));
        context.put("commitSha", preferences.getString(COMMIT_SHA, ""));
        context.put("baseSha", preferences.getString(BASE_SHA, ""));
        context.put("patchHash", preferences.getString(PATCH_HASH, ""));
        context.put("appVersion", safeText(
                preferences.getString(PREVIEW_VERSION, BuildConfig.VERSION_NAME),
                "unknown", 80
        ));
        context.put(
                "appVersionCode",
                preferences.getInt(APP_VERSION_CODE, BuildConfig.VERSION_CODE)
        );
        context.put("device", deviceInfo());
        context.put("startedAt", startedAt);
        context.put("endedAt", utcNow());
        context.put("tests", tests);
        context.put("overallStatus", hasFailure ? "failed" : hasBlock ? "blocked" : "passed");
        context.put("syntheticOnly", true);
        return context;
    }

    private JSONObject deviceInfo() throws JSONException {
        JSONObject info = new JSONObject();
        info.put("model", safeText(Build.MODEL, "unknown", 80));
        info.put("androidVersion", safeText(Build.VERSION.RELEASE, "unknown", 40));
        info.put("webViewVersion", webViewVersion());
        JSONObject screen = new JSONObject();
        int orientation = activity.getResources().getConfiguration().orientation;
        screen.put(
                "orientation",
                orientation == Configuration.ORIENTATION_LANDSCAPE
                        ? "landscape"
                        : orientation == Configuration.ORIENTATION_PORTRAIT
                        ? "portrait"
                        : "unknown"
        );
        Point size = screenSize();
        screen.put("width", size.x);
        screen.put("height", size.y);
        info.put("screen", screen);
        return info;
    }

    private String webViewVersion() {
        try {
            PackageInfo packageInfo = WebView.getCurrentWebViewPackage();
            return safeText(
                    packageInfo == null ? "" : packageInfo.versionName,
                    "unknown",
                    80
            );
        } catch (Exception ignored) {
            return "unknown";
        }
    }

    private Point screenSize() {
        try {
            WindowManager manager =
                    (WindowManager) activity.getSystemService(Context.WINDOW_SERVICE);
            Display display = manager == null ? null : manager.getDefaultDisplay();
            Point size = new Point();
            if (display != null) {
                display.getRealSize(size);
            }
            return size;
        } catch (Exception ignored) {
            return new Point(0, 0);
        }
    }

    private String renderIssueBody(JSONObject report) throws JSONException {
        JSONObject device = report.optJSONObject("device");
        JSONObject screen = device == null ? null : device.optJSONObject("screen");
        StringBuilder body = new StringBuilder();
        body.append("KGG device test report\n\n");
        body.append("kind: ").append(safeText(report.optString("kind"), "unknown", 80)).append('\n');
        body.append("schemaVersion: ").append(report.optInt("schemaVersion", 0)).append('\n');
        body.append("sessionId: ").append(safeText(report.optString("sessionId"), "unknown", 80)).append('\n');
        body.append("previewRequestId: ").append(safeText(report.optString("previewRequestId"), "unknown", 80)).append('\n');
        body.append("commitSha: ").append(safeText(report.optString("commitSha"), "unknown", 80)).append('\n');
        body.append("baseSha: ").append(safeText(report.optString("baseSha"), "unknown", 80)).append('\n');
        body.append("patchHash: ").append(safeText(report.optString("patchHash"), "unknown", 90)).append('\n');
        body.append("appVersion: ").append(safeText(report.optString("appVersion"), "unknown", 80)).append('\n');
        body.append("appVersionCode: ").append(report.optInt("appVersionCode", 0)).append('\n');
        body.append("model: ").append(safeText(device == null ? "" : device.optString("model"), "unknown", 80)).append('\n');
        body.append("androidVersion: ").append(safeText(device == null ? "" : device.optString("androidVersion"), "unknown", 40)).append('\n');
        body.append("webViewVersion: ").append(safeText(device == null ? "" : device.optString("webViewVersion"), "unknown", 80)).append('\n');
        body.append("screen: ").append(screen == null ? 0 : screen.optInt("width", 0))
                .append("x").append(screen == null ? 0 : screen.optInt("height", 0))
                .append(" / ").append(safeText(screen == null ? "" : screen.optString("orientation"), "unknown", 20)).append('\n');
        body.append("startedAt: ").append(safeText(report.optString("startedAt"), "unknown", 40)).append('\n');
        body.append("endedAt: ").append(safeText(report.optString("endedAt"), "unknown", 40)).append('\n');
        body.append("overallStatus: ").append(safeText(report.optString("overallStatus"), "unknown", 20)).append('\n');
        body.append("syntheticOnly: true\n\n");
        body.append("testCases:\n");
        JSONArray tests = report.optJSONArray("tests");
        if (tests != null) {
            for (int index = 0; index < tests.length(); index++) {
                JSONObject test = tests.optJSONObject(index);
                if (test == null) {
                    continue;
                }
                body.append("- ")
                        .append(safeText(test.optString("testId"), "unknown", 80))
                        .append(" | ")
                        .append(safeText(test.optString("status"), "blocked", 20))
                        .append(" | durationMs=")
                        .append(Math.max(0L, Math.min(MAX_TEST_DURATION_MS, test.optLong("durationMs", 0L))))
                        .append(" | noteCode=")
                        .append(safeText(test.optString("noteCode"), NOT_EXECUTED_NOTE_CODE, 80))
                        .append('\n');
            }
        }
        return body.toString();
    }

    private boolean launchIssue(Uri uri) throws InterruptedException {
        AtomicBoolean launched = new AtomicBoolean(false);
        Runnable action = () -> {
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                if (intent.resolveActivity(activity.getPackageManager()) == null) {
                    return;
                }
                activity.startActivity(intent);
                launched.set(true);
            } catch (Exception ignored) {
                Toast.makeText(activity, "Bericht konnte nicht geöffnet werden", Toast.LENGTH_SHORT).show();
            }
        };
        if (Looper.myLooper() == Looper.getMainLooper()) {
            action.run();
            return launched.get();
        }
        CountDownLatch latch = new CountDownLatch(1);
        activity.runOnUiThread(() -> {
            try {
                action.run();
            } finally {
                latch.countDown();
            }
        });
        latch.await(2, TimeUnit.SECONDS);
        return launched.get();
    }

    private boolean isActive() {
        return preferences.getBoolean(ACTIVE, false);
    }

    private boolean hasKeepScreenOnFlag() {
        Window window = activity.getWindow();
        return window != null
                && (window.getAttributes().flags & WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) != 0;
    }

    private void setKeepScreenOn(boolean enabled) {
        Runnable action = () -> {
            Window window = activity.getWindow();
            if (window == null) {
                return;
            }
            if (enabled) {
                window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            } else {
                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            }
        };
        if (Looper.myLooper() == Looper.getMainLooper()) {
            action.run();
        } else {
            activity.runOnUiThread(action);
        }
    }

    private void restoreScreenState(boolean previousKeepScreenOn) {
        setKeepScreenOn(previousKeepScreenOn);
    }

    private static boolean isStatus(String status) {
        return "passed".equals(status)
                || "failed".equals(status)
                || "blocked".equals(status)
                || "skipped".equals(status);
    }

    private static String safeText(String value, String fallback, int limit) {
        if (value == null) {
            return fallback;
        }
        String clean = value
                .replaceAll("[\\p{Cntrl}]", " ")
                .replaceAll("[^A-Za-z0-9 ._:/+\\-]", "_")
                .trim();
        if (clean.isEmpty()) {
            return fallback;
        }
        if (clean.length() > limit) {
            clean = clean.substring(0, limit);
        }
        return clean;
    }

    private static boolean nonEmpty(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static String utcNow() {
        return Instant.now().toString();
    }

    private static JSONObject error(String code) {
        JSONObject result = new JSONObject();
        try {
            result.put("ok", false);
            result.put("error", code);
        } catch (JSONException ignored) {
        }
        return result;
    }
}
