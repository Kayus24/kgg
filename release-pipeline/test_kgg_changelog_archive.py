import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_changelog_archive as archive


class ChangelogArchiveTests(unittest.TestCase):
    def test_current_repository_archive_contract(self):
        archive.validate_repository()

    def test_required_archive_reference_cannot_be_removed(self):
        _text, changelog = archive.load_embedded()
        changelog.pop("archiveSnapshots")
        with self.assertRaisesRegex(archive.ChangelogArchiveError, "legacy v062"):
            archive.validate_changelog_archives(changelog, required=True)

    def test_archive_keeps_the_reviewed_v062_snapshot_exactly(self):
        document = json.loads(archive.ARCHIVE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(34, len(document["entries"]))
        self.assertEqual(
            "d1b3a5d67dd78ae6819bfbf28b321c66cdacdc173b4c39b358344e380fb30fef",
            archive.entries_sha256(document["entries"]),
        )

    def test_current_snapshot_is_full_and_embedded_window_is_its_prefix(self):
        _text, changelog = archive.load_embedded()
        document = archive.validate_changelog_archives(changelog, required=True)
        self.assertIsNotNone(document)
        self.assertEqual(
            document["entries"][: archive.CURRENT_RETAINED_ENTRY_COUNT],
            changelog["entries"],
        )
        reviewed = json.loads((HERE.parent / "docs/changelog-archive/kgg-therapist-changelog-through-v096.json").read_text(encoding="utf-8"))
        self.assertEqual(37, len(reviewed["entries"]))
        self.assertEqual(69, len(document["entries"]))
        self.assertEqual(
            "49767017066c2fbecb49bdec329c3c0c18231747883aa9d2fe3e662ca7c1a9cd",
            archive.entries_sha256(reviewed["entries"]),
        )
        self.assertEqual(archive.CURRENT_RETAINED_ENTRY_COUNT, len(changelog["entries"]))

    def test_legacy_snapshot_remains_referenced_after_current_compaction(self):
        _text, changelog = archive.load_embedded()
        snapshots = changelog["archiveSnapshots"]
        self.assertEqual(15, len(snapshots))
        self.assertIn(archive.archive_reference(), snapshots)
        current = [item for item in snapshots if item != archive.archive_reference()]
        self.assertEqual(14, len(current))
        self.assertEqual(89, current[0]["snapshotVersionCode"])
        self.assertEqual([*range(89, 97), 123, 124, 125, 126, 127, 128], [item["snapshotVersionCode"] for item in current])

    def test_compact_current_recovers_from_previous_compact_window(self):
        _text, current = archive.load_embedded()
        current_archive = json.loads(
            (HERE.parent / current["archiveSnapshots"][-2]["repositoryPath"])
            .read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "kgg-update/src/metadata").mkdir(parents=True)
            (root / "docs/changelog-archive").mkdir(parents=True)
            shutil.copy2(
                HERE.parent / "kgg-update/src/metadata/changelog.html",
                root / "kgg-update/src/metadata/changelog.html",
            )
            shutil.copy2(HERE.parent / "kgg-update/version.json", root / "kgg-update/version.json")
            shutil.copy2(HERE.parent / "kgg-update/src/parts.json", root / "kgg-update/src/parts.json")
            for reference in current["archiveSnapshots"][:-1]:
                shutil.copy2(
                    HERE.parent / reference["repositoryPath"],
                    root / reference["repositoryPath"],
                )
            pre_compaction = dict(current)
            pre_compaction["entries"] = [current["entries"][0]] + current_archive["entries"][: archive.CURRENT_RETAINED_ENTRY_COUNT]
            pre_compaction["archiveSnapshots"] = current["archiveSnapshots"][:-1]
            text = (root / "kgg-update/src/metadata/changelog.html").read_text(encoding="utf-8")
            (root / "kgg-update/src/metadata/changelog.html").write_text(
                archive._replace_json_script(text, "kgg-changelog", pre_compaction),
                encoding="utf-8",
                newline="\n",
            )
            result = archive.compact_current(root)
            self.assertEqual(len(current_archive["entries"]) + 1, result["entryCount"])
            archive.validate_repository(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
