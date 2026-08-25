import { DurableObject } from "cloudflare:workers";
import {
  constantTimeEqualBase64Url,
  isBase64UrlOfBytes,
  isIsoDate,
  nowIso,
  randomBase64Url,
  randomDecimalCode,
  sha256Base64Url,
  utf8,
  utf8Decode,
} from "./encoding";
import {
  AUTH_TIMEOUT_MS,
  backlogBytes,
  MAX_BACKLOG_BYTES,
  MAX_BODY_BYTES,
  MAX_DATA_FRAMES,
  MAX_FRAME_BYTES,
  PROTOCOL_NAME,
  PROTOCOL_VERSION,
  SESSION_TTL_MS,
  validateOuterFrame,
  frameReplayKey,
  isSessionRecord,
  isSocketAttachment,
  isOpaqueToken,
  parseArmBody,
  parseAuthFrame,
  parseJoinBody,
  parseReserveBody,
} from "./protocol";
import type { JoinBody, Role, SessionRecord, SocketAttachment } from "./protocol";

export interface Env {
  LIVE_SYNC_MODE?: string;
  TEST_TTL_SECONDS?: string;
  TEST_PRIVATE_ORIGINS?: string;
  LIVE_SYNC_SESSIONS: DurableObjectNamespace;
}

type HibernatableWebSocket = WebSocket & {
  serializeAttachment(value: unknown): void;
  deserializeAttachment(): unknown;
};

type SessionInit = {
  sessionId: string;
  sessionSalt: string;
  expiresAt: string;
  therapistTokenHash: string;
};

