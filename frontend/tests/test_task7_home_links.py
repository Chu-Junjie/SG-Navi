"""Task 7 integration homepage navigates to two existing schema forms without extra fields."""
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]

class CandidateHomeLinksTests(unittest.TestCase):
    def test_candidate_homepage_link_contract(self):
        html = (FRONTEND / "index.html").read_text(encoding="utf-8")
        js = (FRONTEND / "js" / "task5-flow.js").read_text(encoding="utf-8")
        self.assertIn('data-case="Rental Deposit"', html)
        self.assertIn('data-case="Consumer Complaint"', html)
        self.assertEqual(html.count("Open guided form"), 2)
        self.assertIn('window.location.assign("./task5-flow.html?case_type=" + caseType)', html)
        self.assertIn('new URLSearchParams(window.location.search).get("case_type")', js)
        self.assertIn('Object.prototype.hasOwnProperty.call(CASES, requestedCase)', js)
        self.assertNotIn('placeholder in Task 1', html)

if __name__ == "__main__":
    unittest.main()
