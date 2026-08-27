package de.kgg.app;

import java.util.Arrays;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

/** Mutable, zeroable holder for the one active AES session key. */
final class KggLiveSessionSecrets {
    private byte[] key;

    synchronized void replace(byte[] value) {
        if (value == null || value.length != KggLiveCryptoCore.AES_KEY_BYTES) {
            throw new IllegalArgumentException("session_key_invalid");
        }
        clear();
        key = Arrays.copyOf(value, value.length);
    }

    synchronized boolean isActive() {
        return key != null;
    }

    synchronized byte[] copy() {
        return key == null ? null : Arrays.copyOf(key, key.length);
    }

    synchronized SecretKey asSecretKey() {
        return key == null ? null : new SecretKeySpec(key, "AES");
    }

    synchronized void clear() {
        if (key != null) {
            Arrays.fill(key, (byte) 0);
            key = null;
        }
    }
}
