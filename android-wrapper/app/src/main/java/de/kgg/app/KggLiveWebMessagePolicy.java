package de.kgg.app;

final class KggLiveWebMessagePolicy {
    static final String ERROR_FRAME_NOT_ALLOWED = "frame_not_allowed";
    static final String ERROR_ORIGIN_NOT_ALLOWED = "origin_not_allowed";
    static final int MAX_REQUEST_CHARS = 128 * 1024;

    private KggLiveWebMessagePolicy() {
    }

    static String frameError(
            boolean isMainFrame,
            String currentMainFrameUrl,
            String trustedBaseUrl
    ) {
        if (!isMainFrame) {
            return ERROR_FRAME_NOT_ALLOWED;
        }
        if (!KggLiveBridgePolicy.isTrustedPageUrl(currentMainFrameUrl, trustedBaseUrl)) {
            return ERROR_ORIGIN_NOT_ALLOWED;
        }
        return "";
    }

    static boolean isTransportReady(boolean featureSupported, boolean registrationSucceeded) {
        return featureSupported && registrationSucceeded;
    }
}
