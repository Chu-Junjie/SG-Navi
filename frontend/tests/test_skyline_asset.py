"""Guard against truncated skyline uploads and broken homepage asset paths."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "frontend" / "assets" / "sg-skyline.webp"


class SkylineAssetTests(unittest.TestCase):
    def test_uploaded_webp_is_complete(self):
        content = ASSET.read_bytes()
        self.assertGreater(len(content), 30_000, "Skyline image appears truncated")
        self.assertEqual(content[:4], b"RIFF")
        self.assertEqual(content[8:12], b"WEBP")
        self.assertEqual(int.from_bytes(content[4:8], "little") + 8, len(content),
                         "WebP RIFF declared file size does not match actual bytes")
        self.assertIn(content[12:16], (b"VP8 ", b"VP8L", b"VP8X"))

    def test_root_and_frontend_html_use_existing_relative_image(self):
        for page, expected in (
            (ROOT / "index.html", "./frontend/assets/sg-skyline.webp"),
            (ROOT / "frontend" / "index.html", "./assets/sg-skyline.webp"),
        ):
            with self.subTest(page=str(page)):
                html = page.read_text(encoding="utf-8")
                self.assertEqual(html.count(f'url("{expected}")'), 2)
                self.assertTrue((page.parent / expected).is_file())
                self.assertTrue(re.search(r'background-image\s*:', html))


if __name__ == "__main__":
    unittest.main()
