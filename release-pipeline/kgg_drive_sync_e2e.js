#!/usr/bin/env node
'use strict';

// Synthetic HTML integration test. The NativeSync transport is injected and is
// explicitly a filesystem-test adapter, never an Android/SAF certification.
// --prepare/--self-test do not launch a browser or touch the Drive folder.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');
const assert = require('assert/strict');
const cp = require('child_process');
const { performance } = require('node:perf_hooks');

const ROOT = path.resolve(__dirname, '..');
const OUTPUT_ROOT = path.join(ROOT, 'output', 'drive-sync-e2e-20261015');
// Loopback remains a secure context for the existing WebCrypto/image pipeline.
// Playwright fulfills every request; nothing listens on this port.
const BASE_URL = 'http://127.0.0.1:37843';
const MAX_BYTES = 8_000_000;
const POLL_MS = 15_000;
const ADAPTER_DELAY_MS = 65;
const DEVICE_A = 'synthetic_drive_a_20261015';
const DEVICE_B = 'synthetic_drive_b_20261015';
const ROOM = 'synthetic_drive_room_20261015';
const PATIENT_SENTINEL = 'SYNTHETIC_PATIENT_EXCLUDE_20261015';
const SECRET_SENTINEL = 'SYNTHETIC_SECRET_EXCLUDE_20261015';
const STATE_KEY = 'kgg_html_app_v2_state';
const BANK_KEY = 'kgg_html_app_v2_custom_exercise_bank';
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const json = value => Buffer.from(JSON.stringify(value, null, 2) + '\n', 'utf8');

function args(argv) {
  const out = { mode: '', runId: 'run-20261015', round: 1, cloudHold: false, cloudWaitMs: 600_000, resetOwned: false, driveDir: '', cloudFolderId: '', uiDelayProbeMs: 0 };
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (['--prepare', '--run', '--self-test'].includes(key)) {
      assert(!out.mode, 'select exactly one mode'); out.mode = key.slice(2);
    } else if (key === '--run-id') out.runId = argv[++i];
    else if (key === '--drive-dir') out.driveDir = argv[++i];
    else if (key === '--cloud-folder-id') out.cloudFolderId = argv[++i];
    else if (key === '--round') out.round = Number(argv[++i]);
    else if (key === '--cloud-hold') out.cloudHold = true;
    else if (key === '--reset-owned') out.resetOwned = true;
    else if (key === '--cloud-wait-ms') out.cloudWaitMs = Number(argv[++i]);
    else if (key === '--ui-delay-probe-ms') out.uiDelayProbeMs = Number(argv[++i]);
    else if (key === '--help' || key === '-h') out.help = true;
    else throw new Error('unsupported argument: ' + key);
  }
  assert(/^[A-Za-z0-9][A-Za-z0-9._-]{0,70}$/.test(out.runId), 'invalid run-id');
  assert([1, 2].includes(out.round), 'round must be 1 or 2');
  assert(Number.isInteger(out.cloudWaitMs) && out.cloudWaitMs >= 10_000 && out.cloudWaitMs <= 1_800_000, 'cloud wait must be 10s..30min');
  assert(Number.isInteger(out.uiDelayProbeMs) && out.uiDelayProbeMs >= 0 && out.uiDelayProbeMs <= 2000, 'UI delay probe must be 0..2000ms');
  if (out.uiDelayProbeMs) assert(!out.driveDir && !out.cloudHold, 'UI delay probe is restricted to the local synthetic transport');
  assert(!(out.cloudHold && out.round !== 1), 'cloud hold is for round 1');
  if (out.driveDir) assert(path.isAbsolute(out.driveDir), 'drive-dir must be an explicit absolute path');
  if (out.cloudFolderId) assert(/^[A-Za-z0-9_-]{10,100}$/.test(out.cloudFolderId), 'invalid cloud folder ID');
  if (out.cloudHold) assert(out.driveDir && out.cloudFolderId, 'cloud hold requires explicit drive-dir and cloud-folder-id');
  return out;
}

function inside(root, target) {
  const relative = path.relative(path.resolve(root), path.resolve(target));
  return relative !== '' && !relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative);
}

function outputPath(config, name) {
  assert(/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(name), 'invalid output name');
  const target = path.resolve(config.outputDir, name);
  assert(inside(OUTPUT_ROOT, target), 'output escaped owned directory');
  return target;
}

function makeConfig(options) {
  const suffix = options.round === 2 ? '-r2' : '';
  const outputDir = path.join(OUTPUT_ROOT, options.runId, 'round-' + options.round);
  return { schema: 'kgg-drive-sync-e2e/v1', runId: options.runId, round: options.round,
    driveDir: options.driveDir ? path.resolve(options.driveDir) : path.join(outputDir, 'transport'), cloudFolderId: options.cloudFolderId || null,
    externalDrive: !!options.driveDir, outputDir,
    files: { a: 'drive-a' + suffix + '.json', b: 'drive-b' + suffix + '.json' },
    deviceIds: { a: DEVICE_A, b: DEVICE_B }, roomId: ROOM, transport: 'filesystem-test',
    cloudHold: options.cloudHold, cloudWaitMs: options.cloudWaitMs, uiDelayProbeMs: options.uiDelayProbeMs };
}

function checkDrive(config) {
  if (config.externalDrive) assert(/^KGG_Sync_Test_\d{8}_\d{4}$/i.test(path.basename(config.driveDir)), 'external transport must be an explicitly named KGG_Sync_Test_YYYYMMDD_HHMM folder');
  else { assert(inside(config.outputDir, config.driveDir), 'local transport escaped owned output'); fs.mkdirSync(config.driveDir, { recursive: true }); }
  assert(fs.statSync(config.driveDir).isDirectory(), 'approved Drive folder is unavailable');
  const actual = fs.realpathSync(config.driveDir);
  assert.equal(path.resolve(actual).toLowerCase(), path.resolve(config.driveDir).toLowerCase(), 'transport root resolved elsewhere');
  const allowed = config.round === 2 ? ['drive-a-r2.json', 'drive-b-r2.json'] : ['drive-a.json', 'drive-b.json'];
  for (const client of ['a', 'b']) assert(allowed.includes(config.files[client]), 'unexpected peer file');
}

function drivePath(config, client) {
  assert(['a', 'b'].includes(client), 'invalid client');
  const target = path.resolve(config.driveDir, config.files[client]);
  assert(inside(config.driveDir, target), 'Drive path escaped approved folder');
  if (fs.existsSync(target)) assert(!fs.lstatSync(target).isSymbolicLink(), 'peer file must not be a symlink');
  return target;
}

function fileMeta(file) {
  if (!fs.existsSync(file)) return { exists: false };
  const bytes = fs.readFileSync(file);
  return { exists: true, bytes: bytes.length, sha256: hash(bytes), md5: crypto.createHash('md5').update(bytes).digest('hex') };
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let j = 0; j < 8; j++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function png(rgb) {
  const width = 40, height = 30;
  function chunk(type, data) {
    const tag = Buffer.from(type), length = Buffer.alloc(4), crc = Buffer.alloc(4);
    length.writeUInt32BE(data.length); crc.writeUInt32BE(crc32(Buffer.concat([tag, data])));
    return Buffer.concat([length, tag, data, crc]);
  }
  const header = Buffer.alloc(13); header.writeUInt32BE(width); header.writeUInt32BE(height, 4); header[8] = 8; header[9] = 2;
  const pixels = Buffer.alloc(height * (1 + width * 3));
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) for (let c = 0; c < 3; c++) pixels[y * (1 + width * 3) + 1 + x * 3 + c] = rgb[c];
  return Buffer.concat([Buffer.from('89504e470d0a1a0a', 'hex'), chunk('IHDR', header), chunk('IDAT', zlib.deflateSync(pixels)), chunk('IEND', Buffer.alloc(0))]);
}

