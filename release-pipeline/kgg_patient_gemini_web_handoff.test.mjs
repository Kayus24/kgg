import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  prepareWebHandoff, finalizeWebHandoff, unavailableWebHandoff
} from "./kgg_patient_gemini_web_handoff.mjs";

const SHA = "a".repeat(40);
function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "kgg-video-web-"));
  const dir = path.join(root, "patient-ui-parity");
  fs.mkdirSync(dir);
  const checks = [{ pass: true, name: "synthetic-state-check" }];
  const steps = { "pair-kg": { elapsedMs: 3100 }, "pair-wdh": { elapsedMs: 4200 } };
  const report = {
    schema: 1, syntheticOnly: true, engine: "chromium", status: "PASS",
    candidateSha: SHA, gitSha: SHA, checks, unexpectedDifferences: [],
    variants: [
      { mode: "legacy", viewport: "phone", steps },
      { mode: "react", viewport: "phone", steps }
    ]
  };
  fs.writeFileSync(path.join(dir, "report.json"), JSON.stringify(report));
  for (const mode of ["legacy", "react"]) {
    fs.writeFileSync(path.join(dir, "phone-" + mode + ".webm"),
      Buffer.concat([Buffer.from("1a45dfa3", "hex"), Buffer.from("synthetic-video-" + mode)]));
  }
  return { dir, report, cleanup: () => fs.rmSync(root, { recursive: true, force: true }) };
}
const rawResponse = (overrides = {}) => JSON.stringify({
  verdict: "no_unexpected_difference", confidence: "medium",
  expectedDifferences: ["React header"], findings: [], ...overrides
});
function observation(raw = rawResponse()) {
  return {
    observedModel: "Gemini 3.1 Pro", thinkingLabel: "Pro · Erweitert",
    uploadVisible: { legacy: true, react: true },
    generationObserved: true, generationStopped: true,
    startedAt: "2026-10-12T10:00:00.000Z",
    stoppedAt: "2026-10-12T10:00:20.000Z",
    responseSnapshots: [
      { observedAt: "2026-10-12T10:00:22.000Z", text: raw },
      { observedAt: "2026-10-12T10:00:24.200Z", text: raw }
    ]
  };
}
function withFixture(fn) {
  const f = fixture();
  try { return fn(f); } finally { f.cleanup(); }
}
test("prepare: synthetic verified SHA, video hashes, timestamps and browser-only workflow", () =>
  withFixture(({ dir }) => {
    const p = prepareWebHandoff(dir, SHA);
    assert.equal(p.sourceSha, SHA);
    assert.equal(p.videos.legacy.sha256.length, 64);
    assert.equal(p.timing.react["pair-wdh"], 4.2);
    assert.equal(p.instructions.browserMcp, "fahrklar_gemini_web");
    assert.match(p.prompt, /unexpected field-selection/);
    assert.doesNotMatch(JSON.stringify(p), /GEMINI_API_KEY|apiKey|bearer/i);
  }));
test("prepare: wrong source SHA rejected", () =>
  withFixture(({ dir }) =>
    assert.throws(() => prepareWebHandoff(dir, "b".repeat(40)), /Candidate SHA/)));
test("prepare: missing or non-synthetic parity rejected", () =>
  withFixture(({ dir, report }) => {
    report.syntheticOnly = false;
    fs.writeFileSync(path.join(dir, "report.json"), JSON.stringify(report));
    assert.throws(() => prepareWebHandoff(dir, SHA), /synthetic-only/);
  }));
test("prepare: deterministic failing state rejected", () =>
  withFixture(({ dir, report }) => {
    report.checks.push({ pass: false });
    fs.writeFileSync(path.join(dir, "report.json"), JSON.stringify(report));
    assert.throws(() => prepareWebHandoff(dir, SHA), /Deterministic check/);
  }));
test("prepare: spoofed or missing WebM rejected", () =>
  withFixture(({ dir }) => {
    fs.writeFileSync(path.join(dir, "phone-react.webm"), Buffer.from("not-a-webm"));
    assert.throws(() => prepareWebHandoff(dir, SHA), /WebM/);
  }));
test("finalize: stable observed model and response yield only advisory PASS", () =>
  withFixture(({ dir }) => {
    const result = finalizeWebHandoff(prepareWebHandoff(dir, SHA), observation());
    assert.equal(result.status, "PASS");
    assert.equal(result.advisoryOnly, true);
    assert.equal(result.sourceSha, SHA);
    assert.ok(result.notCovered.includes("physical Oppo"));
  }));
test("finalize: any changed video fails hash binding", () =>
  withFixture(({ dir }) => {
    const prepared = prepareWebHandoff(dir, SHA);
    fs.appendFileSync(path.join(dir, "phone-legacy.webm"), "mutation");
    assert.throws(() => finalizeWebHandoff(prepared, observation()), /Evidence changed/);
  }));
