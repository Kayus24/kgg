"use strict";

// Shared bounded navigation for the existing one-shot and persistent hosts.
async function navigate(page, operation, allowedUrl, fail) {
  if (operation === "back") {
    const cdp = await page.context().newCDPSession(page);
    let history;
    try { history = await cdp.send("Page.getNavigationHistory"); }
    finally { await cdp.detach(); }
    const previous = history.entries[history.currentIndex - 1];
    if (!previous || previous.url === "about:blank") fail("back_history_unavailable");
    if (!allowedUrl(previous.url)) fail("origin_escape");
  }
  try {
    if (operation === "reload") await page.reload({ waitUntil: "domcontentloaded", timeout: 5000 });
    else if (operation === "back") await page.goBack({ waitUntil: "domcontentloaded", timeout: 5000 });
    else fail("step_operation_invalid");
  } catch (error) {
    if (error.name === "TimeoutError") fail("navigation_timeout");
    throw error;
  }
  if (!allowedUrl(page.url())) fail("origin_escape");
  return true;
}

module.exports = { navigate };
