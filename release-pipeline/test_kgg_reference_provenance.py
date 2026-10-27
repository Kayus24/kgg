"""Approved cross-session screenshots preserve the trusted CSS viewport and DPR."""
import base64
from copy import deepcopy
import hashlib
import struct
import unittest
import zlib

from test_kgg_real_browser_bridge import server


class ReferenceViewportProvenanceTests(unittest.TestCase):
    def setUp(self):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        raw = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 480, 480, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress((b"\0" + b"\0\0\0" * 480) * 480)) + chunk(b"IEND", b"")
        encoded = base64.b64encode(raw).decode()
        digest = hashlib.sha256(raw).hexdigest()
        self.current = {"viewport": {"width": 480, "height": 480, "device_scale_factor": 1}}
        self.source = {
            "session_id": "source-review-session",
            "viewport": {"width": 240, "height": 240, "device_scale_factor": 2},
            "visual_observations": {"a" * 64: {"artifact": {"id": "source-review-artifact", "sha256": digest}, "image": {"data_base64": encoded}, "viewport": {"width": 240, "height": 240, "device_scale_factor": 2}}},
        }
        self.reference = {
            "reference_class": "approved_golden", "reference_id": "source-review-artifact",
            "reference_sha256": digest, "source_session_id": "source-review-session",
            "observation_id": "a" * 64, "approval_id": "approved:viewport-review",
            "viewport": deepcopy(self.current["viewport"]),
            "threshold": {"max_changed_pixels": 0, "max_changed_ratio": 0, "pixel_delta": 0},
        }
        self.image = {"data_base64": encoded}

    def test_same_pixel_dimensions_cannot_relabel_source_css_viewport_and_dpr(self):
        with self.assertRaisesRegex(server.ServerError, "reference_viewport_mismatch"):
            server._visual_reference(self.reference, self.current, self.source)

    def test_actual_matching_source_viewport_still_allows_identical_reference(self):
        self.source["viewport"] = deepcopy(self.current["viewport"])
        self.source["visual_observations"]["a" * 64]["viewport"] = deepcopy(self.current["viewport"])
        reference = server._visual_reference(self.reference, self.current, self.source)
        self.assertEqual(server._compare_visual_images(self.image, reference)["status"], "PASS")

    def test_later_source_session_change_cannot_relabel_captured_viewport(self):
        self.source["viewport"] = deepcopy(self.current["viewport"])
        with self.assertRaisesRegex(server.ServerError, "reference_viewport_mismatch"):
            server._visual_reference(self.reference, self.current, self.source)

    def test_observation_snapshots_capture_viewport_by_value(self):
        runtime = server.Runtime()
        observed = {"state": "admin-ready", "artifacts": [{"id": self.reference["reference_id"], "sha256": self.reference["reference_sha256"]}], "images": [self.image]}
        record = runtime._record_visual_observation(self.source, observed)
        self.source["viewport"]["device_scale_factor"] = 1
        self.assertEqual(self.source["visual_observations"][record["observation"]["id"]]["viewport"], {"width": 240, "height": 240, "device_scale_factor": 2})


if __name__ == "__main__":
    unittest.main()
