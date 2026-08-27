(function () {
  "use strict";

  var bridge = window.KGGDeviceTestStation;
  var API = window.KGGDualDeviceFixtures;
  if (!bridge || !API) return;

  var ROOT_ID = "kgg-device-test-station";
  var STORAGE_PREFIX = "kgg_dual_device_display_v404_";
  var PREVIEW_MANIFEST_URL = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/index.json";
  var PREVIEW_HTML_PREFIX = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/";
  var DEVICE_JOB_PREFIX = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/";
  var PATIENT_PWA_BASE_URL = "https://kayus24.github.io/kgg-patient-preview/device-test/";
  var MAX_MANIFEST_CHARS = 262144;
  var MAX_JOB_CHARS = 65536;
  var MAX_PWA_META_CHARS = 16384;
  var ADMIN_STEPS = [
    { id: "admin-portrait", title: "Hochformat", instruction: "Prüfe die Admin-App im Hochformat.", noteCode: "layout_portrait" },
    { id: "admin-landscape", title: "Querformat", instruction: "Drehe das Tab ins Querformat und prüfe Menü und Karten.", noteCode: "layout_landscape" },
    { id: "admin-split-screen", title: "Geteilter Bildschirm", instruction: "Öffne den geteilten Bildschirm. Die App muss bedienbar bleiben.", noteCode: "layout_split_screen" },
    { id: "admin-package-button", title: "Paket-Schaltfläche", instruction: "Öffne die Paket-Schaltfläche mit einer Berührung.", noteCode: "package_button" },
    { id: "admin-touch-dialog-save", title: "Dialog und Speichern", instruction: "Speichere einen Plan mit einem künstlichen Namen.", noteCode: "touch_dialog_save" },
    { id: "admin-seven-exercises", title: "Sieben künstliche Übungen", instruction: "Lege genau sieben künstliche Übungen an.", noteCode: "synthetic_exercise_set_7" },
    { id: "admin-reorder-save-reload", title: "Reihenfolge und Neuladen", instruction: "Ändere die Reihenfolge, speichere und lade neu.", noteCode: "reorder_persistence" }
  ];
  var job = null;
  var runtimeContext = null;
  var state = null;
  var root = null;

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }
  function parseNative(value) {
    try { return JSON.parse(String(value || "")); } catch (error) { return { ok: false, error: "native_response_invalid" }; }
  }
  function readJson(key) {
    try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (error) { return null; }
  }
  function writeJson(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (error) {}
  }
  function storageKey() { return STORAGE_PREFIX + job.sessionId; }
  function now() { return new Date().toISOString(); }

  async function fetchJson(url, maxChars, label) {
    var response = await fetch(url, { cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer" });
    if (!response.ok) throw new Error(label + " nicht erreichbar (HTTP " + response.status + ")");
    var text = await response.text();
    if (!text || text.length > maxChars) throw new Error(label + " ist leer oder zu groß.");
    return JSON.parse(text);
  }

  function runtimeFromLatest(latest) {
    if (!latest || typeof latest !== "object" || Array.isArray(latest)) throw new Error("Aktueller Preview-Stand fehlt.");
    var requestId = String(latest.requestId || "");
    var sourceSha = String(latest.sourceSha || "").toLowerCase();
    var patchHash = String(latest.patchHash || "").toLowerCase();
    var jobUrl = String(latest.deviceTestJobUrl || "");
    if (latest.kind !== "kgg_gpt_preview" || latest.sourceType !== "existing-main") throw new Error("Aktueller Preview-Stand ist kein persistenter Device-Test.");
    if (!/^[a-z0-9][a-z0-9-]{5,63}$/.test(requestId)) throw new Error("Preview Request-ID ist ungültig.");
    if (!/^[a-f0-9]{40}$/.test(sourceSha) || String(latest.baseSha || "").toLowerCase() !== sourceSha || String(latest.commitSha || "").toLowerCase() !== sourceSha) throw new Error("Preview Source-SHA ist nicht exakt gepinnt.");
    if (!/^[a-f0-9]{64}$/.test(patchHash) || !/^[a-f0-9]{64}$/.test(String(latest.sha256 || "").toLowerCase())) throw new Error("Preview Prüfsumme ist ungültig.");
    if (!Number.isInteger(latest.rolloutCode) || latest.rolloutCode <= 0) throw new Error("Preview Rollout ist ungültig.");
    var expectedHtmlUrl = PREVIEW_HTML_PREFIX + requestId + "/admin.html";
    var expectedJobUrl = DEVICE_JOB_PREFIX + requestId + "/job.json";
    if (String(latest.url || "") !== expectedHtmlUrl || jobUrl !== expectedJobUrl) throw new Error("Preview- und Job-Adressen passen nicht zur Request-ID.");
    return {
      kind: "kgg_device_test_runtime_context",
      schemaVersion: 1,
      requestId: requestId,
      sourceSha: sourceSha,
      patchHash: patchHash,
      jobUrl: jobUrl,
      rolloutCode: latest.rolloutCode
    };
  }

  function immutablePatientPwaUrl(value, requestId) {
    var url = String(value || "");
    if (url.indexOf(PATIENT_PWA_BASE_URL) !== 0) throw new Error("Patient-Test-PWA-Adresse ist ungültig.");
    var suffix = url.slice(PATIENT_PWA_BASE_URL.length);
    var match = suffix.match(/^([a-z0-9][a-z0-9-]{5,63})\/([0-9]+-[0-9]+)\/$/);
    if (!match || match[1] !== requestId) throw new Error("Patient-Test-PWA ist nicht laufbezogen gepinnt.");
    return url;
  }

  async function verifyPatientPwa(jobValue) {
    var patientPwaUrl = immutablePatientPwaUrl(jobValue.patientPwaUrl, jobValue.requestId);
    var meta = await fetchJson(patientPwaUrl + "device-test-meta.json", MAX_PWA_META_CHARS, "Patient-Test-PWA-Metadaten");
    if (!meta || meta.kind !== "kgg_device_test_pwa_meta" || meta.schemaVersion !== 1 || meta.syntheticOnly !== true) {
      throw new Error("Patient-Test-PWA-Metadaten sind ungültig.");
    }
    if (String(meta.requestId || "") !== jobValue.requestId
        || String(meta.sourceSha || "").toLowerCase() !== jobValue.sourceSha
        || String(meta.jobHash || "").toLowerCase() !== jobValue.jobHash) {
      throw new Error("Patient-Test-PWA und Testauftrag stammen nicht aus demselben Lauf.");
    }
  }

  async function fetchJob() {
    var manifest = await fetchJson(PREVIEW_MANIFEST_URL, MAX_MANIFEST_CHARS, "Preview-Manifest");
    if (manifest.kind !== "kgg_gpt_preview_manifest" || !manifest.latest) throw new Error("Preview-Manifest ist ungültig.");
    var current = runtimeFromLatest(manifest.latest);
    var value = await fetchJson(current.jobUrl, MAX_JOB_CHARS, "Testauftrag");
    API.validateJob(value);
    if (!(await API.verifyJobHash(value))) throw new Error("Prüfsumme des Testauftrags stimmt nicht.");
    immutablePatientPwaUrl(value.patientPwaUrl, value.requestId);
    if (value.requestId !== current.requestId || value.sourceSha !== current.sourceSha || value.patchHash !== current.patchHash) {
      throw new Error("Preview und Testauftrag stammen nicht aus demselben Lauf.");
    }
    await verifyPatientPwa(value);
    current.sessionId = value.sessionId;
    current.jobHash = value.jobHash;
    // The native bridge keeps its stable preview-only base boundary; the synthetic run URL stays in the validated job.
    current.patientPwaUrl = PATIENT_PWA_BASE_URL;
    current.profile = value.profile;
    runtimeContext = Object.freeze(current);
    return value;
  }

  function steps() {
    var output = job.profile === "full" ? ADMIN_STEPS.slice() : [];
    output.push({ id: "display-pairing", title: "Oppo mit Test verbinden", instruction: "Scanne diesen Verbindungs-QR zuerst mit dem Oppo.", noteCode: "pairing_displayed", pairing: true });
    job.fixtures.forEach(function (fixture) {
      output.push({
        id: "display-" + fixture.fixtureId,
        title: fixture.fixtureId,
        instruction: fixture.displayVariant === "photo" ? "Fotografiere diesen QR mit dem Oppo und wähle das Foto in der Test-PWA aus." : "Lasse den QR vom echten Patienten-Scanner auf dem Oppo lesen.",
        noteCode: "display_" + fixture.fixtureId.replace(/-/g, "_"),
        fixture: fixture
      });
    });
    return output;
  }

  function ensureRoot() {
    if (root) return;
    var old = document.getElementById(ROOT_ID);
    if (old) old.remove();
    root = document.createElement("section");
    root.id = ROOT_ID;
    document.documentElement.appendChild(root);
    var style = document.createElement("style");
    style.id = "kgg-device-test-station-style";
    style.textContent = "#" + ROOT_ID + "{all:initial;position:fixed;z-index:2147483000;inset:auto 12px 12px 12px;font-family:system-ui,sans-serif;color:#0f172a}#" + ROOT_ID + " *{box-sizing:border-box}#" + ROOT_ID + " .panel{max-width:920px;margin:auto;background:#fff;border:2px solid #0ea5e9;border-radius:22px;padding:16px;box-shadow:0 24px 70px #0007;max-height:94vh;overflow:auto}#" + ROOT_ID + " h2{font-size:24px;margin:0 0 8px}#" + ROOT_ID + " p{font-size:16px;line-height:1.4;margin:7px 0}#" + ROOT_ID + " .meta{font:12px ui-monospace,monospace;color:#475569;overflow-wrap:anywhere}#" + ROOT_ID + " .actions{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}#" + ROOT_ID + " button{min-height:50px;border:1px solid #94a3b8;border-radius:13px;background:#fff;color:#0f172a;font-size:15px;font-weight:900;padding:8px}#" + ROOT_ID + " .primary{background:#0284c7;color:#fff;border-color:#0369a1}#" + ROOT_ID + " .pass{background:#16a34a;color:#fff}#" + ROOT_ID + " .fail{background:#dc2626;color:#fff}#" + ROOT_ID + " .qr-stage{margin:12px auto;padding:22px;background:#fff;border:8px solid #e2e8f0;position:relative;width:min(100%,760px);min-height:360px;display:flex;align-items:center;justify-content:center;overflow:hidden}#" + ROOT_ID + " .marker{position:absolute;width:34px;height:34px;background:#00a6ff;border:5px solid #003b5c}#" + ROOT_ID + " .m1{left:4px;top:4px}#" + ROOT_ID + " .m2{right:4px;top:4px}#" + ROOT_ID + " .m3{right:4px;bottom:4px}#" + ROOT_ID + " .m4{left:4px;bottom:4px}#" + ROOT_ID + " .qr-stage img{display:block;width:min(72vw,620px);height:auto;image-rendering:pixelated}#" + ROOT_ID + " .variant-far-angle img{width:min(36vw,340px);transform:perspective(900px) rotateY(19deg) rotateZ(3deg)}#" + ROOT_ID + " .variant-low-contrast img{opacity:.56;filter:contrast(.72)}#" + ROOT_ID + " .variant-photo img{width:min(82vw,700px)}#" + ROOT_ID + " .warning{background:#ffedd5;color:#9a3412;padding:10px;border-radius:12px;font-weight:800}@media(max-width:640px){#" + ROOT_ID + "{inset:6px}#" + ROOT_ID + " .panel{padding:11px;border-radius:16px}#" + ROOT_ID + " .actions{grid-template-columns:1fr}#" + ROOT_ID + " .qr-stage{padding:14px;min-height:300px}}";
    document.head.appendChild(style);
  }

  function button(label, className, handler, status) {
    var node = document.createElement("button");
    node.type = "button";
    node.textContent = label;
    node.className = className || "";
    if (status) node.dataset.status = status;
    node.addEventListener("click", handler);
    return node;
  }

  function renderLauncher() {
    ensureRoot();
    root.innerHTML = '<div class="panel"><h2>Dual-Geräte QR-Teststation v404</h2><p>Das Galaxy Tab zeigt QR-Codes. Das Oppo scannt sie mit der Patienten-Test-PWA.</p><p>Es werden nur künstliche Testdaten verwendet.</p><div class="actions"></div></div>';
    root.querySelector(".actions").appendChild(button("Teststation laden", "primary", start));
  }

  function renderError(error) {
    ensureRoot();
    root.innerHTML = '<div class="panel"><h2>Teststation blockiert</h2><p class="warning">' + esc(error && error.message ? error.message : error) + '</p><div class="actions"></div></div>';
    root.querySelector(".actions").appendChild(button("Erneut versuchen", "primary", start));
  }

  async function start() {
    try {
      job = await fetchJob();
      var nativeSession = parseNative(bridge.beginSession(JSON.stringify(runtimeContext)));
      if (!nativeSession.ok || nativeSession.sessionId !== job.sessionId || nativeSession.jobHash !== job.jobHash || nativeSession.previewRequestId !== job.requestId) throw new Error("Native Sitzung passt nicht zum aktuellen Testauftrag.");
      state = readJson(storageKey());
      if (!state || state.sessionId !== job.sessionId || state.requestId !== job.requestId) {
        state = { active: true, sessionId: job.sessionId, requestId: job.requestId, profile: job.profile, startedAt: nativeSession.startedAt || now(), index: 0, tests: {}, stepStartedAt: Date.now() };
      }
      writeJson(storageKey(), state);
      renderStep();
    } catch (error) {
      renderError(error);
    }
  }

  function pairingUrl() {
    var token = API.encodePairing({
      kind: API.pairingKind,
      schemaVersion: 1,
      sessionId: job.sessionId,
      requestId: job.requestId,
      sourceSha: job.sourceSha,
      jobHash: job.jobHash,
      profile: job.profile,
      jobUrl: runtimeContext.jobUrl,
      patientPwaUrl: job.patientPwaUrl
    });
    return job.patientPwaUrl + (job.patientPwaUrl.indexOf("?") >= 0 ? "&" : "?") + "kggTest=" + encodeURIComponent(token);
  }

  function planUrl(fixture) {
    var definition = API.fixtureById(fixture.fixtureId);
    if (!definition) throw new Error("Fixture fehlt: " + fixture.fixtureId);
    var raw = API.syntheticPlan(definition);
    var fingerprint = API.planFingerprint(raw);
    var order = API.orderDigest(raw);
    if (fingerprint !== fixture.expectedFingerprint || order !== fixture.expectedOrderDigest) throw new Error("Fixture-Prüfsumme stimmt nicht: " + fixture.fixtureId);
    var code = fixture.format === "KGGH2" ? window.KGGPlanFormat.encodeKggH2(raw) : window.KGGPlanFormat.encodeKggH3(raw);
    return job.patientPwaUrl + "?plan=" + encodeURIComponent(code);
  }

  function qrDataUrl(value) {
    if (typeof window.qrcode !== "function") throw new Error("Lokaler QR-Generator fehlt.");
    var qr = window.qrcode(0, "M");
    qr.addData(value);
    qr.make();
    return qr.createDataURL(6, 5);
  }

  function qrStage(value, variant) {
    var stage = document.createElement("div");
    stage.className = "qr-stage variant-" + String(variant || "normal");
    ["m1", "m2", "m3", "m4"].forEach(function (name) {
      var marker = document.createElement("span");
      marker.className = "marker " + name;
      marker.setAttribute("aria-hidden", "true");
      stage.appendChild(marker);
    });
    var image = document.createElement("img");
    image.alt = "Synthetischer QR-Testcode";
    image.src = qrDataUrl(value);
    stage.appendChild(image);
    return stage;
  }

  function renderStep() {
    ensureRoot();
    var list = steps();
    if (state.index >= list.length) return renderFinish();
    var step = list[state.index];
    state.stepStartedAt = state.stepStartedAt || Date.now();
    writeJson(storageKey(), state);
    root.innerHTML = '<div class="panel"><p class="meta">' + esc(job.sessionId) + " · " + esc(job.sourceSha.slice(0, 12)) + " · " + esc(job.profile) + " · " + (state.index + 1) + "/" + list.length + '</p><h2>' + esc(step.title) + '</h2><p>' + esc(step.instruction) + '</p><div data-content></div><div class="actions"></div></div>';
    var content = root.querySelector("[data-content]");
    if (step.pairing || step.fixture) {
      try {
        var value = step.pairing ? pairingUrl() : planUrl(step.fixture);
        content.appendChild(qrStage(value, step.fixture ? step.fixture.displayVariant : "normal"));
        var detail = document.createElement("p");
        detail.className = "meta";
        detail.textContent = step.pairing ? "Verbindungs-QR · keine Patientendaten" : step.fixture.format + " · " + step.fixture.exerciseCount + " Übungen · Fingerabdruck " + step.fixture.expectedFingerprint;
        content.appendChild(detail);
      } catch (error) {
        var warning = document.createElement("p");
        warning.className = "warning";
        warning.textContent = "QR konnte nicht erzeugt werden: " + error.message;
        content.appendChild(warning);
      }
    }
    var actions = root.querySelector(".actions");
    actions.appendChild(button("Bestanden", "pass", function () { mark(step, "passed"); }, "passed"));
    actions.appendChild(button("Fehlgeschlagen", "fail", function () { mark(step, "failed"); }, "failed"));
    actions.appendChild(button("Blockiert", "", function () { mark(step, "blocked"); }, "blocked"));
    if (step.fixture && !step.fixture.required) {
      actions.appendChild(button("Diagnose nicht lesbar (erlaubt)", "", function () { mark(step, "skipped", "diagnostic_unreadable"); }, "skipped"));
    }
  }

  function mark(step, status, noteCode) {
    state.tests[step.id] = {
      testId: step.id,
      status: status,
      durationMs: Math.max(0, Math.min(86400000, Date.now() - (state.stepStartedAt || Date.now()))),
      noteCode: noteCode || step.noteCode
    };
    state.index += 1;
    state.stepStartedAt = Date.now();
    writeJson(storageKey(), state);
    renderStep();
  }

  function buildReport() {
    var list = steps();
    var tests = list.map(function (step) {
      return state.tests[step.id] || { testId: step.id, status: "blocked", durationMs: 0, noteCode: "not_executed" };
    });
    return { role: "display", profile: job.profile, jobHash: job.jobHash, tests: tests, fixtures: job.fixtures };
  }

  function renderFinish() {
    root.innerHTML = '<div class="panel"><h2>Tab-Anzeigetest abgeschlossen</h2><p>Jetzt wird der private GitHub-Bericht vorbereitet.</p><div class="actions"></div></div>';
    var actions = root.querySelector(".actions");
    actions.appendChild(button("Bericht speichern", "primary", function () {
      var result = parseNative(bridge.endSession(JSON.stringify(buildReport())));
      if (!result.ok) return renderError("Bericht wurde abgelehnt: " + (result.error || "unbekannt"));
      state.active = false;
      writeJson(storageKey(), state);
      root.querySelector(".panel").innerHTML = '<h2>Bericht gespeichert</h2><p>Öffne den vorbereiteten privaten GitHub-Bericht und tippe dort auf „Submit“.</p><div class="actions"></div>';
      root.querySelector(".actions").appendChild(button("GitHub-Bericht öffnen", "primary", function () { bridge.openReportIssue(); }));
    }));
    actions.appendChild(button("Letzten Schritt prüfen", "", function () { state.index = Math.max(0, steps().length - 1); writeJson(storageKey(), state); renderStep(); }));
  }

  function boot() {
    if (!document.documentElement || !document.head) {
      window.setTimeout(boot, 50);
      return;
    }
    renderLauncher();
  }

  boot();
})();
