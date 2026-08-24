package de.kgg.app;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import android.os.Looper;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyStore;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

/**
 * Native-only live-sync key bridge. It never shares the release/GitHub bridge
 * state and has no plaintext persistence or plaintext fallback.
 */
public final class KggLiveKeyBridge {
    public static final String JS_NAME = "KGGLiveKey";

    private static final int PROTOCOL_VERSION = 1;
    private static final int KEY_VERSION = 1;
    private static final int MAX_PAIRINGS = 32;
    private static final int MAX_STATE_BYTES = 64 * 1024;
    private static final String PREFS = "kgg_live_key_private_v1";
    private static final String PREF_STATE = "state";
    private static final String MASTER_KEY_ALIAS = "kgg_live_key_master_v1";
    private static final byte[] STATE_AAD =
            "KGGLiveKeyStateV1".getBytes(StandardCharsets.UTF_8);
    private static final Set<String> STATE_KEYS = new HashSet<>(Arrays.asList("v", "pairings"));
    private static final Set<String> PAIRING_KEYS = new HashSet<>(Arrays.asList(
            "pairingId", "pairingSecret", "keyVersion", "createdAt", "qrExported"
    ));
    private static final Set<String> OFFER_KEYS = new HashSet<>(Arrays.asList(
            "v", "pairingId", "role", "sessionId", "publicKey", "mac"
    ));

    private final Activity activity;
    private final Context appContext;
    private final WebView webView;
    private final SharedPreferences preferences;
    private final SecureRandom random;
    private final boolean cryptoCoreAvailable;
    private volatile boolean bridgeActive;
    private volatile String trustedBaseUrl = "";
    private volatile BlackoutSnapshot blackoutSnapshot;
    private volatile View blackoutView;
    private boolean cryptoUnavailable;

    private KeyPair ephemeralKeyPair;
    private String activePlanKey;
    private String activeRole;
    private byte[] activePairingId;
    private byte[] activeSessionId;
    private final KggLiveSessionSecrets sessionSecrets = new KggLiveSessionSecrets();

    public KggLiveKeyBridge(Activity activity, WebView webView) {
        if (activity == null || webView == null) {
            throw new IllegalArgumentException("bridge_context_invalid");
        }
        this.activity = activity;
        this.appContext = activity.getApplicationContext();
        this.webView = webView;
        this.preferences = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        SecureRandom candidate = null;
        boolean supported = false;
        try {
            candidate = KggLiveCryptoCore.newSecureRandom();
            supported = KggLiveCryptoCore.isSupported();
        } catch (Exception ignored) {
            // Keep the bridge unavailable. There is intentionally no fallback.
        }
        this.random = candidate;
        this.cryptoCoreAvailable = supported;
        this.cryptoUnavailable = !supported;
    }

    /** Called only after a trusted local KGG document finished loading. */
    void activateForPage(String pageUrl, String expectedBaseUrl) {
        if (!KggLiveBridgePolicy.isTrustedPageUrl(pageUrl, expectedBaseUrl)) {
            deactivateForPage();
            return;
        }
        synchronized (this) {
            trustedBaseUrl = expectedBaseUrl;
            bridgeActive = true;
        }
    }

    /** Remove the bridge's authority before a WebView navigation. */
    void deactivateForPage() {
        synchronized (this) {
            bridgeActive = false;
            trustedBaseUrl = "";
            clearSessionLocked();
        }
        disableBlackout();
    }

    void onPause() {
        synchronized (this) {
            clearSessionLocked();
        }
        disableBlackout();
    }

    void onError() {
        deactivateForPage();
    }

    void onDestroy() {
        deactivateForPage();
    }

    @JavascriptInterface
    public synchronized String getCapabilities() {
        if (!isTrustedBridgeCallLocked()) {
            return capabilities(false, "bridge_inactive");
        }
        if (!ensureCryptoAvailableLocked()) {
            return capabilities(false, "crypto_unavailable");
        }
        return capabilities(true, "");
    }

