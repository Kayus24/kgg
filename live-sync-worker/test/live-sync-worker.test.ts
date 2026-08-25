import { env } from "cloudflare:workers";
import {
  SELF,
  evictAllDurableObjects,
  reset,
  runDurableObjectAlarm,
  runInDurableObject,
} from "cloudflare:test";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  base64UrlDecode,
  base64UrlEncode,
  nowIso,
  randomBase64Url,
  sha256Base64Url,
  utf8,
} from "../src/encoding";
import {
  MAX_DATA_FRAMES,
  MAX_FRAME_BYTES,
} from "../src/protocol";
import type { SessionRecord } from "../src/protocol";

type RuntimeEnv = {
  LIVE_SYNC_SESSIONS: DurableObjectNamespace;
};

const runtimeEnv = env as unknown as RuntimeEnv;

function testNamespace(): DurableObjectNamespace {
  try {
    return runtimeEnv.LIVE_SYNC_SESSIONS.jurisdiction("eu");
  } catch (error) {
    if (error instanceof Error && error.message === "Jurisdiction restrictions are not implemented in workerd.") {
      return runtimeEnv.LIVE_SYNC_SESSIONS;
    }
    throw error;
  }
}

afterEach(async () => {
  await reset();
  await evictAllDurableObjects({ webSockets: "close" });
  vi.restoreAllMocks();
});

async function jsonBody(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (text === "") {
    throw new Error(`empty response body status=${response.status} content-type=${response.headers.get("Content-Type") ?? ""}`);
  }
  return JSON.parse(text) as Record<string, unknown>;
}

async function reserve() {
  const therapistToken = randomBase64Url(32);
  const response = await SELF.fetch("http://localhost/v1/sessions/reserve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ therapistTokenHash: await sha256Base64Url(therapistToken) }),
  });
  expect(response.status).toBe(201);
  const body = await jsonBody(response);
  expect(body.code).toMatch(/^[0-9]{8}$/);
  return { code: body.code as string, therapistToken };
}

async function challenge(code: string) {
  const response = await SELF.fetch(`http://localhost/v1/sessions/${code}/challenge`);
  expect(response.status).toBe(200);
  return await jsonBody(response);
}

function concatBytes(...parts: Uint8Array[]): Uint8Array {
  const result = new Uint8Array(parts.reduce((total, part) => total + part.byteLength, 0));
  let offset = 0;
  for (const part of parts) {
    result.set(part, offset);
    offset += part.byteLength;
  }
  return result;
}

function ownedBuffer(value: Uint8Array): ArrayBuffer {
  const buffer = new ArrayBuffer(value.byteLength);
  new Uint8Array(buffer).set(value);
  return buffer;
}

async function makeJoinProof(pairingSecret: string, sessionId: string, sessionSalt: string): Promise<string> {
  const keyBytes = base64UrlDecode(pairingSecret);
  const sessionIdBytes = base64UrlDecode(sessionId);
  const sessionSaltBytes = base64UrlDecode(sessionSalt);
  if (keyBytes === null || sessionIdBytes === null || sessionSaltBytes === null) {
    throw new Error("synthetic test material was not base64url");
  }
  const key = await crypto.subtle.importKey("raw", ownedBuffer(keyBytes), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const data = concatBytes(utf8("KGG-LIVE-JOIN-V1"), sessionIdBytes, sessionSaltBytes);
  return base64UrlEncode(await crypto.subtle.sign("HMAC", key, ownedBuffer(data)));
}

async function armAndJoin(code: string, therapistToken: string) {
  const pairingSecret = randomBase64Url(32);
  const challengeBody = await challenge(code);
  const joinProof = await makeJoinProof(pairingSecret, challengeBody.sessionId as string, challengeBody.sessionSalt as string);
  const armResponse = await SELF.fetch(`http://localhost/v1/sessions/${code}/arm`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${therapistToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ joinProof }),
  });
  expect(armResponse.status).toBe(200);
  const patientToken = randomBase64Url(32);
  const joinResponse = await SELF.fetch(`http://localhost/v1/sessions/${code}/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ joinProof, patientTokenHash: await sha256Base64Url(patientToken) }),
  });
  expect(joinResponse.status).toBe(200);
  return { joinProof, patientToken };
}

async function openSocket(code: string): Promise<WebSocket> {
  const response = await SELF.fetch(`http://localhost/v1/sessions/${code}/socket`, {
    headers: { Upgrade: "websocket" },
  });
  expect(response.status).toBe(101);
  const socket = response.webSocket;
  expect(socket).not.toBeNull();
  socket?.accept();
  return socket as WebSocket;
}

