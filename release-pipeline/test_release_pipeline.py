import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("kgg_release_pipeline", HERE / "release_pipeline.py")
pipeline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(pipeline)


class ReleasePipelineTests(unittest.TestCase):
    def test_v389_profile_transform_is_hardened(self):
        admin = pipeline.read_text(pipeline.BASE_ADMIN)
        colleague = pipeline.apply_baseline_profile_transform(admin)
        self.assertIn("colleagueMode", colleague)
        for token in pipeline.COLLEAGUE_FORBIDDEN:
            self.assertNotIn(token, colleague)

    def test_current_files_pass_html_contract(self):
        pipeline.validate_html(pipeline.read_text(pipeline.BASE_ADMIN), "admin")
        pipeline.validate_html(pipeline.read_text(pipeline.BASE_COLLEAGUE), "colleague")

    def test_manifest_has_separate_channels(self):
        manifest = pipeline.ensure_schema_v2(pipeline.load_json(pipeline.MANIFEST))
        self.assertEqual(2, manifest["schema"])
        self.assertNotEqual(manifest["channels"]["admin"]["sha256"], manifest["channels"]["colleague"]["sha256"])

    def test_legacy_release_is_rollback_target(self):
        release = pipeline.load_release("v389")
        self.assertEqual("v389", release["releaseId"])
        self.assertIn("admin", release["profiles"])
        self.assertIn("colleague", release["profiles"])

    def test_document_write_loader_is_rejected(self):
        html = pipeline.read_text(pipeline.BASE_ADMIN).replace("</body>", "<script>document.write('x')</script></body>")
        with self.assertRaises(pipeline.ReleaseError):
            pipeline.validate_html(html, "bad")


if __name__ == "__main__":
    unittest.main()
