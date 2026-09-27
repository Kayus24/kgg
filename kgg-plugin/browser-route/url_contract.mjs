const MAX_URL_LENGTH = 2048;
const MAX_CONVERSATION_ID_LENGTH = 128;
const CONVERSATION_ID_RE = /^[A-Za-z0-9_-]+$/;

export function canonicalChatgptUrl(value) {
  if (typeof value !== "string") return null;
  const raw = value.trim();
  if (!raw || raw.length > MAX_URL_LENGTH) return null;

  const authorityMatch = raw.match(/^https:\/\/([^/?#]+)(?:[/?#]|$)/i);
  const authority = authorityMatch?.[1]?.toLowerCase();
  if (authority !== "chatgpt.com" && authority !== "www.chatgpt.com") {
    return null;
  }

  let url;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }

  if (url.protocol !== "https:") return null;
  if (url.username || url.password || url.port) return null;

  const host = url.hostname.toLowerCase();
  if (host !== "chatgpt.com" && host !== "www.chatgpt.com") {
    return null;
  }

  const segments = url.pathname.split("/").filter(Boolean);
  let conversationId = null;
  if (segments.length === 2 && segments[0] === "c") {
    conversationId = segments[1];
  } else if (
    segments.length === 4 &&
    segments[0] === "g" &&
    segments[1] &&
    segments[2] === "c"
  ) {
    conversationId = segments[3];
  }

  if (
    !conversationId ||
    conversationId.length > MAX_CONVERSATION_ID_LENGTH ||
    !CONVERSATION_ID_RE.test(conversationId)
  ) {
    return null;
  }

  return `https://chatgpt.com/c/${conversationId}`;
}
