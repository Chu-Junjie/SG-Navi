"""Task 20/21 pre-contract UI fixture checks. Not a published API test."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]


class Task20ConceptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (FRONTEND / "task20-concept.html").read_text(encoding="utf-8")
        cls.css = (FRONTEND / "css/task20-concept.css").read_text(encoding="utf-8")
        cls.script = (FRONTEND / "js/task20-concept.js").read_text(encoding="utf-8")

    def test_single_input_and_one_persistent_question_modal(self):
        self.assertEqual(self.page.count('id="question-overlay"'), 1)
        self.assertEqual(self.page.count('role="dialog" aria-modal="true" aria-labelledby="dialog-heading"'), 1)
        self.assertEqual(self.page.count('id="description"'), 1)
        self.assertIn('id="question-options"', self.page)
        self.assertIn('id="question-back"', self.page)
        self.assertIn('id="question-next"', self.page)
        self.assertIn('function focusTrap(e)', self.script)
        self.assertIn('state.lastFocus', self.script)
        self.assertIn('e.key==="Escape"', self.script)

    def test_first_step_and_disclosures_are_scroll_bounded(self):
        self.assertIn('id="action-heading"', self.page)
        self.assertIn('id="next-step"', self.page)
        self.assertIn('id="quick-list"', self.page)
        self.assertIn('id="extra"', self.page)
        self.assertIn('id="details-overlay"', self.page)
        self.assertIn('max-height:min(55dvh,500px)', self.css)
        self.assertIn('overflow-y:auto', self.css)
        self.assertIn('@media(max-width:700px)', self.css)
        self.assertIn('prefers-reduced-motion', self.css)

    def test_no_fabricated_legal_contact_or_private_transmission(self):
        for expression in ("fetch(", "localStorage", "sessionStorage", "innerHTML",
                           "tel:", "mailto:", "refund guaranteed", "automatically eligible"):
            self.assertNotIn(expression, self.script)
        self.assertIn("No data has been submitted.", self.script)
        self.assertIn("Not a verified source match", self.page)
        self.assertIn("noopener noreferrer", self.script)
        self.assertIn('https://www.case.org.sg/submit-a-complaint/', self.script)

    def test_browser_script_has_valid_syntax_and_pure_helpers(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable; browser script syntax not checked here")
        filename = str(FRONTEND / "js/task20-concept.js")
        for args in (
            [node, "--check", filename],
            [node, "--test", str(FRONTEND / "tests/test_task20_concept.cjs")],
        ):
            result = subprocess.run(args, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