function nextMessage(socket: WebSocket): Promise<string> {
  return new Promise((resolve, reject) => {
    socket.addEventListener("message", (event) => resolve(String(event.data)), { once: true });
    socket.addEventListener("error", () => reject(new Error("synthetic websocket error")), { once: true });
  });
}

function nextClose(socket: WebSocket): Promise<CloseEvent> {
  if (socket.readyState === WebSocket.CLOSED) {
    return Promise.resolve(new CloseEvent("close", { code: 1000 }));
  }
  return new Promise((resolve) => socket.addEventListener("close", (event) => resolve(event), { once: true }));
}

function frame(sender: "therapist" | "patient", sequence: number, ciphertext = randomBase64Url(32)): string {
  return JSON.stringify({
    v: 1,
    messageId: randomBase64Url(16),
    sender,
    sequence,
    nonce: randomBase64Url(12),
    ciphertext,
    createdAt: nowIso(),
  });
}

async function authenticate(socket: WebSocket, role: "therapist" | "patient", token: string): Promise<void> {
  const response = nextMessage(socket);
  socket.send(JSON.stringify({ type: "auth", role, token }));
  expect(JSON.parse(await response)).toEqual({ type: "auth_ok", role });
}

async function storedSession(code: string): Promise<SessionRecord | undefined> {
  const namespace = testNamespace();
  const stub = namespace.get(namespace.idFromName(code));
  return runInDurableObject(stub, async (_instance, state) => await state.storage.get<SessionRecord>("session"));
}

