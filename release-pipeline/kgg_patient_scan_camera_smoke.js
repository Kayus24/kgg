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
const FIXTURE_DIR = path.join(__dirname, "patient-scan-fixtures");
const FIXTURE_MANIFEST = path.join(FIXTURE_DIR, "camera-fixtures.json");
const SCANNER_PATH = path.join(ROOT, "patient-start-scan.js");
const SERVICE_WORKER_PATH = path.join(ROOT, "service-worker.js");
const VENDORED_JSQR_PATH = path.join(ROOT, "vendor", "jsqr-1.4.0.js");
const JSQR_PATH = require.resolve("jsqr");
const OUTPUT_DIR = path.join(ROOT, "tmp", "patient-scan-camera");
const VERSION = "patient-scan-camera-v3-live-lossless";

const args = new Set(process.argv.slice(2));
const generateOnly = args.has("--generate-fixtures");
const caseArg = process.argv.slice(2).find((arg) => arg.startsWith("--case="));
const selectedCase = caseArg ? caseArg.slice("--case=".length) : "";

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function encodePlan(plan) {
  return Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .filter((key) => !["importedAt", "updatedAt", "lastSavedAt"].includes(key))
        .sort()
        .map((key) => [key, stable(value[key])])
    );
  }
  return value;
}

function same(left, right) {
  return JSON.stringify(stable(left)) === JSON.stringify(stable(right));
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const initialPlan = {
  i: "camera-base-plan",
  t: "Camera Baseline",
  v: 7,
  d: 6,
  extendDays: true,
  stepDays: 6,
  syntheticMeta: { keep: "top-level" },
  e: [
    [
      "Rudern",
      3,
      "LR",
      "kg",
      "Wdh",
      "20",
      "12",
      "data:image/png;base64,c3ludGhldGljLW1lZGlh",
      "https://example.invalid/video-old",
      "Video alt",
      "exercise",
      { keep: "exercise-tail" }
    ],
    ["Kniebeuge", 3, "B", "kg", "Wdh", "30", "10", "https://example.invalid/knee.png", "", "", "set"]
  ]
};

const compactUpdate = {
  i: "camera-update-plan",
  t: "Camera Update",
  v: 8,
  d: 12,
  extendDays: true,
  stepDays: 6,
  e: [
    ["Rudern", 3, "LR", "kg", "Wdh", "22", "10", "", "", "", "exercise"],
    ["Beinpresse", 3, "B", "kg", "Wdh", "40", "12", "", "", "", "exercise"]
  ]
};

const realisticUpdate = {
  ...compactUpdate,
  t: "Realistic Camera Update",
  e: [
    ...compactUpdate.e,
    ["Latzug", 3, "B", "kg", "Wdh", "25", "12", "", "https://example.invalid/latzug", "Video", "exercise"],
    ["Brustpresse", 3, "B", "kg", "Wdh", "20", "12", "", "", "", "set"]
  ]
};

const replacementUpdate = {
  ...compactUpdate,
  t: "Camera Media Replacement",
  e: [
    [
      "Rudern",
      4,
      "LR",
      "kg",
      "Wdh",
      "24",
      "8",
      "https://example.invalid/media-new.png",
      "https://example.invalid/video-new",
      "Video neu",
      "set",
      { replace: "exercise-tail" }
    ]
  ]
};

const compactText = `KGGH2:${encodePlan(compactUpdate)}`;
const realisticText = `https://kayus24.github.io/kgg/?plan=${encodeURIComponent(`KGGH2:${encodePlan(realisticUpdate)}`)}`;
const replacementText = `KGGH2:${encodePlan(replacementUpdate)}`;

function makeMatrix(text) {
  const qr = qrFactory(0, "M");
  qr.addData(text);
  qr.make();
  const count = qr.getModuleCount();
  return Array.from({ length: count }, (_, row) =>
    Array.from({ length: count }, (_, col) => qr.isDark(row, col))
  );
}

const matrices = {
  compact: makeMatrix(compactText),
  realistic: makeMatrix(realisticText)
};

function createServer() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const relative = url.pathname === "/__patient_scan_test__.html" ? "index.html" : url.pathname.replace(/^\/+/, "");
    const target = path.resolve(ROOT, relative || "index.html");
    if (!target.startsWith(ROOT + path.sep) && target !== path.join(ROOT, "index.html")) {
      response.writeHead(403).end("forbidden");
      return;
    }
    try {
      const body = fs.readFileSync(target);
      const type = target.endsWith(".html")
        ? "text/html; charset=utf-8"
        : target.endsWith(".js")
          ? "application/javascript; charset=utf-8"
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
      resolve({ server, baseUrl: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function renderFrame(renderPage, matrix, spec) {
  const dataUrl = await renderPage.evaluate(
    ({ matrix: modules, spec: frameSpec, seed }) => {
      const width = frameSpec.width;
      const height = frameSpec.height;
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      ctx.fillStyle = frameSpec.background || "#e7e7e7";
      ctx.fillRect(0, 0, width, height);

      const quiet = 4;
      const count = modules.length;
      const qrCanvas = document.createElement("canvas");
      qrCanvas.width = count + quiet * 2;
      qrCanvas.height = count + quiet * 2;
      const qrCtx = qrCanvas.getContext("2d");
      qrCtx.fillStyle = "white";
      qrCtx.fillRect(0, 0, qrCanvas.width, qrCanvas.height);
      qrCtx.fillStyle = "black";
      for (let row = 0; row < count; row += 1) {
        for (let col = 0; col < count; col += 1) {
          if (modules[row][col]) qrCtx.fillRect(col + quiet, row + quiet, 1, 1);
        }
      }

      const size = Math.max(24, Math.round(Math.min(width, height) * (frameSpec.qrFraction || 0.35)));
      const centerX = width / 2 + (frameSpec.offsetX || 0);
      const centerY = height / 2 + (frameSpec.offsetY || 0);
      const rotation = ((frameSpec.rotation || 0) * Math.PI) / 180;
      const brightness = frameSpec.brightness === undefined ? 1 : frameSpec.brightness;
      const contrast = frameSpec.contrast === undefined ? 1 : frameSpec.contrast;
      const blur = frameSpec.blur || 0;

      const drawImageTriangle = (image, source, destination) => {
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

      const drawPerspectiveImage = (motionOffset) => {
        const yaw = ((frameSpec.yaw || 0) * Math.PI) / 180;
        const pitch = ((frameSpec.pitch || 0) * Math.PI) / 180;
        const cosYaw = Math.cos(yaw);
        const sinYaw = Math.sin(yaw);
        const cosPitch = Math.cos(pitch);
        const sinPitch = Math.sin(pitch);
        const cameraDistance = 2.2;
        const corners = frameSpec.cornerWarp || [[0, 0], [0, 0], [0, 0], [0, 0]];
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
        const cells = 24;
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
            drawImageTriangle(qrCanvas, [s00, s10, s11], [d00, d10, d11]);
            drawImageTriangle(qrCanvas, [s00, s11, s01], [d00, d11, d01]);
          }
        }
      };

      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(rotation);
      ctx.filter = `brightness(${brightness}) contrast(${contrast}) blur(${blur}px)`;
      ctx.imageSmoothingEnabled = false;

      const copies = frameSpec.motion ? 7 : 1;
      for (let copy = 0; copy < copies; copy += 1) {
        const motionOffset = copies === 1 ? 0 : ((copy / (copies - 1)) - 0.5) * frameSpec.motion;
        ctx.globalAlpha = copies === 1 ? 1 : 0.22;
        if (frameSpec.yaw || frameSpec.pitch || frameSpec.cornerWarp) {
          drawPerspectiveImage(motionOffset);
        } else {
          ctx.drawImage(qrCanvas, -size / 2 + motionOffset, -size / 2, size, size);
        }
      }
      ctx.restore();

      const noise = Number(frameSpec.noise || 0);
      if (noise > 0) {
        const image = ctx.getImageData(0, 0, width, height);
        let state = (seed ^ width ^ (height << 8) ^ Math.round(noise * 100)) >>> 0;
        const random = () => {
          state ^= state << 13;
          state ^= state >>> 17;
          state ^= state << 5;
          return (state >>> 0) / 4294967296;
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
    },
    { matrix, spec, seed: 24061986 }
  );
  return Buffer.from(dataUrl.split(",")[1], "base64");
}

function initScript(detectorMode, detectorRaw) {
  return `(() => {
    try { localStorage.setItem('kggPatientLang', 'en'); } catch (e) {}
    window.__kggScanTestTrace = { barcodeAttempts: 0, jsQrAttempts: 0, barcodeMode: ${JSON.stringify(detectorMode)}, barcodeLast: '', jsQrLast: '' };
    const mode = ${JSON.stringify(detectorMode)};
    const raw = ${JSON.stringify(detectorRaw || "")};
    if (mode === 'absent') {
      try { delete window.BarcodeDetector; } catch (e) { window.BarcodeDetector = undefined; }
      return;
    }
    Object.defineProperty(window, 'BarcodeDetector', {
      configurable: true,
      value: class BarcodeDetectorTestDouble {
        constructor(options) { this.options = options; }
        async detect() {
          window.__kggScanTestTrace.barcodeAttempts += 1;
          if (mode === 'throw') throw new Error('synthetic BarcodeDetector failure');
          if (mode === 'success') {
            window.__kggScanTestTrace.barcodeLast = raw;
            return [{ rawValue: raw }];
          }
          return [];
        }
      }
    });
  })();`;
}

async function createPatientPage(browser, baseUrl, options = {}) {
  const detectorMode = options.detectorMode || "absent";
  const detectorRaw = options.detectorRaw || "";
  const jsQrMode = options.jsQrMode || "real";
  const context = await browser.newContext({ viewport: { width: 430, height: 900 }, serviceWorkers: "block" });
  await context.addInitScript({ content: initScript(detectorMode, detectorRaw) });
  const page = await context.newPage();
  const dialogs = [];
  page.on("dialog", async (dialog) => {
    dialogs.push({ type: dialog.type(), message: dialog.message() });
    if (dialog.type() === "prompt") await dialog.dismiss();
    else await dialog.accept();
  });

  const initialText = `KGGH2:${encodePlan(initialPlan)}`;
  await page.goto(`${baseUrl}/__patient_scan_test__.html?plan=${encodeURIComponent(initialText)}`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => typeof window.render === "function" && document.getElementById("plan"));

  await page.addScriptTag({ path: JSQR_PATH });
  await page.addScriptTag({
    content: `(() => {
      const realJsQr = window.jsQR;
      const mode = ${JSON.stringify(jsQrMode)};
      window.jsQR = function tracedJsQr() {
        window.__kggScanTestTrace.jsQrAttempts += 1;
        if (mode === 'throw') throw new Error('synthetic jsQR failure');
        if (mode === 'miss') return null;
        const result = realJsQr.apply(this, arguments);
        window.__kggScanTestTrace.jsQrLast = result && result.data || '';
        return result;
      };
      v = {
        '1|0|1|L|a': '31', '1|0|1|L|b': '11',
        '1|0|1|R|a': '32', '1|0|1|R|b': '12',
        '2|1|1|B|a': '45', '2|1|1|B|b': '9'
      };
      done = [1];
      d = 2;
      localStorage.setItem('kggCurrentPlanV1', JSON.stringify({ plan: ${JSON.stringify(initialPlan)}, importedAt: '2026-07-13T08:00:00.000Z', source: 'synthetic-test' }));
      localStorage.setItem('kggPatientMultiPlansV1', JSON.stringify({
        version: 1,
        plans: [${JSON.stringify(initialPlan)}, { i: 'other-slot', t: 'Other slot', e: [['Unchanged', 1, 'B', 'kg', 'Wdh']] }],
        active: 0,
        day: { 0: 2, 1: 1 },
        marker: 'keep-multi-root'
      }));
      save();
      render();
      window.__kggPatientTestSnapshot = () => ({
        p: JSON.parse(JSON.stringify(p)),
        v: JSON.parse(JSON.stringify(v)),
        done: JSON.parse(JSON.stringify(done)),
        d,
        current: JSON.parse(localStorage.getItem('kggCurrentPlanV1') || 'null'),
        multi: JSON.parse(localStorage.getItem('kggPatientMultiPlansV1') || 'null'),
        status: document.getElementById('status') && document.getElementById('status').textContent || ''
      });
      window.__kggBeginSyntheticStream = async (width, height) => {
        const source = document.createElement('canvas');
        source.width = width;
        source.height = height;
        const initialContext = source.getContext('2d');
        initialContext.fillStyle = '#e7e7e7';
        initialContext.fillRect(0, 0, width, height);
        const stream = source.captureStream(5);
        window.__kggSyntheticTrackStops = 0;
        stream.getTracks().forEach((track) => {
          const originalStop = track.stop.bind(track);
          track.stop = () => { window.__kggSyntheticTrackStops += 1; originalStop(); };
        });
        const mediaDevices = navigator.mediaDevices || {};
        Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: mediaDevices });
        mediaDevices.getUserMedia = async () => stream;
        window.__kggSyntheticStream = { source, stream };
        const track = stream.getVideoTracks()[0];
        return { kind: track && track.kind || '', settings: track && track.getSettings ? track.getSettings() : {} };
      };
      window.__kggRejectSyntheticCamera = () => {
        const mediaDevices = navigator.mediaDevices || {};
        Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: mediaDevices });
        mediaDevices.getUserMedia = async () => { throw new DOMException('synthetic permission denied', 'NotAllowedError'); };
      };
      window.__kggFeedSyntheticStreamFrame = async (dataUrl) => {
        const holder = window.__kggSyntheticStream;
        if (!holder) throw new Error('synthetic MediaStream not started');
        const image = new Image();
        await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject; image.src = dataUrl; });
        const sourceContext = holder.source.getContext('2d');
        sourceContext.clearRect(0, 0, holder.source.width, holder.source.height);
        sourceContext.drawImage(image, 0, 0, holder.source.width, holder.source.height);
        await new Promise((resolve) => setTimeout(resolve, 80));
      };
      window.__kggSyntheticCameraSnapshot = () => ({
        trackStops: window.__kggSyntheticTrackStops || 0,
        overlay: !!document.getElementById('kggLiveScan'),
        fallbackVisible: !!(document.getElementById('kggLiveScanFallback') && !document.getElementById('kggLiveScanFallback').hidden),
        fallbackDisplay: document.getElementById('kggLiveScanFallback') ? getComputedStyle(document.getElementById('kggLiveScanFallback')).display : '',
        status: document.getElementById('kggLiveScanStatus') && document.getElementById('kggLiveScanStatus').textContent || ''
      });
      window.__kggEndSyntheticStream = () => {
        const holder = window.__kggSyntheticStream;
        if (holder) holder.stream.getTracks().forEach((track) => track.stop());
        delete window.__kggSyntheticStream;
      };
    })();`
  });
  await page.addScriptTag({ path: SCANNER_PATH });
  await page.waitForFunction(() => window.__kggStartScanVersion === "start-scan-v8-html-version-label");
  await page.waitForFunction(() => document.getElementById("kggPatientHtmlVersion")?.textContent === "PAT HTML v52");
  await page.waitForFunction(() => document.getElementById("kggPlanScanInput"));
  const before = await page.evaluate(() => window.__kggPatientTestSnapshot());
  return { context, page, dialogs, before };
}

async function waitForScan(page, dialogs, beforeAttempts, beforeDialogs, timeout = 5000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const state = await page.evaluate(() => ({
      trace: { ...window.__kggScanTestTrace },
      status: document.getElementById("status") && document.getElementById("status").textContent || ""
    }));
    const attempts = state.trace.barcodeAttempts + state.trace.jsQrAttempts;
    if (
      dialogs.length > beforeDialogs ||
      (/Plan updated/i.test(state.status) && attempts > beforeAttempts) ||
      (attempts > beforeAttempts && (state.trace.jsQrLast || state.trace.barcodeLast))
    ) {
      await page.waitForTimeout(140);
      return state;
    }
    await page.waitForTimeout(25);
  }
  throw new Error("scan attempt timed out");
}

async function feedFile(page, dialogs, buffer, name = "camera.png") {
  const trace = await page.evaluate(() => ({ ...window.__kggScanTestTrace }));
  const beforeAttempts = trace.barcodeAttempts + trace.jsQrAttempts;
  const beforeDialogs = dialogs.length;
  await page.locator("#kggPlanScanInput").setInputFiles({ name, mimeType: "image/png", buffer });
  return waitForScan(page, dialogs, beforeAttempts, beforeDialogs);
}

async function feedStreamFrame(page, dialogs, buffer, name) {
  const trace = await page.evaluate(() => ({ ...window.__kggScanTestTrace }));
  const beforeAttempts = trace.barcodeAttempts + trace.jsQrAttempts;
  const beforeJsQrAttempts = trace.jsQrAttempts;
  const dataUrl = `data:image/png;base64,${buffer.toString("base64")}`;
  await page.evaluate(({ dataUrl: frame, name: fileName }) => window.__kggFeedSyntheticStreamFrame(frame, fileName), { dataUrl, name });
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    const state = await page.evaluate(() => ({ ...window.__kggScanTestTrace }));
    if (state.jsQrAttempts > beforeJsQrAttempts || (state.barcodeAttempts + state.jsQrAttempts > beforeAttempts && state.barcodeLast)) {
      await page.waitForTimeout(260);
      return state;
    }
    await page.waitForTimeout(25);
  }
  throw new Error("live scan attempt timed out");
}

function preservationChecks(before, after) {
  const checks = {
    values: same(before.v, after.v),
    completedDays: same(before.done, after.done),
    activeDay: before.d === after.d,
    topLevelMetadata: after.current && after.current.plan && same(after.current.plan.syntheticMeta, initialPlan.syntheticMeta),
    existingMedia: after.current && after.current.plan && after.current.plan.e && after.current.plan.e[0] && after.current.plan.e[0][7] === initialPlan.e[0][7],
    secondExerciseMedia: after.current && after.current.plan && after.current.plan.e && after.current.plan.e[1] && after.current.plan.e[1][7] === initialPlan.e[1][7],
    videoMetadata: after.current && after.current.plan && after.current.plan.e && after.current.plan.e[0] && after.current.plan.e[0][8] === initialPlan.e[0][8] && after.current.plan.e[0][9] === initialPlan.e[0][9],
    painMode: after.current && after.current.plan && after.current.plan.e && after.current.plan.e[0] && after.current.plan.e[0][10] === initialPlan.e[0][10],
    exerciseTail: after.current && after.current.plan && after.current.plan.e && after.current.plan.e[0] && same(after.current.plan.e[0][11], initialPlan.e[0][11]),
    otherMultiSlot: after.multi && before.multi && same(after.multi.plans[1], before.multi.plans[1]),
    multiRoot: after.multi && after.multi.marker === "keep-multi-root",
    newExercise: after.p && after.p.ex && after.p.ex.some((exercise) => exercise.n === "Beinpresse")
  };
  return { checks, passed: Object.values(checks).every(Boolean) };
}

function attachPreservationResult(result, preservation) {
  result.preservation = preservation.checks;
  if (!preservation.passed) {
    const missing = Object.entries(preservation.checks).filter(([, passed]) => !passed).map(([name]) => name);
    result.knownGaps = missing;
    result.notes.push(`lossless update gap: ${missing.join(", ")}`);
  }
}

async function runDecoderCase(browser, baseUrl, definition, compactPng) {
  const session = await createPatientPage(browser, baseUrl, definition);
  const result = {
    id: definition.id,
    category: "decoder",
    gate: definition.gate !== false,
    status: "pass",
    decoder: "none",
    notes: []
  };
  try {
    await feedFile(session.page, session.dialogs, compactPng, `${definition.id}.png`);
    const trace = await session.page.evaluate(() => ({ ...window.__kggScanTestTrace }));
    const after = await session.page.evaluate(() => window.__kggPatientTestSnapshot());
    result.decoder = trace.barcodeLast ? "barcode-detector" : trace.jsQrLast ? "jsqr" : "none";
    result.barcodeAttempts = trace.barcodeAttempts;
    result.jsQrAttempts = trace.jsQrAttempts;
    result.dialogs = session.dialogs.map((dialog) => dialog.type);
    result.decodedHash = sha256(trace.barcodeLast || trace.jsQrLast || "");

    if (definition.expect === "updated") {
      assert(/Plan updated/i.test(after.status), `${definition.id}: parser did not update the plan`);
      const preservation = preservationChecks(session.before, after);
      attachPreservationResult(result, preservation);
    } else {
      assert(same(session.before.p, after.p), `${definition.id}: invalid/error scan changed in-memory plan`);
      assert(same(session.before.v, after.v), `${definition.id}: invalid/error scan changed values`);
    }
    if (definition.expectedDecoder) assert(result.decoder === definition.expectedDecoder, `${definition.id}: expected ${definition.expectedDecoder}, got ${result.decoder}`);
    if (definition.expectedJsQrAttempts !== undefined) assert(trace.jsQrAttempts === definition.expectedJsQrAttempts, `${definition.id}: unexpected jsQR attempts ${trace.jsQrAttempts}`);
  } catch (error) {
    if (definition.knownGap) {
      result.status = "known-gap";
      result.notes.push(error.message);
    } else {
      result.status = "fail";
      result.notes.push(error.message);
    }
  } finally {
    await session.context.close();
  }
  return result;
}

async function runMediaReplacementCase(browser, baseUrl, compactPng) {
  const session = await createPatientPage(browser, baseUrl, { detectorMode: "success", detectorRaw: replacementText });
  const result = {
    id: "lossless-media-replacement",
    category: "plan-update",
    gate: true,
    status: "pass",
    decoder: "barcode-detector",
    notes: []
  };
  try {
    await feedFile(session.page, session.dialogs, compactPng, "lossless-media-replacement.png");
    const after = await session.page.evaluate(() => window.__kggPatientTestSnapshot());
    const exercises = after.current && after.current.plan && after.current.plan.e || [];
    assert(exercises[0][7] === replacementUpdate.e[0][7], "new non-empty exercise media did not replace the old media");
    assert(exercises[0][8] === replacementUpdate.e[0][8] && exercises[0][9] === replacementUpdate.e[0][9], "new video metadata did not replace the old metadata");
    assert(exercises[0][10] === "set", "new pain mode did not replace the old pain mode");
    assert(same(exercises[0][11], replacementUpdate.e[0][11]), "explicit exercise tail did not replace the old tail");
    assert(exercises[1][0] === "Kniebeuge" && exercises[1][7] === initialPlan.e[1][7], "exercise omitted by the update lost its media or position");
    assert(same(session.before.v, after.v) && same(session.before.done, after.done) && session.before.d === after.d, "media replacement changed patient values or day state");
    assert(same(session.before.multi.plans[1], after.multi.plans[1]) && after.multi.marker === "keep-multi-root", "media replacement changed another plan slot");
    result.replacedMedia = true;
    result.preservedOmittedExercise = true;
    result.preservedValues = true;
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
  } finally {
    await session.context.close();
  }
  return result;
}

async function runStaticCase(browser, baseUrl, renderPage, definition, renderedFrame = null) {
  const payloadKey = definition.payload || "compact";
  const payloadText = payloadKey === "compact" ? compactText : realisticText;
  const frame = renderedFrame || await renderFrame(renderPage, matrices[payloadKey], definition);
  const session = await createPatientPage(browser, baseUrl, { detectorMode: "absent" });
  const result = {
    id: definition.id,
    category: definition.category || "static-image",
    condition: definition.label || definition.id,
    gate: definition.gate !== false,
    resolution: `${definition.width}x${definition.height}`,
    qrFraction: definition.qrFraction,
    yaw: definition.yaw || 0,
    pitch: definition.pitch || 0,
    status: "pass",
    decoder: "none",
    payloadHash: sha256(payloadText),
    notes: []
  };
  let after = null;
  try {
    await feedFile(session.page, session.dialogs, frame, `${definition.id}.png`);
    const trace = await session.page.evaluate(() => ({ ...window.__kggScanTestTrace }));
    after = await session.page.evaluate(() => window.__kggPatientTestSnapshot());
    result.decoder = trace.jsQrLast ? "jsqr" : "none";
    result.decodedHash = sha256(trace.jsQrLast || "");
    result.recognized = trace.jsQrLast === payloadText;
    if (!result.recognized) throw new Error("QR text was not recognized exactly");
    const preservation = preservationChecks(session.before, after);
    attachPreservationResult(result, preservation);
  } catch (error) {
    result.status = result.gate ? "fail" : "observed-limit";
    result.notes.push(error.message);
    if (after && !result.recognized) {
      result.unchangedOnFailure = same(session.before.p, after.p) && same(session.before.v, after.v) && same(session.before.done, after.done) && session.before.d === after.d && same(session.before.current, after.current) && same(session.before.multi, after.multi);
      if (!result.unchangedOnFailure) {
        result.gate = true;
        result.status = "fail";
        result.notes.push("unrecognized image changed patient state");
      }
    }
  } finally {
    await session.context.close();
  }
  return result;
}

async function runStreamCase(browser, baseUrl, renderPage, definition) {
  const session = await createPatientPage(browser, baseUrl, { detectorMode: definition.detectorMode || "absent" });
  const result = {
    id: definition.id,
    category: "synthetic-mediastream",
    gate: true,
    resolution: `${definition.width}x${definition.height}`,
    status: "pass",
    decoder: "none",
    firstSuccessfulFrame: null,
    frameCount: definition.frames.length,
    notes: []
  };
  try {
    result.stream = await session.page.evaluate(({ width, height }) => window.__kggBeginSyntheticStream(width, height), definition);
    await session.page.locator("#kggPlanScanBtn").click();
    await session.page.waitForSelector("#kggLiveScanVideo");
    await session.page.waitForFunction(() => {
      const video = document.getElementById("kggLiveScanVideo");
      return !!(video && video.readyState >= 2 && video.videoWidth > 0);
    });
    const initialCamera = await session.page.evaluate(() => window.__kggSyntheticCameraSnapshot());
    assert(!initialCamera.fallbackVisible && initialCamera.fallbackDisplay === "none", `${definition.id}: fallback actions were visible while the live camera was active`);
    for (let index = 0; index < definition.frames.length; index += 1) {
      const spec = { width: definition.width, height: definition.height, ...definition.frames[index] };
      const frame = await renderFrame(renderPage, matrices.realistic, spec);
      await feedStreamFrame(session.page, session.dialogs, frame, `${definition.id}-${index + 1}.png`);
      if (index === definition.frames.length - 1) {
        try {
          await session.page.waitForFunction((expected) => window.__kggScanTestTrace.jsQrLast === expected || window.__kggScanTestTrace.barcodeLast === expected, realisticText, { timeout: 2500 });
        } catch (error) {}
      }
      const trace = await session.page.evaluate(() => ({ ...window.__kggScanTestTrace }));
      if (trace.jsQrLast === realisticText) {
        result.firstSuccessfulFrame = index + 1;
        result.decoder = "jsqr";
        break;
      }
    }
    result.trace = await session.page.evaluate(() => ({ ...window.__kggScanTestTrace }));
    assert(result.firstSuccessfulFrame !== null, `${definition.id}: no frame was recognized, including the final clear frame`);
    await session.page.waitForFunction(() => {
      const status = document.getElementById("status");
      return !!(status && /Plan updated/i.test(status.textContent || "") && !document.getElementById("kggLiveScan"));
    });
    const after = await session.page.evaluate(() => window.__kggPatientTestSnapshot());
    const preservation = preservationChecks(session.before, after);
    attachPreservationResult(result, preservation);
    result.camera = await session.page.evaluate(() => window.__kggSyntheticCameraSnapshot());
    assert(result.camera.trackStops >= 1, `${definition.id}: camera track was not stopped after success`);
    assert(!result.camera.overlay, `${definition.id}: live scanner overlay remained open after success`);
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
  } finally {
    try { await session.page.evaluate(() => window.__kggEndSyntheticStream && window.__kggEndSyntheticStream()); } catch (error) {}
    await session.context.close();
  }
  return result;
}

async function runCameraLifecycleCase(browser, baseUrl) {
  const session = await createPatientPage(browser, baseUrl, { detectorMode: "absent" });
  const result = {
    id: "live-camera-permission-and-cleanup",
    category: "camera-lifecycle",
    gate: true,
    status: "pass",
    decoder: "none",
    notes: []
  };
  try {
    await session.page.evaluate(() => window.__kggRejectSyntheticCamera());
    await session.page.locator("#kggPlanScanBtn").click();
    await session.page.waitForFunction(() => {
      const fallback = document.getElementById("kggLiveScanFallback");
      return !!(fallback && !fallback.hidden);
    });
    const denied = await session.page.evaluate(() => window.__kggSyntheticCameraSnapshot());
    assert(denied.overlay && denied.fallbackVisible && denied.fallbackDisplay !== "none", "permission denial did not expose the photo fallback");
    const afterDenied = await session.page.evaluate(() => window.__kggPatientTestSnapshot());
    assert(same(session.before.p, afterDenied.p) && same(session.before.v, afterDenied.v), "permission denial changed patient state");
    await session.page.locator(".kggLiveScanClose").click();
    await session.page.evaluate(() => window.__kggBeginSyntheticStream(1280, 720));
    await session.page.locator("#kggPlanScanBtn").click();
    await session.page.waitForSelector("#kggLiveScanVideo");
    await session.page.evaluate(() => window.dispatchEvent(new Event("pagehide")));
    await session.page.waitForFunction(() => !document.getElementById("kggLiveScan"));
    const cleanup = await session.page.evaluate(() => window.__kggSyntheticCameraSnapshot());
    assert(cleanup.trackStops >= 1, "pagehide did not stop the live camera track");
    result.permissionFallback = true;
    result.pagehideCleanup = true;
    result.trackStops = cleanup.trackStops;
  } catch (error) {
    result.status = "fail";
    result.notes.push(error.message);
  } finally {
    try { await session.page.evaluate(() => window.__kggEndSyntheticStream && window.__kggEndSyntheticStream()); } catch (error) {}
    await session.context.close();
  }
  return result;
}

function markdownReport(run) {
  const count = (status) => run.results.filter((result) => result.status === status).length;
  const productGaps = [...new Set(run.results.flatMap((result) => result.knownGaps || []))];
  const lines = [
    `# Patienten-QR Kamera-Testbericht (${VERSION})`,
    "",
    `- Zeitpunkt: ${run.generatedAt}`,
    `- Basis: ${run.gitCommit}`,
    `- Umgebung: ${run.environment}`,
    `- Ergebnis: ${count("pass")} bestanden, ${count("known-gap")} bekannte Lücken, ${count("observed-limit")} beobachtete Grenzfälle, ${count("fail")} Fehler`,
    `- Verlustfreie Update-Prüfung: ${productGaps.length ? `bekannte Abweichungen bei ${productGaps.join(", ")}` : "bestanden"}`,
    "",
    "## Automatisierte Ergebnisse",
    "",
    "| Fall | Bedingung | Kategorie | Auflösung | Decoder | Erster Treffer | Status |",
    "|---|---|---|---:|---|---:|---|"
  ];
  for (const result of run.results) {
    lines.push(`| ${result.id} | ${result.condition || result.id} | ${result.category} | ${result.resolution || "–"} | ${result.decoder || "–"} | ${result.firstSuccessfulFrame || "–"} | ${result.status} |`);
  }
  lines.push(
    "",
    "## Wichtige Einordnung",
    "",
    "Die Produktions-App nutzt einen kontinuierlichen `getUserMedia`-Scan und prüft Canvas-Frames automatisch. Die Stream-Fälle ersetzen die Rückkamera durch einen test-only Canvas-`MediaStream` und durchlaufen damit denselben Live-Scanner wie die PWA. Der Fotoimport bleibt als Fallback und prüft mehrere Ausschnitt-/Kontrastvarianten.",
    "",
    "`BarcodeDetector` wird in den automatisierten Vertragstests kontrolliert simuliert. Fehler und fehlende QR-Unterstützung fallen auf die lokal gepinnte jsQR-Version zurück. Native Android-Erkennung bleibt ein manueller Gerätetest.",
    "",
    "## Physischer Android-Handtest",
    "",
    `Automatisierung: ${run.android.status}`,
    "",
    "Nutzerbefund vom 13.07.2026: Die Aktualisieren-/Kamerafunktion erkannte einen realen Plan-QR-Code auf dem Android-Gerät nicht. Gerätemodell, Chrome-Version, Kameradistanz und Originalaufnahme liegen für die Reproduktion noch nicht vor.",
    "",
    "1. Patienten-App in aktuellem Chrome öffnen und `window.__kggStartScanVersion` dokumentieren.",
    "2. Einen synthetischen Ausgangsplan laden, Werte eintragen und vorhandenes Übungsmedium prüfen.",
    "3. `canonical-realistic.png` mit 15/30/60 cm Abstand, frontal und schräg sowie bei normalem, schwachem und starkem Licht fotografieren.",
    "4. Vorher-/Nachher-Screenshots, UI-Zustand und Logcat sichern; Tap-Koordinaten aus dem UI-Tree ableiten.",
    "5. Decoderroute nach Möglichkeit über temporäre Chrome-Remote-Debug-Instrumentierung erfassen.",
    "6. Planinhalt, Werte, erledigte Tage, Medien und zweiten Multi-Plan-Slot vergleichen.",
    "",
    "Ein Emulator oder synthetischer Stream ersetzt diesen Test nicht.",
    ""
  );
  const notable = run.results.filter((result) => result.notes && result.notes.length);
  if (notable.length) {
    lines.push("## Befunde", "");
    for (const result of notable) lines.push(`- ${result.id}: ${result.notes.join("; ")}`);
    lines.push("");
  }
  return lines.join("\n");
}

async function detectAndroid() {
  const { spawnSync } = require("child_process");
  const probe = spawnSync("adb", ["devices"], { encoding: "utf8" });
  if (probe.error || probe.status !== 0) return { status: "nicht durchgeführt – ADB nicht verfügbar" };
  const devices = probe.stdout.split(/\r?\n/).slice(1).filter((line) => /\tdevice$/.test(line));
  if (!devices.length) return { status: "nicht durchgeführt – kein physisches Android-Gerät per ADB verbunden" };
  return { status: `nicht automatisch durchgeführt – Gerät erkannt (${devices.map((line) => line.split("\t")[0]).join(", ")}); reale Kamera erfordert die manuelle QR-Aufnahme` };
}

async function generateReferenceFixtures(renderPage, writeFiles) {
  const compact = await renderFrame(renderPage, matrices.compact, { width: 1280, height: 720, qrFraction: 0.40 });
  const realistic = await renderFrame(renderPage, matrices.realistic, { width: 1280, height: 720, qrFraction: 0.78 });
  if (writeFiles) {
    fs.mkdirSync(FIXTURE_DIR, { recursive: true });
    fs.writeFileSync(path.join(FIXTURE_DIR, "canonical-compact.png"), compact);
    fs.writeFileSync(path.join(FIXTURE_DIR, "canonical-realistic.png"), realistic);
  }
  return { compact, realistic };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function perspectiveGalleryHtml(cases) {
  const cards = cases.map((definition) => `
    <article>
      <img src="./perspective/${escapeHtml(definition.id)}.png" alt="${escapeHtml(definition.label || definition.id)}">
      <h2>${escapeHtml(definition.label || definition.id)}</h2>
      <p>${definition.width}×${definition.height} · QR ${Math.round(definition.qrFraction * 100)} % · ${definition.gate === false ? "Messgrenze" : "Pflichtfall"}</p>
      <code>${escapeHtml(definition.id)}</code>
    </article>`).join("");
  return `<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Patienten-QR Perspektiv-Fixtures</title>
<style>body{margin:0;padding:24px;background:#17191d;color:#f3f4f6;font:15px/1.45 system-ui,sans-serif}h1{margin:0 0 8px}.intro{color:#c5cad3;margin:0 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}article{background:#242831;border:1px solid #3b414d;border-radius:12px;padding:12px}img{display:block;width:100%;height:auto;background:#e7e7e7;border-radius:7px}h2{font-size:17px;margin:12px 0 5px}p{color:#c5cad3;margin:0 0 7px}code{color:#8bd5ff}</style>
</head><body><h1>Patienten-QR Perspektiv-Fixtures</h1><p class="intro">Jede Aufnahme wird separat durch den aktuellen Produktionsscanner geprüft. Eine spätere frontale Aufnahme kann einen vorherigen Fehlschlag nicht verdecken.</p><main class="grid">${cards}
</main></body></html>\n`;
}

async function generatePerspectiveFixtures(renderPage, cases, writeFiles) {
  const frames = new Map();
  const perspectiveDir = path.join(FIXTURE_DIR, "perspective");
  if (writeFiles) fs.mkdirSync(perspectiveDir, { recursive: true });
  for (const definition of cases) {
    const payloadKey = definition.payload || "realistic";
    const frame = await renderFrame(renderPage, matrices[payloadKey], definition);
    frames.set(definition.id, frame);
    if (writeFiles) fs.writeFileSync(path.join(perspectiveDir, `${definition.id}.png`), frame);
  }
  if (writeFiles) fs.writeFileSync(path.join(FIXTURE_DIR, "perspective-gallery.html"), perspectiveGalleryHtml(cases));
  return frames;
}

async function main() {
  const manifest = JSON.parse(fs.readFileSync(FIXTURE_MANIFEST, "utf8"));
  assert(manifest.version === VERSION, "fixture manifest version mismatch");
  assert(fs.existsSync(SCANNER_PATH), "patient-start-scan.js missing");
  assert(fs.readFileSync(SCANNER_PATH, "utf8").includes("start-scan-v8-html-version-label"), "patient scanner target version mismatch");
  assert(fs.existsSync(VENDORED_JSQR_PATH), "vendored jsQR runtime missing");
  assert(sha256(fs.readFileSync(VENDORED_JSQR_PATH)) === "bc40c8a15196236b2314db0856f72ca0b49980cd5413b8c852a7349f5fee0859", "vendored jsQR runtime hash mismatch");
  const serviceWorkerText = fs.readFileSync(SERVICE_WORKER_PATH, "utf8");
  assert(serviceWorkerText.includes("kgg-handyplan-v52-html-version-label"), "service worker target version mismatch");
  assert(serviceWorkerText.includes("./vendor/jsqr-1.4.0.js"), "service worker does not precache jsQR");
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const renderContext = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const renderPage = await renderContext.newPage();
  await renderPage.setContent("<!doctype html><meta charset=utf-8><title>QR fixture renderer</title>");
  const references = await generateReferenceFixtures(renderPage, generateOnly);
  const perspectiveFrames = await generatePerspectiveFixtures(renderPage, manifest.perspectiveCases || [], generateOnly);
  if (generateOnly) {
    await browser.close();
    console.log(`Generated ${path.relative(ROOT, FIXTURE_DIR)} reference PNGs.`);
    return;
  }
  const committedCompact = path.join(FIXTURE_DIR, "canonical-compact.png");
  const committedRealistic = path.join(FIXTURE_DIR, "canonical-realistic.png");
  assert(fs.existsSync(committedCompact) && fs.readFileSync(committedCompact).equals(references.compact), "canonical-compact.png is stale; run with --generate-fixtures");
  assert(fs.existsSync(committedRealistic) && fs.readFileSync(committedRealistic).equals(references.realistic), "canonical-realistic.png is stale; run with --generate-fixtures");
  for (const definition of manifest.perspectiveCases || []) {
    const committed = path.join(FIXTURE_DIR, "perspective", `${definition.id}.png`);
    assert(fs.existsSync(committed) && fs.readFileSync(committed).equals(perspectiveFrames.get(definition.id)), `${definition.id}.png is stale; run with --generate-fixtures`);
  }

  const { server, baseUrl } = await createServer();
  const results = [];
  try {
    const decoderCases = [
      { id: "barcode-success", detectorMode: "success", detectorRaw: compactText, expect: "updated", expectedDecoder: "barcode-detector", expectedJsQrAttempts: 0 },
      { id: "barcode-empty-jsqr", detectorMode: "empty", expect: "updated", expectedDecoder: "jsqr" },
      { id: "barcode-absent-jsqr", detectorMode: "absent", expect: "updated", expectedDecoder: "jsqr" },
      { id: "barcode-throws", detectorMode: "throw", expect: "updated", expectedDecoder: "jsqr" },
      { id: "decoded-non-plan", detectorMode: "success", detectorRaw: "https://example.invalid/not-a-plan", expect: "unchanged", expectedDecoder: "barcode-detector", expectedJsQrAttempts: 0 },
      { id: "jsqr-throws", detectorMode: "empty", jsQrMode: "throw", expect: "unchanged", expectedDecoder: "none" }
    ];
    for (const definition of decoderCases.filter((item) => !selectedCase || item.id === selectedCase)) {
      console.log(`RUN  ${definition.id}`);
      results.push(await runDecoderCase(browser, baseUrl, definition, references.compact));
    }
    if (!selectedCase || selectedCase === "live-camera-permission-and-cleanup") {
      console.log("RUN  live-camera-permission-and-cleanup");
      results.push(await runCameraLifecycleCase(browser, baseUrl));
    }
    if (!selectedCase || selectedCase === "lossless-media-replacement") {
      console.log("RUN  lossless-media-replacement");
      results.push(await runMediaReplacementCase(browser, baseUrl, references.compact));
    }
    for (const definition of manifest.staticCases.filter((item) => !selectedCase || item.id === selectedCase)) {
      console.log(`RUN  ${definition.id}`);
      results.push(await runStaticCase(browser, baseUrl, renderPage, definition));
    }
    for (const definition of (manifest.perspectiveCases || []).filter((item) => !selectedCase || item.id === selectedCase)) {
      console.log(`RUN  ${definition.id}`);
      results.push(await runStaticCase(browser, baseUrl, renderPage, { ...definition, category: "perspective-image" }, perspectiveFrames.get(definition.id)));
    }
    for (const definition of manifest.streamCases.filter((item) => !selectedCase || item.id === selectedCase)) {
      console.log(`RUN  ${definition.id}`);
      results.push(await runStreamCase(browser, baseUrl, renderPage, definition));
    }
  } finally {
    server.close();
    await renderContext.close();
    await browser.close();
  }

  const { spawnSync } = require("child_process");
  const commitProbe = spawnSync("git", ["rev-parse", "--short", "HEAD"], { cwd: ROOT, encoding: "utf8" });
  const run = {
    version: VERSION,
    generatedAt: new Date().toISOString(),
    gitCommit: commitProbe.status === 0 ? commitProbe.stdout.trim() : "unknown",
    environment: `${process.platform} ${os.release()} / Node ${process.version} / Chromium ${chromium._revision || "Playwright-managed"}`,
    android: await detectAndroid(),
    results
  };
  if (selectedCase && results.length === 0) throw new Error(`unknown patient scan case: ${selectedCase}`);
  const jsonPath = path.join(OUTPUT_DIR, "results.json");
  const reportPath = path.join(OUTPUT_DIR, "report.md");
  fs.writeFileSync(jsonPath, JSON.stringify(run, null, 2) + "\n");
  fs.writeFileSync(reportPath, markdownReport(run));

  for (const result of results) {
    const label = result.status === "pass" ? "PASS" : result.status === "fail" ? "FAIL" : "WARN";
    console.log(`${label.padEnd(4)} ${result.id} (${result.decoder || "none"})`);
  }
  console.log(`Results: ${path.relative(ROOT, jsonPath)}`);
  console.log(`Report:  ${path.relative(ROOT, reportPath)}`);
  const failures = results.filter((result) => result.gate && result.status === "fail");
  if (failures.length) {
    throw new Error(`patient scan camera battery failed: ${failures.map((result) => result.id).join(", ")}`);
  }
}

main().catch((error) => {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
});
