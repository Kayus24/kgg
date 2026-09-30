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
const MAX_ELEMENT_REFS = 40;
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

function safeOptionalElementText(value) {
  if (typeof value !== "string") return null;
  const normalized = value.trim().replace(/\s+/g, " ");
  if (!normalized || normalized.length > MAX_TEXT || !SAFE_LABEL.test(normalized)) return null;
  const lowered = normalized.toLowerCase();
  for (const token of ["token", "secret", "password", "api_key", "patient_data", "raw_qr", "base64"]) {
    if (lowered.includes(token)) return null;
  }
  return normalized;
}

async function elementSnapshot(page, policy) {
  assertSafePage();
  const locator = page.locator(
    `[${policy.action_attribute}], [${policy.input_attribute}], button, a[href], input, textarea, select, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="switch"], [role="textbox"], [role="combobox"]`
  );
  const raw = await locator.evaluateAll((nodes, config) => {
    const roleFor = node => {
      const explicit = node.getAttribute("role");
      if (explicit) return explicit.toLowerCase();
      const tag = node.tagName.toLowerCase();
      if (tag === "button") return "button";
      if (tag === "a") return "link";
      if (tag === "textarea") return "textbox";
      if (tag === "select") return "combobox";
      if (tag === "input") {
        const type = String(node.getAttribute("type") || "text").toLowerCase();
        if (type === "checkbox") return "checkbox";
        if (type === "radio") return "radio";
        if (["button", "submit", "reset"].includes(type)) return "button";
        return "textbox";
      }
      if (node.hasAttribute(config.actionAttribute)) return "action";
      if (node.hasAttribute(config.inputAttribute)) return "textbox";
      return "generic";
    };
    return nodes.map((node, nodeIndex) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      if (node.hidden || node.getAttribute("aria-hidden") === "true" || style.display === "none" ||
          style.visibility === "hidden" || rect.width <= 0 || rect.height <= 0) return null;
      const type = String(node.getAttribute("type") || "").toLowerCase();
      return {
        node_index: nodeIndex,
        role: roleFor(node),
        action_id: node.getAttribute(config.actionAttribute),
        input_id: node.getAttribute(config.inputAttribute),
        label: node.getAttribute("aria-label") || node.getAttribute("placeholder"),
        sensitive: type === "password",
      };
    }).filter(Boolean).slice(0, config.maxItems);
  }, {
    actionAttribute: policy.action_attribute,
    inputAttribute: policy.input_attribute,
    maxItems: MAX_ELEMENT_REFS,
  });

  const allowedRoles = new Set(["button", "link", "textbox", "checkbox", "radio", "switch", "combobox", "action", "generic"]);
  const elements = [];
  const refs = new Map();
  for (const item of raw) {
    if (!item || item.sensitive === true || !allowedRoles.has(String(item.role))) continue;
    const actionId = safeOptionalElementText(item.action_id);
    const inputId = safeOptionalElementText(item.input_id);
    const label = safeOptionalElementText(item.label);
    const handle = await locator.nth(item.node_index).elementHandle();
    if (!handle) continue;
    const ref = `e${elements.length + 1}`;
    const element = { ref, role: String(item.role) };
    if (actionId) element.action_id = actionId;
    if (inputId) element.input_id = inputId;
    if (label) element.label = label;
    refs.set(ref, handle);
    elements.push(element);
    if (elements.length >= MAX_ELEMENT_REFS) break;
  }
  return { elements, refs };
}

async function locateAction(page, label, policy) {
  const escaped = label.replace(/"/g, "");
  const marked = page.locator(`[${policy.action_attribute}="${escaped}"]`).first();
  if (await marked.count()) return marked;
  const roleButton = page.getByRole("button", { name: label, exact: true }).first();
  if (await roleButton.count()) return roleButton;
  fail("action_target_not_found");
}

async function performAction(page, step, policy, elementRefs) {
  const before = await stateValue(page, policy);
  if (step.operation === "click" || step.operation === "tap") {
    if (step.element_ref) {
      const target = elementRefs.get(step.element_ref);
      if (!target) fail("element_ref_not_found");
      if (!(await target.isVisible())) fail("element_ref_stale");
      await target.click({ timeout: 5000 });
    } else if (step.coordinates) {
      await page.mouse.click(step.coordinates.x, step.coordinates.y, { timeout: 5000 });
    } else {
      await (await locateAction(page, step.label, policy)).click({ timeout: 5000 });
    }
  } else if (step.operation === "type") {
    if (step.element_ref) {
      const target = elementRefs.get(step.element_ref);
      if (!target) fail("element_ref_not_found");
      if (!(await target.isVisible())) fail("element_ref_stale");
      await target.fill(step.text);
    } else {
      const input = page.locator(`[${policy.input_attribute}="${step.label.replace(/"/g, "")}"]`).first();
      if (!(await input.count())) fail("input_target_not_found");
      await input.fill(step.text);
    }
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

const session = { browser: null, context: null, page: null, runId: null, screenshotNumber: 0, originViolation: false, policy: DEFAULT_POLICY, viewport: null, elementRefs: new Map() };

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
    session.elementRefs = new Map();
    await session.page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
    assertSafePage();
    return { status: "PASS", error_class: "", state: await stateValue(session.page, session.policy) };
  }
  if (!session.page) fail("visual_session_not_initialized");
  if (request.command === "observe") {
    assertSafePage();
    session.screenshotNumber += 1;
    const observed = await screenshot(session.page, session.runId, session.screenshotNumber, session.policy);
    const snapshot = await elementSnapshot(session.page, session.policy);
    session.elementRefs = snapshot.refs;
    return { status: "PASS", error_class: "", state: observed.state, artifacts: [observed.artifact], elements: snapshot.elements };
  }
  if (request.command === "act") {
    assertSafePage();
    const step = safeStep(request.step, session.viewport);
    return { status: "PASS", error_class: "", action: await performAction(session.page, step, session.policy, session.elementRefs) };
  }
  if (request.command === "close") {
    await session.context?.close().catch(() => {});
    await session.browser?.close().catch(() => {});
    session.browser = null;
    session.context = null;
    session.page = null;
    session.viewport = null;
    session.policy = DEFAULT_POLICY;
    session.elementRefs = new Map();
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
