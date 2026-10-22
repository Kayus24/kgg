package de.kgg.app;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Document transport only: each device owns one writable document and reads bound peers. */
final class KggDriveSyncTransport {
    static final int MAX_BYTES = 8_000_000;
    static final int MAX_MESH_BYTES = 32_000_000;
    static final int MAX_PEERS = 80;
    interface State {
        String read(String key) throws IOException;
        void write(String key, String value) throws IOException;
    }
    interface Documents {
        String read(String document) throws IOException;
        void write(String document, String payload) throws IOException;
    }
    private final State state;
    private final Documents documents;
    private volatile String runtimeError = "";
    private static final Set<String> ENVELOPE = keys("kind", "version", "schema", "scopes", "appVersion", "exportedAt", "roomId", "privacy", "origin", "exerciseBank", "packages", "tombstones", "mediaBlobs");
    private static final Set<String> EXERCISE = keys("id", "name", "aliases", "nameDe", "nameEn", "sets", "unit", "weightUnit", "loadUnit", "metricUnit", "measure", "side", "videoUrl", "videoLabel", "media", "progressionGroupId", "progressionMainId", "progressionVariants", "shared", "createdAt", "updatedAt", "syncRevision");
    private static final Set<String> STAGE = keys("id", "groupId", "name", "nameDe", "nameEn", "order", "sourceId", "sets", "unit", "weightUnit", "loadUnit", "metricUnit", "measure", "side", "videoUrl", "videoLabel", "media");
    private static final Set<String> MEDIA = keys("id", "type", "mime", "width", "height");
    private static final Set<String> IMAGE_TYPES = keys("image/jpeg", "image/png", "image/webp");

    KggDriveSyncTransport(State state, Documents documents) {
        this.state = state;
        this.documents = documents;
    }

    JSONObject status() {
        JSONObject result = new JSONObject();
        try {
            JSONObject flags = flags();
            boolean configured = configured();
            boolean pending = flags.optBoolean("pendingWrite") || flags.optBoolean("readPending");
            result.put("transport", configured ? "saf-document" : "local");
            result.put("driveConfigured", configured);
            JSONObject own = own();
            if (configured && own != null) result.put("syncRoomId", own.optString("roomId", ""));
            result.put("pending", pending);
            result.put("providerAccepted", configured && !pending && flags.optBoolean("accepted") && runtimeError.isEmpty());
            result.put("lastError", runtimeError.isEmpty() ? flags.optString("lastError", "") : runtimeError);
            result.put("peerCount", peers().length());
        } catch (Exception ignored) {
            try {
                result.put("transport", "saf-document");
                result.put("driveConfigured", true);
                result.put("pending", true);
                result.put("providerAccepted", false);
                result.put("lastError", "local_state_failed");
            } catch (Exception unused) { }
        }
        return result;
    }

    synchronized boolean configureOwn(String document, String deviceId, String roomId) {
        try {
            requireDocument(document);
            requireIdentity(deviceId);
            requireIdentity(roomId);
            String outbox = state.read("outbox");
            if (!outbox.isEmpty()) {
                JSONObject previousPayload = validate(outbox, null, null);
                if (!deviceId.equals(previousPayload.getJSONObject("origin").getString("deviceId")) || !roomId.equals(previousPayload.getString("roomId"))) {
                    // Explicit reconfiguration preserves the old room's complete pending snapshot.
                    state.write("retained_" + sha256(outbox.getBytes(StandardCharsets.UTF_8)), outbox);
                }
            }
            JSONObject own = new JSONObject().put("uri", document).put("deviceId", deviceId).put("roomId", roomId);
            JSONObject configuration = configuration();
            JSONObject previous = own();
            if (previous != null && (!deviceId.equals(previous.optString("deviceId")) || !roomId.equals(previous.optString("roomId")))) {
                configuration.put("peers", new JSONArray());
            }
            JSONObject flags = flags().put("pendingWrite", true).put("accepted", false).put("lastError", "");
            state.write("flags", flags.toString());
            // The one atomic binding commit is last. A failure leaves all previous bindings usable.
            state.write("configuration", configuration.put("own", own).put("enabled", true).toString());
            runtimeError = "";
            return true;
        } catch (Exception error) {
            fail(code(error, "configure_failed"), false);
            return false;
        }
    }

