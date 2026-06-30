import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kgg_encoding_guard import validate_html_encoding


class EncodingGuardTests(unittest.TestCase):
    def findings(self, html: str):
        return validate_html_encoding(html.encode("utf-8"), "test")

    def test_accepts_early_utf8_charset_before_umlauts_and_icons(self):
        html = '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<title>Übungen 📦</title></head><body>Übungsdatenbank</body></html>'
        self.assertEqual([], self.findings(html))

    def test_rejects_late_charset_after_non_ascii(self):
        html = '<!doctype html>\n<html lang="de">\n<head>\n<!-- Übung before charset -->\n<meta charset="utf-8">\n<title>KGG</title></head></html>'
        messages = " ".join(f.message for f in self.findings(html))
        self.assertIn("First non-ASCII byte", messages)

    def test_rejects_mojibake_markers(self):
        mojibake = "\u00c3\u0153bungen \u00e2\u017e\u2022 \u00e2\u2013\u00b6 \u00e2\u0161\u2122\u00ef\u00b8\u008f \u00e2\u0152\u0192 \u00f0\u0178\u201c\u00a6"
        html = f'<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<title>{mojibake}</title></head></html>'
        messages = " ".join(f.message for f in self.findings(html))
        self.assertIn("Mojibake marker", messages)

    def test_rejects_missing_charset(self):
        html = "<!doctype html>\n<html lang=\"de\">\n<head>\n<title>KGG</title></head></html>"
        messages = " ".join(f.message for f in self.findings(html))
        self.assertIn("Missing early", messages)


if __name__ == "__main__":
    unittest.main()
