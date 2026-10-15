#!/usr/bin/env node
"use strict";

// Synthetic, read-only browser comparison. No patient records or external URLs.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const { chromium, webkit } = require("playwright");
const { validateFixtureState } = require("./kgg_patient_ui_parity_contracts.cjs");
const {execFileSync} = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.resolve(process.env.KGG_PARITY_OUT || path.join(ROOT, ".tmp", "patient-ui-parity"));
const ENGINE = process.env.KGG_PARITY_ENGINE || "chromium";
const INCLUDE_P8 = process.env.KGG_PARITY_P8_GRID === "1";
const VIEWPORTS = [{ name: "phone", width: 390, height: 844 },
                   { name: "tablet", width: 768, height: 1024 }];
const STEPS = ["pair-kg", "pair-wdh", "remaining-kg", "pair-complete", "manual-zero", "cancelled", "saved-zero", "center-complete", "lr-left", "lr-right", "seconds-complete", "reloaded"];
const assert = (x, msg) => { if (!x) throw new Error(msg); };


function mime(filename) {
  if (filename.endsWith(".html")) return "text/html; charset=utf-8";
  if (filename.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (filename.endsWith(".css")) return "text/css; charset=utf-8";
  if (filename.endsWith(".json")) return "application/json; charset=utf-8";
  if (filename.endsWith(".png")) return "image/png";
  if (filename.endsWith(".svg")) return "image/svg+xml";
  return "application/octet-stream";
}

function serve() {
  const server = http.createServer((req, res) => {
    try {
      const pathname = new URL(req.url, "http://localhost").pathname;
      const requested = path.resolve(ROOT, "." + decodeURIComponent(pathname === "/" ? "/index.html" : pathname));
      if (!requested.startsWith(ROOT + path.sep) || !fs.existsSync(requested) || !fs.statSync(requested).isFile()) {
        res.writeHead(404).end("404");
        return;
      }
      res.setHeader("Content-Type", mime(requested));
      res.setHeader("Cache-Control", "no-store");
      res.end(fs.readFileSync(requested));
    } catch (error) {
      res.writeHead(400).end("bad request");
    }
  });
  return server;
}

function planUrl(port, mode) {
  const plan = { i: "synthetic-parity-v1", t: "SYNTHETIC UI PARITY", v: 1, d: 6,
    e: [["Pair", 3, "B", "kg", "Wdh"], ["Sides", 1, "LR", "kg", "Wdh"], ["Timer", 1, "B", "keine", "Sek."]] };
  const encoded = Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
  return "http://127.0.0.1:" + port + "/?kggReactPad=" + (mode === "legacy" ? "0" : "1") +
    (mode === "react-grid" ? "&kggReactGrid=1" : "") + "&plan=" + encodeURIComponent("KGGH2:" + encoded);
}

async function openCard(card, page) {
  for (let i = 0; i < 5; i++) {
    if (await card.evaluate(el => el.classList.contains("kggOpen"))) return;
    await card.locator("h3").click();
    await page.waitForTimeout(90);
  }
  throw new Error("Synthetic card did not open");
}

async function tapField(card, setIndex, key) {
  const proxy = card.locator(":scope > .set").nth(setIndex)
    .locator(".kggCompactTapProxy[data-kgg-key='" + key + "']").first();
  await proxy.waitFor({ state: "visible" });
  await proxy.click();
}

async function tapInput(input) {
  const index = await input.evaluate(el => [...el.parentElement.querySelectorAll(".kggCompactTapProxy")].findIndex(p => p.__kggInput === el));
  assert(index >= 0, "real compact tap proxy missing");
  await input.locator("xpath=..").locator(".kggCompactTapProxy").nth(index).click();
}

async function state(page) {
  return page.evaluate(() => {
    const pad = document.getElementById("pad");
    const api = window.__kggNumpadEditingApi;
    const editing = api && api.getSnapshot ? api.getSnapshot() : null;
    const card = document.querySelector("#list .ex");
    const rect = (selector) => {
      const node = document.querySelector(selector);
      if (!node || !node.getBoundingClientRect) return null;
      const r = node.getBoundingClientRect();
      return { left: r.left, top: r.top, width: r.width, height: r.height };
    };
    const texts = selector => [...document.querySelectorAll(selector)].map(el => el.textContent.trim());
    const isOpen = !!pad && !pad.classList.contains("hide");
    const react = document.body.classList.contains("kggReactNumpadHeaderV1");
    const legacyPair = texts("#kggPadPair .kggPairValue");
    const legacyTransfer = texts("#kggPadTransfer > button:not(.kggTransferGhost)");
    const visiblePair = react ? texts(".kgg-react-numpad-pair__value") : legacyPair;
    const visibleTransfer = react ? texts(".kgg-react-numpad-transfer__button") : legacyTransfer;
    const valuePair = (ei, set, side) => ["a", "b"].map(key => String(v[k(ei,set,side,key)] ?? ""));
    return {
      fixture: {pair1:valuePair(0,1,"B"),pair2:valuePair(0,2,"B"),pair3:valuePair(0,3,"B"),left:valuePair(1,1,"L"),right:valuePair(1,1,"R"),timer:valuePair(2,1,"B")},
      visiblePair, visibleTransfer,
      visibleMatchesLegacy: !isOpen || (JSON.stringify(visiblePair) === JSON.stringify(legacyPair) && JSON.stringify(visibleTransfer) === JSON.stringify(legacyTransfer)),
      day: d,
      done: [...done].sort((a, b) => a - b),
      // The fixture is entirely synthetic; comparing the actual legacy store catches duplicate commits.
      values: Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])),
      inputs: card ? [...card.querySelectorAll("input.num")].map(el => String(el.value)) : [],
      padOpen: !!pad && !pad.classList.contains("hide"),
      field: editing && editing.meta ? {
        ei: editing.meta.ei, s: editing.meta.s, side: editing.meta.side, key: editing.meta.key
      } : null,
      draft: editing ? editing.padValue : "",
      dirty: editing ? !!editing.dirty : false,
      transfer: [...document.querySelectorAll("#kggPadTransfer > button:not(.kggTransferGhost)")].map(el => el.textContent.trim()),
      scroll: { windowY: window.scrollY, mainTop: document.querySelector("main")?.scrollTop || 0 },
      geometry: { keys: rect("#pad .padGrid"), actions: rect("#pad .padActions") }
    };
  });
}

