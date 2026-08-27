#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const GUARD = path.join(
  ROOT,
  "android-wrapper",
  "app",
  "src",
  "preview",
  "assets",
  "android",
  "kgg_device_test_runtime_guard.js",
);

function fail(message) {
  throw new Error(message);
}

function main() {
  const source = fs.readFileSync(GUARD, "utf8");
  let status = {
    previewChannel: true,
    rolloutCode: 101,
    releaseId: "apk-context-a",
    pendingHealthCheck: false,
  };
  let nativeBeginCalls = 0;
  let nativeContext = null;

  const window = {
    KGGAndroidApp: {
      updateStatus: () => JSON.stringify(status),
    },
    KGGDeviceTestStationNative: {
      getDeviceInfo: () => JSON.stringify({ class: "android-tablet" }),
      beginSession: (runtimeContextJson) => {
        nativeBeginCalls += 1;
        nativeContext = JSON.parse(runtimeContextJson);
        return JSON.stringify({
          ok: true,
          sessionId: nativeContext.sessionId,
          previewRequestId: nativeContext.requestId,
          jobHash: nativeContext.jobHash,
          profile: nativeContext.profile,
        });
      },
      endSession: () => JSON.stringify({ ok: true }),
      openReportIssue: () => true,
    },
  };

  vm.runInNewContext(source, { window, JSON, String, Number, Object, Array, Error }, { filename: GUARD });
  const bridge = window.KGGDeviceTestStation;
  if (!bridge || typeof bridge.beginSession !== "function") fail("runtime guard did not expose station bridge");

  const runtimeB = {
    kind: "kgg_device_test_runtime_context",
    schemaVersion: 1,
    requestId: "preview-job-b",
    sourceSha: "b".repeat(40),
    patchHash: "c".repeat(64),
    jobUrl: "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/preview-job-b/job.json",
    rolloutCode: 202,
    sessionId: "kgg-test-" + "d".repeat(32),
    jobHash: "e".repeat(64),
    patientPwaUrl: "https://kayus24.github.io/kgg-patient-preview/device-test/",
    profile: "quick",
  };

  let result = JSON.parse(bridge.beginSession(JSON.stringify(runtimeB)));
  if (result.ok !== false || result.error !== "preview_html_not_current") fail("stale loaded HTML A was not blocked");
  if (nativeBeginCalls !== 0) fail("native session started while HTML A was still loaded");

  status = {
    previewChannel: true,
    rolloutCode: runtimeB.rolloutCode,
    releaseId: runtimeB.requestId,
    pendingHealthCheck: true,
  };
  result = JSON.parse(bridge.beginSession(JSON.stringify(runtimeB)));
  if (result.ok !== false || result.error !== "preview_html_not_healthy") fail("pending B health check was not blocked");
  if (nativeBeginCalls !== 0) fail("native session started before B became healthy");

  status.pendingHealthCheck = false;
  result = JSON.parse(bridge.beginSession(JSON.stringify(runtimeB)));
  if (!result.ok) fail("current healthy HTML B was rejected");
  if (nativeBeginCalls !== 1) fail("native session was not started exactly once for B");
  if (!nativeContext || nativeContext.requestId !== runtimeB.requestId) fail("native bridge did not receive request B");
  if (nativeContext.sourceSha !== runtimeB.sourceSha) fail("native bridge did not receive source SHA B");
  if (nativeContext.sessionId !== runtimeB.sessionId) fail("native bridge did not receive session B");
  if (nativeContext.jobHash !== runtimeB.jobHash) fail("native bridge did not receive job hash B");
  if (nativeContext.jobUrl !== runtimeB.jobUrl) fail("native bridge did not receive job URL B");
  if (nativeContext.profile !== runtimeB.profile) fail("native bridge did not receive profile B");
  if (Number(nativeContext.rolloutCode) !== runtimeB.rolloutCode) fail("native bridge did not receive rollout B");

  console.log(JSON.stringify({
    ok: true,
    suite: "persistent-runtime-guard",
    staleHtmlBlocked: true,
    pendingHealthBlocked: true,
    activeRequest: nativeContext.requestId,
    activeSourceSha: nativeContext.sourceSha,
    activeSessionId: nativeContext.sessionId,
    activeJobHash: nativeContext.jobHash,
    activeJobUrl: nativeContext.jobUrl,
    activeProfile: nativeContext.profile,
    activeRollout: nativeContext.rolloutCode,
  }));
}

try {
  main();
} catch (error) {
  console.error("ERROR: " + (error && error.stack ? error.stack : String(error)));
  process.exit(1);
}
