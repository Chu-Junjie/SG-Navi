"""Actual homepage regression after authorized Task 20 UI migration."""
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "index.html"


class HomepageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_title_and_brand(self):
        self.assertIn("<title>SG Navi | Start Here</title>", self.html)
        self.assertIn('alt="SG Navi"', self.html)
        self.assertIn('class="brand-logo"', self.html)

    def test_one_input_replaces_legacy_topic_cards(self):
        self.assertIn('id="problem-text"', self.html)
        self.assertIn('id="problem-review"', self.html)
        self.assertIn('id="problem-submit"', self.html)
        self.assertIn("Find my next step", self.html)
        self.assertEqual(self.html.count('class="choice"'), 0)
        self.assertNotIn("Open guided form", self.html)
        self.assertNotIn('action="/api/navigate"', self.html)

    def test_api_versioned_integration_remains_on_real_script(self):
        self.assertIn('src="./js/api-config.js"', self.html)
        self.assertIn('src="./js/task15-flow.js"', self.html)
        self.assertIn('src="./css/task20-live.css"', self.html)
        self.assertIn('content="/api/health"', self.html)
        self.assertNotIn('id="api-status"', self.html)


if __name__ == "__main__":
    unittest.main()
