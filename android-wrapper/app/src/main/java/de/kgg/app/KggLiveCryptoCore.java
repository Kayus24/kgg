package de.kgg.app;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.AlgorithmParameters;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.security.interfaces.ECPublicKey;
import java.security.spec.ECGenParameterSpec;
import java.security.spec.ECParameterSpec;
import java.security.spec.ECPoint;
import java.security.spec.ECPublicKeySpec;
import java.util.Arrays;
import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.KeyAgreement;
import javax.crypto.Mac;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * Provider-neutral cryptographic primitives for the native live-key bridge.
 * Android Keystore access deliberately remains in {@link KggLiveKeyBridge}.
 */
final class KggLiveCryptoCore {
    static final int PAIRING_ID_BYTES = 16;
    static final int PAIRING_SECRET_BYTES = 32;
    static final int SESSION_ID_BYTES = 16;
    static final int SESSION_SALT_BYTES = 32;
    static final int P256_PUBLIC_KEY_BYTES = 65;
    static final int HMAC_BYTES = 32;
    static final int AES_KEY_BYTES = 32;
    static final int GCM_NONCE_BYTES = 12;
    static final int GCM_TAG_BYTES = 16;
    static final int MAX_AAD_BYTES = 4 * 1024;
    static final int MAX_FRAME_CIPHERTEXT_BYTES = 64 * 1024;
    static final int MAX_OFFER_BYTES = 4 * 1024;

    private static final byte[] JOIN_CONTEXT =
            "KGG-LIVE-JOIN-V1".getBytes(StandardCharsets.UTF_8);
    private static final byte[] OFFER_CONTEXT =
            "KGG-LIVE-ECDH-OFFER-V1".getBytes(StandardCharsets.UTF_8);
    private static final byte[] SESSION_CONTEXT =
            "KGG-LIVE-SESSION-V1".getBytes(StandardCharsets.UTF_8);

    private KggLiveCryptoCore() {
    }

