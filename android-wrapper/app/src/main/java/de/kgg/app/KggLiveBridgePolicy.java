package de.kgg.app;

import java.util.regex.Pattern;

final class KggLiveBridgePolicy {
    static final int MAX_PAGE_URL_LENGTH = 2048;
    static final int MAX_PLAN_KEY_LENGTH = 128;
    private static final Pattern PLAN_KEY =
            Pattern.compile("[A-Za-z0-9][A-Za-z0-9._~-]{0,127}");
    private static final Pattern ROLE = Pattern.compile("therapist|patient");

    private KggLiveBridgePolicy() {
    }

    static boolean isTrustedPageUrl(String candidate, String expectedBaseUrl) {
        if (candidate == null || expectedBaseUrl == null
                || candidate.length() > MAX_PAGE_URL_LENGTH
                || expectedBaseUrl.length() > MAX_PAGE_URL_LENGTH
                || !expectedBaseUrl.startsWith("file:///")) {
            return false;
        }
        return candidate.equals(expectedBaseUrl)
                || candidate.startsWith(expectedBaseUrl + "#")
                || candidate.startsWith(expectedBaseUrl + "?");
    }

    static boolean isPlanKey(String value) {
        return value != null && value.length() <= MAX_PLAN_KEY_LENGTH
                && PLAN_KEY.matcher(value).matches();
    }

    static boolean isRole(String value) {
        return value != null && ROLE.matcher(value).matches();
    }

    static String oppositeRole(String role) {
        if ("therapist".equals(role)) {
            return "patient";
        }
        if ("patient".equals(role)) {
            return "therapist";
        }
        return "";
    }
}
