#!/usr/bin/env node
/*
 * Bounded persistent Playwright host for one KGG visual interaction loop.
 *
 * The Python MCP boundary owns authorization, leases and evidence binding.
 * This helper owns one ephemeral page only until close.  It accepts a tiny
 * JSONL protocol (init, observe, act, close), never arbitrary JavaScript or
 * selectors, and keeps screenshots in memory.
 */

const readline = require("readline");
const crypto = require("crypto");
const { chromium } = require("playwright");

const MAX_TEXT = 200;
const MAX_IMAGE_BYTES = 2 * 1024 * 1024;
const SAFE_LABEL = /^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$/;
const SAFE_RUN = /^[a-z0-9][a-z0-9-]{5,128}$/;

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
  const https = parsed.protocol === "https:" && Boolean(parsed.hostname);
  if ((!localHttp && !https) || parsed.username || parsed.password) fail("app_url_invalid");
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

function safeCoordinates(value) {
  if (value === undefined) return undefined;
  if (!value || !Number.isInteger(value.x) || !Number.isInteger(value.y) || value.x < 0 || value.y < 0) {
    fail("coordinates_invalid");
  }
  return { x: value.x, y: value.y };
}

function safeStep(step) {
  if (!step || typeof step !== "object" || typeof step.operation !== "string") fail("step_invalid");
  if (!["click", "tap", "type", "scroll", "wait"].includes(step.operation)) fail("step_operation_invalid");
  const result = { operation: step.operation, label: safeText(step.label || step.operation, "step_label") };
  result.coordinates = safeCoordinates(step.coordinates);
  if (step.operation === "type") {
    if (typeof step.text !== "string" || step.text.length > MAX_TEXT) fail("type_text_invalid");
    result.text = step.text;
  }
  if (step.operation === "scroll") {
    const delta = step.delta_y === undefined ? 500 : step.delta_y;
    if (!Number.isInteger(delta) || delta < -10000 || delta > 10000) fail("scroll_delta_invalid");
    result.delta_y = delta;
  }
  if (step.operation === "wait") {
    const timeout = step.timeout_ms === undefined ? 1000 : step.timeout_ms;
    if (!Number.isInteger(timeout) || timeout < 1 || timeout > 5000) fail("wait_timeout_invalid");
    result.timeout_ms = timeout;
  }
  return result;
}

function hashBytes(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function artifact(runId, sequence, buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 1 || buffer.length > MAX_IMAGE_BYTES) fail("screenshot_too_large");
  return {
    id: `kgg-visual-${runId.slice(-12)}-${String(sequence).padStart(2, "0")}`,
    kind: "screenshot",
    ref: `memory://kgg-ui-lab/${runId}/visual-${sequence}.png`,
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

async function performAction(page, step) {
  const before = await stateValue(page);
  if (step.operation === "click" || step.operation === "tap") {
    if (step.coordinates) {
      await page.mouse.click(step.coordinates.x, step.coordinates.y, { timeout: 5000 });
    } else {
      await (await locateAction(page, step.label)).click({ timeout: 5000 });
    }
  } else if (step.operation === "type") {
    const input = page.locator(`[data-kgg-input="${step.label.replace(/"/g, "")}"]`).first();
    if (!(await input.count())) fail("input_target_not_found");
    await input.fill(step.text);
  } else if (step.operation === "scroll") {
    await page.mouse.wheel(0, step.delta_y);
  } else if (step.operation === "wait") {
    await page.waitForTimeout(step.timeout_ms);
  } else {
    fail("step_operation_invalid");
  }
  return { expected: step.label, actual: "action completed", status: "pass", before_state: before, after_state: await stateValue(page) };
}

async function screenshot(page, runId, sequence) {
  const image = await page.screenshot({ type: "png", animations: "disabled" });
  return { artifact: artifact(runId, sequence, image), state: await stateValue(page) };
}

const session = { browser: null, context: null, page: null, runId: null, screenshotNumber: 0 };

async function handle(request) {
  if (!request || typeof request.command !== "string") fail("host_request_invalid");
  if (request.command === "init") {
    if (session.page) fail("visual_session_exists");
    if (!SAFE_RUN.test(String(request.run_id || ""))) fail("host_request_invalid");
    const url = safeUrl(request.url);
    const viewport = safeViewport(request.viewport);
    session.browser = await chromium.launch({ headless: true });
    session.context = await session.browser.newContext({ viewport, deviceScaleFactor: viewport.deviceScaleFactor });
    session.page = await session.context.newPage();
    session.runId = String(request.run_id);
    session.screenshotNumber = 0;
    await session.page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
    return { status: "PASS", error_class: "", state: await stateValue(session.page) };
  }
  if (!session.page) fail("visual_session_not_initialized");
  if (request.command === "observe") {
    session.screenshotNumber += 1;
    const observed = await screenshot(session.page, session.runId, session.screenshotNumber);
    return { status: "PASS", error_class: "", state: observed.state, artifacts: [observed.artifact] };
  }
  if (request.command === "act") {
    const step = safeStep(request.step);
    return { status: "PASS", error_class: "", action: await performAction(session.page, step) };
  }
  if (request.command === "close") {
    await session.context?.close().catch(() => {});
    await session.browser?.close().catch(() => {});
    session.browser = null;
    session.context = null;
    session.page = null;
    return { status: "PASS", error_class: "", state: "closed" };
  }
  fail("host_command_invalid");
}

async function closeSession() {
  await session.context?.close().catch(() => {});
  await session.browser?.close().catch(() => {});
}

async function main() {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  try {
    for await (const line of rl) {
      if (!line.trim()) continue;
      try {
        process.stdout.write(JSON.stringify(await handle(JSON.parse(line))) + "\n");
      } catch (error) {
        process.stdout.write(JSON.stringify({ status: "FAIL", error_class: error.code || "REAL_BROWSER_HOST_FAILED", state: "unknown", artifacts: [] }) + "\n");
      }
    }
  } finally {
    await closeSession();
  }
}

main();