const WORKER_VERSION = "0.1.0";
const SESSION_ROUTE = /^\/v1\/sessions\/([0-9]{8})(?:\/(arm|challenge|join|socket))?$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function jsonResponse(value: unknown, status = 200, extraHeaders?: HeadersInit): Response {
  const headers = new Headers(extraHeaders);
  headers.set("Content-Type", "application/json; charset=utf-8");
  headers.set("Cache-Control", "no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "no-referrer");
  return new Response(JSON.stringify(value), { status, headers });
}

function emptyResponse(status = 204, extraHeaders?: HeadersInit): Response {
  const headers = new Headers(extraHeaders);
  headers.set("Cache-Control", "no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "no-referrer");
  return new Response(null, { status, headers });
}

function errorResponse(code: string, status: number, headers?: HeadersInit): Response {
  return jsonResponse({ error: code }, status, headers);
}

function modeOf(env: Env): "off" | "test" | "production" {
  const mode = env.LIVE_SYNC_MODE?.trim().toLowerCase();
  if (mode === "test") {
    return "test";
  }
  if (mode === "production") {
    return "production";
  }
  return "off";
}

function sessionTtlMs(env: Env, mode: "off" | "test" | "production"): number {
  if (mode !== "test") {
    return SESSION_TTL_MS;
  }
  const seconds = Number.parseInt(env.TEST_TTL_SECONDS ?? "", 10);
  if (!Number.isInteger(seconds) || seconds < 1 || seconds * 1000 > SESSION_TTL_MS) {
    return SESSION_TTL_MS;
  }
  return seconds * 1000;
}

function isPrivateHostname(hostname: string): boolean {
  const host = hostname.toLowerCase().replace(/^\[/, "").replace(/\]$/, "");
  if (host === "localhost" || host === "::1") {
    return true;
  }
  if (host.startsWith("fc") || host.startsWith("fd")) {
    return true;
  }
  const parts = host.split(".");
  if (parts.length !== 4 || parts.some((part) => !/^\d+$/.test(part))) {
    return false;
  }
  const octets = parts.map((part) => Number(part));
  if (octets.some((octet) => octet < 0 || octet > 255)) {
    return false;
  }
  return octets[0] === 10
    || (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)
    || (octets[0] === 192 && octets[1] === 168);
}

function isAllowedTestOrigin(origin: string, env: Env): boolean {
  if (origin === "null") {
    return false;
  }
  let candidate: URL;
  try {
    candidate = new URL(origin);
  } catch {
    return false;
  }
  if ((candidate.protocol !== "http:" && candidate.protocol !== "https:") || candidate.origin !== origin || !isPrivateHostname(candidate.hostname)) {
    return false;
  }
  if (candidate.hostname.toLowerCase() === "localhost" || candidate.hostname === "127.0.0.1") {
    return true;
  }
  const explicit = (env.TEST_PRIVATE_ORIGINS ?? "")
    .split(",")
    .map((value) => value.trim())
    .filter((value) => value.length > 0);
  return explicit.some((value) => {
    try {
      const parsed = new URL(value);
      return parsed.origin === origin && isPrivateHostname(parsed.hostname) && (parsed.protocol === "http:" || parsed.protocol === "https:");
    } catch {
      return false;
    }
  });
}

function corsOrigin(request: Request, env: Env, mode: "off" | "test" | "production"): string | null | false {
  const origin = request.headers.get("Origin");
  if (origin === null) {
    return null;
  }
  return mode === "test" && isAllowedTestOrigin(origin, env) ? origin : false;
}

function withCors(response: Response, origin: string | null): Response {
  if (origin === null) {
    return response;
  }
  try {
    response.headers.set("Vary", "Origin");
    response.headers.set("Access-Control-Allow-Origin", origin);
  } catch {
    // Durable Object responses are immutable after crossing the binding. The
    // DO adds the same headers before returning its response.
  }
  return response;
}

function validatePreflight(request: Request): boolean {
  const requestedMethod = request.headers.get("Access-Control-Request-Method");
  if (requestedMethod !== null && !["GET", "POST", "DELETE"].includes(requestedMethod.toUpperCase())) {
    return false;
  }
  const requestedHeaders = request.headers.get("Access-Control-Request-Headers");
  if (requestedHeaders === null || requestedHeaders.trim() === "") {
    return true;
  }
  const allowed = new Set(["authorization", "content-type"]);
  return requestedHeaders.split(",").map((value) => value.trim().toLowerCase()).every((value) => allowed.has(value));
}

function addPreflightHeaders(response: Response, origin: string | null): Response {
  response.headers.set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
  response.headers.set("Access-Control-Allow-Headers", "Authorization, Content-Type");
  response.headers.set("Access-Control-Max-Age", "300");
  return withCors(response, origin);
}

async function readRequestText(request: Request, maxBytes = MAX_BODY_BYTES): Promise<string | null> {
  const declaredLength = request.headers.get("Content-Length");
  if (declaredLength !== null) {
    const length = Number.parseInt(declaredLength, 10);
    if (!Number.isSafeInteger(length) || length < 0 || length > maxBytes) {
      return null;
    }
  }
  try {
    const body = await request.arrayBuffer();
    if (body.byteLength > maxBytes) {
      return null;
    }
    return utf8Decode(body);
  } catch {
    return null;
  }
}

function parseBearerToken(request: Request): string | null {
  const value = request.headers.get("Authorization");
  if (value === null || !value.startsWith("Bearer ")) {
    return null;
  }
  const token = value.slice("Bearer ".length);
  return isOpaqueToken(token) ? token : null;
}

function sessionNamespace(env: Env): DurableObjectNamespace {
  try {
    return env.LIVE_SYNC_SESSIONS.jurisdiction("eu");
  } catch (error) {
    // The local workerd used by the test harness does not implement jurisdiction yet.
    // The fallback is reachable only in explicit test mode; deployed modes fail closed.
    if (modeOf(env) === "test" && error instanceof Error && error.message === "Jurisdiction restrictions are not implemented in workerd.") {
      return env.LIVE_SYNC_SESSIONS;
    }
    throw error;
  }
}

function sessionStub(env: Env, code: string): DurableObjectStub {
  const euNamespace = sessionNamespace(env);
  const id = euNamespace.idFromName(code);
  return euNamespace.get(id);
}

function internalRequest(request: Request, path: string, body?: string): Request {
  const headers = new Headers(request.headers);
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    headers.delete("Content-Length");
  }
  return new Request(`https://kgg-live-sync.internal${path}`, {
    method: request.method,
    headers,
    body: body === undefined ? undefined : body,
  });
}

async function reserveSession(request: Request, env: Env, mode: "off" | "test" | "production"): Promise<Response> {
  const bodyText = await readRequestText(request);
  const body = bodyText === null ? null : parseReserveBody(bodyText);
  if (body === null) {
    return errorResponse("INVALID_REQUEST", 400);
  }
  const ttl = sessionTtlMs(env, mode);
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const code = randomDecimalCode();
    const init: SessionInit = {
      sessionId: randomBase64Url(16),
      sessionSalt: randomBase64Url(32),
      expiresAt: nowIso(Date.now() + ttl),
      therapistTokenHash: body.therapistTokenHash,
    };
    const response = await sessionStub(env, code).fetch(internalRequest(request, "/__internal/reserve", JSON.stringify(init)));
    if (response.status === 409) {
      continue;
    }
    if (!response.ok) {
      return errorResponse("RESERVE_FAILED", 503);
    }
    return jsonResponse({ code, expiresAt: init.expiresAt, protocolVersion: PROTOCOL_NAME }, 201);
  }
  return errorResponse("RESERVE_FAILED", 503);
}

