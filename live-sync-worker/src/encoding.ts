const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder("utf-8", { fatal: true });

export function utf8(value: string): Uint8Array {
  return textEncoder.encode(value);
}

export function utf8Decode(value: ArrayBuffer | ArrayBufferView): string | null {
  try {
    const bytes = value instanceof ArrayBuffer
      ? new Uint8Array(value)
      : new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
    return textDecoder.decode(bytes);
  } catch {
    return null;
  }
}

export function base64UrlEncode(value: ArrayBuffer | ArrayBufferView): string {
  const bytes = value instanceof ArrayBuffer
    ? new Uint8Array(value)
    : new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

export function base64UrlDecode(value: unknown): Uint8Array | null {
  if (typeof value !== "string" || value.length > 100_000 || !/^[A-Za-z0-9_-]*$/.test(value)) {
    return null;
  }
  if (value.length % 4 === 1) {
    return null;
  }
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (value.length % 4)) % 4);
  try {
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes;
  } catch {
    return null;
  }
}

export function isBase64UrlOfBytes(value: unknown, expectedBytes: number): value is string {
  const decoded = base64UrlDecode(value);
  return decoded !== null && decoded.byteLength === expectedBytes && base64UrlEncode(decoded) === value;
}

export function constantTimeEqualBytes(left: Uint8Array, right: Uint8Array): boolean {
  const length = Math.max(left.byteLength, right.byteLength);
  let difference = left.byteLength ^ right.byteLength;
  for (let index = 0; index < length; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
}

export function constantTimeEqualBase64Url(left: unknown, right: unknown, expectedBytes?: number): boolean {
  const leftDecoded = base64UrlDecode(left);
  const rightDecoded = base64UrlDecode(right);
  const leftBytes = leftDecoded ?? new Uint8Array(0);
  const rightBytes = rightDecoded ?? new Uint8Array(0);
  const equal = constantTimeEqualBytes(leftBytes, rightBytes);
  const expectedLengthOk = expectedBytes === undefined
    || (leftBytes.byteLength === expectedBytes && rightBytes.byteLength === expectedBytes);
  const canonical = typeof left === "string"
    && typeof right === "string"
    && base64UrlEncode(leftBytes) === left
    && base64UrlEncode(rightBytes) === right;
  return equal && expectedLengthOk && canonical;
}

export function randomBytes(length: number): Uint8Array {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return bytes;
}

export function randomBase64Url(bytes: number): string {
  return base64UrlEncode(randomBytes(bytes));
}

export function randomDecimalCode(): string {
  const range = 100_000_000;
  const maxUint32 = 0x1_0000_0000;
  const limit = maxUint32 - (maxUint32 % range);
  const candidate = new Uint32Array(1);
  do {
    crypto.getRandomValues(candidate);
  } while (candidate[0] >= limit);
  return String(candidate[0] % range).padStart(8, "0");
}

export async function sha256Base64Url(value: string): Promise<string> {
  const input = utf8(value);
  const copy = new ArrayBuffer(input.byteLength);
  new Uint8Array(copy).set(input);
  const digest = await crypto.subtle.digest("SHA-256", copy);
  return base64UrlEncode(digest);
}

export function isIsoDate(value: unknown): value is string {
  if (typeof value !== "string" || value.length < 20 || value.length > 64) {
    return false;
  }
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && value === new Date(parsed).toISOString();
}

export function nowIso(now = Date.now()): string {
  return new Date(now).toISOString();
}
