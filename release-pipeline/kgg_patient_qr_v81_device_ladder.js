#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { chromium } = require("playwright");
const qrFactory = require("qrcode-generator");

const ROOT = path.resolve(__dirname, "..");
const JSQR_PATH = require.resolve("jsqr");
const FFLATE = require(path.join(ROOT, "vendor", "fflate-0.8.3.js"));
const SCANNER_PATH = path.join(ROOT, "patient-start-scan.js");
const OUTPUT_DIR = path.join(ROOT, "tmp", "patient-qr-v81-device-ladder");
const VERSION = "patient-qr-v81-device-ladder-1";
const SCANNER_SOURCE = fs.readFileSync(SCANNER_PATH, "utf8");
const SCANNER_VERSION = (SCANNER_SOURCE.match(/const VERSION='([^']+)'/) || [])[1] || "unknown";
const TOTAL_TIMEOUT_MS = Number(process.env.KGG_PATIENT_QR_LADDER_TIMEOUT_MS || 300000);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}

function fingerprint(value) {
  const json = JSON.stringify(stable(value));
  let hash = 2166136261;
  for (let index = 0; index < json.length; index += 1) {
    hash ^= json.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function encodeH2(raw) {
  return "KGGH2:" + Buffer.from(JSON.stringify(raw), "utf8").toString("base64url");
}

function encodeH3(raw) {
  return "KGGH3:" + Buffer.from(FFLATE.zlibSync(Buffer.from(JSON.stringify(raw), "utf8"))).toString("base64url");
}

function makePlan(count) {
  return {
    v: 2,
    i: "v81-synthetic-" + count,
    t: "Synthetischer KGGH3-Plan " + count,
    d: 6,
    extendDays: true,
    stepDays: 6,
    e: Array.from({ length: count }, (_, index) => [
      "Übung " + (index + 1),
      index % 4 === 0 ? 4 : 3,
      index % 3 === 0 ? "LR" : "B",
      "kg",
      "Wdh",
      String(10 + index),
      String(8 + index),
      "",
      "",
      "Video öffnen",
      "exercise"
    ]),
    patient: {
      name: "Synthetik Test",
      date: "2026-08-23",
      therapist: "Geräte-Ladder",
      notes: "Nur synthetische Diagnose"
    },
    m: {
      source: "kgg-therapist-app",
      schema: "KGGH3",
      createdAt: "2026-08-23T00:00:00.000Z",
      media: { expected: false, count: 0, ready: 0, status: "none" }
    }
  };
}

function makeMatrix(code) {
  const qr = qrFactory(0, "M");
  qr.addData(code);
  qr.make();
  const count = qr.getModuleCount();
  return Array.from({ length: count }, (_, row) =>
    Array.from({ length: count }, (_, col) => qr.isDark(row, col))
  );
}

function createServer() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const relative = url.pathname === "/__patient_qr_v81__.html" ? "index.html" : url.pathname.replace(/^\/+/, "");
    const target = path.resolve(ROOT, relative || "index.html");
    if (!target.startsWith(ROOT + path.sep) && target !== ROOT) {
      response.writeHead(403).end("forbidden");
      return;
    }
    try {
      const body = fs.readFileSync(target);
      const type = target.endsWith(".html")
        ? "text/html; charset=utf-8"
        : target.endsWith(".js")
          ? "application/javascript; charset=utf-8"
          : target.endsWith(".css")
            ? "text/css; charset=utf-8"
            : target.endsWith(".png")
              ? "image/png"
              : "application/octet-stream";
      response.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store" });
      response.end(body);
    } catch (error) {
      response.writeHead(404).end("not found");
    }
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, baseUrl: "http://127.0.0.1:" + address.port });
    });
  });
}