async function recordVariant(browser, port, mode, viewport) {
  const prefix = viewport.name + "-" + mode;
  const evidence = { mode, viewport: viewport.name, steps: {}, oracle: [], consoleErrors: [], externalRequests: [], motion: [] };
  const started = Date.now();
  const ctx = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    screen: { width: viewport.width, height: viewport.height },
    isMobile: true,
    hasTouch: true,
    reducedMotion: "no-preference",
    serviceWorkers: "block",
    recordVideo: { dir: path.join(OUT, "_raw"), size: { width: viewport.width, height: viewport.height } }
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(8500);
  const video = page.video();
  const reactMode = mode !== "legacy";
  const gridKey = index => mode === "react-grid"
    ? page.locator("#kggReactNumpadGridRoot .kgg-react-numpad-grid__key").nth(index)
    : page.locator("#pad .padGrid > button").nth(index);
  page.on("pageerror", error => evidence.consoleErrors.push(String(error)));
  await page.route("**/*", async route => {
    const url = route.request().url();
    if (!url.startsWith("http://127.0.0.1:" + port + "/")) {
      evidence.externalRequests.push(url.split("?")[0]);
      await route.abort();
      return;
    }
    await route.continue();
  });
  await page.addInitScript(() => {
    if (!sessionStorage.syntheticParityBoot) {
      localStorage.clear();
      localStorage.kggInstallAsked = "1";
      sessionStorage.syntheticParityBoot = "1";
    }
  });

  async function checkpoint(label) {
    await page.waitForTimeout(270); // includes the legacy 220ms transfer-caret transition
    const current = await state(page);
    evidence.steps[label] = current;
    current.elapsedMs = Date.now() - started;
    evidence.oracle.push(validateFixtureState(label, current));
    await page.screenshot({ path: path.join(OUT, prefix + "-" + label + ".png"), animations: "disabled" });
    if (current.padOpen) {
      for (const part of ["keys", "actions"]) {
        const selector = part === "keys" ? "#pad .padGrid" : "#pad .padActions";
        await page.locator(selector).screenshot({
          path: path.join(OUT, prefix + "-" + label + "-" + part + ".png"),
          animations: "disabled"
        });
      }
    }
  }

  try {
    await page.goto(planUrl(port, mode), { waitUntil: "networkidle" });
    await page.waitForFunction(() => document.body.classList.contains("kggAlwaysCollapsed"));
    if (reactMode) {
      await page.waitForFunction(() => document.body.classList.contains("kggReactNumpadHeaderV1"));
      if (mode === "react-grid") {
        await page.waitForFunction(() => document.body.classList.contains("kggReactNumpadGridV1") &&
          document.querySelectorAll(".kgg-react-numpad-grid__key").length === 12);
      }
    } else {
      assert(!(await page.evaluate(() => document.body.classList.contains("kggReactNumpadHeaderV1"))), "Legacy unexpectedly loaded React");
    }
    await page.evaluate(() => {
      const putDay = (ei, s, side, key, value, day = 1) => { v[k(ei, s, side, key, day)] = String(value); };
      putDay(0, 1, "B", "a", 15);
      putDay(0, 1, "B", "b", 12);
      putDay(0, 3, "B", "a", 25); putDay(0, 3, "B", "b", 9);
      putDay(1, 1, "L", "a", 11); putDay(1, 1, "L", "b", 8);
      putDay(1, 1, "R", "a", 13); putDay(1, 1, "R", "b", 9);
      putDay(2, 1, "B", "b", 45);
      d = 2; done = [1]; save(); render();
    });
    await page.waitForTimeout(450);
    const card = page.locator("#list .ex").first();
    await openCard(card, page);
    await tapField(card, 0, "a");
    await page.waitForFunction(() => !document.getElementById("pad").classList.contains("hide"));
    if (reactMode) {
      await page.locator("[data-kgg-react-numpad-header='v1']").waitFor();
    }
    await page.waitForTimeout(850); // stabilize initial scroll before measuring a same-row switch
    await checkpoint("pair-kg");

    const pairB = reactMode
      ? ".kgg-react-numpad-pair__button[data-kgg-key='b']"
      : "#kggPadPair .kggPairField[data-kgg-key='b']";
    await page.evaluate(() => {
      const samples=[];window.__kggParityMotion={samples,active:true};
      function frame(){
        if(!window.__kggParityMotion.active)return;
        samples.push({t:performance.now(),padOpen:!document.getElementById("pad").classList.contains("hide"),y:window.scrollY,main:document.querySelector("main").scrollTop});
        requestAnimationFrame(frame);
      }requestAnimationFrame(frame);
    });
    await page.locator(pairB).click();
    await page.waitForFunction(() => window.__kggNumpadEditingApi?.getSnapshot?.().meta?.key === "b");
    await page.waitForTimeout(320);
    const samples=await page.evaluate(()=>{window.__kggParityMotion.active=false;return window.__kggParityMotion.samples});
    assert(samples.length>=2,mode+" missing frame evidence");
    assert(samples.every(s=>s.padOpen),mode+" NumPad closed during same-row switch");
    for(const axis of ["y","main"]){const xs=samples.map(s=>s[axis]);assert(Math.max(...xs)-Math.min(...xs)<=2,mode+" transient scroll jump on "+axis)}
    evidence.motion.push({step:"pair-wdh",samples});
    await checkpoint("pair-wdh");

    const transferB = reactMode
      ? ".kgg-react-numpad-transfer__button[data-kgg-transfer-key='b']"
      : "#kggPadTransfer > button[data-kgg-transfer-key='b']";
    await page.locator(transferB).click();
    await checkpoint("remaining-kg");

    const transferA = reactMode
      ? ".kgg-react-numpad-transfer__button[data-kgg-transfer-key='a']"
      : "#kggPadTransfer > button[data-kgg-transfer-key='a']";
    await page.locator(transferA).click();
    await checkpoint("pair-complete");
    assert(evidence.steps["pair-complete"].padOpen === false, mode + " pair did not close");

    await tapField(card, 1, "a");
    await gridKey(6).click(); // 7
    await gridKey(11).click(); // backspace
    await gridKey(10).click(); // explicit 0
    await checkpoint("manual-zero");

    await page.locator("#pad .padActions .padCancel").click();
    await checkpoint("cancelled");

    await tapField(card, 1, "a");
    await gridKey(10).click();
    await page.locator("#pad .padActions .padOk").click();
    await checkpoint("saved-zero");

    const both = reactMode ? '.kgg-react-numpad-transfer__button[data-kgg-transfer-both="1"]' : '#kggPadTransfer > button[data-kgg-transfer-both="1"]';
    await tapField(card,2,"a");
    await page.locator(both).click();
    await checkpoint("center-complete");

    const lr=page.locator("#list .ex").nth(1);await openCard(lr,page);
    await tapInput(lr.locator(".kggSideL").first().locator("input.num").first());
    await page.locator(both).click();await checkpoint("lr-left");
    await tapInput(lr.locator(".kggSideR").first().locator("input.num").first());
    await page.locator(both).click();await checkpoint("lr-right");

    const timer=page.locator("#list .ex").nth(2);await openCard(timer,page);
    await tapInput(timer.locator("input.num:not(.kggUnitInactive)").first());
    const timerTransfer=reactMode ? '.kgg-react-numpad-transfer__button[data-kgg-transfer-key="b"]' : '#kggPadTransfer > button[data-kgg-transfer-key="b"]';
    await page.locator(timerTransfer).click();await checkpoint("seconds-complete");
    await page.reload({waitUntil:"networkidle"});
    await page.waitForFunction(()=>document.querySelectorAll("#list .ex").length===3);
    if(reactMode)await page.waitForFunction(()=>document.body.classList.contains("kggReactNumpadHeaderV1"));
    await checkpoint("reloaded");

    assert(evidence.consoleErrors.length === 0, mode + " page errors: " + evidence.consoleErrors.join("; "));
    assert(evidence.steps["saved-zero"].padOpen === false, mode + " numpad still open after OK");
    return evidence;
  } finally {
    await ctx.close();
    if (video) await video.saveAs(path.join(OUT, prefix + ".webm"));
  }
}

