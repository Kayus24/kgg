import json
import sys
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
        with self.assertRaisesRegex(archive.ChangelogArchiveError, "exactly one snapshot"):
            archive.validate_changelog_archives(changelog, required=True)

    def test_archive_keeps_the_reviewed_v062_snapshot_exactly(self):
        document = json.loads(archive.ARCHIVE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(34, len(document["entries"]))
        self.assertEqual(
            "d1b3a5d67dd78ae6819bfbf28b321c66cdacdc173b4c39b358344e380fb30fef",
            archive.entries_sha256(document["entries"]),
        )

    def test_embedded_window_is_a_suffix_preserving_archive_order(self):
        _text, changelog = archive.load_embedded()
        document = archive.validate_changelog_archives(changelog, required=True)
        self.assertIsNotNone(document)
        self.assertEqual(
            document["entries"][: archive.RETAINED_ENTRY_COUNT],
            changelog["entries"][-archive.RETAINED_ENTRY_COUNT :],
        )
        combined_count = len(document["entries"]) + len(changelog["entries"]) - archive.RETAINED_ENTRY_COUNT
        self.assertGreaterEqual(combined_count, 35)


if __name__ == "__main__":
    unittest.main(verbosity=2)
