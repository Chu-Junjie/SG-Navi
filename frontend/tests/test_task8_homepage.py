"""Task 8: new problem-first entry and legacy journey regression checks."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Task8HomepageTests(unittest.TestCase):
    def test_both_homepages_have_accessible_problem_first_entry(self):
        for path in (ROOT / "index.html", ROOT / "frontend" / "index.html"):
            with self.subTest(page=str(path)):
                html = path.read_text(encoding="utf-8")
                for required in (
                    'id="problem-form"', 'id="problem-text"', 'id="problem-submit"',
                    'type="submit">Find Guidance', 'for="problem-text"',
                    'id="problem-review"', 'id="review-title" tabindex="-1"',
                    'id="review-back"', 'id="review-continue"',
                    'value="unsure"', 'value="other"',
                    'data-example-question=', 'maxlength="1200"',
                    'id="api-status"', 'id="refresh-api"',
                    'data-case="Rental Deposit"', 'data-case="Consumer Complaint"',
                    'class="choice-label">Open guided form',
                    'SGNaviApiConfig.resolve("/api/health", window.location)',
                    'For demonstration only', 'Not legal advice', 'made-up details',
                ):
                    self.assertIn(required, html)
                self.assertEqual(html.count('class="choice-label">Open guided form'), 2)
                self.assertNotIn("EN / 中文", html)
                self.assertNotIn("Copy sample question", html)

    def test_public_and_local_assets_are_safely_scoped(self):
        public = (ROOT / "index.html").read_text(encoding="utf-8")
        local = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        for path in ("./frontend/css/task8-home.css", "./frontend/js/task8-home.js"):
            self.assertIn(path, public)
        for path in ("./css/task8-home.css", "./js/task8-home.js"):
            self.assertIn(path, local)
        self.assertIn('data-form-path="./frontend/task5-flow.html"', public)
        self.assertIn('data-form-path="./task5-flow.html"', local)
        for path in ("frontend/css/task8-home.css", "frontend/js/task8-home.js"):
            self.assertTrue((ROOT / path).is_file())

    def test_no_fake_production_intake(self):
        script = (ROOT / "frontend/js/task8-home.js").read_text(encoding="utf-8")
        self.assertIn("Automatic problem understanding is not available yet.", script)
        self.assertIn("Legacy /api/navigate workflow intentionally starts fresh", script)
        self.assertIn("textContent = value", script)
        self.assertNotIn("localStorage", script)
        self.assertNotIn("sessionStorage", script)
        self.assertNotIn("innerHTML", script)
        self.assertNotIn('fetch("/api/intake"', script)


if __name__ == "__main__":
    unittest.main()
