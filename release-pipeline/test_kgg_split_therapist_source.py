#!/usr/bin/env python3
"""Fail-closed and transactional tests for the therapist source splitter."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build_therapist_source as builder
import kgg_split_therapist_source as splitter


ROOT = Path(__file__).resolve().parents[1]
SECOND = "<!-- SPLIT SECOND -->\n"
THIRD = "<!-- SPLIT THIRD -->\n"


def fixture_html(*, duplicate_second: bool = False) -> bytes:
    repeated = SECOND if duplicate_second else ""
    return (
        "<!doctype html>\n<html><head><title>KGG Test</title></head><body>\n"
        "<!-- KGG_ADMIN_ONLY_START --><!-- KGG_ADMIN_ONLY_END -->\n"
        '<script id="kgg-source-truth" type="application/json">{}</script>\n'
        '<script id="kgg-changelog" type="application/json">{}</script>\n'
        f"{SECOND}{repeated}"
        "<script>const VERSION='KGG_TEST';const KGG_BUILD_INFO={};"
        "/* KGGDataStore.currentPlan */</script>\n"
        f"{THIRD}"
        "<!-- KGG PATCH START test-patch -->\n"
        "<script>window.__splitTest=true;</script>\n"
        "<!-- KGG PATCH END test-patch -->\n"
        "</body></html>\n"
    ).encode("utf-8")


class SplitFixture:
    def __init__(self, *, duplicate_second: bool = False) -> None:
        tmp_root = ROOT / "tmp"
        tmp_root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="kgg-split-unit-", dir=tmp_root))
        self.src = self.root / "src"
        self.src.mkdir()
        self.manifest = self.src / "parts.json"
        self.source = self.src / "base.html"
        self.output = self.root / "index.html"
        self.version = self.root / "version.json"
        self.plan = self.root / "split-plan.json"
        raw = fixture_html(duplicate_second=duplicate_second)
        self.source.write_bytes(raw)
        self.output.write_bytes(raw)
        manifest = {
            "schema": 1,
            "output": "../index.html",
            "versionManifest": "../version.json",
            "sourceRoles": {
                "documentTitle": "base.html",
                "runtimeIdentity": "base.html",
            },
            "requiredPatchIds": ["test-patch"],
            "parts": ["base.html"],
        }
        self.manifest.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        self.version.write_text(
            json.dumps(
                {
                    "versionCode": 1,
                    "versionName": "split-test",
                    "indexUrl": "index.html?v=1",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def write_plan(self, anchors: tuple[str, str] = (SECOND, THIRD)) -> None:
        plan = {
            "schema": 1,
            "sourceParts": ["base.html"],
            "segments": [
                {"path": "document/shell.html"},
                {"path": "runtime/core.html", "startAnchor": anchors[0]},
                {"path": "features/tail.html", "startAnchor": anchors[1]},
            ],
            "sourceRoleUpdates": {
                "documentTitle": "document/shell.html",
                "runtimeIdentity": "runtime/core.html",
            },
        }
        self.plan.write_text(
            json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
        )

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class SplitterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = SplitFixture()
        self.fixture.write_plan()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_rejects_missing_anchor_without_writes(self) -> None:
        before = self.fixture.source.read_bytes()
        self.fixture.write_plan(("<!-- DOES NOT EXIST -->\n", THIRD))
        with self.assertRaisesRegex(splitter.SplitError, "startAnchor is missing"):
            splitter.prepare(self.fixture.plan, self.fixture.manifest)
        self.assertEqual(before, self.fixture.source.read_bytes())
        self.assertFalse((self.fixture.src / "document" / "shell.html").exists())

    def test_rejects_duplicate_anchor(self) -> None:
        self.fixture.close()
        self.fixture = SplitFixture(duplicate_second=True)
        self.fixture.write_plan()
        with self.assertRaisesRegex(splitter.SplitError, "must occur exactly once; found 2"):
            splitter.prepare(self.fixture.plan, self.fixture.manifest)

    def test_rejects_anchors_in_wrong_order(self) -> None:
        self.fixture.write_plan((THIRD, SECOND))
        with self.assertRaisesRegex(splitter.SplitError, "wrong order"):
            splitter.prepare(self.fixture.plan, self.fixture.manifest)

    def test_apply_is_byte_identical_and_updates_roles(self) -> None:
        output_before = self.fixture.output.read_bytes()
        version_before = self.fixture.version.read_bytes()
        prepared = splitter.prepare(self.fixture.plan, self.fixture.manifest)
        splitter.apply(prepared, self.fixture.manifest)

        self.assertFalse(self.fixture.source.exists())
        manifest = json.loads(self.fixture.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            ["document/shell.html", "runtime/core.html", "features/tail.html"],
            manifest["parts"],
        )
        self.assertEqual("document/shell.html", manifest["sourceRoles"]["documentTitle"])
        self.assertEqual("runtime/core.html", manifest["sourceRoles"]["runtimeIdentity"])
        self.assertEqual(
            output_before,
            b"".join((self.fixture.src / path).read_bytes() for path in manifest["parts"]),
        )
        self.assertEqual(output_before, self.fixture.output.read_bytes())
        self.assertEqual(version_before, self.fixture.version.read_bytes())
        builder.check(self.fixture.manifest)

    def test_apply_rolls_back_all_paths_when_post_write_check_fails(self) -> None:
        manifest_before = self.fixture.manifest.read_bytes()
        source_before = self.fixture.source.read_bytes()
        output_before = self.fixture.output.read_bytes()
        version_before = self.fixture.version.read_bytes()
        prepared = splitter.prepare(self.fixture.plan, self.fixture.manifest)
        real_check = builder.check
        checks = 0

        def fail_second_check(path: Path) -> str:
            nonlocal checks
            checks += 1
            if checks == 2:
                raise builder.BuildError("intentional post-delete failure")
            return real_check(path)

        with mock.patch.object(splitter.builder, "check", side_effect=fail_second_check):
            with self.assertRaisesRegex(builder.BuildError, "intentional post-delete failure"):
                splitter.apply(prepared, self.fixture.manifest)

        self.assertEqual(manifest_before, self.fixture.manifest.read_bytes())
        self.assertEqual(source_before, self.fixture.source.read_bytes())
        self.assertEqual(output_before, self.fixture.output.read_bytes())
        self.assertEqual(version_before, self.fixture.version.read_bytes())
        self.assertFalse((self.fixture.src / "document" / "shell.html").exists())
        self.assertFalse((self.fixture.src / "runtime" / "core.html").exists())
        self.assertFalse((self.fixture.src / "features" / "tail.html").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
