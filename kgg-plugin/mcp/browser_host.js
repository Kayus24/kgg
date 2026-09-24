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
const ATTRIBUTE_RE = /^data-[a-z0-9-]{1,63}$/;
const NAMESPACE_RE = /^[a-z0-9][a-z0-9._-]{1,63}$/;
const DEFAULT_POLICY = {
  allowed_https_hosts: ["kayus24.github.io"],
  allowed_https_path_prefixes: ["/kgg", "/kgg-patient-preview"],
  state_attribute: "data-kgg-state",
  action_attribute: "data-kgg-action",
  input_attribute: "data-kgg-input",
  evidence_namespace: "kgg-ui-lab",
};

function normalizePolicy(value) {
  const policy = value && typeof value === "object" ? value : DEFAULT_POLICY;
  const hosts = Array.isArray(policy.allowed_https_hosts) ? policy.allowed_https_hosts : [];
  const prefixes = Array.isArray(policy.allowed_https_path_prefixes) ? policy.allowed_https_path_prefixes : [];
  const attributes = [policy.state_attribute, policy.action_attribute, policy.input_attribute];
  if (!hosts.every(host => typeof host === "string" && host.length > 0 && !host.includes("/")) ||
      !prefixes.every(prefix => typeof prefix === "string" && prefix.startsWith("/")) ||
      !attributes.every(attribute => typeof attribute === "string" && ATTRIBUTE_RE.test(attribute)) ||
      typeof policy.evidence_namespace !== "string" || !NAMESPACE_RE.test(policy.evidence_namespace)) {
    fail("browser_policy_invalid");
  }
  return {
    allowed_https_hosts: hosts,
    allowed_https_path_prefixes: prefixes,
    state_attribute: policy.state_attribute,
    action_attribute: policy.action_attribute,
    input_attribute: policy.input_attribute,
    evidence_namespace: policy.evidence_namespace,
  };
}

function allowedPath(pathname, prefixes) {
  return prefixes.some(prefix => {
    const normalized = prefix.replace(/\/+$/, "") || "/";
    return pathname === normalized || pathname.startsWith(`${normalized}/`);
  });
}