async function forwardJson(request: Request, env: Env, code: string, path: string, parser: (value: string) => object | null): Promise<Response> {
  const bodyText = await readRequestText(request);
  const body = bodyText === null ? null : parser(bodyText);
  if (body === null) {
    return errorResponse("INVALID_REQUEST", 400);
  }
  return sessionStub(env, code).fetch(internalRequest(request, path, JSON.stringify(body)));
}

async function handleWorkerRequest(request: Request, env: Env): Promise<Response> {
  const mode = modeOf(env);
  const origin = corsOrigin(request, env, mode);
  if (origin === false) {
    return errorResponse("CORS_DENIED", 403);
  }
  if (request.method === "OPTIONS") {
    if (mode !== "test" || !validatePreflight(request)) {
      return errorResponse("CORS_DENIED", 403);
    }
    return addPreflightHeaders(emptyResponse(), origin);
  }
  const url = new URL(request.url);
  if (url.pathname === "/health" && request.method === "GET" && url.search === "") {
    return jsonResponse({ version: WORKER_VERSION, mode, serverTime: nowIso() });
  }
  if (mode !== "test") {
    return errorResponse(mode === "production" ? "PRODUCTION_DISABLED" : "LIVE_SYNC_OFF", 404);
  }
  if (url.search !== "") {
    return errorResponse("INVALID_REQUEST", 400);
  }
  if (url.pathname === "/v1/sessions/reserve" && request.method === "POST") {
    return reserveSession(request, env, mode);
  }
  const match = SESSION_ROUTE.exec(url.pathname);
  if (match === null || match[1] === undefined) {
    return errorResponse("NOT_FOUND", 404);
  }
  const code = match[1];
  const operation = match[2];
  if (operation === "arm" && request.method === "POST") {
    const token = parseBearerToken(request);
    if (token === null) {
      return errorResponse("UNAUTHORIZED", 401);
    }
    // Authorization is passed only to the Durable Object request and never returned.
    return forwardJson(request, env, code, "/__internal/arm", parseArmBody);
  }
  if (operation === "challenge" && request.method === "GET") {
    return sessionStub(env, code).fetch(internalRequest(request, "/__internal/challenge"));
  }
  if (operation === "join" && request.method === "POST") {
    return forwardJson(request, env, code, "/__internal/join", parseJoinBody);
  }
  if (operation === "socket" && request.method === "GET") {
    if (request.headers.get("Upgrade")?.toLowerCase() !== "websocket") {
      return errorResponse("UPGRADE_REQUIRED", 426);
    }
    return sessionStub(env, code).fetch(internalRequest(request, "/__internal/socket"));
  }
  if (operation === undefined && request.method === "DELETE") {
    return sessionStub(env, code).fetch(internalRequest(request, "/__internal/delete"));
  }
  return errorResponse("METHOD_NOT_ALLOWED", 405);
}

export async function fetch(request: Request, env: Env): Promise<Response> {
  try {
    const mode = modeOf(env);
    const origin = corsOrigin(request, env, mode);
    const response = await handleWorkerRequest(request, env);
    return withCors(response, origin === false ? null : origin);
  } catch {
    return withCors(errorResponse("INTERNAL_ERROR", 500), null);
  }
}

