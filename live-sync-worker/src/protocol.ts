import {
  base64UrlDecode,
  constantTimeEqualBase64Url,
  isBase64UrlOfBytes,
  isIsoDate,
  utf8,
} from "./encoding";

export const PROTOCOL_VERSION = 1 as const;
export const PROTOCOL_NAME = "KGG-LIVE-V1" as const;
export const MAX_FRAME_BYTES = 64 * 1024;
export const MAX_BODY_BYTES = 16 * 1024;
export const MAX_DATA_FRAMES = 400;
export const MAX_BACKLOG_BYTES = 5 * 1024 * 1024;
export const AUTH_TIMEOUT_MS = 5_000;
export const SESSION_TTL_MS = 2 * 60 * 60 * 1000;

export type Role = "therapist" | "patient";

export interface OuterFrame {
  v: 1;
  messageId: string;
  sender: Role;
  sequence: number;
  nonce: string;
  ciphertext: string;
  createdAt: string;
}

export interface AuthFrame {
  type: "auth";
  role: Role;
  token: string;
}

export interface KeyHelloFrame {
  v: 1;
  type: "key_hello";
  sessionId: string;
  role: Role;
  publicKey: string;
  signature: string;
}

export interface ReserveBody {
  therapistTokenHash: string;
}

export interface ArmBody {
  joinProof: string;
}

export interface JoinBody {
  joinProof: string;
  patientTokenHash: string;
}

export interface SessionRecord {
  schemaVersion: 1;
  sessionId: string;
  sessionSalt: string;
  expiresAt: string;
  therapistTokenHash: string;
  joinProof: string | null;
  patientTokenHash: string | null;
  joinFailures: number;
  locked: boolean;
  acceptedFrames: number;
  replayHashes: string[];
  backlog: BacklogEntry[];
}

export interface BacklogEntry {
  targetRole: Role;
  frame: string;
  bytes: number;
}

export interface SocketAttachment {
  schemaVersion: 1;
  role: Role | null;
  authDeadline: number;
}

const AUTH_KEYS = ["role", "token", "type"] as const;
const RESERVE_KEYS = ["therapistTokenHash"] as const;
const ARM_KEYS = ["joinProof"] as const;
const JOIN_KEYS = ["joinProof", "patientTokenHash"] as const;
const KEY_HELLO_KEYS = ["publicKey", "role", "sessionId", "signature", "type", "v"] as const;
const OUTER_FRAME_KEYS = ["ciphertext", "createdAt", "messageId", "nonce", "sender", "sequence", "v"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function parseJson(value: string): unknown {
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return null;
  }
}

export function isRole(value: unknown): value is Role {
  return value === "therapist" || value === "patient";
}

export function isOpaqueToken(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9_-]{16,512}$/.test(value);
}

export function parseAuthFrame(value: string): AuthFrame | null {
  const parsed = parseJson(value);
  if (!isRecord(parsed) || !hasExactKeys(parsed, AUTH_KEYS) || parsed.type !== "auth" || !isRole(parsed.role) || !isOpaqueToken(parsed.token)) {
    return null;
  }
  return { type: "auth", role: parsed.role, token: parsed.token };
}

export function parseKeyHelloFrame(value: string): KeyHelloFrame | null {
  const parsed = parseJson(value);
  if (!isRecord(parsed)
    || !hasExactKeys(parsed, KEY_HELLO_KEYS)
    || parsed.v !== PROTOCOL_VERSION
    || parsed.type !== "key_hello"
    || !isRole(parsed.role)
    || !isBase64UrlOfBytes(parsed.sessionId, 16)
    || !isBase64UrlOfBytes(parsed.publicKey, 65)
    || !isBase64UrlOfBytes(parsed.signature, 32)) {
    return null;
  }
  return {
    v: PROTOCOL_VERSION,
    type: "key_hello",
    sessionId: parsed.sessionId as string,
    role: parsed.role,
    publicKey: parsed.publicKey as string,
    signature: parsed.signature as string,
  };
}

export function parseReserveBody(value: string): ReserveBody | null {
  const parsed = parseJson(value);
  if (!isRecord(parsed) || !hasExactKeys(parsed, RESERVE_KEYS) || !isBase64UrlOfBytes(parsed.therapistTokenHash, 32)) {
    return null;
  }
  return { therapistTokenHash: parsed.therapistTokenHash as string };
}

export function parseArmBody(value: string): ArmBody | null {
  const parsed = parseJson(value);
  if (!isRecord(parsed) || !hasExactKeys(parsed, ARM_KEYS) || !isBase64UrlOfBytes(parsed.joinProof, 32)) {
    return null;
  }
  return { joinProof: parsed.joinProof as string };
}