async function renderFrame(page, matrix, spec) {
  const dataUrl = await page.evaluate(({ modules, frame }) => {
    const width = frame.width;
    const height = frame.height;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.fillStyle = frame.background || "#e7e7e7";
    ctx.fillRect(0, 0, width, height);

    const quiet = 4;
    const count = modules.length;
    const qrCanvas = document.createElement("canvas");
    qrCanvas.width = count + quiet * 2;
    qrCanvas.height = count + quiet * 2;
    const qrCtx = qrCanvas.getContext("2d");
    qrCtx.fillStyle = "#fff";
    qrCtx.fillRect(0, 0, qrCanvas.width, qrCanvas.height);
    qrCtx.fillStyle = "#000";
    for (let row = 0; row < count; row += 1) {
      for (let col = 0; col < count; col += 1) {
        if (modules[row][col]) qrCtx.fillRect(col + quiet, row + quiet, 1, 1);
      }
    }

    const size = Math.max(24, Math.round(Math.min(width, height) * (frame.qrFraction || 0.52)));
    const centerX = width / 2 + (frame.offsetX || 0);
    const centerY = height / 2 + (frame.offsetY || 0);
    const rotation = ((frame.rotation || 0) * Math.PI) / 180;
    const blur = Number(frame.blur || 0);
    const brightness = frame.brightness === undefined ? 1 : frame.brightness;
    const contrast = frame.contrast === undefined ? 1 : frame.contrast;

    const drawTriangle = (image, source, destination) => {
      const [s1, s2, s3] = source;
      const [d1, d2, d3] = destination;
      const denominator = s1.x * (s2.y - s3.y) + s2.x * (s3.y - s1.y) + s3.x * (s1.y - s2.y);
      if (Math.abs(denominator) < 0.000001) return;
      const a = (d1.x * (s2.y - s3.y) + d2.x * (s3.y - s1.y) + d3.x * (s1.y - s2.y)) / denominator;
      const b = (d1.y * (s2.y - s3.y) + d2.y * (s3.y - s1.y) + d3.y * (s1.y - s2.y)) / denominator;
      const c = (d1.x * (s3.x - s2.x) + d2.x * (s1.x - s3.x) + d3.x * (s2.x - s1.x)) / denominator;
      const d = (d1.y * (s3.x - s2.x) + d2.y * (s1.x - s3.x) + d3.y * (s2.x - s1.x)) / denominator;
      const e = (d1.x * (s2.x * s3.y - s3.x * s2.y) + d2.x * (s3.x * s1.y - s1.x * s3.y) + d3.x * (s1.x * s2.y - s2.x * s1.y)) / denominator;
      const f = (d1.y * (s2.x * s3.y - s3.x * s2.y) + d2.y * (s3.x * s1.y - s1.x * s3.y) + d3.y * (s1.x * s2.y - s2.x * s1.y)) / denominator;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(d1.x, d1.y);
      ctx.lineTo(d2.x, d2.y);
      ctx.lineTo(d3.x, d3.y);
      ctx.closePath();
      ctx.clip();
      ctx.transform(a, b, c, d, e, f);
      ctx.drawImage(image, 0, 0);
      ctx.restore();
    };

    const drawPerspective = (motionOffset) => {
      const yaw = ((frame.yaw || 0) * Math.PI) / 180;
      const pitch = ((frame.pitch || 0) * Math.PI) / 180;
      const cosYaw = Math.cos(yaw);
      const sinYaw = Math.sin(yaw);
      const cosPitch = Math.cos(pitch);
      const sinPitch = Math.sin(pitch);
      const cameraDistance = 2.2;
      const corners = frame.cornerWarp || [[0, 0], [0, 0], [0, 0], [0, 0]];
      const vertex = (u, v) => {
        const x = u - 0.5;
        const y = v - 0.5;
        const xYaw = x * cosYaw;
        const zYaw = -x * sinYaw;
        const yPitch = y * cosPitch - zYaw * sinPitch;
        const zPitch = y * sinPitch + zYaw * cosPitch;
        const projection = cameraDistance / (cameraDistance + zPitch);
        const topX = corners[0][0] * (1 - u) + corners[1][0] * u;
        const bottomX = corners[3][0] * (1 - u) + corners[2][0] * u;
        const topY = corners[0][1] * (1 - u) + corners[1][1] * u;
        const bottomY = corners[3][1] * (1 - u) + corners[2][1] * u;
        return {
          x: xYaw * projection * size + (topX * (1 - v) + bottomX * v) * size + motionOffset,
          y: yPitch * projection * size + (topY * (1 - v) + bottomY * v) * size
        };
      };
      const cells = 28;
      for (let row = 0; row < cells; row += 1) {
        for (let col = 0; col < cells; col += 1) {
          const u0 = col / cells;
          const u1 = (col + 1) / cells;
          const v0 = row / cells;
          const v1 = (row + 1) / cells;
          const s00 = { x: u0 * qrCanvas.width, y: v0 * qrCanvas.height };
          const s10 = { x: u1 * qrCanvas.width, y: v0 * qrCanvas.height };
          const s11 = { x: u1 * qrCanvas.width, y: v1 * qrCanvas.height };
          const s01 = { x: u0 * qrCanvas.width, y: v1 * qrCanvas.height };
          const d00 = vertex(u0, v0);
          const d10 = vertex(u1, v0);
          const d11 = vertex(u1, v1);
          const d01 = vertex(u0, v1);
          drawTriangle(qrCanvas, [s00, s10, s11], [d00, d10, d11]);
          drawTriangle(qrCanvas, [s00, s11, s01], [d00, d11, d01]);
        }
      }
    };

    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.rotate(rotation);
    ctx.filter = "brightness(" + brightness + ") contrast(" + contrast + ") blur(" + blur + "px)";
    ctx.imageSmoothingEnabled = false;
    const copies = frame.motion ? 7 : 1;
    for (let copy = 0; copy < copies; copy += 1) {
      const motionOffset = copies === 1 ? 0 : ((copy / (copies - 1)) - 0.5) * frame.motion;
      ctx.globalAlpha = copies === 1 ? 1 : 0.22;
      if (frame.yaw || frame.pitch || frame.cornerWarp) drawPerspective(motionOffset);
      else ctx.drawImage(qrCanvas, -size / 2 + motionOffset, -size / 2, size, size);
    }
    ctx.restore();

    const noise = Number(frame.noise || 0);
    if (noise > 0) {
      const image = ctx.getImageData(0, 0, width, height);
      let seed = (24061986 ^ width ^ (height << 8) ^ Math.round(noise * 100)) >>> 0;
      const random = () => {
        seed ^= seed << 13;
        seed ^= seed >>> 17;
        seed ^= seed << 5;
        return (seed >>> 0) / 4294967296;
      };
      for (let index = 0; index < image.data.length; index += 4) {
        const delta = Math.round((random() * 2 - 1) * noise);
        image.data[index] = Math.max(0, Math.min(255, image.data[index] + delta));
        image.data[index + 1] = Math.max(0, Math.min(255, image.data[index + 1] + delta));
        image.data[index + 2] = Math.max(0, Math.min(255, image.data[index + 2] + delta));
      }
      ctx.putImageData(image, 0, 0);
    }
    return canvas.toDataURL("image/png");
  }, { modules: matrix, frame: spec });
  return Buffer.from(dataUrl.split(",")[1], "base64");
}

