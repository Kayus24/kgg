#!/usr/bin/env node
"use strict";

// Synthetic, read-only browser comparison. No patient records or external URLs.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const { chromium, webkit } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.resolve(process.env.KGG_PARITY_OUT || path.join(ROOT, ".tmp", "patient-ui-parity"));
const ENGINE = process.env.KGG_PARITY_ENGINE || "chromium";
const VIEWPORTS = [{ name: "phone", width: 390, height: 844 },
                   { name: "tablet", width: 768, height: 1024 }];
const STEPS = ["pair-kg", "pair-wdh", "remaining-kg", "pair-complete", "manual-zero", "cancelled", "saved-zero"];
const assert = (x, msg) => { if (!x) throw new Error(msg); };
const sleep = ms => new Promise(done => setTimeout(done, ms));

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
    e: [["Pair", 2, "B", "kg", "Wdh"]] };
  const encoded = Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
  return "http://127.0.0.1:" + port + "/?kggReactPad=" + (mode === "react" ? "1" : "0") +
    "&plan=" + encodeURIComponent("KGGH2:" + encoded);
}

async function openCard(card, page) {
  for (let i = 0; i < 5; i++) {
    if (await card.evaluate(el => el.classList.contains("kggOpen"))) return;
    await card.locator("h3").evaluate(el => el.click());
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
    return {
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
  const evidence = { mode, viewport: viewport.name, steps: {}, consoleErrors: [], externalRequests: [] };
  const ctx = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    screen: { width: viewport.width, height: viewport.height },
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
    recordVideo: { dir: path.join(OUT, "_raw"), size: { width: viewport.width, height: viewport.height } }
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(8500);
  const video = page.video();
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
    if (mode === "react") {
      await page.waitForFunction(() => document.body.classList.contains("kggReactNumpadHeaderV1"));
    } else {
      assert(!(await page.evaluate(() => document.body.classList.contains("kggReactNumpadHeaderV1"))), "Legacy unexpectedly loaded React");
    }
    await page.evaluate(() => {
      const putDay = (ei, s, side, key, value, day = 1) => { v[k(ei, s, side, key, day)] = String(value); };
      putDay(0, 1, "B", "a", 15);
      putDay(0, 1, "B", "b", 12);
      d = 2; done = [1]; save(); render();
    });
    await page.waitForTimeout(450);
    const card = page.locator("#list .ex").first();
    await openCard(card, page);
    await tapField(card, 0, "a");
    await page.waitForFunction(() => !document.getElementById("pad").classList.contains("hide"));
    if (mode === "react") {
      await page.locator("[data-kgg-react-numpad-header='v1']").waitFor();
    }
    await checkpoint("pair-kg");

    const pairB = mode === "react"
      ? ".kgg-react-numpad-pair__button[data-kgg-key='b']"
      : "#kggPadPair .kggPairField[data-kgg-key='b']";
    await page.locator(pairB).click();
    await page.waitForFunction(() => window.__kggNumpadEditingApi?.getSnapshot?.().meta?.key === "b");
    await checkpoint("pair-wdh");

    const transferB = mode === "react"
      ? ".kgg-react-numpad-transfer__button[data-kgg-transfer-key='b']"
      : "#kggPadTransfer > button[data-kgg-transfer-key='b']";
    await page.locator(transferB).click();
    await checkpoint("remaining-kg");

    const transferA = mode === "react"
      ? ".kgg-react-numpad-transfer__button[data-kgg-transfer-key='a']"
      : "#kggPadTransfer > button[data-kgg-transfer-key='a']";
    await page.locator(transferA).click();
    await checkpoint("pair-complete");
    assert(evidence.steps["pair-complete"].padOpen === false, mode + " pair did not close");

    await tapField(card, 1, "a");
    await page.locator("#pad .padGrid button").nth(6).click(); // 7
    await page.locator("#pad .padGrid button").nth(11).click(); // backspace
    await page.locator("#pad .padGrid button").nth(10).click(); // explicit 0
    await checkpoint("manual-zero");

    await page.locator("#pad .padActions .padCancel").click();
    await checkpoint("cancelled");

    await tapField(card, 1, "a");
    await page.locator("#pad .padGrid button").nth(10).click();
    await page.locator("#pad .padActions .padOk").click();
    await checkpoint("saved-zero");

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
  const report = { schema: 1, syntheticOnly: true, engine: ENGINE, status: "INCOMPLETE",
    gitSha: process.env.GITHUB_SHA || "local", checks: [], recordings: [], unexpectedDifferences: [] };
  const server = serve();
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  let browser;
  try {
    browser = await (ENGINE === "webkit" ? webkit : chromium).launch({ headless: true });
    const comparisonPage = await browser.newPage();
    for (const viewport of VIEWPORTS) {
      const baseline = await recordVariant(browser, port, "legacy", viewport);
      const react = await recordVariant(browser, port, "react", viewport);
      report.recordings.push(viewport.name + "-legacy.webm", viewport.name + "-react.webm");
      for (const step of STEPS) {
        const a = baseline.steps[step], b = react.steps[step];
        assert(a && b, "missing step " + step);
        const keys = ["day", "done", "values", "inputs", "padOpen", "field", "draft", "dirty", "transfer"];
        for (const key of keys) {
          const same = JSON.stringify(a[key]) === JSON.stringify(b[key]);
          report.checks.push({ viewport: viewport.name, step, kind: "state:" + key, pass: same });
          if (!same) report.unexpectedDifferences.push({ viewport: viewport.name, step, kind: "state:" + key, legacy: a[key], react: b[key] });
        }
        // Absolute main.scrollTop can differ because the two visual headers reserve
        // different non-content space. The safety contract is NO EXTRA JUMP during
        // switching/editing, assessed relative to the current open/closed phase.
        const scrollAnchor = ["pair-wdh", "remaining-kg", "manual-zero"].includes(step)
          ? "pair-kg"
          : ["cancelled", "saved-zero"].includes(step) ? "pair-complete" : null;
        for (const axis of ["windowY", "mainTop"]) {
          const absoluteDelta = Math.abs(a.scroll[axis] - b.scroll[axis]);
          if (!scrollAnchor) {
            report.checks.push({ viewport: viewport.name, step, kind: "scroll-base:" + axis,
              pass: true, absoluteDelta, policy: "observed-only on open/close transition" });
            continue;
          }
          const aMove = a.scroll[axis] - baseline.steps[scrollAnchor].scroll[axis];
          const bMove = b.scroll[axis] - react.steps[scrollAnchor].scroll[axis];
          const jumpDelta = Math.abs(aMove - bMove);
          report.checks.push({ viewport: viewport.name, step, kind: "scroll-jump:" + axis,
            pass: jumpDelta <= 2, jumpDelta, legacyMove: aMove, reactMove: bMove });
          if (jumpDelta > 2) report.unexpectedDifferences.push({
            viewport: viewport.name, step, kind: "scroll-jump:" + axis, jumpDelta, legacyMove: aMove, reactMove: bMove
          });
        }
        if (a.padOpen && b.padOpen) {
          for (const part of ["keys", "actions"]) {
            const x = a.geometry[part], y = b.geometry[part];
            const sameShape = x && y && ["left", "top", "width", "height"].every(k => Math.abs(x[k] - y[k]) <= 2);
            report.checks.push({ viewport: viewport.name, step, kind: "geometry:" + part, pass: !!sameShape });
            if (!sameShape) report.unexpectedDifferences.push({ viewport: viewport.name, step, kind: "geometry:" + part, legacy: x, react: y });
            const diff = await pixelDifference(comparisonPage,
              path.join(OUT, viewport.name + "-legacy-" + step + "-" + part + ".png"),
              path.join(OUT, viewport.name + "-react-" + step + "-" + part + ".png"));
            const equal = diff.dimensionsMatch && diff.ratio <= 0.01;
            report.checks.push({ viewport: viewport.name, step, kind: "pixel:" + part, pass: equal, diff });
            if (!equal) report.unexpectedDifferences.push({ viewport: viewport.name, step, kind: "pixel:" + part, diff });
          }
        }
      }
      assert(baseline.consoleErrors.length === 0 && react.consoleErrors.length === 0, "unexpected runtime errors");
    }
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
