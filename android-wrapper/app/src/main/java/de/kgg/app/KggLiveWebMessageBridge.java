package de.kgg.app;

import android.net.Uri;
import android.webkit.WebView;

import androidx.webkit.JavaScriptReplyProxy;
import androidx.webkit.WebMessageCompat;
import androidx.webkit.WebViewCompat;

import org.json.JSONObject;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Strict asynchronous KGGLiveKey message endpoint. It is intentionally not a
 * JavascriptInterface and every callback re-checks the current main frame.
 */
final class KggLiveWebMessageBridge implements WebViewCompat.WebMessageListener {
    private static final int PROTOCOL_VERSION = 1;
    private static final int MAX_REQUEST_ID_CHARS = 64;
    private static final int MAX_OPERATION_CHARS = 40;
    private static final int MAX_PLAN_KEY_CHARS = KggLiveBridgePolicy.MAX_PLAN_KEY_LENGTH;
    private static final int MAX_SMALL_STRING_CHARS = 128;
    private static final int MAX_EXPIRES_AT_CHARS = 40;
    private static final int MAX_AAD_BASE64_CHARS = 8 * 1024;
    private static final int MAX_FRAME_BASE64_CHARS = 96 * 1024;
    private static final Pattern REQUEST_ID = Pattern.compile(
            "[A-Za-z0-9][A-Za-z0-9._~-]{0,63}"
    );
    private static final Set<String> REQUEST_KEYS = immutableSet(
            "version", "requestId", "op", "args"
    );
    private static final Set<String> OPERATIONS = immutableSet(
            "getCapabilities",
            "hasPairing",
            "createPairing",
            "rotatePairing",
            "deletePairing",
            "computeJoinHmac",
            "verifyPeerOffer",
            "createEphemeralKeyPair",
            "deriveSessionKey",
            "encryptFrame",
            "decryptFrame",
            "closeSession",
            "enableBlackout",
            "disableBlackout"
    );

    private final KggLiveKeyBridge nativeBridge;

    KggLiveWebMessageBridge(KggLiveKeyBridge nativeBridge) {
        if (nativeBridge == null) {
            throw new IllegalArgumentException("bridge_invalid");
        }
        this.nativeBridge = nativeBridge;
    }

    @Override
    public void onPostMessage(
            WebView view,
            WebMessageCompat message,
            Uri sourceOrigin,
            boolean isMainFrame,
            JavaScriptReplyProxy replyProxy
    ) {
        // This guard deliberately runs before touching message data or JSON.
        String frameError = nativeBridge.messageFrameError(view, isMainFrame);
        if (!frameError.isEmpty()) {
            if (KggLiveWebMessagePolicy.ERROR_ORIGIN_NOT_ALLOWED.equals(frameError)) {
                nativeBridge.deactivateForPage();
            }
            replyError(replyProxy, "", frameError);
            return;
        }
        if (message == null || message.getType() != WebMessageCompat.TYPE_STRING) {
            replyError(replyProxy, "", "message_not_allowed");
            return;
        }
        String requestJson = message.getData();
        if (requestJson == null || requestJson.length() > KggLiveWebMessagePolicy.MAX_REQUEST_CHARS) {
            replyError(replyProxy, "", "request_too_large");
            return;
        }

        JSONObject request;
        String requestId = "";
        try {
            request = parseRequest(requestJson);
            requestId = request.getString("requestId");
            dispatch(request, requestId, replyProxy);
        } catch (Exception ignored) {
            replyError(replyProxy, requestId, "invalid_request");
        }
    }

    private JSONObject parseRequest(String requestJson) throws Exception {
        JSONObject request = new JSONObject(requestJson);
        if (request.length() != REQUEST_KEYS.size() || !hasOnlyKeys(request, REQUEST_KEYS)) {
            throw new IllegalArgumentException("request_fields_invalid");
        }
        Object version = request.get("version");
        if (!(version instanceof Integer) || ((Integer) version) != PROTOCOL_VERSION) {
            throw new IllegalArgumentException("request_version_invalid");
        }
        Object rawRequestId = request.get("requestId");
        if (!(rawRequestId instanceof String)
                || ((String) rawRequestId).length() < 1
                || ((String) rawRequestId).length() > MAX_REQUEST_ID_CHARS
                || !REQUEST_ID.matcher((String) rawRequestId).matches()) {
            throw new IllegalArgumentException("request_id_invalid");
        }
        Object rawOperation = request.get("op");
        if (!(rawOperation instanceof String)
                || ((String) rawOperation).length() < 1
                || ((String) rawOperation).length() > MAX_OPERATION_CHARS
                || !OPERATIONS.contains(rawOperation)) {
            throw new IllegalArgumentException("operation_invalid");
        }
        if (!(request.get("args") instanceof JSONObject)) {
            throw new IllegalArgumentException("args_invalid");
        }
        return request;
    }

