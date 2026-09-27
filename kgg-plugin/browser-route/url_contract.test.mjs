import test from "node:test";
import assert from "node:assert/strict";
import { canonicalChatgptUrl } from "./url_contract.mjs";

const direct = "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555";

test("accepts direct /c route", () => {
  assert.equal(canonicalChatgptUrl(direct), direct);
});

test("canonicalizes GPT project route", () => {
  assert.equal(
    canonicalChatgptUrl("https://chatgpt.com/g/g-xyz/c/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    "https://chatgpt.com/c/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  );
});

test("strips query and fragment", () => {
  assert.equal(
    canonicalChatgptUrl(direct + "?foo=1#bar"),
    direct
  );
});
test("normalizes www host", () => {
  assert.equal(
    canonicalChatgptUrl("https://www.chatgpt.com/c/abc_123"),
    "https://chatgpt.com/c/abc_123"
  );
});

test("rejects share routes", () => {
  assert.equal(canonicalChatgptUrl("https://chatgpt.com/share/abc"), null);
});

test("rejects ChatGPT home", () => {
  assert.equal(canonicalChatgptUrl("https://chatgpt.com/"), null);
});

test("rejects lookalike host", () => {
  assert.equal(canonicalChatgptUrl("https://chatgpt.example/c/abc"), null);
});

test("rejects nested redirect bait", () => {
  assert.equal(
    canonicalChatgptUrl("https://evil.example/?next=https://chatgpt.com/c/abc"),
    null
  );
});
test("rejects non-https", () => {
  assert.equal(canonicalChatgptUrl("http://chatgpt.com/c/abc"), null);
});

test("rejects malformed or oversized ids", () => {
  assert.equal(canonicalChatgptUrl("https://chatgpt.com/c/%0A"), null);
  assert.equal(canonicalChatgptUrl("https://chatgpt.com/c/" + "a".repeat(129)), null);
});

test("rejects credentials and explicit ports", () => {
  assert.equal(canonicalChatgptUrl("https://user@chatgpt.com/c/abc"), null);
  assert.equal(canonicalChatgptUrl("https://chatgpt.com:443/c/abc"), null);
});
