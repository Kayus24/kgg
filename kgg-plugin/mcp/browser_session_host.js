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
const ATTRIBUTE_RE = /^data-[a-z0-9-]{1,63}$/;
const NAMESPACE_RE = /^[a-z0-9][a-z0-9._-]{1,63}$/;
const DEFAULT_POLICY = {
  allowed_https_hosts: ["kayus24.github.io"],
  allowed_https_path_prefixes: ["/kgg", "/kgg-patient-preview"],
  state_attribute: "data-kgg-state",
  action_attribute: "data-kgg-action",
  input_attribute: "data-kgg-input",
  language_toggle_id: "kggLangSwitch",
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
      (policy.language_toggle_id !== null && (typeof policy.language_toggle_id !== "string" || !/^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(policy.language_toggle_id))) ||
      typeof policy.evidence_namespace !== "string" || !NAMESPACE_RE.test(policy.evidence_namespace)) {
    fail("browser_policy_invalid");
  }
  return {
    allowed_https_hosts: hosts,
    allowed_https_path_prefixes: prefixes,
    state_attribute: policy.state_attribute,
    action_attribute: policy.action_attribute,
    input_attribute: policy.input_attribute,
    language_toggle_id: policy.language_toggle_id,
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

function safeCoordinates(value) {
  if (value === undefined) return undefined;
  if (!value || !Number.isInteger(value.x) || !Number.isInteger(value.y) || value.x < 0 || value.y < 0) {
    fail("coordinates_invalid");
  }
  return { x: value.x, y: value.y };
}

function safeSwipePoint(value, label, viewport) {
  const point = safeCoordinates(value);
  if (!point) fail(`${label}_invalid`);
  if (point.x >= viewport.width || point.y >= viewport.height) fail("swipe_bounds_invalid");
  return point;
}

function safeStep(step, viewport) {
  if (!step || typeof step !== "object" || typeof step.operation !== "string") fail("step_invalid");
  if (!["click", "tap", "type", "scroll", "wait", "swipe"].includes(step.operation)) fail("step_operation_invalid");
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
  if (step.operation === "swipe") {
    result.start = safeSwipePoint(step.start, "swipe_start", viewport);
    result.end = safeSwipePoint(step.end, "swipe_end", viewport);
    if (result.start.x === result.end.x && result.start.y === result.end.y) fail("swipe_unchanged");
    const duration = step.duration_ms === undefined ? 300 : step.duration_ms;
    if (!Number.isInteger(duration) || duration < 50 || duration > 5000) fail("swipe_duration_invalid");
    result.duration_ms = duration;
  }
  return result;
}

function hashBytes(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function artifact(runId, sequence, buffer, policy) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 1 || buffer.length > MAX_IMAGE_BYTES) fail("screenshot_too_large");
  return {
    id: `${policy.evidence_namespace}-visual-${runId.slice(-12)}-${String(sequence).padStart(2, "0")}`,
    kind: "screenshot",
    ref: `memory://${policy.evidence_namespace}/${runId}/visual-${sequence}.png`,
    sha256: hashBytes(buffer),
    content_type: "image/png",
    data_base64: buffer.toString("base64"),
  };
}

async function stateValue(page, policy) {
  assertSafePage();
  const marker = await page.evaluate(config => {
    const node = document.querySelector(`[${config.state_attribute}]`);
    const explicit = node?.getAttribute(config.state_attribute) || document.body?.getAttribute(config.state_attribute);
    if (explicit) return { kind: "explicit", value: explicit };
    // Some supported synthetic patient previews expose a bounded language
    // toggle but no data-kgg-state marker. Expose only that non-sensitive
    // state, never page text, values, or storage contents.
    const languageToggle = (config.language_toggle_id && document.getElementById(config.language_toggle_id)) || document.querySelector(`[${config.action_attribute}="language-toggle"]`);
    if (languageToggle) {
      let language = "de";
      try { language = localStorage.getItem("kggPatientLang") === "en" ? "en" : "de"; } catch {}
      return { kind: "bounded-language", value: `lang-${language}` };
    }
    return { kind: "unknown", value: "unknown" };
  }, policy);
  return safeText(String(marker.value), "state");
}