    synchronized boolean configurePeers(String[] selected, String roomId) {
        try {
            JSONObject own = requireOwn();
            if (!own.getString("roomId").equals(roomId)) throw new Invalid("room_mismatch");
            if (selected == null || selected.length == 0 || selected.length > MAX_PEERS) throw new Invalid("invalid_peer_selection");
            JSONArray bindings = new JSONArray();
            Set<String> identities = new HashSet<>();
            Set<String> uris = new HashSet<>();
            int meshBytes = meshHeader(roomId).toString().getBytes(StandardCharsets.UTF_8).length;
            for (String document : selected) {
                requireDocument(document);
                if (!uris.add(document) || document.equals(own.getString("uri"))) throw new Invalid("invalid_peer_selection");
                JSONObject payload = validate(documents.read(document), null, roomId);
                meshBytes = budgetMesh(meshBytes, payload, bindings.length());
                String deviceId = payload.getJSONObject("origin").getString("deviceId");
                if (deviceId.equals(own.getString("deviceId")) || !identities.add(deviceId)) throw new Invalid("invalid_peer_selection");
                bindings.put(new JSONObject().put("uri", document).put("deviceId", deviceId).put("roomId", roomId));
            }
            JSONObject flags = flags().put("readPending", false).put("lastError", "");
            state.write("flags", flags.toString());
            state.write("configuration", configuration().put("peers", bindings).toString());
            runtimeError = "";
            return true;
        } catch (Exception error) {
            fail(code(error, "peer_selection_failed"), true);
            return false;
        }
    }

    synchronized boolean write(String payload) {
        try {
            JSONObject own = configured() ? requireOwn() : null;
            validate(payload, own == null ? null : own.getString("deviceId"), own == null ? null : own.getString("roomId"));
            JSONObject flags = flags().put("pendingWrite", true).put("accepted", false);
            state.write("flags", flags.toString());
            state.write("outbox", payload);
            if (own == null) {
                fail("not_configured", false);
                return false;
            }
            documents.write(own.getString("uri"), payload);
            flags = flags().put("pendingWrite", false).put("accepted", true);
            if (!flags.optBoolean("readPending")) flags.put("lastError", "");
            state.write("flags", flags.toString());
            runtimeError = "";
            return true;
        } catch (Exception error) {
            fail(code(error, "write_failed"), false);
            return false;
        }
    }

    synchronized JSONObject read() {
        try {
            JSONObject own = requireOwn();
            JSONArray result = new JSONArray();
            JSONArray bindings = peers();
            int meshBytes = meshHeader(own.getString("roomId")).toString().getBytes(StandardCharsets.UTF_8).length;
            for (int i = 0; i < bindings.length(); i++) {
                JSONObject binding = bindings.getJSONObject(i);
                if (!binding.getString("roomId").equals(own.getString("roomId"))) throw new Invalid("room_mismatch");
                JSONObject peer = validate(documents.read(binding.getString("uri")), binding.getString("deviceId"), binding.getString("roomId"));
                meshBytes = budgetMesh(meshBytes, peer, result.length());
                result.put(peer);
            }
            JSONObject flags = flags().put("readPending", false);
            if (!flags.optBoolean("pendingWrite")) flags.put("lastError", "");
            state.write("flags", flags.toString());
            runtimeError = "";
            return meshHeader(own.getString("roomId")).put("peers", result);
        } catch (Exception error) {
            String code = code(error, "read_failed");
            fail(code, true);
            try { return new JSONObject().put("kind", "kgg_sync_transport_error").put("error", code); }
            catch (Exception unused) { return new JSONObject(); }
        }
    }

