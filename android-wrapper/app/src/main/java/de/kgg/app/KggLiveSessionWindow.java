package de.kgg.app;

import java.util.HashSet;
import java.util.Set;

/**
 * Ephemeral native session lifetime and replay state. No key or plaintext is
 * stored here; only bounded nonce identifiers and frame accounting are kept.
 */
final class KggLiveSessionWindow {
    static final long MAX_SESSION_LIFETIME_MILLIS = 2L * 60L * 60L * 1000L;
    static final int MAX_SUCCESSFUL_FRAMES = 400;

    private final long expiresAtEpochMillis;
    private final long expiresAtElapsedMillis;
    private final Set<String> consumedIncomingNonces = new HashSet<>();
    private int successfulFrameCount;
    private boolean cleared;

    private KggLiveSessionWindow(long expiresAtEpochMillis, long expiresAtElapsedMillis) {
        this.expiresAtEpochMillis = expiresAtEpochMillis;
        this.expiresAtElapsedMillis = expiresAtElapsedMillis;
    }

    static KggLiveSessionWindow create(
            long expiresAtEpochMillis,
            long nowEpochMillis,
            long nowElapsedMillis
    ) {
        long remaining = expiresAtEpochMillis - nowEpochMillis;
        if (expiresAtEpochMillis <= nowEpochMillis
                || remaining > MAX_SESSION_LIFETIME_MILLIS
                || nowElapsedMillis > Long.MAX_VALUE - remaining) {
            throw new IllegalArgumentException("session_expiry_invalid");
        }
        return new KggLiveSessionWindow(
                expiresAtEpochMillis,
                nowElapsedMillis + remaining
        );
    }

    boolean isExpired(long nowEpochMillis, long nowElapsedMillis) {
        return cleared
                || nowEpochMillis >= expiresAtEpochMillis
                || nowElapsedMillis >= expiresAtElapsedMillis;
    }

    boolean canUseFrame(long nowEpochMillis, long nowElapsedMillis) {
        return !isExpired(nowEpochMillis, nowElapsedMillis)
                && successfulFrameCount < MAX_SUCCESSFUL_FRAMES;
    }

    boolean canAttemptIncomingNonce(
            byte[] nonce,
            long nowEpochMillis,
            long nowElapsedMillis
    ) {
        if (nonce == null || nonce.length != KggLiveCryptoCore.GCM_NONCE_BYTES
                || !canUseFrame(nowEpochMillis, nowElapsedMillis)) {
            return false;
        }
        return !consumedIncomingNonces.contains(KggLiveCryptoCore.base64Url(nonce));
    }

    /** Marks an incoming nonce only after the caller has authenticated GCM. */
    boolean markIncomingNonceAfterAuthentication(
            byte[] nonce,
            long nowEpochMillis,
            long nowElapsedMillis
    ) {
        if (!canAttemptIncomingNonce(nonce, nowEpochMillis, nowElapsedMillis)) {
            return false;
        }
        consumedIncomingNonces.add(KggLiveCryptoCore.base64Url(nonce));
        successfulFrameCount += 1;
        return true;
    }

    /** Counts an outgoing frame only after encryption has completed. */
    boolean markOutgoingFrameAfterSuccess(long nowEpochMillis, long nowElapsedMillis) {
        if (!canUseFrame(nowEpochMillis, nowElapsedMillis)) {
            return false;
        }
        successfulFrameCount += 1;
        return true;
    }

    int successfulFrameCount() {
        return successfulFrameCount;
    }

    void clear() {
        consumedIncomingNonces.clear();
        successfulFrameCount = 0;
        cleared = true;
    }
}
