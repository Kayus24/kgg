#!/usr/bin/env node
/*
 * Bounded, one-shot Playwright host for the KGG UI-Lab MCP bridge.
 *
 * The Python MCP server owns authorization, leases, URL policy and evidence
 * binding. This helper only owns one ephemeral browser context for one
 * already-authorized run. It never writes a screenshot to disk and never
 * accepts arbitrary JavaScript, shell commands or unrestricted selectors.
 */

const readline = require("readline");
const crypto = require("crypto");
const { chromium } = require("playwright");

const MAX_TEXT = 200;
const MAX_IMAGE_BYTES = 2 * 1024 * 1024;
const SAFE_LABEL = /^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$/;
const SAFE_RUN = /^[a-z0-9][a-z0-9-]{5,128}$/;
const ALLOWED_HTTPS_HOST = "kayus24.github.io";

function allowedKggPath(pathname) {
  return pathname === "/kgg" || pathname === "/kgg-patient-preview" || pathname.startsWith("/kgg/") || pathname.startsWith("/kgg-patient-preview/");
}

function allowedPageUrl(value) {
  let parsed;
  try { parsed = new URL(value); } catch { return false; }
  const localHttp = parsed.protocol === "http:" && (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1");
  const https = parsed.protocol === "https:" && parsed.hostname === ALLOWED_HTTPS_HOST && allowedKggPath(parsed.pathname);
  return (localHttp || https) && !parsed.username && !parsed.password && !parsed.hash;
}

function fail(code, detail = "") {
  const error = new Error(detail ? `${code}: ${detail}` : code);
  error.code = code;
  throw error;
}

function safeText(value, label) {
  if (typeof value !== "string" || value.length < 1 || value.length > MAX_TEXT || !SAFE_LABEL.test(value)) {
    fail(`${label}_invalid`);
  }
  const lowered = value.toLowerCase();
  for (const token of ["token", "secret", "password", "api_key", "patient_data", "raw_qr", "base64"]) {
    if (lowered.includes(token)) fail("sensitive_field", label);
  }
  return value;
}

function safeUrl(value) {
  let parsed;
  try { parsed = new URL(value); } catch { fail("app_url_invalid"); }
  const localHttp = parsed.protocol === "http:" && (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1");
  const https = parsed.protocol === "https:" && parsed.hostname === ALLOWED_HTTPS_HOST && allowedKggPath(parsed.pathname);
  if ((!localHttp && !https) || parsed.username || parsed.password || parsed.hash) fail("app_url_invalid");
  return parsed.toString();
}

function safeViewport(value) {
  if (!value || !Number.isInteger(value.width) || !Number.isInteger(value.height) ||
      value.width < 240 || value.width > 10000 || value.height < 240 || value.height > 10000 ||
      typeof value.device_scale_factor !== "number" || value.device_scale_factor < 0.5 || value.device_scale_factor > 4) {
    fail("viewport_invalid");
  }
  return { width: value.width, height: value.height, deviceScaleFactor: value.device_scale_factor };
}

function safeStep(step) {
  if (!step || typeof step !== "object" || typeof step.operation !== "string") fail("step_invalid");
  const operation = step.operation;
  if (!["read_state", "click", "tap", "type", "scroll", "reload", "back", "wait", "capture_screenshot"].includes(operation)) {
    fail("step_operation_invalid");
  }
  const label = safeText(step.label || operation, "step_label");
  const result = { operation, label };
  if (operation === "wait") {
    const timeout = step.timeout_ms === undefined ? 1000 : step.timeout_ms;
    if (!Number.isInteger(timeout) || timeout < 1 || timeout > 5000) fail("wait_timeout_invalid");
    result.timeout_ms = timeout;
  }
  if (operation === "type") {
    if (typeof step.text !== "string" || step.text.length > MAX_TEXT) fail("type_text_invalid");
    result.text = step.text;
  }
  if (operation === "scroll") {
    const delta = step.delta_y === undefined ? 500 : step.delta_y;
    if (!Number.isInteger(delta) || delta < -10000 || delta > 10000) fail("scroll_delta_invalid");
    result.delta_y = delta;
  }
  if (step.coordinates !== undefined) {
    const point = step.coordinates;
    if (!point || !Number.isInteger(point.x) || !Number.isInteger(point.y) || point.x < 0 || point.y < 0) fail("coordinates_invalid");
    result.coordinates = { x: point.x, y: point.y };
  }
  return result;
}

function hashBytes(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function artifact(runId, sequence, buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 1 || buffer.length > MAX_IMAGE_BYTES) fail("screenshot_too_large");
  return {
    id: `kgg-shot-${runId.slice(-12)}-${String(sequence).padStart(2, "0")}`,
    kind: "screenshot",
    ref: `memory://kgg-ui-lab/${runId}/screenshot-${sequence}.png`,
    sha256: hashBytes(buffer),
    content_type: "image/png",
    data_base64: buffer.toString("base64"),
  };
}

async function stateValue(page) {
  const value = await page.evaluate(() => {
    const node = document.querySelector("[data-kgg-state]");
    return node?.getAttribute("data-kgg-state") || document.body?.getAttribute("data-kgg-state") || "unknown";
  });
  return safeText(String(value), "state");
}

async function locateAction(page, label) {
  const escaped = label.replace(/"/g, "");
  const marked = page.locator(`[data-kgg-action="${escaped}"]`).first();
  if (await marked.count()) return marked;
  const roleButton = page.getByRole("button", { name: label, exact: true }).first();
  if (await roleButton.count()) return roleButton;
  fail("action_target_not_found");
}

async function performStep(page, step, runId, screenshotNumber) {
  const operation = step.operation;
  if (operation === "read_state") {
    const state = await stateValue(page);
    return { expected: step.label, actual: state, status: "pass", artifacts: [], state };
  }
  if (operation === "capture_screenshot") {
    const image = await page.screenshot({ type: "png", animations: "disabled" });
    const shot = artifact(runId, screenshotNumber, image);
    return { expected: "screenshot", actual: "screenshot captured", status: "pass", artifacts: [shot], state: await stateValue(page) };
  }
  if (operation === "click" || operation === "tap") {
    if (step.coordinates) {
      await page.mouse.click(step.coordinates.x, step.coordinates.y, { timeout: 5000 });
    } else {
      await (await locateAction(page, step.label)).click({ timeout: 5000 });
    }
    return { expected: step.label, actual: "action completed", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  if (operation === "type") {
    const input = page.locator(`[data-kgg-input="${step.label.replace(/"/g, "")}"]`).first();
    if (!(await input.count())) fail("input_target_not_found");
    await input.fill(step.text);
    return { expected: step.label, actual: "text entered", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  if (operation === "scroll") {
    await page.mouse.wheel(0, step.delta_y);
    return { expected: step.label, actual: "scroll completed", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  if (operation === "reload") {
    await page.reload({ waitUntil: "domcontentloaded", timeout: 5000 });
    return { expected: step.label, actual: "reload completed", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  if (operation === "back") {
    await page.goBack({ waitUntil: "domcontentloaded", timeout: 5000 });
    return { expected: step.label, actual: "back completed", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  if (operation === "wait") {
    await page.waitForTimeout(step.timeout_ms);
    return { expected: step.label, actual: "wait completed", status: "pass", artifacts: [], state: await stateValue(page) };
  }
  fail("step_operation_invalid");
}

async function run(request) {
  if (!request || request.command !== "run" || !SAFE_RUN.test(String(request.run_id || ""))) fail("host_request_invalid");
  const runId = String(request.run_id);
  const url = safeUrl(request.url);
  const viewport = safeViewport(request.viewport);
  if (!Array.isArray(request.steps) || request.steps.length < 1 || request.steps.length > 20) fail("steps_invalid");
  const steps = request.steps.map(safeStep);
  const started = Date.now();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: viewport.deviceScaleFactor });
  const page = await context.newPage();
  let originViolation = false;
  page.on("framenavigated", frame => {
    if (frame === page.mainFrame() && !allowedPageUrl(frame.url())) originViolation = true;
  });
  const output = [];
  const artifacts = [];
  let screenshotNumber = 0;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
    if (originViolation || !allowedPageUrl(page.url())) fail("origin_escape");
    for (const step of steps) {
      if (originViolation || !allowedPageUrl(page.url())) fail("origin_escape");
      if (step.operation === "capture_screenshot") screenshotNumber += 1;
      const value = await performStep(page, step, runId, screenshotNumber);
      output.push(value);
      for (const item of value.artifacts) artifacts.push(item);
    }
    if (originViolation || !allowedPageUrl(page.url())) fail("origin_escape");
    const finalState = await stateValue(page);
    return { status: "PASS", error_class: "", steps: output, artifacts, final_state: finalState, runtime_ms: Date.now() - started };
  } catch (error) {
    return { status: "FAIL", error_class: error.code || "REAL_BROWSER_STEP_FAILED", steps: output, artifacts, final_state: "unknown", runtime_ms: Date.now() - started };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

async function main() {
  const input = await new Promise((resolve, reject) => {
    let data = "";
    const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
    rl.on("line", line => { data += line; rl.close(); });
    rl.on("close", () => resolve(data));
    rl.on("error", reject);
  });
  try {
    const request = JSON.parse(input);
    process.stdout.write(JSON.stringify(await run(request)) + "\n");
  } catch (error) {
    process.stdout.write(JSON.stringify({ status: "FAIL", error_class: error.code || "REAL_BROWSER_HOST_FAILED", steps: [], artifacts: [], final_state: "unknown", runtime_ms: 0 }) + "\n");
    process.exitCode = 1;
  }
}

main();
