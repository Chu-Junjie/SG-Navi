"""Plain-language checks for public and local SG Navi entry pages.

Assertions cover visitor-visible HTML and status copy. They do not replace
live Pages browser verification or change the API integration contract.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PlainLanguageHomepagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {
            "public Pages homepage": (ROOT / "index.html").read_text(encoding="utf-8"),
            "local frontend homepage": (ROOT / "frontend/index.html").read_text(encoding="utf-8"),
        }

    def test_no_prototype_or_developer_status_is_displayed(self):
        for name, html in self.pages.items():
            with self.subTest(page=name):
                for phrase in (
                    "prototype", "Backend API status", "GET /api/health</span>",
                    "Health endpoint responded", "Backend not reachable",
                    "Public API not configured", "verified HTTPS backend",
                    "synthetic information only",
                ):
                    self.assertNotIn(phrase.lower(), html.lower())

                for phrase in (
                    "For demonstration only", "Not legal advice",
                    "Does not submit cases", "made-up details",
                    "Is the service available?", "Online · Ready to use",
                    "Unavailable · Please try again later",
                ):
                    self.assertIn(phrase, html)

    def test_live_two_topic_navigation_and_health_are_preserved(self):
        for name, html in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual(html.count('class="choice-label">Open guided form'), 2)
                self.assertIn('data-case="Rental Deposit"', html)
                self.assertIn('data-case="Consumer Complaint"', html)
                self.assertIn('SGNaviApiConfig.resolve("/api/health", window.location)', html)
                self.assertIn('statusPanel.dataset.state = "online"', html)
                self.assertIn('statusPanel.dataset.state = "offline"', html)
                self.assertIn('id="refresh-api"', html)

        self.assertIn(
            'window.location.assign("./frontend/task5-flow.html?case_type=" + caseType)',
            self.pages["public Pages homepage"],
        )
        self.assertIn(
            'window.location.assign("./task5-flow.html?case_type=" + caseType)',
            self.pages["local frontend homepage"],
        )


if __name__ == "__main__":
    unittest.main()
