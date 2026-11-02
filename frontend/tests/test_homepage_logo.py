"""Verify the real SG Navi logo lockup is not cropped in either homepage."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "frontend" / "assets" / "sg-navi-logo.webp"

class HomepageLogoTests(unittest.TestCase):
    def test_lossless_webp_is_complete(self):
        content = LOGO.read_bytes()
        self.assertGreater(len(content), 4000)
        self.assertEqual(content[:4], b"RIFF")
        self.assertEqual(content[8:12], b"WEBP")
        self.assertEqual(int.from_bytes(content[4:8], "little") + 8, len(content))
    def test_both_homepages_use_original_full_logo(self):
        for file, src in ((ROOT / "index.html", "./frontend/assets/sg-navi-logo.webp"),
                          (ROOT / "frontend" / "index.html", "./assets/sg-navi-logo.webp")):
            with self.subTest(file=str(file)):
                s = file.read_text(encoding="utf-8")
                self.assertIn('class="brand-logo"', s)
                self.assertIn('src="' + src + '"', s)
                self.assertIn('object-fit: contain;', s)
                self.assertNotIn('class="brand-mark"', s)
                self.assertNotIn('class="brand-name"', s)
                self.assertTrue((file.parent / src).is_file())

if __name__ == "__main__":
    unittest.main()
