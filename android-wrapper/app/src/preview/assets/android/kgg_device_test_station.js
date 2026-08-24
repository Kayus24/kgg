(function () {
  "use strict";

  var bridge = window.KGGDeviceTestStation;
  if (!bridge) return;

  var STORAGE_KEY = "kgg_tab_s9_test_station_progress_v1";
  var ROOT_ID = "kgg-device-test-station";
  var STATUS_LABELS = {
    passed: "bestanden",
    failed: "fehlgeschlagen",
    blocked: "blockiert",
    skipped: "optional übersprungen"
  };
  var STEPS = [
    {
      id: "admin-portrait",
      block: "Admin / Tablet",
      title: "Hochformat",
      instruction: "Prüfe die App im Hochformat. Die Bedienung bleibt sichtbar und ruhig.",
      noteCode: "layout_portrait"
    },
    {
      id: "admin-landscape",
      block: "Admin / Tablet",
      title: "Querformat",
      instruction: "Drehe den Tab ins Querformat und prüfe Menü, Planbereich und Karten.",
      noteCode: "layout_landscape"
    },
    {
      id: "admin-split-screen",
      block: "Admin / Tablet",
      title: "Split-Screen",
      instruction: "Öffne Split-Screen und prüfe, dass die App ohne Überlauf bedienbar bleibt.",
      noteCode: "layout_split_screen"
    },
    {
      id: "admin-package-button",
      block: "Admin / Tablet",
      title: "Paket-Schaltfläche",
      instruction: "Öffne die Paket-Schaltfläche und prüfe die Berührung am Tablet.",
      noteCode: "package_button"
    },
    {
      id: "admin-touch-dialog-save",
      block: "Admin / Tablet",
      title: "Dialog, Name und Speichern",
      instruction: "Öffne den Dialog, vergebe einen künstlichen Namen und speichere.",
      noteCode: "touch_dialog_save"
    },
    {
      id: "admin-seven-exercises",
      block: "Admin / Tablet",
      title: "Sieben synthetische Übungen",
      instruction: "Lege genau sieben künstliche Übungen an. Keine echten Patientendaten verwenden.",
      noteCode: "synthetic_exercise_set_7"
    },
    {
      id: "admin-reorder-save-reload",
      block: "Admin / Tablet",
      title: "Reihenfolge und Neuladen",
      instruction: "Ändere die Reihenfolge, speichere und lade die Ansicht neu.",
      noteCode: "reorder_persistence"
    },
    {
      id: "patient-first-start",
      block: "Patient / Plan",
      title: "Erststart",
      instruction: "Prüfe den Erststart mit einem künstlichen Testprofil.",
      noteCode: "patient_first_start"
    },
    {
      id: "patient-add-plan",
      block: "Patient / Plan",
      title: "Plan hinzufügen",
      instruction: "Füge einen künstlichen Plan hinzu und prüfe die Anzeige.",
      noteCode: "plan_add"
    },
    {
      id: "patient-replace-cancel",
      block: "Patient / Plan",
      title: "Plan ersetzen und abbrechen",
      instruction: "Starte das Ersetzen eines Plans und brich den Vorgang ab.",
      noteCode: "plan_replace_cancel"
    },
    {
      id: "patient-switch-plan",
      block: "Patient / Plan",
      title: "Planwechsel",
      instruction: "Wechsle zwischen zwei künstlichen Plänen.",
      noteCode: "plan_switch"
    },
    {
      id: "patient-rename",
      block: "Patient / Plan",
      title: "Umbenennen",
      instruction: "Benenne einen künstlichen Plan um und prüfe die neue Bezeichnung.",
      noteCode: "plan_rename"
    },
    {
      id: "patient-values-reload",
      block: "Patient / Plan",
      title: "Werte nach Neuladen",
      instruction: "Setze künstliche Werte, lade neu und prüfe Zustand und Werte.",
      noteCode: "values_reload"
    },
    {
      id: "patient-offline-restore",
      block: "Patient / Plan",
      title: "Offline und Wiederherstellung",
      instruction: "Prüfe den Offline-Zustand und die Wiederherstellung danach.",
      noteCode: "offline_restore"
    },
    {
      id: "qr-oppo-display",
      block: "QR-Schlussblock",
      title: "Oppo nur als QR-Anzeige",
      instruction: "Das Oppo dient später nur als QR-Anzeige. Keine Eingabe am Oppo bewerten.",
      optional: true,
      noteCode: "oppo_display_only"
    },
    {
      id: "qr-scan-7",
      block: "QR-Schlussblock",
      title: "KGGH2/KGGH3 mit 7 Übungen",
      instruction: "Scanne einen synthetischen KGGH2- oder KGGH3-Plan mit sieben Übungen.",
      noteCode: "synthetic_kgg_plan_7",
      camera: true
    },
    {
      id: "qr-scan-12",
      block: "QR-Schlussblock",
      title: "KGGH2/KGGH3 mit 12 Übungen",
      instruction: "Scanne einen synthetischen KGGH2- oder KGGH3-Plan mit zwölf Übungen.",
      noteCode: "synthetic_kgg_plan_12",
      camera: true
    },
    {
      id: "qr-scan-20",
      block: "QR-Schlussblock",
      title: "KGGH2/KGGH3 mit 20 Übungen",
      instruction: "Scanne einen synthetischen KGGH2- oder KGGH3-Plan mit 20 Übungen.",
      noteCode: "synthetic_kgg_plan_20",
      camera: true
    },
    {
      id: "qr-angle-distance",
      block: "QR-Schlussblock",
      title: "Winkel und Abstand",
      instruction: "Prüfe Winkel und Abstand. Bei fehlendem Tab: blockiert – echtes Tab nötig.",
      noteCode: "camera_angle_distance",
      camera: true
    },
    {
      id: "qr-weak-photo-fallback",
      block: "QR-Schlussblock",
      title: "Schwaches Bild und Foto-Ausweichweg",
      instruction: "Prüfe ein schwaches synthetisches Bild und den Foto-Ausweichweg.",
      noteCode: "weak_image_photo_fallback",
      camera: true
    },
    {
      id: "qr-camera-stop",
      block: "QR-Schlussblock",
      title: "Kamerastream sauber beenden",
      instruction: "Beende den Kameratest nach Erfolg oder Abbruch. Der Stream muss sauber enden.",
      noteCode: "camera_stream_cleanup",
      camera: true
    }
  ];

  var progress = loadProgress();
  var root = document.getElementById(ROOT_ID);
  if (root) root.parentNode.removeChild(root);
  root = document.createElement("div");
  root.id = ROOT_ID;
  document.documentElement.appendChild(root);

  function loadProgress() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      var value = raw ? JSON.parse(raw) : null;
      if (!value || typeof value !== "object") return null;
      if (!value.results || typeof value.results !== "object") value.results = {};
      return value;
    } catch (error) {
      return null;
    }
  }

  function saveProgress() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    } catch (error) {
      // Native endSession remains the authoritative report boundary.
    }
  }

  function parseNative(raw) {
    try {
      return JSON.parse(String(raw || ""));
    } catch (error) {
      return { ok: false, error: "native_response_invalid" };
    }
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function currentStep() {
    return STEPS[Math.max(0, Math.min(STEPS.length - 1, Number(progress.index) || 0))];
  }

  function resultCount() {
    var count = 0;
    STEPS.forEach(function (step) {
      if (progress.results && progress.results[step.id]) count += 1;
    });
    return count;
  }

  function clearRoot() {
    while (root.firstChild) root.removeChild(root.firstChild);
    root.className = "kgg-device-test-station-root";
  }

  function addStyles() {
    if (document.getElementById("kgg-device-test-station-style")) return;
    var style = document.createElement("style");
    style.id = "kgg-device-test-station-style";
    style.textContent =
      "#" + ROOT_ID + "{all:initial!important;position:fixed!important;right:10px!important;bottom:10px!important;z-index:2147483001!important;font:14px/1.4 system-ui,sans-serif!important;color:#12233f!important}" +
      "#" + ROOT_ID + " *{box-sizing:border-box!important;font-family:system-ui,sans-serif!important}" +
      "#" + ROOT_ID + " button{cursor:pointer!important;border:0!important;border-radius:10px!important;font:600 14px/1.2 system-ui,sans-serif!important}" +
      "#" + ROOT_ID + " .kgg-station-launch{background:#0b5cab!important;color:#fff!important;padding:12px 15px!important;box-shadow:0 5px 16px rgba(9,39,78,.3)!important}" +
      "#" + ROOT_ID + " .kgg-station-panel{width:min(390px,calc(100vw - 20px))!important;max-height:min(720px,calc(100vh - 20px))!important;overflow:auto!important;background:#fff!important;border:1px solid #b8c8dc!important;border-radius:16px!important;box-shadow:0 12px 36px rgba(9,39,78,.28)!important;padding:16px!important}" +
      "#" + ROOT_ID + " .kgg-station-kicker{color:#50647f!important;font-size:12px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.05em!important}" +
      "#" + ROOT_ID + " h2{margin:5px 0 8px!important;font-size:21px!important;line-height:1.15!important;color:#102b52!important}" +
      "#" + ROOT_ID + " p{margin:8px 0!important;color:#354c68!important}" +
      "#" + ROOT_ID + " .kgg-station-progress{height:7px!important;border-radius:8px!important;background:#e7edf5!important;overflow:hidden!important;margin:14px 0!important}" +
      "#" + ROOT_ID + " .kgg-station-progress>span{display:block!important;height:100%!important;background:#0b72c9!important}" +
      "#" + ROOT_ID + " .kgg-station-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important;margin-top:14px!important}" +
      "#" + ROOT_ID + " .kgg-station-status{padding:12px 8px!important;color:#fff!important}" +
      "#" + ROOT_ID + " .kgg-station-status[data-status=passed]{background:#16794d!important}" +
      "#" + ROOT_ID + " .kgg-station-status[data-status=failed]{background:#b32828!important}" +
      "#" + ROOT_ID + " .kgg-station-status[data-status=blocked]{background:#8b5e00!important}" +
      "#" + ROOT_ID + " .kgg-station-status[data-status=skipped]{background:#5d6673!important}" +
      "#" + ROOT_ID + " .kgg-station-secondary{background:#e8eef6!important;color:#1b3d66!important;padding:10px 12px!important;margin-top:8px!important}" +
      "#" + ROOT_ID + " .kgg-station-danger{background:#fce7e7!important;color:#8c2020!important;padding:10px 12px!important}" +
      "#" + ROOT_ID + " .kgg-station-meta{font-size:11px!important;color:#65758b!important;overflow-wrap:anywhere!important}" +
      "#" + ROOT_ID + " .kgg-station-note{padding:9px 10px!important;background:#f3f7fb!important;border-left:3px solid #5c8ab8!important;margin-top:10px!important}";
    document.head.appendChild(style);
  }

  function button(label, className, handler, dataStatus) {
    var element = document.createElement("button");
    element.type = "button";
    element.textContent = label;
    element.className = className || "";
    if (dataStatus) element.setAttribute("data-status", dataStatus);
    element.addEventListener("click", handler);
    return element;
  }

  function renderLauncher() {
    clearRoot();
    var hasActive = Boolean(progress && progress.active);
    var label = hasActive ? "Teststation fortsetzen" : "Tab-S9-Teststation";
    root.appendChild(button(label, "kgg-station-launch", startOrResume));
  }

  function startOrResume() {
    try {
      var session = parseNative(bridge.beginSession());
      if (!session.ok || !session.sessionId) throw new Error("session_start_failed");
      var old = progress && progress.active ? progress : null;
      if (old && old.sessionId !== session.sessionId) old = null;
      progress = old || {
        active: true,
        sessionId: session.sessionId,
        startedAt: session.startedAt,
        startedAtMs: Date.now(),
        index: 0,
        results: {}
      };
      progress.active = true;
      progress.previewRequestId = session.previewRequestId || "";
      progress.previewVersion = session.previewVersion || "";
      progress.startedAt = progress.startedAt || session.startedAt || "";
      progress.startedAtMs = progress.startedAtMs || Date.now();
      progress.stepStartedAtMs = Date.now();
      progress.deviceInfo = parseNative(bridge.getDeviceInfo());
      saveProgress();
      renderStep();
    } catch (error) {
      renderFailure("Teststation konnte nicht gestartet werden.");
    }
  }

  function renderStep() {
    if (!progress || !progress.active) return renderLauncher();
    var step = currentStep();
    clearRoot();
    var panel = document.createElement("section");
    panel.className = "kgg-station-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Tab-S9-Teststation");
    panel.innerHTML =
      "<div class=\"kgg-station-kicker\">" + escapeHtml(step.block) + "</div>" +
      "<h2>" + escapeHtml(step.title) + "</h2>" +
      "<p>" + escapeHtml(step.instruction) + "</p>" +
      "<div class=\"kgg-station-progress\"><span style=\"width:" +
      Math.round(((Number(progress.index) + 1) / STEPS.length) * 100) +
      "%\"></span></div>" +
      "<div class=\"kgg-station-meta\">Schritt " + (Number(progress.index) + 1) +
      " von " + STEPS.length + " · " + resultCount() + " bewertet</div>";
    if (step.camera) {
      var cameraNote = document.createElement("div");
      cameraNote.className = "kgg-station-note";
      cameraNote.textContent = "Ohne echten Tab-S9-Test nichts erfinden: Status „blockiert“ und der feste Grundcode dokumentieren den fehlenden Gerätetest.";
      panel.appendChild(cameraNote);
    }
    var actions = document.createElement("div");
    actions.className = "kgg-station-actions";
    ["passed", "failed", "blocked", "skipped"].forEach(function (status) {
      if (status === "skipped" && !step.optional) return;
      actions.appendChild(button(STATUS_LABELS[status], "kgg-station-status", function () {
        markStep(step, status);
      }, status));
    });
    panel.appendChild(actions);
    panel.appendChild(button("Teststation abbrechen", "kgg-station-secondary", function () {
      finishSession(true);
    }));
    root.appendChild(panel);
  }

  function markStep(step, status) {
    progress.results[step.id] = {
      testId: step.id,
      status: status,
      durationMs: Math.max(0, Date.now() - Number(progress.stepStartedAtMs || Date.now())),
      noteCode: step.noteCode
    };
    progress.index = Math.min(STEPS.length, Number(progress.index) + 1);
    progress.stepStartedAtMs = Date.now();
    saveProgress();
    if (progress.index >= STEPS.length) renderFinish();
    else renderStep();
  }

  function renderFinish() {
    clearRoot();
    var panel = document.createElement("section");
    panel.className = "kgg-station-panel";
    panel.innerHTML =
      "<div class=\"kgg-station-kicker\">Teststation</div>" +
      "<h2>Alle Schritte bewertet</h2>" +
      "<p>Der Bericht enthält nur grobe Gerätedaten, feste Statuswerte und künstliche Testfälle.</p>" +
      "<div class=\"kgg-station-meta\">" + resultCount() + " von " + STEPS.length + " Testfällen vorbereitet</div>";
    panel.appendChild(button("Bericht speichern und beenden", "kgg-station-launch", function () {
      finishSession(false);
    }));
    panel.appendChild(button("Zurück zum letzten Schritt", "kgg-station-secondary", function () {
      progress.index = Math.max(0, STEPS.length - 1);
      renderStep();
    }));
    panel.appendChild(button("Teststation abbrechen", "kgg-station-danger", function () {
      finishSession(true);
    }));
    root.appendChild(panel);
  }

  function finishSession(aborted) {
    if (!progress || !progress.active) return;
    var tests = STEPS.map(function (step) {
      return progress.results[step.id] || {
        testId: step.id,
        status: "blocked",
        durationMs: 0,
        noteCode: "not_executed"
      };
    });
    var result = parseNative(bridge.endSession(JSON.stringify({ tests: tests })));
    if (!result.ok) {
      renderFailure("Bericht konnte noch nicht gespeichert werden. Die Sitzung bleibt zum Fortsetzen aktiv.");
      return;
    }
    progress.active = false;
    progress.finished = true;
    progress.overallStatus = result.overallStatus || (aborted ? "blocked" : "passed");
    saveProgress();
    renderReportSaved();
  }

  function renderReportSaved() {
    clearRoot();
    var panel = document.createElement("section");
    panel.className = "kgg-station-panel";
    panel.innerHTML =
      "<div class=\"kgg-station-kicker\">Bericht lokal gespeichert</div>" +
      "<h2>Status: " + escapeHtml(STATUS_LABELS[progress.overallStatus] || progress.overallStatus) + "</h2>" +
      "<p>Das Öffnen erstellt nur einen vorausgefüllten GitHub-Issue-Entwurf. Absenden bleibt deine Bestätigung.</p>" +
      "<div class=\"kgg-station-meta\">Bei Offline-Zustand bleibt der Bericht lokal erhalten.</div>";
    panel.appendChild(button("GitHub-Issue-Entwurf öffnen", "kgg-station-launch", function () {
      if (!bridge.openReportIssue()) {
        renderFailure("Issue-Entwurf konnte nicht geöffnet werden. Der lokale Bericht bleibt erhalten.");
      }
    }));
    panel.appendChild(button("Schließen", "kgg-station-secondary", renderLauncher));
    root.appendChild(panel);
  }

  function renderFailure(message) {
    clearRoot();
    var panel = document.createElement("section");
    panel.className = "kgg-station-panel";
    panel.innerHTML =
      "<div class=\"kgg-station-kicker\">Teststation</div>" +
      "<h2>Hinweis</h2><p class=\"kgg-station-danger\">" + escapeHtml(message) + "</p>";
    panel.appendChild(button("Schließen", "kgg-station-secondary", function () {
      if (progress && progress.active) renderStep();
      else renderLauncher();
    }));
    root.appendChild(panel);
  }

  function finishAfterError() {
    if (!progress || !progress.active) return;
    try {
      var tests = STEPS.map(function (step) {
        return progress.results[step.id] || {
          testId: step.id,
          status: "blocked",
          durationMs: 0,
          noteCode: "not_executed"
        };
      });
      var result = parseNative(bridge.endSession(JSON.stringify({ tests: tests })));
      if (result.ok) {
        progress.active = false;
        progress.finished = true;
        progress.overallStatus = "blocked";
        saveProgress();
      }
    } catch (error) {
      // The native session remains pinned and can be continued after reload.
    }
  }

  addStyles();
  window.addEventListener("error", finishAfterError);
  window.addEventListener("unhandledrejection", finishAfterError);

  try {
    var context = window.KGGPreviewContext || {};
    if (!context.requestId || !context.patchHash || !context.baseSha || !context.previewVersion) {
      renderFailure("Preview-Kontext fehlt. Teststation nicht gestartet.");
    } else if (progress && progress.active) {
      var resumed = parseNative(bridge.beginSession());
      if (!resumed.ok || resumed.sessionId !== progress.sessionId) {
        progress = null;
        renderLauncher();
      } else {
        progress.previewRequestId = resumed.previewRequestId || progress.previewRequestId;
        progress.previewVersion = resumed.previewVersion || progress.previewVersion;
        progress.deviceInfo = parseNative(bridge.getDeviceInfo());
        progress.stepStartedAtMs = Date.now();
        saveProgress();
        renderStep();
      }
    } else if (progress && progress.finished) {
      renderReportSaved();
    } else {
      renderLauncher();
    }
  } catch (error) {
    renderFailure("Teststation konnte nicht geladen werden.");
  }
}());