    static boolean isSupported() {
        try {
            SecureRandom random = newSecureRandom();
            KeyPair pair = generateP256KeyPair(random);
            byte[] publicKey = rawPublicKey(pair.getPublic());
            PublicKey parsed = publicKeyFromRaw(publicKey);
            byte[] shared = ecdh(pair.getPrivate(), parsed);
            byte[] salt = randomBytes(random, SESSION_SALT_BYTES);
            byte[] derived = hkdfSha256(shared, salt, SESSION_CONTEXT, AES_KEY_BYTES);
            SecretKey key = new SecretKeySpec(derived, "AES");
            GcmResult encrypted = encrypt(key, new byte[0], new byte[0], random);
            decrypt(key, new byte[0], encrypted.nonce, encrypted.ciphertext);
            clear(shared, derived, salt, encrypted.nonce, encrypted.ciphertext, publicKey);
            destroy(pair.getPrivate());
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    static SecureRandom newSecureRandom() {
        SecureRandom random = new SecureRandom();
        byte[] probe = new byte[PAIRING_SECRET_BYTES];
        random.nextBytes(probe);
        clear(probe);
        return random;
    }

    static byte[] randomBytes(SecureRandom random, int length) {
        if (random == null || length < 1 || length > 1024) {
            throw new IllegalArgumentException("random_input_invalid");
        }
        byte[] value = new byte[length];
        random.nextBytes(value);
        return value;
    }

    static String base64Url(byte[] value) {
        if (value == null) {
            throw new IllegalArgumentException("base64_input_invalid");
        }
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }

    static byte[] decodeBase64Url(String value, int expectedBytes, int maxBytes)
            throws GeneralSecurityException {
        if (value == null || expectedBytes < -1 || maxBytes < 0
                || value.length() > maxBase64Chars(maxBytes)
                || value.indexOf('=') >= 0
                || (value.length() & 3) == 1) {
            throw new GeneralSecurityException("base64_input_invalid");
        }
        for (int index = 0; index < value.length(); index += 1) {
            char character = value.charAt(index);
            if (!isBase64UrlCharacter(character)) {
                throw new GeneralSecurityException("base64_input_invalid");
            }
        }
        final byte[] decoded;
        try {
            decoded = Base64.getUrlDecoder().decode(value);
        } catch (IllegalArgumentException error) {
            throw new GeneralSecurityException("base64_input_invalid", error);
        }
        if (decoded.length > maxBytes || (expectedBytes >= 0 && decoded.length != expectedBytes)
                || !base64Url(decoded).equals(value)) {
            clear(decoded);
            throw new GeneralSecurityException("base64_size_invalid");
        }
        return decoded;
    }

    static byte[] utf8(String value, int maxBytes) {
        if (value == null || maxBytes < 0 || value.length() > maxBytes) {
            throw new IllegalArgumentException("text_input_invalid");
        }
        byte[] encoded = value.getBytes(StandardCharsets.UTF_8);
        if (encoded.length > maxBytes) {
            clear(encoded);
            throw new IllegalArgumentException("text_size_invalid");
        }
        return encoded;
    }

    static byte[] joinHmac(byte[] pairingSecret, byte[] sessionId, byte[] sessionSalt)
            throws GeneralSecurityException {
        requireLength(pairingSecret, PAIRING_SECRET_BYTES, "pairing_secret_invalid");
        requireLength(sessionId, SESSION_ID_BYTES, "session_id_invalid");
        requireLength(sessionSalt, SESSION_SALT_BYTES, "session_salt_invalid");
        return hmacSha256(pairingSecret, concat(JOIN_CONTEXT, sessionId, sessionSalt));
    }

    static byte[] peerOfferMac(
            byte[] pairingSecret,
            byte[] pairingId,
            String role,
            byte[] sessionId,
            byte[] publicKey
    ) throws GeneralSecurityException {
        requireLength(pairingSecret, PAIRING_SECRET_BYTES, "pairing_secret_invalid");
        requireLength(pairingId, PAIRING_ID_BYTES, "pairing_id_invalid");
        requireLength(sessionId, SESSION_ID_BYTES, "session_id_invalid");
        requireLength(publicKey, P256_PUBLIC_KEY_BYTES, "public_key_invalid");
        byte[] roleBytes = utf8(role, 16);
        try {
            return hmacSha256(
                    pairingSecret,
                    concat(OFFER_CONTEXT, pairingId, roleBytes, sessionId, publicKey)
            );
        } finally {
            clear(roleBytes);
        }
    }

    static byte[] hmacSha256(byte[] key, byte[] message) throws GeneralSecurityException {
        if (key == null || key.length < 16 || key.length > 64 || message == null
                || message.length > 256 * 1024) {
            throw new GeneralSecurityException("hmac_input_invalid");
        }
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key, "HmacSHA256"));
        return mac.doFinal(message);
    }

    static boolean constantTimeEquals(byte[] left, byte[] right) {
        return left != null && right != null && MessageDigest.isEqual(left, right);
    }

    static byte[] hkdfSha256(byte[] ikm, byte[] salt, byte[] info, int outputLength)
            throws GeneralSecurityException {
        if (ikm == null || ikm.length < 1 || ikm.length > 256
                || salt == null || salt.length > 256
                || info == null || info.length > 1024
                || outputLength < 1 || outputLength > 255 * 32) {
            throw new GeneralSecurityException("hkdf_input_invalid");
        }
        byte[] actualSalt = salt.length == 0 ? new byte[32] : Arrays.copyOf(salt, salt.length);
        byte[] prk = hmacSha256(actualSalt, ikm);
        byte[] output = new byte[outputLength];
        byte[] previous = new byte[0];
        try {
            int offset = 0;
            int counter = 1;
            while (offset < outputLength) {
                byte[] blockInput = concat(previous, info, new byte[]{(byte) counter});
                byte[] block = hmacSha256(prk, blockInput);
                clear(blockInput, previous);
                int copyLength = Math.min(block.length, outputLength - offset);
                System.arraycopy(block, 0, output, offset, copyLength);
                offset += copyLength;
                clear(previous);
                previous = block;
                counter += 1;
            }
            return output;
        } finally {
            clear(actualSalt, prk, previous);
        }
    }