function allowedPageUrl(value, policy = DEFAULT_POLICY) {
  let parsed;
  try { parsed = new URL(value); } catch { return false; }
  const localHttp = parsed.protocol === "http:" && (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1");
  const https = parsed.protocol === "https:" && policy.allowed_https_hosts.includes(parsed.hostname) && allowedPath(parsed.pathname, policy.allowed_https_path_prefixes);
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

function safeUrl(value, policy) {
  let parsed;
  try { parsed = new URL(value); } catch { fail("app_url_invalid"); }
  const localHttp = parsed.protocol === "http:" && (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1");
  if (!allowedPageUrl(value, policy) || (!localHttp && parsed.protocol !== "https:") || parsed.username || parsed.password || parsed.hash) fail("app_url_invalid");
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

function safeSwipePoint(value, label, viewport) {
  if (!value || !Number.isInteger(value.x) || !Number.isInteger(value.y) || value.x < 0 || value.y < 0) fail(`${label}_invalid`);
  if (value.x >= viewport.width || value.y >= viewport.height) fail("swipe_bounds_invalid");
  return { x: value.x, y: value.y };
}

function safeStep(step, viewport) {
  if (!step || typeof step !== "object" || typeof step.operation !== "string") fail("step_invalid");
  const operation = step.operation;
  if (!["read_state", "click", "tap", "type", "scroll", "swipe", "reload", "back", "wait", "capture_screenshot"].includes(operation)) {
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
  if (operation === "swipe") {
    result.start = safeSwipePoint(step.start, "swipe_start", viewport);
    result.end = safeSwipePoint(step.end, "swipe_end", viewport);
    if (result.start.x === result.end.x && result.start.y === result.end.y) fail("swipe_unchanged");
    const duration = step.duration_ms === undefined ? 300 : step.duration_ms;
    if (!Number.isInteger(duration) || duration < 50 || duration > 5000) fail("swipe_duration_invalid");
    result.duration_ms = duration;
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

function artifact(runId, sequence, buffer, policy) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 1 || buffer.length > MAX_IMAGE_BYTES) fail("screenshot_too_large");
  return {
    id: `${policy.evidence_namespace}-shot-${runId.slice(-12)}-${String(sequence).padStart(2, "0")}`,
    kind: "screenshot",
    ref: `memory://${policy.evidence_namespace}/${runId}/screenshot-${sequence}.png`,
    sha256: hashBytes(buffer),
    content_type: "image/png",
    data_base64: buffer.toString("base64"),
  };
}

async function stateValue(page, policy) {
  const marker = await page.evaluate(attribute => {
    const node = document.querySelector(`[${attribute}]`);
    return node?.getAttribute(attribute) || document.body?.getAttribute(attribute) || "unknown";
  }, policy.state_attribute);
  return safeText(String(marker), "state");
}

async function locateAction(page, label, policy) {
  const escaped = label.replace(/"/g, "");
  const marked = page.locator(`[${policy.action_attribute}="${escaped}"]`).first();
  if (await marked.count()) return marked;
  const roleButton = page.getByRole("button", { name: label, exact: true }).first();
  if (await roleButton.count()) return roleButton;
  fail("action_target_not_found");
}

async function performStep(page, step, runId, screenshotNumber, policy) {
  const operation = step.operation;
  if (operation === "read_state") {
    const state = await stateValue(page, policy);
    return { expected: step.label, actual: state, status: "pass", artifacts: [], state };
  }
  if (operation === "capture_screenshot") {
    const image = await page.screenshot({ type: "png", animations: "disabled" });
    const shot = artifact(runId, screenshotNumber, image, policy);
    return { expected: "screenshot", actual: "screenshot captured", status: "pass", artifacts: [shot], state: await stateValue(page, policy) };
  }
  if (operation === "click" || operation === "tap") {
    if (step.coordinates) {
      await page.mouse.click(step.coordinates.x, step.coordinates.y, { timeout: 5000 });
    } else {
      await (await locateAction(page, step.label, policy)).click({ timeout: 5000 });
    }
    return { expected: step.label, actual: "action completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "type") {
    const input = page.locator(`[${policy.input_attribute}="${step.label.replace(/"/g, "")}"]`).first();
    if (!(await input.count())) fail("input_target_not_found");
    await input.fill(step.text);
    return { expected: step.label, actual: "text entered", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "scroll") {
    await page.mouse.wheel(0, step.delta_y);
    return { expected: step.label, actual: "scroll completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "swipe") {
    const moveSteps = Math.max(2, Math.ceil(step.duration_ms / 16));
    const delay = Math.max(1, Math.floor(step.duration_ms / moveSteps));
    await page.mouse.move(step.start.x, step.start.y);
    await page.mouse.down();
    try {
      for (let index = 1; index <= moveSteps; index += 1) {
        const progress = index / moveSteps;
        const x = Math.round(step.start.x + (step.end.x - step.start.x) * progress);
        const y = Math.round(step.start.y + (step.end.y - step.start.y) * progress);
        await page.mouse.move(x, y);
        if (index < moveSteps) await page.waitForTimeout(delay);
      }
    } finally {
      await page.mouse.up().catch(() => {});
    }
    return { expected: step.label, actual: "swipe completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "reload") {
    await page.reload({ waitUntil: "domcontentloaded", timeout: 5000 });
    return { expected: step.label, actual: "reload completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "back") {
    await page.goBack({ waitUntil: "domcontentloaded", timeout: 5000 });
    return { expected: step.label, actual: "back completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  if (operation === "wait") {
    await page.waitForTimeout(step.timeout_ms);
    return { expected: step.label, actual: "wait completed", status: "pass", artifacts: [], state: await stateValue(page, policy) };
  }
  fail("step_operation_invalid");
}

async function run(request) {
  if (!request || request.command !== "run" || !SAFE_RUN.test(String(request.run_id || ""))) fail("host_request_invalid");
  const runId = String(request.run_id);
  const policy = normalizePolicy(request.policy);
  const url = safeUrl(request.url, policy);
  const viewport = safeViewport(request.viewport);
  if (!Array.isArray(request.steps) || request.steps.length < 1 || request.steps.length > 20) fail("steps_invalid");
  const steps = request.steps.map(step => safeStep(step, viewport));
  const started = Date.now();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: viewport.deviceScaleFactor });
  const page = await context.newPage();
  let originViolation = false;
  page.on("framenavigated", frame => {
    if (frame === page.mainFrame() && !allowedPageUrl(frame.url(), policy)) originViolation = true;
  });
  const output = [];
  const artifacts = [];
  let screenshotNumber = 0;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
    if (originViolation || !allowedPageUrl(page.url(), policy)) fail("origin_escape");
    for (const step of steps) {
      if (originViolation || !allowedPageUrl(page.url(), policy)) fail("origin_escape");
      if (step.operation === "capture_screenshot") screenshotNumber += 1;
      const value = await performStep(page, step, runId, screenshotNumber, policy);
      output.push(value);
      for (const item of value.artifacts) artifacts.push(item);
    }
    if (originViolation || !allowedPageUrl(page.url(), policy)) fail("origin_escape");
    const finalState = await stateValue(page, policy);
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
