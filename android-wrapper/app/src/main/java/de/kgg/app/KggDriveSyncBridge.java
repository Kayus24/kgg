package de.kgg.app;

import android.app.Activity;
import android.content.ClipData;
import android.content.ContentResolver;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.UriPermission;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.LinkedHashSet;
import java.util.LinkedHashMap;
import java.util.Map;

/** User-selected SAF documents. No OAuth, broad storage permission or directory traversal. */
public final class KggDriveSyncBridge {
    private static final int OWN_REQUEST = 4302;
    private static final int PEERS_REQUEST = 4303;
    private static final int READ = Intent.FLAG_GRANT_READ_URI_PERMISSION;
    private static final int WRITE = Intent.FLAG_GRANT_WRITE_URI_PERMISSION;
    private final Activity activity;
    private final ContentResolver resolver;
    private final SharedPreferences preferences;
    private final KggDriveSyncTransport transport;
    private final Runnable ready;
    private int pendingRequest;
    private String pendingDevice = "";
    private String pendingRoom = "";
    private volatile KggSyncRequestCoordinator syncOwner;
    private Runnable configurationChanged=()->{};
    void attachSyncOwner(KggSyncRequestCoordinator owner,Runnable changed){syncOwner=owner;configurationChanged=changed;}
    private void reportError(String code){
        KggSyncRequestCoordinator owner=syncOwner;
        if(owner!=null&&!owner.isOwnerThread())owner.reportError(code);else transport.reportError(code);
    }

