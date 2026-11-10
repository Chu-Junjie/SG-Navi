"""Previously public two-card entry is intentionally migrated in Task 20.

The original guided URLs remain available for historical compatibility until
coordinator authorizes redirect; root homepage now starts the real Task15 APIs.
"""
import unittest
from pathlib import Path

FRONTEND=Path(__file__).resolve().parents[1]


class CandidateHomeLinksTests(unittest.TestCase):
    def test_new_homepage_uses_real_task15_entry_and_legacy_form_still_exists(self):
        html=(FRONTEND/"index.html").read_text(encoding="utf-8")
        flow=(FRONTEND/"js/task15-flow.js").read_text(encoding="utf-8")
        legacy=(FRONTEND/"js/task5-flow.js").read_text(encoding="utf-8")
        self.assertIn('id="problem-intake"',html)
        self.assertIn('id="problem-text"',html)
        self.assertIn('src="./js/task15-flow.js"',html)
        self.assertNotIn('class="choices"',html)
        self.assertIn('"/api/intake"',flow)
        self.assertIn('"/api/guidance"',flow)
        self.assertIn('new URLSearchParams(window.location.search).get("case_type")',legacy)
        self.assertIn('Object.prototype.hasOwnProperty.call(CASES, requestedCase)',legacy)
        self.assertIn('href="../" aria-label="SG Navi home"><img src="./assets/sg-navi-logo-2026.png"',(FRONTEND/"task5-flow.html").read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
