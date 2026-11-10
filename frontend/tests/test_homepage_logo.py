"""Verify the transparent SG Navi logo is used consistently across public pages."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "frontend" / "assets" / "sg-navi-logo-2026.png"

class HomepageLogoTests(unittest.TestCase):
    def test_png_asset_present_and_complete(self):
        content = LOGO.read_bytes()
        self.assertGreater(len(content), 4000)
        self.assertEqual(content[:8], b"\x89PNG\r\n\x1a\n")

    def test_both_homepages_use_new_full_logo(self):
        for file, src in ((ROOT / "index.html", "./frontend/assets/sg-navi-logo-2026.png"),
                          (ROOT / "frontend" / "index.html", "./assets/sg-navi-logo-2026.png"),
                          (ROOT / "frontend" / "task5-flow.html", "./assets/sg-navi-logo-2026.png")):
            with self.subTest(file=str(file)):
                text = file.read_text(encoding="utf-8")
                self.assertIn('src="' + src + '"', text)
                self.assertTrue((file.parent / src).is_file())

    def test_no_legacy_logo_filter(self):
        css = (ROOT / "frontend" / "css" / "task23-ui.css").read_text(encoding="utf-8")
        self.assertIn("filter:none", css)
        self.assertNotIn("sg-navi-original-logo-outline", css)

if __name__ == "__main__":
    unittest.main()