    synchronized String[] selectedDocuments() {
        LinkedHashSet<String> result = new LinkedHashSet<>();
        try {
            JSONObject own = own();
            if (own != null) result.add(own.getString("uri"));
            JSONArray peers = peers();
            for (int i = 0; i < peers.length(); i++) result.add(peers.getJSONObject(i).getString("uri"));
        } catch (Exception ignored) { }
        return result.toArray(new String[0]);
    }

    synchronized boolean disconnect() {
        try {
            state.write("flags", new JSONObject().put("pendingWrite", !state.read("outbox").isEmpty())
                    .put("readPending", false).put("accepted", false).put("lastError", "").toString());
            state.write("configuration", new JSONObject().put("enabled", false).put("peers", new JSONArray()).toString());
            runtimeError = "";
            return true;
        } catch (Exception error) {
            fail("local_state_failed", false);
            return false;
        }
    }

    synchronized void reportError(String code) { fail(code, true); }

    private JSONObject configuration() throws Exception {
        String value = state.read("configuration");
        return value.isEmpty() ? new JSONObject().put("enabled", false).put("peers", new JSONArray()) : new JSONObject(value);
    }
    private boolean configured() throws Exception { return configuration().optBoolean("enabled"); }
    private JSONObject own() throws Exception { return configuration().optJSONObject("own"); }
    private JSONObject requireOwn() throws Exception {
        JSONObject own = own();
        if (!configured() || own == null) throw new Invalid("not_configured");
        requireDocument(own.getString("uri"));
        requireIdentity(own.getString("deviceId"));
        requireIdentity(own.getString("roomId"));
        return own;
    }
    private JSONArray peers() throws Exception {
        return configuration().getJSONArray("peers");
    }
    private JSONObject flags() throws Exception {
        String value = state.read("flags");
        return value.isEmpty() ? new JSONObject() : new JSONObject(value);
    }
    private void fail(String code, boolean readPending) {
        runtimeError = code;
        try {
            JSONObject flags = flags().put("lastError", code).put("accepted", false);
            if (readPending) flags.put("readPending", true);
            else flags.put("pendingWrite", true);
            state.write("flags", flags.toString());
        } catch (Exception ignored) { }
    }
    private static String code(Exception error, String fallback) { return error instanceof Invalid ? error.getMessage() : fallback; }
    private static final class Invalid extends Exception { Invalid(String code) { super(code); } }
    private static Set<String> keys(String... names) { return new HashSet<>(Arrays.asList(names)); }
    private static void requireIdentity(String value) throws Invalid {
        if (value == null || !value.matches("[A-Za-z0-9._-]{1,96}")) throw new Invalid("invalid_identity");
    }
    private static void requireDocument(String value) throws Invalid {
        if (value == null || !value.startsWith("content://") || value.length() > 4096) throw new Invalid("invalid_document");
    }
    private static void allowed(JSONObject value, Set<String> allowed) throws Exception {
        Iterator<String> names = value.keys();
        while (names.hasNext()) if (!allowed.contains(names.next())) throw new Invalid("invalid_payload");
    }
    private static void scalarFields(JSONObject value, Set<String> nested) throws Exception {
        Iterator<String> names = value.keys();
        while (names.hasNext()) {
            String name = names.next();
            if (nested.contains(name)) continue;
            Object field = value.get(name);
            if (!(field instanceof String || field instanceof Number || field instanceof Boolean)) throw new Invalid("invalid_payload");
        }
    }
    private static String string(JSONObject value, String name) throws Exception {
        Object field = value.get(name);
        if (!(field instanceof String)) throw new Invalid("invalid_payload");
        return (String) field;
    }
    private static void timestamp(JSONObject value, String name) throws Exception { Instant.parse(string(value, name)); }
    private static void media(JSONArray media, Map<String, String> referenced) throws Exception {
        if (media.length() > 32) throw new Invalid("invalid_payload");
        for (int i = 0; i < media.length(); i++) {
            JSONObject item = media.getJSONObject(i);
            allowed(item, MEDIA);
            scalarFields(item, keys());
            String id = string(item, "id");
            if (id.isEmpty() || id.length() > 160 || !IMAGE_TYPES.contains(string(item, "mime"))) throw new Invalid("invalid_payload");
            if (!"image".equals(string(item, "type"))) throw new Invalid("invalid_payload");
            String priorMime = referenced.put(id, item.getString("mime"));
            if (priorMime != null && !priorMime.equals(item.getString("mime"))) throw new Invalid("invalid_payload");
        }
    }
    private static void exercise(JSONObject item, boolean stage, Map<String, String> referenced) throws Exception {
        allowed(item, stage ? STAGE : EXERCISE);
        scalarFields(item, keys("media", "progressionVariants", "syncRevision"));
        if (item.has("nameDe") && (!(item.get("nameDe") instanceof String) || item.getString("nameDe").length() > 200 || item.getString("nameDe").matches("(?s).*[\\x00-\\x1f\\x7f].*"))) throw new Invalid("invalid_payload");
        String id = string(item, "id");
        if ((!stage && id.isEmpty()) || id.length() > 160 || string(item, "name").trim().isEmpty()) throw new Invalid("invalid_payload");
        if (item.has("media")) media(item.getJSONArray("media"), referenced);
        if (item.has("videoUrl") && !string(item, "videoUrl").isEmpty()) publicVideo(string(item, "videoUrl"));
        if (stage) return;
        if (item.has("createdAt")) timestamp(item, "createdAt");
        if (item.has("updatedAt")) timestamp(item, "updatedAt");
        if (item.has("syncRevision")) {
            JSONObject revision = item.getJSONObject("syncRevision");
            allowed(revision, keys("counter", "deviceId"));
            Object counter = revision.get("counter");
            if (!(counter instanceof Number) || ((Number) counter).doubleValue() < 0 || ((Number) counter).doubleValue() > 9_007_199_254_740_991d
                    || ((Number) counter).doubleValue() != ((Number) counter).longValue()) throw new Invalid("invalid_payload");
            String device = string(revision, "deviceId");
            if (!device.isEmpty()) requireIdentity(device);
        }
        if (item.has("progressionVariants")) {
            JSONArray variants = item.getJSONArray("progressionVariants");
            if (variants.length() > 32) throw new Invalid("invalid_payload");
            for (int i = 0; i < variants.length(); i++) exercise(variants.getJSONObject(i), true, referenced);
        }
    }

