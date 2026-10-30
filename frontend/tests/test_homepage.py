"""Task 1 homepage structural checks; stdlib only (no backend required)."""
import re
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "index.html"


class HomepageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_title_and_brand(self):
        self.assertIn("<title>SG Navi | Start Here</title>", self.html)
        self.assertIn('aria-label="SG Navi compass logo"', self.html)
        self.assertIn('class="brand-name">SG Navi</span>', self.html)

    def test_only_two_task1_topics(self):
        matches = re.findall(r'data-case="([^"]+)"', self.html)
        self.assertEqual(matches, ["Rental Deposit", "Consumer Complaint"])
        self.assertEqual(self.html.count("Flow coming soon"), 2)
        self.assertNotIn('action="/api/navigate"', self.html)

    def test_health_status_uses_real_request(self):
        self.assertIn('fetch("/api/health"', self.html)
        self.assertIn('response.ok', self.html)
        self.assertIn('statusPanel.dataset.state = "offline"', self.html)
        self.assertIn('statusPanel.dataset.state = "online"', self.html)
        self.assertIn('role="status"', self.html)


if __name__ == "__main__":
    unittest.main()
