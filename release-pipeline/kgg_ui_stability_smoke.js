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
const HTML_PATH = path.resolve(process.env.KGG_UI_SMOKE_HTML || path.join(ROOT, "kgg-update", "index.html"));
const STORAGE_KEY = "kgg_html_app_v2_state";
const CUSTOM_BANK_KEY = "kgg_html_app_v2_custom_exercise_bank";

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { level: "critical", caseName: "all" };
  for (let i = 0; i < args.length; i += 1) {
    if ((args[i] === "--level" || args[i] === "--suite") && args[i + 1]) {
      out.level = String(args[i + 1]).toLowerCase();
      i += 1;
    } else if ((args[i] === "--case" || args[i] === "--scope") && args[i + 1]) {
      out.caseName = String(args[i + 1]).toLowerCase();
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
  console.log("Usage: node release-pipeline/kgg_ui_stability_smoke.js --level critical|regression [--case all|gestures|ui-mini-series|bank-thumbnails|phone-admin-menu|phone-scan-dock|phone-history-packages|phone-bank-align|tablet-layout-button|tablet-card-reorder|tablet-layout-visual|tablet-split-phone-layout|phone-landscape-tablet-menu|tablet-app-boot] [--browser]");
  console.log("Optional: set KGG_UI_SMOKE_HTML to test a release HTML instead of kgg-update/index.html.");
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

  assertIncludes(html, "kggDeviceSyncOpen", "separate device sync menu entry");
  assertRegex(html, /Ger(?:\u00e4|\u00c3\u00a4|ae)te-Sync/, "device sync menu label");
  assertIncludes(html, "document.getElementById('syncQrBtn')", "device sync opens sync dialog through sync button");
  assertRegex(html, /tabletMenuTherapistShareBtn[\s\S]{0,260}openKggTherapistAppOnlyQr\(\)/, "therapist share opens app QR directly");
  assertIncludes(html, "Kolleg:innen-App APK QR", "colleague APK share QR label");
  assertIncludes(html, "kgg-v051-android-qr-pdf-bridge", "v051 Android QR/PDF bridge marker");
  assertIncludes(html, 'id="kggAdminMenuQrPrint"', "admin QR print button");
  assertIncludes(html, "function buildKggAdminMenuQrPrintPdf", "admin QR print PDF builder");
  assertIncludes(html, "function printKggAdminMenuQr", "admin QR print handler");
  assertIncludes(html, "window.KGG_ANDROID_QR_PDF_BRIDGE_V051", "v051 public probe");
  assertIncludes(html, "kgg-v052-pdf-plan-thumbnails", "v052 PDF thumbnail marker");
  assertIncludes(html, "function attachKggPdfExerciseThumbnails", "PDF thumbnail snapshot helper");
  assertIncludes(html, "function createKggPdfThumbnailDataUrl", "PDF thumbnail data URL helper");
  assertIncludes(html, "KGGOfflineJsPDF.prototype.addImage", "offline PDF image embedding");
  assertIncludes(html, "doc.addImage(thumb.dataUrl,'JPEG'", "PDF card draws JPEG thumbnail");
  assertIncludes(html, "target.grid==='1x3'", "large-print PDF thumbnail skip guard");
  assertIncludes(html, "window.KGG_PDF_PLAN_THUMBNAILS_V052", "v052 public probe");

  console.log("Static UI stability guards OK");
}

function caseMatches(caseName, names) {
  const normalized = String(caseName || "all").toLowerCase();
  return normalized === "all" || names.includes(normalized);
}

function staticUiMiniSeriesGuardSuite(caseName) {
  const html = readHtml();

  if (caseMatches(caseName, ["ui-mini-series", "bank-thumbnails"])) {
    assertIncludes(html, "kgg-v041-ui-mini-series", "v041 UI mini-series marker");
    assertIncludes(html, "function bankCardThumbnailHtml", "exercise-bank thumbnail helper");
    assertIncludes(html, "function hydrateBankThumbnails", "exercise-bank thumbnail hydration");
    assertIncludes(html, "data-bank-thumb-id", "exercise-bank thumbnail data attribute");
    assertIncludes(html, "bankCardThumbnailHtml(ex)", "thumbnail rendered inside bank rows");
    assertIncludes(html, "hydrateBankThumbnails(c)", "bank thumbnail hydration call");
    assertIncludes(html, "filter:grayscale(1)", "black-and-white bank thumbnail styling");
  }

  if (caseMatches(caseName, ["ui-mini-series", "tablet-layout-button"])) {
    assertRegex(
      html,
      /function setTabletLayoutEditMode\(open\)[\s\S]{0,460}panel\.hidden=!next/,
      "tablet layout button reveals layout panel"
    );
    assertRegex(
      html,
      /function setTabletSideMenuOpen\(open\)[\s\S]{0,1250}setTabletLayoutEditMode\(false\)/,
      "tablet side menu closes layout edit mode"
    );
  }

  if (caseMatches(caseName, ["ui-mini-series", "tablet-card-reorder"])) {
    assertIncludes(html, "kgg-v043-tablet-card-reorder", "v043 tablet card reorder marker");
    assertIncludes(html, "tabletCardReorderBound", "tablet card reorder binding guard");
    assertRegex(
      html,
      /if\(!isTabletLayout\(\)\)return;[\s\S]{0,260}startAnimatedReorderPress\(ev\)/,
      "card-surface reorder starts only in tablet layout"
    );
    assertIncludes(
      html,
      "target.closest('button,input,textarea,select,a,.planCardActions,.drag')",
      "tablet card reorder ignores interactive card controls"
    );
    assertIncludes(html, "const eventTarget=ev.currentTarget", "reorder press resolves card or handle target");
    assertIncludes(
      html,
      "cardFromTarget?cardFromTarget.querySelector('.drag[data-sort-id]'):null",
      "card-surface reorder resolves the existing drag handle"
    );
  }

  if (caseMatches(caseName, ["ui-mini-series", "phone-admin-menu"])) {
    assertIncludes(html, "kggPhoneAdminMenu", "phone admin submenu");
    assertIncludes(html, "kgg-v042-phone-dock-anchored-correction", "v042 anchored phone dock correction");
    assertIncludes(html, "kgg-v044-phone-liquid-actions", "v044 phone liquid actions marker");
    assertIncludes(html, "kgg-v050-phone-ui-mini-fix", "v050 phone mini-fix marker");
    assertIncludes(html, "KGG_UI_PHONE_MINI_FIX_V050", "v050 phone mini-fix public probe");
    assertIncludes(html, "header.appendChild(menu)", "phone admin menu anchored in plan header");
    assertIncludes(html, "top:8px!important", "phone plan admin menu top anchor");
    assertIncludes(html, "right:88px!important", "phone plan admin menu right anchor");
    assertIncludes(html, "kggPhoneUpdateCenterMenu", "phone update center submenu entry");
    assertIncludes(html, "kggPhoneDeviceSyncMenu", "phone device sync submenu entry");
    assertIncludes(html, "kggPhoneTherapistShareMenu", "phone colleague app share submenu entry");
    assertIncludes(html, "kggPhoneAdminConfigMenu", "phone admin config submenu entry");
    assertIncludes(html, "kggPhoneBankShareMenu", "phone exercise-bank share submenu entry");
    assertIncludes(html, "data-kgg-phone-menu-group=\"update\"", "phone admin menu update group");
    assertIncludes(html, "data-kgg-phone-menu-group=\"sync-share\"", "phone admin menu sync/share group");
    assertIncludes(html, "data-kgg-phone-menu-group=\"admin\"", "phone admin menu admin group");
    assertRegex(
      html,
      /#scanHub #syncQrBtn,[\s\S]{0,160}#scanHub #adminConfigBtn,[\s\S]{0,160}#scanHub #sharedBankBtn[\s\S]{0,120}display:none!important/,
      "phone direct admin/QR scanHub buttons are hidden"
    );
  }

  if (caseMatches(caseName, ["ui-mini-series", "phone-scan-dock"])) {
    assertIncludes(html, "phonePhotoMenuToggle", "phone photo dropdown toggle");
    assertIncludes(html, "kggScanButtonWithMenu", "phone photo toggle integrated into scan button");
    assertIncludes(html, "kggPhoneLiquidAction", "phone liquid action class");
    assertIncludes(html, "kggPhoneLiquidChevron", "phone liquid chevron class");
    assertIncludes(html, "phoneScanLabel", "phone scan label");
    assertIncludes(html, "body.kggPhoneDrawerOpen #scanHub", "phone dock stays behind drawer");
    assertIncludes(html, "kggPhonePhotoMenu", "phone photo menu");
    assertIncludes(html, "window.KGGScan.pick(\"file\")", "phone gallery picker route");
    assertIncludes(html, "kggPhoneHasPlan", "phone plan-state dock class");
    assertIncludes(html, "backdrop-filter:blur(30px)", "strong liquid glass dock style");
    assertIncludes(html, "kggPhoneScanMenuInline", "v050 inline scan photo menu mode");
    assertIncludes(html, "body.kggPhonePhotoMenuOpen #scanHub.kggPhoneScanMenuInline", "v050 scan button grows vertically when photo menu opens");
    assertIncludes(html, "#scanHub.kggPhoneScanMenuInline #kggPhonePhotoMenu", "v050 photo menu lives inside scan hub");
    assertIncludes(html, "content:none!important", "v050 scan chevron divider is removed");
    assertIncludes(html, ".planActions.hasPlan #recentToggle", "phone recent toggle non-collapse override");
    assertIncludes(html, "min-width:148px", "phone recent toggle stays readable");
    assertRegex(html, /#scanHub[\s\S]{0,420}position:fixed!important/, "phone scanHub fixed bottom dock");
    assertRegex(html, /#finishBtn:not\(\.hidden\)[\s\S]{0,300}position:fixed!important/, "phone finish button joins dock");
  }

  if (caseMatches(caseName, ["ui-mini-series", "phone-history-packages", "phone-bank-align"])) {
    assertIncludes(html, "kgg-v045-phone-drawer-bank-align", "v045 phone drawer/bank alignment marker");
    assertIncludes(html, "KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045", "v045 phone drawer/bank public probe");
  }
  if (caseMatches(caseName, ["ui-mini-series", "tablet-layout-visual", "tablet-split-phone-layout", "tablet-app-boot"])) {
    assertIncludes(html, "kgg-v046-tablet-runtime-viewport-guard", "v046 tablet runtime viewport guard marker");
    assertIncludes(html, "KGG_TABLET_RUNTIME_VIEWPORT_GUARD_V046", "v046 tablet runtime viewport guard public probe");
    assertIncludes(html, "restoreTabletScanButton", "v046 restores scan button when leaving phone viewport");
    assertIncludes(html, "if(!isPhone()){", "v046 phone runtime patches are viewport-gated");
  }
  if (caseMatches(caseName, ["ui-mini-series", "phone-landscape-tablet-menu"])) {
    assertIncludes(html, "kgg-v047-phone-landscape-tablet-menu", "v047 phone landscape tablet menu marker");
    assertIncludes(html, "KGG_LANDSCAPE_TABLET_VIEWPORT_V047", "v047 phone landscape viewport public probe");
    assertIncludes(html, "width=760, initial-scale=1, viewport-fit=cover", "v047 forced tablet viewport");
    assertIncludes(html, "function isLandscapeTabletViewport", "v047 central landscape tablet mode helper");
  }
  if (caseMatches(caseName, ["ui-mini-series", "phone-history-packages"])) {
    assertIncludes(html, "openPhoneDrawerSafe", "phone history/packages safe drawer handler");
    assertIncludes(html, "bindDrawerButton(\"recentToggle\",\"recent\")", "phone recent safe drawer binding");
    assertIncludes(html, "bindDrawerButton(\"packageToggle\",\"package\")", "phone package safe drawer binding");
  }
  if (caseMatches(caseName, ["ui-mini-series", "phone-bank-align"])) {
    assertIncludes(html, "alignBankEndToScanDock", "phone exercise-bank scan-dock alignment");
    assertIncludes(html, "margin-top:clamp(28px,5dvh,44px)", "phone create panel top breathing room");
  }

  console.log(`Static UI mini-series guards OK (${caseName || "all"})`);
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

function seededCustomBank() {
  return [
    {
      id: "bank_thumb_probe",
      name: "Bank Bild Probe",
      aliases: "bank bild probe",
      custom: true,
      unit: "Wdh",
      weightUnit: "kg",
      media: [
        {
          id: "media_probe_missing",
          type: "image",
          mime: "image/jpeg",
          name: "probe.jpg",
        },
      ],
    },
  ];
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
    await context.addInitScript(({ storageKey, customBankKey, exercises, customBank }) => {
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
      localStorage.setItem(customBankKey, JSON.stringify(customBank));
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-25T00:00:00.000Z");
    }, { storageKey: STORAGE_KEY, customBankKey: CUSTOM_BANK_KEY, exercises: seededExercises(30), customBank: seededCustomBank() });

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

function wantsPhoneMiniSeries(caseName) {
  return caseMatches(caseName, ["ui-mini-series", "bank-thumbnails", "phone-admin-menu", "phone-scan-dock", "phone-history-packages", "phone-bank-align"]);
}

function wantsTabletMiniSeries(caseName) {
  return caseMatches(caseName, ["tablet-layout-visual"]);
}

function wantsTabletSplitPhoneMiniSeries(caseName) {
  return caseMatches(caseName, ["tablet-split-phone-layout"]);
}

function wantsPhoneLandscapeTabletMenu(caseName) {
  return caseMatches(caseName, ["phone-landscape-tablet-menu"]);
}

async function browserUiMiniSeriesSuite(caseName) {
  if (!wantsPhoneMiniSeries(caseName) && !wantsTabletMiniSeries(caseName) && !wantsTabletSplitPhoneMiniSeries(caseName) && !wantsPhoneLandscapeTabletMenu(caseName)) {
    console.log(`Browser UI mini-series skipped (${caseName || "all"}; static guard only)`);
    return;
  }
  const { chromium } = requirePlaywright();
  const htmlUrl = pathToFileURL(HTML_PATH).href;
  const externalRequests = [];
  const pageErrors = [];
  const browser = await chromium.launch({ headless: true });
  try {
    if (wantsPhoneMiniSeries(caseName)) {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        locale: "de-DE",
        userAgent:
          "Mozilla/5.0 (Linux; Android 14; KGG UI Mini Series) AppleWebKit/537.36 " +
          "(KHTML, like Gecko) Chrome/126 Mobile Safari/537.36",
      });
      await context.route(/^https?:\/\//, async (route) => {
        externalRequests.push(route.request().url());
        await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
      });
      await context.addInitScript(({ storageKey, customBankKey, exercises, customBank }) => {
        localStorage.setItem(
          storageKey,
          JSON.stringify({
            plan: exercises,
            patient: { name: "UI Mini", date: "2026-06-26", therapist: "Codex" },
            bankOpen: true,
            recent: [
              {
                id: "ui_recent_probe",
                name: "UI Probe Plan",
                date: "2026-06-26",
                exercises: exercises.slice(0, 2),
              },
            ],
            packages: [
              {
                id: "ui_package_probe",
                name: "UI Probe Paket",
                exercises: ["Beinpresse UI 1", "Latziehen UI 3"],
                source: "ui-smoke",
              },
            ],
          })
        );
        localStorage.setItem(customBankKey, JSON.stringify(customBank));
        localStorage.setItem(
          "kgg_admin_local_secrets_v1",
          JSON.stringify({ version: 2, updatedAt: "2026-06-26T00:00:00.000Z", geminiKeys: ["test-key"], mediaDropzoneEndpoint: "", mediaDropzoneUploadToken: "" })
        );
        localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-26T00:00:00.000Z");
      }, { storageKey: STORAGE_KEY, customBankKey: CUSTOM_BANK_KEY, exercises: seededExercises(3), customBank: seededCustomBank() });

      const page = await context.newPage();
      page.on("pageerror", (err) => pageErrors.push(err.message));
      await page.goto(htmlUrl, { waitUntil: "commit", timeout: 60000 });
      await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_UI_MINI_SERIES && window.KGG_UI_MINI_SERIES.check, null, { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_UI_MINI_SERIES_V042 && window.KGG_UI_MINI_SERIES_V042.check, null, { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_UI_PHONE_LIQUID_ACTIONS_V044, null, { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045, null, { timeout: 15000 });
      await page.waitForTimeout(500);

      if (caseMatches(caseName, ["ui-mini-series", "bank-thumbnails"])) {
        await page.waitForSelector('[data-bank-thumb-id="media_probe_missing"]', { timeout: 10000 });
        const thumb = await page.evaluate(() => {
          const node = document.querySelector('[data-bank-thumb-id="media_probe_missing"]');
          return {
            exists: !!node,
            fallback: !!(node && node.classList.contains("bankThumbFallback")),
            width: node ? Math.round(node.getBoundingClientRect().width) : 0,
            height: node ? Math.round(node.getBoundingClientRect().height) : 0,
          };
        });
        if (!thumb.exists || !thumb.fallback || thumb.width < 30 || thumb.height < 30) {
          fail(`Bank thumbnail probe failed: ${JSON.stringify(thumb)}`);
        }
      }

      if (caseMatches(caseName, ["ui-mini-series", "phone-admin-menu"])) {
        await page.waitForSelector("#kggPhoneAdminMenu", { timeout: 10000 });
        await page.waitForFunction(() => document.body.classList.contains("adminMode"), null, { timeout: 10000 });
        const hidden = await page.evaluate(() => {
          const ids = ["syncQrBtn", "adminConfigBtn", "sharedBankBtn"];
          return Object.fromEntries(ids.map((id) => {
            const el = document.getElementById(id);
            return [id, el ? getComputedStyle(el).display : "missing"];
          }));
        });
        if (hidden.syncQrBtn !== "none" || hidden.adminConfigBtn !== "none" || hidden.sharedBankBtn !== "none") {
          fail(`Phone admin/QR buttons still visible in scanHub: ${JSON.stringify(hidden)}`);
        }
        await page.locator("#kggPhoneAdminMenuBtn").click();
        const menu = await page.evaluate(() => ({
          panelOpen: !document.getElementById("kggPhoneAdminMenuPanel").hidden,
          update: !!document.getElementById("kggPhoneUpdateCenterMenu"),
          sync: !!document.getElementById("kggPhoneDeviceSyncMenu"),
          therapist: !!document.getElementById("kggPhoneTherapistShareMenu"),
          admin: !!document.getElementById("kggPhoneAdminConfigMenu"),
          bank: !!document.getElementById("kggPhoneBankShareMenu"),
          oldQr: !!document.getElementById("kggPhoneQrShareMenu"),
          groups: Array.from(document.querySelectorAll("#kggPhoneAdminMenuPanel [data-kgg-phone-menu-group]")).map((node) => node.getAttribute("data-kgg-phone-menu-group")),
          anchored: !!document.querySelector("#createPanel .planHeader #kggPhoneAdminMenu"),
          position: getComputedStyle(document.getElementById("kggPhoneAdminMenu")).position,
          planHeader: (() => {
            const header = document.querySelector("#createPanel .planHeader");
            const menuNode = document.getElementById("kggPhoneAdminMenu");
            const add = document.getElementById("planAddPackageBtn");
            const rect = (node) => {
              if (!node) return null;
              const r = node.getBoundingClientRect();
              return { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), width: Math.round(r.width) };
            };
            return {
              header: rect(header),
              menu: rect(menuNode),
              add: rect(add),
              rightCss: menuNode ? getComputedStyle(menuNode).right : "",
              transform: menuNode ? getComputedStyle(menuNode).transform : "",
            };
          })(),
        }));
        const menuRect = menu.planHeader.menu || {};
        const headerRect = menu.planHeader.header || {};
        const addRect = menu.planHeader.add || {};
        const menuRightAnchored = menuRect.left > (headerRect.left || 0) + ((headerRect.width || 0) * 0.45);
        const menuBeforeAddButton = !addRect.left || menuRect.right <= addRect.left + 10;
        if (
          !menu.panelOpen ||
          !menu.update ||
          !menu.sync ||
          !menu.therapist ||
          !menu.admin ||
          !menu.bank ||
          menu.oldQr ||
          !menu.groups.includes("update") ||
          !menu.groups.includes("sync-share") ||
          !menu.groups.includes("admin") ||
          !menu.anchored ||
          menu.position === "fixed" ||
          menu.planHeader.rightCss !== "88px" ||
          menu.planHeader.transform !== "none" ||
          !menuRightAnchored ||
          !menuBeforeAddButton
        ) {
          fail(`Phone admin submenu failed: ${JSON.stringify(menu)}`);
        }
      }

      if (caseMatches(caseName, ["ui-mini-series", "phone-scan-dock"])) {
        await page.waitForSelector("#phonePhotoMenuToggle", { timeout: 10000 });
        const dock = await page.evaluate(() => {
          const hub = document.querySelector(".scanHub");
          const finish = document.getElementById("finishBtn");
          const scan = document.getElementById("scanBtn");
          const toggle = document.getElementById("phonePhotoMenuToggle");
          const recent = document.getElementById("recentToggle");
          const recentText = recent ? recent.querySelector(".recentText") : null;
          return {
            bodyHasPlan: document.body.classList.contains("kggPhoneHasPlan"),
            hubPosition: hub ? getComputedStyle(hub).position : "missing",
            hubZ: hub ? Number.parseInt(getComputedStyle(hub).zIndex, 10) : -1,
            scanHeight: scan ? Math.round(scan.getBoundingClientRect().height) : 0,
            scanBackdrop: scan ? (getComputedStyle(scan).backdropFilter || getComputedStyle(scan).webkitBackdropFilter || "none") : "missing",
            scanLabel: scan ? (scan.querySelector(".phoneScanLabel") || {}).textContent || "" : "",
            scanLiquid: !!(scan && scan.classList.contains("kggPhoneLiquidAction")),
            toggleText: toggle ? toggle.textContent : "",
            toggleInsideScan: !!(toggle && scan && toggle.parentElement === scan),
            toggleLiquid: !!(toggle && toggle.classList.contains("kggPhoneLiquidChevron")),
            finishPosition: finish ? getComputedStyle(finish).position : "missing",
            finishHidden: finish ? finish.classList.contains("hidden") : true,
            finishWidth: finish ? Math.round(finish.getBoundingClientRect().width) : 0,
            finishZ: finish ? Number.parseInt(getComputedStyle(finish).zIndex, 10) : -1,
            finishBackdrop: finish ? (getComputedStyle(finish).backdropFilter || getComputedStyle(finish).webkitBackdropFilter || "none") : "missing",
            finishLiquid: !!(finish && finish.classList.contains("kggPhoneLiquidAction")),
            recentWidth: recent ? Math.round(recent.getBoundingClientRect().width) : 0,
            recentTextOpacity: recentText ? Number.parseFloat(getComputedStyle(recentText).opacity) : 0,
            recentTextWidth: recentText ? Math.round(recentText.getBoundingClientRect().width) : 0,
            recentText: recent ? recent.textContent : "",
            packageWidth: document.getElementById("packageToggle") ? Math.round(document.getElementById("packageToggle").getBoundingClientRect().width) : 0,
          };
        });
        if (
          !dock.bodyHasPlan ||
          dock.hubPosition !== "fixed" ||
          dock.hubZ >= 90 ||
          dock.scanHeight < 50 ||
          !dock.scanLiquid ||
          !dock.scanLabel.includes("Plan scannen") ||
          !dock.toggleInsideScan ||
          !dock.toggleLiquid ||
          !/^(?:\u2303|âŒƒ|\^)$/.test(dock.toggleText.trim()) ||
          String(dock.scanBackdrop).toLowerCase() === "none" ||
          dock.finishPosition !== "fixed" ||
          dock.finishHidden ||
          dock.finishWidth < 90 ||
          dock.finishZ >= 90 ||
          !dock.finishLiquid ||
          String(dock.finishBackdrop).toLowerCase() === "none" ||
          dock.recentWidth < 250 ||
          (dock.packageWidth && dock.recentWidth < dock.packageWidth * 0.88) ||
          dock.recentTextOpacity < 0.9 ||
          dock.recentTextWidth < 60 ||
          !dock.recentText.includes("Plan-His")
        ) {
          fail(`Phone scan dock failed: ${JSON.stringify(dock)}`);
        }
        const closedScan = await page.evaluate(() => {
          const hub = document.querySelector(".scanHub");
          const scan = document.getElementById("scanBtn");
          const menu = document.getElementById("kggPhonePhotoMenu");
          const toggle = document.getElementById("phonePhotoMenuToggle");
          const before = toggle ? getComputedStyle(toggle, "::before") : null;
          const rect = (node) => {
            if (!node) return null;
            const r = node.getBoundingClientRect();
            return { width: Math.round(r.width), height: Math.round(r.height), top: Math.round(r.top), bottom: Math.round(r.bottom) };
          };
          return {
            hub: rect(hub),
            scan: rect(scan),
            menuParent: menu && menu.parentElement ? menu.parentElement.id : "",
            menuPosition: menu ? getComputedStyle(menu).position : "missing",
            menuDisplay: menu ? getComputedStyle(menu).display : "missing",
            dividerDisplay: before ? before.display : "missing",
            dividerContent: before ? before.content : "missing",
          };
        });
        await page.evaluate(() => {
          document.getElementById("phonePhotoMenuToggle").dispatchEvent(
            new MouseEvent("click", { bubbles: true, cancelable: true, composed: true })
          );
        });
        const photoMenu = await page.evaluate(() => ({
          open: document.body.classList.contains("kggPhonePhotoMenuOpen"),
          gallery: !!document.getElementById("phonePhotoGallery"),
          camera: !!document.getElementById("phonePhotoCamera"),
          display: getComputedStyle(document.getElementById("kggPhonePhotoMenu")).display,
          parent: document.getElementById("kggPhonePhotoMenu").parentElement.id,
          position: getComputedStyle(document.getElementById("kggPhonePhotoMenu")).position,
          hub: (() => {
            const r = document.querySelector(".scanHub").getBoundingClientRect();
            return { width: Math.round(r.width), height: Math.round(r.height), top: Math.round(r.top), bottom: Math.round(r.bottom) };
          })(),
          scan: (() => {
            const r = document.getElementById("scanBtn").getBoundingClientRect();
            return { width: Math.round(r.width), height: Math.round(r.height), top: Math.round(r.top), bottom: Math.round(r.bottom) };
          })(),
        }));
        if (
          !photoMenu.open ||
          !photoMenu.gallery ||
          !photoMenu.camera ||
          photoMenu.display === "none" ||
          photoMenu.parent !== "scanHub" ||
          photoMenu.position === "fixed" ||
          closedScan.menuParent !== "scanHub" ||
          closedScan.menuPosition === "fixed" ||
          closedScan.dividerDisplay !== "none" ||
          Math.abs(photoMenu.hub.width - closedScan.hub.width) > 4 ||
          photoMenu.hub.height < closedScan.hub.height + 55 ||
          Math.abs(photoMenu.scan.width - closedScan.scan.width) > 4
        ) {
          fail(`Phone inline photo menu failed: ${JSON.stringify({ closedScan, photoMenu })}`);
        }
        const modalLayering = await page.evaluate(() => {
          const hub = document.querySelector(".scanHub");
          const finish = document.getElementById("finishBtn");
          const photoMenu = document.getElementById("kggPhonePhotoMenu");
          const modal = document.getElementById("syncPairModal");
          modal.classList.add("open");
          const z = (el) => Number.parseInt(getComputedStyle(el).zIndex, 10) || 0;
          return {
            hubZ: z(hub),
            finishZ: z(finish),
            photoMenuZ: z(photoMenu),
            modalZ: z(modal),
          };
        });
        if (
          modalLayering.modalZ <= modalLayering.hubZ ||
          modalLayering.modalZ <= modalLayering.finishZ
        ) {
          fail(`Phone modal layer order failed: ${JSON.stringify(modalLayering)}`);
        }
      }

      if (caseMatches(caseName, ["ui-mini-series", "phone-history-packages"])) {
        const beforeErrors = pageErrors.length;
        await page.evaluate(() => {
          document.querySelectorAll(".modal.open").forEach((modal) => modal.classList.remove("open"));
          if (window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045 && window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045.closeDrawer) {
            window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045.closeDrawer();
          }
        });
        await page.locator("#recentToggle").click({ timeout: 7000 });
        await page.waitForFunction(() => !document.getElementById("recentList").classList.contains("hidden"), null, { timeout: 7000 });
        const recentOpen = await page.evaluate(() => ({
          bodyOpen: document.body.classList.contains("kggPhoneDrawerSafeOpen"),
          text: document.getElementById("recentList").textContent,
          buttonFloat: document.getElementById("recentToggle").classList.contains("phoneButtonFloat"),
        }));
        if (!recentOpen.bodyOpen || !recentOpen.buttonFloat || !recentOpen.text.includes("UI Probe Plan")) {
          fail(`Phone recent drawer failed to open: ${JSON.stringify(recentOpen)}`);
        }
        await page.locator("#recentToggle").click({ timeout: 7000 });
        await page.waitForFunction(() => document.getElementById("recentList").classList.contains("hidden"), null, { timeout: 7000 });
        await page.locator("#packageToggle").click({ timeout: 7000 });
        await page.waitForFunction(() => !document.getElementById("packageList").classList.contains("hidden"), null, { timeout: 7000 });
        const packageOpen = await page.evaluate(() => ({
          bodyOpen: document.body.classList.contains("kggPhoneDrawerSafeOpen"),
          text: document.getElementById("packageList").textContent,
          buttonFloat: document.getElementById("packageToggle").classList.contains("phoneButtonFloat"),
        }));
        if (!packageOpen.bodyOpen || !packageOpen.buttonFloat || !packageOpen.text.includes("UI Probe Paket")) {
          fail(`Phone package drawer failed to open: ${JSON.stringify(packageOpen)}`);
        }
        await page.locator("#packageToggle").click({ timeout: 7000 });
        await page.waitForFunction(() => document.getElementById("packageList").classList.contains("hidden"), null, { timeout: 7000 });
        if (pageErrors.length !== beforeErrors) {
          fail(`Phone history/packages drawer produced page errors: ${pageErrors.slice(beforeErrors).join(" | ")}`);
        }
      }

      if (caseMatches(caseName, ["ui-mini-series", "phone-bank-align"])) {
        const beforeErrors = pageErrors.length;
        await page.evaluate(() => {
          document.querySelectorAll(".modal.open").forEach((modal) => modal.classList.remove("open"));
          if (window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045 && window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045.closeDrawer) {
            window.KGG_UI_PHONE_DRAWER_BANK_ALIGN_V045.closeDrawer();
          }
          window.scrollTo(0, 0);
        });
        const initiallyOpen = await page.evaluate(() => document.getElementById("bankArea").classList.contains("bankOpen"));
        if (initiallyOpen) {
          await page.locator("#bankToggle").click({ timeout: 7000 });
          await page.waitForFunction(() => !document.getElementById("bankArea").classList.contains("bankOpen"), null, { timeout: 7000 });
        }
        await page.locator("#bankToggle").click({ timeout: 7000 });
        await page.waitForFunction(() => document.getElementById("bankArea").classList.contains("bankOpen"), null, { timeout: 7000 });
        await page.waitForTimeout(900);
        const align = await page.evaluate(() => {
          const bank = document.getElementById("bankArea");
          const hub = document.querySelector(".scanHub");
          const create = document.getElementById("createPanel");
          const bankRect = bank.getBoundingClientRect();
          const hubRect = hub.getBoundingClientRect();
          return {
            bankOpen: bank.classList.contains("bankOpen"),
            bankBottom: Math.round(bankRect.bottom),
            hubTop: Math.round(hubRect.top),
            gap: Math.round(hubRect.top - bankRect.bottom),
            createMarginTop: Math.round(Number.parseFloat(getComputedStyle(create).marginTop) || 0),
            hubPosition: getComputedStyle(hub).position,
          };
        });
        if (
          !align.bankOpen ||
          align.hubPosition !== "fixed" ||
          align.createMarginTop < 28 ||
          align.gap < 0 ||
          align.gap > 22
        ) {
          fail(`Phone bank alignment failed: ${JSON.stringify(align)}`);
        }
        if (pageErrors.length !== beforeErrors) {
          fail(`Phone bank alignment produced page errors: ${pageErrors.slice(beforeErrors).join(" | ")}`);
        }
      }

      await context.close();
    }

    if (wantsPhoneLandscapeTabletMenu(caseName)) {
      const context = await browser.newContext({
        viewport: { width: 720, height: 390 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        locale: "de-DE",
        userAgent:
          "Mozilla/5.0 (Linux; Android 14; Phone Landscape) AppleWebKit/537.36 " +
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
            patient: { name: "Phone Landscape", date: "2026-06-30", therapist: "Codex" },
            bankOpen: false,
          })
        );
        localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-30T00:00:00.000Z");
      }, { storageKey: STORAGE_KEY, exercises: seededExercises(4) });
      const page = await context.newPage();
      page.on("pageerror", (err) => pageErrors.push(err.message));
      await page.goto(htmlUrl, { waitUntil: "commit", timeout: 60000 });
      await page.waitForSelector("#tabletMenuBtn", { timeout: 15000 });
      await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047 && window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive(), null, { timeout: 15000 });
      await page.waitForTimeout(500);
      const landscape = await page.evaluate(() => {
        const menu = document.getElementById("tabletMenuBtn");
        const hub = document.querySelector(".scanHub");
        const scan = document.getElementById("scanBtn");
        const toggle = document.getElementById("phonePhotoMenuToggle");
        const rect = (el) => {
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return { width: Math.round(r.width), height: Math.round(r.height), display: getComputedStyle(el).display, position: getComputedStyle(el).position };
        };
        return {
          width: window.innerWidth,
          height: window.innerHeight,
          phoneMedia: window.matchMedia("(max-width:759px)").matches,
          tabletMedia: window.matchMedia("(min-width:760px)").matches,
          landscapeActive: !!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047 && window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive()),
          bodyTablet: document.body.classList.contains("tabletLayoutCustom"),
          menu: rect(menu),
          hub: rect(hub),
          scanHydrated: !!(scan && scan.dataset.kggV042ScanHydrated === "1"),
          phoneToggleInsideScan: !!(toggle && scan && toggle.parentElement === scan),
          visual: window.visualViewport ? { width: Math.round(window.visualViewport.width), height: Math.round(window.visualViewport.height), scale: window.visualViewport.scale } : null,
        };
      });
      if (
        !landscape.landscapeActive ||
        !landscape.tabletMedia ||
        landscape.phoneMedia ||
        !landscape.bodyTablet ||
        !landscape.menu ||
        landscape.menu.display === "none" ||
        landscape.menu.width < 34 ||
        !landscape.hub ||
        landscape.hub.position === "fixed" ||
        landscape.scanHydrated ||
        landscape.phoneToggleInsideScan
      ) {
        fail(`Phone landscape tablet menu failed: ${JSON.stringify(landscape)}`);
      }
      await context.close();
    }

    if (wantsTabletSplitPhoneMiniSeries(caseName)) {
      const context = await browser.newContext({
        viewport: { width: 650, height: 844 },
        deviceScaleFactor: 1.5,
        isMobile: false,
        hasTouch: true,
        locale: "de-DE",
        userAgent:
          "Mozilla/5.0 (Linux; Android 14; Tablet Split Screen) AppleWebKit/537.36 " +
          "(KHTML, like Gecko) Chrome/126 Safari/537.36",
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
            patient: { name: "Tablet Split", date: "2026-06-29", therapist: "Codex" },
            bankOpen: false,
          })
        );
        localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-29T00:00:00.000Z");
      }, { storageKey: STORAGE_KEY, exercises: seededExercises(3) });
      const page = await context.newPage();
      page.on("pageerror", (err) => pageErrors.push(err.message));
      await page.goto(htmlUrl, { waitUntil: "commit", timeout: 60000 });
      await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
      await page.waitForFunction(() => window.KGG_UI_MINI_SERIES && window.KGG_UI_MINI_SERIES_V042 && window.KGG_TABLET_RUNTIME_VIEWPORT_GUARD_V046, null, { timeout: 15000 });
      await page.waitForSelector("#phonePhotoMenuToggle", { timeout: 10000 });
      const splitPhone = await page.evaluate(() => {
        const hub = document.querySelector(".scanHub");
        const scan = document.getElementById("scanBtn");
        const toggle = document.getElementById("phonePhotoMenuToggle");
        return {
          width: window.innerWidth,
          phoneMedia: window.matchMedia("(max-width:759px)").matches,
          hubPosition: hub ? getComputedStyle(hub).position : "missing",
          phoneHasPlan: document.body.classList.contains("kggPhoneHasPlan"),
          scanHydrated: !!(scan && scan.dataset.kggV042ScanHydrated === "1"),
          toggleInsideScan: !!(toggle && scan && toggle.parentElement === scan),
          scanLabel: scan ? (scan.querySelector(".phoneScanLabel") || {}).textContent || "" : "",
        };
      });
      if (
        splitPhone.width >= 760 ||
        !splitPhone.phoneMedia ||
        splitPhone.hubPosition !== "fixed" ||
        !splitPhone.phoneHasPlan ||
        !splitPhone.scanHydrated ||
        !splitPhone.toggleInsideScan ||
        !splitPhone.scanLabel.includes("Plan scannen")
      ) {
        fail(`Tablet split-screen phone layout failed: ${JSON.stringify(splitPhone)}`);
      }

      await page.setViewportSize({ width: 1024, height: 768 });
      await page.waitForTimeout(350);
      const wideTablet = await page.evaluate(() => {
        const hub = document.querySelector(".scanHub");
        const scan = document.getElementById("scanBtn");
        const toggle = document.getElementById("phonePhotoMenuToggle");
        return {
          width: window.innerWidth,
          phoneMedia: window.matchMedia("(max-width:759px)").matches,
          hubPosition: hub ? getComputedStyle(hub).position : "missing",
          phoneClasses: ["kggPhoneHasPlan", "kggPhonePhotoMenuOpen"].filter((name) => document.body.classList.contains(name)),
          scanHydrated: !!(scan && scan.dataset.kggV042ScanHydrated === "1"),
          toggleInsideScan: !!(toggle && scan && toggle.parentElement === scan),
          scanText: scan ? scan.textContent.trim() : "",
        };
      });
      if (
        wideTablet.width < 760 ||
        wideTablet.phoneMedia ||
        wideTablet.hubPosition === "fixed" ||
        wideTablet.phoneClasses.length ||
        wideTablet.scanHydrated ||
        wideTablet.toggleInsideScan ||
        !wideTablet.scanText.includes("Plan scannen")
      ) {
        fail(`Tablet split-screen cleanup failed after widening: ${JSON.stringify(wideTablet)}`);
      }

      await page.setViewportSize({ width: 650, height: 844 });
      await page.waitForTimeout(450);
      const backToSplit = await page.evaluate(() => {
        const scan = document.getElementById("scanBtn");
        const toggle = document.getElementById("phonePhotoMenuToggle");
        return {
          phoneMedia: window.matchMedia("(max-width:759px)").matches,
          scanHydrated: !!(scan && scan.dataset.kggV042ScanHydrated === "1"),
          toggleInsideScan: !!(toggle && scan && toggle.parentElement === scan),
        };
      });
      if (!backToSplit.phoneMedia || !backToSplit.scanHydrated || !backToSplit.toggleInsideScan) {
        fail(`Tablet split-screen phone layout did not rehydrate after narrowing: ${JSON.stringify(backToSplit)}`);
      }
      await context.close();
    }

    if (wantsTabletMiniSeries(caseName)) {
      const context = await browser.newContext({
        viewport: { width: 1180, height: 820 },
        deviceScaleFactor: 1,
        isMobile: false,
        hasTouch: true,
        locale: "de-DE",
      });
      await context.route(/^https?:\/\//, async (route) => {
        externalRequests.push(route.request().url());
        await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
      });
      const page = await context.newPage();
      page.on("pageerror", (err) => pageErrors.push(err.message));
      const tabletHtml = fs.readFileSync(HTML_PATH, "utf8").replace(/<script\b[\s\S]*?<\/script>/gi, "");
      await page.setContent(tabletHtml, { waitUntil: "domcontentloaded", timeout: 30000 });
      const injectedProbe = await page.evaluate(() => ({
        readyState: document.readyState,
        htmlLength: document.documentElement ? document.documentElement.outerHTML.length : 0,
        bodyLength: document.body ? document.body.innerHTML.length : 0,
        hasScanHub: !!document.querySelector(".scanHub"),
        bodyStart: document.body ? document.body.innerHTML.slice(0, 160) : "",
      }));
      if (!injectedProbe.hasScanHub) {
        fail(`Tablet HTML injection did not expose scanHub: ${JSON.stringify(injectedProbe)}`);
      }
      await page.waitForSelector(".scanHub", { state: "attached", timeout: 15000 });
      await page.evaluate((exercises) => {
        document.body.classList.add("adminMode", "tabletLayoutCustom");
        const createPanel = document.getElementById("createPanel");
        if (createPanel) createPanel.classList.add("planMode");
        const planActions = document.getElementById("planActions");
        if (planActions) planActions.classList.add("hasPlan");
        const rightPlanStack = document.getElementById("rightPlanStack");
        if (rightPlanStack) rightPlanStack.classList.remove("hidden");
        const currentPlanBlock = document.getElementById("currentPlanBlock");
        if (currentPlanBlock) currentPlanBlock.classList.remove("hidden");
        const finish = document.getElementById("finishBtn");
        if (finish) finish.classList.remove("hidden");
        const panelTitle = document.getElementById("panelTitle");
        if (panelTitle) panelTitle.textContent = "✏️ Aktueller Plan";
        const currentPlanCount = document.getElementById("currentPlanCount");
        if (currentPlanCount) currentPlanCount.textContent = `${exercises.length} Übungen`;
        const planList = document.getElementById("planList");
        if (planList) {
          planList.innerHTML = exercises.map((ex, index) => `
            <div class="planCard" data-plan-id="${ex.id}">
              <div class="planMain">
                <button class="drag" data-sort-id="${ex.id}" type="button">⋮⋮</button>
                <span class="planText"><b class="planName">${index + 1}. ${ex.name}</b><small>3 Sätze · beidseitig · kg · Wdh</small></span>
              </div>
              <button class="iconBtn" type="button">⚙️</button>
            </div>
          `).join("");
        }
      }, seededExercises(8));
      await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
      await page.waitForTimeout(500);
      const layoutProbe = await page.evaluate(() => {
        const rect = (id) => {
          const el = id.startsWith(".") || id.startsWith("#") ? document.querySelector(id) : document.getElementById(id);
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return {
            left: Math.round(r.left),
            top: Math.round(r.top),
            right: Math.round(r.right),
            bottom: Math.round(r.bottom),
            width: Math.round(r.width),
            height: Math.round(r.height),
            display: getComputedStyle(el).display,
            position: getComputedStyle(el).position,
            visibility: getComputedStyle(el).visibility,
            pointerEvents: getComputedStyle(el).pointerEvents,
          };
        };
        const scan = rect(".scanHub");
        const create = rect("createPanel");
        const input = rect("inputWrap");
        const current = rect("currentPlanBlock");
        const planList = rect("planList");
        const menuButton = rect("tabletMenuBtn");
        const cards = Array.from(document.querySelectorAll("#planList .planCard[data-plan-id]")).map((card) => {
          const r = card.getBoundingClientRect();
          return { left: Math.round(r.left), top: Math.round(r.top), right: Math.round(r.right), bottom: Math.round(r.bottom), width: Math.round(r.width), height: Math.round(r.height) };
        });
        const modalOpen = !!document.querySelector(".modal.open");
        const phoneClasses = ["kggPhoneHasPlan", "kggPhoneDrawerOpen", "kggPhoneDrawerSafeOpen", "kggPhonePhotoMenuOpen"].filter((name) => document.body.classList.contains(name));
        const overlapInputPlan = input && current ? (input.left < current.right && input.right > current.left && input.top < current.bottom && input.bottom > current.top) : true;
        return {
          bodyClass: document.body.className,
          viewport: { width: window.innerWidth, height: window.innerHeight },
          scan,
          create,
          input,
          current,
          planList,
          menuButton,
          cards,
          modalOpen,
          phoneClasses,
          overlapInputPlan,
          cardCount: cards.length,
          visibleCardCount: cards.filter((r) => r.width > 180 && r.height > 38 && r.bottom > 0 && r.top < window.innerHeight).length,
        };
      });
      if (
        layoutProbe.viewport.width < 760 ||
        !layoutProbe.scan ||
        layoutProbe.scan.position === "fixed" ||
        !layoutProbe.current ||
        layoutProbe.current.width < 300 ||
        layoutProbe.current.height < 220 ||
        !layoutProbe.planList ||
        layoutProbe.cardCount < 6 ||
        layoutProbe.visibleCardCount < 3 ||
        !layoutProbe.menuButton ||
        layoutProbe.menuButton.width < 30 ||
        layoutProbe.modalOpen ||
        layoutProbe.phoneClasses.length ||
        layoutProbe.overlapInputPlan
      ) {
        fail(`Tablet visual layout probe failed: ${JSON.stringify(layoutProbe)}`);
      }

      await page.waitForSelector("#tabletMenuBtn", { timeout: 15000 });
      if (caseMatches(caseName, ["ui-mini-series", "tablet-layout-visual"])) {
        await page.evaluate(() => document.body.classList.add("tabletMenuOpen"));
        const menuState = await page.evaluate(() => {
          const ids = ["tabletMenuLayoutBtn", "tabletMenuTherapistShareBtn", "tabletMenuRecentBtn", "tabletMenuPackagesBtn"];
          return Object.fromEntries(ids.map((id) => {
            const el = id.startsWith(".") || id.startsWith("#") ? document.querySelector(id) : document.getElementById(id);
            if (!el) return [id, { exists: false }];
            const r = el.getBoundingClientRect();
            return [id, {
              exists: true,
              display: getComputedStyle(el).display,
              width: Math.round(r.width),
              height: Math.round(r.height),
              text: el.textContent.trim(),
            }];
          }));
        });
        for (const [id, state] of Object.entries(menuState)) {
          if (!state.exists || state.display === "none" || state.width < 80 || state.height < 32) {
            fail(`Tablet menu item not usable (${id}): ${JSON.stringify(menuState)}`);
          }
        }
      }
      if (!caseMatches(caseName, ["tablet-layout-visual"])) {
        await page.locator("#tabletMenuBtn").click();
        await page.waitForFunction(() => document.body.classList.contains("tabletMenuOpen"), null, { timeout: 10000 });
        await page.locator("#tabletMenuLayoutBtn").click();
        await page.waitForFunction(() => document.body.classList.contains("tabletLayoutEditMode"), null, { timeout: 10000 });
        const openState = await page.evaluate(() => {
          const panel = document.getElementById("tabletMenuLayoutPanel");
          const tools = document.getElementById("tabletLayoutFreeTools");
          return {
            editMode: document.body.classList.contains("tabletLayoutEditMode"),
            panelHidden: panel ? panel.hidden : true,
            expanded: document.getElementById("tabletMenuLayoutBtn").getAttribute("aria-expanded"),
            toolsDisplay: tools ? getComputedStyle(tools).display : "missing",
          };
        });
        if (!openState.editMode || openState.panelHidden || openState.expanded !== "true" || openState.toolsDisplay === "none") {
          fail(`Tablet layout panel did not open: ${JSON.stringify(openState)}`);
        }
        await page.locator("#tabletMenuLayoutBtn").click();
        await page.waitForFunction(() => !document.body.classList.contains("tabletLayoutEditMode"), null, { timeout: 10000 });
        const closedState = await page.evaluate(() => {
          const panel = document.getElementById("tabletMenuLayoutPanel");
          return {
            editMode: document.body.classList.contains("tabletLayoutEditMode"),
            panelHidden: panel ? panel.hidden : false,
            expanded: document.getElementById("tabletMenuLayoutBtn").getAttribute("aria-expanded"),
          };
        });
        if (closedState.editMode || !closedState.panelHidden || closedState.expanded !== "false") {
          fail(`Tablet layout panel did not close: ${JSON.stringify(closedState)}`);
        }
        await page.locator("#tabletMenuBtn").click();
        await page.waitForFunction(() => !document.body.classList.contains("tabletMenuOpen"), null, { timeout: 10000 });
        const card = page.locator("#planList .planCard[data-plan-id]").first();
        const center = await elementCenter(card);
        await dispatchPointer(page, "#planList .planCard[data-plan-id]", "pointerdown", center.x, center.y, 77);
        await page.waitForTimeout(180);
        const armed = await page.evaluate(() => ({
          reorderClass: document.body.classList.contains("kggPlanCardReordering"),
          lifted: !!document.querySelector("#planList .planCard.reorder-lifted"),
          placeholder: !!document.querySelector("#planList .reorder-placeholder"),
        }));
        if (!armed.reorderClass || !armed.lifted || !armed.placeholder) {
          fail(`Tablet card surface reorder did not start: ${JSON.stringify(armed)}`);
        }
        await dispatchPointer(page, "document", "pointerup", center.x + 8, center.y + 8, 77);
        await page.waitForTimeout(220);
        const cleanup = await page.evaluate(() => ({
          reorderClass: document.body.classList.contains("kggPlanCardReordering"),
          lifted: !!document.querySelector("#planList .planCard.reorder-lifted"),
          placeholder: !!document.querySelector("#planList .reorder-placeholder"),
        }));
        if (cleanup.reorderClass || cleanup.lifted || cleanup.placeholder) {
          fail(`Tablet card reorder cleanup leaked state: ${JSON.stringify(cleanup)}`);
        }
      }
      await context.close();
    }

    if (pageErrors.length) fail(`Page error during UI mini-series tests: ${pageErrors.join(" | ")}`);
    console.log(`Browser UI mini-series OK (${caseName || "all"}, ${externalRequests.length} external request(s) blocked)`);
  } finally {
    await browser.close();
  }
}

