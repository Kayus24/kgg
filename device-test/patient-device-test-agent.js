(function () {
  "use strict";

  var API = window.KGGDualDeviceFixtures;
  if (!API || window.__kggPatientDeviceTestAgentV404) return;
  window.__kggPatientDeviceTestAgentV404 = true;

  var PAIR_KEY = "kgg_device_test_pair_v404";
  var STATE_PREFIX = "kgg_device_test_state_v404_";
  var REPORT_PREFIX = "kgg_device_test_report_v404_";
  var REPORT_URL = "https://github.com/Kayus24/kgg-device-test-reports/issues/new";
  var MAX_JOB_CHARS = 65536;
  var storage = window.KGGDeviceTestStorage;
  if (!storage) return;
  var pair = null;
  var job = null;
  var state = null;
  var root = null;
  var wakeLock = null;
  var wakeWarning = "";
  var scannerMeta = {};
  var pendingImportTimer = null;

  function now() { return new Date().toISOString(); }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }
  function readJson(key) {
    try { return JSON.parse(storage.getItem(key) || "null"); } catch (error) { return null; }
  }
  function writeJson(key, value) {
    storage.setItem(key, JSON.stringify(value));
  }
  function cleanStatus(status) {
    return ["passed", "failed", "blocked", "skipped"].indexOf(status) >= 0 ? status : "blocked";
  }
  function stateKey() { return STATE_PREFIX + pair.sessionId; }

  function parsePairing() {
    var params = new URLSearchParams(location.search);
    var token = params.get("kggTest") || "";
    if (token) {
      var parsed = API.decodePairing(token);
      writeJson(PAIR_KEY, parsed);
      try {
        params.delete("kggTest");
        history.replaceState(null, "", location.pathname + (params.toString() ? "?" + params.toString() : "") + location.hash);
      } catch (error) {}
      return parsed;
    }
    var stored = readJson(PAIR_KEY);
    if (!stored) return null;
    API.validatePairing(stored);
    return stored;
  }

  async function loadJob() {
    var response = await fetch(pair.jobUrl, { cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer" });
    if (!response.ok) throw new Error("Testauftrag nicht erreichbar (HTTP " + response.status + ")");
    var text = await response.text();
    if (!text || text.length > MAX_JOB_CHARS) throw new Error("Testauftrag ist leer oder zu groß");
    var parsed = JSON.parse(text);
    API.validateJob(parsed);
    if (!(await API.verifyJobHash(parsed))) throw new Error("Prüfsumme des Testauftrags stimmt nicht");
    if (parsed.sessionId !== pair.sessionId || parsed.requestId !== pair.requestId || parsed.sourceSha !== pair.sourceSha || parsed.jobHash !== pair.jobHash || parsed.patientPwaUrl !== pair.patientPwaUrl || parsed.profile !== pair.profile) {
      throw new Error("Kopplung und Testauftrag passen nicht zusammen");
    }
    return parsed;
  }

  function manualSteps() {
    if (!job || job.profile !== "full") return [];
    return [
      { id: "patient-add-plan", title: "Zweiten Plan hinzufügen", noteCode: "plan_add" },
      { id: "patient-replace-cancel", title: "Ersetzen und Abbrechen", noteCode: "plan_replace_cancel" },
      { id: "patient-switch-plan", title: "Zwischen Plänen wechseln", noteCode: "plan_switch" },
      { id: "patient-rename", title: "Plan umbenennen", noteCode: "plan_rename" },
      { id: "patient-values-reload", title: "Werte speichern und neu laden", noteCode: "values_reload" },
      { id: "patient-offline-restore", title: "Offline und wieder online", noteCode: "offline_restore" }
    ];
  }

  function allSteps() {
    var fixtureSteps = (job ? job.fixtures : []).map(function (fixture) {
      return {
        id: "scan-" + fixture.fixtureId,
        title: fixture.fixtureId,
        noteCode: "fixture_" + fixture.fixtureId.replace(/-/g, "_"),
        fixture: fixture
      };
    });
    return fixtureSteps.concat(manualSteps()).concat([
      { id: "camera-stream-stop", title: "Kamera sauber beendet", noteCode: "camera_stream_cleanup" }
    ]);
  }

  function freshState() {
    return {
      sessionId: pair.sessionId,
      requestId: pair.requestId,
      profile: pair.profile,
      startedAt: now(),
      index: 0,
      tests: {},
      telemetry: {},
      pendingImport: null,
      active: true
    };
  }

  function saveState() {
    if (state) writeJson(stateKey(), state);
  }

  function currentStep() {
    var steps = allSteps();
    return steps[Math.max(0, Math.min(steps.length - 1, Number(state.index) || 0))] || null;
  }

  function setResult(step, status, durationMs, noteCode) {
    state.tests[step.id] = {
      testId: step.id,
      status: cleanStatus(status),
      durationMs: Math.max(0, Math.min(86400000, Math.round(Number(durationMs) || 0))),
      noteCode: noteCode || step.noteCode
    };
    state.index = Math.min(allSteps().length, state.index + 1);
    saveState();
    render();
  }

  function deviceSummary() {
    var orientation = screen.width > screen.height ? "landscape" : "portrait";
    return {
      class: "android-pwa",
      runtime: "standalone-pwa",
      screen: {
        width: Math.max(0, Math.min(20000, Math.round(screen.width || 0))),
        height: Math.max(0, Math.min(20000, Math.round(screen.height || 0))),
        orientation: orientation
      },
      wakeLock: wakeWarning || "active"
    };
  }

  async function requestWakeLock() {
    if (!state || !state.active || document.visibilityState !== "visible") return;
    if (!("wakeLock" in navigator) || !navigator.wakeLock || typeof navigator.wakeLock.request !== "function") {
      wakeWarning = "unsupported";
      return;
    }
    try {
      wakeLock = await navigator.wakeLock.request("screen");
      wakeWarning = "active";
      wakeLock.addEventListener("release", function () { wakeLock = null; });
    } catch (error) {
      wakeWarning = "request-failed";
    }
  }

  async function releaseWakeLock() {
    if (!wakeLock) return;
    try { await wakeLock.release(); } catch (error) {}
    wakeLock = null;
  }

  function ensureUi() {
    if (root) return;
    var style = document.createElement("style");
    style.id = "kgg-device-test-agent-style";
    style.textContent = "#kgg-device-test-agent{position:fixed;z-index:12000;left:8px;right:8px;bottom:8px;max-width:700px;margin:auto;background:#07111f;color:#fff;border:2px solid #38bdf8;border-radius:18px;padding:12px;box-shadow:0 20px 60px #0009;font-family:system-ui,sans-serif}#kgg-device-test-agent.min .kgg-test-body{display:none}#kgg-device-test-agent h2{font-size:18px;margin:0 0 5px}#kgg-device-test-agent p{font-size:13px;line-height:1.35;margin:5px 0;color:#dbeafe}#kgg-device-test-agent .meta{font:11px ui-monospace,monospace;color:#93c5fd;overflow-wrap:anywhere}#kgg-device-test-agent .actions{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;margin-top:8px}#kgg-device-test-agent button{min-height:44px;border-radius:12px;border:1px solid #64748b;background:#fff;color:#0f172a;font-weight:900;padding:7px}#kgg-device-test-agent .primary{background:#0ea5e9;color:#fff;border-color:#38bdf8}#kgg-device-test-agent .pass{background:#16a34a;color:#fff}#kgg-device-test-agent .fail{background:#dc2626;color:#fff}#kgg-device-test-agent .top{display:flex;justify-content:space-between;gap:8px;align-items:center}#kgg-device-test-agent .top button{min-height:34px;padding:3px 10px}#kgg-device-test-agent .warn{background:#7c2d12;padding:8px;border-radius:10px}";
    document.head.appendChild(style);
    root = document.createElement("section");
    root.id = "kgg-device-test-agent";
    root.setAttribute("aria-live", "polite");
    document.body.appendChild(root);
  }

  function button(label, className, handler) {
    var node = document.createElement("button");
    node.type = "button";
    node.textContent = label;
    node.className = className || "";
    node.addEventListener("click", handler);
    return node;
  }

  function renderError(message) {
    ensureUi();
    root.innerHTML = '<div class="top"><h2>QR-Test blockiert</h2></div><p class="warn">' + esc(message) + "</p><p>Es wurden keine echten Testdaten übertragen.</p>";
  }

  function render() {
    ensureUi();
    var steps = allSteps();
    if (state.index >= steps.length) return renderFinish();
    var step = currentStep();
    root.innerHTML = '<div class="top"><h2>Oppo-Scanner · ' + esc(job.profile === "full" ? "Volltest" : "Schnelltest") + '</h2><button type="button" data-min>–</button></div><div class="kgg-test-body"><p class="meta">' + esc(pair.sessionId) + " · " + esc(pair.sourceSha.slice(0, 12)) + " · " + (state.index + 1) + "/" + steps.length + "</p><h2>" + esc(step.title) + "</h2><div data-copy></div></div>";
    root.querySelector("[data-min]").onclick = function () { root.classList.toggle("min"); };
    var actions = document.createElement("div");
    actions.className = "actions";
    if (step.fixture) {
      var detail = document.createElement("p");
      detail.textContent = step.fixture.format + " · " + step.fixture.exerciseCount + " Übungen · " + (step.fixture.required ? "Pflichttest" : "Diagnose");
      root.querySelector("[data-copy]").appendChild(detail);
      actions.appendChild(button(step.fixture.displayVariant === "photo" ? "Foto auswählen" : "Scanner öffnen", "primary", function () {
        state.stepStartedAt = Date.now();
        scannerMeta = { fixtureId: step.fixture.fixtureId, startedAt: Date.now() };
        saveState();
        var scanner = window.__kggPatientStartScanTest;
        if (!scanner) return renderError("Der echte Patienten-Scanner ist noch nicht bereit.");
        if (step.fixture.displayVariant === "photo" && typeof scanner.openPhotoScan === "function") scanner.openPhotoScan("update");
        else if (typeof scanner.openCameraScan === "function") scanner.openCameraScan("update");
        else renderError("Die Scanner-Schnittstelle fehlt.");
      }));
      actions.appendChild(button("Blockiert", "", function () { setResult(step, "blocked", Date.now() - (state.stepStartedAt || Date.now()), "scanner_blocked"); }));
      if (!step.fixture.required) {
        actions.appendChild(button("Diagnose nicht lesbar (erlaubt)", "", function () { setResult(step, "skipped", Date.now() - (state.stepStartedAt || Date.now()), "diagnostic_unreadable"); }));
      }
    } else if (step.id === "camera-stream-stop") {
      var stopped = state.lastStreamStopped === true;
      var info = document.createElement("p");
      info.textContent = stopped ? "Der letzte Kamerastream wurde beendet." : "Die App hat noch keinen sicheren Stream-Stopp bestätigt.";
      root.querySelector("[data-copy]").appendChild(info);
      actions.appendChild(button("Bestanden", "pass", function () { setResult(step, stopped ? "passed" : "failed", 0, stopped ? step.noteCode : "stream_not_stopped"); }));
      actions.appendChild(button("Fehlgeschlagen", "fail", function () { setResult(step, "failed", 0, "stream_not_stopped"); }));
    } else {
      var manual = document.createElement("p");
      manual.textContent = "Führe diesen Schritt in der Patienten-App mit künstlichen Daten aus. Danach bewertest du nur das sichtbare Ergebnis.";
      root.querySelector("[data-copy]").appendChild(manual);
      actions.appendChild(button("Bestanden", "pass", function () { setResult(step, "passed", Date.now() - (state.stepStartedAt || Date.now()), step.noteCode); }));
      actions.appendChild(button("Fehlgeschlagen", "fail", function () { setResult(step, "failed", Date.now() - (state.stepStartedAt || Date.now()), step.noteCode); }));
      actions.appendChild(button("Blockiert", "", function () { setResult(step, "blocked", Date.now() - (state.stepStartedAt || Date.now()), step.noteCode); }));
    }
    root.querySelector(".kgg-test-body").appendChild(actions);
    state.stepStartedAt = state.stepStartedAt || Date.now();
    saveState();
  }

  function telemetryValues(observed, meta) {
    return {
      fixtureId: observed.fixtureId,
      decoder: ["barcode-detector", "jsqr"].indexOf(meta.decoder) >= 0 ? meta.decoder : "unknown",
      recognitionMs: Math.max(0, Math.min(120000, Math.round(Number(meta.recognitionMs) || 0))),
      qrWidthRatioPct: Math.max(0, Math.min(100, Math.round(Number(meta.qrWidthRatioPct) || 0))),
      distanceBand: ["very-near", "near", "normal", "far", "very-far", "unknown"].indexOf(meta.distanceBand) >= 0 ? meta.distanceBand : "unknown",
      frameWidth: Math.max(0, Math.min(10000, Math.round(Number(meta.frameWidth) || 0))),
      frameHeight: Math.max(0, Math.min(10000, Math.round(Number(meta.frameHeight) || 0))),
      fpsBand: ["under-3", "3-5", "6-9", "10-plus", "unknown"].indexOf(meta.fpsBand) >= 0 ? meta.fpsBand : "unknown",
      angleBand: ["front", "slight", "steep", "unknown"].indexOf(meta.angleBand) >= 0 ? meta.angleBand : "unknown",
      brightnessBand: ["dark", "low", "normal", "bright", "unknown"].indexOf(meta.brightnessBand) >= 0 ? meta.brightnessBand : "unknown",
      blurBand: ["blurred", "soft", "sharp", "unknown"].indexOf(meta.blurBand) >= 0 ? meta.blurBand : "unknown",
      testFrameStatus: ["visible", "clipped", "unknown"].indexOf(meta.testFrameStatus) >= 0 ? meta.testFrameStatus : "unknown",
      format: observed.format,
      exerciseCount: observed.exerciseCount,
      fingerprint: observed.fingerprint,
      orderDigest: observed.orderDigest,
      storedFingerprint: observed.storedFingerprint || "none",
      visibleExerciseCount: Math.max(0, Math.min(40, Number(observed.visibleExerciseCount) || 0)),
      streamStopped: !!state.lastStreamStopped
    };
  }

  function consumeScan(raw, meta) {
    if (!state || !state.active) return false;
    var step = currentStep();
    if (!step || !step.fixture) return false;
    var started = state.stepStartedAt || Date.now();
    try {
      var decoded = window.KGGPlanFormat.decodePlanText(raw);
      var observed = {
        fixtureId: step.fixture.fixtureId,
        format: decoded.format,
        exerciseCount: decoded.raw.e.length,
        fingerprint: API.planFingerprint(decoded.raw),
        orderDigest: API.orderDigest(decoded.raw),
        storedFingerprint: "none",
        visibleExerciseCount: document.querySelectorAll("#list .ex").length
      };
      var matches = observed.format === step.fixture.format && observed.exerciseCount === step.fixture.exerciseCount && observed.fingerprint === step.fixture.expectedFingerprint && observed.orderDigest === step.fixture.expectedOrderDigest;
      state.telemetry[step.fixture.fixtureId] = telemetryValues(observed, Object.assign({}, scannerMeta, meta || {}));
      if (!matches) {
        setResult(step, "failed", Date.now() - started, "fixture_integrity_mismatch");
        return true;
      }
      if (step.fixture.importMode === "product") {
        state.pendingImport = { stepId: step.id, fixtureId: step.fixture.fixtureId, expectedFingerprint: step.fixture.expectedFingerprint, expectedOrderDigest: step.fixture.expectedOrderDigest, startedAt: started };
        saveState();
        schedulePendingImportCheck();
        return false;
      }
      setResult(step, "passed", Date.now() - started, step.noteCode);
      return true;
    } catch (error) {
      setResult(step, step.fixture.required ? "failed" : "skipped", Date.now() - started, step.fixture.required ? "fixture_decode_failed" : "diagnostic_unreadable");
      return true;
    }
  }

  function finishPendingImport(finalAttempt) {
    if (!state || !state.pendingImport) return true;
    var pending = state.pendingImport;
    var saved = readJson("kggCurrentPlanV1");
    var raw = saved && saved.plan;
    if (!raw || !Array.isArray(raw.e)) {
      if (!finalAttempt) return false;
      var missingStep = allSteps().find(function (candidate) { return candidate.id === pending.stepId; });
      state.pendingImport = null;
      if (missingStep) setResult(missingStep, "failed", Date.now() - pending.startedAt, "stored_plan_timeout");
      return true;
    }
    var fingerprint = API.planFingerprint(raw);
    var order = API.orderDigest(raw);
    var matches = fingerprint === pending.expectedFingerprint && order === pending.expectedOrderDigest;
    if (!matches && !finalAttempt) return false;
    var step = allSteps().find(function (candidate) { return candidate.id === pending.stepId; });
    var telemetry = state.telemetry[pending.fixtureId] || {};
    telemetry.storedFingerprint = fingerprint;
    telemetry.visibleExerciseCount = document.querySelectorAll("#list .ex").length;
    telemetry.streamStopped = state.lastStreamStopped === true;
    state.telemetry[pending.fixtureId] = telemetry;
    state.pendingImport = null;
    if (step) setResult(step, matches ? "passed" : "failed", Date.now() - pending.startedAt, matches ? step.noteCode : "stored_plan_mismatch");
    return true;
  }

  function schedulePendingImportCheck() {
    if (pendingImportTimer) clearTimeout(pendingImportTimer);
    var deadline = Date.now() + 120000;
    function poll() {
      pendingImportTimer = null;
      if (!state || !state.pendingImport) return;
      if (finishPendingImport(false)) return;
      if (Date.now() >= deadline) {
        finishPendingImport(true);
        return;
      }
      pendingImportTimer = setTimeout(poll, 250);
    }
    pendingImportTimer = setTimeout(poll, 150);
  }

  function emit(event, payload) {
    if (!state || !state.active) return;
    var clean = payload && typeof payload === "object" ? payload : {};
    if (event === "scanner-start") scannerMeta = Object.assign({}, scannerMeta, { startedAt: Date.now() });
    if (event === "scan-metrics") scannerMeta = Object.assign({}, scannerMeta, clean);
    if (event === "scanner-stop") {
      state.lastStreamStopped = clean.tracksStopped === true;
      saveState();
    }
  }

  function report() {
    var steps = allSteps();
    var tests = steps.map(function (step) {
      return state.tests[step.id] || { testId: step.id, status: "blocked", durationMs: 0, noteCode: "not_executed" };
    });
    var statuses = tests.map(function (test) { return test.status; });
    var overall = statuses.indexOf("failed") >= 0 ? "failed" : statuses.indexOf("blocked") >= 0 ? "blocked" : "passed";
    return {
      kind: "kgg_device_test_report",
      schemaVersion: 2,
      sessionId: pair.sessionId,
      role: "scanner",
      requestId: pair.requestId,
      sourceSha: pair.sourceSha,
      patchHash: job.patchHash,
      jobHash: pair.jobHash,
      appVersion: "v404-patient-test-pwa",
      device: deviceSummary(),
      profile: job.profile,
      startedAt: state.startedAt,
      endedAt: now(),
      tests: tests,
      fixtures: job.fixtures,
      telemetry: job.fixtures.map(function (fixture) {
        return state.telemetry[fixture.fixtureId] || {
          fixtureId: fixture.fixtureId,
          decoder: "unknown",
          recognitionMs: 0,
          qrWidthRatioPct: 0,
          distanceBand: "unknown",
          frameWidth: 0,
          frameHeight: 0,
          fpsBand: "unknown",
          angleBand: "unknown",
          brightnessBand: "unknown",
          blurBand: "unknown",
          testFrameStatus: "unknown",
          format: fixture.format,
          exerciseCount: 0,
          fingerprint: "00000000",
          orderDigest: "00000000",
          storedFingerprint: "none",
          visibleExerciseCount: 0,
          streamStopped: false
        };
      }),
      overallStatus: overall,
      syntheticOnly: true
    };
  }

  function openReportIssue() {
    var value = report();
    writeJson(REPORT_PREFIX + pair.sessionId, value);
    var body = "KGG device test report\n\n```json\n" + JSON.stringify(value, null, 2) + "\n```";
    var url = REPORT_URL + "?title=" + encodeURIComponent("KGG scanner Testbericht " + pair.sessionId) + "&body=" + encodeURIComponent(body);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function renderFinish() {
    state.active = false;
    saveState();
    releaseWakeLock();
    var value = report();
    var failed = value.tests.filter(function (test) { return test.status === "failed"; }).length;
    var blocked = value.tests.filter(function (test) { return test.status === "blocked"; }).length;
    root.innerHTML = '<div class="top"><h2>Oppo-Test abgeschlossen</h2></div><div class="kgg-test-body"><p>Fehler: ' + failed + " · Blockiert: " + blocked + '</p><p class="meta">' + esc(pair.sessionId) + '</p><div class="actions"><button type="button" class="primary" data-report>Privaten GitHub-Bericht öffnen</button><button type="button" data-reset>Test neu beginnen</button></div></div>';
    root.querySelector("[data-report]").onclick = openReportIssue;
    root.querySelector("[data-reset]").onclick = function () {
      storage.removeItem(stateKey());
      state = freshState();
      saveState();
      requestWakeLock();
      render();
    };
  }

  async function init() {
    try {
      pair = parsePairing();
      if (!pair) return;
      job = await loadJob();
      state = readJson(stateKey());
      if (!state || state.sessionId !== pair.sessionId || state.requestId !== pair.requestId) state = freshState();
      saveState();
      window.KGGPatientDeviceTestObserver = Object.freeze({ emit: emit, consumeScan: consumeScan });
      await requestWakeLock();
      if (state.pendingImport) schedulePendingImportCheck();
      render();
    } catch (error) {
      renderError(error && error.message ? error.message : String(error));
    }
  }

  window.__kggPatientDeviceTestAgentTest = Object.freeze({
    report: function () { return state && job && pair ? clone(report()) : null; }
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") requestWakeLock();
  });
  window.addEventListener("pagehide", function () { releaseWakeLock(); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