function initScript(detectorMode, detectorRaw) {
  return String.raw`(() => {
    const config = window.__kggDeviceConfig = {
      detectorMode: ${JSON.stringify(detectorMode)},
      detectorRaw: ${JSON.stringify(detectorRaw || "")},
      stream: null,
      constraints: null,
      detectorAttempts: 0,
      jsQrAttempts: 0,
      jsQrLast: "",
      barcodeLast: ""
    };
    const mediaDevices = navigator.mediaDevices || {};
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: mediaDevices });
    mediaDevices.getUserMedia = async (constraints) => {
      config.constraints = constraints;
      if (config.detectorMode === "deny") throw new DOMException("synthetic camera denial", "NotAllowedError");
      if (!config.stream) throw new Error("synthetic stream not ready");
      return config.stream;
    };
    if (${JSON.stringify(detectorMode)} === "absent") {
      try { delete window.BarcodeDetector; } catch (error) { window.BarcodeDetector = undefined; }
    } else {
      Object.defineProperty(window, "BarcodeDetector", {
        configurable: true,
        value: class DeviceLadderBarcodeDetector {
          static async getSupportedFormats() { return ["qr_code"]; }
          async detect() {
            config.detectorAttempts += 1;
            if (config.detectorMode === "throw") throw new Error("synthetic native detector failure");
            if (config.detectorMode === "success") {
              config.barcodeLast = config.detectorRaw;
              return [{ rawValue: config.detectorRaw }];
            }
            return [];
          }
        }
      });
    }
  })();`;
}