async function locateAction(page, label, policy) {
  const escaped = label.replace(/"/g, "");
  const marked = page.locator(`[${policy.action_attribute}="${escaped}"]`).first();
  if (await marked.count()) return marked;
  const roleButton = page.getByRole("button", { name: label, exact: true }).first();
  if (await roleButton.count()) return roleButton;
  fail("action_target_not_found");
}

async function performAction(page, step, policy) {
  const before = await stateValue(page, policy);
  if (step.operation === "click" || step.operation === "tap") {
    if (step.coordinates) {
      await page.mouse.click(step.coordinates.x, step.coordinates.y, { timeout: 5000 });
    } else {
      await (await locateAction(page, step.label, policy)).click({ timeout: 5000 });
    }
  } else if (step.operation === "type") {
    const input = page.locator(`[${policy.input_attribute}="${step.label.replace(/"/g, "")}"]`).first();
    if (!(await input.count())) fail("input_target_not_found");
    await input.fill(step.text);
  } else if (step.operation === "scroll") {
    await page.mouse.wheel(0, step.delta_y);
  } else if (step.operation === "wait") {
    await page.waitForTimeout(step.timeout_ms);
  } else if (step.operation === "swipe") {
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
  } else {
    fail("step_operation_invalid");
  }
  return { expected: step.label, actual: "action completed", status: "pass", before_state: before, after_state: await stateValue(page, policy) };
}

async function screenshot(page, runId, sequence, policy) {
  assertSafePage();
  const image = await page.screenshot({ type: "png", animations: "disabled" });
  return { artifact: artifact(runId, sequence, image, policy), state: await stateValue(page, policy) };
}

const session = { browser: null, context: null, page: null, runId: null, screenshotNumber: 0, originViolation: false, policy: DEFAULT_POLICY, viewport: null };

function assertSafePage() {
  if (!session.page || session.originViolation || !allowedPageUrl(session.page.url(), session.policy)) fail("origin_escape");
}

async function handle(request) {
  if (!request || typeof request.command !== "string") fail("host_request_invalid");
  if (request.command === "init") {
    if (session.page) fail("visual_session_exists");
    if (!SAFE_RUN.test(String(request.run_id || ""))) fail("host_request_invalid");
    const policy = normalizePolicy(request.policy);
    const url = safeUrl(request.url, policy);
    const viewport = safeViewport(request.viewport);
    session.browser = await chromium.launch({ headless: true });
    session.context = await session.browser.newContext({ viewport, deviceScaleFactor: viewport.deviceScaleFactor });
    session.page = await session.context.newPage();
    session.originViolation = false;
    session.policy = policy;
    session.viewport = viewport;
    session.page.on("framenavigated", frame => {
      if (frame === session.page.mainFrame() && !allowedPageUrl(frame.url(), session.policy)) session.originViolation = true;
    });
    session.runId = String(request.run_id);
    session.screenshotNumber = 0;
    await session.page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
    assertSafePage();
    return { status: "PASS", error_class: "", state: await stateValue(session.page, session.policy) };
  }
  if (!session.page) fail("visual_session_not_initialized");
  if (request.command === "observe") {
    assertSafePage();
    session.screenshotNumber += 1;
    const observed = await screenshot(session.page, session.runId, session.screenshotNumber, session.policy);
    return { status: "PASS", error_class: "", state: observed.state, artifacts: [observed.artifact] };
  }
  if (request.command === "act") {
    assertSafePage();
    const step = safeStep(request.step, session.viewport);
    return { status: "PASS", error_class: "", action: await performAction(session.page, step, session.policy) };
  }
  if (request.command === "close") {
    await session.context?.close().catch(() => {});
    await session.browser?.close().catch(() => {});
    session.browser = null;
    session.context = null;
    session.page = null;
    session.viewport = null;
    session.policy = DEFAULT_POLICY;
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
