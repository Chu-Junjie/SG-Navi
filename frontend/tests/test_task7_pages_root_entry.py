"""Task 7 Pages entry regression checks (coordinator-authorized root-only change).

Checks static wiring, not a claim that GitHub Pages has published this commit.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class PublicPagesRootEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_both_public_buttons_are_active(self):
        self.assertIn('data-case="Rental Deposit"', self.html)
        self.assertIn('data-case="Consumer Complaint"', self.html)
        self.assertEqual(self.html.count('class="choice-label">Open guided form'), 2)
        self.assertNotIn("Flow coming soon", self.html)
        self.assertNotIn("placeholder in Task 1", self.html)
        self.assertIn('caseType = button.dataset.case === "Rental Deposit" ? "rental_deposit"', self.html)
        self.assertIn('button.dataset.case === "Consumer Complaint" ? "consumer_complaint"', self.html)
        self.assertIn('window.location.assign("./frontend/task5-flow.html?case_type=" + caseType)', self.html)

    def test_real_approved_api_health_resolver(self):
        self.assertIn('<script src="./frontend/js/api-config.js"></script>', self.html)
        self.assertIn('SGNaviApiConfig.resolve("/api/health", window.location)', self.html)
        self.assertIn("fetch(endpoint", self.html)
        self.assertNotIn('fetch("/api/health"', self.html)
        self.assertIn('statusPanel.dataset.state = "offline"', self.html)
        self.assertIn('statusPanel.dataset.state = "online"', self.html)

    def test_relative_static_assets_and_both_form_paths_exist(self):
        self.assertTrue((ROOT / "frontend" / "js" / "api-config.js").is_file())
        self.assertTrue((ROOT / "frontend" / "task5-flow.html").is_file())
        self.assertTrue((ROOT / "frontend" / "schemas" / "rental_deposit_input.schema.json").is_file())
        self.assertTrue((ROOT / "frontend" / "schemas" / "consumer_complaint_input.schema.json").is_file())

if __name__ == "__main__":
    unittest.main()
