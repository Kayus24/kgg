#!/usr/bin/env python3
"""Negative and rollback tests for the modular KGG build gate."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import build_therapist_source as builder
import kgg_new_patch as scaffolder
import kgg_patch_hygiene as hygiene
import kgg_selftest_build as gate
import kgg_test_battery as battery


ROOT = Path(__file__).resolve().parents[1]


class ReleaseDriftBaselineTests(unittest.TestCase):
    def test_required_release_paths_are_classified(self) -> None:
        runtime_identity = builder.source_role_repo_path(
            builder.DEFAULT_MANIFEST, "runtimeIdentity"
        )
        paths = {
            runtime_identity,
            "kgg-update/index.html",
            "kgg-update/version.json",
            "therapist-app/android_update_manifest.json",
            "therapist-app/kgg_update_manifest.json",
            "therapist-app/releases/web/r9999/admin.html",
            "release-inbox/admin.html",
            "release-pipeline/release_pipeline.py",
        }
        self.assertEqual(paths, hygiene.release_alignment_paths(paths))

    def test_tooling_only_paths_are_not_release_relevant(self) -> None:
        paths = {
            "release-pipeline/kgg_patch_hygiene.py",
            "release-pipeline/kgg_test_battery.py",
            "release-pipeline/test_kgg_selftest_build.py",
        }
        self.assertEqual(set(), hygiene.release_alignment_paths(paths))

    def test_patch_hygiene_accepts_inherited_drift_for_non_release_branch_diff(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    hygiene,
                    "changed_paths_since_main",
                    return_value={"release-pipeline/kgg_patch_hygiene.py"},
                )
            )
            stack.enter_context(mock.patch.object(hygiene, "status_paths", return_value=set()))
            stack.enter_context(mock.patch.object(hygiene, "is_origin_main_ancestor", return_value=True))
            alignment = stack.enter_context(mock.patch.object(hygiene, "assert_source_release_alignment"))
            hygiene.run(ROOT)
        alignment.assert_not_called()

    def test_patch_hygiene_enforces_alignment_for_release_branch_diff(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    hygiene,
                    "changed_paths_since_main",
                    return_value={"kgg-update/version.json"},
                )
            )
            stack.enter_context(mock.patch.object(hygiene, "status_paths", return_value=set()))
            stack.enter_context(mock.patch.object(hygiene, "is_origin_main_ancestor", return_value=True))
            alignment = stack.enter_context(mock.patch.object(hygiene, "assert_source_release_alignment"))
            hygiene.run(ROOT)
        alignment.assert_called_once_with(ROOT)

    def test_patch_hygiene_enforces_alignment_for_dirty_release_path(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    hygiene,
                    "changed_paths_since_main",
                    return_value={"release-pipeline/kgg_patch_hygiene.py"},
                )
            )
            stack.enter_context(
                mock.patch.object(
                    hygiene,
                    "status_paths",
                    return_value={"therapist-app/kgg_update_manifest.json"},
                )
            )
            stack.enter_context(mock.patch.object(hygiene, "is_origin_main_ancestor", return_value=True))
            alignment = stack.enter_context(mock.patch.object(hygiene, "assert_source_release_alignment"))
            hygiene.run(ROOT)
        alignment.assert_called_once_with(ROOT)

    def test_battery_accepts_inherited_drift_for_non_release_diff(self) -> None:
        with mock.patch.object(
            hygiene,
            "touched_paths",
            return_value={"release-pipeline/kgg_test_battery.py"},
        ), mock.patch.object(hygiene, "assert_source_release_alignment") as alignment:
            battery.run_release_drift_check()
        alignment.assert_not_called()

    def test_battery_delegates_relevant_drift_to_fail_closed_guard(self) -> None:
        runtime_identity = builder.source_role_repo_path(
            builder.DEFAULT_MANIFEST, "runtimeIdentity"
        )
        with mock.patch.object(
            hygiene,
            "touched_paths",
            return_value={runtime_identity},
        ), mock.patch.object(
            hygiene,
            "assert_source_release_alignment",
            side_effect=hygiene.HygieneError("expected release drift failure"),
        ):
            with self.assertRaisesRegex(battery.BatteryError, "expected release drift failure"):
                battery.run_release_drift_check()


def patch_block(patch_id: str) -> str:
    return (
        f"<!-- KGG PATCH START {patch_id} -->\n"
        f"<script id=\"{patch_id}\">window.__testPatch=true;</script>\n"
        f"<!-- KGG PATCH END {patch_id} -->\n"
    )


def valid_html(patch_ids: list[str]) -> bytes:
    patches = "".join(patch_block(patch_id) for patch_id in patch_ids)
    return (
        "<!doctype html>\n<html><body>\n"
        "<!-- KGG_ADMIN_ONLY_START --><!-- KGG_ADMIN_ONLY_END -->\n"
        "<script id=\"kgg-source-truth\" type=\"application/json\">{}</script>\n"
        "<script id=\"kgg-changelog\" type=\"application/json\">[]</script>\n"
        "<script>/* KGGDataStore.currentPlan */</script>\n"
        f"{patches}</body></html>\n"
    ).encode("utf-8")


class Fixture:
    def __init__(self) -> None:
        (ROOT / "tmp").mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix="kgg-selftest-unit-", dir=ROOT / "tmp"))
        self.src = self.path / "src"
        self.src.mkdir(parents=True)
        self.output = self.path / "index.html"
        self.version = self.path / "version.json"
        self.manifest = self.src / "parts.json"
        self.impact = self.src / "test-impact.json"

    def close(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)

    def write(self, *, patch_ids: list[str] | None = None, html: bytes | None = None) -> bytes:
        ids = patch_ids or ["test-patch-a", "test-patch-b"]
        raw = html if html is not None else valid_html(ids)
        (self.src / "base.html").write_bytes(raw)
        manifest = {
            "schema": 1,
            "output": "../index.html",
            "versionManifest": "../version.json",
            "sourceRoles": {
                "documentTitle": "base.html",
                "runtimeIdentity": "base.html",
            },
            "requiredPatchIds": ids,
            "parts": ["base.html"],
        }
        self.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        digest = hashlib.sha256(raw).hexdigest()
        self.output.write_bytes(raw)
        self.version.write_text(
            json.dumps({"versionCode": 1, "versionName": "test-v1", "indexUrl": "index.html?v=1", "sha256": digest}, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        self.impact.write_text(
            json.dumps({"schema": 1, "unknownChangesRequireFullRegression": True, "rules": [{"glob": "base.html", "fullRegression": True}]}, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return raw


class BuilderNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_rejects_duplicate_part_paths(self) -> None:
        self.fixture.write()
        manifest = json.loads(self.fixture.manifest.read_text(encoding="utf-8"))
        manifest["parts"] = ["base.html", "base.html"]
        self.fixture.manifest.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(builder.BuildError, "duplicate paths"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_missing_required_source_role(self) -> None:
        self.fixture.write()
        manifest = json.loads(self.fixture.manifest.read_text(encoding="utf-8"))
        del manifest["sourceRoles"]["runtimeIdentity"]
        self.fixture.manifest.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(builder.BuildError, "missing required role.*runtimeIdentity"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_source_role_outside_parts(self) -> None:
        self.fixture.write()
        manifest = json.loads(self.fixture.manifest.read_text(encoding="utf-8"))
        manifest["sourceRoles"]["runtimeIdentity"] = "not-a-part.html"
        self.fixture.manifest.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(builder.BuildError, "must reference exactly one entry"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_wrong_patch_order(self) -> None:
        self.fixture.write(html=valid_html(["test-patch-b", "test-patch-a"]))
        with self.assertRaisesRegex(builder.BuildError, "patch order"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_external_runtime_script(self) -> None:
        raw = valid_html(["test-patch-a", "test-patch-b"]).replace(
            b"</body>", b'<script src="https://example.invalid/x.js"></script>\n</body>'
        )
        self.fixture.write(html=raw)
        with self.assertRaisesRegex(builder.BuildError, "external scripts"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_forbidden_source_control_characters(self) -> None:
        raw = valid_html(["test-patch-a", "test-patch-b"]).replace(
            b"KGGDataStore.currentPlan",
            b"KGGDataStore.currentPlan\x08",
        )
        self.fixture.write(html=raw)
        with self.assertRaisesRegex(builder.BuildError, r"U\+0008.*line"):
            builder.load_build(self.fixture.manifest)

    def test_rejects_unicode_c1_source_control_characters(self) -> None:
        raw = valid_html(["test-patch-a", "test-patch-b"]).replace(
            b"KGGDataStore.currentPlan",
            b"KGGDataStore.currentPlan" + "\u0085".encode("utf-8"),
        )
        self.fixture.write(html=raw)
        with self.assertRaisesRegex(builder.BuildError, r"U\+0085.*line"):
            builder.load_build(self.fixture.manifest)

    def test_allows_source_tabs_and_lf(self) -> None:
        raw = valid_html(["test-patch-a", "test-patch-b"]).replace(
            b"KGGDataStore.currentPlan",
            b"\tKGGDataStore.currentPlan",
        )
        self.fixture.write(html=raw)
        builder.load_build(self.fixture.manifest)

    def test_rejects_generated_output_drift(self) -> None:
        self.fixture.write()
        self.fixture.output.write_bytes(b"direct edit")
        with self.assertRaisesRegex(builder.BuildError, "differs from modular source"):
            builder.check(self.fixture.manifest)


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_impact_policy_only_references_registered_tests(self) -> None:
        policy = json.loads((ROOT / "kgg-update" / "src" / "test-impact.json").read_text(encoding="utf-8"))
        registered = {str(item["id"]) for item in battery.TEST_REGISTRY}
        referenced = {test_id for rule in policy["rules"] for test_id in rule.get("testIds", [])}
        self.assertEqual([], sorted(referenced - registered))

    def test_future_source_directories_require_full_regression(self) -> None:
        policy = json.loads((ROOT / "kgg-update" / "src" / "test-impact.json").read_text(encoding="utf-8"))
        full_globs = {
            rule.get("glob")
            for rule in policy["rules"]
            if rule.get("fullRegression") is True
        }
        self.assertTrue(
            {"document/*.html", "runtime/*.html", "features/*.html", "compat/*.html"}
            <= full_globs
        )

    def test_required_gate_resolves_runtime_identity_role(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "kgg-required-gate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("--print-source-role runtimeIdentity", workflow)
        classification_line = next(
            line for line in workflow.splitlines() if "admin_camera_qr=true" in line
        )
        self.assertIn("$runtime_identity_path", classification_line)
        self.assertNotIn("base-app", classification_line)

    def test_scaffolder_updates_separate_semantic_role_files(self) -> None:
        (ROOT / "tmp").mkdir(parents=True, exist_ok=True)
        fixture_root = Path(tempfile.mkdtemp(prefix="kgg-role-unit-", dir=ROOT / "tmp"))
        try:
            document = fixture_root / "document.html"
            runtime = fixture_root / "runtime.html"
            manifest_path = fixture_root / "parts.json"
            document.write_text("<title>Old</title>\n", encoding="utf-8", newline="\n")
            runtime.write_text(
                "const VERSION='OLD';\nconst KGG_BUILD_INFO={\"old\":true};\n",
                encoding="utf-8",
                newline="\n",
            )
            manifest = {
                "parts": ["document.html", "runtime.html"],
                "sourceRoles": {
                    "documentTitle": "document.html",
                    "runtimeIdentity": "runtime.html",
                },
            }
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8", newline="\n")
            updates = scaffolder.render_source_role_updates(
                manifest,
                code=66,
                title="Role Test",
                slug="role-test",
                build_time="2026-08-11T00:00:00Z",
                manifest_path=manifest_path,
            )
            self.assertIn(b"<title>KGG Update v066 Role Test</title>", updates[document])
            self.assertIn(b"KGG_GITHUB_UPDATE_v066_role_test", updates[runtime])
            self.assertIn(b'"buildCode":"module-v066-role-test"', updates[runtime])
            self.assertNotIn(b"KGG_GITHUB_UPDATE", updates[document])
        finally:
            shutil.rmtree(fixture_root, ignore_errors=True)

    def test_patch_scaffolder_dry_run_is_non_mutating_and_guarded(self) -> None:
        base_args = dict(
            slug="unit-dry-run",
            title="Unit Dry Run",
            summary="Validiert den Scaffolder ohne Schreibzugriff.",
            area=["UI"],
            version_name=None,
            allow_protected=False,
            allow_changelog_overflow=False,
            approval_note="",
            dry_run=True,
        )
        before = (ROOT / "kgg-update" / "index.html").read_bytes()
        current_version = json.loads((ROOT / "kgg-update" / "version.json").read_text(encoding="utf-8"))["versionCode"]
        planned, report = scaffolder.prepare(SimpleNamespace(**base_args))
        self.assertEqual(current_version + 1, report["versionCode"])
        self.assertGreater(report["changelogBytesAfter"], 0)
        self.assertIn(ROOT / "kgg-update" / "index.html", planned)
        planned_version = json.loads(planned[ROOT / "kgg-update" / "version.json"])
        self.assertEqual(
            f"v{report['versionCode']:03d}: {base_args['summary']}",
            planned_version["notes"],
        )
        self.assertFalse((ROOT / "kgg-update" / "src" / report["patchFile"]).exists())
        self.assertEqual(before, (ROOT / "kgg-update" / "index.html").read_bytes())

    def test_patch_scaffolder_blocks_protected_area_without_override(self) -> None:
        args = SimpleNamespace(
            slug="protected-dry-run",
            title="Protected Dry Run",
            summary="Muss ohne Freigabe blockieren.",
            area=["Plan-State"],
            version_name=None,
            allow_protected=False,
            allow_changelog_overflow=False,
            approval_note="Automatischer lokaler Unit-Dry-run.",
            dry_run=True,
        )
        with self.assertRaisesRegex(scaffolder.ScaffoldError, "protected area"):
            scaffolder.prepare(args)

    def test_scaffolder_blocks_entry_and_byte_overflow_without_override(self) -> None:
        entry_overflow = {"entries": [{} for _ in range(31)]}
        with self.assertRaisesRegex(scaffolder.ScaffoldError, "31 entries"):
            scaffolder.assert_changelog_limits(
                entry_overflow,
                {"maxEmbeddedEntries": 30, "maxEmbeddedBytes": 55000},
                False,
            )

        byte_overflow = {"entries": [{"summary": "x" * 1000}]}
        with self.assertRaisesRegex(scaffolder.ScaffoldError, "UTF-8 bytes"):
            scaffolder.assert_changelog_limits(
                byte_overflow,
                {"maxEmbeddedEntries": 30, "maxEmbeddedBytes": 100},
                False,
            )

    def test_failed_transaction_restores_previous_output_and_version(self) -> None:
        self.fixture.write()
        old_output = b"last known green output\n"
        old_version = b'{"versionCode": 1, "versionName": "last-green"}\n'
        self.fixture.output.write_bytes(old_output)
        self.fixture.version.write_bytes(old_version)
        state = self.fixture.path / "state"

        patches = {
            "ROOT": self.fixture.path,
            "SRC": self.fixture.src,
            "IMPACT_PATH": self.fixture.impact,
            "STATE_ROOT": state,
            "RUNS_ROOT": state / "runs",
            "PENDING_PATH": state / "pending.json",
            "LOCK_PATH": state / "build.lock",
            "LATEST_PATH": state / "latest.json",
            "LAST_FAILED_PATH": state / "last-failed.json",
            "BATTERY": self.fixture.path / "fake-battery.py",
        }

        def failing_runner(_command: list[str], _env: dict[str, str]) -> tuple[int, str, float]:
            return 9, "intentional negative test\n", 0.01

        with ExitStack() as stack:
            stack.enter_context(mock.patch.multiple(gate, **patches))
            stack.enter_context(mock.patch.object(builder, "DEFAULT_MANIFEST", self.fixture.manifest))
            with self.assertRaisesRegex(gate.GateError, "Self-test failed"):
                gate.execute_build("smart", runner=failing_runner)

        self.assertEqual(old_output, self.fixture.output.read_bytes())
        self.assertEqual(old_version, self.fixture.version.read_bytes())
        self.assertFalse((state / "pending.json").exists())
        self.assertFalse((state / "build.lock").exists())
        failed = json.loads((state / "last-failed.json").read_text(encoding="utf-8"))
        self.assertTrue(failed.get("restoredLastGreen"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
