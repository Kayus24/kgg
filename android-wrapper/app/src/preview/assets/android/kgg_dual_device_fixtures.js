(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.KGGDualDeviceFixtures = Object.freeze(api);
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var VERSION = "v404-dual-device-fixtures-1";
  var JOB_KIND = "kgg_dual_device_test_job";
  var JOB_SCHEMA = 1;
  var PAIR_KIND = "KGGTEST1";
  var FIXTURES = [
    { id: "h2-1-baseline", format: "KGGH2", exerciseCount: 1, required: true, variant: "normal", profiles: ["quick", "full"], importMode: "capture" },
    { id: "h2-7-legacy", format: "KGGH2", exerciseCount: 7, required: true, variant: "normal", profiles: ["quick", "full"], importMode: "capture" },
    { id: "h2-12-diagnostic", format: "KGGH2", exerciseCount: 12, required: false, variant: "normal", profiles: ["full"], importMode: "capture" },
    { id: "h2-20-diagnostic", format: "KGGH2", exerciseCount: 20, required: false, variant: "normal", profiles: ["full"], importMode: "capture" },
    { id: "h3-7-normal", format: "KGGH3", exerciseCount: 7, required: true, variant: "normal", profiles: ["quick", "full"], importMode: "product" },
    { id: "h3-12-normal", format: "KGGH3", exerciseCount: 12, required: true, variant: "normal", profiles: ["quick", "full"], importMode: "capture" },
    { id: "h3-20-normal", format: "KGGH3", exerciseCount: 20, required: true, variant: "normal", profiles: ["quick", "full"], importMode: "capture" },
    { id: "h3-20-far-angle", format: "KGGH3", exerciseCount: 20, required: true, variant: "far-angle", profiles: ["quick", "full"], importMode: "capture" },
    { id: "h3-20-low-contrast", format: "KGGH3", exerciseCount: 20, required: true, variant: "low-contrast", profiles: ["full"], importMode: "capture" },
    { id: "h3-20-photo", format: "KGGH3", exerciseCount: 20, required: true, variant: "photo", profiles: ["full"], importMode: "capture" }
  ];

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function stable(value) {
    if (Array.isArray(value)) return value.map(stable);
    if (value && typeof value === "object") {
      return Object.keys(value).sort().reduce(function (out, key) {
        out[key] = stable(value[key]);
        return out;
      }, {});
    }
    return value;
  }

  function stableJson(value) {
    return JSON.stringify(stable(value));
  }

  function fnv1a(value) {
    var text = String(value || "");
    var hash = 2166136261;
    for (var index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16).padStart(8, "0");
  }

  function planFingerprint(raw) {
    return fnv1a(stableJson(raw));
  }

  function exerciseName(index, count) {
    var number = String(index + 1).padStart(2, "0");
    if (index === 0) return "SENTINEL-FIRST-" + String(count).padStart(2, "0");
    if (index === Math.floor((count - 1) / 2)) return "SENTINEL-MIDDLE-" + String(count).padStart(2, "0");
    if (index === count - 1) return "SENTINEL-LAST-" + String(count).padStart(2, "0");
    return "SYNTHETIC-EXERCISE-" + number + "-OF-" + String(count).padStart(2, "0");
  }

  function syntheticPlan(fixture) {
    var count = Number(fixture && fixture.exerciseCount);
    if (!Number.isInteger(count) || count < 1 || count > 40) throw new Error("fixture_exercise_count_invalid");
    var exercises = [];
    for (var index = 0; index < count; index += 1) {
      exercises.push([
        exerciseName(index, count),
        3,
        index % 2 ? "B" : "LR",
        index % 3 ? "kg" : "Stufe",
        "Wdh",
        String(10 + index),
        String(12 + (index % 4)),
        "",
        "",
        "Video öffnen",
        "exercise"
      ]);
    }
    return {
      i: "synthetic-" + String(fixture.format || "KGGH3").toLowerCase() + "-" + count + "-v404",
      t: "Synthetischer QR-Test " + count,
      v: 404,
      d: 6,
      extendDays: true,
      stepDays: 6,
      m: { synthetic: true, recipe: VERSION },
      e: exercises
    };
  }

  function orderDigest(raw) {
    var names = raw && Array.isArray(raw.e) ? raw.e.map(function (exercise) {
      return Array.isArray(exercise) ? String(exercise[0] || "") : "";
    }) : [];
    return fnv1a(names.join("\u001f"));
  }

  function fixtureContract(fixture) {
    var raw = syntheticPlan(fixture);
    return {
      fixtureId: fixture.id,
      format: fixture.format,
      exerciseCount: fixture.exerciseCount,
      required: !!fixture.required,
      displayVariant: fixture.variant,
      importMode: fixture.importMode,
      expectedFingerprint: planFingerprint(raw),
      expectedOrderDigest: orderDigest(raw)
    };
  }

  function fixturesForProfile(profile) {
    var selected = profile === "full" ? "full" : "quick";
    return FIXTURES.filter(function (fixture) {
      return fixture.profiles.indexOf(selected) !== -1;
    }).map(fixtureContract);
  }

  function fixtureById(id) {
    for (var index = 0; index < FIXTURES.length; index += 1) {
      if (FIXTURES[index].id === id) return clone(FIXTURES[index]);
    }
    return null;
  }

  function bytesToBase64Url(bytes) {
    var binary = "";
    for (var index = 0; index < bytes.length; index += 0x8000) {
      binary += String.fromCharCode.apply(null, bytes.subarray(index, index + 0x8000));
    }
    if (typeof btoa === "function") return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
    return Buffer.from(bytes).toString("base64url");
  }

  function base64UrlToBytes(value) {
    var clean = String(value || "");
    if (!clean || clean.length > 4096 || !/^[A-Za-z0-9_-]+$/.test(clean)) throw new Error("pair_token_invalid");
    if (typeof atob === "function") {
      var padded = clean.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - clean.length % 4) % 4);
      var binary = atob(padded);
      var bytes = new Uint8Array(binary.length);
      for (var index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
      return bytes;
    }
    return new Uint8Array(Buffer.from(clean, "base64url"));
  }

  function utf8Encode(value) {
    if (typeof TextEncoder === "function") return new TextEncoder().encode(String(value));
    return new Uint8Array(Buffer.from(String(value), "utf8"));
  }

  function utf8Decode(value) {
    if (typeof TextDecoder === "function") return new TextDecoder("utf-8", { fatal: true }).decode(value);
    return Buffer.from(value).toString("utf8");
  }

  function encodePairing(pairing) {
    return PAIR_KIND + ":" + bytesToBase64Url(utf8Encode(stableJson(pairing)));
  }

  function decodePairing(value) {
    var match = String(value || "").match(/^KGGTEST1:([A-Za-z0-9_-]+)$/);
    if (!match) throw new Error("pair_prefix_invalid");
    var parsed = JSON.parse(utf8Decode(base64UrlToBytes(match[1])));
    validatePairing(parsed);
    return parsed;
  }

  function safeUrl(value, label) {
    var parsed;
    try { parsed = new URL(String(value || "")); } catch (error) { throw new Error(label + "_invalid"); }
    if (parsed.protocol !== "https:") throw new Error(label + "_https_required");
    if (parsed.username || parsed.password || parsed.hash) throw new Error(label + "_unsafe");
    return parsed.href;
  }

  function validatePairing(pairing) {
    if (!pairing || typeof pairing !== "object" || Array.isArray(pairing)) throw new Error("pair_object_invalid");
    if (pairing.kind !== PAIR_KIND || pairing.schemaVersion !== 1) throw new Error("pair_schema_invalid");
    if (!/^kgg-test-[a-f0-9]{32}$/.test(String(pairing.sessionId || ""))) throw new Error("pair_session_invalid");
    if (!/^[a-z0-9][a-z0-9-]{5,63}$/.test(String(pairing.requestId || ""))) throw new Error("pair_request_invalid");
    if (!/^[a-f0-9]{64}$/.test(String(pairing.jobHash || ""))) throw new Error("pair_job_hash_invalid");
    if (!/^[a-f0-9]{40}$/.test(String(pairing.sourceSha || ""))) throw new Error("pair_source_sha_invalid");
    if (pairing.profile !== "quick" && pairing.profile !== "full") throw new Error("pair_profile_invalid");
    safeUrl(pairing.jobUrl, "pair_job_url");
    safeUrl(pairing.patientPwaUrl, "pair_pwa_url");
    return pairing;
  }

  function validateJob(job) {
    if (!job || typeof job !== "object" || Array.isArray(job)) throw new Error("job_object_invalid");
    var keys = Object.keys(job).sort();
    var expected = ["createdAt", "expiresAt", "fixtures", "jobHash", "kind", "patchHash", "patientPwaUrl", "profile", "recipeVersion", "requestId", "schemaVersion", "sessionId", "sourceSha", "syntheticOnly"].sort();
    if (keys.join("|") !== expected.join("|")) throw new Error("job_fields_invalid");
    if (job.kind !== JOB_KIND || job.schemaVersion !== JOB_SCHEMA || job.syntheticOnly !== true) throw new Error("job_schema_invalid");
    if (!/^kgg-test-[a-f0-9]{32}$/.test(String(job.sessionId || ""))) throw new Error("job_session_invalid");
    if (!/^[a-z0-9][a-z0-9-]{5,63}$/.test(String(job.requestId || ""))) throw new Error("job_request_invalid");
    if (!/^[a-f0-9]{40}$/.test(String(job.sourceSha || ""))) throw new Error("job_source_invalid");
    if (!/^[a-f0-9]{64}$/.test(String(job.patchHash || "")) || !/^[a-f0-9]{64}$/.test(String(job.jobHash || ""))) throw new Error("job_hash_invalid");
    if (job.profile !== "quick" && job.profile !== "full") throw new Error("job_profile_invalid");
    if (job.recipeVersion !== VERSION) throw new Error("job_recipe_invalid");
    safeUrl(job.patientPwaUrl, "job_pwa_url");
    var created = Date.parse(job.createdAt), expires = Date.parse(job.expiresAt);
    if (!Number.isFinite(created) || !Number.isFinite(expires) || expires <= created || expires - created > 14 * 86400000) throw new Error("job_expiry_invalid");
    if (Date.now() > expires) throw new Error("job_expired");
    if (!Array.isArray(job.fixtures) || !job.fixtures.length || job.fixtures.length > FIXTURES.length) throw new Error("job_fixtures_invalid");
    var canonical = fixturesForProfile(job.profile);
    if (stableJson(job.fixtures) !== stableJson(canonical)) throw new Error("job_fixture_contract_mismatch");
    return job;
  }

  function jobHashInput(job) {
    var copy = clone(job);
    delete copy.jobHash;
    return stableJson(copy);
  }

  async function sha256Hex(value) {
    if (typeof crypto !== "undefined" && crypto.subtle) {
      var digest = await crypto.subtle.digest("SHA-256", utf8Encode(value));
      return Array.from(new Uint8Array(digest)).map(function (byte) { return byte.toString(16).padStart(2, "0"); }).join("");
    }
    if (typeof require === "function") return require("crypto").createHash("sha256").update(String(value), "utf8").digest("hex");
    throw new Error("sha256_unavailable");
  }

  async function verifyJobHash(job) {
    validateJob(job);
    return (await sha256Hex(jobHashInput(job))) === job.jobHash;
  }

  return {
    version: VERSION,
    jobKind: JOB_KIND,
    pairingKind: PAIR_KIND,
    definitions: clone(FIXTURES),
    fixtureById: fixtureById,
    fixturesForProfile: fixturesForProfile,
    syntheticPlan: syntheticPlan,
    planFingerprint: planFingerprint,
    orderDigest: orderDigest,
    stableJson: stableJson,
    encodePairing: encodePairing,
    decodePairing: decodePairing,
    validatePairing: validatePairing,
    validateJob: validateJob,
    jobHashInput: jobHashInput,
    sha256Hex: sha256Hex,
    verifyJobHash: verifyJobHash
  };
});