function prepare(config) {
  fs.mkdirSync(config.outputDir, { recursive: true });
  const configFile = outputPath(config, 'config.json');
  if (fs.existsSync(configFile)) assert.deepEqual(JSON.parse(fs.readFileSync(configFile, 'utf8')), config, 'existing run config differs');
  else fs.writeFileSync(configFile, json(config), { flag: 'wx' });
  fs.writeFileSync(outputPath(config, 'image-red.png'), png([220, 30, 30]));
  fs.writeFileSync(outputPath(config, 'image-blue.png'), png([30, 50, 220]));
  return { config: configFile, transport: config.transport, driveFiles: config.files, browserStarted: false, driveWritten: false };
}

class DriveAdapter {
  constructor(config, report) {
    this.config = config; this.report = report; this.orderReversed = false; this.operationSequence = 0;
    this.state = { a: { readFail: false, writeFail: false, reads: 0, writes: 0, failures: 0, active: 0, maxActive: 0, documents: {} },
      b: { readFail: false, writeFail: false, reads: 0, writes: 0, failures: 0, active: 0, maxActive: 0, documents: {} } };
  }
  log(value) {
    const record = { at: new Date().toISOString(), ...value };
    this.report.transportEvents.push(record);
    fs.appendFileSync(outputPath(this.config, 'transport-events.jsonl'), JSON.stringify(record) + '\n');
  }
  async operation(client, operation, callback, documentId) {
    assert(typeof documentId === 'string' && documentId.startsWith(client + '-') && /^[a-z0-9-]{10,90}$/i.test(documentId), 'invalid synthetic document ID');
    const metadata = { client, documentId, operationId: ++this.operationSequence, method: operation };
    const state = this.state[client]; state.active++; state.maxActive = Math.max(state.maxActive, state.active);
    const document = state.documents[documentId] ||= { active: 0, maxActive: 0, reads: 0, writes: 0 };
    document.active++; document.maxActive = Math.max(document.maxActive, document.active); document[operation + 's']++;
    this.log({ ...metadata, operation: 'operation-start', active: state.active, documentActive: document.active });
    let success = false;
    try { await sleep(ADAPTER_DELAY_MS); const result = await callback(metadata); success = true; return result; }
    catch (error) { state.failures++; this.log({ ...metadata, operation, success: false, error: error.code || 'synthetic_transport_error' }); throw error; }
    finally { state.active--; document.active--; this.log({ ...metadata, operation: 'operation-end', success, active: state.active, documentActive: document.active }); }
  }
  async read(client, documentId) {
    return this.operation(client, 'read', metadata => {
      const state = this.state[client]; state.reads++;
      if (state.readFail) { const error = new Error('synthetic read failure'); error.code = 'synthetic_read_failure'; throw error; }
      let entries = ['a', 'b']; if (this.orderReversed) entries.reverse();
      const peers = [];
      for (const owner of entries) {
        const file = drivePath(this.config, owner);
        if (!fs.existsSync(file)) continue;
        const bytes = fs.readFileSync(file); assert(bytes.length <= MAX_BYTES, 'transport input exceeds bound');
        this.log({ ...metadata, operation: 'read-file', owner, file: this.config.files[owner], exists: true,
          bytes: bytes.length, sha256: hash(bytes), md5: crypto.createHash('md5').update(bytes).digest('hex'), success: true });
        peers.push(JSON.parse(bytes.toString('utf8')));
      }
      return { kind: 'kgg_cross_data_safe_sync_mesh', version: 1, roomId: ROOM, peers };
    }, documentId);
  }
  async write(client, document, documentId) {
    return this.operation(client, 'write', metadata => {
      const state = this.state[client];
      if (state.writeFail) { const error = new Error('synthetic write failure'); error.code = 'synthetic_write_failure'; throw error; }
      this.assertExport(document, client);
      this.replace(client, document, 'app', metadata); state.writes++; return true;
    }, documentId);
  }
  assertExport(document, client) {
    assert.equal(document.kind, 'kgg_cross_data_safe_sync', 'unexpected exported kind');
    assert.equal(document.version, 2, 'unexpected exported version');
    assert.equal(document.roomId, ROOM, 'unexpected exported room');
    assert.equal(document.origin.deviceId, this.config.deviceIds[client], 'client wrote another origin');
    for (const field of ['patients', 'secrets', 'debugPayloads', 'rawData']) assert.equal(document.privacy[field], false, 'privacy policy mismatch');
    assert.equal((document.packages || []).length, 0, 'plan packages leaked into automatic sync');
    const raw = JSON.stringify(document); assert(!raw.includes(PATIENT_SENTINEL), 'synthetic patient sentinel exported');
    assert(!raw.includes(SECRET_SENTINEL), 'synthetic secret sentinel exported');
    assert(Buffer.byteLength(raw) <= MAX_BYTES, 'export exceeds byte bound');
    const forbidden = /patient|secret|token|apikey|api_key|rawpayload|qrraw/i;
    function visit(value, route = '') {
      if (!value || typeof value !== 'object') return;
      for (const [key, entry] of Object.entries(value)) {
        if (route !== 'privacy') assert(!forbidden.test(key), 'forbidden field exported');
        visit(entry, route ? route + '.' + key : key);
      }
    }
    visit(document);
    for (const item of document.mediaBlobs || []) {
      const bytes = Buffer.from(item.base64, 'base64');
      assert.equal(hash(bytes), item.sha256, 'exported image hash mismatch');
    }
  }
  replace(client, document, actor = 'fixture', metadata = {}) {
    const file = drivePath(this.config, client), bytes = Buffer.isBuffer(document) ? document : json(document);
    assert(bytes.length <= MAX_BYTES, 'fixture exceeds bound');
    // Exact own file only. A crash may leave a partial file, which the reader must
    // reject as a whole; no neighboring or pre-existing canary files are touched.
    fs.writeFileSync(file, bytes);
    this.log({ ...metadata, client, operation: 'write-file', actor, file: this.config.files[client], ...fileMeta(file), success: true });
  }
  snapshot(client) { return JSON.parse(fs.readFileSync(drivePath(this.config, client), 'utf8')); }
}

async function until(label, action, predicate, timeout = 45_000) {
  const deadline = Date.now() + timeout; let result;
  while (Date.now() < deadline) { result = await action(); if (predicate(result)) return result; await sleep(180); }
  throw new Error('timeout: ' + label);
}

async function catalog(page) {
  return page.evaluate(() => window.KGGProgressionEditorBridge.catalog());
}
async function bankEntry(page, id) { return (await catalog(page)).find(item => String(item.id) === String(id)); }
async function waitEntry(page, id, predicate = () => true, label = 'automatic peer reception') {
  return until(label, () => bankEntry(page, id), value => !!value && predicate(value));
}
async function quietEditor(page) {
  if (await page.locator('#adminSecretsModal.open').isVisible()) await page.locator('#closeAdminSecrets').click();
}
async function openBankEditor(page, id) {
  await quietEditor(page);
  if (await page.locator('#editorModal.open').isVisible()) await page.locator('#closeEditor').click();
  if (!await page.locator('#bankContent [data-edit="' + id + '"]').isVisible()) {
    if (await page.locator('#exerciseInput').inputValue()) await page.locator('#exerciseInput').fill('');
    if (!await page.locator('#bankContent [data-edit="' + id + '"]').isVisible()) await page.locator('#bankToggle').click();
  }
  // Baseline a237 and the bound candidate both replace Bank gear nodes when a
  // dirty textmaster blurs. Complete that real UI transition before locating
  // the gear again; see editor-focus-20261015/report.json.
  const input = page.locator('#exerciseInput');
  if (await input.evaluate(node => document.activeElement === node)) await input.press('Tab');
  const gear = page.locator('#bankContent [data-edit="' + id + '"]');
  await gear.click();
  await page.locator('#editorModal.open').waitFor();
}
async function saveEditor(page) { await page.locator('#saveExercise').click(); await page.locator('#editorModal.open').waitFor({ state: 'hidden' }); }

