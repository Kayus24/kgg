package de.kgg.app;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

import org.junit.Test;

public class KggLiveCryptoCoreTest {
    private final SecureRandom random = KggLiveCryptoCore.newSecureRandom();

    @Test
    public void providerCryptoIsAvailable() {
        assertTrue(KggLiveCryptoCore.isSupported());
    }

    @Test
    public void pairingMaterialAndJoinHmacAreBoundAndDifferent() throws Exception {
        byte[] secretA = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_SECRET_BYTES
        );
        byte[] secretB = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_SECRET_BYTES
        );
        byte[] idA = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_ID_BYTES
        );
        byte[] idB = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.PAIRING_ID_BYTES
        );
        byte[] sessionId = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.SESSION_ID_BYTES
        );
        byte[] salt = KggLiveCryptoCore.randomBytes(
                random,
                KggLiveCryptoCore.SESSION_SALT_BYTES
        );

        assertFalse(Arrays.equals(secretA, secretB));
        assertFalse(Arrays.equals(idA, idB));
        byte[] hmacA = KggLiveCryptoCore.joinHmac(secretA, sessionId, salt);
        byte[] hmacARepeat = KggLiveCryptoCore.joinHmac(secretA, sessionId, salt);
        byte[] hmacB = KggLiveCryptoCore.joinHmac(secretB, sessionId, salt);
        assertArrayEquals(hmacA, hmacARepeat);
        assertFalse(Arrays.equals(hmacA, hmacB));

        byte[] changedSalt = Arrays.copyOf(salt, salt.length);
        changedSalt[0] ^= 0x01;
        assertFalse(Arrays.equals(hmacA, KggLiveCryptoCore.joinHmac(secretA, sessionId, changedSalt)));
    }

    @Test
    public void twoP256PeersDeriveTheSameHkdfKey() throws Exception {
        KeyPair first = KggLiveCryptoCore.generateP256KeyPair(random);
        KeyPair second = KggLiveCryptoCore.generateP256KeyPair(random);
        byte[] firstPublic = KggLiveCryptoCore.rawPublicKey(first.getPublic());
        byte[] secondPublic = KggLiveCryptoCore.rawPublicKey(second.getPublic());
        byte[] firstShared = KggLiveCryptoCore.ecdh(
                first.getPrivate(),
                KggLiveCryptoCore.publicKeyFromRaw(secondPublic)
        );
        byte[] secondShared = KggLiveCryptoCore.ecdh(
                second.getPrivate(),
                KggLiveCryptoCore.publicKeyFromRaw(firstPublic)
        );
        byte[] pairingId = KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.PAIRING_ID_BYTES);
        byte[] sessionId = KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.SESSION_ID_BYTES);
        byte[] salt = KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.SESSION_SALT_BYTES);
        byte[] info = KggLiveCryptoCore.concat(
                "KGG-LIVE-SESSION-V1".getBytes(StandardCharsets.UTF_8),
                pairingId,
                sessionId,
                "therapist".getBytes(StandardCharsets.UTF_8),
                "patient".getBytes(StandardCharsets.UTF_8)
        );

        assertArrayEquals(firstShared, secondShared);
        assertArrayEquals(
                KggLiveCryptoCore.hkdfSha256(firstShared, salt, info, KggLiveCryptoCore.AES_KEY_BYTES),
                KggLiveCryptoCore.hkdfSha256(secondShared, salt, info, KggLiveCryptoCore.AES_KEY_BYTES)
        );
        byte[] changedPairingId = Arrays.copyOf(pairingId, pairingId.length);
        changedPairingId[0] ^= 0x01;
        byte[] changedInfo = KggLiveCryptoCore.concat(
                "KGG-LIVE-SESSION-V1".getBytes(StandardCharsets.UTF_8),
                changedPairingId,
                sessionId,
                "therapist".getBytes(StandardCharsets.UTF_8),
                "patient".getBytes(StandardCharsets.UTF_8)
        );
        assertFalse(Arrays.equals(
                KggLiveCryptoCore.hkdfSha256(firstShared, salt, info, KggLiveCryptoCore.AES_KEY_BYTES),
                KggLiveCryptoCore.hkdfSha256(firstShared, salt, changedInfo, KggLiveCryptoCore.AES_KEY_BYTES)
        ));

        byte[] secret = KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.PAIRING_SECRET_BYTES);
        byte[] therapistMac = KggLiveCryptoCore.peerOfferMac(
                secret, pairingId, "therapist", sessionId, firstPublic
        );
        byte[] patientMac = KggLiveCryptoCore.peerOfferMac(
                secret, pairingId, "patient", sessionId, firstPublic
        );
        assertFalse(Arrays.equals(therapistMac, patientMac));
        secret[0] ^= 0x01;
        assertFalse(Arrays.equals(
                therapistMac,
                KggLiveCryptoCore.peerOfferMac(secret, pairingId, "therapist", sessionId, firstPublic)
        ));
    }

    @Test
    public void aesGcmAuthenticatesAadAndCiphertext() throws Exception {
        SecretKey key = new SecretKeySpec(
                KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.AES_KEY_BYTES),
                "AES"
        );
        byte[] aad = "v=1|session=synthetic|sequence=1".getBytes(StandardCharsets.UTF_8);
        byte[] plaintext = "synthetic-live-frame".getBytes(StandardCharsets.UTF_8);
        KggLiveCryptoCore.GcmResult encrypted = KggLiveCryptoCore.encrypt(
                key, aad, plaintext, random
        );
        assertArrayEquals(plaintext, KggLiveCryptoCore.decrypt(
                key, aad, encrypted.nonce, encrypted.ciphertext
        ));

        byte[] wrongAad = Arrays.copyOf(aad, aad.length);
        wrongAad[0] ^= 0x01;
        assertFails(() -> KggLiveCryptoCore.decrypt(
                key, wrongAad, encrypted.nonce, encrypted.ciphertext
        ));
        byte[] corrupted = Arrays.copyOf(encrypted.ciphertext, encrypted.ciphertext.length);
        corrupted[corrupted.length - 1] ^= 0x01;
        assertFails(() -> KggLiveCryptoCore.decrypt(
                key, aad, encrypted.nonce, corrupted
        ));
    }

    @Test
    public void aesGcmNoncesDoNotRepeatInSeries() throws Exception {
        SecretKey key = new SecretKeySpec(
                KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.AES_KEY_BYTES),
                "AES"
        );
        Set<String> nonces = new HashSet<>();
        byte[] aad = "synthetic-aad".getBytes(StandardCharsets.UTF_8);
        byte[] plaintext = new byte[]{1, 2, 3};
        for (int index = 0; index < 256; index += 1) {
            KggLiveCryptoCore.GcmResult encrypted = KggLiveCryptoCore.encrypt(
                    key, aad, plaintext, random
            );
            nonces.add(KggLiveCryptoCore.base64Url(encrypted.nonce));
        }
        assertEquals(256, nonces.size());
    }

    @Test
    public void keystoreLikeStateWrapRejectsWrongAliasAndCorruption() throws Exception {
        SecretKey aliasA = new SecretKeySpec(
                KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.AES_KEY_BYTES),
                "AES"
        );
        SecretKey aliasB = new SecretKeySpec(
                KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.AES_KEY_BYTES),
                "AES"
        );
        byte[] aad = "KGGLiveKeyStateV1".getBytes(StandardCharsets.UTF_8);
        byte[] state = "{\"v\":1,\"pairings\":{}}".getBytes(StandardCharsets.UTF_8);
        KggLiveCryptoCore.GcmResult wrapped = KggLiveCryptoCore.encrypt(
                aliasA, aad, state, random
        );
        assertArrayEquals(state, KggLiveCryptoCore.decrypt(
                aliasA, aad, wrapped.nonce, wrapped.ciphertext
        ));
        assertFails(() -> KggLiveCryptoCore.decrypt(
                aliasB, aad, wrapped.nonce, wrapped.ciphertext
        ));
        byte[] corrupted = Arrays.copyOf(wrapped.ciphertext, wrapped.ciphertext.length);
        corrupted[0] ^= 0x01;
        assertFails(() -> KggLiveCryptoCore.decrypt(aliasA, aad, wrapped.nonce, corrupted));
    }

    @Test
    public void sessionCloseRemovesTheMutableSessionMaterial() {
        KggLiveSessionSecrets secrets = new KggLiveSessionSecrets();
        secrets.replace(KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.AES_KEY_BYTES));
        assertTrue(secrets.isActive());
        assertEquals(KggLiveCryptoCore.AES_KEY_BYTES, secrets.copy().length);
        secrets.clear();
        assertFalse(secrets.isActive());
        assertTrue(secrets.copy() == null);
    }

    @Test
    public void base64AndBridgeInputsAreStrictlyBounded() throws Exception {
        String sessionId = KggLiveCryptoCore.base64Url(
                KggLiveCryptoCore.randomBytes(random, KggLiveCryptoCore.SESSION_ID_BYTES)
        );
        assertEquals(
                KggLiveCryptoCore.SESSION_ID_BYTES,
                KggLiveCryptoCore.decodeBase64Url(
                        sessionId,
                        KggLiveCryptoCore.SESSION_ID_BYTES,
                        KggLiveCryptoCore.SESSION_ID_BYTES
                ).length
        );
        assertFails(() -> KggLiveCryptoCore.decodeBase64Url(
                sessionId + "=", KggLiveCryptoCore.SESSION_ID_BYTES, KggLiveCryptoCore.SESSION_ID_BYTES
        ));
        assertFails(() -> KggLiveCryptoCore.decodeBase64Url(
                "A", 1, 1
        ));
        assertFalse(KggLiveBridgePolicy.isTrustedPageUrl(
                "https://attacker.invalid/kgg.html",
                "file:///data/user/0/de.kgg.app/files/web/kgg.html"
        ));
        assertTrue(KggLiveBridgePolicy.isTrustedPageUrl(
                "file:///data/user/0/de.kgg.app/files/web/kgg.html?trusted=1",
                "file:///data/user/0/de.kgg.app/files/web/kgg.html"
        ));
        assertFalse(KggLiveBridgePolicy.isTrustedPageUrl(
                "file:///data/user/0/de.kgg.app/files/web/kgg.html.evil",
                "file:///data/user/0/de.kgg.app/files/web/kgg.html"
        ));
        assertTrue(KggLiveBridgePolicy.isPlanKey("plan-2026_08"));
        assertFalse(KggLiveBridgePolicy.isPlanKey("patient name"));
        assertEquals("patient", KggLiveBridgePolicy.oppositeRole("therapist"));
    }

    private static void assertFails(CryptoAction action) throws Exception {
        try {
            action.run();
            fail("expected cryptographic failure");
        } catch (Exception expected) {
            // Expected authentication, size, or format failure.
        }
    }

    private interface CryptoAction {
        void run() throws Exception;
    }
}
