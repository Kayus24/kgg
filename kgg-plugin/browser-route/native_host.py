from __future__ import annotations

import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
from urllib.parse import urlsplit

SCHEMA = "kgg-chatgpt-browser-route/v1"
MAX_FRAME_BYTES = 4096
MAX_URL_LENGTH = 2048
MAX_CONVERSATION_ID_LENGTH = 128
CONVERSATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
EXPECTED_KEYS = {"schema", "state", "canonical_url", "observed_at"}


class ProtocolError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def default_state_path() -> Path:
    override = os.environ.get("KGG_CHATGPT_ROUTE_STATE")
    if override:
        return Path(override)
    root = os.environ.get("LOCALAPPDATA")
    if root:
        return Path(root) / "KGG" / "project-status" / "chatgpt-route-state.json"
    return Path.home() / ".local" / "state" / "kgg" / "chatgpt-route-state.json"


def canonical_chatgpt_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw or len(raw) > MAX_URL_LENGTH:
        return None
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() != "https":
        return None
    if parsed.username or parsed.password or port is not None:
        return None
    host = (parsed.hostname or "").lower()
    if host not in {"chatgpt.com", "www.chatgpt.com"}:
        return None
    if parsed.netloc.lower() not in {"chatgpt.com", "www.chatgpt.com"}:
        return None
    segments = [segment for segment in parsed.path.split("/") if segment]
    conversation_id = None
    if len(segments) == 2 and segments[0] == "c":
        conversation_id = segments[1]
    elif (
        len(segments) == 4
        and segments[0] == "g"
        and segments[1]
        and segments[2] == "c"
    ):
        conversation_id = segments[3]
    if (
        not conversation_id
        or len(conversation_id) > MAX_CONVERSATION_ID_LENGTH
        or not CONVERSATION_ID_RE.fullmatch(conversation_id)
    ):
        return None
    return f"https://chatgpt.com/c/{conversation_id}"


def validate_observation(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ProtocolError("payload_not_object")
    if set(payload) != EXPECTED_KEYS:
        raise ProtocolError("payload_keys_invalid")
    if payload.get("schema") != SCHEMA:
        raise ProtocolError("schema_invalid")
    state = payload.get("state")
    if state not in {"verified", "unavailable"}:
        raise ProtocolError("state_invalid")
    observed_at = payload.get("observed_at")
    if type(observed_at) is not int or observed_at < 0:
        raise ProtocolError("observed_at_invalid")
    canonical_url = payload.get("canonical_url")
    if state == "verified":
        normalized = canonical_chatgpt_url(canonical_url)
        if normalized is None or normalized != canonical_url:
            raise ProtocolError("canonical_url_invalid")
    elif canonical_url is not None:
        raise ProtocolError("unavailable_url_must_be_null")
    return {
        "schema": SCHEMA,
        "state": state,
        "canonical_url": canonical_url,
        "observed_at": observed_at,
    }


def write_state_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def read_frame(stream) -> bytes | None:
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ProtocolError("frame_header_truncated")
    length = struct.unpack("<I", header)[0]
    if length <= 0 or length > MAX_FRAME_BYTES:
        raise ProtocolError("frame_size_invalid")
    body = stream.read(length)
    if len(body) != length:
        raise ProtocolError("frame_body_truncated")
    return body


def write_frame(stream, payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream.write(struct.pack("<I", len(body)))
    stream.write(body)
    stream.flush()
def handle_raw(frame: bytes, state_path: Path) -> dict[str, object]:
    try:
        payload = json.loads(frame.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProtocolError("json_invalid")
    validated = validate_observation(payload)
    write_state_atomic(state_path, validated)
    return {"ok": True}


def main() -> int:
    if sys.platform == "win32":
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    try:
        frame = read_frame(sys.stdin.buffer)
        if frame is None:
            return 0
        response = handle_raw(frame, default_state_path())
    except ProtocolError as error:
        response = {"ok": False, "error": error.code}
    except Exception:
        response = {"ok": False, "error": "internal_error"}
    write_frame(sys.stdout.buffer, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