    static KeyPair generateP256KeyPair(SecureRandom random) throws GeneralSecurityException {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("EC");
        generator.initialize(new ECGenParameterSpec("secp256r1"), random);
        return generator.generateKeyPair();
    }

    static byte[] rawPublicKey(PublicKey publicKey) throws GeneralSecurityException {
        if (!(publicKey instanceof ECPublicKey)) {
            throw new GeneralSecurityException("public_key_type_invalid");
        }
        ECPoint point = ((ECPublicKey) publicKey).getW();
        if (point == null || point.equals(ECPoint.POINT_INFINITY)) {
            throw new GeneralSecurityException("public_key_point_invalid");
        }
        byte[] x = unsignedFixed(point.getAffineX(), 32);
        byte[] y = unsignedFixed(point.getAffineY(), 32);
        byte[] output = new byte[P256_PUBLIC_KEY_BYTES];
        output[0] = 0x04;
        System.arraycopy(x, 0, output, 1, x.length);
        System.arraycopy(y, 0, output, 33, y.length);
        clear(x, y);
        return output;
    }

    static PublicKey publicKeyFromRaw(byte[] raw) throws GeneralSecurityException {
        requireLength(raw, P256_PUBLIC_KEY_BYTES, "public_key_invalid");
        if (raw[0] != 0x04) {
            throw new GeneralSecurityException("public_key_format_invalid");
        }
        byte[] x = Arrays.copyOfRange(raw, 1, 33);
        byte[] y = Arrays.copyOfRange(raw, 33, 65);
        try {
            AlgorithmParameters parameters = AlgorithmParameters.getInstance("EC");
            parameters.init(new ECGenParameterSpec("secp256r1"));
            ECParameterSpec curve = parameters.getParameterSpec(ECParameterSpec.class);
            ECPublicKeySpec specification = new ECPublicKeySpec(
                    new ECPoint(new BigInteger(1, x), new BigInteger(1, y)),
                    curve
            );
            return KeyFactory.getInstance("EC").generatePublic(specification);
        } finally {
            clear(x, y);
        }
    }

    static byte[] ecdh(PrivateKey privateKey, PublicKey publicKey) throws GeneralSecurityException {
        if (privateKey == null || publicKey == null) {
            throw new GeneralSecurityException("ecdh_key_invalid");
        }
        KeyAgreement agreement = KeyAgreement.getInstance("ECDH");
        agreement.init(privateKey);
        agreement.doPhase(publicKey, true);
        return agreement.generateSecret();
    }