    KggDriveSyncBridge(Activity activity, Runnable ready) {
        this.activity = activity;
        this.ready = ready;
        this.resolver = activity.getContentResolver();
        this.preferences = activity.getSharedPreferences("kgg_drive_sync_v1", Activity.MODE_PRIVATE);
        File directory = new File(activity.getFilesDir(), "drive-sync");
        KggDriveSyncTransport.State state = new KggDriveSyncTransport.State() {
            private volatile String cachedConfiguration;
            public String read(String key) throws IOException {
                if ("configuration".equals(key)) {
                    if(cachedConfiguration==null)cachedConfiguration=initialConfiguration();
                    return cachedConfiguration;
                }
                if (!fileKey(key)) return preferences.getString(key, "");
                File outbox = new File(directory, key + ".json");
                if (!outbox.exists()) return "";
                try (InputStream input = Files.newInputStream(outbox.toPath())) {
                    return KggDriveSyncTransport.readUtf8Bounded(input);
                }
            }
            public void write(String key, String value) throws IOException {
                if (!fileKey(key)) {
                    if (!preferences.edit().putString(key, value).commit()) throw new IOException("private_state_failed");
                    return;
                }
                if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("private_state_failed");
                File temporary = new File(directory, key + ".tmp");
                File destination = new File(directory, key + ".json");
                Files.write(temporary.toPath(), value.getBytes(StandardCharsets.UTF_8));
                try {
                    Files.move(temporary.toPath(), destination.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
                } catch (AtomicMoveNotSupportedException unsupported) {
                    Files.move(temporary.toPath(), destination.toPath(), StandardCopyOption.REPLACE_EXISTING);
                }
                if ("configuration".equals(key)) cachedConfiguration = value;
            }
            private boolean fileKey(String key) { return "outbox".equals(key) || "configuration".equals(key) || key.matches("retained_[a-f0-9]{64}"); }
            private String initialConfiguration() {
                File file = new File(directory, "configuration.json");
                if (!file.exists()) return "";
                try (InputStream input = Files.newInputStream(file.toPath())) { return KggDriveSyncTransport.readUtf8Bounded(input); }
                catch (IOException failure) { return "{"; } // Failed closed: never silently switch a damaged configuration to local.
            }
        };
        this.transport = new KggDriveSyncTransport(state, new KggDriveSyncTransport.Documents() {
            public String read(String document) throws IOException {
                Uri uri = Uri.parse(document);
                if (!hasGrant(uri, READ)) throw new IOException("permission_missing");
                long expected = documentSize(uri);
                if (expected > KggDriveSyncTransport.MAX_BYTES) throw new IOException("document_too_large");
                try (InputStream input = resolver.openInputStream(uri)) {
                    return KggDriveSyncTransport.readUtf8Bounded(input, expected);
                } catch (SecurityException failure) { throw new IOException("permission_missing"); }
            }
            public void write(String document, String payload) throws IOException {
                Uri uri = Uri.parse(document);
                if (!hasGrant(uri, READ | WRITE) || !supportsWrite(uri)) throw new IOException("permission_missing");
                try (OutputStream output = resolver.openOutputStream(uri, "wt")) {
                    if (output == null) throw new IOException("document_unavailable");
                    output.write(payload.getBytes(StandardCharsets.UTF_8));
                    output.flush();
                } catch (SecurityException failure) { throw new IOException("permission_missing"); }
            }
        });
    }

    @JavascriptInterface public String getStatus() { return transport.status().toString(); }
    @JavascriptInterface public String readSyncJson() { return transport.read().toString(); }
    @JavascriptInterface public boolean writeSyncJson(String payload) { return transport.write(payload); }

    @JavascriptInterface public boolean configureOwnDriveFile(String optionsJson) {
        try {
            JSONObject options = new JSONObject(optionsJson);
            if(syncOwner!=null&&!syncOwner.isOwnerThread())return syncOwner.runBooleanWhenIdle(()->configureOwnDriveFile(optionsJson));
            return startPicker(OWN_REQUEST, options.getString("deviceId"), options.getString("roomId"));
        } catch (Exception failure) { reportError("invalid_identity"); return false; }
    }

    @JavascriptInterface public boolean selectDrivePeerFiles(String optionsJson) {
        try {
            JSONObject options = new JSONObject(optionsJson);
            if(syncOwner!=null&&!syncOwner.isOwnerThread())return syncOwner.runBooleanWhenIdle(()->selectDrivePeerFiles(optionsJson));
            if (!transport.status().optBoolean("driveConfigured")) {
                reportError("not_configured");
                return false;
            }
            return startPicker(PEERS_REQUEST, "", options.getString("roomId"));
        } catch (Exception failure) { reportError("invalid_identity"); return false; }
    }

    private synchronized boolean startPicker(int request, String device, String room) {
        if (pendingRequest != 0 || !room.matches("[A-Za-z0-9._-]{1,96}")
                || (request == OWN_REQUEST && !device.matches("[A-Za-z0-9._-]{1,96}"))) return false;
        pendingRequest = request;
        pendingDevice = device;
        pendingRoom = room;
        activity.runOnUiThread(() -> {
            try {
                Intent intent = new Intent(request == OWN_REQUEST ? Intent.ACTION_CREATE_DOCUMENT : Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.addFlags(READ | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                if (request == OWN_REQUEST) {
                    intent.addFlags(WRITE);
                    intent.putExtra(Intent.EXTRA_TITLE, "kgg_" + device + ".json");
                } else {
                    intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                }
                activity.startActivityForResult(intent, request);
            } catch (Exception failure) {
                clearPending();
                reportError("picker_unavailable");
                ready.run();
            }
        });
        return true;
    }

    /** Consumes only this feature's request codes; camera/PDF/release callbacks stay untouched. */
    boolean onActivityResult(int request, int result, Intent data) {
        if (request != OWN_REQUEST && request != PEERS_REQUEST) return false;
        final String device;
        final String room;
        synchronized (this) {
            if (pendingRequest != request) return true;
            device = pendingDevice;
            room = pendingRoom;
        }
        if (result != Activity.RESULT_OK || data == null) {
            clearPending();
            return true;
        }
        LinkedHashSet<String> selected = new LinkedHashSet<>();
        if (data.getData() != null) selected.add(data.getData().toString());
        ClipData clip = data.getClipData();
        if (clip != null) {
            if (clip.getItemCount() > KggDriveSyncTransport.MAX_PEERS) {
                clearPending();
                reportError("invalid_peer_selection");
                ready.run();
                return true;
            }
            for (int i = 0; i < clip.getItemCount(); i++) if (clip.getItemAt(i).getUri() != null) selected.add(clip.getItemAt(i).getUri().toString());
        }
        int granted = data.getFlags();
        Runnable selection=()->acceptSelection(request,selected.toArray(new String[0]),device,room,granted);
        if(syncOwner!=null){
            if(!syncOwner.enqueueControl(selection,ready)){clearPending();syncOwner.reportError("queue_busy");activity.runOnUiThread(ready);}
        }else new Thread(selection,"kgg-drive-selection").start();
        return true;
    }

    private void acceptSelection(int request, String[] selected, String device, String room, int granted) {
        Map<Uri, Integer> newGrants = new LinkedHashMap<>();
        int required = request == OWN_REQUEST ? READ | WRITE : READ;
        String[] previous = transport.selectedDocuments();
        try {
            if (selected.length == 0 || selected.length > KggDriveSyncTransport.MAX_PEERS || (request == OWN_REQUEST && selected.length != 1)
                    || (granted & required) != required) throw new IOException("permission_missing");
            for (String document : selected) {
                Uri uri = Uri.parse(document);
                if (!"content".equals(uri.getScheme())) throw new IOException("invalid_document");
                int before = grantMask(uri);
                if ((before & required) != required) {
                    resolver.takePersistableUriPermission(uri, required);
                    newGrants.put(uri, required & ~before);
                }
                if (!hasGrant(uri, required) || (request == OWN_REQUEST && !supportsWrite(uri))) throw new IOException("permission_missing");
            }
            boolean accepted = request == OWN_REQUEST
                    ? transport.configureOwn(selected[0], device, room)
                    : transport.configurePeers(selected, room);
            if (!accepted) {
                for (Map.Entry<Uri, Integer> grant : newGrants.entrySet()) release(grant.getKey(), grant.getValue());
                return;
            }
            configurationChanged.run();
            LinkedHashSet<String> active = new LinkedHashSet<>(java.util.Arrays.asList(transport.selectedDocuments()));
            for (String old : previous) if (!active.contains(old)) release(Uri.parse(old), request == OWN_REQUEST ? READ | WRITE : READ);
        } catch (Exception failure) {
            for (Map.Entry<Uri, Integer> grant : newGrants.entrySet()) release(grant.getKey(), grant.getValue());
            // Transport validation supplies a precise bounded code; never expose provider exceptions/URIs.
            transport.reportError("selection_failed");
        } finally {
            clearPending();
            if(syncOwner==null)activity.runOnUiThread(ready);
        }
    }

    @JavascriptInterface public boolean disconnectDrive() {
        if(syncOwner!=null&&!syncOwner.isOwnerThread()){
            boolean result=syncOwner.runBooleanWhenIdle(this::disconnectDrive);
            if(result)activity.runOnUiThread(ready);
            return result;
        }
        synchronized (this) { if (pendingRequest != 0) return false; }
        String[] selected = transport.selectedDocuments();
        if (!transport.disconnect()) return false;
        configurationChanged.run();
        for (int i = 0; i < selected.length; i++) release(Uri.parse(selected[i]), i == 0 ? READ | WRITE : READ);
        if(syncOwner==null)activity.runOnUiThread(ready);
        return true;
    }

    private synchronized void clearPending() { pendingRequest = 0; pendingDevice = ""; pendingRoom = ""; }

    private boolean hasGrant(Uri uri, int required) {
        return (grantMask(uri) & required) == required;
    }

    private int grantMask(Uri uri) {
        for (UriPermission permission : resolver.getPersistedUriPermissions()) {
            if (!permission.getUri().equals(uri)) continue;
            return (permission.isReadPermission() ? READ : 0) | (permission.isWritePermission() ? WRITE : 0);
        }
        return 0;
    }

    private boolean supportsWrite(Uri uri) throws IOException {
        try (Cursor cursor = resolver.query(uri, new String[]{DocumentsContract.Document.COLUMN_FLAGS, DocumentsContract.Document.COLUMN_MIME_TYPE}, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst()) return false;
            int flagIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_FLAGS);
            int mimeIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_MIME_TYPE);
            if (flagIndex < 0 || mimeIndex < 0) return false;
            int flags = cursor.getInt(flagIndex);
            return (flags & DocumentsContract.Document.FLAG_SUPPORTS_WRITE) != 0
                    && !DocumentsContract.Document.MIME_TYPE_DIR.equals(cursor.getString(mimeIndex));
        } catch (RuntimeException failure) { throw new IOException("document_unavailable"); }
    }

    private long documentSize(Uri uri) throws IOException {
        try (Cursor cursor = resolver.query(uri, new String[]{OpenableColumns.SIZE}, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst()) return -1;
            int index = cursor.getColumnIndex(OpenableColumns.SIZE);
            return index < 0 || cursor.isNull(index) ? -1 : cursor.getLong(index);
        } catch (RuntimeException failure) { throw new IOException("document_unavailable"); }
    }

    private void release(Uri uri, int flags) {
        try {
            for (UriPermission permission : resolver.getPersistedUriPermissions()) {
                if (!permission.getUri().equals(uri)) continue;
                int actual = (permission.isReadPermission() ? READ : 0) | (permission.isWritePermission() ? WRITE : 0);
                if ((actual & flags) != 0) resolver.releasePersistableUriPermission(uri, actual & flags);
            }
        } catch (RuntimeException ignored) { }
    }
}
