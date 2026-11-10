"""Regression guards for Task 23 homepage logo, layout and footer cleanup."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class Task23HomepageVisualTests(unittest.TestCase):
    def test_actual_entrypoints_have_natural_logo_and_no_duplicate_language_badge(self):
        css=(ROOT/"frontend/css/task23-ui.css").read_text(encoding="utf-8")
        self.assertIn(".brand-logo{height:39px;max-width:160px",css)
        self.assertIn("mix-blend-mode:screen",css)
        self.assertIn("grayscale(1) invert(1) contrast(1.3)",css)
        self.assertNotIn("filter:brightness(0) invert(1)",css)
        self.assertIn(".site-header .brand{display:inline-flex",css)
        self.assertIn("background:transparent;border:0;box-shadow:none",css)
        self.assertNotIn(".site-footer{background:var(--navy-deep)",css)
        for path in ("index.html","frontend/index.html"):
            with self.subTest(page=path):
                html=(ROOT/path).read_text(encoding="utf-8")
                self.assertIn('class="brand-logo"',html)
                self.assertIn('data-task23-language="en"',html)
                self.assertIn('data-task23-language="zh"',html)
                self.assertNotIn("English · Singapore",html)
                self.assertNotIn('class="intake-language"',html)
                self.assertNotIn('class="site-footer shell"',html)
                self.assertIn("For demonstration only · Not legal advice · Does not submit cases",html)
                self.assertIn("sg-skyline.webp",html)

    def test_language_still_has_header_toggle_and_no_removed_targets(self):
        js=(ROOT/"frontend/js/task23-locale.js").read_text(encoding="utf-8")
        self.assertIn("[data-task23-language]",js)
        self.assertIn("For demonstration only · Not legal advice · Does not submit cases",js)
        self.assertNotIn('[".intake-language","English · Singapore"]',js)
        self.assertNotIn('[".site-footer","SG Navi',js)


if __name__=="__main__":
    unittest.main()