// Observe the real rendered name, not the catalog bridge. Re-query after every
// render because the app replaces Bank rows. The observer never scrolls or syncs.
async function armRenameTiming(page, selector, expectedName, local, delayMs) {
  return page.evaluate(({ selector, expectedName, local, delayMs }) => {
    if (window.__kggDriveRenameTiming) throw new Error('rename timing already armed');
    const previousName = document.querySelector(selector)?.textContent.trim();
    if (!previousName || previousName === expectedName) throw new Error('rename timing needs the previous visible name');
    const data = { armedAtMs: performance.now(), previousName, clickCount: 0, clickAtMs: null, visibleAtMs: null,
      delayRequestedMs: delayMs, delayInvocations: 0, delayActualMs: 0, visibleRect: null };
    let frame = 0, stopped = false;
    const click = event => {
      if (!event.target.closest?.('#saveExercise')) return;
      document.removeEventListener('click', click, true);
      data.clickCount++; data.clickAtMs = performance.now();
      // Opt-in sensitivity control on this actual Save event only. This is a
      // bounded test stimulus, never a product latency budget or app patch.
      if (delayMs) {
        data.delayInvocations++;
        const start = performance.now();
        while (performance.now() - start < delayMs) { /* deliberate UI-thread stall */ }
        data.delayActualMs = performance.now() - start;
      }
    };
    function visibleName() {
      const node = document.querySelector(selector);
      if (!node || node.textContent.trim() !== expectedName || document.querySelector('#editorModal.open')) return null;
      const box = node.getBoundingClientRect();
      let left = Math.max(0, box.left), top = Math.max(0, box.top), right = Math.min(innerWidth, box.right), bottom = Math.min(innerHeight, box.bottom);
      for (let parent = node; parent; parent = parent.parentElement) {
        const style = getComputedStyle(parent);
        if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) === 0) return null;
        const rect = parent.getBoundingClientRect();
        if (parent !== node && /auto|scroll|hidden|clip/.test(style.overflowX)) { left = Math.max(left, rect.left); right = Math.min(right, rect.right); }
        if (parent !== node && /auto|scroll|hidden|clip/.test(style.overflowY)) { top = Math.max(top, rect.top); bottom = Math.min(bottom, rect.bottom); }
      }
      if (right <= left || bottom <= top) return null;
      const hit = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
      if (!node.closest('[data-add]')?.contains(hit)) return null;
      return { left, top, width: right - left, height: bottom - top };
    }
    const stop = () => { stopped = true; cancelAnimationFrame(frame); document.removeEventListener('click', click, true); };
    const sample = () => {
      if (stopped) return;
      if (!local || data.clickAtMs !== null) {
        const rect = visibleName();
        if (rect) { data.visibleAtMs = performance.now(); data.visibleRect = rect; stop(); return; }
      }
      frame = requestAnimationFrame(sample);
    };
    window.__kggDriveRenameTiming = { data, stop };
    if (local) document.addEventListener('click', click, true);
    frame = requestAnimationFrame(sample);
    return { armedAtMs: data.armedAtMs, previousName };
  }, { selector, expectedName, local, delayMs });
}

async function measureRenameSave(a, b, exerciseId, expectedName, report, delayMs) {
  const sample = { case: 'edit-rename-stable-id-english-clear-and-reload', exerciseId, status: 'INCOMPLETE',
    endCondition: 'same Bank ID has expected name, editor closed, text visible in viewport and scroll container, unobscured at a sampled animation frame' };
  report.timings.samples.push(sample);
  const selector = '#bankContent [data-add="' + exerciseId + '"] .bankText b';
  try {
    await a.locator('#saveExercise').waitFor({ state: 'visible' });
    sample.armed = await Promise.all([armRenameTiming(a, selector, expectedName, true, delayMs), armRenameTiming(b, selector, expectedName, false, 0)]);
    sample.armedBeforeAction = true;
    // A uses its own monotonic event clock. Cross-client elapsed time uses one
    // Node clock, including automation observation overhead; never subtract the
    // unrelated performance.now() origins of the two browser pages.
    const localVisible = a.waitForFunction(() => window.__kggDriveRenameTiming.data.visibleAtMs !== null, null, { polling: 'raf', timeout: 45_000 });
    const peerVisible = b.waitForFunction(() => window.__kggDriveRenameTiming.data.visibleAtMs !== null, null, { polling: 'raf', timeout: 45_000 })
      .then(async handle => { const observedAtMs = performance.now(); await handle.dispose(); return observedAtMs; });
    sample.actionDispatchRootMs = performance.now();
    const [, localHandle, peerObservedRootMs] = await Promise.all([saveEditor(a), localVisible, peerVisible]);
    await localHandle.dispose();
    const [local, peer] = await Promise.all([a.evaluate(() => window.__kggDriveRenameTiming.data), b.evaluate(() => window.__kggDriveRenameTiming.data)]);
    sample.local = local; sample.peer = peer; sample.peerObservedRootMs = peerObservedRootMs;
    sample.saveClickToLocalVisibleFrameMs = local.visibleAtMs - local.clickAtMs;
    sample.saveDispatchToPeerVisibleObservedMs = peerObservedRootMs - sample.actionDispatchRootMs;
    assert.equal(local.clickCount, 1, 'timing did not observe the actual Save click');
    assert(Number.isFinite(sample.saveClickToLocalVisibleFrameMs) && sample.saveClickToLocalVisibleFrameMs >= 0, 'local UI timing missing');
    assert(Number.isFinite(sample.saveDispatchToPeerVisibleObservedMs) && sample.saveDispatchToPeerVisibleObservedMs >= 0, 'peer visible timing missing');
    assert.equal(local.delayInvocations, delayMs ? 1 : 0, 'requested UI delay probe did not execute on the Save event');
    if (delayMs) {
      assert(local.delayActualMs >= delayMs, 'actual UI delay shorter than the requested control stimulus');
      assert(sample.saveClickToLocalVisibleFrameMs >= local.delayActualMs, 'local UI measurement missed the executed delay');
    }
    sample.delayProbeStatus = delayMs ? 'EXECUTED_AND_OBSERVED' : 'NOT_REQUESTED';
    sample.status = 'MEASURED'; report.timings.status = 'MEASURED';
  } finally {
    const partial = await Promise.allSettled([a, b].map(page => page.evaluate(() => {
      const probe = window.__kggDriveRenameTiming, data = probe?.data;
      probe?.stop(); delete window.__kggDriveRenameTiming;
      return data;
    })));
    for (const [index, key] of ['local', 'peer'].entries()) {
      if (partial[index].status === 'fulfilled' && partial[index].value) sample[key] = partial[index].value;
    }
  }
}

async function enterExercise(page, name) {
  await quietEditor(page); await page.locator('#exerciseInput').fill(name); await page.locator('#exerciseInput').press('Enter');
  return until('confirmed Enter persisted to library without editor Save', () => catalog(page), items => items.some(item => item.name === name));
}
async function imageColor(page, expected) {
  await page.locator('#editMediaPreview img').waitFor({ state: 'visible' });
  const pixels = await page.locator('#editMediaPreview img').evaluate(async image => {
    await image.decode(); const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1;
    const context = canvas.getContext('2d'); context.drawImage(image, 0, 0, 1, 1);
    return Array.from(context.getImageData(0, 0, 1, 1).data);
  });
  if (expected === 'red') assert(pixels[0] > pixels[2] + 100, 'received decoded image is not the red fixture');
  else assert(pixels[2] > pixels[0] + 100, 'received decoded image is not the blue fixture');
}

