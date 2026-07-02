import importlib.util
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("kgg_release_pipeline", HERE / "release_pipeline.py")
pipeline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(pipeline)
MOBILE_SPEC = importlib.util.spec_from_file_location("kgg_mobile_inbox", HERE / "mobile_inbox.py")
mobile_inbox = importlib.util.module_from_spec(MOBILE_SPEC)
assert MOBILE_SPEC.loader
MOBILE_SPEC.loader.exec_module(mobile_inbox)


class ReleasePipelineTests(unittest.TestCase):
    def test_v24_profile_transform_is_hardened(self):
        admin = pipeline.read_text(pipeline.BASE_ADMIN)
        colleague = pipeline.derive_colleague(admin)
        self.assertIn("colleagueMode", colleague)
        for token in pipeline.COLLEAGUE_FORBIDDEN:
            self.assertNotIn(token, colleague)

    def test_current_files_pass_html_contract(self):
        pipeline.validate_html(pipeline.read_text(pipeline.BASE_ADMIN), "admin")
        pipeline.validate_html(pipeline.derive_colleague(pipeline.read_text(pipeline.BASE_ADMIN)), "colleague")

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

    def test_source_truth_manifest_matches_html(self):
        version = pipeline.load_json(pipeline.ROOT / "kgg-update" / "version.json")
        html_bytes = pipeline.BASE_ADMIN.read_bytes()
        raw_digest = hashlib.sha256(html_bytes).hexdigest()
        normalized_digest = hashlib.sha256(html_bytes.replace(b"\r\n", b"\n")).hexdigest()
        self.assertIn(version["sha256"], {raw_digest, normalized_digest})

    def test_release_center_is_explicit_admin_only_block(self):
        admin = pipeline.read_text(pipeline.BASE_ADMIN)
        self.assertEqual(1, admin.count(pipeline.ADMIN_START))
        self.assertEqual(1, admin.count(pipeline.ADMIN_END))
        self.assertIn('id="kgg-release-center-v31-script"', admin)
        self.assertNotIn("kgg-release-center-v31-script", pipeline.derive_colleague(admin))

    def test_colleague_has_no_legacy_release_center_entrypoints(self):
        colleague = pipeline.derive_colleague(pipeline.read_text(pipeline.BASE_ADMIN))
        for token in ("kgg-v12-release-center-entry-restore", "kgg-v13-update-zentrale-marker", "kggReleaseCenterOpen", "kggPhoneUpdateCenterMenu", "window.KGGReleaseCenter"):
            self.assertNotIn(token, colleague)

    def test_remote_web_update_is_manual_only(self):
        admin = pipeline.read_text(pipeline.BASE_ADMIN)
        self.assertIn("kgg-no-auto-release-navigation-v32", admin)
        self.assertIn("stageManualRemoteWebUpdate(webTarget)", admin)
        self.assertNotIn("location.replace(target.url)", admin)

    def test_colleague_has_no_unconditional_admin_dom_bindings(self):
        colleague = pipeline.derive_colleague(pipeline.read_text(pipeline.BASE_ADMIN))
        forbidden_binding = re.compile(
            r"\$\('(adminConfigBtn|adminSecretsModal|closeAdminSecrets|saveAdminSecrets|clearAdminSecrets)'\)\.(onclick|addEventListener)"
        )
        self.assertIsNone(forbidden_binding.search(colleague))

    def test_mobile_inbox_rejects_older_base_marker(self):
        current = pipeline.load_json(pipeline.ROOT / "kgg-update" / "version.json")["versionCode"]
        old_html = pipeline.read_text(pipeline.BASE_ADMIN).replace(
            f"KGG_GITHUB_UPDATE_v{current:03d}",
            f"KGG_GITHUB_UPDATE_v{current - 1:03d}",
            1,
        )
        self.assertLess(mobile_inbox.html_version_code(old_html), current)

    def test_mobile_inbox_next_release_id_advances(self):
        release_id = mobile_inbox.next_release_id(pipeline.ROOT)
        self.assertRegex(release_id, r"^r[0-9]{4,}$")
        self.assertGreater(int(release_id[1:]), 397)


if __name__ == "__main__":
    unittest.main()
