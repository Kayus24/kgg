from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import os
import struct
import subprocess
import sys
import tempfile
import unittest

from native_host import (
    MAX_FRAME_BYTES,
    ProtocolError,
    canonical_chatgpt_url,
    handle_raw,
    read_frame,
    validate_observation,
    write_frame,
)


class NativeHostTest(unittest.TestCase):
    def test_canonical_url_parity(self):
        self.assertEqual(
            canonical_chatgpt_url("https://chatgpt.com/c/abc?x=1#y"),
            "https://chatgpt.com/c/abc",
        )
        self.assertEqual(
            canonical_chatgpt_url("https://www.chatgpt.com/g/g-x/c/abc_123"),
            "https://chatgpt.com/c/abc_123",
        )
        self.assertIsNone(canonical_chatgpt_url("https://chatgpt.com/share/abc"))
        self.assertIsNone(canonical_chatgpt_url("http://chatgpt.com/c/abc"))
        self.assertIsNone(canonical_chatgpt_url("https://user@chatgpt.com/c/abc"))
    def test_valid_verified_persists_exact_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "route.json"
            payload = {
                "schema": "kgg-chatgpt-browser-route/v1",
                "state": "verified",
                "canonical_url": "https://chatgpt.com/c/abc",
                "observed_at": 123,
            }
            response = handle_raw(json.dumps(payload).encode(), path)
            self.assertEqual(response, {"ok": True})
            self.assertEqual(json.loads(path.read_text("utf-8")), payload)
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_unavailable_overwrites_previous_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "route.json"
            first = {
                "schema": "kgg-chatgpt-browser-route/v1",
                "state": "verified",
                "canonical_url": "https://chatgpt.com/c/a",
                "observed_at": 1,
            }
            second = {
                "schema": "kgg-chatgpt-browser-route/v1",
                "state": "unavailable",
                "canonical_url": None,
                "observed_at": 2,
            }
            handle_raw(json.dumps(first).encode(), path)
            handle_raw(json.dumps(second).encode(), path)
            self.assertEqual(json.loads(path.read_text("utf-8")), second)
    def test_unknown_key_fails_closed(self):
        payload = {
            "schema": "kgg-chatgpt-browser-route/v1",
            "state": "verified",
            "canonical_url": "https://chatgpt.com/c/a",
            "observed_at": 1,
            "extra": "no",
        }
        with self.assertRaisesRegex(ProtocolError, "payload_keys_invalid"):
            validate_observation(payload)

    def test_verified_requires_already_canonical_url(self):
        payload = {
            "schema": "kgg-chatgpt-browser-route/v1",
            "state": "verified",
            "canonical_url": "https://www.chatgpt.com/c/a?x=1",
            "observed_at": 1,
        }
        with self.assertRaisesRegex(ProtocolError, "canonical_url_invalid"):
            validate_observation(payload)

    def test_unavailable_rejects_url(self):
        payload = {
            "schema": "kgg-chatgpt-browser-route/v1",
            "state": "unavailable",
            "canonical_url": "https://chatgpt.com/c/a",
            "observed_at": 1,
        }
        with self.assertRaisesRegex(ProtocolError, "unavailable_url_must_be_null"):
            validate_observation(payload)
    def test_frame_round_trip(self):
        stream = BytesIO()
        write_frame(stream, {"ok": True})
        stream.seek(0)
        body = read_frame(stream)
        self.assertEqual(json.loads(body.decode("utf-8")), {"ok": True})

    def test_oversized_frame_rejected_before_body_read(self):
        stream = BytesIO(struct.pack("<I", MAX_FRAME_BYTES + 1))
        with self.assertRaisesRegex(ProtocolError, "frame_size_invalid"):
            read_frame(stream)

    def test_invalid_json_is_typed_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ProtocolError, "json_invalid"):
                handle_raw(b"{not-json", Path(tmp) / "route.json")

    def test_native_host_entrypoint_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "route.json"
            payload = {
                "schema": "kgg-chatgpt-browser-route/v1",
                "state": "verified",
                "canonical_url": "https://chatgpt.com/c/subprocess",
                "observed_at": 456,
            }
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            frame = struct.pack("<I", len(body)) + body
            env = os.environ.copy()
            env["KGG_CHATGPT_ROUTE_STATE"] = str(state_path)
            result = subprocess.run(
                [sys.executable, "-I", str(Path(__file__).with_name("native_host.py"))],
                input=frame,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, b"")
            self.assertGreaterEqual(len(result.stdout), 4)
            response_length = struct.unpack("<I", result.stdout[:4])[0]
            response = json.loads(result.stdout[4:4 + response_length].decode("utf-8"))
            self.assertEqual(response, {"ok": True})
            self.assertEqual(json.loads(state_path.read_text("utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
