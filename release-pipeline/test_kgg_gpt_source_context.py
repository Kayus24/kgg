import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_gpt_source_context as context


class GptSourceContextTests(unittest.TestCase):
    def source(self, payload: bytes, path: str = "kgg-update/src/example.html") -> context.SourceDocument:
        return context.SourceDocument(path, context.normalize_lf_bytes(payload))

    def test_lf_normalization_is_strict_and_deterministic(self):
        lf = context.normalize_lf_bytes(b"first\nsecond\n")
        crlf = context.normalize_lf_bytes(b"first\r\nsecond\r\n")
        self.assertEqual(lf, crlf)
        self.assertEqual(hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest())
        with self.assertRaises(UnicodeDecodeError):
            context.normalize_lf_bytes(b"\xff")

    def test_manifest_order_starts_with_parts_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            (root / "a.html").write_bytes(b"a\r\n")
            (root / "nested" / "b.html").write_bytes(b"b")
            manifest = {"parts": ["nested/b.html", "a.html"]}
            parts = root / "parts.json"
            parts.write_text(json.dumps(manifest), encoding="utf-8")
            documents = context.read_source_documents(root, parts)
        self.assertEqual(
            [item.path for item in documents],
            [
                "kgg-update/src/parts.json",
                "kgg-update/src/nested/b.html",
                "kgg-update/src/a.html",
            ],
        )
        self.assertEqual(b"b\n", documents[1].payload)

    def test_manifest_rejects_escape_duplicate_and_missing_paths(self):
        cases = [
            (["../escape.html"], "escapes"),
            (["a.html", "a.html"], "duplicate"),
            (["missing.html"], "missing"),
        ]
        for parts_list, message in cases:
            with self.subTest(parts=parts_list), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "a.html").write_text("a", encoding="utf-8")
                parts = root / "parts.json"
                parts.write_text(json.dumps({"parts": parts_list}), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, message):
                    context.read_source_documents(root, parts)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "a.html"
            source.write_text("a", encoding="utf-8")
            parts = root / "parts.json"
            parts.write_text(json.dumps({"parts": [str(source.resolve())]}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "must stay relative"):
                context.read_source_documents(root, parts)

    def test_natural_boundary_requires_exact_rolling_window(self):
        window = [f"line-{number}\n".encode() for number in range(context.ROLLING_LINE_WINDOW)]
        self.assertFalse(context.is_natural_boundary(window[:-1], mask=0))
        self.assertTrue(context.is_natural_boundary(window, mask=0))

    def test_minimum_natural_boundary_and_small_final_chunk(self):
        source = self.source(b"".join(f"line-{number:04d}\n".encode() for number in range(83)))
        chunks = context.chunk_source(
            source,
            min_payload_bytes=200,
            max_payload_bytes=10_000,
            boundary_mask=0,
        )
        self.assertGreaterEqual(len(chunks[0].payload), 200)
        self.assertLess(len(chunks[-1].payload), 200)
        self.assertEqual(source.payload, b"".join(item.payload for item in chunks))

    def test_hard_max_and_overlong_line(self):
        source = self.source(b"123456789\n" * 20)
        chunks = context.chunk_source(
            source,
            min_payload_bytes=50,
            max_payload_bytes=64,
            boundary_mask=0xFFFF,
        )
        self.assertTrue(all(len(item.payload) <= 64 for item in chunks))
        overlong = self.source(b"x" * 65)
        with self.assertRaisesRegex(RuntimeError, "source line exceeds 64 bytes"):
            context.chunk_source(overlong, min_payload_bytes=50, max_payload_bytes=64)

    def test_rolling_window_is_reset_for_each_source(self):
        payload = b"".join(f"line-{number:04d}\n".encode() for number in range(300))
        first = context.chunk_source(
            self.source(payload, "kgg-update/src/first.html"),
            min_payload_bytes=200,
            max_payload_bytes=1_000,
            boundary_mask=0x000F,
        )
        second = context.chunk_source(
            self.source(payload, "kgg-update/src/second.html"),
            min_payload_bytes=200,
            max_payload_bytes=1_000,
            boundary_mask=0x000F,
        )
        self.assertEqual([item.payload for item in first], [item.payload for item in second])

    def test_content_addressed_name_and_prefix_collision(self):
        chunk = context.chunk_source(self.source(b"hello\n"))[0]
        self.assertEqual(f"chunk-v2-{chunk.sha256[:16]}.md", chunk.name)
        registry: dict[str, str] = {}
        context.register_hash_prefix(registry, "a" * 64)
        context.register_hash_prefix(registry, "a" * 64)
        with self.assertRaisesRegex(RuntimeError, "hash-prefix collision"):
            context.register_hash_prefix(registry, ("a" * 16) + ("b" * 48))

    def test_unrecognized_chunk_file_is_never_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            chunk_dir = Path(temp)
            unexpected = chunk_dir / "chunk-notes.md"
            unexpected.write_text("preserve me", encoding="utf-8")
            with mock.patch.object(context, "CHUNK_DIR", chunk_dir):
                with self.assertRaisesRegex(RuntimeError, "refusing to replace"):
                    context.current_generated_chunks()
            self.assertEqual("preserve me", unexpected.read_text(encoding="utf-8"))

    def test_existing_v2_prefix_collision_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            chunk_dir = Path(temp)
            path = chunk_dir / "chunk-v2-aaaaaaaaaaaaaaaa.md"
            path.write_bytes(b"existing")
            outputs = {path: b"replacement"}
            digests = {
                b"existing": ("a" * 16) + ("1" * 48),
                b"replacement": ("a" * 16) + ("2" * 48),
            }
            with mock.patch.object(
                context, "payload_sha256", side_effect=lambda payload: digests[payload]
            ):
                with self.assertRaisesRegex(RuntimeError, "hash-prefix collision"):
                    context.reject_existing_v2_mismatches({path}, outputs)
            self.assertEqual(b"existing", path.read_bytes())

    def test_existing_corrupt_v2_chunk_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            chunk_dir = Path(temp)
            path = chunk_dir / "chunk-v2-aaaaaaaaaaaaaaaa.md"
            path.write_bytes(b"corrupt")
            with self.assertRaisesRegex(RuntimeError, "corrupt content-addressed"):
                context.reject_existing_v2_mismatches({path}, {path: b"replacement"})
            self.assertEqual(b"corrupt", path.read_bytes())

    def test_early_change_preserves_content_addressed_suffix(self):
        lines = [hashlib.sha256(f"line-{number}".encode()).hexdigest().encode() + b"\n" for number in range(8_000)]
        original = context.chunk_source(self.source(b"".join(lines)))
        changed = context.chunk_source(self.source(b"inserted-near-start\n" + b"".join(lines)))
        original_hashes = [item.sha256 for item in original]
        changed_hashes = {item.sha256 for item in changed}
        self.assertGreaterEqual(len(set(original_hashes[2:]).intersection(changed_hashes)), 5)

    def test_v2_index_and_routes_have_ordered_source_local_metadata(self):
        source = self.source(b"before\nneedle\nafter\n")
        chunks = context.chunk_source(source)
        routes_before = context.AREA_ROUTES
        context.AREA_ROUTES = [
            {"id": "fixture", "triggers": ["fixture"], "markers": ["needle"], "tests": [], "notes": "fixture"}
        ]
        try:
            route_json, _route_md = context.render_area_routes([source], {source.path: chunks})
        finally:
            context.AREA_ROUTES = routes_before
        route = json.loads(route_json)["routes"][0]
        marker = route["markers"][0]
        self.assertEqual(source.path, marker["sourcePath"])
        self.assertEqual(2, marker["sourceLine"])
        self.assertEqual(chunks[0].sha256, marker["payloadSha256"])
        self.assertNotIn("line", marker)
        self.assertNotIn("linesPerChunk", json.loads(route_json))

    def test_current_repository_contract_without_writing(self):
        outputs = context.render_outputs()
        index = json.loads(outputs[context.INDEX_PATH])
        routes = json.loads(outputs[context.ROUTES_JSON_PATH])
        self.assertEqual(2, index["version"])
        self.assertEqual(2, routes["version"])
        self.assertEqual("kgg-update/src/parts.json", index["sources"][0]["path"])
        serialized = json.dumps(index)
        self.assertNotIn("startLine", serialized)
        self.assertNotIn("endLine", serialized)
        self.assertNotIn("linesPerChunk", serialized)
        self.assertFalse(any("kgg-patient-gpt-source" in path.as_posix() for path in outputs))

        for source in index["sources"]:
            rebuilt = b""
            for chunk in source["chunks"]:
                payload = outputs[context.ROOT / chunk["path"]]
                self.assertEqual(chunk["payloadSha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(chunk["payloadBytes"], len(payload))
                self.assertEqual(chunk["payloadLines"], len(payload.splitlines(keepends=True)))
                rebuilt += payload
            self.assertEqual(source["sha256"], hashlib.sha256(rebuilt).hexdigest())
            self.assertEqual(source["bytes"], len(rebuilt))
            self.assertEqual(source["lines"], len(rebuilt.splitlines(keepends=True)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
