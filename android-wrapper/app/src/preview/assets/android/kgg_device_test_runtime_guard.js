(function (root) {
  "use strict";

  var nativeBridge = root && root.KGGDeviceTestStationNative;
  var appBridge = root && root.KGGAndroidApp;
  if (!root || !nativeBridge || !appBridge) return;

  function parseJson(value) {
    return JSON.parse(String(value || ""));
  }

  function failure(code) {
    return JSON.stringify({ ok: false, error: code });
  }

  function requireLoadedPreview(runtimeContext) {
    if (!runtimeContext || typeof runtimeContext !== "object" || Array.isArray(runtimeContext)) {
      throw new Error("runtime_context_invalid");
    }
    if (typeof appBridge.updateStatus !== "function") {
      throw new Error("preview_status_unavailable");
    }
    var status = parseJson(appBridge.updateStatus());
    if (status.previewChannel !== true) {
      throw new Error("preview_profile_required");
    }
    if (Number(status.rolloutCode) !== Number(runtimeContext.rolloutCode)
        || String(status.releaseId || "") !== String(runtimeContext.requestId || "")) {
      throw new Error("preview_html_not_current");
    }
    if (status.pendingHealthCheck === true) {
      throw new Error("preview_html_not_healthy");
    }
    return status;
  }

  root.KGGDeviceTestStation = Object.freeze({
    getDeviceInfo: function () {
      return nativeBridge.getDeviceInfo();
    },
    beginSession: function (runtimeContextJson) {
      try {
        var runtimeContext = parseJson(runtimeContextJson);
        requireLoadedPreview(runtimeContext);
        return nativeBridge.beginSession(runtimeContextJson);
      } catch (error) {
        var code = error && error.message ? String(error.message) : "preview_runtime_guard_failed";
        return failure(code);
      }
    },
    endSession: function (reportJson) {
      return nativeBridge.endSession(reportJson);
    },
    openReportIssue: function () {
      return nativeBridge.openReportIssue();
    }
  });
})(typeof window !== "undefined" ? window : null);