async function makeClient(browser, client, config, adapter, report) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block', locale: 'de-DE' });
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== BASE_URL) return route.abort();
    const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '');
    const file = path.resolve(ROOT, relative);
    if (!inside(ROOT, file) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return route.fulfill({ status: 404, body: '' });
    const contentType = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css', '.json': 'application/json' }[path.extname(file)] || 'application/octet-stream';
    return route.fulfill({ status: 200, contentType, body: fs.readFileSync(file) });
  });
  await context.exposeBinding('__kggDriveRead', (_, documentId) => adapter.read(client, documentId));
  await context.exposeBinding('__kggDriveWrite', (_, documentId, document) => adapter.write(client, document, documentId));
  await context.addInitScript(({ client, deviceIds, roomId, patientSentinel, secretSentinel }) => {
    const id = deviceIds[client], peer = deviceIds[client === 'a' ? 'b' : 'a'];
    if (!localStorage.getItem('kggDriveSyntheticSetupV1')) {
      localStorage.setItem('kgg_html_app_v2_state', JSON.stringify({ plan: [], patient: { name: patientSentinel, notes: patientSentinel, therapist: 'Synthetic ' + client },
        packages: [{ id: 'synthetic_plan_package', name: patientSentinel, exercises: ['Beinpresse'] }], bankOpen: true }));
      localStorage.setItem('kgg_admin_local_secrets_v1', JSON.stringify({ geminiKeys: [secretSentinel], mediaDropzoneUploadToken: secretSentinel }));
      localStorage.setItem('kgg_sync_pair_device_id_v1', id);
      localStorage.setItem('kgg_sync_pair_follow_config_v1', JSON.stringify({ therapistId: id, syncRoomId: roomId, followedTherapists: [{ therapistId: peer, deviceId: peer, roomId, displayName: 'Synthetic peer', autoDownload: true, scopes: ['exerciseBank'] }] }));
      localStorage.setItem('kggInstallAsked', '1'); localStorage.setItem('kggDriveSyntheticSetupV1', '1');
    }
    const documentId = client + '-' + crypto.randomUUID();
    window.__kggDriveDocumentId = documentId;
    let peerMesh = { kind: 'kgg_cross_data_safe_sync_mesh', version: 1, roomId, peers: [] };
    window.KGGNativeSync = { available: true, platform: 'filesystem-test',
      status: () => ({ available: true, platform: 'filesystem-test', transport: 'filesystem-test', driveConfigured: false, providerAccepted: false, syntheticTest: true }),
      read: async () => { const mesh = await window.__kggDriveRead(documentId); peerMesh = mesh; return mesh; },
      write: document => window.__kggDriveWrite(documentId, document),
      // The production UI consumes listPeers synchronously. Diagnostics must
      // neither start a provider read nor masquerade as a completed import.
      listPeers: () => peerMesh,
      getFollowConfig: () => JSON.parse(localStorage.getItem('kgg_sync_pair_follow_config_v1')),
      setFollowConfig: value => { localStorage.setItem('kgg_sync_pair_follow_config_v1', JSON.stringify(value)); return true; } };
  }, { client, deviceIds: config.deviceIds, roomId: ROOM, patientSentinel: PATIENT_SENTINEL, secretSentinel: SECRET_SENTINEL });
  const page = await context.newPage();
  page.on('pageerror', error => report.browserErrors.push({ client, messageHash: hash(error.message) }));
  await page.goto(BASE_URL + '/kgg-update/index.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.KGGNativeExerciseSync && window.KGGProgressionEditorBridge && document.getElementById('exerciseInput'));
  await quietEditor(page);
  return { context, page };
}

async function lifecycle(page, event) {
  // Dispatch only a browser event to exercise the installed automatic handler.
  // This is deliberately reported as a handler test, never a device resume.
  await page.evaluate(event => {
    if (event === 'visibilitychange') document.dispatchEvent(new Event(event));
    else window.dispatchEvent(new Event(event));
  }, event);
}

async function captureFailure(client, instance, config, adapter, report) {
  if (!instance?.page || instance.page.isClosed()) return;
  const page = instance.page, evidence = { client, capturedAt: new Date().toISOString(), files: [] };
  const save = (name, bytes) => {
    const file = outputPath(config, name); fs.writeFileSync(file, bytes);
    evidence.files.push({ name, bytes: Buffer.byteLength(bytes), sha256: hash(bytes) });
  };
  try {
    const screenshot = await page.screenshot({ fullPage: false, timeout: 5000 });
    save('failure-' + client + '.png', screenshot);
  } catch (error) { evidence.screenshotErrorHash = hash(error.message); }
  try {
    const ui = await page.evaluate(() => {
      const clone = document.body.cloneNode(true);
      // Keep synthetic UI evidence, never executable source, secret-entry forms,
      // raw export fields or inline media/payload attributes.
      clone.querySelectorAll('script,style,#adminSecretsModal,#sharedBankText,#shareText,#syncPairQrBox').forEach(node => node.remove());
      clone.querySelectorAll('input[type="password"]').forEach(node => node.remove());
      for (const node of clone.querySelectorAll('*')) for (const attribute of [...node.attributes]) {
        if (/payload|token|secret|api.?key/i.test(attribute.name) || /^on/i.test(attribute.name)
          || /^(data:|javascript:)/i.test(attribute.value)) node.removeAttribute(attribute.name);
      }
      const visible = node => !!(node.getBoundingClientRect().width && node.getBoundingClientRect().height)
        && getComputedStyle(node).visibility !== 'hidden';
      const bankNames = window.KGGProgressionEditorBridge?.catalog?.().map(item => String(item.name || '')) || [];
      return { dom: '<!doctype html><html lang="de"><body>' + clone.innerHTML + '</body></html>',
        inputValue: document.getElementById('exerciseInput')?.value || '', bankNames,
        visibleModalIds: [...document.querySelectorAll('.modal.open,[role="dialog"]')].filter(visible).map(node => node.id || '(anonymous)'),
        syncStatus: document.getElementById('syncPairStatus')?.textContent || '',
        transportStatus: window.KGGNativeSync?.status?.() || null };
    });
    save('failure-' + client + '-dom.html', Buffer.from(ui.dom, 'utf8')); delete ui.dom;
    save('failure-' + client + '-diagnostics.json', json({ capturedAt: evidence.capturedAt, ...ui,
      adapter: adapter.state[client], recentTransport: report.transportEvents.slice(-20) }));
  } catch (error) { evidence.diagnosticErrorHash = hash(error.message); }
  report.failureEvidence = report.failureEvidence || []; report.failureEvidence.push(evidence);
}

