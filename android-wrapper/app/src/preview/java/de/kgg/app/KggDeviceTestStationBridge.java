package de.kgg.app;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.res.Configuration;
import android.graphics.Point;
import android.net.Uri;
import android.os.Build;
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
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/** Preview-only native boundary for the v404 dual-device QR test station. */
public final class KggDeviceTestStationBridge {
    private static final String PREFS = "kgg_dual_device_test_station_v2";
    private static final String ACTIVE = "active";
    private static final String SESSION_ID = "session_id";
    private static final String STARTED_AT = "started_at";
    private static final String PREVIOUS_KEEP_SCREEN_ON = "previous_keep_screen_on";
    private static final String LAST_REPORT = "last_report";
    private static final String REPORT_ISSUE_URL =
            "https://github.com/Kayus24/kgg-device-test-reports/issues/new";
    private static final int REPORT_SCHEMA_VERSION = 2;
    private static final int MAX_REPORT_CHARS = 32_000;
    private static final int MAX_ISSUE_BODY_CHARS = 14_000;
    private static final long MAX_TEST_DURATION_MS = 24L * 60L * 60L * 1000L;

    private static final String[] ADMIN_TEST_IDS = {
            "admin-portrait",
            "admin-landscape",
            "admin-split-screen",
            "admin-package-button",
            "admin-touch-dialog-save",
            "admin-seven-exercises",
            "admin-reorder-save-reload",
    };
    private static final String[] QUICK_FIXTURE_IDS = {
            "h2-1-baseline",
            "h2-7-legacy",
            "h3-7-normal",
            "h3-12-normal",
            "h3-20-normal",
            "h3-20-far-angle",
    };
    private static final String[] FULL_FIXTURE_IDS = {
            "h2-1-baseline",
            "h2-7-legacy",
            "h2-12-diagnostic",
            "h2-20-diagnostic",
            "h3-7-normal",
            "h3-12-normal",
            "h3-20-normal",
            "h3-20-far-angle",
            "h3-20-low-contrast",
            "h3-20-photo",
    };
    private static final Map<String, String> NOTE_CODES = noteCodes();
    private static final Map<String, Integer> FIXTURE_COUNTS = fixtureCounts();
    private static final Map<String, String> FIXTURE_FORMATS = fixtureFormats();
    private static final Map<String, String> FIXTURE_VARIANTS = fixtureVariants();
    private static final Set<String> OPTIONAL_TESTS = Collections.unmodifiableSet(
            new HashSet<>(Arrays.asList(
                    "display-h2-12-diagnostic",
                    "display-h2-20-diagnostic"
            ))
    );

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
            return "{\"class\":\"android-tablet\",\"model\":\"unknown\","
                    + "\"androidVersion\":\"unknown\",\"runtime\":\"unknown\","
                    + "\"screen\":{\"width\":0,\"height\":0,\"orientation\":\"unknown\"},"
                    + "\"wakeLock\":\"unknown\"}";
        }
    }

    @JavascriptInterface
    public String beginSession() {
        synchronized (this) {
            try {
                JSONObject context = buildContext();
                String expectedSession = context.getString("sessionId");
                if (isActive() && expectedSession.equals(preferences.getString(SESSION_ID, ""))) {
                    setKeepScreenOn(true);
                    return sessionSnapshot(true, context).toString();
                }
                if (isActive()) {
                    restoreScreenState(preferences.getBoolean(PREVIOUS_KEEP_SCREEN_ON, false));
                }
                boolean previousKeepScreenOn = hasKeepScreenOnFlag();
                preferences.edit()
                        .putBoolean(ACTIVE, true)
                        .putString(SESSION_ID, expectedSession)
                        .putString(STARTED_AT, utcNow())
                        .putBoolean(PREVIOUS_KEEP_SCREEN_ON, previousKeepScreenOn)
                        .apply();
                setKeepScreenOn(true);
                return sessionSnapshot(false, context).toString();
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
                        .remove(PREVIOUS_KEEP_SCREEN_ON)
                        .apply();
                restoreScreenState(previousKeepScreenOn);
                return new JSONObject()
                        .put("ok", true)
                        .put("sessionId", report.getString("sessionId"))
                        .put("overallStatus", report.getString("overallStatus"))
                        .toString();
            } catch (Exception ignored) {
                return error("report_invalid").toString();
            }
        }
    }

    @JavascriptInterface
    public boolean openReportIssue() {
        String reportText = preferences.getString(LAST_REPORT, "");
        if (!nonEmpty(reportText)) {
            return false;
        }
        try {
            JSONObject report = new JSONObject(reportText);
            String body = "KGG device test report\n\n```json\n"
                    + report.toString(2) + "\n```";
            if (body.length() > MAX_ISSUE_BODY_CHARS) {
                return false;
            }
            String title = "KGG display Testbericht "
                    + safeText(report.optString("sessionId"), "unknown", 80);
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

    private JSONObject buildContext() throws JSONException {
        String requestId = BuildConfig.KGG_PREVIEW_REQUEST_ID;
        String patchHash = BuildConfig.KGG_PREVIEW_PATCH_HASH;
        String sourceSha = BuildConfig.KGG_PREVIEW_COMMIT_SHA;
        String sessionId = BuildConfig.KGG_DEVICE_TEST_SESSION_ID;
        String jobHash = BuildConfig.KGG_DEVICE_TEST_JOB_HASH;
        String jobUrl = BuildConfig.KGG_DEVICE_TEST_JOB_URL;
        String patientPwaUrl = BuildConfig.KGG_PATIENT_PWA_URL;
        String profile = BuildConfig.KGG_DEVICE_TEST_PROFILE;
        if (!requestId.matches("[a-z0-9][a-z0-9-]{5,63}")
                || !patchHash.matches("[0-9a-f]{64}")
                || !sourceSha.matches("[0-9a-f]{40}")
                || !sessionId.matches("kgg-test-[0-9a-f]{32}")
                || !jobHash.matches("[0-9a-f]{64}")
                || !("quick".equals(profile) || "full".equals(profile))
                || !allowedHttps(jobUrl, "raw.githubusercontent.com")
                || !allowedHttps(patientPwaUrl, "kayus24.github.io")) {
            throw new IllegalStateException("context");
        }
        return new JSONObject()
                .put("requestId", requestId)
                .put("patchHash", patchHash)
                .put("sourceSha", sourceSha)
                .put("sessionId", sessionId)
                .put("jobHash", jobHash)
                .put("jobUrl", jobUrl)
                .put("patientPwaUrl", patientPwaUrl)
                .put("profile", profile);
    }

    private JSONObject sessionSnapshot(boolean resumed, JSONObject context)
            throws JSONException {
        return new JSONObject()
                .put("ok", true)
                .put("active", true)
                .put("resumed", resumed)
                .put("sessionId", preferences.getString(SESSION_ID, ""))
                .put("startedAt", preferences.getString(STARTED_AT, ""))
                .put("previewRequestId", context.getString("requestId"))
                .put("previewVersion", BuildConfig.VERSION_NAME)
                .put("jobHash", context.getString("jobHash"))
                .put("profile", context.getString("profile"))
                .put("contextPinned", true);
    }

    private JSONObject sanitizeReport(JSONObject input) throws JSONException {
        JSONObject context = buildContext();
        if (!"display".equals(input.optString("role"))
                || !context.getString("profile").equals(input.optString("profile"))
                || !context.getString("jobHash").equals(input.optString("jobHash"))) {
            throw new IllegalArgumentException("identity");
        }
        JSONArray tests = sanitizeTests(input.optJSONArray("tests"), context.getString("profile"));
        JSONArray fixtures = sanitizeFixtures(
                input.optJSONArray("fixtures"),
                context.getString("profile")
        );
        boolean failed = false;
        boolean blocked = false;
        for (int index = 0; index < tests.length(); index++) {
            String status = tests.getJSONObject(index).getString("status");
            failed |= "failed".equals(status);
            blocked |= "blocked".equals(status);
        }
        return new JSONObject()
                .put("kind", "kgg_device_test_report")
                .put("schemaVersion", REPORT_SCHEMA_VERSION)
                .put("sessionId", preferences.getString(SESSION_ID, ""))
                .put("role", "display")
                .put("requestId", context.getString("requestId"))
                .put("sourceSha", context.getString("sourceSha"))
                .put("patchHash", context.getString("patchHash"))
                .put("jobHash", context.getString("jobHash"))
                .put("appVersion", BuildConfig.VERSION_NAME)
                .put("device", deviceInfo())
                .put("profile", context.getString("profile"))
                .put("startedAt", preferences.getString(STARTED_AT, ""))
                .put("endedAt", utcNow())
                .put("tests", tests)
                .put("fixtures", fixtures)
                .put("telemetry", new JSONArray())
                .put("overallStatus", failed ? "failed" : blocked ? "blocked" : "passed")
                .put("syntheticOnly", true);
    }

    private JSONArray sanitizeTests(JSONArray supplied, String profile)
            throws JSONException {
        List<String> expected = expectedTestIds(profile);
        if (supplied == null || supplied.length() != expected.size()) {
            throw new IllegalArgumentException("tests");
        }
        Map<String, JSONObject> byId = new HashMap<>();
        for (int index = 0; index < supplied.length(); index++) {
            JSONObject value = supplied.optJSONObject(index);
            String testId = value == null ? "" : value.optString("testId", "");
            if (!expected.contains(testId) || byId.put(testId, value) != null) {
                throw new IllegalArgumentException("test_id");
            }
        }
        JSONArray clean = new JSONArray();
        for (String testId : expected) {
            JSONObject value = byId.get(testId);
            String status = value.optString("status", "blocked");
            if (!isStatus(status)
                    || ("skipped".equals(status) && !OPTIONAL_TESTS.contains(testId))) {
                throw new IllegalArgumentException("test_status");
            }
            long duration = Math.max(
                    0L,
                    Math.min(MAX_TEST_DURATION_MS, value.optLong("durationMs", 0L))
            );
            clean.put(new JSONObject()
                    .put("testId", testId)
                    .put("status", status)
                    .put("durationMs", duration)
                    .put("noteCode", NOTE_CODES.get(testId)));
        }
        return clean;
    }

    private JSONArray sanitizeFixtures(JSONArray supplied, String profile)
            throws JSONException {
        String[] expected = "full".equals(profile) ? FULL_FIXTURE_IDS : QUICK_FIXTURE_IDS;
        if (supplied == null || supplied.length() != expected.length) {
            throw new IllegalArgumentException("fixtures");
        }
        JSONArray clean = new JSONArray();
        for (int index = 0; index < expected.length; index++) {
            JSONObject value = supplied.optJSONObject(index);
            String fixtureId = value == null ? "" : value.optString("fixtureId", "");
            if (!expected[index].equals(fixtureId)
                    || !FIXTURE_FORMATS.get(fixtureId).equals(value.optString("format"))
                    || FIXTURE_COUNTS.get(fixtureId) != value.optInt("exerciseCount", -1)
                    || !FIXTURE_VARIANTS.get(fixtureId).equals(value.optString("displayVariant"))
                    || !value.optString("expectedFingerprint").matches("[0-9a-f]{8}")
                    || !value.optString("expectedOrderDigest").matches("[0-9a-f]{8}")) {
                throw new IllegalArgumentException("fixture_contract");
            }
            clean.put(new JSONObject()
                    .put("fixtureId", fixtureId)
                    .put("format", value.getString("format"))
                    .put("exerciseCount", value.getInt("exerciseCount"))
                    .put("required", value.optBoolean("required", false))
                    .put("displayVariant", value.getString("displayVariant"))
                    .put("importMode", safeText(value.optString("importMode"), "capture", 20))
                    .put("expectedFingerprint", value.getString("expectedFingerprint"))
                    .put("expectedOrderDigest", value.getString("expectedOrderDigest")));
        }
        return clean;
    }

    private JSONObject deviceInfo() throws JSONException {
        Point size = screenSize();
        int orientation = activity.getResources().getConfiguration().orientation;
        return new JSONObject()
                .put("class", "android-tablet")
                .put("model", safeText(Build.MODEL, "unknown", 80))
                .put("androidVersion", safeText(Build.VERSION.RELEASE, "unknown", 40))
                .put("runtime", "webview-" + webViewVersion())
                .put("screen", new JSONObject()
                        .put("width", size.x)
                        .put("height", size.y)
                        .put("orientation",
                                orientation == Configuration.ORIENTATION_LANDSCAPE
                                        ? "landscape"
                                        : orientation == Configuration.ORIENTATION_PORTRAIT
                                        ? "portrait"
                                        : "unknown"))
                .put("wakeLock", isActive() ? "active" : "released");
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
                Toast.makeText(
                        activity,
                        "Bericht konnte nicht geöffnet werden",
                        Toast.LENGTH_SHORT
                ).show();
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
                && (window.getAttributes().flags
                & WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) != 0;
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

    private static List<String> expectedTestIds(String profile) {
        List<String> values = new ArrayList<>();
        if ("full".equals(profile)) {
            values.addAll(Arrays.asList(ADMIN_TEST_IDS));
        }
        values.add("display-pairing");
        String[] fixtures = "full".equals(profile) ? FULL_FIXTURE_IDS : QUICK_FIXTURE_IDS;
        for (String fixture : fixtures) {
            values.add("display-" + fixture);
        }
        return values;
    }

    private static Map<String, String> noteCodes() {
        Map<String, String> values = new HashMap<>();
        values.put("admin-portrait", "layout_portrait");
        values.put("admin-landscape", "layout_landscape");
        values.put("admin-split-screen", "layout_split_screen");
        values.put("admin-package-button", "package_button");
        values.put("admin-touch-dialog-save", "touch_dialog_save");
        values.put("admin-seven-exercises", "synthetic_exercise_set_7");
        values.put("admin-reorder-save-reload", "reorder_persistence");
        values.put("display-pairing", "pairing_displayed");
        for (String fixture : FULL_FIXTURE_IDS) {
            values.put("display-" + fixture, "display_" + fixture.replace('-', '_'));
        }
        return Collections.unmodifiableMap(values);
    }

    private static Map<String, Integer> fixtureCounts() {
        Map<String, Integer> values = new HashMap<>();
        values.put("h2-1-baseline", 1);
        values.put("h2-7-legacy", 7);
        values.put("h2-12-diagnostic", 12);
        values.put("h2-20-diagnostic", 20);
        values.put("h3-7-normal", 7);
        values.put("h3-12-normal", 12);
        values.put("h3-20-normal", 20);
        values.put("h3-20-far-angle", 20);
        values.put("h3-20-low-contrast", 20);
        values.put("h3-20-photo", 20);
        return Collections.unmodifiableMap(values);
    }

    private static Map<String, String> fixtureFormats() {
        Map<String, String> values = new HashMap<>();
        for (String fixture : FULL_FIXTURE_IDS) {
            values.put(fixture, fixture.startsWith("h2-") ? "KGGH2" : "KGGH3");
        }
        return Collections.unmodifiableMap(values);
    }

    private static Map<String, String> fixtureVariants() {
        Map<String, String> values = new HashMap<>();
        values.put("h2-1-baseline", "normal");
        values.put("h2-7-legacy", "normal");
        values.put("h2-12-diagnostic", "normal");
        values.put("h2-20-diagnostic", "normal");
        values.put("h3-7-normal", "normal");
        values.put("h3-12-normal", "normal");
        values.put("h3-20-normal", "normal");
        values.put("h3-20-far-angle", "far-angle");
        values.put("h3-20-low-contrast", "low-contrast");
        values.put("h3-20-photo", "photo");
        return Collections.unmodifiableMap(values);
    }

    private static boolean allowedHttps(String value, String host) {
        try {
            Uri uri = Uri.parse(value);
            return "https".equals(uri.getScheme())
                    && host.equals(uri.getHost())
                    && !nonEmpty(uri.getUserInfo())
                    && !nonEmpty(uri.getFragment());
        } catch (Exception ignored) {
            return false;
        }
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
        return clean.length() > limit ? clean.substring(0, limit) : clean;
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