    @JavascriptInterface
    public synchronized boolean hasPairing(String planKey) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return false;
        }
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            JSONObject state = loadStateLocked();
            return state.getJSONObject("pairings").has(checkedPlanKey);
        } catch (Exception ignored) {
            return false;
        }
    }

    /**
     * Creates a pairing and returns its QR payload exactly once. Existing
     * pairings are never exported by this method.
     */
    @JavascriptInterface
    public synchronized String createPairing(String planKey) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return error("pairing_unavailable");
        }
        PairingMaterial material = null;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            JSONObject state = loadStateLocked();
            JSONObject pairings = state.getJSONObject("pairings");
            if (pairings.has(checkedPlanKey)) {
                return error("pairing_exists");
            }
            if (pairings.length() >= MAX_PAIRINGS) {
                return error("pairing_limit");
            }
            material = newPairingLocked();
            pairings.put(checkedPlanKey, material.toJson());
            String pairingPackage = pairingPackage(material);
            if (!saveStateLocked(state)) {
                return error("pairing_persist_failed");
            }
            return pairingResponse(pairingPackage);
        } catch (Exception ignored) {
            return error("pairing_failed");
        } finally {
            if (material != null) {
                material.clear();
            }
        }
    }

    /** Replaces the local pairing and returns only the new one-time QR payload. */
    @JavascriptInterface
    public synchronized String rotatePairing(String planKey) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return error("pairing_unavailable");
        }
        PairingMaterial material = null;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            JSONObject state = loadStateLocked();
            JSONObject pairings = state.getJSONObject("pairings");
            if (!pairings.has(checkedPlanKey) && pairings.length() >= MAX_PAIRINGS) {
                return error("pairing_limit");
            }
            closeSessionForPlanLocked(checkedPlanKey);
            material = newPairingLocked();
            pairings.put(checkedPlanKey, material.toJson());
            String pairingPackage = pairingPackage(material);
            if (!saveStateLocked(state)) {
                return error("pairing_persist_failed");
            }
            return pairingResponse(pairingPackage);
        } catch (Exception ignored) {
            return error("pairing_rotate_failed");
        } finally {
            if (material != null) {
                material.clear();
            }
        }
    }

    @JavascriptInterface
    public synchronized boolean deletePairing(String planKey) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return false;
        }
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            JSONObject state = loadStateLocked();
            JSONObject pairings = state.getJSONObject("pairings");
            if (!pairings.has(checkedPlanKey)) {
                return false;
            }
            pairings.remove(checkedPlanKey);
            if (!saveStateLocked(state)) {
                return false;
            }
            closeSessionForPlanLocked(checkedPlanKey);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    @JavascriptInterface
    public synchronized String computeJoinHmac(
            String planKey,
            String sessionIdBase64Url,
            String sessionSaltBase64Url
    ) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return error("join_unavailable");
        }
        byte[] sessionId = null;
        byte[] sessionSalt = null;
        PairingMaterial material = null;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            sessionId = KggLiveCryptoCore.decodeBase64Url(
                    sessionIdBase64Url,
                    KggLiveCryptoCore.SESSION_ID_BYTES,
                    KggLiveCryptoCore.SESSION_ID_BYTES
            );
            sessionSalt = KggLiveCryptoCore.decodeBase64Url(
                    sessionSaltBase64Url,
                    KggLiveCryptoCore.SESSION_SALT_BYTES,
                    KggLiveCryptoCore.SESSION_SALT_BYTES
            );
            material = loadPairingMaterialLocked(loadStateLocked(), checkedPlanKey);
            byte[] hmac = KggLiveCryptoCore.joinHmac(material.secret, sessionId, sessionSalt);
            try {
                return new JSONObject().put("ok", true)
                        .put("hmac", KggLiveCryptoCore.base64Url(hmac))
                        .toString();
            } finally {
                KggLiveCryptoCore.clear(hmac);
            }
        } catch (Exception ignored) {
            return error("join_failed");
        } finally {
            KggLiveCryptoCore.clear(sessionId, sessionSalt);
            if (material != null) {
                material.clear();
            }
        }
    }

    /** Creates a P-256 offer; its private key never enters the WebView. */
    @JavascriptInterface
    public synchronized String createPeerOffer(
            String planKey,
            String role,
            String sessionIdBase64Url
    ) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return error("offer_unavailable");
        }
        PairingMaterial material = null;
        byte[] sessionId = null;
        KeyPair newKeyPair = null;
        byte[] publicKey = null;
        byte[] mac = null;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            requireRole(role);
            sessionId = KggLiveCryptoCore.decodeBase64Url(
                    sessionIdBase64Url,
                    KggLiveCryptoCore.SESSION_ID_BYTES,
                    KggLiveCryptoCore.SESSION_ID_BYTES
            );
            material = loadPairingMaterialLocked(loadStateLocked(), checkedPlanKey);
            newKeyPair = KggLiveCryptoCore.generateP256KeyPair(random);
            publicKey = KggLiveCryptoCore.rawPublicKey(newKeyPair.getPublic());
            mac = KggLiveCryptoCore.peerOfferMac(
                    material.secret, material.id, role, sessionId, publicKey
            );
            JSONObject offer = new JSONObject()
                    .put("v", PROTOCOL_VERSION)
                    .put("pairingId", material.idBase64Url)
                    .put("role", role)
                    .put("sessionId", sessionIdBase64Url)
                    .put("publicKey", KggLiveCryptoCore.base64Url(publicKey))
                    .put("mac", KggLiveCryptoCore.base64Url(mac));
            clearSessionLocked();
            ephemeralKeyPair = newKeyPair;
            newKeyPair = null;
            activePlanKey = checkedPlanKey;
            activeRole = role;
            activePairingId = Arrays.copyOf(material.id, material.id.length);
            activeSessionId = Arrays.copyOf(sessionId, sessionId.length);
            return offer.toString();
        } catch (Exception ignored) {
            return error("offer_failed");
        } finally {
            if (newKeyPair != null) {
                KggLiveCryptoCore.destroy(newKeyPair.getPrivate());
            }
            KggLiveCryptoCore.clear(sessionId, publicKey, mac);
            if (material != null) {
                material.clear();
            }
        }
    }

    @JavascriptInterface
    public synchronized boolean verifyPeerOffer(
            String planKey,
            String localRole,
            String sessionIdBase64Url,
            String offerJson
    ) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return false;
        }
        byte[] sessionId = null;
        PairingMaterial material = null;
        PeerOffer offer = null;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            requireRole(localRole);
            sessionId = KggLiveCryptoCore.decodeBase64Url(
                    sessionIdBase64Url,
                    KggLiveCryptoCore.SESSION_ID_BYTES,
                    KggLiveCryptoCore.SESSION_ID_BYTES
            );
            material = loadPairingMaterialLocked(loadStateLocked(), checkedPlanKey);
            offer = parsePeerOffer(offerJson);
            return verifyPeerOfferLocked(material, localRole, sessionId, offer);
        } catch (Exception ignored) {
            return false;
        } finally {
            KggLiveCryptoCore.clear(sessionId);
            if (material != null) {
                material.clear();
            }
            if (offer != null) {
                offer.clear();
            }
        }
    }

    /** Verifies the peer offer and stores only the derived AES session key. */
    @JavascriptInterface
    public synchronized String deriveSessionKey(
            String planKey,
            String sessionSaltBase64Url,
            String offerJson
    ) {
        if (!isTrustedBridgeCallLocked() || !ensureCryptoAvailableLocked()) {
            return error("session_unavailable");
        }
        byte[] sessionSalt = null;
        byte[] sharedSecret = null;
        byte[] info = null;
        byte[] derived = null;
        byte[] expectedMac = null;
        PairingMaterial material = null;
        PeerOffer offer = null;
        boolean stored = false;
        try {
            String checkedPlanKey = requirePlanKey(planKey);
            sessionSalt = KggLiveCryptoCore.decodeBase64Url(
                    sessionSaltBase64Url,
                    KggLiveCryptoCore.SESSION_SALT_BYTES,
                    KggLiveCryptoCore.SESSION_SALT_BYTES
            );
            if (!checkedPlanKey.equals(activePlanKey)
                    || ephemeralKeyPair == null
                    || !KggLiveBridgePolicy.isRole(activeRole)
                    || activePairingId == null
                    || activeSessionId == null) {
                throw new IllegalStateException("session_context_invalid");
            }
            material = loadPairingMaterialLocked(loadStateLocked(), checkedPlanKey);
            if (!KggLiveCryptoCore.constantTimeEquals(material.id, activePairingId)) {
                throw new IllegalStateException("pairing_changed");
            }
            offer = parsePeerOffer(offerJson);
            if (!KggLiveCryptoCore.constantTimeEquals(offer.pairingId, activePairingId)
                    || !KggLiveCryptoCore.constantTimeEquals(offer.sessionId, activeSessionId)
                    || !KggLiveBridgePolicy.oppositeRole(activeRole).equals(offer.role)) {
                throw new IllegalStateException("offer_context_invalid");
            }
            expectedMac = KggLiveCryptoCore.peerOfferMac(
                    material.secret,
                    material.id,
                    offer.role,
                    offer.sessionId,
                    offer.publicKey
            );
            if (!KggLiveCryptoCore.constantTimeEquals(expectedMac, offer.mac)) {
                throw new IllegalStateException("offer_auth_invalid");
            }
            PublicKey peerPublicKey = KggLiveCryptoCore.publicKeyFromRaw(offer.publicKey);
            sharedSecret = KggLiveCryptoCore.ecdh(
                    ephemeralKeyPair.getPrivate(),
                    peerPublicKey
            );
            byte[] therapistRole = KggLiveCryptoCore.utf8("therapist", 16);
            byte[] patientRole = KggLiveCryptoCore.utf8("patient", 16);
            try {
                info = KggLiveCryptoCore.concat(
                        "KGG-LIVE-SESSION-V1".getBytes(StandardCharsets.UTF_8),
                        activePairingId,
                        activeSessionId,
                        therapistRole,
                        patientRole
                );
            } finally {
                KggLiveCryptoCore.clear(therapistRole, patientRole);
            }
            derived = KggLiveCryptoCore.hkdfSha256(
                    sharedSecret,
                    sessionSalt,
                    info,
                    KggLiveCryptoCore.AES_KEY_BYTES
            );
            clearSessionKeyOnlyLocked();
            sessionSecrets.replace(derived);
            derived = null;
            stored = true;
            KggLiveCryptoCore.destroy(ephemeralKeyPair.getPrivate());
            ephemeralKeyPair = null;
            KggLiveCryptoCore.clear(activePairingId, activeSessionId);
            activePairingId = null;
            activeSessionId = null;
            activeRole = null;
            return ok();
        } catch (Exception ignored) {
            clearSessionLocked();
            return error("session_failed");
        } finally {
            KggLiveCryptoCore.clear(sessionSalt, sharedSecret, info, expectedMac, derived);
            if (material != null) {
                material.clear();
            }
            if (offer != null) {
                offer.clear();
            }
            if (!stored && derived != null) {
                KggLiveCryptoCore.clear(derived);
            }
        }
    }

    @JavascriptInterface
    public synchronized String encrypt(
            String planKey,
            String aadBase64Url,
            String plaintextBase64Url
    ) {
        if (!isTrustedBridgeCallLocked() || !hasActiveSessionLocked(planKey)) {
            return error("encrypt_unavailable");
        }
        byte[] aad = null;
        byte[] plaintext = null;
        byte[] keyBytes = null;
        KggLiveCryptoCore.GcmResult result = null;
        try {
            aad = KggLiveCryptoCore.decodeBase64Url(
                    aadBase64Url,
                    -1,
                    KggLiveCryptoCore.MAX_AAD_BYTES
            );
            if (aad.length < 1) {
                throw new IllegalArgumentException("aad_required");
            }
            plaintext = KggLiveCryptoCore.decodeBase64Url(
                    plaintextBase64Url,
                    -1,
                    KggLiveCryptoCore.MAX_FRAME_CIPHERTEXT_BYTES
                            - KggLiveCryptoCore.GCM_TAG_BYTES
            );
            keyBytes = sessionSecrets.copy();
            result = KggLiveCryptoCore.encrypt(
                    new SecretKeySpec(keyBytes, "AES"), aad, plaintext, random
            );
            return new JSONObject()
                    .put("ok", true)
                    .put("nonce", KggLiveCryptoCore.base64Url(result.nonce))
                    .put("ciphertext", KggLiveCryptoCore.base64Url(result.ciphertext))
                    .toString();
        } catch (Exception ignored) {
            return error("encrypt_failed");
        } finally {
            KggLiveCryptoCore.clear(aad, plaintext, keyBytes);
            if (result != null) {
                KggLiveCryptoCore.clear(result.nonce, result.ciphertext);
            }
        }
    }

    @JavascriptInterface
    public synchronized String decrypt(
            String planKey,
            String nonceBase64Url,
            String aadBase64Url,
            String ciphertextBase64Url
    ) {
        if (!isTrustedBridgeCallLocked() || !hasActiveSessionLocked(planKey)) {
            return error("decrypt_unavailable");
        }
        byte[] nonce = null;
        byte[] aad = null;
        byte[] ciphertext = null;
        byte[] plaintext = null;
        byte[] keyBytes = null;
        try {
            nonce = KggLiveCryptoCore.decodeBase64Url(
                    nonceBase64Url,
                    KggLiveCryptoCore.GCM_NONCE_BYTES,
                    KggLiveCryptoCore.GCM_NONCE_BYTES
            );
            aad = KggLiveCryptoCore.decodeBase64Url(
                    aadBase64Url,
                    -1,
                    KggLiveCryptoCore.MAX_AAD_BYTES
            );
            if (aad.length < 1) {
                throw new IllegalArgumentException("aad_required");
            }
            ciphertext = KggLiveCryptoCore.decodeBase64Url(
                    ciphertextBase64Url,
                    -1,
                    KggLiveCryptoCore.MAX_FRAME_CIPHERTEXT_BYTES
            );
            keyBytes = sessionSecrets.copy();
            plaintext = KggLiveCryptoCore.decrypt(
                    new SecretKeySpec(keyBytes, "AES"), aad, nonce, ciphertext
            );
            String encodedPlaintext = KggLiveCryptoCore.base64Url(plaintext);
            return new JSONObject()
                    .put("ok", true)
                    .put("plaintext", encodedPlaintext)
                    .toString();
        } catch (Exception ignored) {
            return error("decrypt_failed");
        } finally {
            KggLiveCryptoCore.clear(nonce, aad, ciphertext, plaintext, keyBytes);
        }
    }

    @JavascriptInterface
    public synchronized boolean closeSession() {
        clearSessionLocked();
        return true;
    }

    /** Debug/test-only black immersive cover; production builds always reject it. */
    @JavascriptInterface
    public boolean enableBlackout() {
        if (!BuildConfig.DEBUG || !isCurrentPageTrusted()) {
            return false;
        }
        if (blackoutSnapshot != null) {
            return true;
        }
        AtomicBoolean success = new AtomicBoolean(false);
        runOnUiThreadAndWait(() -> {
            if (blackoutSnapshot != null) {
                success.set(true);
                return;
            }
            Window window = activity.getWindow();
            ViewGroup root = activity.findViewById(android.R.id.content);
            if (window == null || root == null) {
                return;
            }
            BlackoutSnapshot snapshot = new BlackoutSnapshot(
                    window.getAttributes().flags,
                    window.getAttributes().screenBrightness,
                    window.getDecorView().getSystemUiVisibility()
            );
            View cover = new View(activity);
            cover.setBackgroundColor(Color.BLACK);
            cover.setClickable(true);
            cover.setFocusable(true);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                cover.setElevation(1000.0f);
            }
            try {
                root.addView(cover, new ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                ));
                WindowManager.LayoutParams attributes = window.getAttributes();
                attributes.screenBrightness = 0.0f;
                window.setAttributes(attributes);
                window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                window.getDecorView().setSystemUiVisibility(
                        snapshot.systemUiVisibility
                                | View.SYSTEM_UI_FLAG_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                );
                blackoutSnapshot = snapshot;
                blackoutView = cover;
                success.set(true);
            } catch (Exception ignored) {
                blackoutSnapshot = snapshot;
                blackoutView = cover;
                try {
                    root.removeView(cover);
                } catch (Exception ignoredRemoval) {
                    // Keep the reference so a later lifecycle restore can retry.
                }
                try {
                    restoreWindow(window, snapshot);
                } catch (Exception ignoredRestore) {
                    // Keep the snapshot for a later lifecycle restore attempt.
                }
            }
        });
        return success.get();
    }

    @JavascriptInterface
    public boolean disableBlackout() {
        AtomicBoolean success = new AtomicBoolean(true);
        runOnUiThreadAndWait(() -> {
            BlackoutSnapshot snapshot = blackoutSnapshot;
            View cover = blackoutView;
            Window window = activity.getWindow();
            boolean removed = true;
            boolean restored = true;
            try {
                if (cover != null && cover.getParent() instanceof ViewGroup) {
                    ((ViewGroup) cover.getParent()).removeView(cover);
                }
            } catch (Exception ignored) {
                removed = false;
            }
            try {
                if (window != null && snapshot != null) {
                    restoreWindow(window, snapshot);
                }
            } catch (Exception ignored) {
                restored = false;
            }
            if (removed && restored) {
                blackoutView = null;
                blackoutSnapshot = null;
            } else {
                success.set(false);
            }
        });
        return success.get();
    }

    private boolean isTrustedBridgeCallLocked() {
        return isCurrentPageTrusted();
    }

    private boolean isCurrentPageTrusted() {
        if (!bridgeActive) {
            return false;
        }
        try {
            return KggLiveBridgePolicy.isTrustedPageUrl(webView.getUrl(), trustedBaseUrl);
        } catch (Exception ignored) {
            return false;
        }
    }

    private boolean ensureCryptoAvailableLocked() {
        if (cryptoUnavailable || random == null || !cryptoCoreAvailable) {
            cryptoUnavailable = true;
            return false;
        }
        try {
            getMasterKeyLocked();
            loadStateLocked();
            return true;
        } catch (Exception ignored) {
            cryptoUnavailable = true;
            clearSessionLocked();
            return false;
        }
    }

    private SecretKey getMasterKeyLocked() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (!store.containsAlias(MASTER_KEY_ALIAS)) {
            KeyGenerator generator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES,
                    "AndroidKeyStore"
            );
            generator.init(new KeyGenParameterSpec.Builder(
                    MASTER_KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
            ).setKeySize(256)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setRandomizedEncryptionRequired(true)
                    .build());
            generator.generateKey();
        }
        KeyStore.Entry entry = store.getEntry(MASTER_KEY_ALIAS, null);
        if (!(entry instanceof KeyStore.SecretKeyEntry)) {
            throw new IllegalStateException("master_key_type_invalid");
        }
        SecretKey key = ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        if (key == null || !"AES".equalsIgnoreCase(key.getAlgorithm())) {
            throw new IllegalStateException("master_key_invalid");
        }
        return key;
    }

    private JSONObject loadStateLocked() throws Exception {
        String envelope = preferences.getString(PREF_STATE, "");
        if (envelope == null || envelope.isEmpty()) {
            return emptyState();
        }
        String[] parts = envelope.split("\\.", -1);
        if (parts.length != 2) {
            throw new IllegalStateException("state_envelope_invalid");
        }
        byte[] nonce = null;
        byte[] ciphertext = null;
        byte[] plaintext = null;
        try {
            nonce = KggLiveCryptoCore.decodeBase64Url(
                    parts[0],
                    KggLiveCryptoCore.GCM_NONCE_BYTES,
                    KggLiveCryptoCore.GCM_NONCE_BYTES
            );
            ciphertext = KggLiveCryptoCore.decodeBase64Url(
                    parts[1],
                    -1,
                    MAX_STATE_BYTES
            );
            plaintext = KggLiveCryptoCore.decrypt(
                    getMasterKeyLocked(), STATE_AAD, nonce, ciphertext
            );
            if (plaintext.length > MAX_STATE_BYTES) {
                throw new IllegalStateException("state_size_invalid");
            }
            JSONObject state = new JSONObject(new String(plaintext, StandardCharsets.UTF_8));
            validateState(state);
            return state;
        } finally {
            KggLiveCryptoCore.clear(nonce, ciphertext, plaintext);
        }
    }

    private boolean saveStateLocked(JSONObject state) throws Exception {
        validateState(state);
        byte[] plaintext = state.toString().getBytes(StandardCharsets.UTF_8);
        if (plaintext.length > MAX_STATE_BYTES
                || plaintext.length > KggLiveCryptoCore.MAX_FRAME_CIPHERTEXT_BYTES
                        - KggLiveCryptoCore.GCM_TAG_BYTES) {
            KggLiveCryptoCore.clear(plaintext);
            return false;
        }
        KggLiveCryptoCore.GcmResult encrypted = null;
        try {
            encrypted = KggLiveCryptoCore.encrypt(
                    getMasterKeyLocked(), STATE_AAD, plaintext, random
            );
            String envelope = KggLiveCryptoCore.base64Url(encrypted.nonce)
                    + "."
                    + KggLiveCryptoCore.base64Url(encrypted.ciphertext);
            return preferences.edit().putString(PREF_STATE, envelope).commit();
        } finally {
            KggLiveCryptoCore.clear(plaintext);
            if (encrypted != null) {
                KggLiveCryptoCore.clear(encrypted.nonce, encrypted.ciphertext);
            }
        }
    }

    private void validateState(JSONObject state) throws Exception {
        if (state == null || !hasOnlyKeys(state, STATE_KEYS)
                || state.optInt("v", 0) != PROTOCOL_VERSION) {
            throw new IllegalStateException("state_invalid");
        }
        JSONObject pairings = state.optJSONObject("pairings");
        if (pairings == null || pairings.length() > MAX_PAIRINGS) {
            throw new IllegalStateException("pairings_invalid");
        }
        Iterator<String> keys = pairings.keys();
        while (keys.hasNext()) {
            String planKey = keys.next();
            if (!KggLiveBridgePolicy.isPlanKey(planKey)) {
                throw new IllegalStateException("plan_key_invalid");
            }
            validatePairing(pairings.optJSONObject(planKey));
        }
    }

    private void validatePairing(JSONObject pairing) throws Exception {
        if (pairing == null || !hasOnlyKeys(pairing, PAIRING_KEYS)
                || pairing.optInt("keyVersion", 0) != KEY_VERSION
                || !pairing.optBoolean("qrExported", false)) {
            throw new IllegalStateException("pairing_record_invalid");
        }
        byte[] pairingId = null;
        byte[] pairingSecret = null;
        try {
            pairingId = KggLiveCryptoCore.decodeBase64Url(
                    pairing.optString("pairingId", ""),
                    KggLiveCryptoCore.PAIRING_ID_BYTES,
                    KggLiveCryptoCore.PAIRING_ID_BYTES
            );
            pairingSecret = KggLiveCryptoCore.decodeBase64Url(
                    pairing.optString("pairingSecret", ""),
                    KggLiveCryptoCore.PAIRING_SECRET_BYTES,
                    KggLiveCryptoCore.PAIRING_SECRET_BYTES
            );
        } finally {
            KggLiveCryptoCore.clear(pairingId, pairingSecret);
        }
        String createdAt = pairing.optString("createdAt", "");
        if (createdAt.length() > 64 || !createdAt.endsWith("Z")) {
            throw new IllegalStateException("created_at_invalid");
        }
        Instant.parse(createdAt);
    }

    private PairingMaterial loadPairingMaterialLocked(JSONObject state, String planKey)
            throws Exception {
        JSONObject pairing = state.getJSONObject("pairings").optJSONObject(planKey);
        if (pairing == null) {
            throw new IllegalStateException("pairing_missing");
        }
        byte[] id = null;
        byte[] secret = null;
        try {
            id = KggLiveCryptoCore.decodeBase64Url(
                    pairing.getString("pairingId"),
                    KggLiveCryptoCore.PAIRING_ID_BYTES,
                    KggLiveCryptoCore.PAIRING_ID_BYTES
            );
            secret = KggLiveCryptoCore.decodeBase64Url(
                    pairing.getString("pairingSecret"),
                    KggLiveCryptoCore.PAIRING_SECRET_BYTES,
                    KggLiveCryptoCore.PAIRING_SECRET_BYTES
            );
            return new PairingMaterial(
                    id,
                    secret,
                    pairing.getString("createdAt")
            );
        } catch (Exception error) {
            KggLiveCryptoCore.clear(id, secret);
            throw error;
        }
    }

    private PairingMaterial newPairingLocked() {
        byte[] id = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_ID_BYTES
        );
        byte[] secret = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_SECRET_BYTES
        );
        return new PairingMaterial(id, secret, Instant.now().toString());
    }

    private String pairingPackage(PairingMaterial material) {
        String canonicalJson = "{\"v\":1,\"pairingId\":\""
                + material.idBase64Url
                + "\",\"pairingSecret\":\""
                + material.secretBase64Url
                + "\",\"keyVersion\":1,\"createdAt\":\""
                + material.createdAt
                + "\"}";
        return "KGGLIVEPAIR1:" + KggLiveCryptoCore.base64Url(
                canonicalJson.getBytes(StandardCharsets.UTF_8)
        );
    }

    private PeerOffer parsePeerOffer(String offerJson) throws Exception {
        if (offerJson == null || offerJson.length() > KggLiveCryptoCore.MAX_OFFER_BYTES) {
            throw new IllegalStateException("offer_size_invalid");
        }
        JSONObject value = new JSONObject(offerJson);
        if (!hasOnlyKeys(value, OFFER_KEYS) || value.optInt("v", 0) != PROTOCOL_VERSION) {
            throw new IllegalStateException("offer_invalid");
        }
        String role = value.getString("role");
        requireRole(role);
        byte[] pairingId = KggLiveCryptoCore.decodeBase64Url(
                value.getString("pairingId"),
                KggLiveCryptoCore.PAIRING_ID_BYTES,
                KggLiveCryptoCore.PAIRING_ID_BYTES
        );
        byte[] sessionId = KggLiveCryptoCore.decodeBase64Url(
                value.getString("sessionId"),
                KggLiveCryptoCore.SESSION_ID_BYTES,
                KggLiveCryptoCore.SESSION_ID_BYTES
        );
        byte[] publicKey = KggLiveCryptoCore.decodeBase64Url(
                value.getString("publicKey"),
                KggLiveCryptoCore.P256_PUBLIC_KEY_BYTES,
                KggLiveCryptoCore.P256_PUBLIC_KEY_BYTES
        );
        byte[] mac = KggLiveCryptoCore.decodeBase64Url(
                value.getString("mac"),
                KggLiveCryptoCore.HMAC_BYTES,
                KggLiveCryptoCore.HMAC_BYTES
        );
        return new PeerOffer(
                pairingId,
                role,
                sessionId,
                publicKey,
                mac
        );
    }

    private boolean verifyPeerOfferLocked(
            PairingMaterial material,
            String localRole,
            byte[] sessionId,
            PeerOffer offer
    ) throws Exception {
        if (!KggLiveBridgePolicy.oppositeRole(localRole).equals(offer.role)
                || !KggLiveCryptoCore.constantTimeEquals(material.id, offer.pairingId)
                || !KggLiveCryptoCore.constantTimeEquals(sessionId, offer.sessionId)) {
            return false;
        }
        byte[] expected = KggLiveCryptoCore.peerOfferMac(
                material.secret,
                material.id,
                offer.role,
                offer.sessionId,
                offer.publicKey
        );
        try {
            return KggLiveCryptoCore.constantTimeEquals(expected, offer.mac);
        } finally {
            KggLiveCryptoCore.clear(expected);
        }
    }

    private boolean hasActiveSessionLocked(String planKey) {
        return sessionSecrets.isActive()
                && KggLiveBridgePolicy.isPlanKey(planKey)
                && planKey.equals(activePlanKey);
    }

    private void closeSessionForPlanLocked(String planKey) {
        if (planKey.equals(activePlanKey)) {
            clearSessionLocked();
        }
    }

    private void clearSessionLocked() {
        clearSessionKeyOnlyLocked();
        if (ephemeralKeyPair != null) {
            KggLiveCryptoCore.destroy(ephemeralKeyPair.getPrivate());
        }
        ephemeralKeyPair = null;
        activePlanKey = null;
        activeRole = null;
        KggLiveCryptoCore.clear(activePairingId, activeSessionId);
        activePairingId = null;
        activeSessionId = null;
    }

    private void clearSessionKeyOnlyLocked() {
        sessionSecrets.clear();
    }

    private String requirePlanKey(String planKey) {
        if (!KggLiveBridgePolicy.isPlanKey(planKey)) {
            throw new IllegalArgumentException("plan_key_invalid");
        }
        return planKey;
    }

    private void requireRole(String role) {
        if (!KggLiveBridgePolicy.isRole(role)) {
            throw new IllegalArgumentException("role_invalid");
        }
    }

    private static boolean hasOnlyKeys(JSONObject value, Set<String> allowed) {
        if (value == null || allowed == null) {
            return false;
        }
        Iterator<String> keys = value.keys();
        while (keys.hasNext()) {
            if (!allowed.contains(keys.next())) {
                return false;
            }
        }
        return true;
    }

    private static JSONObject emptyState() throws Exception {
        return new JSONObject()
                .put("v", PROTOCOL_VERSION)
                .put("pairings", new JSONObject());
    }

    private static String capabilities(boolean available, String error) {
        try {
            JSONObject value = new JSONObject()
                    .put("available", available)
                    .put("protocolVersion", PROTOCOL_VERSION)
                    .put("keyVersion", KEY_VERSION)
                    .put("pairingExport", "create-or-rotate-once");
            if (error != null && !error.isEmpty()) {
                value.put("error", error);
            }
            return value.toString();
        } catch (Exception ignored) {
            return available ? "{\"available\":true}" : "{\"available\":false}";
        }
    }

    private static String pairingResponse(String pairingPackage) {
        try {
            return new JSONObject().put("ok", true)
                    .put("pairing", pairingPackage)
                    .toString();
        } catch (Exception ignored) {
            return error("pairing_response_failed");
        }
    }

    private static String ok() {
        return "{\"ok\":true}";
    }

    private static String error(String code) {
        try {
            return new JSONObject().put("ok", false).put("error", code).toString();
        } catch (Exception ignored) {
            return "{\"ok\":false,\"error\":\"bridge_failed\"}";
        }
    }

    private void runOnUiThreadAndWait(UiWork work) {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            try {
                work.run();
            } catch (Exception ignored) {
            }
            return;
        }
        CountDownLatch latch = new CountDownLatch(1);
        try {
            activity.runOnUiThread(() -> {
                try {
                    work.run();
                } catch (Exception ignored) {
                } finally {
                    latch.countDown();
                }
            });
        } catch (Exception ignored) {
            return;
        }
        try {
            latch.await(3, TimeUnit.SECONDS);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    private void restoreWindow(Window window, BlackoutSnapshot snapshot) {
        window.setFlags(snapshot.windowFlags, -1);
        WindowManager.LayoutParams attributes = window.getAttributes();
        attributes.screenBrightness = snapshot.screenBrightness;
        window.setAttributes(attributes);
        window.getDecorView().setSystemUiVisibility(snapshot.systemUiVisibility);
    }

    private interface UiWork {
        void run() throws Exception;
    }

    private static final class PairingMaterial {
        final byte[] id;
        final byte[] secret;
        final String idBase64Url;
        final String secretBase64Url;
        final String createdAt;

        PairingMaterial(byte[] id, byte[] secret, String createdAt) {
            this.id = id;
            this.secret = secret;
            this.idBase64Url = KggLiveCryptoCore.base64Url(id);
            this.secretBase64Url = KggLiveCryptoCore.base64Url(secret);
            this.createdAt = createdAt;
        }

        JSONObject toJson() throws Exception {
            return new JSONObject()
                    .put("pairingId", idBase64Url)
                    .put("pairingSecret", secretBase64Url)
                    .put("keyVersion", KEY_VERSION)
                    .put("createdAt", createdAt)
                    .put("qrExported", true);
        }

        void clear() {
            KggLiveCryptoCore.clear(id, secret);
        }
    }

    private static final class PeerOffer {
        final byte[] pairingId;
        final String role;
        final byte[] sessionId;
        final byte[] publicKey;
        final byte[] mac;

        PeerOffer(byte[] pairingId, String role, byte[] sessionId, byte[] publicKey, byte[] mac) {
            this.pairingId = pairingId;
            this.role = role;
            this.sessionId = sessionId;
            this.publicKey = publicKey;
            this.mac = mac;
        }

        void clear() {
            KggLiveCryptoCore.clear(pairingId, sessionId, publicKey, mac);
        }
    }

    private static final class BlackoutSnapshot {
        final int windowFlags;
        final float screenBrightness;
        final int systemUiVisibility;

        BlackoutSnapshot(int windowFlags, float screenBrightness, int systemUiVisibility) {
            this.windowFlags = windowFlags;
            this.screenBrightness = screenBrightness;
            this.systemUiVisibility = systemUiVisibility;
        }
    }
}