    static GcmResult encrypt(
            SecretKey key,
            byte[] aad,
            byte[] plaintext,
            SecureRandom random
    ) throws GeneralSecurityException {
        validateAesKey(key);
        if (aad == null || aad.length > MAX_AAD_BYTES || plaintext == null
                || plaintext.length > MAX_FRAME_CIPHERTEXT_BYTES - GCM_TAG_BYTES
                || random == null) {
            throw new GeneralSecurityException("encrypt_input_invalid");
        }
        byte[] nonce = randomBytes(random, GCM_NONCE_BYTES);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(GCM_TAG_BYTES * 8, nonce));
            cipher.updateAAD(aad);
            return new GcmResult(nonce, cipher.doFinal(plaintext));
        } catch (GeneralSecurityException error) {
            clear(nonce);
            throw error;
        }
    }

    static byte[] decrypt(
            SecretKey key,
            byte[] aad,
            byte[] nonce,
            byte[] ciphertext
    ) throws GeneralSecurityException {
        validateAesKey(key);
        requireLength(nonce, GCM_NONCE_BYTES, "nonce_invalid");
        if (aad == null || aad.length > MAX_AAD_BYTES || ciphertext == null
                || ciphertext.length < GCM_TAG_BYTES
                || ciphertext.length > MAX_FRAME_CIPHERTEXT_BYTES) {
            throw new GeneralSecurityException("decrypt_input_invalid");
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(GCM_TAG_BYTES * 8, nonce));
        cipher.updateAAD(aad);
        return cipher.doFinal(ciphertext);
    }

    static byte[] concat(byte[]... parts) {
        int length = 0;
        if (parts == null) {
            throw new IllegalArgumentException("concat_input_invalid");
        }
        for (byte[] part : parts) {
            if (part == null || part.length > 256 * 1024 || length > 1024 * 1024 - part.length) {
                throw new IllegalArgumentException("concat_input_invalid");
            }
            length += part.length;
        }
        byte[] result = new byte[length];
        int offset = 0;
        for (byte[] part : parts) {
            System.arraycopy(part, 0, result, offset, part.length);
            offset += part.length;
        }
        return result;
    }

    static void destroy(PrivateKey privateKey) {
        if (privateKey instanceof javax.security.auth.Destroyable) {
            try {
                ((javax.security.auth.Destroyable) privateKey).destroy();
            } catch (Exception ignored) {
                // Dropping the reference below is the provider-neutral fallback.
            }
        }
    }

    static void clear(byte[]... values) {
        if (values == null) {
            return;
        }
        for (byte[] value : values) {
            if (value != null) {
                Arrays.fill(value, (byte) 0);
            }
        }
    }

    private static void validateAesKey(SecretKey key) throws GeneralSecurityException {
        if (key == null || !"AES".equalsIgnoreCase(key.getAlgorithm())) {
            throw new GeneralSecurityException("aes_key_invalid");
        }
        byte[] encoded = key.getEncoded();
        if (encoded != null) {
            try {
                if (encoded.length != AES_KEY_BYTES) {
                    throw new GeneralSecurityException("aes_key_size_invalid");
                }
            } finally {
                clear(encoded);
            }
        }
    }

    private static byte[] unsignedFixed(BigInteger value, int size)
            throws GeneralSecurityException {
        if (value == null || value.signum() < 0) {
            throw new GeneralSecurityException("ec_point_invalid");
        }
        byte[] encoded = value.toByteArray();
        byte[] output = new byte[size];
        int sourceOffset = 0;
        if (encoded.length == size + 1 && encoded[0] == 0) {
            sourceOffset = 1;
        }
        if (encoded.length - sourceOffset > size) {
            clear(encoded);
            throw new GeneralSecurityException("ec_point_size_invalid");
        }
        System.arraycopy(
                encoded,
                sourceOffset,
                output,
                size - (encoded.length - sourceOffset),
                encoded.length - sourceOffset
        );
        clear(encoded);
        return output;
    }

    private static void requireLength(byte[] value, int expected, String error)
            throws GeneralSecurityException {
        if (value == null || value.length != expected) {
            throw new GeneralSecurityException(error);
        }
    }

    private static boolean isBase64UrlCharacter(char value) {
        return (value >= 'A' && value <= 'Z')
                || (value >= 'a' && value <= 'z')
                || (value >= '0' && value <= '9')
                || value == '-'
                || value == '_';
    }

    private static int maxBase64Chars(int maxBytes) {
        if (maxBytes < 0 || maxBytes > 1024 * 1024) {
            throw new IllegalArgumentException("base64_limit_invalid");
        }
        return ((maxBytes + 2) / 3) * 4;
    }

    static final class GcmResult {
        final byte[] nonce;
        final byte[] ciphertext;

        GcmResult(byte[] nonce, byte[] ciphertext) {
            this.nonce = nonce;
            this.ciphertext = ciphertext;
        }
    }
}