export default { fetch } satisfies ExportedHandler<Env>;

export class LiveSyncSession extends DurableObject<Env, unknown> {
  private operationChain: Promise<unknown> = Promise.resolve();

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
  }

  private runExclusive<T>(operation: () => Promise<T>): Promise<T> {
    const next = this.operationChain.then(operation, operation);
    this.operationChain = next.then(() => undefined, () => undefined);
    return next;
  }

  async fetch(request: Request): Promise<Response> {
    return this.runExclusive(() => this.handleInternalRequest(request));
  }

  async alarm(): Promise<void> {
    await this.runExclusive(async () => {
      const record = await this.loadRecord();
      if (record === null) {
        await this.ctx.storage.deleteAlarm();
        return;
      }
      if (Date.parse(record.expiresAt) <= Date.now()) {
        await this.expireAndDelete();
        return;
      }
      const sockets = this.ctx.getWebSockets();
      for (const socket of sockets) {
        const attachment = this.attachmentOf(socket);
        if (attachment !== null && attachment.role === null && attachment.authDeadline <= Date.now()) {
          this.closeSocket(socket, 4003, "authentication timeout");
        }
      }
      await this.scheduleNextAlarm(record);
    });
  }

  async webSocketMessage(socket: WebSocket, message: string | ArrayBuffer): Promise<void> {
    await this.runExclusive(() => this.handleWebSocketMessage(socket as HibernatableWebSocket, message));
  }

  async webSocketClose(): Promise<void> {
    // Connection ownership is derived from WebSocket attachments; no socket data is persisted here.
  }

  async webSocketError(): Promise<void> {
    // Errors do not cause any application state mutation or logging.
  }

  private async handleInternalRequest(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    let response: Response;
    if (path === "/__internal/reserve" && request.method === "POST") {
      response = await this.handleReserve(request);
    } else if (path === "/__internal/arm" && request.method === "POST") {
      response = await this.handleArm(request);
    } else if (path === "/__internal/challenge" && request.method === "GET") {
      response = await this.handleChallenge();
    } else if (path === "/__internal/join" && request.method === "POST") {
      response = await this.handleJoin(request);
    } else if (path === "/__internal/socket" && request.method === "GET") {
      response = await this.handleSocket(request);
    } else if (path === "/__internal/delete" && request.method === "DELETE") {
      response = await this.handleDelete(request);
    } else {
      response = errorResponse("NOT_FOUND", 404);
    }
    return this.addDurableObjectCors(request, response);
  }

  private addDurableObjectCors(request: Request, response: Response): Response {
    const origin = corsOrigin(request, this.env, modeOf(this.env));
    if (origin !== null && origin !== false) {
      response.headers.set("Vary", "Origin");
      response.headers.set("Access-Control-Allow-Origin", origin);
    }
    return response;
  }

  private async loadRecord(): Promise<SessionRecord | null> {
    const value = await this.ctx.storage.get<unknown>("session");
    return isSessionRecord(value) ? value : null;
  }

  private async saveRecord(record: SessionRecord): Promise<void> {
    await this.ctx.storage.put("session", record);
  }

  private async liveRecord(): Promise<SessionRecord | null> {
    const record = await this.loadRecord();
    if (record === null) {
      return null;
    }
    if (Date.parse(record.expiresAt) <= Date.now()) {
      await this.expireAndDelete();
      return null;
    }
    return record;
  }

  private async handleReserve(request: Request): Promise<Response> {
    const text = await readRequestText(request);
    if (text === null) {
      return errorResponse("INVALID_REQUEST", 400);
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(text) as unknown;
    } catch {
      return errorResponse("INVALID_REQUEST", 400);
    }
    if (!isRecord(parsed)
      || Object.keys(parsed).sort().join(",") !== ["expiresAt", "sessionId", "sessionSalt", "therapistTokenHash"].sort().join(",")
      || !isBase64UrlOfBytes(parsed.sessionId, 16)
      || !isBase64UrlOfBytes(parsed.sessionSalt, 32)
      || !isIsoDate(parsed.expiresAt)
      || !isBase64UrlOfBytes(parsed.therapistTokenHash, 32)) {
      return errorResponse("INVALID_REQUEST", 400);
    }
    const expiresAt = Date.parse(parsed.expiresAt as string);
    if (expiresAt <= Date.now() || expiresAt > Date.now() + SESSION_TTL_MS) {
      return errorResponse("INVALID_REQUEST", 400);
    }
    const current = await this.loadRecord();
    if (current !== null) {
      if (Date.parse(current.expiresAt) <= Date.now()) {
        await this.expireAndDelete();
      } else {
        return errorResponse("SESSION_EXISTS", 409);
      }
    }
    const record: SessionRecord = {
      schemaVersion: 1,
      sessionId: parsed.sessionId as string,
      sessionSalt: parsed.sessionSalt as string,
      expiresAt: parsed.expiresAt as string,
      therapistTokenHash: parsed.therapistTokenHash as string,
      joinProof: null,
      patientTokenHash: null,
      joinFailures: 0,
      locked: false,
      acceptedFrames: 0,
      replayHashes: [],
      backlog: [],
    };
    await this.saveRecord(record);
    await this.scheduleNextAlarm(record);
    return jsonResponse({ reserved: true }, 201);
  }

  private async handleArm(request: Request): Promise<Response> {
    const token = parseBearerToken(request);
    const text = await readRequestText(request);
    const body = text === null ? null : parseArmBody(text);
    if (token === null || body === null) {
      return errorResponse("UNAUTHORIZED", 401);
    }
    const record = await this.liveRecord();
    if (record === null) {
      return errorResponse("SESSION_NOT_FOUND", 404);
    }
    if (record.locked) {
      return errorResponse("SESSION_LOCKED", 423);
    }
    const tokenHash = await sha256Base64Url(token);
    if (!constantTimeEqualBase64Url(record.therapistTokenHash, tokenHash, 32)) {
      return errorResponse("UNAUTHORIZED", 401);
    }
    if (record.joinProof !== null && !constantTimeEqualBase64Url(record.joinProof, body.joinProof, 32)) {
      return errorResponse("ALREADY_ARMED", 409);
    }
    record.joinProof = body.joinProof;
    await this.saveRecord(record);
    return jsonResponse({ armed: true });
  }

  private async handleChallenge(): Promise<Response> {
    const record = await this.liveRecord();
    if (record === null) {
      return errorResponse("SESSION_NOT_FOUND", 404);
    }
    if (record.locked) {
      return errorResponse("SESSION_LOCKED", 423);
    }
    return jsonResponse({
      sessionId: record.sessionId,
      sessionSalt: record.sessionSalt,
      expiresAt: record.expiresAt,
      protocolVersion: PROTOCOL_NAME,
    });
  }

  private async handleJoin(request: Request): Promise<Response> {
    const text = await readRequestText(request);
    const body: JoinBody | null = text === null ? null : parseJoinBody(text);
    if (body === null) {
      return errorResponse("INVALID_REQUEST", 400);
    }
    const record = await this.liveRecord();
    if (record === null) {
      return errorResponse("SESSION_NOT_FOUND", 404);
    }
    if (record.locked) {
      return errorResponse("SESSION_LOCKED", 423);
    }
    if (record.joinProof === null) {
      return errorResponse("SESSION_NOT_ARMED", 409);
    }
    if (!constantTimeEqualBase64Url(record.joinProof, body.joinProof, 32)) {
      record.joinFailures += 1;
      if (record.joinFailures >= 5) {
        record.joinFailures = 5;
        record.locked = true;
        this.closeAllSockets(4004, "session locked");
      }
      await this.saveRecord(record);
      return errorResponse(record.locked ? "SESSION_LOCKED" : "JOIN_REJECTED", record.locked ? 423 : 401);
    }
    if (record.patientTokenHash !== null) {
      if (constantTimeEqualBase64Url(record.patientTokenHash, body.patientTokenHash, 32)) {
        return jsonResponse({ joined: true, alreadyJoined: true });
      }
      return errorResponse("PATIENT_ROLE_TAKEN", 409);
    }
    record.patientTokenHash = body.patientTokenHash;
    await this.saveRecord(record);
    return jsonResponse({ joined: true });
  }

  private async handleSocket(request: Request): Promise<Response> {
    const record = await this.liveRecord();
    if (record === null) {
      return errorResponse("SESSION_NOT_FOUND", 404);
    }
    if (record.locked) {
      return errorResponse("SESSION_LOCKED", 423);
    }
    if (record.joinProof === null) {
      return errorResponse("SESSION_NOT_ARMED", 409);
    }
    const pair = new WebSocketPair();
    const client = pair[0];
    const server = pair[1] as HibernatableWebSocket;
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({ schemaVersion: 1, role: null, authDeadline: Date.now() + AUTH_TIMEOUT_MS } satisfies SocketAttachment);
    await this.scheduleNextAlarm(record);
    return new Response(null, { status: 101, webSocket: client });
  }

  private attachmentOf(socket: WebSocket): SocketAttachment | null {
    try {
      const value = (socket as HibernatableWebSocket).deserializeAttachment();
      return isSocketAttachment(value) ? value : null;
    } catch {
      return null;
    }
  }

  private async handleWebSocketMessage(socket: HibernatableWebSocket, message: string | ArrayBuffer): Promise<void> {
    const attachment = this.attachmentOf(socket);
    if (attachment === null) {
      this.closeSocket(socket, 4003, "authentication required");
      return;
    }
    const text = typeof message === "string" ? message : utf8Decode(message);
    if (text === null || utf8(text).byteLength > MAX_FRAME_BYTES) {
      this.closeSocket(socket, 4002, "invalid frame");
      return;
    }
    if (attachment.role === null) {
      await this.authenticateSocket(socket, attachment, text);
      return;
    }
    await this.relayDataFrame(socket, attachment.role, text);
  }

  private async authenticateSocket(socket: HibernatableWebSocket, attachment: SocketAttachment, text: string): Promise<void> {
    if (Date.now() > attachment.authDeadline) {
      this.closeSocket(socket, 4003, "authentication timeout");
      return;
    }
    const auth = parseAuthFrame(text);
    if (auth === null) {
      this.closeSocket(socket, 4003, "authentication required");
      return;
    }
    const record = await this.liveRecord();
    if (record === null || record.locked) {
      this.closeSocket(socket, record?.locked ? 4004 : 4001, record?.locked ? "session locked" : "session expired");
      return;
    }
    const expectedHash = auth.role === "therapist" ? record.therapistTokenHash : record.patientTokenHash;
    if (expectedHash === null || record.joinProof === null) {
      this.closeSocket(socket, 4003, "role unavailable");
      return;
    }
    const providedHash = await sha256Base64Url(auth.token);
    if (!constantTimeEqualBase64Url(expectedHash, providedHash, 32)) {
      this.closeSocket(socket, 4003, "authentication failed");
      return;
    }
    for (const existing of this.ctx.getWebSockets()) {
      if (existing === socket) {
        continue;
      }
      const existingAttachment = this.attachmentOf(existing);
      if (existingAttachment?.role === auth.role) {
        this.closeSocket(existing, 4008, "replaced");
      }
    }
    socket.serializeAttachment({ schemaVersion: 1, role: auth.role, authDeadline: attachment.authDeadline } satisfies SocketAttachment);
    try {
      socket.send(JSON.stringify({ type: "auth_ok", role: auth.role }));
    } catch {
      return;
    }
    await this.flushBacklog(record, auth.role, socket);
    await this.scheduleNextAlarm(record);
  }

  private async flushBacklog(record: SessionRecord, role: Role, socket: HibernatableWebSocket): Promise<void> {
    const pending = record.backlog.filter((entry) => entry.targetRole === role);
    if (pending.length === 0) {
      return;
    }
    try {
      for (const entry of pending) {
        socket.send(entry.frame);
      }
    } catch {
      return;
    }
    record.backlog = record.backlog.filter((entry) => entry.targetRole !== role);
    await this.saveRecord(record);
  }

  private async relayDataFrame(socket: HibernatableWebSocket, sender: Role, text: string): Promise<void> {
    const frame = validateOuterFrame(text);
    if (frame === null || frame.sender !== sender) {
      this.closeSocket(socket, 4002, "invalid frame");
      return;
    }
    const record = await this.liveRecord();
    if (record === null || record.locked) {
      this.closeSocket(socket, record?.locked ? 4004 : 4001, record?.locked ? "session locked" : "session expired");
      return;
    }
    if (record.acceptedFrames >= MAX_DATA_FRAMES) {
      this.closeSocket(socket, 4009, "message limit");
      return;
    }
    const replayHash = await sha256Base64Url(frameReplayKey(frame));
    if (record.replayHashes.some((stored) => constantTimeEqualBase64Url(stored, replayHash, 32))) {
      this.closeSocket(socket, 4002, "replay");
      return;
    }
    const normalizedFrame = JSON.stringify(frame);
    const frameBytes = utf8(normalizedFrame).byteLength;
    const targetRole: Role = sender === "therapist" ? "patient" : "therapist";
    const target = this.findSocket(targetRole);
    const next: SessionRecord = {
      ...record,
      acceptedFrames: record.acceptedFrames + 1,
      replayHashes: [...record.replayHashes, replayHash],
      backlog: [...record.backlog],
    };
    if (target === null) {
      if (backlogBytes(next.backlog) + frameBytes > MAX_BACKLOG_BYTES) {
        this.closeSocket(socket, 4010, "backlog limit");
        return;
      }
      next.backlog.push({ targetRole, frame: normalizedFrame, bytes: frameBytes });
      await this.saveRecord(next);
      return;
    }
    await this.saveRecord(next);
    try {
      target.send(normalizedFrame);
    } catch {
      if (backlogBytes(next.backlog) + frameBytes <= MAX_BACKLOG_BYTES) {
        next.backlog.push({ targetRole, frame: normalizedFrame, bytes: frameBytes });
        await this.saveRecord(next);
      }
      this.closeSocket(target, 4008, "connection unavailable");
    }
  }

  private findSocket(role: Role): HibernatableWebSocket | null {
    for (const socket of this.ctx.getWebSockets()) {
      const attachment = this.attachmentOf(socket);
      if (attachment?.role === role) {
        return socket as HibernatableWebSocket;
      }
    }
    return null;
  }

  private async handleDelete(request: Request): Promise<Response> {
    const record = await this.loadRecord();
    if (record === null) {
      return errorResponse("SESSION_NOT_FOUND", 404);
    }
    if (Date.parse(record.expiresAt) <= Date.now()) {
      await this.expireAndDelete();
      return errorResponse("SESSION_EXPIRED", 410);
    }
    const token = parseBearerToken(request);
    if (token === null) {
      return errorResponse("UNAUTHORIZED", 401);
    }
    const tokenHash = await sha256Base64Url(token);
    if (!constantTimeEqualBase64Url(record.therapistTokenHash, tokenHash, 32)) {
      return errorResponse("UNAUTHORIZED", 401);
    }
    await this.expireAndDelete(4000, "deleted");
    return jsonResponse({ deleted: true });
  }

  private async expireAndDelete(code = 4001, reason = "expired"): Promise<void> {
    this.closeAllSockets(code, reason);
    await this.ctx.storage.deleteAlarm();
    await this.ctx.storage.deleteAll();
  }

  private closeAllSockets(code: number, reason: string): void {
    for (const socket of this.ctx.getWebSockets()) {
      this.closeSocket(socket, code, reason);
    }
  }

  private closeSocket(socket: WebSocket, code: number, reason: string): void {
    try {
      socket.close(code, reason);
    } catch {
      // A closed socket has no state to update and needs no log entry.
    }
  }

  private async scheduleNextAlarm(record: SessionRecord): Promise<void> {
    let next = Date.parse(record.expiresAt);
    for (const socket of this.ctx.getWebSockets()) {
      const attachment = this.attachmentOf(socket);
      if (attachment?.role === null && attachment.authDeadline > Date.now()) {
        next = Math.min(next, attachment.authDeadline);
      }
    }
    await this.ctx.storage.setAlarm(new Date(next));
  }
}