describe("KGG ticket 034 live-sync worker", () => {
  it("runs reserve/arm/challenge/join/socket relay and deleteAll", async () => {
    const { code, therapistToken } = await reserve();
    const armed = await armAndJoin(code, therapistToken);
    const therapistSocket = await openSocket(code);
    const patientSocket = await openSocket(code);
    await authenticate(therapistSocket, "therapist", therapistToken);
    await authenticate(patientSocket, "patient", armed.patientToken);

    const therapistFrame = frame("therapist", 1);
    const patientReceived = nextMessage(patientSocket);
    therapistSocket.send(therapistFrame);
    expect(JSON.parse(await patientReceived)).toMatchObject(JSON.parse(therapistFrame));

    const patientFrame = frame("patient", 1);
    const therapistReceived = nextMessage(therapistSocket);
    patientSocket.send(patientFrame);
    expect(JSON.parse(await therapistReceived)).toMatchObject(JSON.parse(patientFrame));

    const therapistClosed = nextClose(therapistSocket);
    const patientClosed = nextClose(patientSocket);
    const deleted = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${therapistToken}` },
    });
    expect(deleted.status).toBe(200);
    expect((await jsonBody(deleted)).deleted).toBe(true);
    expect((await storedSession(code))).toBeUndefined();
    expect((await therapistClosed).code).toBe(4000);
    expect((await patientClosed).code).toBe(4000);
  });

  it("requires the session-bound therapist token for deletion", async () => {
    const { code, therapistToken } = await reserve();
    const { patientToken } = await armAndJoin(code, therapistToken);
    const therapistSocket = await openSocket(code);
    const patientSocket = await openSocket(code);
    await authenticate(therapistSocket, "therapist", therapistToken);
    await authenticate(patientSocket, "patient", patientToken);

    const unauthenticated = await SELF.fetch(`http://localhost/v1/sessions/${code}`, { method: "DELETE" });
    expect(unauthenticated.status).toBe(401);
    expect(await storedSession(code)).toBeDefined();

    const wrongToken = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${randomBase64Url(32)}` },
    });
    expect(wrongToken.status).toBe(401);
    expect(await storedSession(code)).toBeDefined();

    const malformedAuthorization = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Basic ${therapistToken}` },
    });
    expect(malformedAuthorization.status).toBe(401);
    expect(await storedSession(code)).toBeDefined();

    const patientDelete = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${patientToken}` },
    });
    expect(patientDelete.status).toBe(401);
    expect(await storedSession(code)).toBeDefined();

    const foreign = await reserve();
    const foreignDelete = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${foreign.therapistToken}` },
    });
    expect(foreignDelete.status).toBe(401);
    expect(await storedSession(code)).toBeDefined();
    expect(await storedSession(foreign.code)).toBeDefined();

    const relayed = frame("therapist", 1);
    const received = nextMessage(patientSocket);
    therapistSocket.send(relayed);
    expect(JSON.parse(await received)).toMatchObject(JSON.parse(relayed));

    const therapistClosed = nextClose(therapistSocket);
    const patientClosed = nextClose(patientSocket);
    const deleted = await SELF.fetch(`http://localhost/v1/sessions/${code}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${therapistToken}` },
    });
    expect(deleted.status).toBe(200);
    expect((await jsonBody(deleted)).deleted).toBe(true);
    expect(await storedSession(code)).toBeUndefined();
    expect(await storedSession(foreign.code)).toBeDefined();
    expect((await therapistClosed).code).toBe(4000);
    expect((await patientClosed).code).toBe(4000);
  });

  it("rejects wrong proof, locks on the fifth false join, and rejects a sixth attempt", async () => {
    const { code, therapistToken } = await reserve();
    const challengeBody = await challenge(code);
    const pairingSecret = randomBase64Url(32);
    const correctProof = await makeJoinProof(pairingSecret, challengeBody.sessionId as string, challengeBody.sessionSalt as string);
    const armResponse = await SELF.fetch(`http://localhost/v1/sessions/${code}/arm`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${therapistToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ joinProof: correctProof }),
    });
    expect(armResponse.status).toBe(200);
    const patientTokenHash = await sha256Base64Url(randomBase64Url(32));
    for (let attempt = 1; attempt <= 6; attempt += 1) {
      const response = await SELF.fetch(`http://localhost/v1/sessions/${code}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ joinProof: randomBase64Url(32), patientTokenHash }),
      });
      expect(response.status).toBe(attempt < 5 ? 401 : 423);
    }
    const correctAfterLock = await SELF.fetch(`http://localhost/v1/sessions/${code}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ joinProof: correctProof, patientTokenHash }),
    });
    expect(correctAfterLock.status).toBe(423);
    expect((await storedSession(code))?.locked).toBe(true);
  });

  it("stores only hashes and encrypted outer frames, and replays offline backlog after reconnect", async () => {
    const { code, therapistToken } = await reserve();
    const { patientToken } = await armAndJoin(code, therapistToken);
    const therapistSocket = await openSocket(code);
    await authenticate(therapistSocket, "therapist", therapistToken);
    const ciphertext = randomBase64Url(32);
    therapistSocket.send(frame("therapist", 1, ciphertext));
    const persisted = await storedSession(code);
    expect(persisted?.backlog).toHaveLength(1);
    const serialized = JSON.stringify(persisted);
    expect(serialized).not.toContain(therapistToken);
    expect(serialized).not.toContain(patientToken);
    expect(serialized).not.toContain("patientName");
    expect(serialized).not.toContain("diagnosis");
    expect(serialized).not.toContain("trainingValue");
    expect(serialized).toContain(ciphertext);

    const patientSocket = await openSocket(code);
    const authOk = nextMessage(patientSocket);
    patientSocket.send(JSON.stringify({ type: "auth", role: "patient", token: patientToken }));
    expect(JSON.parse(await authOk)).toEqual({ type: "auth_ok", role: "patient" });
    const queued = nextMessage(patientSocket);
    expect(JSON.parse(await queued).ciphertext).toBe(ciphertext);
    expect((await storedSession(code))?.backlog).toHaveLength(0);
  });

  it("enforces token authentication, role replacement, frame boundaries and frame quota", async () => {
    const { code, therapistToken } = await reserve();
    const { patientToken } = await armAndJoin(code, therapistToken);
    const wrongTokenSocket = await openSocket(code);
    const wrongClose = nextClose(wrongTokenSocket);
    wrongTokenSocket.send(JSON.stringify({ type: "auth", role: "therapist", token: randomBase64Url(32) }));
    expect((await wrongClose).code).toBe(4003);

    const therapistSocket = await openSocket(code);
    await authenticate(therapistSocket, "therapist", therapistToken);
    const replacementSocket = await openSocket(code);
    const replaced = nextClose(therapistSocket);
    await authenticate(replacementSocket, "therapist", therapistToken);
    expect((await replaced).code).toBe(4008);

    const oversized = nextClose(replacementSocket);
    replacementSocket.send(frame("therapist", 1, "A".repeat(MAX_FRAME_BYTES)));
    expect((await oversized).code).toBe(4002);

    const quotaSocket = await openSocket(code);
    await authenticate(quotaSocket, "therapist", therapistToken);
    const current = await storedSession(code);
    if (current === undefined) {
      throw new Error("synthetic session disappeared");
    }
    const namespace = testNamespace();
    const stub = namespace.get(namespace.idFromName(code));
    await runInDurableObject(stub, async (_instance, state) => {
      current.acceptedFrames = MAX_DATA_FRAMES;
      await state.storage.put("session", current);
    });
    const quotaClose = nextClose(quotaSocket);
    quotaSocket.send(frame("therapist", 2));
    expect((await quotaClose).code).toBe(4009);
    expect(patientToken).toMatch(/^[A-Za-z0-9_-]{43}$/);
  });

  it("fails closed for CORS and does not log request bodies, tokens or frames", async () => {
    const denied = await SELF.fetch("http://localhost/health", { headers: { Origin: "https://example.com" } });
    expect(denied.status).toBe(403);
    const deniedPrivate = await SELF.fetch("http://localhost/health", { headers: { Origin: "http://10.0.0.7:4173" } });
    expect(deniedPrivate.status).toBe(403);
    const allowed = await SELF.fetch("http://localhost/health", { headers: { Origin: "http://localhost:5173" } });
    expect(allowed.status).toBe(200);
    expect(allowed.headers.get("Access-Control-Allow-Origin")).toBe("http://localhost:5173");
    expect((await jsonBody(allowed)).mode).toBe("test");
    const preflight = await SELF.fetch("http://localhost/health", {
      method: "OPTIONS",
      headers: {
        Origin: "http://192.168.1.44:4173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization, content-type",
      },
    });
    expect(preflight.status).toBe(204);
    expect(preflight.headers.get("Access-Control-Allow-Origin")).toBe("http://192.168.1.44:4173");

    const log = vi.spyOn(console, "log");
    const error = vi.spyOn(console, "error");
    const warn = vi.spyOn(console, "warn");
    await SELF.fetch("http://localhost/v1/sessions/reserve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ therapistTokenHash: await sha256Base64Url("synthetic-token") }),
    });
    expect(log).not.toHaveBeenCalled();
    expect(error).not.toHaveBeenCalled();
    expect(warn).not.toHaveBeenCalled();
  });

  it("expires through the short explicit test TTL and removes durable storage", async () => {
    const { code, therapistToken } = await reserve();
    await armAndJoin(code, therapistToken);
    await new Promise((resolve) => setTimeout(resolve, 2_200));
    const namespace = testNamespace();
    const stub = namespace.get(namespace.idFromName(code));
    await runDurableObjectAlarm(stub);
    const challengeResponse = await SELF.fetch(`http://localhost/v1/sessions/${code}/challenge`);
    expect(challengeResponse.status).toBe(404);
    const deleteResponse = await SELF.fetch(`http://localhost/v1/sessions/${code}`, { method: "DELETE" });
    expect(deleteResponse.status).toBe(404);
    expect(await storedSession(code)).toBeUndefined();
  });
});