async function runSuite(config, resetOwned = false) {
  checkDrive(config); prepare(config);
  const reportFile = outputPath(config, 'report.json');
  assert(!fs.existsSync(reportFile), 'run already has a report; choose a new run-id');
  const ownershipFile = path.join(OUTPUT_ROOT, 'owned-' + hash(config.driveDir).slice(0, 16) + '-round-' + config.round + '.json');
  const ownership = { driveDir: config.driveDir, cloudFolderId: config.cloudFolderId, files: config.files, deviceIds: config.deviceIds };
  if (resetOwned) {
    assert(fs.existsSync(ownershipFile), 'cannot reset files without an existing harness ownership record');
    assert.deepEqual(JSON.parse(fs.readFileSync(ownershipFile, 'utf8')), ownership, 'existing ownership record differs');
    for (const client of ['a', 'b']) { const file = drivePath(config, client); if (fs.existsSync(file)) fs.unlinkSync(file); }
  }
  for (const client of ['a', 'b']) assert(!fs.existsSync(drivePath(config, client)), 'peer file already exists; use --reset-owned only for a deliberate retry of owned synthetic files');
  fs.writeFileSync(ownershipFile, json(ownership));
  // Resolve the existing pinned dependency from this repository or NODE_PATH.
  // This test never installs packages or browser binaries.
  const playwright = require('playwright');
  const report = { schema: 'kgg-drive-sync-e2e-report/v1', startedAt: new Date().toISOString(), transport: 'filesystem-test',
    cloudTransportVerified: false, androidSafVerified: false, twoPhysicalDevicesVerified: false,
    sourceSha: cp.execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).trim(),
    htmlSha256: hash(fs.readFileSync(path.join(ROOT, 'kgg-update/index.html'))), harnessSha256: hash(fs.readFileSync(__filename)),
    runId: config.runId, round: config.round, externalDrive: config.externalDrive, cloudFolderId: config.cloudFolderId, files: config.files,
    cases: [], browserErrors: [], transportEvents: [],
    timings: { schema: 'kgg-drive-sync-timing/v1', status: 'INCOMPLETE', scope: 'synthetic-filesystem-two-browser-contexts',
      performanceVerdict: 'NOT_EVALUATED_NO_PRODUCT_BUDGET', nodeVersion: process.version,
      viewport: { width: 1280, height: 900 }, adapterDelayMs: ADAPTER_DELAY_MS,
      scheduling: 'production polling and debounce unchanged; no manual sync trigger in the measured rename',
      localClock: 'page A performance.now: actual Save click to visible DOM at animation-frame observation; not a physical paint measurement',
      peerClock: 'single Node performance.now: Save dispatch to peer-visible observation, including automation overhead',
      uiDelayProbeMs: config.uiDelayProbeMs || 0, samples: [] } };
  const adapter = new DriveAdapter(config, report);
  const browser = await playwright.chromium.launch({ headless: true });
  report.timings.browserVersion = browser.version();
  let a, b;
  async function test(name, callback) {
    const item = { name, startedAt: new Date().toISOString(), status: 'RUNNING' }; report.cases.push(item);
    console.log('E2E ' + name + ' START');
    try { await callback(); item.status = 'PASS'; console.log('E2E ' + name + ' PASS'); }
    catch (error) { item.status = 'FAIL'; item.error = error.message; throw error; }
    finally { item.finishedAt = new Date().toISOString(); fs.writeFileSync(reportFile, json(report)); }
  }
  let exerciseId, originalSnapshot;
  // Exercise text is parsed as training input; keep run identifiers and digits
  // in evidence metadata rather than in authored exercise/stage names.
  const roundName = config.round === 1 ? 'Alpha' : 'Bravo';
  const prefix = 'KGG Drive Test ' + roundName;
  try {
    await test('isolated-boot-real-drive-files', async () => {
      a = await makeClient(browser, 'a', config, adapter, report); b = await makeClient(browser, 'b', config, adapter, report);
      await until('automatic boot writes', async () => adapter.state, states => states.a.writes > 0 && states.b.writes > 0);
      assert.notEqual(await a.page.evaluate(() => localStorage.getItem('kgg_sync_pair_device_id_v1')), await b.page.evaluate(() => localStorage.getItem('kgg_sync_pair_device_id_v1')));
    });
    await test('half-draft-cancel-does-not-create-library-entry', async () => {
      const draft = prefix + ' Unconfirmed'; await a.page.locator('#exerciseInput').fill(draft); await sleep(900);
      assert(!(await catalog(a.page)).some(item => item.name === draft), 'half draft entered own library');
      assert(!(await catalog(b.page)).some(item => item.name === draft), 'half draft entered peer library');
      await a.page.locator('#exerciseInput').fill('');
    });
    await test('confirmed-enter-auto-create-without-extra-save', async () => {
      const name = prefix + ' Create'; const items = await enterExercise(a.page, name);
      exerciseId = items.find(item => item.name === name).id;
      await waitEntry(b.page, exerciseId, item => item.name === name);
      originalSnapshot = adapter.snapshot('a');
    });
    await test('edit-rename-stable-id-english-clear-and-reload', async () => {
      // A real search keeps the known row in view after the app replaces Bank
      // DOM. Prepare both clients before timing; never scroll after Save starts.
      for (const client of [a, b]) {
        await quietEditor(client.page);
        await client.page.locator('#exerciseInput').fill(prefix);
        const name = client.page.locator('#bankContent [data-add="' + exerciseId + '"] .bankText b');
        await name.waitFor({ state: 'visible' }); await name.scrollIntoViewIfNeeded();
        assert.equal((await name.textContent()).trim(), prefix + ' Create', 'timing setup lost the original visible name');
      }
      report.timings.fixture = { operation: 'rename-before-fixture-image-upload', bankQuery: prefix,
        catalogEntriesA: (await catalog(a.page)).length, catalogEntriesB: (await catalog(b.page)).length };
      await openBankEditor(a.page, exerciseId); await a.page.locator('#editName').fill(prefix + ' Renamed');
      await a.page.locator('#editNameEn').fill('Synthetic renamed exercise'); await a.page.locator('#editNameDe').fill('Synthetische Kataloguebung'); await a.page.locator('#editSets').selectOption('4');
      await measureRenameSave(a.page, b.page, exerciseId, prefix + ' Renamed', report, config.uiDelayProbeMs || 0);
      await waitEntry(b.page, exerciseId, item => item.name === prefix + ' Renamed' && item.nameEn === 'Synthetic renamed exercise' && item.nameDe === 'Synthetische Kataloguebung' && item.sets === 4);
      assert.equal((await catalog(b.page)).filter(item => item.id === exerciseId).length, 1, 'rename duplicated stable ID');
      assert(!(await catalog(b.page)).some(item => item.name === prefix + ' Create'), 'rename retained old name');
      await openBankEditor(a.page, exerciseId); await a.page.locator('#editNameEn').fill(''); await saveEditor(a.page);
      await waitEntry(b.page, exerciseId, item => item.nameEn === '');
      await b.page.locator('#exerciseInput').fill('');
      await b.page.reload({ waitUntil: 'domcontentloaded' }); await waitEntry(b.page, exerciseId, item => item.nameEn === '' && item.nameDe === 'Synthetische Kataloguebung' && item.sets === 4);
    });
    await test('image-bytes-add-peer-decode-and-reload', async () => {
      const firstImageEvent = report.transportEvents.length;
      const originDocumentId = await a.page.evaluate(() => window.__kggDriveDocumentId);
      await openBankEditor(a.page, exerciseId); await a.page.locator('#editMediaFile').setInputFiles(outputPath(config, 'image-red.png'));
      const own = await waitEntry(a.page, exerciseId, item => item.media?.length === 1, 'image persisted on owner');
      await imageColor(a.page, 'red'); await a.page.locator('#closeEditor').click();
      await waitEntry(b.page, exerciseId, item => item.media?.[0]?.id === own.media[0].id);
      await openBankEditor(b.page, exerciseId); await imageColor(b.page, 'red'); await b.page.locator('#closeEditor').click();
      let originEchoTimer;
      const originEchoDeadline = Date.now() + 45_000;
      const echoRemaining = () => Math.max(1, originEchoDeadline - Date.now());
      try {
        await Promise.race([(async () => {
          const publication = await until('B automatically published the received image snapshot', async () => {
            const document = adapter.snapshot('b');
            if (!document.exerciseBank.some(item => item.id === exerciseId && item.media?.[0]?.id === own.media[0].id)
              || !document.mediaBlobs?.some(item => item.id === own.media[0].id)) return null;
            const digest = fileMeta(drivePath(config, 'b')).sha256;
            const index = report.transportEvents.findIndex((event, index) => index >= firstImageEvent
              && event.client === 'b' && event.operation === 'write-file' && event.actor === 'app' && event.sha256 === digest);
            return index < 0 ? null : { index, sha256: digest };
          }, value => !!value, echoRemaining());
          const originRead = await until('A actually read the B publication during automatic polling', async () =>
            report.transportEvents.find((event, index) => index > publication.index && event.client === 'a'
              && event.documentId === originDocumentId && event.method === 'read'
              && event.operation === 'read-file' && event.owner === 'b' && event.sha256 === publication.sha256), value => !!value, echoRemaining());
          // app-core 3091/3102/3108 keeps the automatic pipeline running until
          // its awaited import finishes. With cached synchronous listPeers,
          // the next genuine read in this same document proves that completion.
          const nextRead = await until('the next automatic A read starts after the matching-hash import completed', async () =>
            report.transportEvents.find(event => event.client === 'a' && event.documentId === originDocumentId
              && event.operation === 'operation-start' && event.method === 'read'
              && event.operationId > originRead.operationId), value => !!value, echoRemaining());
          assert(report.transportEvents.some(event => event.operation === 'operation-end' && event.operationId === originRead.operationId
            && event.documentId === originDocumentId && event.success), 'matching-hash transport read did not complete successfully');
          const completion = await a.page.evaluate(() => ({ documentId: window.__kggDriveDocumentId,
            pending: localStorage.getItem('kgg_library_sync_pending_v1') }));
          assert.equal(completion.documentId, originDocumentId, 'origin document changed before echo completion');
          assert.equal(completion.pending, '0', 'origin image import remains pending after the next automatic read');
          await openBankEditor(a.page, exerciseId); await imageColor(a.page, 'red'); await a.page.locator('#closeEditor').click();
          await a.page.reload({ waitUntil: 'domcontentloaded' }); await openBankEditor(a.page, exerciseId);
          await imageColor(a.page, 'red'); await a.page.locator('#closeEditor').click();
          report.originImageEcho = { publicationSha256: publication.sha256, originDocumentId, originReadAt: originRead.at,
            originReadOperationId: originRead.operationId, nextReadAt: nextRead.at, nextReadOperationId: nextRead.operationId, pending: completion.pending,
            source: 'B automatic snapshot publication → A actual matching-hash read → next serial automatic read in same document → decode → reload/decode' };
        })(), new Promise((_, reject) => { originEchoTimer = setTimeout(() => reject(new Error('origin image echo assertion exceeded 45s')), 45_000); })]);
      } finally { clearTimeout(originEchoTimer); }
      await b.page.reload({ waitUntil: 'domcontentloaded' }); await openBankEditor(b.page, exerciseId); await imageColor(b.page, 'red'); await b.page.locator('#closeEditor').click();
    });
    await test('image-replace-transport-failure-automatic-retry', async () => {
      const before = adapter.state.a.failures; adapter.state.a.writeFail = true;
      await openBankEditor(a.page, exerciseId); const old = await bankEntry(a.page, exerciseId);
      await a.page.locator('#editMediaFile').setInputFiles(outputPath(config, 'image-blue.png'));
      const updated = await waitEntry(a.page, exerciseId, item => item.media?.[0]?.id && item.media[0].id !== old.media?.[0]?.id);
      await imageColor(a.page, 'blue'); await a.page.locator('#closeEditor').click();
      await until('write failure observed', async () => adapter.state.a.failures, count => count > before);
      adapter.state.a.writeFail = false;
      await waitEntry(b.page, exerciseId, item => item.media?.[0]?.id === updated.media[0].id, 'automatic image retry');
      await openBankEditor(b.page, exerciseId); await imageColor(b.page, 'blue'); await b.page.locator('#closeEditor').click();
    });
    await test('image-remove-failed-write-retry-and-reload', async () => {
      const failures = adapter.state.a.failures; adapter.state.a.writeFail = true;
      await openBankEditor(a.page, exerciseId); await a.page.locator('#removeExerciseImage').click(); await a.page.locator('#closeEditor').click();
      await until('image removal write failure observed', async () => adapter.state.a.failures, count => count > failures);
      assert(!(await bankEntry(a.page, exerciseId)).media?.length, 'failed transport lost local image removal');
      assert((await bankEntry(b.page, exerciseId)).media?.length === 1, 'peer unexpectedly changed before successful transport');
      adapter.state.a.writeFail = false;
      await waitEntry(b.page, exerciseId, item => !item.media?.length); await b.page.reload({ waitUntil: 'domcontentloaded' });
      await waitEntry(b.page, exerciseId, item => !item.media?.length);
    });
    await test('progression-create-english-edit-clear-and-persistence', async () => {
      await openBankEditor(a.page, exerciseId); await a.page.locator('#kgg015ProgressionBox summary').click();
      await a.page.locator('[data-kgg015-add-slot="after"]').click(); await a.page.locator('[data-kgg015-add-name]').fill(prefix + ' Stage');
      await a.page.locator('[data-kgg015-new]').click(); await a.page.locator('[data-kgg015-name-en="1"]').fill('Synthetic stage'); await saveEditor(a.page);
      await waitEntry(b.page, exerciseId, item => item.progressionVariants?.some(stage => stage.nameEn === 'Synthetic stage'));
      await openBankEditor(a.page, exerciseId); if (!await a.page.locator('#kgg015ProgressionBox details').evaluate(node => node.open)) await a.page.locator('#kgg015ProgressionBox summary').click();
      await a.page.locator('[data-kgg015-name-en="1"]').fill(''); await saveEditor(a.page);
      await waitEntry(b.page, exerciseId, item => item.progressionVariants?.[1]?.nameEn === '');
      await b.page.reload({ waitUntil: 'domcontentloaded' }); await waitEntry(b.page, exerciseId, item => item.progressionVariants?.length >= 2 && item.progressionVariants[1].nameEn === '');
    });
    await test('plan-removal-does-not-delete-library', async () => {
      await quietEditor(a.page);
      if (await a.page.locator('#editorModal.open').isVisible()) await a.page.locator('#closeEditor').click();
      // Establish this case's own plan through the normal clear/Bank UI;
      // earlier editor navigation may already have cleared the previous plan.
      await a.page.locator('#clearInput').click();
      await a.page.waitForFunction(() => window.KGGDataStore.getCurrentPlan().exercises.length === 0);
      const add = a.page.locator('#bankContent [data-add="' + exerciseId + '"]');
      if (!await add.isVisible()) await a.page.locator('#bankToggle').click();
      await add.click();
      const planExercise = await until('known library exercise was added through its Bank button', () => a.page.evaluate(id =>
        window.KGGDataStore.getCurrentPlan().exercises.filter(item => String(item.sourceId || item.bankId || '') === String(id))
          .map(item => ({ localId: item.localId || item.id })), exerciseId), items => items.length === 1);
      const planId = planExercise[0].localId;
      const card = a.page.locator('#planList .planCard[data-plan-id="' + planId + '"]');
      await card.locator('[data-planedit="' + planId + '"]').click(); await a.page.locator('#deleteExercise').click();
      await card.waitFor({ state: 'detached' });
      assert(await bankEntry(a.page, exerciseId), 'plan removal deleted own library entry');
      assert(await bankEntry(b.page, exerciseId), 'plan removal deleted peer library entry');
      assert(!adapter.snapshot('a').tombstones?.exerciseBank?.some(item => item.id === exerciseId), 'plan removal exported library tombstone');
    });
    await test('read-error-recovery-online-and-foreground-handlers', async () => {
      for (const event of ['online', 'visibilitychange', 'pageshow', 'kgg:native-sync-resume']) {
        const failures = adapter.state.b.failures; adapter.state.b.readFail = true;
        await openBankEditor(a.page, exerciseId); await a.page.locator('#editNameEn').fill('Lifecycle ' + event); await saveEditor(a.page);
        await until('updated owner file', async () => adapter.snapshot('a'), doc => doc.exerciseBank.some(item => item.id === exerciseId && item.nameEn === 'Lifecycle ' + event));
        await lifecycle(b.page, event);
        await until('read failure observed', async () => adapter.state.b.failures, count => count > failures);
        adapter.state.b.readFail = false; await lifecycle(b.page, event);
        await waitEntry(b.page, exerciseId, item => item.nameEn === 'Lifecycle ' + event);
      }
    });
    await test('visible-polling-without-manual-sync', async () => {
      await openBankEditor(a.page, exerciseId); await a.page.locator('#editNameEn').fill('Polling received'); await saveEditor(a.page);
      await waitEntry(b.page, exerciseId, item => item.nameEn === 'Polling received');
    });
    await test('closed-html-reopen-pulls-new-peer-content', async () => {
      await b.page.close();
      await openBankEditor(a.page, exerciseId); await a.page.locator('#editNameEn').fill('Changed while peer HTML was closed'); await saveEditor(a.page);
      await until('closed peer update reached file', async () => adapter.snapshot('a'), doc => doc.exerciseBank.some(item => item.id === exerciseId && item.nameEn === 'Changed while peer HTML was closed'));
      b.page = await b.context.newPage(); b.page.on('pageerror', error => report.browserErrors.push({ client: 'b', messageHash: hash(error.message) }));
      await b.page.goto(BASE_URL + '/kgg-update/index.html', { waitUntil: 'domcontentloaded' });
      await waitEntry(b.page, exerciseId, item => item.nameEn === 'Changed while peer HTML was closed', 'HTML reopen automatic pull');
    });
    await test('negative-bad-room-nonfollowed-malformed-atomic', async () => {
      adapter.state.a.writeFail = true; const saved = adapter.snapshot('a');
      const stable = hash(json((await catalog(b.page)).find(item => item.id === exerciseId)));
      for (const mode of ['bad-room', 'nonfollowed', 'malformed', 'forbidden', 'bad-image-hash']) {
        const document = structuredClone(saved);
        document.exerciseBank = document.exerciseBank.filter(item => item.id === exerciseId);
        document.exerciseBank[0].nameEn = 'Must never enter bank';
        document.exerciseBank[0].updatedAt = '2099-01-01T00:00:00.000Z';
        document.exerciseBank[0].syncRevision = { counter: Math.max(0, ...saved.exerciseBank.map(item => Number(item.syncRevision?.counter) || 0)) + 1000, deviceId: DEVICE_A };
        if (mode === 'bad-room') { document.roomId = 'wrong_room'; document.origin.roomId = 'wrong_room'; }
        if (mode === 'nonfollowed') { document.origin.deviceId = 'unfollowed_synthetic'; document.origin.therapistId = 'unfollowed_synthetic'; }
        if (mode === 'forbidden') document.exerciseBank[0].patientName = PATIENT_SENTINEL;
        if (mode === 'bad-image-hash') { document.exerciseBank[0].media = [{ id: 'bad_image', type: 'image', mime: 'image/png' }]; document.mediaBlobs = [{ id: 'bad_image', mime: 'image/png', sha256: '0'.repeat(64), base64: png([1, 2, 3]).toString('base64') }]; }
        adapter.replace('a', mode === 'malformed' ? Buffer.from('{"kind":') : document);
        const readCount = adapter.state.b.reads; await lifecycle(b.page, 'online');
        await until('negative snapshot read', async () => adapter.state.b.reads, count => count > readCount); await sleep(500);
        assert.equal(hash(json((await catalog(b.page)).find(item => item.id === exerciseId))), stable, 'negative document changed library: ' + mode);
      }
      adapter.replace('a', saved); adapter.state.a.writeFail = false; await lifecycle(a.page, 'online');
    });
    await test('competing-real-ui-edits-converge-in-both-file-orders', async () => {
      for (const reversed of [false, true]) {
        adapter.state.a.writeFail = true; adapter.state.b.writeFail = true;
        adapter.state.a.readFail = true; adapter.state.b.readFail = true;
        adapter.orderReversed = reversed;
        await openBankEditor(a.page, exerciseId); await a.page.locator('#editNameEn').fill('Older synthetic conflict'); await saveEditor(a.page);
        const older = await bankEntry(a.page, exerciseId);
        let newer;
        for (let attempt = 0; attempt < 10; attempt++) {
          await openBankEditor(b.page, exerciseId); await b.page.locator('#editNameEn').fill('Conflict intermediate ' + attempt); await saveEditor(b.page);
          await openBankEditor(b.page, exerciseId); await b.page.locator('#editNameEn').fill('Newer synthetic conflict'); await saveEditor(b.page);
          newer = await bankEntry(b.page, exerciseId);
          if (Number(newer.syncRevision?.counter) > Number(older.syncRevision?.counter)) break;
        }
        assert(Number(newer.syncRevision?.counter) > Number(older.syncRevision?.counter), 'UI edits did not establish a distinct newer revision');
        const expectedRevision = newer.syncRevision.counter;
        adapter.state.a.writeFail = false; adapter.state.b.writeFail = false;
        adapter.state.a.readFail = false; adapter.state.b.readFail = false;
        await lifecycle(a.page, 'online'); await lifecycle(b.page, 'online');
        await waitEntry(a.page, exerciseId, item => item.nameEn === 'Newer synthetic conflict' && item.syncRevision?.counter === expectedRevision);
        await waitEntry(b.page, exerciseId, item => item.nameEn === 'Newer synthetic conflict' && item.syncRevision?.counter === expectedRevision);
      }
      report.conflictScope = 'Two actual UI clients with reversed two-file enumeration; three-peer permutation coverage belongs to the separate CLI test.';
    });
    if (config.cloudHold) await test('independent-cloud-reverse-update-html-reception', async () => {
      await until('owner pending write settled', () => a.page.evaluate(() => localStorage.getItem('kgg_library_sync_pending_v1')), value => value === '0');
      await until('owner adapter idle', async () => adapter.state.a.active, count => count === 0);
      const source = adapter.snapshot('a'), reverse = structuredClone(source);
      reverse.exportedAt = '2095-01-01T00:00:00.000Z';
      const target = reverse.exerciseBank.find(item => item.id === exerciseId);
      target.nameEn = 'Cloud reverse accepted ' + roundName; target.updatedAt = '2095-01-01T00:00:00.000Z';
      target.syncRevision = { counter: Math.max(0, ...[source, adapter.snapshot('b')].flatMap(doc => doc.exerciseBank.map(item => Number(item.syncRevision?.counter) || 0))) + 100, deviceId: DEVICE_A };
      const reverseFile = outputPath(config, 'cloud-reverse-a.json'); fs.writeFileSync(reverseFile, json(reverse));
      adapter.state.a.writeFail = true; // Cloud replaces A's own file while its writes are paused.
      const ready = { schema: 'kgg-drive-cloud-hold/v1', runId: config.runId, cloudFolderId: config.cloudFolderId,
        localDriveFile: drivePath(config, 'a'), fileName: config.files.a, before: fileMeta(drivePath(config, 'a')),
        uploadSourceFile: reverseFile, expected: fileMeta(reverseFile), continueFile: outputPath(config, 'continue.json'),
        instructions: 'Independently fetch the current Drive file and verify its content/hash. Replace the SAME cloud file ID using uploadSourceFile, then write continue.json with {"cloudReadbackVerified":true,"cloudFileId":"<verified id>","replacementVerified":true}. The harness independently awaits G: bytes and HTML reception.' };
      fs.writeFileSync(outputPath(config, 'ready.json'), json(ready)); console.log('E2E CLOUD_HOLD ready=' + outputPath(config, 'ready.json'));
      const deadline = Date.now() + config.cloudWaitMs; let control;
      while (Date.now() < deadline) {
        if (fs.existsSync(ready.continueFile)) { control = JSON.parse(fs.readFileSync(ready.continueFile, 'utf8')); break; }
        await sleep(500);
      }
      assert(control, 'bounded cloud hold expired');
      assert.equal(control.cloudReadbackVerified, true, 'independent cloud readback not confirmed');
      assert.equal(control.replacementVerified, true, 'cloud replacement not confirmed'); assert(typeof control.cloudFileId === 'string' && control.cloudFileId.length > 8, 'missing verified cloud file ID');
      await until('cloud bytes arrived through Drive Desktop', async () => fileMeta(drivePath(config, 'a')).sha256, value => value === ready.expected.sha256, 90_000);
      await waitEntry(b.page, exerciseId, item => item.nameEn === target.nameEn, 'cloud reverse update automatically received in HTML');
      report.cloudTransportVerified = true; report.cloudFileId = control.cloudFileId; report.cloudReverseSha256 = ready.expected.sha256;
      adapter.state.a.writeFail = false;
    });
    await test('representative-library-and-sync-status-screenshots', async () => {
      await openBankEditor(b.page, exerciseId); await b.page.locator('#closeEditor').click();
      await b.page.locator('#bankContent [data-edit="' + exerciseId + '"]').scrollIntoViewIfNeeded();
      await b.page.screenshot({ path: outputPath(config, 'library-before-delete.png'), fullPage: false });
      const syncMenuDeadline = Date.now() + 30_000;
      const syncMenuRemaining = () => Math.max(1, syncMenuDeadline - Date.now());
      await b.page.locator('#tabletMenuBtn').click({ timeout: syncMenuRemaining() });
      await b.page.locator('#tabletMenuSyncQrBtn').click({ timeout: syncMenuRemaining() });
      await b.page.locator('#syncPairModal.open').waitFor({ timeout: syncMenuRemaining() });
      await b.page.screenshot({ path: outputPath(config, 'sync-status.png'), fullPage: false });
      report.screenshots = ['library-before-delete.png', 'sync-status.png'];
      await b.page.locator('#closeSyncPairModal').click();
    });
    await test('delete-stale-replay-reversed-order-reload', async () => {
      await openBankEditor(a.page, exerciseId); await a.page.locator('#deleteExercise').click(); await a.page.locator('#confirmBankDelete').click();
      await until('delete automatically reached peer', () => bankEntry(b.page, exerciseId), value => !value);
      adapter.state.a.writeFail = true; const tombstone = adapter.snapshot('b');
      for (const reverse of [false, true]) {
        adapter.orderReversed = reverse; adapter.replace('a', originalSnapshot); adapter.replace('b', tombstone);
        await lifecycle(b.page, 'online'); await sleep(900); assert(!await bankEntry(b.page, exerciseId), 'stale replay resurrected deleted ID');
      }
      await b.page.reload({ waitUntil: 'domcontentloaded' }); await sleep(900); assert(!await bankEntry(b.page, exerciseId), 'reload resurrected deleted ID');
      adapter.state.a.writeFail = false;
    });
    await test('no-echo-or-overlapping-transport-and-safe-payload', async () => {
      await sleep(POLL_MS + 1500); const before = adapter.state.a.writes + adapter.state.b.writes;
      await sleep(POLL_MS + 1500); const after = adapter.state.a.writes + adapter.state.b.writes;
      assert.equal(after, before, 'unchanged peers triggered an echo write');
      assert(adapter.state.a.maxActive <= 1 && adapter.state.b.maxActive <= 1, 'transport calls overlapped within a client');
      for (const state of Object.values(adapter.state)) for (const document of Object.values(state.documents))
        assert(document.maxActive <= 1, 'transport calls overlapped within a document');
      for (const client of ['a', 'b']) adapter.assertExport(adapter.snapshot(client), client);
      assert.equal(report.browserErrors.length, 0, 'browser raised uncaught errors');
    });
    assert.equal(report.timings.status, 'MEASURED', 'required visible UI/sync measurement is incomplete');
    assert.equal(report.timings.samples.length, 1, 'expected one observed rename sample');
    report.status = 'PASS';
  } catch (error) {
    report.status = 'FAIL'; report.error = error.message;
    // Capture both clients before finally closes our contexts. Failures in the
    // evidence path must never replace the original test failure.
    await Promise.allSettled([captureFailure('a', a, config, adapter, report), captureFailure('b', b, config, adapter, report)]);
    throw error;
  }
  finally {
    try {
      report.finishedAt = new Date().toISOString(); report.adapter = adapter.state;
      report.timings.sampleCount = report.timings.samples.length;
      report.finalFiles = Object.fromEntries(['a', 'b'].map(client => {
        try { return [client, fileMeta(drivePath(config, client))]; } catch (_) { return [client, { unavailable: true }]; }
      }));
      fs.writeFileSync(reportFile, json(report));
    } finally {
      await Promise.allSettled([a?.context.close(), b?.context.close()].filter(Boolean));
      await browser.close();
    }
    console.log('E2E REPORT ' + reportFile + ' status=' + report.status + ' transport=filesystem-test androidSafVerified=false');
  }
}

