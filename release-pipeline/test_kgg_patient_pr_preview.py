"""Contracts for the separate verified patient PR preview."""
import copy
import base64
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

import kgg_patient_pr_preview as preview


class PatientPrPreviewTests(unittest.TestCase):
    def setUp(self):
        self.sha = "1" * 40
        self.base = "2" * 40
        repo = {"full_name": preview.REPO}
        self.pr = {
            "id": 123, "number": 375, "state": "open",
            "head": {"sha": self.sha, "repo": repo, "ref": "fix/patient"},
            "base": {"sha": self.base, "repo": repo, "ref": "main"},
            "labels": [{"name": "kgg-no-release"}],
        }
        self.run = {
            "id": 456, "head_sha": self.sha, "head_repository": repo,
            "event": "pull_request", "path": preview.REQUIRED_PATH,
            "workflow_id": preview.REQUIRED_ID, "status": "completed",
            "conclusion": "success", "run_attempt": 1,
            "pull_requests": [{"id": 123, "number": 375, "base": {"sha": self.base}}],
        }
        self.jobs = [{"name": "required-gate", "status": "completed", "conclusion": "success"}]

    def verify(self, pr=None, run=None, jobs=None):
        return preview.verify_binding(
            self.pr if pr is None else pr, self.run if run is None else run,
            self.jobs if jobs is None else jobs, 375, self.sha, 456, self.base,
        )

    def test_valid_binding(self):
        self.assertEqual(self.verify(), 1)

    def icon_patch(self):
        return [
            {"filename": name, "status": "modified"} for name in
            ("index.html", "manifest.json", "manifest-v64.webmanifest", "service-worker.js")
        ] + [
            {"filename": f"kgg-icon-{size}-v64.png", "status": "added"}
            for size in ("192", "512", "maskable-512")
        ] + [
            {"filename": name, "status": "modified"} for name in (
                "release-pipeline/kgg_dual_device_package.js",
                "release-pipeline/kgg_pwa_contract_smoke.py",
                ".github/workflows/kgg-patient-ui-parity.yml",
            )
        ]

    def candidates(self, files):
        with patch.object(preview, "api", return_value={
            "status": "ahead", "merge_base_commit": {"sha": self.base}, "files": files,
        }):
            return preview.candidate_files(self.base, self.sha)

    def test_icon_patch_excludes_support_without_publishing_or_executing_it(self):
        result = self.candidates(self.icon_patch())
        self.assertEqual(len(result), 7)
        self.assertTrue(all("/" not in entry["filename"] for entry in result))

    def test_icon_scope_remains_bounded(self):
        files = self.icon_patch()
        for extra in (
            {"filename": "patient-new.js", "status": "added"},
            {"filename": "kgg-icon-192-v65.png", "status": "added"},
            {"filename": "patient-core.js", "status": "modified"},
            {"filename": "release-pipeline/arbitrary.py", "status": "modified"},
            {"filename": "index.html", "status": "renamed"},
        ):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.candidates(files + [extra])

    def k2_patch(self):
        return [
            {"filename": "index.html", "status": "modified"},
            {"filename": "patient-numpad-visibility-fix.js", "status": "modified"},
            {"filename": preview.K2_MODULE, "status": "added"},
        ] + [{"filename": name, "status": "modified"} for name in sorted(preview.K2_SUPPORT)] + [
            {"filename": f"docs/kgg-patient-gpt-source/chunk-{i:03d}.md", "status": "modified"}
            for i in range(1, 15)
        ]

    def test_k2_scope_excludes_inert_support_and_keeps_exact_runtime(self):
        files = self.k2_patch()
        self.assertGreater(len(files), 20)
        self.assertEqual({e["filename"] for e in self.candidates(files)}, preview.K2_RUNTIME)
        for extra in (
            {"filename": "patient-new.js", "status": "added"},
            {"filename": "patient-core.js", "status": "modified"},
            {"filename": "release-pipeline/arbitrary.py", "status": "modified"},
            {"filename": "../patient.js", "status": "added"},
            {"filename": "index.html", "status": "modified"},
        ):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.candidates(files + [extra])
        with self.assertRaises(ValueError):
            self.candidates(files + [{"filename": f"docs/kgg-patient-gpt-source/chunk-{i:03d}.md",
                                      "status": "modified"} for i in range(50, 90)])
        with self.assertRaises(ValueError):
            self.candidates([e for e in files if e["filename"] != "index.html"])

    def test_new_k2_module_keeps_blob_and_sensitive_sink_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = {name: b"const fixture = 1;" for name in preview.K2_RUNTIME}
            for name in preview.K2_RUNTIME - {preview.K2_MODULE}:
                (root / name).write_bytes(data[name])
            def run(module, mode="100644", corrupt=False):
                data[preview.K2_MODULE] = module
                blobs = {name: hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()
                         for name, value in data.items()}
                entries = [{"filename": name, "status": "added" if name == preview.K2_MODULE else "modified",
                            "sha": blobs[name]} for name in sorted(data)]
                def api(endpoint):
                    if endpoint.startswith("compare/"):
                        return {"status": "ahead", "merge_base_commit": {"sha": self.base}, "files": entries}
                    if endpoint.startswith("git/commits/"):
                        return {"tree": {"sha": "3" * 40}}
                    if endpoint.startswith("git/trees/"):
                        return {"truncated": False, "tree": [
                            {"path": name, "mode": mode if name == preview.K2_MODULE else "100644",
                             "type": "blob", "sha": blobs[name], "size": len(data[name])}
                            for name in data]}
                    name = next(name for name, digest in blobs.items() if endpoint.endswith(digest))
                    value = data[name] + (b"x" if corrupt and name == preview.K2_MODULE else b"")
                    return {"encoding": "base64", "content": base64.b64encode(value).decode()}
                with patch.object(preview, "api", side_effect=api):
                    preview.overlay(root, self.base, self.sha)
            for module, mode, corrupt in (
                (b"fetch('/private')", "100644", False),
                (b"localStorage.clear()", "100644", False),
                (b"const x=1;", "120000", False),
                (b"const x=1;", "100644", True),
                (b" " * (preview.K2_MAX_MODULE_BYTES + 1), "100644", False),
            ):
                with self.subTest(module=module[:50], mode=mode, corrupt=corrupt), self.assertRaises(ValueError):
                    run(module, mode, corrupt)
                self.assertFalse((root / preview.K2_MODULE).exists())
            run(b"const x=1;")
            self.assertEqual((root / preview.K2_MODULE).read_bytes(), b"const x=1;")
            expected = list(preview.DIRECT_FIRST_LOAD_MODULES)
            expected.insert(expected.index("patient-version-label.js"), preview.K2_MODULE)
            self.assertEqual(preview.preview_modules(root), tuple(expected))

    @staticmethod
    def png(size):
        def chunk(kind, data):
            return (struct.pack(">I", len(data)) + kind + data
                    + struct.pack(">I", zlib.crc32(kind + data)))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress((b"\x00" + b"\x80" * size * 3) * size))
                + chunk(b"IEND", b""))

    def overlay_icon(self, root, name="kgg-icon-192-v64.png", data=None, mode="100644", corrupt=False):
        data = self.png(192) if data is None else data
        digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        entry = {"filename": name, "status": "added", "sha": digest}
        def api(endpoint):
            if endpoint.startswith("compare/"):
                return {"status": "ahead", "merge_base_commit": {"sha": self.base}, "files": [entry]}
            if endpoint.startswith("git/commits/"):
                return {"tree": {"sha": "3" * 40}}
            if endpoint.startswith("git/trees/"):
                return {"truncated": False, "tree": [{"path": name, "mode": mode, "type": "blob",
                                                       "sha": digest, "size": len(data)}]}
            return {"encoding": "base64", "content": base64.b64encode(data + (b"x" if corrupt else b"")).decode()}
        with patch.object(preview, "api", side_effect=api):
            preview.overlay(root, self.base, self.sha)

    def test_overlay_adds_only_versioned_regular_icons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.overlay_icon(root)
            self.assertEqual((root / "kgg-icon-192-v64.png").read_bytes(), self.png(192))

    def test_overlay_rejects_unsafe_or_invalid_additions(self):
        for kwargs in (
            {"name": "kgg-icon-other.png"}, {"name": "../kgg-icon-192-v64.png"},
            {"name": "patient-new.js"}, {"mode": "120000"}, {"mode": "100755"},
            {"corrupt": True}, {"data": b"not a PNG"}, {"data": self.png(512)},
        ):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaises(ValueError):
                    self.overlay_icon(root, **kwargs)
                self.assertEqual(list(root.iterdir()), [])

    def test_pr_drift_and_missing_scope(self):
        for side, field, value in (
            ("head", "sha", "3" * 40), ("head", "repo", {"full_name": "fork/kgg"}),
            ("base", "sha", "3" * 40), ("base", "ref", "other"),
        ):
            with self.subTest(side=side, field=field):
                pr = copy.deepcopy(self.pr)
                pr[side][field] = value
                with self.assertRaises(ValueError):
                    self.verify(pr=pr)
        with self.assertRaises(ValueError):
            self.verify(pr={**self.pr, "labels": []})

    def test_ci_failed_unknown_or_wrong_run(self):
        for field, value in (
            ("id", 457), ("conclusion", "failure"), ("conclusion", None),
            ("pull_requests", []), ("workflow_id", 0), ("head_sha", self.base),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.verify(run={**self.run, field: value})
        with self.assertRaises(ValueError):
            self.verify(jobs=[])

    def test_replay_and_transport_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (candidate / "index.html").write_bytes(b"synthetic")
            expected = preview.file_hashes(candidate)
            (candidate / "index.html").write_bytes(b"drift")
            with self.assertRaises(ValueError):
                preview.verify_files(candidate, expected)
            (root / "previews" / "pr-375").mkdir(parents=True)
            with self.assertRaises(ValueError):
                preview.require_new(root, "pr-375")

    def test_workflow_uses_registered_main_and_separates_write_credentials(self):
        workflow = preview.ROOT / ".github/workflows/kgg-patient-pr-preview.yml"
        stage, publish = workflow.read_text().split("\n  publish:\n")
        self.assertIn("refs/heads/main", stage)
        self.assertIn("persist-credentials: false", stage)
        self.assertNotIn("secrets.", stage)
        self.assertNotIn("inputs.expected_head_sha }}\n          path:", stage)
        self.assertNotIn("npm ", publish)
        self.assertNotIn("node release-pipeline", publish)
        self.assertIn("KGG_PATIENT_PREVIEW_PUBLISH_TOKEN", publish)


if __name__ == "__main__":
    unittest.main()