    private static JSONObject validate(String payload, String expectedDevice, String expectedRoom) throws Exception {
        if (payload == null || payload.getBytes(StandardCharsets.UTF_8).length > MAX_BYTES) throw new Invalid("invalid_payload");
        new StrictJson(payload).check();
        JSONTokener tokens = new JSONTokener(payload);
        Object parsed = tokens.nextValue();
        if (!(parsed instanceof JSONObject) || tokens.nextClean() != 0) throw new Invalid("invalid_payload");
        JSONObject document = (JSONObject) parsed;
        allowed(document, ENVELOPE);
        if (!"kgg_cross_data_safe_sync".equals(string(document, "kind")) || !"exercise-bank-packages-v2".equals(string(document, "schema"))) throw new Invalid("invalid_payload");
        Object version = document.get("version");
        if (!(version instanceof Number) || ((Number) version).doubleValue() != 2d) throw new Invalid("invalid_payload");
        timestamp(document, "exportedAt");
        if (document.has("appVersion")) string(document, "appVersion");
        JSONObject privacy = document.getJSONObject("privacy");
        Set<String> policy = keys("patients", "secrets", "debugPayloads", "rawData");
        allowed(privacy, policy);
        for (String key : policy) if (!Boolean.FALSE.equals(privacy.get(key))) throw new Invalid("invalid_payload");
        JSONArray scopes = document.getJSONArray("scopes");
        if (scopes.length() != 1 || !"exerciseBank".equals(scopes.get(0))) throw new Invalid("invalid_payload");
        if (document.getJSONArray("packages").length() != 0) throw new Invalid("invalid_payload");
        JSONObject origin = document.getJSONObject("origin");
        allowed(origin, keys("deviceId", "therapistId", "displayName", "roomId"));
        scalarFields(origin, keys());
        String deviceId = string(origin, "deviceId"), roomId = string(document, "roomId");
        requireIdentity(deviceId);
        requireIdentity(roomId);
        if (!roomId.equals(string(origin, "roomId")) || (expectedRoom != null && !expectedRoom.equals(roomId))) throw new Invalid("room_mismatch");
        if (expectedDevice != null && !expectedDevice.equals(deviceId)) throw new Invalid("peer_identity_mismatch");
        Map<String, String> referenced = new LinkedHashMap<>();
        JSONArray exercises = document.getJSONArray("exerciseBank");
        if (exercises.length() > 2000) throw new Invalid("invalid_payload");
        Set<String> ids = new HashSet<>();
        for (int i = 0; i < exercises.length(); i++) {
            JSONObject item = exercises.getJSONObject(i);
            exercise(item, false, referenced);
            if (!ids.add(item.getString("id"))) throw new Invalid("invalid_payload");
        }
        JSONObject tombstones = document.getJSONObject("tombstones");
        allowed(tombstones, keys("exerciseBank"));
        JSONArray deleted = tombstones.getJSONArray("exerciseBank");
        for (int i = 0; i < deleted.length(); i++) {
            JSONObject item = deleted.getJSONObject(i);
            allowed(item, keys("id", "deleted", "updatedAt"));
            if (string(item, "id").isEmpty() || !Boolean.TRUE.equals(item.get("deleted"))) throw new Invalid("invalid_payload");
            timestamp(item, "updatedAt");
        }
        JSONArray blobs = document.optJSONArray("mediaBlobs");
        if (document.has("mediaBlobs") && blobs == null) throw new Invalid("invalid_payload");
        Set<String> supplied = new HashSet<>();
        if (blobs != null) for (int i = 0; i < blobs.length(); i++) {
            JSONObject blob = blobs.getJSONObject(i);
            allowed(blob, keys("id", "mime", "sha256", "base64"));
            String id = string(blob, "id"), digest = string(blob, "sha256"), encoded = string(blob, "base64");
            if (id.isEmpty() || !supplied.add(id) || !IMAGE_TYPES.contains(string(blob, "mime")) || !digest.matches("[a-f0-9]{64}")
                    || encoded.length() > 2_666_670 || !encoded.matches("[A-Za-z0-9+/]+={0,2}")) throw new Invalid("invalid_payload");
            if (!blob.getString("mime").equals(referenced.get(id))) throw new Invalid("invalid_payload");
            byte[] data = Base64.getDecoder().decode(encoded);
            if (data.length == 0 || data.length > 2_000_000 || !sha256(data).equals(digest)) throw new Invalid("invalid_payload");
        }
        if (!supplied.equals(referenced.keySet())) throw new Invalid("invalid_payload");
        return document;
    }

