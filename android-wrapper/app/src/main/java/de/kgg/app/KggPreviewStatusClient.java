package de.kgg.app;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

final class KggPreviewStatusClient {
    private static final int MAX_STATUS_BYTES = 32_768;

    private KggPreviewStatusClient() {
    }

    static KggPreviewStatus fetch() throws Exception {
        String statusUrl = BuildConfig.KGG_PREVIEW_STATUS_URL.trim();
        if (statusUrl.isEmpty()) {
            return null;
        }
        URL url = new URL(statusUrl);
        String protocol = url.getProtocol();
        String host = url.getHost();
        boolean trustedProduction = protocol.equals("https") && host.equals("raw.githubusercontent.com");
        boolean trustedEmulator = BuildConfig.DEBUG && protocol.equals("http") && host.equals("10.0.2.2");
        if (!trustedProduction && !trustedEmulator) {
            throw new IllegalArgumentException("Untrusted Preview status URL");
        }
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setConnectTimeout(8_000);
        connection.setReadTimeout(8_000);
        connection.setUseCaches(false);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-cache");
        try {
            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
                throw new IllegalStateException("Preview status HTTP " + connection.getResponseCode());
            }
            try (InputStream input = connection.getInputStream();
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int total = 0;
                int read;
                while ((read = input.read(buffer)) != -1) {
                    total += read;
                    if (total > MAX_STATUS_BYTES) {
                        throw new IllegalStateException("Preview status response is too large");
                    }
                    output.write(buffer, 0, read);
                }
                return KggPreviewStatus.parse(output.toString(StandardCharsets.UTF_8.name()));
            }
        } finally {
            connection.disconnect();
        }
    }
}
