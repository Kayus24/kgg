#!/usr/bin/env node
/*
 * KGG UI stability smoke.
 *
 * Critical mode is intentionally lightweight and CI-safe: it verifies that the
 * phone-card gesture guards are still present in kgg-update/index.html.
 *
 * Regression mode additionally opens the real HTML in Chromium/Playwright,
 * seeds a 30-card current plan, and performs touch-like PointerEvent gestures
 * against the actual phone plan cards. This is the guard we run after flicker
 * or layout patches, because those patches have historically broken swipe and
 * drag/drop.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const STORAGE_KEY = "kgg_html_app_v2_state";

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { level: "critical" };
  for (let i = 0; i < args.length; i += 1) {
    if ((args[i] === "--level" || args[i] === "--suite") && args[i + 1]) {
      out.level = String(args[i + 1]).toLowerCase();
      i += 1;
    } else if (args[i] === "--browser") {
      out.browser = true;
    } else if (args[i] === "--help" || args[i] === "-h") {
      out.help = true;
    }
  }
  return out;
}

function usage() {
  console.log("Usage: node release-pipeline/kgg_ui_stability_smoke.js --level critical|regression [--browser]");
}

function fail(message) {
  throw new Error(message);
}

function assertIncludes(text, needle, label) {
  if (!text.includes(needle)) fail(`Missing ${label}: ${needle}`);
}

function assertRegex(text, pattern, label) {
  if (!pattern.test(text)) fail(`Missing ${label}: ${pattern}`);
}

function readHtml() {
  if (!fs.existsSync(HTML_PATH)) fail(`HTML file not found: ${HTML_PATH}`);
  return fs.readFileSync(HTML_PATH, "utf8");
}

function staticGestureGuardSuite() {
  const html = readHtml();

  assertIncludes(html, "function startPlanCardSwipeDelete", "plan-card swipe handler");
  assertIncludes(html, "function resetPlanCardSwipe", "plan-card swipe cleanup");
  assertIncludes(html, "card.style.setProperty('--kgg-plan-swipe-x'", "swipe CSS variable update");
  assertRegex(html, /card\.style\.transform\s*=\s*['"]translateX\(var\(--kgg-plan-swipe-x,0px\)\)['"]/, "visible swipe translateX");
  assertIncludes(html, "document.body.classList.add('kggPlanCardSwiping')", "swipe body state");
  assertIncludes(html, "document.body.classList.remove('kggPlanCardSwiping')", "swipe body cleanup");

  assertIncludes(html, "function startAnimatedReorderPress", "drag/drop press handler");
  assertIncludes(html, "press.timer=setTimeout(()=>activateAnimatedReorder(press,ev),100)", "hold-before-drag guard");
  assertIncludes(html, "if(!press.active && (dx>10 || dy>10))", "scroll-before-hold cancellation guard");
  assertIncludes(html, "function cleanupAnimatedReorder", "drag/drop cleanup");
  assertIncludes(html, "press.phoneListAbsoluteDrag=true", "phone local-list drag mode");
  assertIncludes(html, "card.style.setProperty('position','absolute','important')", "phone card absolute positioning");
  assertIncludes(html, "press.listPrevPosition=list.style.getPropertyValue('position')", "planList inline position preservation");
  assertIncludes(html, "press.list.style.removeProperty('position')", "planList inline position cleanup");
  assertIncludes(html, "document.body.classList.add('kggPlanCardReordering')", "drag body state");
  assertIncludes(html, "document.body.classList.remove('kggPlanCardReordering')", "drag body cleanup");

  assertIncludes(html, "body.kggPlanCardSwiping #currentPlanBlock .planCard.swipe-dragging", "phone swipe CSS scope");
  assertIncludes(html, "body.kggPlanCardReordering #currentPlanBlock #planList.planList > .planCard.reorder-lifted", "phone drag CSS scope");
  assertIncludes(html, "transform:translateX(var(--kgg-plan-swipe-x,0px))!important", "phone swipe visible transform override");
  assertIncludes(html, "transform:translate3d(0,0,0)!important", "phone drag local-list transform override");
  assertIncludes(html, "kgg-v11-clean-merge-original-features-phone-drag-local-list", "latest phone drag merge marker");

  console.log("Static UI stability guards OK");
}

function installBundledNodePath() {
  const candidates = [
    path.join(os.homedir(), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules"),
  ];
  const pathEntries = String(process.env.PATH || "")
    .split(path.delimiter)
    .filter(Boolean);
  for (const entry of pathEntries) {
    const normalized = entry.replace(/\\/g, "/");
    if (normalized.endsWith("/node_modules/.bin")) {
      candidates.push(path.dirname(entry));
    }
  }
  const existing = candidates.filter((candidate) => fs.existsSync(candidate));
  if (!existing.length) return;
  const delimiter = path.delimiter;
  const current = process.env.NODE_PATH ? process.env.NODE_PATH.split(delimiter) : [];
  process.env.NODE_PATH = [...existing, ...current].filter(Boolean).join(delimiter);
  require("module").Module._initPaths();
}

function requirePlaywright() {
  installBundledNodePath();
  try {
    return require("playwright");
  } catch (err) {
    fail(
      "Playwright is required for ui-stability regression browser gestures. " +
        "Run inside Codex bundled runtime or install Playwright for this Node environment. " +
        `Original error: ${err && err.message ? err.message : err}`
    );
  }
}

function seededExercises(count) {
  const names = [
    "Beinpresse",
    "Kniebeuger Maschine",
    "Latziehen",
    "Rudern",
    "Romanian Deadlift",
    "Single Leg to Stand",
    "Kniestrecker Maschine",
    "Abduktion Maschine",
    "Adduktion Maschine",
    "Pallof Press",
  ];
  return Array.from({ length: count }, (_, index) => {
    const id = `p_ui_stability_${String(index + 1).padStart(2, "0")}`;
    return {
      id,
      localId: id,
      name: `${names[index % names.length]} UI ${index + 1}`,
      sets: 3,
      side: "BI",
      unit: "Wdh",
      metricUnit: "Wdh",
      weightUnit: "kg",
      loadUnit: "kg",
      startMetric: "12",
      startLoad: String(10 + index),
      pendingNew: index % 3 === 0,
    };
  });
}

async function assertPageCondition(page, predicate, message) {
  const ok = await page.evaluate(predicate);
  if (!ok) fail(message);
}

async function cardNames(page) {
  return page.locator("#planList .planCard .planName").evaluateAll((nodes) =>
    nodes.map((node) => node.textContent.trim())
  );
}

async function dispatchPointer(page, targetSelector, type, x, y, pointerId = 41) {
  await page.evaluate(
    ({ targetSelector, type, x, y, pointerId }) => {
      const target = targetSelector === "document" ? document : document.querySelector(targetSelector);
      if (!target) throw new Error(`Pointer target missing: ${targetSelector}`);
      const event = new PointerEvent(type, {
        bubbles: true,
        cancelable: true,
        composed: true,
        clientX: x,
        clientY: y,
        pointerId,
        pointerType: "touch",
        isPrimary: true,
        button: 0,
        buttons: type === "pointerup" || type === "pointercancel" ? 0 : 1,
      });
      target.dispatchEvent(event);
    },
    { targetSelector, type, x, y, pointerId }
  );
}

async function elementCenter(locator) {
  const box = await locator.boundingBox();
  if (!box) fail("Element has no visible bounding box.");
  return { x: box.x + box.width / 2, y: box.y + box.height / 2, box };
}

async function browserGestureSuite() {
  const { chromium } = requirePlaywright();
  const htmlUrl = pathToFileURL(HTML_PATH).href;
  const externalRequests = [];
  const popups = [];
  const pageErrors = [];
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2,
      isMobile: true,
      hasTouch: true,
      locale: "de-DE",
      userAgent:
        "Mozilla/5.0 (Linux; Android 14; KGG UI Stability) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/126 Mobile Safari/537.36",
    });
    await context.route(/^https?:\/\//, async (route) => {
      externalRequests.push(route.request().url());
      await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
    });
    await context.addInitScript(({ storageKey, exercises }) => {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          plan: exercises,
          patient: { name: "UI Stabilität", date: "2026-06-25", therapist: "Codex" },
          bankOpen: false,
          recent: [],
          packages: [],
        })
      );
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-25T00:00:00.000Z");
    }, { storageKey: STORAGE_KEY, exercises: seededExercises(30) });

    const page = await context.newPage();
    page.on("popup", (popup) => popups.push(popup.url()));
    page.on("pageerror", (err) => pageErrors.push(err.message));

    await page.goto(htmlUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
    await page.waitForTimeout(700);

    if (page.url() !== htmlUrl) fail(`App navigated away on boot: ${page.url()}`);
    if (popups.length) fail(`App opened popup on boot: ${popups.join(", ")}`);
    if (pageErrors.length) fail(`Page error during boot: ${pageErrors.join(" | ")}`);

    const count = await page.locator("#planList .planCard[data-plan-id]").count();
    if (count !== 30) fail(`Expected 30 seeded plan cards, got ${count}`);

    await assertPageCondition(
      page,
      () => !document.body.classList.contains("kggPlanCardSwiping") && !document.body.classList.contains("kggPlanCardReordering"),
      "Gesture body classes leaked before any gesture."
    );

    await runSwipeGesture(page);
    await runScrollBeforeHoldGuard(page);
    await runDragReorderGesture(page);

    if (page.url() !== htmlUrl) fail(`App navigated away during gesture tests: ${page.url()}`);
    console.log(`Browser UI stability gestures OK (${externalRequests.length} external request(s) blocked, no navigation)`);
  } finally {
    await browser.close();
  }
}

async function runSwipeGesture(page) {
  const card = page.locator("#planList .planCard[data-plan-id]").first();
  await card.scrollIntoViewIfNeeded();
  const { x, y } = await elementCenter(card);
  await dispatchPointer(page, "#planList .planCard[data-plan-id]", "pointerdown", x, y, 51);
  await dispatchPointer(page, "document", "pointermove", x + 70, y + 4, 51);
  await page.waitForTimeout(40);

  const active = await page.evaluate(() => {
    const card = document.querySelector("#planList .planCard[data-plan-id]");
    return {
      body: document.body.classList.contains("kggPlanCardSwiping"),
      card: card && card.classList.contains("swipe-dragging"),
      swipeX: card && card.style.getPropertyValue("--kgg-plan-swipe-x"),
      transform: card && card.style.transform,
      computed: card && getComputedStyle(card).transform,
    };
  });
  if (!active.body || !active.card) fail(`Swipe did not enter active state: ${JSON.stringify(active)}`);
  if (!/70px|6\dpx|7\dpx/.test(String(active.swipeX))) fail(`Swipe X var did not move visibly: ${JSON.stringify(active)}`);
  if (!String(active.transform).includes("translateX")) fail(`Swipe did not set visible translateX: ${JSON.stringify(active)}`);

  await dispatchPointer(page, "document", "pointerup", x + 70, y + 4, 51);
  await page.waitForTimeout(280);
  const cleanup = await page.evaluate(() => {
    const card = document.querySelector("#planList .planCard[data-plan-id]");
    return {
      body: document.body.classList.contains("kggPlanCardSwiping"),
      cardDragging: card && card.classList.contains("swipe-dragging"),
      cardArmed: card && card.classList.contains("swipe-armed"),
      transform: card && card.style.transform,
      swipeX: card && card.style.getPropertyValue("--kgg-plan-swipe-x"),
    };
  });
  if (cleanup.body || cleanup.cardDragging || cleanup.cardArmed || cleanup.transform || cleanup.swipeX) {
    fail(`Swipe cleanup leaked state: ${JSON.stringify(cleanup)}`);
  }
}

async function runScrollBeforeHoldGuard(page) {
  const namesBefore = await cardNames(page);
  const handle = page.locator("#planList .planCard[data-plan-id] .drag").nth(1);
  await handle.scrollIntoViewIfNeeded();
  const { x, y } = await elementCenter(handle);
  await dispatchPointer(page, "#planList .planCard[data-plan-id]:nth-child(2) .drag", "pointerdown", x, y, 61);
  await dispatchPointer(page, "document", "pointermove", x + 1, y + 18, 61);
  await page.waitForTimeout(160);
  await dispatchPointer(page, "document", "pointerup", x + 1, y + 18, 61);
  await page.waitForTimeout(80);

  const namesAfter = await cardNames(page);
  const leaked = await page.evaluate(() => ({
    body: document.body.classList.contains("kggPlanCardReordering"),
    lifted: !!document.querySelector("#planList .planCard.reorder-lifted"),
    placeholder: !!document.querySelector("#planList .reorder-placeholder"),
    listPosition: document.getElementById("planList").style.getPropertyValue("position"),
  }));
  if (JSON.stringify(namesBefore) !== JSON.stringify(namesAfter)) {
    fail("Scroll-before-hold changed plan order.");
  }
  if (leaked.body || leaked.lifted || leaked.placeholder || leaked.listPosition) {
    fail(`Scroll-before-hold leaked drag state: ${JSON.stringify(leaked)}`);
  }
}

async function runDragReorderGesture(page) {
  const namesBefore = await cardNames(page);
  const movingName = namesBefore[1];
  const handle = page.locator("#planList .planCard[data-plan-id] .drag").nth(1);
  const targetCard = page.locator("#planList .planCard[data-plan-id]").nth(4);
  await handle.scrollIntoViewIfNeeded();
  await targetCard.scrollIntoViewIfNeeded();
  const from = await elementCenter(handle);
  const target = await elementCenter(targetCard);

  await dispatchPointer(page, "#planList .planCard[data-plan-id]:nth-child(2) .drag", "pointerdown", from.x, from.y, 71);
  await page.waitForTimeout(135);
  await dispatchPointer(page, "document", "pointermove", target.x, target.y + 20, 71);
  await page.waitForTimeout(80);

  const active = await page.evaluate(() => ({
    body: document.body.classList.contains("kggPlanCardReordering"),
    lifted: !!document.querySelector("#planList .planCard.reorder-lifted"),
    placeholder: !!document.querySelector("#planList .reorder-placeholder"),
    listPosition: document.getElementById("planList").style.getPropertyValue("position"),
  }));
  if (!active.body || !active.lifted || !active.placeholder) {
    fail(`Drag reorder did not enter active state: ${JSON.stringify(active)}`);
  }

  await dispatchPointer(page, "document", "pointerup", target.x, target.y + 20, 71);
  await page.waitForTimeout(220);

  const namesAfter = await cardNames(page);
  const fromIndex = namesBefore.indexOf(movingName);
  const toIndex = namesAfter.indexOf(movingName);
  if (toIndex <= fromIndex) {
    fail(`Drag reorder did not move card down. Before=${JSON.stringify(namesBefore.slice(0, 8))} After=${JSON.stringify(namesAfter.slice(0, 8))}`);
  }
  const cleanup = await page.evaluate(() => ({
    body: document.body.classList.contains("kggPlanCardReordering"),
    lifted: !!document.querySelector("#planList .planCard.reorder-lifted"),
    placeholder: !!document.querySelector("#planList .reorder-placeholder"),
    armed: !!document.querySelector("#planList .drag.reorder-armed"),
    listPosition: document.getElementById("planList").style.getPropertyValue("position"),
  }));
  if (cleanup.body || cleanup.lifted || cleanup.placeholder || cleanup.armed || cleanup.listPosition) {
    fail(`Drag cleanup leaked state: ${JSON.stringify(cleanup)}`);
  }
}

async function main() {
  const args = parseArgs();
  if (args.help) {
    usage();
    return;
  }
  if (!["critical", "regression", "all"].includes(args.level)) {
    fail(`Unknown level: ${args.level}`);
  }
  staticGestureGuardSuite();
  if (args.level === "regression" || args.level === "all" || args.browser) {
    await browserGestureSuite();
  }
  console.log(`KGG UI stability smoke OK (${args.level})`);
}

main().catch((err) => {
  console.error(`ERROR: ${err && err.stack ? err.stack : err}`);
  process.exit(1);
});