function harnessScript() {
  return String.raw`(() => {
    const readJson = (key) => {
      try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (error) { return null; }
    };
    window.__kggDeviceTest = {
      startStream(width, height, fps) {
        const source = document.createElement("canvas");
        source.width = width;
        source.height = height;
        const context = source.getContext("2d");
        context.fillStyle = "#e7e7e7";
        context.fillRect(0, 0, width, height);
        const stream = source.captureStream(fps);
        const config = window.__kggDeviceConfig;
        config.stream = stream;
        config.trackStops = 0;
        stream.getTracks().forEach((track) => {
          const originalStop = track.stop.bind(track);
          track.stop = () => {
            config.trackStops += 1;
            originalStop();
          };
        });
        this.source = source;
        this.stream = stream;
        return { settings: stream.getVideoTracks()[0] && stream.getVideoTracks()[0].getSettings ? stream.getVideoTracks()[0].getSettings() : {} };
      },
      async feed(dataUrl) {
        if (!this.source) throw new Error("synthetic stream not started");
        const image = new Image();
        await new Promise((resolve, reject) => {
          image.onload = resolve;
          image.onerror = reject;
          image.src = dataUrl;
        });
        const context = this.source.getContext("2d");
        context.clearRect(0, 0, this.source.width, this.source.height);
        context.drawImage(image, 0, 0, this.source.width, this.source.height);
        await new Promise((resolve) => setTimeout(resolve, 90));
      },
      stopStream() {
        if (this.stream) this.stream.getTracks().forEach((track) => track.stop());
      },
      snapshot() {
        const current = readJson("kggCurrentPlanV1");
        const visible = Array.from(document.querySelectorAll("#list .ex h3")).map((node) => node.textContent.trim());
        const stored = current && current.plan || null;
        return {
          stored,
          storedFingerprint: stored && window.KGGPlanFormat ? window.KGGPlanFormat.fingerprint(stored) : "",
          visible,
          status: document.getElementById("status") && document.getElementById("status").textContent || "",
          overlay: !!document.getElementById("kggLiveScan"),
          trackStops: window.__kggDeviceConfig.trackStops || 0,
          trace: {
            detectorAttempts: window.__kggDeviceConfig.detectorAttempts || 0,
            jsQrAttempts: window.__kggDeviceConfig.jsQrAttempts || 0,
            barcodeLast: window.__kggDeviceConfig.barcodeLast || "",
            jsQrLast: window.__kggDeviceConfig.jsQrLast || ""
          }
        };
      }
    };
  })();`;
}

async function createPage(browser, baseUrl, raw, options = {}) {
  const detectorMode = options.detectorMode || "absent";
  const detectorRaw = options.detectorRaw || "";
  const context = await browser.newContext({ viewport: { width: 430, height: 900 }, serviceWorkers: "block" });
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  await context.addInitScript({ content: initScript(detectorMode, detectorRaw) });
  const dialogs = [];
  page.on("dialog", async (dialog) => {
    dialogs.push({ type: dialog.type(), message: dialog.message() });
    if (dialog.type() === "prompt") await dialog.dismiss();
    else await dialog.accept();
  });
  page.on("pageerror", (error) => dialogs.push({ type: "pageerror", message: error.message }));
  await page.goto(baseUrl + "/__patient_qr_v81__.html?plan=" + encodeURIComponent(encodeH2(raw)), { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => typeof window.render === "function" && document.getElementById("plan"));
  await page.addScriptTag({ path: JSQR_PATH });
  await page.addScriptTag({
    content: String.raw`(() => {
      const real = window.jsQR;
      const config = window.__kggDeviceConfig;
      window.jsQR = function deviceLadderJsQr() {
        config.jsQrAttempts += 1;
        const result = real.apply(this, arguments);
        config.jsQrLast = result && result.data || "";
        return result;
      };
    })();`
  });
  await page.addScriptTag({ content: harnessScript() });
  await page.waitForFunction((version) => window.__kggStartScanVersion === version, SCANNER_VERSION);
  await page.waitForFunction(() => !!document.getElementById("kggPlanScanBtn"));
  const before = await page.evaluate(() => window.__kggDeviceTest.snapshot());
  return { context, client, page, dialogs, before };
}

async function setCpu(client, rate) {
  await client.send("Emulation.setCPUThrottlingRate", { rate });
}

async function openScanner(page, waitForVideo = true) {
  const bubble = page.locator("#kggBubbleScan");
  const fab = page.locator("#kggActionFab");
  if (await bubble.count() && await bubble.isVisible().catch(() => false)) {
    await bubble.click();
  } else if (await fab.count() && await fab.isVisible().catch(() => false)) {
    await fab.click();
    await bubble.waitFor({ state: "visible" });
    await bubble.click();
  } else {
    const button = page.locator("#kggPlanScanBtn");
    await button.waitFor({ state: "visible" });
    await button.click();
  }
  await page.waitForSelector("#kggLiveScan");
  if (waitForVideo) {
    await page.waitForSelector("#kggLiveScanVideo");
    await page.waitForFunction(() => {
      const video = document.getElementById("kggLiveScanVideo");
      return !!(video && video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0);
    }, null, { timeout: 10000 });
  }
}

async function readStages(page, code) {
  return page.evaluate((value) => {
    const decoded = window.KGGPlanFormat.decodeCode(value).raw;
    const parsed = window.__kggPatientStartScanTest.parsePlanFromText(value);
    return {
      decodedFingerprint: window.KGGPlanFormat.fingerprint(decoded),
      parserFingerprint: parsed ? window.KGGPlanFormat.fingerprint(parsed) : "",
      parsedCount: parsed && parsed.e ? parsed.e.length : 0
    };
  }, code);
}

async function waitForStoredPlan(page, count, timeout) {
  await page.waitForFunction((expected) => {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem("kggCurrentPlanV1") || "null"); } catch (error) {}
    return !!(saved && saved.plan && Array.isArray(saved.plan.e) && saved.plan.e.length === expected && !document.getElementById("kggLiveScan"));
  }, count, { timeout });
}

