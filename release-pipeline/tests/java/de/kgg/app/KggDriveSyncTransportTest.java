package de.kgg.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/** Provider is the external boundary; validation, durable state and routing are production code. */
public final class KggDriveSyncTransportTest {
    private static int checks;
    private static final class MemoryState implements KggDriveSyncTransport.State {
        final Map<String, String> values = new LinkedHashMap<>();
        String failOnceKey = "";
        public String read(String key) { return values.getOrDefault(key, ""); }
        public void write(String key, String value) throws IOException {
            if (key.equals(failOnceKey)) { failOnceKey = ""; throw new IOException("private storage boundary failure"); }
            values.put(key, value);
        }
    }
    private static final class Provider implements KggDriveSyncTransport.Documents {
        final Map<String, String> content = new LinkedHashMap<>();
        boolean failRead, failWrite;
        int reads;
        String lastWritten = "";
        public String read(String document) throws IOException {
            reads++;
            if (failRead || !content.containsKey(document)) throw new IOException("external boundary unavailable");
            return content.get(document);
        }
        public void write(String document, String payload) throws IOException {
            if (failWrite) throw new IOException("external boundary unavailable");
            lastWritten = document;
            content.put(document, payload);
        }
    }
    private static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static JSONObject doc(String device, String room) throws Exception {
        return new JSONObject("{\"kind\":\"kgg_cross_data_safe_sync\",\"version\":2,"
                + "\"schema\":\"exercise-bank-packages-v2\",\"scopes\":[\"exerciseBank\"],"
                + "\"exportedAt\":\"2026-10-15T12:00:00Z\",\"privacy\":{\"patients\":false,\"secrets\":false,\"debugPayloads\":false,\"rawData\":false},"
                + "\"exerciseBank\":[{\"id\":\"exercise-one\",\"name\":\"Synthetic exercise\",\"updatedAt\":\"2026-10-15T12:00:00Z\","
                + "\"syncRevision\":{\"counter\":1,\"deviceId\":\"device-a\"}}],\"packages\":[],\"tombstones\":{\"exerciseBank\":[]}}")
                .put("roomId", room).put("origin", new JSONObject().put("deviceId", device)
                        .put("therapistId", device).put("displayName", "Synthetic device").put("roomId", room));
    }
    private static void rejects(KggDriveSyncTransport transport, JSONObject payload, String message) {
        check(!transport.write(payload.toString()), message);
    }
    public static void main(String[] args) throws Exception {
        MemoryState state = new MemoryState();
        Provider provider = new Provider();
        KggDriveSyncTransport transport = new KggDriveSyncTransport(state, provider);
        JSONObject own = doc("device-a", "room-one");
        check(!transport.write(own.toString()), "unconfigured local outbox must not claim provider success");
        check(state.read("outbox").contains("Synthetic exercise"), "pending edit must persist before setup");
        check(transport.status().getBoolean("pending"), "unconfigured outbox remains pending");
        check(transport.configureOwn("content://synthetic/own", "device-a", "room-one"), "explicit own binding must succeed");
        provider.failWrite = true;
        check(!transport.write(own.toString()), "provider failure must return false");
        check(transport.status().getBoolean("pending") && !transport.status().getBoolean("providerAccepted"), "failed upload must stay pending");
        KggDriveSyncTransport restarted = new KggDriveSyncTransport(state, provider);
        check(restarted.status().getBoolean("pending"), "pending upload must survive process recreation");
        provider.failWrite = false;
        check(restarted.write(own.toString()), "a subsequent automatic retry must publish pending data");
        check(!restarted.status().getBoolean("pending") && restarted.status().getBoolean("providerAccepted"), "provider acknowledgement must clear upload pending");
        check(provider.lastWritten.equals("content://synthetic/own"), "only own URI can be written");
        check(!restarted.status().toString().contains("content://"), "status must never expose document identifiers");

        provider.content.put("content://synthetic/peer", doc("device-b", "room-one").toString());
        check(restarted.configurePeers(new String[]{"content://synthetic/peer"}, "room-one"), "explicit peer selection binds origin and room");
        state.failOnceKey = "flags";
        check(!restarted.configureOwn("content://synthetic/rejected-own", "device-a", "room-one"), "setup state failure must be reported");
        check(java.util.Arrays.equals(restarted.selectedDocuments(), new String[]{"content://synthetic/own", "content://synthetic/peer"}), "failed own setup must retain the prior complete binding");
        provider.content.put("content://synthetic/new-peer", doc("device-d", "room-one").toString());
        state.failOnceKey = "flags";
        check(!restarted.configurePeers(new String[]{"content://synthetic/new-peer"}, "room-one"), "peer setup state failure must be reported");
        check(java.util.Arrays.equals(restarted.selectedDocuments(), new String[]{"content://synthetic/own", "content://synthetic/peer"}), "failed peer setup must retain prior bindings, so fresh grants can be released safely");
        state.failOnceKey = "configuration";
        check(!restarted.configureOwn("content://synthetic/rejected-own", "device-a", "room-one"), "failed atomic configuration commit must be reported");
        check(java.util.Arrays.equals(restarted.selectedDocuments(), new String[]{"content://synthetic/own", "content://synthetic/peer"}), "failed final commit must preserve the complete old own/peer binding");
        JSONObject mesh = restarted.read();
        check(mesh.getJSONArray("peers").length() == 1, "configured peer must be readable");
        provider.content.put("content://synthetic/peer", doc("device-c", "room-one").toString());
        check(restarted.read().getString("kind").equals("kgg_sync_transport_error"), "replaced peer identity must fail without rebinding");
        check(restarted.status().getBoolean("pending"), "failed complete peer read must stay pending");
        provider.content.put("content://synthetic/peer", doc("device-b", "room-other").toString());
        check(restarted.read().getString("kind").equals("kgg_sync_transport_error"), "peer room replacement must be rejected");
        provider.content.put("content://synthetic/peer", doc("device-b", "room-one").toString());
        provider.content.put("content://synthetic/peer-two", doc("device-c", "room-one").toString());
        check(restarted.configurePeers(new String[]{"content://synthetic/peer", "content://synthetic/peer-two"}, "room-one"), "multiple explicit peers must bind");
        provider.content.remove("content://synthetic/peer-two");
        check(restarted.read().getString("kind").equals("kgg_sync_transport_error"), "one missing peer must reject the whole mesh, not partially import");
        check(provider.lastWritten.equals("content://synthetic/own"), "peer selection/read must never write partner documents");
        check(!restarted.configurePeers(new String[]{"content://synthetic/own"}, "room-one"), "own document cannot be rebound as peer");

        rejects(restarted, doc("device-c", "room-one"), "a different device cannot overwrite own document");
        rejects(restarted, doc("device-a", "room-other"), "different room cannot overwrite own document");
        for (String key : new String[]{"patientName", "apiKey", "access_token", "rawPayload", "base64Payload", "unexpected"}) {
            rejects(restarted, doc("device-a", "room-one").put(key, "synthetic-canary"), "forbidden envelope field accepted: " + key);
        }
        JSONObject bad = doc("device-a", "room-one");
        bad.getJSONObject("privacy").put("patients", true);
        rejects(restarted, bad, "privacy declarations must all be explicit false");
        bad = doc("device-a", "room-one");
        bad.getJSONArray("exerciseBank").getJSONObject(0).put("startLoad", 40);
        rejects(restarted, bad, "patient plan values cannot cross exercise allowlist");
        bad = doc("device-a", "room-one");
        bad.getJSONArray("exerciseBank").getJSONObject(0).put("media", new JSONObject().put("deleteToken", "synthetic-canary"));
        rejects(restarted, bad, "upload secrets cannot cross nested media allowlist");
        bad = doc("device-a", "room-one").put("mediaBlobs", new JSONArray().put(new JSONObject()
                .put("id", "blob-one").put("mime", "image/png").put("sha256", "0".repeat(64)).put("base64", "aGVsbG8=")));
        rejects(restarted, bad, "wrong image digest cannot be published");
        bad = doc("device-a", "room-one").put("packages", new JSONArray().put(new JSONObject().put("name", "Synthetic patient canary")));
        rejects(restarted, bad, "plan packages cannot be automatically exported");
        check(!restarted.write(own + " trailing"), "trailing data must not be treated as a complete JSON document");
        check(!restarted.write("{"), "truncated document must not be published");
        check(!restarted.write(own.toString().replace("\"kind\"", "'kind'")), "non-JSON single quoted keys must be rejected on Android too");
        check(!restarted.write(own.toString().replace("\"kind\"", "kind")), "non-JSON bare keys must be rejected on Android too");
        check(!restarted.write(" ".repeat(8_000_001)), "oversized document must not be published");
        check(provider.lastWritten.equals("content://synthetic/own"), "invalid payload must never write to peer");

        check(KggDriveSyncTransport.readUtf8Bounded(new ByteArrayInputStream("ü".getBytes(StandardCharsets.UTF_8))).equals("ü"), "bounded stream must preserve UTF-8");
        boolean rejected = false;
        try { KggDriveSyncTransport.readUtf8Bounded(new ByteArrayInputStream(new byte[]{(byte) 0xc3})); }
        catch (IOException expected) { rejected = true; }
        check(rejected, "malformed UTF-8 must not be replaced silently");
        rejected = false;
        try { KggDriveSyncTransport.readUtf8Bounded(new ByteArrayInputStream(new byte[8_000_001])); }
        catch (IOException expected) { rejected = true; }
        check(rejected, "readlimit must fail the whole oversized stream");
        rejected = false;
        try { KggDriveSyncTransport.readUtf8Bounded(new ByteArrayInputStream("{}".getBytes(StandardCharsets.UTF_8)), 20); }
        catch (IOException expected) { rejected = true; }
        check(rejected, "a prematurely closed stream must fail even when its prefix is parseable JSON");
        restarted.disconnect();
        check(!restarted.status().getBoolean("driveConfigured"), "disconnect must remove document transport binding");
        check(!state.read("outbox").isEmpty(), "disconnect must retain the local pending library snapshot");
        String retained = state.read("outbox");
        check(restarted.configureOwn("content://synthetic/new-own", "device-a", "room-two"), "explicit setup after disconnect must allow a new room");
        check(state.values.entrySet().stream().anyMatch(entry -> entry.getKey().startsWith("retained_") && entry.getValue().equals(retained)), "reconfiguration must privately retain the previous complete outbox");
        check(restarted.write(doc("device-a", "room-two").toString()), "new-room UI snapshot must write only the newly selected own document");
        check(provider.lastWritten.equals("content://synthetic/new-own"), "reconfiguration must not overwrite the old room document");
        JSONObject publicVideo = doc("device-a", "room-two");
        publicVideo.getJSONArray("exerciseBank").getJSONObject(0).put("videoUrl", "http://example.invalid/synthetic-video");
        check(restarted.write(publicVideo.toString()), "existing public HTTP video metadata must remain transportable");
        publicVideo.getJSONArray("exerciseBank").getJSONObject(0).put("videoUrl", "https://example.invalid/video?access_token=synthetic-canary");
        rejects(restarted, publicVideo, "secret-bearing video URLs must be rejected");

        byte[] largeImage = new byte[1_875_000];
        String largeBase64 = java.util.Base64.getEncoder().encodeToString(largeImage);
        byte[] largeDigestBytes = java.security.MessageDigest.getInstance("SHA-256").digest(largeImage);
        StringBuilder largeDigest = new StringBuilder();
        for (byte value : largeDigestBytes) largeDigest.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        String[] largePeers = new String[7];
        for (int i = 0; i < largePeers.length; i++) {
            largePeers[i] = "content://synthetic/large-" + i;
            provider.content.put(largePeers[i], doc("large-device-" + i, "room-two").toString());
        }
        check(restarted.configurePeers(largePeers, "room-two"), "explicit small partner documents must configure");
        for (int i = 0; i < largePeers.length; i++) {
            JSONObject large = doc("large-device-" + i, "room-two");
            JSONArray references = new JSONArray(), blobs = new JSONArray();
            for (String id : new String[]{"large-image-a", "large-image-b"}) {
                references.put(new JSONObject().put("id", id).put("type", "image").put("mime", "image/png").put("width", 1).put("height", 1));
                blobs.put(new JSONObject().put("id", id).put("mime", "image/png").put("sha256", largeDigest.toString()).put("base64", largeBase64));
            }
            large.getJSONArray("exerciseBank").getJSONObject(0).put("media", references);
            large.put("mediaBlobs", blobs);
            provider.content.put(largePeers[i], large.toString());
        }
        check(restarted.configurePeers(new String[]{largePeers[0], largePeers[1]}, "room-two"), "two valid 5 MB peer files must not be mistaken for an oversized device file");
        check(restarted.read().getJSONArray("peers").length() == 2, "two normal peers totalling 10 MB must import as one complete mesh");
        // Configure the seven identities while small, then grow them remotely to exceed the mesh budget.
        Map<String, String> largeContent = new LinkedHashMap<>(provider.content);
        for (int i = 0; i < largePeers.length; i++) provider.content.put(largePeers[i], doc("large-device-" + i, "room-two").toString());
        check(restarted.configurePeers(largePeers, "room-two"), "the peer set must bind before growth");
        provider.content.putAll(largeContent);
        provider.reads = 0;
        JSONObject overBudget = restarted.read();
        check(overBudget.optString("error").equals("mesh_too_large"), "aggregate overflow must return a bounded explicit failure, not a partial mesh");
        check(!overBudget.has("peers") && provider.reads <= 7, "overflow must stop before unbounded aggregation and expose no partial success");
        byte[] oversizedImage = new byte[2_000_001];
        StringBuilder oversizedHash = new StringBuilder();
        for (byte value : java.security.MessageDigest.getInstance("SHA-256").digest(oversizedImage)) oversizedHash.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        JSONObject oversizedBlob = doc("device-a", "room-two");
        oversizedBlob.getJSONArray("exerciseBank").getJSONObject(0).put("media", new JSONArray().put(new JSONObject()
                .put("id", "too-large").put("type", "image").put("mime", "image/png")));
        oversizedBlob.put("mediaBlobs", new JSONArray().put(new JSONObject().put("id", "too-large").put("mime", "image/png")
                .put("sha256", oversizedHash.toString()).put("base64", java.util.Base64.getEncoder().encodeToString(oversizedImage))));
        rejects(restarted, oversizedBlob, "per-image 2 MB limit must match the Core wire contract even when the document fits 8 MB");
        KggDriveSyncTransport names = new KggDriveSyncTransport(new MemoryState(), provider);
        check(names.configureOwn("content://synthetic/name-fields", "device-a", "room-two"), "name field setup");
        JSONObject named = doc("device-a", "room-two");
        JSONObject namedExercise = named.getJSONArray("exerciseBank").getJSONObject(0);
        namedExercise.put("nameDe", "Einbeinstand");
        check(names.write(named.toString()), "German alias is accepted and retained");
        check(new JSONObject(provider.content.get("content://synthetic/name-fields")).getJSONArray("exerciseBank").getJSONObject(0).getString("nameDe").equals("Einbeinstand"), "provider bytes keep German alias");
        namedExercise.put("nameDe", "");check(names.write(named.toString()), "explicit empty German alias is valid");
        namedExercise.put("nameDe", 42);rejects(names, named, "invalid German label type must fail");
        namedExercise.put("nameDe", "x".repeat(201));rejects(names, named, "German label length must match Core");
        namedExercise.put("nameDe", "bad\nname");rejects(names, named, "German control characters must fail");
        if (args.length == 1) {
            String realPayload = java.nio.file.Files.readString(java.nio.file.Path.of(args[0]), StandardCharsets.UTF_8);
            JSONObject real = new JSONObject(realPayload);
            String device = real.getJSONObject("origin").getString("deviceId"), room = real.getString("roomId");
            Provider contractProvider = new Provider();
            KggDriveSyncTransport sender = new KggDriveSyncTransport(new MemoryState(), contractProvider);
            check(sender.configureOwn("content://synthetic/core-sender", device, room), "Core document identity must configure");
            check(sender.write(realPayload), "real Core builder document must pass the actual native validator");
            KggDriveSyncTransport receiver = new KggDriveSyncTransport(new MemoryState(), contractProvider);
            check(receiver.configureOwn("content://synthetic/core-receiver", "native-contract-receiver", room), "receiver must configure independently");
            check(receiver.configurePeers(new String[]{"content://synthetic/core-sender"}, room), "the same Core document must bind as an authorized peer");
            JSONObject received = receiver.read().getJSONArray("peers").getJSONObject(0);
            check(received.getJSONObject("origin").getString("deviceId").equals(device)
                    && received.getJSONArray("exerciseBank").length() == real.getJSONArray("exerciseBank").length(), "Core document must survive a complete native transport roundtrip");
            System.out.println("Real Core builder → Native validator → bound peer roundtrip PASS");
        }
        System.out.println("Native SAF transport PASS: " + checks + " checks; provider/device integration not exercised");
    }
}