    private static JSONObject meshHeader(String room) throws Exception {
        return new JSONObject().put("kind", "kgg_cross_data_safe_sync_mesh").put("version", 1).put("roomId", room).put("peers", new JSONArray());
    }
    private static int budgetMesh(int used, JSONObject document, int previousCount) throws Exception {
        int bytes = document.toString().getBytes(StandardCharsets.UTF_8).length + (previousCount > 0 ? 1 : 0);
        if (used > MAX_MESH_BYTES - bytes) throw new Invalid("mesh_too_large");
        return used + bytes;
    }
    private static void publicVideo(String value) throws Exception {
        URI uri = new URI(value.replace(" ", "%20"));
        if (!("https".equalsIgnoreCase(uri.getScheme()) || "http".equalsIgnoreCase(uri.getScheme()))
                || uri.getRawAuthority() == null || uri.getRawAuthority().isEmpty() || uri.getRawUserInfo() != null) throw new Invalid("invalid_payload");
        if (uri.getRawQuery() != null) for (String part : uri.getRawQuery().split("&")) {
            String key = URLDecoder.decode(part.split("=", 2)[0], "UTF-8");
            if (java.util.regex.Pattern.compile("token|secret|api.?key", java.util.regex.Pattern.CASE_INSENSITIVE).matcher(key).find()) throw new Invalid("invalid_payload");
        }
    }