function classifyStages(expected, stages, trace, after, sourceFingerprint) {
  const errors = [];
  if (stages.decodedFingerprint !== sourceFingerprint) errors.push("generator");
  const recognized = trace.barcodeLast || trace.jsQrLast;
  if (recognized !== expected.code) errors.push("recognition");
  if (stages.parserFingerprint !== sourceFingerprint || after.storedFingerprint !== sourceFingerprint) errors.push("parser/import");
  const expectedNames = expected.raw.e.map((exercise) => exercise[0]);
  if (JSON.stringify(after.visible) !== JSON.stringify(expectedNames)) errors.push("display");
  return {
    category: errors[0] || "none",
    errors,
    stages: {
      source: sourceFingerprint,
      generatedCode: fingerprint(expected.code),
      generatedCodeChars: expected.code.length,
      decodedRaw: stages.decodedFingerprint,
      parser: stages.parserFingerprint,
      stored: after.storedFingerprint,
      visible: fingerprint({ exercises: after.visible })
    }
  };
}

async function runScanCase(browser, baseUrl, renderPage, definition) {
  const raw = makePlan(definition.count);
  const code = encodeH3(raw);
  const sourceFingerprint = fingerprint(raw);
  const matrix = makeMatrix(code);
  const frame = await renderFrame(renderPage, matrix, {
    width: definition.width,
    height: definition.height,
    qrFraction: definition.qrFraction || (definition.count === 3 ? 0.68 : 0.54),
    rotation: definition.rotation || 0,
    yaw: definition.yaw || 0,
    pitch: definition.pitch || 0,
    motion: definition.motion || 0,
    blur: definition.blur || 0,
    noise: definition.noise || 0,
    brightness: definition.brightness === undefined ? 1 : definition.brightness,
    contrast: definition.contrast === undefined ? 1 : definition.contrast
  });
  const session = await createPage(browser, baseUrl, raw, { detectorMode: definition.detectorMode || "absent", detectorRaw: code });
  const result = {
    id: definition.id,
    count: definition.count,
    profile: definition.profile,
    category: "device-ladder",
    format: "KGGH3",
    codeChars: code.length,
    h2Chars: encodeH2(raw).length,
    ratio: Number((code.length / encodeH2(raw).length).toFixed(3)),
    status: "pass",
    errorCategory: "none",
    notes: []
  };
  try {
    const generatedStages = await readStages(session.page, code);
    await session.page.evaluate(({ width, height, fps }) => window.__kggDeviceTest.startStream(width, height, fps), definition);
    await setCpu(session.client, definition.cpu || 1);
    const startedAt = Date.now();
    await openScanner(session.page);
    if (definition.detectorMode === "absent" || definition.detectorMode === "throw" || definition.feedFrame) {
      const dataUrl = "data:image/png;base64," + frame.toString("base64");
      const deadline = startedAt + (definition.deadlineMs || 10000);
      while (Date.now() < deadline) {
        await session.page.evaluate((value) => window.__kggDeviceTest.feed(value), dataUrl);
        try {
          await waitForStoredPlan(session.page, definition.count, 900);
          break;
        } catch (error) {}
      }
    } else {
      await waitForStoredPlan(session.page, definition.count, definition.deadlineMs || 10000);
    }
    const elapsedMs = Date.now() - startedAt;
    const after = await session.page.evaluate(() => window.__kggDeviceTest.snapshot());
    const classified = classifyStages({ raw, code }, generatedStages, after.trace, after, sourceFingerprint);
    result.elapsedMs = elapsedMs;
    result.decoder = after.trace.barcodeLast ? "barcode-detector" : after.trace.jsQrLast ? "jsqr" : "none";
    result.detectorAttempts = after.trace.detectorAttempts;
    result.jsQrAttempts = after.trace.jsQrAttempts;
    result.stageFingerprints = classified.stages;
    result.errorCategory = classified.category;
    result.stageErrors = classified.errors;
    result.visibleExercises = after.visible.length;
    result.storedExercises = after.stored && after.stored.e ? after.stored.e.length : 0;
    result.cameraTrackStops = after.trackStops;
    result.constraints = await session.page.evaluate(() => window.__kggDeviceConfig.constraints);
    if (classified.errors.length) {
      result.status = "fail";
      result.notes.push("stage mismatch: " + classified.errors.join(", "));
    }
    assert(after.trackStops >= 1, definition.id + ": scanner did not stop the synthetic camera");
    assert(after.visible.length === definition.count, definition.id + ": visible card count " + after.visible.length + " != " + definition.count);
    assert(!after.overlay, definition.id + ": scanner overlay remained open");
    if (definition.deadlineMs) assert(elapsedMs <= definition.deadlineMs, definition.id + ": deadline " + definition.deadlineMs + " ms exceeded by " + elapsedMs + " ms");
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
    if (result.errorCategory === "none") result.errorCategory = "recognition";
  } finally {
    try { await session.page.evaluate(() => window.__kggDeviceTest.stopStream()); } catch (error) {}
    await session.context.close();
  }
  return result;
}