    private void dispatch(
            JSONObject request,
            String requestId,
            JavaScriptReplyProxy replyProxy
    ) throws Exception {
        String operation = request.getString("op");
        JSONObject args = request.getJSONObject("args");
        switch (operation) {
            case "getCapabilities":
                requireArgs(args);
                replyNativeJson(replyProxy, requestId, nativeBridge.getCapabilities());
                return;
            case "hasPairing":
                requireArgs(args, "planKey");
                replyResult(replyProxy, requestId, nativeBridge.hasPairing(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS)
                ));
                return;
            case "createPairing":
                requireArgs(args, "planKey");
                replyNativeJson(replyProxy, requestId, nativeBridge.createPairing(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS)
                ));
                return;
            case "rotatePairing":
                requireArgs(args, "planKey");
                replyNativeJson(replyProxy, requestId, nativeBridge.rotatePairing(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS)
                ));
                return;
            case "deletePairing":
                requireArgs(args, "planKey");
                replyResult(replyProxy, requestId, nativeBridge.deletePairing(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS)
                ));
                return;
            case "computeJoinHmac":
                requireArgs(args, "planKey", "sessionId", "sessionSalt");
                replyNativeJson(replyProxy, requestId, nativeBridge.computeJoinHmac(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "sessionSalt", MAX_SMALL_STRING_CHARS)
                ));
                return;
            case "verifyPeerOffer":
                requireArgs(args, "planKey", "localRole", "sessionId", "offer");
                replyResult(replyProxy, requestId, nativeBridge.verifyPeerOffer(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "localRole", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "offer", KggLiveCryptoCore.MAX_OFFER_BYTES)
                ));
                return;
            case "createEphemeralKeyPair":
                requireArgs(args, "curve", "planKey", "sessionId", "role");
                replyNativeJson(replyProxy, requestId, nativeBridge.createEphemeralKeyPair(
                        stringArg(args, "curve", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "role", MAX_SMALL_STRING_CHARS)
                ));
                return;
            case "deriveSessionKey":
                requireArgs(
                        args,
                        "curve", "planKey", "sessionId", "sessionSalt", "pairingId",
                        "pairingBinding", "privateKeyHandle", "peerPublicKey", "role", "expiresAt"
                );
                replyNativeJson(replyProxy, requestId, nativeBridge.deriveSessionKeyForClient(
                        stringArg(args, "curve", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "sessionSalt", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "pairingId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "pairingBinding", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "privateKeyHandle", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "peerPublicKey", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "role", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "expiresAt", MAX_EXPIRES_AT_CHARS)
                ));
                return;
            case "encryptFrame":
                requireArgs(args, "planKey", "sessionId", "aad", "plaintext");
                replyNativeJson(replyProxy, requestId, nativeBridge.encryptFrame(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "aad", MAX_AAD_BASE64_CHARS),
                        stringArg(args, "plaintext", MAX_FRAME_BASE64_CHARS)
                ));
                return;
            case "decryptFrame":
                requireArgs(args, "planKey", "sessionId", "nonce", "aad", "ciphertext");
                replyNativeJson(replyProxy, requestId, nativeBridge.decryptFrame(
                        stringArg(args, "planKey", MAX_PLAN_KEY_CHARS),
                        stringArg(args, "sessionId", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "nonce", MAX_SMALL_STRING_CHARS),
                        stringArg(args, "aad", MAX_AAD_BASE64_CHARS),
                        stringArg(args, "ciphertext", MAX_FRAME_BASE64_CHARS)
                ));
                return;
            case "closeSession":
                requireArgs(args);
                replyResult(replyProxy, requestId, nativeBridge.closeSession());
                return;
            case "enableBlackout":
                requireArgs(args);
                replyResult(replyProxy, requestId, nativeBridge.enableBlackout());
                return;
            case "disableBlackout":
                requireArgs(args);
                replyResult(replyProxy, requestId, nativeBridge.disableBlackout());
                return;
            default:
                // parseRequest already applies the explicit allowlist.
                throw new IllegalArgumentException("operation_invalid");
        }
    }

    private static void requireArgs(JSONObject args, String... names) throws Exception {
        Set<String> expected = immutableSet(names);
        if (args == null || args.length() != expected.size() || !hasOnlyKeys(args, expected)) {
            throw new IllegalArgumentException("args_fields_invalid");
        }
    }

    private static String stringArg(JSONObject args, String name, int maxChars) throws Exception {
        Object value = args.get(name);
        if (!(value instanceof String)) {
            throw new IllegalArgumentException("arg_type_invalid");
        }
        String result = (String) value;
        if (result.length() > maxChars) {
            throw new IllegalArgumentException("arg_size_invalid");
        }
        return result;
    }

    private static boolean hasOnlyKeys(JSONObject value, Set<String> allowed) {
        Iterator<String> keys = value.keys();
        while (keys.hasNext()) {
            if (!allowed.contains(keys.next())) {
                return false;
            }
        }
        return true;
    }

    private static Set<String> immutableSet(String... values) {
        return Collections.unmodifiableSet(new HashSet<>(Arrays.asList(values)));
    }

    private static void replyNativeJson(
            JavaScriptReplyProxy replyProxy,
            String requestId,
            String nativeJson
    ) throws Exception {
        JSONObject result = new JSONObject(nativeJson);
        Object ok = result.opt("ok");
        if (ok instanceof Boolean && !((Boolean) ok)) {
            replyError(replyProxy, requestId, "operation_failed");
            return;
        }
        replyResult(replyProxy, requestId, result);
    }

    private static void replyResult(
            JavaScriptReplyProxy replyProxy,
            String requestId,
            Object result
    ) {
        String response;
        try {
            response = new JSONObject()
                    .put("version", PROTOCOL_VERSION)
                    .put("requestId", requestId)
                    .put("ok", true)
                    .put("result", result)
                    .toString();
        } catch (Exception ignored) {
            response = "{\"version\":1,\"requestId\":\""
                    + requestId
                    + "\",\"ok\":false,\"error\":\"bridge_failed\"}";
        }
        replyProxy.postMessage(response);
    }

    private static void replyError(
            JavaScriptReplyProxy replyProxy,
            String requestId,
            String error
    ) {
        String response;
        try {
            response = new JSONObject()
                    .put("version", PROTOCOL_VERSION)
                    .put("requestId", requestId == null ? "" : requestId)
                    .put("ok", false)
                    .put("error", error)
                    .toString();
        } catch (Exception ignored) {
            response = "{\"version\":1,\"requestId\":\"\",\"ok\":false,\"error\":\"bridge_failed\"}";
        }
        replyProxy.postMessage(response);
    }
}