    private static String sha256(byte[] bytes) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder result = new StringBuilder();
        for (byte value : hash) result.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        return result.toString();
    }

    /** Android's JSONTokener also accepts JavaScript syntax; provider documents must be strict JSON. */
    private static final class StrictJson {
        private final String text;
        private int offset;
        StrictJson(String text) { this.text = text; }
        void check() throws Exception { value(0); whitespace(); if (offset != text.length()) throw new Invalid("invalid_payload"); }
        private void whitespace() { while (offset < text.length() && " \t\r\n".indexOf(text.charAt(offset)) >= 0) offset++; }
        private boolean take(char expected) { whitespace(); if (offset < text.length() && text.charAt(offset) == expected) { offset++; return true; } return false; }
        private void need(char expected) throws Invalid { if (!take(expected)) throw new Invalid("invalid_payload"); }
        private void string() throws Invalid {
            need('"');
            while (offset < text.length()) {
                char character = text.charAt(offset++);
                if (character == '"') return;
                if (character < 32) throw new Invalid("invalid_payload");
                if (character == '\\') {
                    if (offset >= text.length()) throw new Invalid("invalid_payload");
                    char escaped = text.charAt(offset++);
                    if (escaped == 'u') {
                        for (int i = 0; i < 4; i++) if (offset >= text.length() || "0123456789abcdefABCDEF".indexOf(text.charAt(offset++)) < 0) throw new Invalid("invalid_payload");
                    } else if ("\"\\/bfnrt".indexOf(escaped) < 0) throw new Invalid("invalid_payload");
                }
            }
            throw new Invalid("invalid_payload");
        }
        private void value(int depth) throws Exception {
            if (depth > 64) throw new Invalid("invalid_payload");
            whitespace();
            if (offset >= text.length()) throw new Invalid("invalid_payload");
            char current = text.charAt(offset);
            if (current == '{') {
                offset++;
                if (take('}')) return;
                Set<String> names = new HashSet<>();
                do {
                    whitespace();
                    int start = offset;
                    string();
                    String key = (String) new JSONTokener(text.substring(start, offset)).nextValue();
                    if (!names.add(key)) throw new Invalid("invalid_payload");
                    need(':');
                    value(depth + 1);
                    if (take('}')) return;
                } while (take(','));
                throw new Invalid("invalid_payload");
            }
            if (current == '[') {
                offset++;
                if (take(']')) return;
                do { value(depth + 1); if (take(']')) return; } while (take(','));
                throw new Invalid("invalid_payload");
            }
            if (current == '"') { string(); return; }
            for (String literal : new String[]{"true", "false", "null"}) {
                if (text.startsWith(literal, offset)) { offset += literal.length(); return; }
            }
            int start = offset;
            while (offset < text.length() && ",]} \t\r\n".indexOf(text.charAt(offset)) < 0) offset++;
            if (start == offset || !text.substring(start, offset).matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?")) throw new Invalid("invalid_payload");
        }
    }

    static String readUtf8Bounded(InputStream stream) throws IOException {
        if (stream == null) throw new IOException("document_unavailable");
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int size;
        while ((size = stream.read(buffer)) != -1) {
            if (size == 0) continue;
            if (bytes.size() + size > MAX_BYTES) throw new IOException("document_too_large");
            bytes.write(buffer, 0, size);
        }
        try {
            return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes.toByteArray())).toString();
        } catch (CharacterCodingException invalid) { throw new IOException("invalid_utf8"); }
    }
    static String readUtf8Bounded(InputStream stream, long expectedBytes) throws IOException {
        if (expectedBytes > MAX_BYTES) throw new IOException("document_too_large");
        String value = readUtf8Bounded(stream);
        if (expectedBytes >= 0 && value.getBytes(StandardCharsets.UTF_8).length != expectedBytes) throw new IOException("read_incomplete");
        return value;
    }
}
