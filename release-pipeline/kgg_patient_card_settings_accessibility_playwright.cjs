const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');

const [source, destination] = process.argv.slice(2).map(value => path.resolve(value));
const plan = Buffer.from(JSON.stringify({ i: 'issue377-synthetic', t: 'KGG Testplan', v: 1, d: 6,
  e: [['Beinpresse', 2, 'B', 'kg', 'Wdh', '40', '10']] })).toString('base64url');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const server = http.createServer((req, res) => {
  const route = new URL(req.url, 'http://127.0.0.1').pathname;
  const name = route === '/' ? 'index.html' : route.slice(1);
  if (!/^(?:vendor\/|patient-react-dist\/)?[\w.-]+$/.test(name)) return res.writeHead(404).end();
  const file = path.join(source, name);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return res.writeHead(404).end();
  const contentType = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css' }[path.extname(file)];
  res.writeHead(200, { 'Content-Type': (contentType || 'application/octet-stream') + '; charset=utf-8',
    'Cache-Control': 'no-store' }).end(fs.readFileSync(file));
});

async function main() {
  fs.mkdirSync(destination, { recursive: true });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true,
      hasTouch: true, locale: 'de-DE', serviceWorkers: 'block' });
    await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    await context.addInitScript(() => { localStorage.kggInstallAsked = '1'; });
    const page = await context.newPage();
    page.setDefaultTimeout(6000);
    const sourceResponse = page.waitForResponse(response => /\/patient-card-settings\.js[?]/.test(response.url()));
    await page.goto(`${origin}/?plan=${encodeURIComponent('KGGH2:' + plan)}`);
    const delivered = await sourceResponse;
    assert.equal(delivered.status(), 200);
    const servedSha256 = hash(await delivered.body());
    assert.equal(servedSha256, hash(fs.readFileSync(path.join(source, 'patient-card-settings.js'))));
    const card = page.locator('#list .ex').first();
    await page.waitForFunction(() => document.body.classList.contains('kggAlwaysCollapsed'));
    await card.locator('h3').tap();
    const button = card.locator('button.kggCardDots');
    await button.waitFor({ state: 'visible' });
    const initial = await page.screenshot({ path: path.join(destination, 'initial.png'), animations: 'disabled' });
    const label = await button.getAttribute('title');
    const zeroOrOne = await card.getByRole('button', { name: label, exact: true }).count();
    assert.equal(label, 'Übung anpassen');
    // Use the same real tap for both variants, including the unlabelled baseline.
    await button.tap();
    await page.locator('#kggSettingsSheet').waitFor({ state: 'visible' });
    const after = await page.screenshot({ path: path.join(destination, 'post-tap.png'), animations: 'disabled' });
    assert.notEqual(hash(initial), hash(after));
    const result = { status: zeroOrOne === 1 ? 'PASS' : 'FAIL', expectedAccessibleName: label,
      matchedButtons: zeroOrOne, settingsSheetVisibleAfterTap: true, servedSha256,
      screenshotSha256: { initial: hash(initial), postTap: hash(after) } };
    fs.writeFileSync(path.join(destination, 'result.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
    assert.equal(zeroOrOne, 1, 'The settings button must have the localized accessible name.');
  } finally {
    await browser?.close();
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
