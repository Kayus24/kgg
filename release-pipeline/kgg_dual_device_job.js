#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const fixtures = require(path.join(
  __dirname,
  "..",
  "android-wrapper",
  "app",
  "src",
  "preview",
  "assets",
  "android",
  "kgg_dual_device_fixtures.js",
));

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (key === "--self-test") {
      result.selfTest = true;
      continue;
    }
    if (!key.startsWith("--") || index + 1 >= argv.length) fail("Ungültiges Argument: " + key);
    result[key.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = argv[++index];
  }
  return result;
}

function boundedText(value, pattern, label) {
  const clean = String(value || "").trim();
  if (!pattern.test(clean)) fail(label + " ist ungültig");
  return clean;
}

function buildJob(args) {
  const createdAt = args.createdAt || new Date().toISOString();
  const expiresAt = args.expiresAt || new Date(Date.parse(createdAt) + 48 * 60 * 60 * 1000).toISOString();
  const profile = args.profile === "full" ? "full" : "quick";
  const job = {
    kind: fixtures.jobKind,
    schemaVersion: 1,
    sessionId: boundedText(args.sessionId, /^kgg-test-[a-f0-9]{32}$/, "sessionId"),
    requestId: boundedText(args.requestId, /^[a-z0-9][a-z0-9-]{5,63}$/, "requestId"),
    sourceSha: boundedText(args.sourceSha, /^[a-f0-9]{40}$/, "sourceSha"),
    patchHash: boundedText(args.patchHash, /^[a-f0-9]{64}$/, "patchHash"),
    jobHash: "0".repeat(64),
    patientPwaUrl: String(args.patientPwaUrl || ""),
    profile,
    recipeVersion: fixtures.version,
    createdAt,
    expiresAt,
    fixtures: fixtures.fixturesForProfile(profile),
    syntheticOnly: true,
  };
  job.jobHash = crypto.createHash("sha256").update(fixtures.jobHashInput(job), "utf8").digest("hex");
  fixtures.validateJob(job);
  return job;
}

function selfTest() {
  const job = buildJob({
    sessionId: "kgg-test-" + "a".repeat(32),
    requestId: "dual-device-job-self-test",
    sourceSha: "b".repeat(40),
    patchHash: "c".repeat(64),
    patientPwaUrl: "https://kayus24.github.io/kgg-patient-preview/device-test/",
    profile: "quick",
    createdAt: new Date(Date.now() - 60_000).toISOString(),
    expiresAt: new Date(Date.now() + 60_000).toISOString(),
  });
  if (job.fixtures.length !== 6) fail("Quick-Profil hat eine unerwartete Fixture-Anzahl");
  if (job.fixtures.find((item) => item.fixtureId === "h3-20-normal").exerciseCount !== 20) fail("Vollplan-Fixture fehlt");
  const tampered = JSON.parse(JSON.stringify(job));
  tampered.fixtures[0].exerciseCount = 2;
  try {
    fixtures.validateJob(tampered);
    fail("Manipuliertes Job-Manifest wurde akzeptiert");
  } catch (error) {
    if (/Manipuliertes/.test(String(error && error.message))) throw error;
  }
  console.log(JSON.stringify({ ok: true, suite: "dual-device-job", jobHash: job.jobHash, fixtures: job.fixtures.length }));
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.selfTest) return selfTest();
  if (!args.output) fail("--output fehlt");
  const job = buildJob(args);
  const output = path.resolve(args.output);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(job, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({ ok: true, output, sessionId: job.sessionId, jobHash: job.jobHash, profile: job.profile }));
}

try {
  main();
} catch (error) {
  console.error("ERROR: " + (error && error.message ? error.message : String(error)));
  process.exit(1);
}