test("finalize: no verified Gemini model fails closed", () =>
  withFixture(({ dir }) => {
    const obs = observation();
    obs.observedModel = "Gemini Flash";
    assert.throws(() => finalizeWebHandoff(prepareWebHandoff(dir, SHA), obs), /model\/upload/);
  }));
test("finalize: missing upload or generation evidence fails closed", () =>
  withFixture(({ dir }) => {
    const obs = observation();
    obs.uploadVisible.react = false;
    assert.throws(() => finalizeWebHandoff(prepareWebHandoff(dir, SHA), obs), /completion/);
    obs.uploadVisible.react = true;
    obs.generationStopped = false;
    assert.throws(() => finalizeWebHandoff(prepareWebHandoff(dir, SHA), obs), /completion/);
  }));
test("finalize: response must be stable twice 2s apart", () =>
  withFixture(({ dir }) => {
    const obs = observation();
    obs.responseSnapshots[1].observedAt = "2026-10-12T10:00:22.500Z";
    assert.throws(() => finalizeWebHandoff(prepareWebHandoff(dir, SHA), obs), /stably/);
    obs.responseSnapshots[1].observedAt = "2026-10-12T10:00:25.000Z";
    obs.responseSnapshots[1].text = rawResponse({ confidence: "high" });
    assert.throws(() => finalizeWebHandoff(prepareWebHandoff(dir, SHA), obs), /stably/);
  }));
test("finalize: bad JSON, contradictory verdict and extra keys fail", () =>
  withFixture(({ dir }) => {
    const p = prepareWebHandoff(dir, SHA);
    assert.throws(() => finalizeWebHandoff(p, observation("unstructured prose")), /JSON/);
    assert.throws(() => finalizeWebHandoff(p, observation(rawResponse({
      findings: [{ step: "kg", timestampLegacy: "00:04", timestampReact: "00:04",
        severity: "major", description: "Pad disappeared" }]
    }))), /conflict/);
    assert.throws(() => finalizeWebHandoff(p, observation(rawResponse({ injected: true }))), /keys/);
  }));
test("finalize: suspicious visible finding becomes REVIEW_REQUIRED, never auto-pass", () =>
  withFixture(({ dir }) => {
    const finding = { step: "pair-wdh", timestampLegacy: "00:04",
      timestampReact: "00:05", severity: "major", description: "Pad closes unexpectedly" };
    const raw = rawResponse({ verdict: "suspected_regression", findings: [finding] });
    const result = finalizeWebHandoff(prepareWebHandoff(dir, SHA), observation(raw));
    assert.equal(result.status, "REVIEW_REQUIRED");
    assert.equal(result.findings[0].severity, "major");
  }));
test("finalize: low confidence and inconclusive remain INCONCLUSIVE", () =>
  withFixture(({ dir }) => {
    const p = prepareWebHandoff(dir, SHA);
    assert.equal(finalizeWebHandoff(p, observation(rawResponse({ confidence: "low" }))).status,
      "INCONCLUSIVE");
    assert.equal(finalizeWebHandoff(p, observation(rawResponse({ verdict: "inconclusive" }))).status,
      "INCONCLUSIVE");
  }));
test("unavailable: login, quota and tool errors are never PASS", () =>
  withFixture(({ dir }) => {
    const p = prepareWebHandoff(dir, SHA);
    for (const reason of ["LOGIN_REQUIRED", "QUOTA", "TIMEOUT"]) {
      assert.equal(unavailableWebHandoff(p, reason).status, "UNAVAILABLE");
    }
    assert.throws(() => unavailableWebHandoff(p, "all good"), /Invalid unavailable/);
  }));

import { execFileSync } from "node:child_process";
const renderer = path.resolve("release-pipeline/kgg_patient_ui_parity_report.mjs");
test("offline gallery includes verified advisory status and escapes Gemini findings", () =>
  withFixture(({ dir }) => {
    fs.writeFileSync(path.join(dir, "gemini-web-review.json"), JSON.stringify({
      advisoryOnly: true, reviewer: "gemini-web", sourceSha: SHA,
      status: "REVIEW_REQUIRED",
      findings: [{ step: "kg", timestampLegacy: "00:05", timestampReact: "00:05",
        description: "<script>alert(1)</script>" }]
    }));
    execFileSync(process.execPath, [renderer, dir], { encoding: "utf8" });
    const html = fs.readFileSync(path.join(dir, "report.html"), "utf8");
    assert.match(html, /Status: REVIEW_REQUIRED/);
    assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
    assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  }));
test("offline gallery never trusts web PASS from a different candidate", () =>
  withFixture(({ dir }) => {
    fs.writeFileSync(path.join(dir, "gemini-web-review.json"), JSON.stringify({
      advisoryOnly: true, reviewer: "gemini-web", sourceSha: "b".repeat(40),
      status: "PASS", findings: []
    }));
    execFileSync(process.execPath, [renderer, dir], { encoding: "utf8" });
    const html = fs.readFileSync(path.join(dir, "report.html"), "utf8");
    assert.match(html, /Status: INCONCLUSIVE/);
    assert.doesNotMatch(html, /Status: PASS/);
  }));