export function parseJoinBody(value: string): JoinBody | null {
  const parsed = parseJson(value);
  if (!isRecord(parsed) || !hasExactKeys(parsed, JOIN_KEYS) || !isBase64UrlOfBytes(parsed.joinProof, 32) || !isBase64UrlOfBytes(parsed.patientTokenHash, 32)) {
    return null;
  }
  return {
    joinProof: parsed.joinProof as string,
    patientTokenHash: parsed.patientTokenHash as string,
  };
}

export function validateOuterFrame(value: string): OuterFrame | null {
  if (utf8(value).byteLength > MAX_FRAME_BYTES) {
    return null;
  }
  const parsed = parseJson(value);
  if (!isRecord(parsed) || !hasExactKeys(parsed, OUTER_FRAME_KEYS)) {
    return null;
  }
  if (parsed.v !== PROTOCOL_VERSION || !isRole(parsed.sender) || !Number.isSafeInteger(parsed.sequence) || (parsed.sequence as number) < 1) {
    return null;
  }
  if (!isBase64UrlOfBytes(parsed.messageId, 16) || !isBase64UrlOfBytes(parsed.nonce, 12)) {
    return null;
  }
  if (!isBase64UrlOfBytes(parsed.ciphertext, base64UrlDecode(parsed.ciphertext as string)?.byteLength ?? -1) || (parsed.ciphertext as string).length === 0) {
    return null;
  }
  if (!isIsoDate(parsed.createdAt)) {
    return null;
  }
  return {
    v: PROTOCOL_VERSION,
    messageId: parsed.messageId as string,
    sender: parsed.sender,
    sequence: parsed.sequence as number,
    nonce: parsed.nonce as string,
    ciphertext: parsed.ciphertext as string,
    createdAt: parsed.createdAt as string,
  };
}

export function frameReplayKey(frame: OuterFrame): string {
  return `${frame.sender}:${frame.sequence}:${frame.messageId}:${frame.nonce}`;
}

export function backlogBytes(backlog: readonly BacklogEntry[]): number {
  return backlog.reduce((total, entry) => total + entry.bytes, 0);
}

export function isSessionRecord(value: unknown): value is SessionRecord {
  const joinFailures = isRecord(value) && typeof value.joinFailures === "number" ? value.joinFailures : Number.NaN;
  const acceptedFrames = isRecord(value) && typeof value.acceptedFrames === "number" ? value.acceptedFrames : Number.NaN;
  if (!isRecord(value)
    || value.schemaVersion !== 1
    || !isBase64UrlOfBytes(value.sessionId, 16)
    || !isBase64UrlOfBytes(value.sessionSalt, 32)
    || !isIsoDate(value.expiresAt)
    || !isBase64UrlOfBytes(value.therapistTokenHash, 32)
    || (value.joinProof !== null && !isBase64UrlOfBytes(value.joinProof, 32))
    || (value.patientTokenHash !== null && !isBase64UrlOfBytes(value.patientTokenHash, 32))
    || !Number.isInteger(joinFailures)
    || joinFailures < 0
    || joinFailures > 5
    || typeof value.locked !== "boolean"
    || !Number.isInteger(acceptedFrames)
    || acceptedFrames < 0
    || acceptedFrames > MAX_DATA_FRAMES
    || !Array.isArray(value.replayHashes)
    || value.replayHashes.length > MAX_DATA_FRAMES
    || value.replayHashes.some((entry) => !isBase64UrlOfBytes(entry, 32))
    || !Array.isArray(value.backlog)
    || value.backlog.length > MAX_DATA_FRAMES) {
    return false;
  }
  const backlogValid = value.backlog.every((entry) => isRecord(entry)
    && isRole(entry.targetRole)
    && typeof entry.frame === "string"
    && typeof entry.bytes === "number"
    && Number.isInteger(entry.bytes)
    && entry.bytes >= 0
    && entry.bytes <= MAX_FRAME_BYTES
    && entry.bytes === utf8(entry.frame).byteLength
    && validateOuterFrame(entry.frame) !== null);
  return backlogValid && backlogBytes(value.backlog as BacklogEntry[]) <= MAX_BACKLOG_BYTES;
}

export function isSocketAttachment(value: unknown): value is SocketAttachment {
  return isRecord(value)
    && value.schemaVersion === 1
    && (value.role === null || isRole(value.role))
    && Number.isFinite(value.authDeadline)
    && (value.authDeadline as number) > 0;
}
