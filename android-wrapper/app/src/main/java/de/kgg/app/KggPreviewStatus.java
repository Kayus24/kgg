package de.kgg.app;

import org.json.JSONObject;

import java.util.regex.Pattern;

final class KggPreviewStatus {
    private static final Pattern REQUEST_ID = Pattern.compile("^[a-z0-9][a-z0-9-]{5,63}$");

    final String requestId;
    final String runId;
    final String runUrl;
    final String phase;
    final String conclusion;
    final String message;

    private KggPreviewStatus(
            String requestId,
            String runId,
            String runUrl,
            String phase,
            String conclusion,
            String message
    ) {
        this.requestId = requestId;
        this.runId = runId;
        this.runUrl = runUrl;
        this.phase = phase;
        this.conclusion = conclusion;
        this.message = message;
    }

    static KggPreviewStatus parse(String raw) throws Exception {
        JSONObject value = new JSONObject(raw);
        if (!"kgg_preview_run_status".equals(value.optString("kind")) || value.optInt("schema") != 1) {
            throw new IllegalArgumentException("Unsupported Preview status document");
        }
        String requestId = value.optString("requestId");
        String runId = value.optString("runId");
        String runUrl = value.optString("runUrl");
        String phase = value.optString("phase");
        String status = value.optString("status");
        String conclusion = value.isNull("conclusion") ? "" : value.optString("conclusion");
        String message = value.optString("message").trim();
        if (!REQUEST_ID.matcher(requestId).matches()
                || !runId.matches("^[0-9]+$")
                || !runUrl.startsWith("https://github.com/Kayus24/kgg/actions/runs/")
                || !(phase.equals("validating") || phase.equals("publishing")
                || phase.equals("success") || phase.equals("failure"))
                || message.isEmpty() || message.length() > 240) {
            throw new IllegalArgumentException("Invalid Preview status fields");
        }
        boolean terminal = phase.equals("success") || phase.equals("failure");
        if (terminal != status.equals("completed")
                || (!terminal && !status.equals("in_progress"))
                || (terminal && !conclusion.equals(phase))
                || (!terminal && !conclusion.isEmpty())) {
            throw new IllegalArgumentException("Inconsistent Preview status state");
        }
        return new KggPreviewStatus(requestId, runId, runUrl, phase, conclusion, message);
    }

    boolean isTerminal() {
        return phase.equals("success") || phase.equals("failure");
    }

    boolean isSuccess() {
        return phase.equals("success");
    }

    String eventKey() {
        return runId + "|" + phase + "|" + conclusion;
    }
}