async function runPhotoFallbackCase(browser, baseUrl, renderPage) {
  const target = makePlan(20);
  const initial = { ...target, i: "v81-photo-initial", t: "Photo initial", e: [target.e[0]] };
  const code = encodeH3(target);
  const frame = await renderFrame(renderPage, makeMatrix(code), { width: 1920, height: 1080, qrFraction: 0.56 });
  const session = await createPage(browser, baseUrl, initial, { detectorMode: "absent" });
  const result = { id: "high-resolution-photo-fallback-20", count: 20, category: "photo-fallback", format: "KGGH3", status: "pass", decoder: "none", notes: [] };
  try {
    const startedAt = Date.now();
    await session.page.locator("#kggPlanScanInput").setInputFiles({ name: "synthetic-20-plan.png", mimeType: "image/png", buffer: frame });
    await session.page.waitForFunction((expected) => {
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem("kggCurrentPlanV1") || "null"); } catch (error) {}
      return !!(saved && saved.plan && saved.plan.e && saved.plan.e.length === expected && /Plan aktualisiert|Plan updated/i.test(document.getElementById("status").textContent || ""));
    }, 20, { timeout: 25000 });
    const after = await session.page.evaluate(() => window.__kggDeviceTest.snapshot());
    result.elapsedMs = Date.now() - startedAt;
    result.decoder = after.trace.jsQrLast === code ? "jsqr" : after.trace.barcodeLast === code ? "barcode-detector" : "photo-parser";
    result.visibleExercises = after.visible.length;
    result.storedExercises = after.stored && after.stored.e ? after.stored.e.length : 0;
    result.recognized = after.trace.jsQrLast === code || after.trace.barcodeLast === code;
    assert(result.recognized, "20-exercise photo path did not decode the exact KGGH3 payload");
    assert(after.visible.length === 20 && result.storedExercises === 20, "20-exercise photo path changed exercise count");
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
  } finally {
    await session.context.close();
  }
  return result;
}

async function runExtremeLifecycleCase(browser, baseUrl) {
  const raw = makePlan(7);
  const session = await createPage(browser, baseUrl, raw, { detectorMode: "absent" });
  const result = { id: "extreme-320x240-lifecycle-fallback", profile: { width: 320, height: 240, fps: 3, cpu: 20 }, category: "lifecycle-fallback", status: "pass", detection: "optional", notes: [] };
  try {
    await session.page.evaluate(() => window.__kggDeviceTest.startStream(320, 240, 3));
    await setCpu(session.client, 20);
    await openScanner(session.page);
    await session.page.evaluate(() => window.__kggDeviceTest.stopStream());
    await session.page.locator(".kggLiveScanClose").click();
    await session.page.waitForFunction(() => !document.getElementById("kggLiveScan"));
    const closed = await session.page.evaluate(() => window.__kggDeviceTest.snapshot());
    assert(closed.trackStops >= 1, "extreme stream end/abort did not stop the track");
    await session.page.evaluate(() => { window.__kggDeviceConfig.detectorMode = "deny"; window.__kggDeviceConfig.stream = null; });
    await openScanner(session.page, false);
    await session.page.waitForFunction(() => {
      const fallback = document.getElementById("kggLiveScanFallback");
      return !!(fallback && !fallback.hidden);
    }, null, { timeout: 10000 });
    result.fallbackVisible = true;
    await session.page.locator(".kggLiveScanClose").click();
    result.closeAfterFallback = true;
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
  } finally {
    await session.context.close();
  }
  return result;
}

