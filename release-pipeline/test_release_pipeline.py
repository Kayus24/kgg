import copy
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
    def test_legacy_manifest_projection_matches_checked_in_file(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        projected = pipeline.project_legacy_manifest(canonical)
        self.assertEqual(projected, pipeline.load_json(pipeline.LEGACY_MANIFEST))
        self.assertEqual(pipeline.render_json_bytes(projected), pipeline.LEGACY_MANIFEST.read_bytes())

    def test_legacy_projection_uses_channels_not_flat_web_aliases(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        canonical.update({
            "latestWebVersion": "r0001",
            "adminHtmlUrl": "http://stale.invalid/admin.html",
            "adminSha256": "stale",
            "colleagueHtmlUrl": "http://stale.invalid/colleague.html",
            "colleagueSha256": "stale",
            "sha256": "stale",
            "androidApkUrl": "http://stale.invalid/app.apk",
            "androidApkSha256": "stale",
            "latestAndroidApkUrl": "http://stale.invalid/app.apk",
            "latestAndroidApkSha256": "stale",
            "latestColleagueAndroidApkUrl": "http://stale.invalid/colleague.apk",
            "latestColleagueAndroidApkSha256": "stale",
            "latestAdminAndroidApkUrl": "http://stale.invalid/admin.apk",
            "latestAdminAndroidApkSha256": "stale",
        })
        projected = pipeline.project_legacy_manifest(canonical)
        self.assertEqual(canonical["channels"]["admin"]["releaseId"], projected["latestAdminReleaseId"])
        self.assertEqual(canonical["channels"]["admin"]["url"], projected["adminUrl"])
        self.assertEqual(canonical["channels"]["colleague"]["releaseId"], projected["latestVersion"])
        self.assertEqual(canonical["channels"]["colleague"]["url"], projected["latestUrl"])
        self.assertEqual(canonical["colleagueAndroidApkUrl"], projected["latestAndroidApkUrl"])
        self.assertEqual(canonical["colleagueAndroidApkSha256"], projected["latestColleagueAndroidApkSha256"])
        self.assertEqual(canonical["adminAndroidApkUrl"], projected["latestAdminAndroidApkUrl"])
        self.assertEqual(canonical["adminAndroidApkSha256"], projected["latestAdminAndroidApkSha256"])

    def test_legacy_projection_rejects_invalid_contract_fields(self):
        baseline = pipeline.load_json(pipeline.MANIFEST)
        cases = (
            (("schema",), 1),
            (("channels", "admin", "releaseId"), "admin-424"),
            (("channels", "admin", "releaseId"), "r424"),
            (("channels", "admin", "releaseId"), "v401"),
            (("channels", "admin", "versionName"), "version-60"),
            (("channels", "colleague", "sha256"), "ABC"),
            (("channels", "colleague", "url"), "http://example.invalid/r0397/colleague.html"),
            (("latestAndroidShellVersion",), "401"),
            (("latestAndroidShellVersion",), "v402"),
            (("colleagueAndroidApkUrl",), "http://example.invalid/app.apk"),
            (("adminAndroidApkUrl",), baseline["colleagueAndroidApkUrl"]),
            (("adminAndroidApkSha256",), "0" * 63),
        )
        for path, value in cases:
            with self.subTest(path=path):
                canonical = copy.deepcopy(baseline)
                target = canonical
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(pipeline.ReleaseError):
                    pipeline.project_legacy_manifest(canonical)

    def test_v389_sentinel_uses_explicit_historical_urls(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        for profile, filename in (
            ("admin", "KGG_APP_ADMIN_v389_flow_stability.html"),
            ("colleague", "KGG_APP_KOLLEGEN_v389_flow_stability.html"),
        ):
            canonical["channels"][profile].update({
                "releaseId": "v389",
                "versionName": filename.removesuffix(".html"),
                "url": f"https://kayus24.github.io/kgg/therapist-app/releases/v389/web/{filename}",
            })
        projected = pipeline.project_legacy_manifest(canonical)
        self.assertEqual("v389", projected["latestAdminReleaseId"])
        self.assertEqual("v389", projected["latestColleagueReleaseId"])
        self.assertIn("/v389/web/KGG_APP_ADMIN_v389_flow_stability.html", projected["adminUrl"])
        self.assertIn("/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html", projected["colleagueUrl"])
        invalid_name = copy.deepcopy(canonical)
        invalid_name["channels"]["admin"]["versionName"] = "1.0.389-release-pipeline-baseline"
        with self.assertRaises(pipeline.ReleaseError):
            pipeline.project_legacy_manifest(invalid_name)
        invalid_url = copy.deepcopy(canonical)
        invalid_url["channels"]["colleague"]["url"] = (
            "https://kayus24.github.io/kgg/therapist-app/releases/v389/colleague.html"
        )
        with self.assertRaises(pipeline.ReleaseError):
            pipeline.project_legacy_manifest(invalid_url)

    def test_v389_rollback_remains_publishable_for_both_channels(self):
        baseline = pipeline.MANIFEST.read_bytes()
        for profile in ("admin", "colleague"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temporary_directory:
                temporary = Path(temporary_directory)
                canonical_path = temporary / "android_update_manifest.json"
                legacy_path = temporary / "kgg_update_manifest.json"
                canonical_path.write_bytes(baseline)
                with mock.patch.object(pipeline, "ROOT", temporary), mock.patch.object(
                    pipeline, "MANIFEST", canonical_path
                ), mock.patch.object(pipeline, "LEGACY_MANIFEST", legacy_path):
                    target = pipeline.rollback(profile, "v389")
                    self.assertEqual("v389", target["releaseId"])
                    expected_name = (
                        "KGG_APP_ADMIN_v389_flow_stability"
                        if profile == "admin"
                        else "KGG_APP_KOLLEGEN_v389_flow_stability"
                    )
                    self.assertEqual(expected_name, target["versionName"])
                    self.assertEqual("current", pipeline.sync_legacy_manifest(check=True)["status"])

    def test_legacy_projection_is_deterministic_without_timestamp(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        original = copy.deepcopy(canonical)
        first = pipeline.render_json_bytes(pipeline.project_legacy_manifest(canonical))
        second = pipeline.render_json_bytes(pipeline.project_legacy_manifest(canonical))
        self.assertEqual(original, canonical)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertNotIn(b"\r\n", first)
        self.assertNotIn(b"releasedAt", first)
        self.assertIn(b'\n  "kind":', first)

    def test_manifest_writer_and_sync_check_keep_pair_byte_exact(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            canonical_path = temporary / "android_update_manifest.json"
            legacy_path = temporary / "kgg_update_manifest.json"
            with mock.patch.object(pipeline, "ROOT", temporary), mock.patch.object(
                pipeline, "MANIFEST", canonical_path
            ), mock.patch.object(pipeline, "LEGACY_MANIFEST", legacy_path):
                pipeline.write_update_manifests(canonical)
                self.assertEqual(pipeline.render_json_bytes(canonical), canonical_path.read_bytes())
                expected_legacy = pipeline.render_json_bytes(pipeline.project_legacy_manifest(canonical))
                self.assertEqual(expected_legacy, legacy_path.read_bytes())
                self.assertEqual("current", pipeline.sync_legacy_manifest(check=True)["status"])
                legacy_path.write_text("{}\n", encoding="utf-8")
                with self.assertRaises(pipeline.ReleaseError):
                    pipeline.sync_legacy_manifest(check=True)
                self.assertEqual("written", pipeline.sync_legacy_manifest()["status"])
                self.assertEqual(expected_legacy, legacy_path.read_bytes())

    def test_manifest_pair_restores_canonical_when_legacy_write_fails(self):
        canonical = pipeline.load_json(pipeline.MANIFEST)
        canonical["notes"] = "Transactional writer test"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            canonical_path = temporary / "android_update_manifest.json"
            legacy_path = temporary / "kgg_update_manifest.json"
            original_canonical = b'{"original":"canonical"}\n'
            original_legacy = b'{"original":"legacy"}\n'
            canonical_path.write_bytes(original_canonical)
            legacy_path.write_bytes(original_legacy)
            real_atomic_write = pipeline.atomic_write_bytes
            write_count = 0

            def fail_second_write(path, value):
                nonlocal write_count
                write_count += 1
                if write_count == 2:
                    real_atomic_write(path, value)
                    raise pipeline.ReleaseError("synthetic legacy write failure")
                real_atomic_write(path, value)

            with mock.patch.object(pipeline, "MANIFEST", canonical_path), mock.patch.object(
                pipeline, "LEGACY_MANIFEST", legacy_path
            ), mock.patch.object(pipeline, "atomic_write_bytes", side_effect=fail_second_write):
                with self.assertRaises(pipeline.ReleaseError):
                    pipeline.write_update_manifests(canonical)

            self.assertEqual(4, write_count)
            self.assertEqual(original_canonical, canonical_path.read_bytes())
            self.assertEqual(original_legacy, legacy_path.read_bytes())

    def test_manifest_writing_workflows_stage_both_projections(self):
        for relative in (
            ".github/workflows/mobile-inbox-release.yml",
            ".github/workflows/promote-latest-admin-beta.yml",
            ".github/workflows/release-control.yml",
            ".github/workflows/release-pr.yml",
        ):
            workflow = pipeline.read_text(pipeline.ROOT / relative)
            self.assertIn("therapist-app/android_update_manifest.json", workflow, relative)
            self.assertIn("therapist-app/kgg_update_manifest.json", workflow, relative)
            self.assertRegex(
                workflow,
                r"git add[^\n]*therapist-app/android_update_manifest\.json[^\n]*therapist-app/kgg_update_manifest\.json",
                relative,
            )

        release_pr = pipeline.read_text(pipeline.ROOT / ".github/workflows/release-pr.yml")
        self.assertIn("(android_update_manifest|kgg_update_manifest)", release_pr)

    def test_mobile_inbox_stages_generated_artifacts_before_redacted_secret_scan(self):
        workflow = pipeline.read_text(
            pipeline.ROOT / ".github/workflows/mobile-inbox-release.yml"
        )
        stage = (
            "git add -A -- release-inbox therapist-app/android_update_manifest.json "
            "therapist-app/kgg_update_manifest.json therapist-app/releases/web"
        )
        scanner = "python release-pipeline/kgg_secret_scan.py"

        self.assertNotIn("git grep -nE", workflow)
        self.assertIn(stage, workflow)
        self.assertIn(scanner, workflow)
        self.assertLess(workflow.index(stage), workflow.index(scanner))
        self.assertLess(workflow.index(scanner), workflow.index('git switch -c "$branch"'))
        self.assertLess(workflow.index(scanner), workflow.index("git commit -m"))

    def test_mobile_inbox_rejects_ambiguous_html_uploads(self):
        workflow = pipeline.read_text(
            pipeline.ROOT / ".github/workflows/mobile-inbox-release.yml"
        )

        self.assertIn("mapfile -t changed_html", workflow)
        self.assertIn('"${#changed_html[@]}" -gt 1', workflow)
        self.assertIn('"${#changed_html[@]}" -eq 1', workflow)
        self.assertNotIn("head -n 1", workflow)
        self.assertIn("Expected exactly one changed HTML file", workflow)

    def test_legacy_direct_main_workflows_are_retired(self):
        for relative in (
            ".github/workflows/apply-update-inbox.yml",
            ".github/workflows/generate-kgg-update.yml",
            ".github/workflows/generate-kgg-v007-qr-photo-update.yml",
        ):
            self.assertFalse((pipeline.ROOT / relative).exists(), relative)

        guide = pipeline.read_text(pipeline.ROOT / "update-inbox/README.md")
        self.assertIn("# update-inbox (stillgelegt)", guide)
        self.assertIn("Niemals `patch.py` oder `release.json`", guide)
        self.assertIn("Branch namens `mobile-inbox`", guide)
        self.assertIn("Genau eine neue oder geänderte Admin-HTML", guide)
        self.assertIn(".github/workflows/mobile-inbox-release.yml", guide)
        self.assertIn("unveränderliche Release-Artefakte", guide)
        self.assertIn("geprüften Pull Request", guide)
        self.assertIn("`kgg-update/src/**`", guide)
        self.assertIn("build_therapist_source.py --check", guide)
        self.assertNotIn("`patch.py` hier hochladen", guide)
        self.assertNotIn("Beides nach `main` committen", guide)
        self.assertNotIn("Action `Apply Update Inbox`", guide)

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

    def test_release_version_must_match_candidate_source_identity(self):
        html = pipeline.read_text(pipeline.BASE_ADMIN)
        version = pipeline.load_json(pipeline.ROOT / "kgg-update" / "version.json")
        self.assertEqual(
            (version["versionCode"], version["versionName"]),
            pipeline.validate_release_version_identity(html, version["versionName"]),
        )
        with self.assertRaisesRegex(pipeline.ReleaseError, "exactly match"):
            pipeline.validate_release_version_identity(html, "1.0.999-wrong-but-valid")
        with self.assertRaisesRegex(pipeline.ReleaseError, "semantic version"):
            pipeline.validate_release_version_identity(html, "version-65")

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
        with self.assertRaisesRegex(mobile_inbox.pipeline.ReleaseError, "VERSION marker"):
            mobile_inbox.html_source_identity(old_html)

    def test_mobile_inbox_uses_candidate_source_version_name(self):
        current = pipeline.load_json(pipeline.ROOT / "kgg-update" / "version.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            release = mobile_inbox.prepare(
                pipeline.BASE_ADMIN,
                temporary / "release.json",
                temporary / "admin.html",
                pipeline.ROOT,
            )
        self.assertEqual(current["versionName"], release["versionName"])
        self.assertNotIn("mobile-inbox-r", release["versionName"])

    def test_mobile_inbox_rejects_source_marker_metadata_mismatch(self):
        html = pipeline.read_text(pipeline.BASE_ADMIN)
        match = mobile_inbox.SOURCE_TRUTH_PATTERN.search(html)
        self.assertIsNotNone(match)
        source_truth = json.loads(match.group(1))
        source_truth["currentVersion"]["versionCode"] += 1
        future_code = source_truth["currentVersion"]["versionCode"]
        source_truth["currentVersion"]["versionName"] = f"1.0.{future_code}-future-fixture"
        replacement = json.dumps(source_truth, ensure_ascii=False, indent=2)
        mismatched = html[: match.start(1)] + replacement + html[match.end(1) :]
        with self.assertRaisesRegex(mobile_inbox.pipeline.ReleaseError, "VERSION marker"):
            mobile_inbox.html_source_identity(mismatched)

    def test_mobile_inbox_source_contract_matches_runtime_parser(self):
        html = pipeline.read_text(pipeline.BASE_ADMIN)
        current = pipeline.load_json(pipeline.ROOT / "kgg-update" / "version.json")["versionCode"]
        marker = re.search(r"KGG_GITHUB_UPDATE_v[0-9]{3,8}_[a-z0-9_]+", html, re.I)
        self.assertIsNotNone(marker)
        without_suffix = html[: marker.start()] + f"KGG_GITHUB_UPDATE_v{current:03d}" + html[marker.end() :]
        with self.assertRaisesRegex(mobile_inbox.pipeline.ReleaseError, "VERSION marker"):
            mobile_inbox.html_source_identity(without_suffix)

        source_match = mobile_inbox.SOURCE_TRUTH_PATTERN.search(html)
        self.assertIsNotNone(source_match)
        source_truth = json.loads(source_match.group(1))
        source_truth["currentVersion"]["versionName"] = f"2.5.{current}-wrong-contract"
        replacement = json.dumps(source_truth, ensure_ascii=False, indent=2)
        wrong_semver = html[: source_match.start(1)] + replacement + html[source_match.end(1) :]
        with self.assertRaisesRegex(mobile_inbox.pipeline.ReleaseError, "1.0"):
            mobile_inbox.html_source_identity(wrong_semver)

    def test_mobile_inbox_next_release_id_advances(self):
        release_id = mobile_inbox.next_release_id(pipeline.ROOT)
        self.assertRegex(release_id, r"^r[0-9]{4,}$")
        self.assertGreater(int(release_id[1:]), 397)


if __name__ == "__main__":
    unittest.main()