async function browserTabletAppBootSuite() {
  const { chromium } = requirePlaywright();
  const htmlUrl = pathToFileURL(HTML_PATH).href;
  const externalRequests = [];
  const pageErrors = [];
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({
      viewport: { width: 1180, height: 820 },
      deviceScaleFactor: 1,
      isMobile: false,
      hasTouch: true,
      locale: "de-DE",
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
          patient: { name: "Tablet Runtime", date: "2026-06-29", therapist: "Codex" },
          bankOpen: false,
          recent: [],
          packages: [],
        })
      );
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-06-29T00:00:00.000Z");
    }, { storageKey: STORAGE_KEY, exercises: seededExercises(8) });

    const page = await context.newPage();
    page.on("pageerror", (err) => pageErrors.push(err.message));
    await page.goto(htmlUrl, { waitUntil: "commit", timeout: 15000 });
    try {
      await page.waitForSelector("#scanHub", { state: "attached", timeout: 12000 });
    } catch (err) {
      fail(`Tablet app boot did not expose #scanHub before timeout; likely early runtime freeze. ${err && err.message ? err.message : err} | pageErrors=${JSON.stringify(pageErrors)}`);
    }
    await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 12000 });
    await page.waitForTimeout(500);
    const boot = await page.evaluate(() => {
      const rect = (id) => {
        const el = document.getElementById(id);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {
          width: Math.round(r.width),
          height: Math.round(r.height),
          display: getComputedStyle(el).display,
          position: getComputedStyle(el).position,
        };
      };
      return {
        readyState: document.readyState,
        bodyClass: document.body.className,
        scan: rect("scanHub"),
        current: rect("currentPlanBlock"),
        cardCount: document.querySelectorAll("#planList .planCard[data-plan-id]").length,
        modalOpen: !!document.querySelector(".modal.open"),
        tabletMenuBtn: rect("tabletMenuBtn"),
      };
    });
    if (!boot.scan || !boot.current || boot.current.width < 300 || boot.cardCount < 6 || !boot.tabletMenuBtn) {
      fail(`Tablet app boot probe failed: ${JSON.stringify(boot)}`);
    }
    if (pageErrors.length) fail(`Page error during tablet app boot: ${pageErrors.join(" | ")}`);
    await context.close();
    console.log(`Browser tablet app boot OK (${externalRequests.length} external request(s) blocked)`);
  } finally {
    await browser.close();
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
  const knownCases = ["all", "gestures", "ui-mini-series", "bank-thumbnails", "phone-admin-menu", "phone-scan-dock", "phone-history-packages", "phone-bank-align", "tablet-layout-button", "tablet-card-reorder", "tablet-layout-visual", "tablet-split-phone-layout", "phone-landscape-tablet-menu", "tablet-app-boot"];
  if (!knownCases.includes(args.caseName)) {
    fail(`Unknown case: ${args.caseName}`);
  }
  if (caseMatches(args.caseName, ["gestures"])) {
    staticGestureGuardSuite();
  }
  if (args.caseName !== "gestures") {
    staticUiMiniSeriesGuardSuite(args.caseName);
  }
  if (args.level === "regression" || args.level === "all" || args.browser) {
    if (caseMatches(args.caseName, ["gestures"])) {
      await browserGestureSuite();
    }
    if (args.caseName !== "gestures") {
      await browserUiMiniSeriesSuite(args.caseName);
    }
    if (args.caseName === "tablet-app-boot") {
      await browserTabletAppBootSuite();
    }
  }
  console.log(`KGG UI stability smoke OK (${args.level}, case=${args.caseName})`);
}

main().catch((err) => {
  console.error(`ERROR: ${err && err.stack ? err.stack : err}`);
  process.exit(1);
});
