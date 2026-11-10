"""Ensure both live homepages present one concise intake prompt."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class IntakeCopyTests(unittest.TestCase):
    def test_no_repeated_introduction_and_accessible_form(self):
        for relpath in ("index.html", "frontend/index.html"):
            with self.subTest(page=relpath):
                html = (ROOT / relpath).read_text(encoding="utf-8")
                self.assertEqual(html.count('id="hero-heading">What happened?</h1>'), 1)
                self.assertNotIn('id="intake-heading">Tell us what happened</h2>', html)
                self.assertNotIn('class="intake-description"', html)
                self.assertIn('id="problem-intake"', html)
                self.assertIn('aria-labelledby="problem-label"', html)
                self.assertIn('id="problem-label" for="problem-text"', html)
                self.assertIn('id="problem-text"', html)
                self.assertIn('id="problem-submit"', html)


if __name__ == "__main__":
    unittest.main()
