package de.kgg.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Environment;
import android.webkit.JavascriptInterface;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public class KggSyncBridge {
    private static final String PREFS = "kgg_sync_prefs";
    private static final String FOLLOW_CONFIG = "follow_config_json";
    private static final String SYNC_FILE_NAME = "kgg_cross_data_safe_sync_v2.json";
    private static final String LEGACY_SYNC_FILE_NAME = "kgg_sync_exercise_bank_v1.json";
    private static final String PUBLIC_SYNC_DIR_NAME = "KGG Sync";
    private static final String ROOMS_DIR_NAME = "rooms";
    private static final String DEVICES_DIR_NAME = "devices";
    private static final String DEFAULT_ROOM_ID = "default";
    private static final int MAX_PEER_FILES = 80;

    private final Context appContext;

    public KggSyncBridge(Context context) {
        this.appContext = context.getApplicationContext();
    }

    @JavascriptInterface
    public String getStatus() {
        try {
            JSONObject config = followConfigJson();
            String roomId = syncRoomId(config);
            JSONObject mesh = meshSyncDocument(roomId, config);
            JSONArray peers = mesh.optJSONArray("peers");
            File activeFile = syncFile();
            File sharedRoot = sharedSyncRoot();
            File privateRoot = privateSyncRoot();
            boolean sharedWritable = canUseSharedSyncFolder(true);
            statusEnsureRoom(config, roomId);

            JSONObject status = new JSONObject();
            status.put("available", true);
            status.put("platform", "android");
            status.put("syncFile", SYNC_FILE_NAME);
            status.put("syncRoomId", roomId);
            status.put("syncPath", activeFile.getAbsolutePath());
            status.put("sharedSyncPath", sharedRoot.getAbsolutePath());
            status.put("privateSyncPath", privateRoot.getAbsolutePath());
            status.put("writePath", (sharedWritable ? sharedRoot : privateRoot).getAbsolutePath());
            status.put("usingSharedFolder", samePath(activeFile, sharedSyncFile()));
            status.put("writeUsesSharedFolder", sharedWritable);
            status.put("sharedWritable", sharedWritable);
            status.put("hasSyncFile", activeFile.exists());
            status.put("meshAvailable", true);
            status.put("peerCount", peers != null ? peers.length() : 0);
            status.put("followConfig", config);
            return status.toString();
        } catch (Exception err) {
            return "{\"available\":true,\"platform\":\"android\",\"error\":\"status_failed\"}";
        }
    }

    @JavascriptInterface
    public String readSyncJson() {
        try {
            JSONObject config = followConfigJson();
            String roomId = syncRoomId(config);
            JSONObject mesh = meshSyncDocument(roomId, config);
            JSONArray peers = mesh.optJSONArray("peers");
            if (peers != null && peers.length() > 0) {
                return mesh.toString();
            }

            File file = syncFile();
            if (!file.exists()) {
                File legacyFile = legacySyncFile();
                if (legacyFile.exists()) {
                    file = legacyFile;
                }
            }
            if (!file.exists()) {
                return emptySyncDocument(roomId).toString();
            }
            return new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
        } catch (Exception err) {
            return emptySyncDocument(DEFAULT_ROOM_ID).toString();
        }
    }

    @JavascriptInterface
    public String listPeerSyncJson() {
        try {
            JSONObject config = followConfigJson();
            return meshSyncDocument(syncRoomId(config), config).toString();
        } catch (Exception err) {
            return "{\"kind\":\"kgg_cross_data_safe_sync_mesh\",\"version\":1,\"peers\":[]}";
        }
    }

    @JavascriptInterface
    public boolean writeSyncJson(String json) {
        try {
            if (!isSafeExerciseBankSyncPayload(json)) {
                return false;
            }
            JSONObject parsed = new JSONObject(json);
            JSONObject config = followConfigJson();
            String roomId = syncRoomIdFromDocument(parsed, config);
            JSONObject origin = parsed.optJSONObject("origin");
            if (origin == null) {
                origin = new JSONObject();
            }
            String deviceId = origin.optString("deviceId", "");
            if (deviceId.trim().isEmpty()) {
                deviceId = config.optString("therapistId", "");
            }
            if (deviceId.trim().isEmpty()) {
                deviceId = "android_" + Integer.toHexString(appContext.getPackageName().hashCode());
            }
            origin.put("deviceId", deviceId);
            origin.put("roomId", roomId);
            parsed.put("origin", origin);
            parsed.put("roomId", roomId);

            String payload = parsed.toString(2);
            File targetFile = preferredWritePeerFile(roomId, deviceId);
            if (writeSyncFile(targetFile, payload)) {
                return true;
            }
            File fallbackFile = privatePeerFile(roomId, deviceId);
            return !samePath(targetFile, fallbackFile) && writeSyncFile(fallbackFile, payload);
        } catch (Exception err) {
            return false;
        }
    }

    @JavascriptInterface
    public String readFollowConfig() {
        SharedPreferences prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return prefs.getString(FOLLOW_CONFIG, "{\"therapistId\":\"\",\"syncRoomId\":\"\",\"followedTherapists\":[]}");
    }

    @JavascriptInterface
    public boolean writeFollowConfig(String json) {
        try {
            JSONObject parsed = new JSONObject(json);
            SharedPreferences prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            prefs.edit().putString(FOLLOW_CONFIG, parsed.toString()).apply();
            return true;
        } catch (Exception err) {
            return false;
        }
    }

    private void statusEnsureRoom(JSONObject config, String roomId) {
        try {
            if (config.optString("syncRoomId", "").trim().isEmpty()) {
                config.put("syncRoomId", roomId);
                writeFollowConfig(config.toString());
            }
        } catch (Exception ignored) {
        }
    }

    private JSONObject followConfigJson() {
        try {
            return new JSONObject(readFollowConfig());
        } catch (Exception err) {
            return new JSONObject();
        }
    }

    private String syncRoomId(JSONObject config) {
        String roomId = config.optString("syncRoomId", "").trim();
        if (roomId.isEmpty()) {
            roomId = DEFAULT_ROOM_ID;
        }
        return safeFilePart(roomId);
    }

    private String syncRoomIdFromDocument(JSONObject doc, JSONObject config) {
        String roomId = doc.optString("roomId", "").trim();
        JSONObject origin = doc.optJSONObject("origin");
        if (roomId.isEmpty() && origin != null) {
            roomId = origin.optString("roomId", "").trim();
        }
        if (roomId.isEmpty()) {
            roomId = syncRoomId(config);
        }
        return safeFilePart(roomId);
    }

    private JSONObject meshSyncDocument(String roomId, JSONObject config) {
        JSONObject mesh = new JSONObject();
        try {
            JSONArray peers = collectPeerSyncDocuments(roomId);
            mesh.put("kind", "kgg_cross_data_safe_sync_mesh");
            mesh.put("version", 1);
            mesh.put("roomId", roomId);
            mesh.put("generatedAt", new java.util.Date().toInstant().toString());
            mesh.put("peers", peers);
            mesh.put("followConfig", config);
        } catch (Exception ignored) {
        }
        return mesh;
    }

    private JSONArray collectPeerSyncDocuments(String roomId) {
        LinkedHashMap<String, JSONObject> docs = new LinkedHashMap<>();
        collectPeerDocsFromDir(docs, sharedPeerDir(roomId));
        collectPeerDocsFromDir(docs, privatePeerDir(roomId));
        collectPeerDoc(docs, sharedSyncFile());
        collectPeerDoc(docs, privateSyncFile());
        collectPeerDoc(docs, legacySyncFile());
        JSONArray peers = new JSONArray();
        for (Map.Entry<String, JSONObject> entry : docs.entrySet()) {
            peers.put(entry.getValue());
        }
        return peers;
    }

    private void collectPeerDocsFromDir(LinkedHashMap<String, JSONObject> docs, File dir) {
        try {
            if (!dir.exists() || !dir.isDirectory()) {
                return;
            }
            File[] files = dir.listFiles((file) -> file.isFile() && file.getName().endsWith(".json"));
            if (files == null) {
                return;
            }
            int count = 0;
            for (File file : files) {
                collectPeerDoc(docs, file);
                count += 1;
                if (count >= MAX_PEER_FILES) {
                    break;
                }
            }
        } catch (Exception ignored) {
        }
    }

    private void collectPeerDoc(LinkedHashMap<String, JSONObject> docs, File file) {
        try {
            if (!file.exists() || !file.isFile()) {
                return;
            }
            String text = new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
            if (!isSafeExerciseBankSyncPayload(text)) {
                return;
            }
            JSONObject doc = new JSONObject(text);
            if (!"kgg_cross_data_safe_sync".equals(doc.optString("kind"))) {
                return;
            }
            JSONObject origin = doc.optJSONObject("origin");
            String key = peerKey(doc, file);
            JSONObject existing = docs.get(key);
            if (existing == null || syncTimestamp(doc.optString("exportedAt")) >= syncTimestamp(existing.optString("exportedAt"))) {
                docs.put(key, doc);
            }
        } catch (Exception ignored) {
        }
    }

    private String peerKey(JSONObject doc, File file) {
        JSONObject origin = doc.optJSONObject("origin");
        if (origin != null) {
            String deviceId = origin.optString("deviceId", "").trim();
            if (!deviceId.isEmpty()) {
                return "device:" + deviceId;
            }
            String therapistId = origin.optString("therapistId", "").trim();
            if (!therapistId.isEmpty()) {
                return "therapist:" + therapistId;
            }
        }
        return "file:" + file.getName();
    }

    private long syncTimestamp(String value) {
        try {
            java.time.Instant instant = java.time.Instant.parse(value);
            return instant.toEpochMilli();
        } catch (Exception err) {
            return 0L;
        }
    }

    private File syncFile() {
        File existing = newestExistingSyncFile();
        return existing != null ? existing : preferredWriteSyncFile();
    }

    private File preferredWriteSyncFile() {
        return canUseSharedSyncFolder(true) ? sharedSyncFile() : privateSyncFile();
    }

    private File preferredWritePeerFile(String roomId, String deviceId) {
        return canUseSharedSyncFolder(true) ? sharedPeerFile(roomId, deviceId) : privatePeerFile(roomId, deviceId);
    }

    private File newestExistingSyncFile() {
        File newest = null;
        File[] candidates = new File[]{sharedSyncFile(), privateSyncFile(), legacySyncFile()};
        for (File candidate : candidates) {
            if (candidate.exists() && candidate.isFile()) {
                if (newest == null || candidate.lastModified() > newest.lastModified()) {
                    newest = candidate;
                }
            }
        }
        return newest;
    }

    private File sharedSyncRoot() {
        File documentsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS);
        return new File(documentsDir, PUBLIC_SYNC_DIR_NAME);
    }

    private File privateSyncRoot() {
        return new File(appContext.getFilesDir(), "sync");
    }

    private File sharedSyncFile() {
        return new File(sharedSyncRoot(), SYNC_FILE_NAME);
    }

    private File privateSyncFile() {
        return new File(privateSyncRoot(), SYNC_FILE_NAME);
    }

    private File sharedPeerDir(String roomId) {
        return new File(new File(new File(sharedSyncRoot(), ROOMS_DIR_NAME), safeFilePart(roomId)), DEVICES_DIR_NAME);
    }

    private File privatePeerDir(String roomId) {
        return new File(new File(new File(privateSyncRoot(), ROOMS_DIR_NAME), safeFilePart(roomId)), DEVICES_DIR_NAME);
    }

    private File sharedPeerFile(String roomId, String deviceId) {
        return new File(sharedPeerDir(roomId), safeFilePart(deviceId) + ".json");
    }

    private File privatePeerFile(String roomId, String deviceId) {
        return new File(privatePeerDir(roomId), safeFilePart(deviceId) + ".json");
    }

    private boolean canUseSharedSyncFolder(boolean create) {
        try {
            if (!Environment.MEDIA_MOUNTED.equals(Environment.getExternalStorageState())) {
                return false;
            }
            File root = sharedSyncRoot();
            if (!root.exists()) {
                if (!create) {
                    return false;
                }
                if (!root.mkdirs() && !root.exists()) {
                    return false;
                }
            }
            return root.isDirectory() && root.canRead() && root.canWrite();
        } catch (Exception err) {
            return false;
        }
    }

    private boolean writeSyncFile(File file, String payload) {
        try {
            File parent = file.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs() && !parent.exists()) {
                return false;
            }
            File tempFile = new File(parent != null ? parent : appContext.getCacheDir(), file.getName() + ".tmp");
            Files.write(tempFile.toPath(), payload.getBytes(StandardCharsets.UTF_8));
            if (file.exists() && !file.delete()) {
                tempFile.delete();
                return false;
            }
            if (!tempFile.renameTo(file)) {
                tempFile.delete();
                return false;
            }
            return true;
        } catch (Exception err) {
            return false;
        }
    }

    private boolean samePath(File left, File right) {
        try {
            return left.getCanonicalPath().equals(right.getCanonicalPath());
        } catch (Exception err) {
            return left.getAbsolutePath().equals(right.getAbsolutePath());
        }
    }

    private String safeFilePart(String value) {
        String cleaned = String.valueOf(value == null ? "" : value)
                .replaceAll("[^A-Za-z0-9._-]", "_");
        if (cleaned.isEmpty()) {
            cleaned = DEFAULT_ROOM_ID;
        }
        return cleaned.length() > 96 ? cleaned.substring(0, 96) : cleaned;
    }

    private JSONObject emptySyncDocument(String roomId) {
        JSONObject doc = new JSONObject();
        try {
            doc.put("kind", "kgg_cross_data_safe_sync");
            doc.put("version", 2);
            doc.put("roomId", roomId);
            doc.put("schema", "exercise-bank-packages-v2");
            JSONObject privacy = new JSONObject();
            privacy.put("patients", false);
            privacy.put("secrets", false);
            privacy.put("debugPayloads", false);
            privacy.put("rawData", false);
            doc.put("privacy", privacy);
            doc.put("scopes", new JSONArray().put("exerciseBank").put("packages"));
            doc.put("exerciseBank", new JSONArray());
            doc.put("packages", new JSONArray());
            JSONObject tombstones = new JSONObject();
            tombstones.put("exerciseBank", new JSONArray());
            doc.put("tombstones", tombstones);
            doc.put("exportedAt", "");
        } catch (Exception ignored) {
        }
        return doc;
    }

    private File legacySyncFile() {
        return new File(privateSyncRoot(), LEGACY_SYNC_FILE_NAME);
    }

    private boolean isSafeExerciseBankSyncPayload(String json) {
        if (json == null || json.length() > 8_000_000) {
            return false;
        }
        String lower = json.toLowerCase(Locale.ROOT);
        return !lower.contains("api_key")
                && !lower.contains("apikey")
                && !lower.contains("gemini")
                && !lower.contains("patientname")
                && !lower.contains("patient_name")
                && !lower.contains("qrraw")
                && !lower.contains("rawpayload")
                && !lower.contains("base64payload")
                && !lower.contains("access_token")
                && !lower.contains("refresh_token");
    }
}