async function selfTest() {
  assert(inside(OUTPUT_ROOT, path.join(OUTPUT_ROOT, 'run', 'round-1', 'report.json')));
  assert(!inside(OUTPUT_ROOT, path.resolve(OUTPUT_ROOT, '..', 'escape.json')));
  assert.throws(() => args(['--run', '--round', '3']));
  assert.throws(() => args(['--run', '--run-id', '../escape']));
  assert.throws(() => args(['--run', '--round', '2', '--cloud-hold']));
  assert.throws(() => args(['--run', '--cloud-hold']));
  assert.equal(args(['--run', '--ui-delay-probe-ms', '250']).uiDelayProbeMs, 250);
  for (const value of ['-1', '2001', 'NaN']) assert.throws(() => args(['--run', '--ui-delay-probe-ms', value]));
  assert.throws(() => args(['--run', '--ui-delay-probe-ms', '250', '--drive-dir', path.resolve('synthetic-test-folder')]));
  const image = png([20, 40, 60]); assert.equal(image.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  assert.equal(image.readUInt32BE(16), 40); assert.equal(image.readUInt32BE(20), 30);
  assert.equal(makeConfig(args(['--prepare'])).files.a, 'drive-a.json');
  assert.equal(makeConfig(args(['--prepare', '--round', '2'])).files.a, 'drive-a-r2.json');
  assert.equal(hash(Buffer.from('abc')), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  const report = { transportEvents: [] }, adapter = new DriveAdapter({}, report);
  adapter.log = event => report.transportEvents.push(event); // Metadata only: no filesystem transport.
  await adapter.operation('a', 'read', metadata => assert.equal(metadata.method, 'read'), 'a-selftest-document');
  assert.equal(adapter.state.a.maxActive, 1); assert.equal(adapter.state.a.active, 0);
  assert.equal(report.transportEvents[0].operation, 'operation-start');
  assert.equal(report.transportEvents[1].operation, 'operation-end');
  assert.equal(report.transportEvents[0].operationId, report.transportEvents[1].operationId);
  assert.equal(report.transportEvents[1].success, true);
  await assert.rejects(adapter.operation('a', 'write', () => { throw Error('synthetic failure'); }, 'a-selftest-document'));
  assert.equal(adapter.state.a.active, 0); assert.equal(adapter.state.a.documents['a-selftest-document'].active, 0);
  assert.equal(report.transportEvents.at(-1).success, false);
  await Promise.all(['a-overlap-document-one', 'a-overlap-document-two'].map(id => adapter.operation('a', 'read', () => true, id)));
  assert.equal(adapter.state.a.maxActive, 2, 'global counter must retain cross-document overlap');
  assert.equal(adapter.state.a.documents['a-overlap-document-one'].maxActive, 1);
  await Promise.all([1, 2].map(() => adapter.operation('b', 'read', () => true, 'b-overlap-document')));
  assert.equal(adapter.state.b.documents['b-overlap-document'].maxActive, 2, 'document counter must detect overlap');
  console.log('Drive E2E CLI self-test PASS; no browser, no Drive reads/writes');
}

async function main() {
  const options = args(process.argv.slice(2));
  if (options.help || !options.mode) {
    console.log('Usage: node release-pipeline/kgg_drive_sync_e2e.js --prepare|--run|--self-test [--run-id ID] [--round 1|2] [--drive-dir ABSOLUTE_SYNTHETIC_TEST_FOLDER --cloud-folder-id ID] [--cloud-hold] [--cloud-wait-ms N] [--reset-owned] [--ui-delay-probe-ms 0..2000]');
    return;
  }
  if (options.mode === 'self-test') return selfTest();
  const config = makeConfig(options);
  if (options.mode === 'prepare') console.log(JSON.stringify(prepare(config), null, 2));
  else await runSuite(config, options.resetOwned);
}
if (require.main === module) main().catch(error => { console.error('Drive sync E2E FAIL: ' + error.message); process.exitCode = 1; });
module.exports = { args, inside, makeConfig, png, crc32, DriveAdapter };