async function runDirectJsQrConditions(renderPage, counts) {
  const results = [];
  const conditions = [
    { id: "distance-small-qr", width: 1280, height: 720, qrFraction: 0.38 },
    { id: "angle-rotation", width: 960, height: 540, qrFraction: 0.40, rotation: 8 },
    { id: "perspective", width: 960, height: 540, qrFraction: 0.43, yaw: 7, pitch: -5 },
    { id: "motion-noise-low-light", width: 640, height: 480, qrFraction: 0.46, motion: 3, blur: 0.18, noise: 4, brightness: 0.78, contrast: 1.12 }
  ];
  for (const count of counts) {
    const code = encodeH3(makePlan(count));
    for (const condition of conditions) {
      const frame = await renderFrame(renderPage, makeMatrix(code), condition);
      const decoded = await renderPage.evaluate(async ({ dataUrl, width, height }) => {
        const image = new Image();
        await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject; image.src = dataUrl; });
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d", { willReadFrequently: true });
        context.drawImage(image, 0, 0);
        const data = context.getImageData(0, 0, width, height);
        const result = window.jsQR(data.data, width, height, { inversionAttempts: "attemptBoth" });
        return result && result.data || "";
      }, { dataUrl: "data:image/png;base64," + frame.toString("base64"), width: condition.width, height: condition.height });
      results.push({ id: condition.id + "-" + count, count, condition: condition.id, resolution: condition.width + "x" + condition.height, decoder: "jsqr", status: decoded === code ? "pass" : "observed-limit", exact: decoded === code });
    }
  }
  return results;
}

function reportMarkdown(run) {
  const lines = [
    "# KGG v81 QR-Geräte-Testleiter",
    "",
    "- Version: " + run.version,
    "- Commit: " + run.gitCommit,
    "- Zeitpunkt: " + run.generatedAt,
    "- Umgebung: " + run.environment,
    "- Oppo: " + run.oppo,
    "",
    "## Format-Diagnose",
    "",
    "| Übungen | KGGH2 Zeichen | KGGH3 Zeichen | Verhältnis | Decoder | Ausgangs-FP | Code-FP | Roh-FP | Parser-FP | Gespeichert-FP | Sichtbare-Karten-FP | Kategorie | Zeit |",
    "|---:|---:|---:|---:|---|---|---|---|---|---|---|---|---:|"
  ];
  for (const item of run.diagnostics) {
    const stages = item.stageFingerprints || {};
    lines.push("| " + item.count + " | " + item.h2Chars + " | " + item.codeChars + " | " + item.ratio + " | " + (item.decoder || "–") + " | " + (stages.source || "–") + " | " + (stages.generatedCode || "–") + " | " + (stages.decodedRaw || "–") + " | " + (stages.parser || "–") + " | " + (stages.stored || "–") + " | " + (stages.visible || "–") + " | " + item.errorCategory + " | " + (item.elapsedMs || "–") + " ms |");
  }
  lines.push("", "## Geräteprofile", "", "| Profil | Auflösung | FPS | CPU | Plan | Zeit | Decoder | Status |", "|---|---:|---:|---:|---:|---:|---|---|");
  for (const item of run.profiles) {
    const profile = item.profile || {};
    lines.push("| " + item.id + " | " + (profile.width ? profile.width + "x" + profile.height : "–") + " | " + (profile.fps || "–") + " | " + (profile.cpu || "–") + " | " + (item.count || "–") + " | " + (item.elapsedMs || "–") + " ms | " + (item.decoder || "–") + " | " + item.status + " |");
  }
  lines.push("", "## Render-/Decoder-Bedingungen", "", "| Fall | Auflösung | Status |", "|---|---:|---|");
  for (const item of run.conditions) lines.push("| " + item.id + " | " + item.resolution + " | " + item.status + " |");
  lines.push("", "## Ausweichwege", "", "- Foto-Fallback 20 Übungen: " + run.photoFallback.status, "- Extremprofil: " + run.extreme.status, "", "## Grenzen", "", "- Oppo-Werte sind noch nicht real gemessen; die Oppo-Simulation ist ausdrücklich ein Proxy.", "- WebKit/iPhone bleibt simuliert; kein echter iPhone-Kameratest.", "- Harte Perspektive/Unschärfe kann als beobachtete Grenze erscheinen; die Ausweichwege bleiben Pflicht.");
  return lines.join("\n") + "\n";
}

