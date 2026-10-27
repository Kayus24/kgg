const { test } = require('node:test');
const assert = require('node:assert/strict');
const { navigate } = require('../kgg-plugin/mcp/browser_navigation');
const allowed = url => url.startsWith('http://127.0.0.1/');
const fail = code => { throw new Error(code); };

function pageWithHistory(entries, index) {
  let calls = 0;
  return {
    context: () => ({ newCDPSession: async () => ({ send: async () => ({ entries: entries.map(url => ({ url })), currentIndex: index }), detach: async () => {} }) }),
    goBack: async () => { calls++; },
    url: () => 'http://127.0.0.1/entry',
    calls: () => calls,
  };
}
test('denied history origin is rejected before navigation', async () => {
  const page = pageWithHistory(['https://example.invalid/private', 'http://127.0.0.1/current'], 1);
  await assert.rejects(navigate(page, 'back', allowed, fail), /origin_escape/);
  assert.equal(page.calls(), 0);
});
test('about blank history is not an app back target', async () => {
  const page = pageWithHistory(['about:blank', 'http://127.0.0.1/current'], 1);
  await assert.rejects(navigate(page, 'back', allowed, fail), /back_history_unavailable/);
  assert.equal(page.calls(), 0);
});
test('empty history cannot claim navigation success', async () => {
  const page = pageWithHistory(['http://127.0.0.1/current'], 0);
  await assert.rejects(navigate(page, 'back', allowed, fail), /back_history_unavailable/);
  assert.equal(page.calls(), 0);
});
test('navigation timeout fails with stable classification', async () => {
  const page = { reload: async () => { const e = new Error('bounded timeout'); e.name = 'TimeoutError'; throw e; } };
  await assert.rejects(navigate(page, 'reload', allowed, fail), /navigation_timeout/);
});
test('redirected reload cannot claim successful safe navigation', async () => {
  const page = { reload: async () => {}, url: () => 'https://example.invalid/denied' };
  await assert.rejects(navigate(page, 'reload', allowed, fail), /origin_escape/);
});