async function pixelDifference(page, fileA, fileB) {
  const [a, b] = [fileA, fileB].map(f => fs.readFileSync(f).toString("base64"));
  return page.evaluate(async ([left, right]) => {
    const load = async b64 => {
      const image = new Image();
      image.src = "data:image/png;base64," + b64;
      await image.decode();
      const canvas = document.createElement("canvas");
      canvas.width = image.width; canvas.height = image.height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(image, 0, 0);
      return { width: image.width, height: image.height, data: ctx.getImageData(0, 0, image.width, image.height).data };
    };
    const x = await load(left), y = await load(right);
    if (x.width !== y.width || x.height !== y.height) return { ratio: 1, dimensionsMatch: false };
    let changed = 0;
    for (let i = 0; i < x.data.length; i += 4) {
      if (Math.max(Math.abs(x.data[i] - y.data[i]), Math.abs(x.data[i + 1] - y.data[i + 1]),
                   Math.abs(x.data[i + 2] - y.data[i + 2])) > 24) changed++;
    }
    return { dimensionsMatch: true, ratio: changed / (x.width * x.height), width: x.width, height: x.height };
  }, [a, b]);
}

async function main() {
  assert(["chromium", "webkit"].includes(ENGINE), "unsupported browser " + ENGINE);
  // OUT must be a dedicated evidence directory, never a repo root or home directory.
  assert(path.basename(OUT) === "patient-ui-parity", "output must end in patient-ui-parity");
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });
  fs.mkdirSync(path.join(OUT, "_raw"), { recursive: true });
  const report = { schema: 2, syntheticOnly: true, engine: ENGINE, status: "INCOMPLETE",
    candidateSha: process.env.KGG_PARITY_HEAD_SHA || execFileSync("git",["rev-parse","HEAD"],{cwd:ROOT,encoding:"utf8"}).trim(),
    gitSha: process.env.GITHUB_SHA || execFileSync("git",["rev-parse","HEAD"],{cwd:ROOT,encoding:"utf8"}).trim(),
    motionMode:"normal", serviceWorkerCoverage:"separate existing PWA tests; blocked in this recorder",
    steps: STEPS, variants: [], checks: [], recordings: [], unexpectedDifferences: [] };
  const server = serve();
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  let browser;
  try {
    browser = await (ENGINE === "webkit" ? webkit : chromium).launch({ headless: true });
    const comparisonPage = await browser.newPage();
    for (const viewport of VIEWPORTS) {
      const baseline = await recordVariant(browser, port, "legacy", viewport);
      const originalReact = await recordVariant(browser, port, "react", viewport);
      const variants = [baseline, originalReact];
      if (INCLUDE_P8) variants.push(await recordVariant(browser, port, "react-grid", viewport));
      for (const variant of variants) {
        report.recordings.push(viewport.name + "-" + variant.mode + ".webm");
        report.variants.push(variant);
        for (const result of variant.oracle) report.checks.push({
          viewport: viewport.name, mode: variant.mode, kind: "independent-fixture", ...result
        });
      }
      for (const react of variants.slice(1)) {
        const addCheck = row => report.checks.push({comparison: react.mode, ...row});
        const addDiff = row => report.unexpectedDifferences.push({comparison: react.mode, ...row});
        for (const step of STEPS) {
        const a = baseline.steps[step], b = react.steps[step];
        assert(a && b, "missing step " + step);
        const keys = ["day", "done", "values", "inputs", "padOpen", "field", "draft", "dirty", "transfer", "visibleMatchesLegacy", "fixture"];
        for (const key of keys) {
          const same = JSON.stringify(a[key]) === JSON.stringify(b[key]);
          addCheck({ viewport: viewport.name, step, kind: "state:" + key, pass: same });
          if (!same) addDiff({ viewport: viewport.name, step, kind: "state:" + key, legacy: a[key], react: b[key] });
        }
        // Absolute main.scrollTop can differ because the two visual headers reserve
        // different non-content space. The safety contract is NO EXTRA JUMP during
        // switching/editing, assessed relative to the current open/closed phase.
        const scrollAnchor = ["pair-wdh", "remaining-kg"].includes(step) ? "pair-kg" : null;
        for (const axis of ["windowY", "mainTop"]) {
          const absoluteDelta = Math.abs(a.scroll[axis] - b.scroll[axis]);
          if (!scrollAnchor) {
            addCheck({ viewport: viewport.name, step, kind: "scroll-base:" + axis,
              pass: null, absoluteDelta, policy: "OBSERVATION ONLY: different card/open/close phase; not a passed invariant" });
            continue;
          }
          const aMove = a.scroll[axis] - baseline.steps[scrollAnchor].scroll[axis];
          const bMove = b.scroll[axis] - react.steps[scrollAnchor].scroll[axis];
          const jumpDelta = Math.abs(aMove - bMove);
          addCheck({ viewport: viewport.name, step, kind: "scroll-jump:" + axis,
            pass: jumpDelta <= 2, jumpDelta, legacyMove: aMove, reactMove: bMove });
          if (jumpDelta > 2) addDiff({
            viewport: viewport.name, step, kind: "scroll-jump:" + axis, jumpDelta, legacyMove: aMove, reactMove: bMove
          });
        }
        if (a.padOpen && b.padOpen) {
          for (const part of ["keys", "actions"]) {
            const x = a.geometry[part], y = b.geometry[part];
            const sameShape = x && y && ["left", "top", "width", "height"].every(k => Math.abs(x[k] - y[k]) <= 2);
            addCheck({ viewport: viewport.name, step, kind: "geometry:" + part, pass: !!sameShape });
            if (!sameShape) addDiff({ viewport: viewport.name, step, kind: "geometry:" + part, legacy: x, react: y });
            const diff = await pixelDifference(comparisonPage,
              path.join(OUT, viewport.name + "-legacy-" + step + "-" + part + ".png"),
              path.join(OUT, viewport.name + "-react-" + step + "-" + part + ".png"));
            const equal = diff.dimensionsMatch && diff.ratio <= 0.01;
            addCheck({ viewport: viewport.name, step, kind: "pixel:" + part, pass: equal, diff });
            if (!equal) addDiff({ viewport: viewport.name, step, kind: "pixel:" + part, diff });
          }
        }
      }
        assert(baseline.consoleErrors.length === 0 && react.consoleErrors.length === 0,
          "unexpected runtime errors in " + react.mode);
      }
    }
    assert(!INCLUDE_P8 || report.variants.filter(v => v.mode === "react-grid").length === VIEWPORTS.length,
      "P8 requested but not exercised for every viewport");
    report.status = report.unexpectedDifferences.length ? "FAIL" : "PASS";
    console.log("KGG patient React/legacy parity: " + report.status +
      " (" + report.checks.length + " checks; " + report.unexpectedDifferences.length + " differences)");
    if (report.unexpectedDifferences.length) {
      console.error("PARITY_DIAGNOSTIC=" + JSON.stringify(report.unexpectedDifferences.slice(0, 24)));
    }
  } catch (error) {
    report.status = "FAIL";
    report.error = String(error && error.stack || error);
    console.error(report.error);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(path.join(OUT, "_raw"), { recursive: true, force: true });
    fs.writeFileSync(path.join(OUT, "report.json"), JSON.stringify(report, null, 2) + "\n");
  }
  if (report.status !== "PASS") process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