async function main() {
  assert(SCANNER_VERSION === "start-scan-v81-kgg-h3", "unexpected patient scanner version: " + SCANNER_VERSION);
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const renderContext = await browser.newContext({ viewport: { width: 1920, height: 1080 }, serviceWorkers: "block" });
  const renderPage = await renderContext.newPage();
  await renderPage.setContent("<!doctype html><meta charset=utf-8><title>v81 QR renderer</title>");
  await renderPage.addScriptTag({ path: JSQR_PATH });
  const setup = await createServer();
  const baseUrl = setup.baseUrl;
  const diagnostics = [];
  const profiles = [];
  let conditions = [];
  let photoFallback = { status: "not-run" };
  let extreme = { status: "not-run" };
  try {
    const diagnosticsToRun = [1, 3, 7, 12, 20].map((count) => ({
      id: "diagnostic-jsqr-" + count,
      count,
      profile: { width: 1280, height: 720, fps: 10, cpu: 1 },
      width: 1280,
      height: 720,
      fps: 10,
      cpu: 1,
      qrFraction: count === 3 ? 0.68 : 0.54,
      detectorMode: "absent",
      feedFrame: true,
      deadlineMs: 15000
    }));
    for (const definition of diagnosticsToRun) {
      process.stdout.write("RUN " + definition.id + "\n");
      diagnostics.push(await runScanCase(browser, baseUrl, renderPage, definition));
    }
    const ladderDefinitions = [
      { id: "oppo-simulation-provisional-7", count: 7, profile: { width: 1280, height: 720, fps: 10, cpu: 1 }, width: 1280, height: 720, fps: 10, cpu: 1, detectorMode: "throw", feedFrame: true, deadlineMs: 15000 },
      { id: "medium-20", count: 20, profile: { width: 1280, height: 720, fps: 10, cpu: 2 }, width: 1280, height: 720, fps: 10, cpu: 2, detectorMode: "throw", feedFrame: true, deadlineMs: 15000 },
      { id: "old-7", count: 7, profile: { width: 960, height: 540, fps: 7, cpu: 4 }, width: 960, height: 540, fps: 7, cpu: 4, detectorMode: "absent", feedFrame: true, deadlineMs: 15000 },
      { id: "old-12", count: 12, profile: { width: 960, height: 540, fps: 7, cpu: 4 }, width: 960, height: 540, fps: 7, cpu: 4, detectorMode: "absent", feedFrame: true, deadlineMs: 15000 },
      { id: "weak-7", count: 7, profile: { width: 640, height: 480, fps: 5, cpu: 8 }, width: 640, height: 480, fps: 5, cpu: 8, qrFraction: 0.68, detectorMode: "absent", feedFrame: true, deadlineMs: 25000 }
    ];
    for (const definition of ladderDefinitions) {
      process.stdout.write("RUN " + definition.id + "\n");
      profiles.push(await runScanCase(browser, baseUrl, renderPage, definition));
    }
    conditions = await runDirectJsQrConditions(renderPage, [7, 20]);
    photoFallback = await runPhotoFallbackCase(browser, baseUrl, renderPage);
    extreme = await runExtremeLifecycleCase(browser, baseUrl);
  } finally {
    setup.server.close();
    await renderContext.close();
    await browser.close();
  }
  const child = require("child_process").spawnSync("git", ["rev-parse", "--short", "HEAD"], { cwd: ROOT, encoding: "utf8" });
  const run = {
    version: VERSION,
    generatedAt: new Date().toISOString(),
    gitCommit: child.status === 0 ? child.stdout.trim() : "unknown",
    environment: process.platform + " " + os.release() + " / Node " + process.version + " / Chromium " + (chromium._revision || "Playwright-managed"),
    scannerVersion: SCANNER_VERSION,
    oppo: "not-yet-measured; provisional simulation only",
    diagnostics,
    profiles,
    conditions,
    photoFallback,
    extreme
  };
  fs.writeFileSync(path.join(OUTPUT_DIR, "results.json"), JSON.stringify(run, null, 2) + "\n");
  fs.writeFileSync(path.join(OUTPUT_DIR, "report.md"), reportMarkdown(run));
  const all = diagnostics.concat(profiles, conditions, [photoFallback, extreme]);
  for (const item of all) {
    const label = item.status === "pass" ? "PASS" : item.status === "fail" ? "FAIL" : "WARN";
    process.stdout.write(label + " " + (item.id || item.condition || "case") + (item.errorCategory ? " [" + item.errorCategory + "]" : "") + "\n");
  }
  const failures = all.filter((item) => item.status === "fail");
  if (failures.length) throw new Error("v81 device ladder failed: " + failures.map((item) => item.id).join(", "));
  process.stdout.write("Results: " + path.relative(ROOT, path.join(OUTPUT_DIR, "results.json")) + "\n");
  process.stdout.write("Report: " + path.relative(ROOT, path.join(OUTPUT_DIR, "report.md")) + "\n");
}

const watchdog = setTimeout(() => {
  process.stderr.write("ERROR: v81 QR device ladder exceeded " + TOTAL_TIMEOUT_MS + " ms\n");
  process.exit(124);
}, TOTAL_TIMEOUT_MS);

main()
  .then(() => { clearTimeout(watchdog); process.exit(0); })
  .catch((error) => { clearTimeout(watchdog); process.stderr.write("ERROR: " + (error.stack || error.message) + "\n"); process.exit(1); });
