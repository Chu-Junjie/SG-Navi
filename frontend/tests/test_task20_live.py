"""Task 20 live Concept01: root/local entries and existing API kept intact."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LiveActionFirstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flowscript = (ROOT / "frontend/js/task15-flow.js").read_text(encoding="utf-8")
        cls.style = (ROOT / "frontend/css/task20-live.css").read_text(encoding="utf-8")

    def test_both_real_entries_have_new_layout_and_existing_skyline(self):
        for path, asset in [
            ("index.html", "./frontend/assets/sg-skyline.webp"),
            ("frontend/index.html", "./assets/sg-skyline.webp"),
        ]:
            with self.subTest(path=path):
                html=(ROOT/path).read_text(encoding="utf-8")
                self.assertIn('id="problem-text"', html)
                self.assertIn('id="problem-review"', html)
                self.assertIn('id="candidate-facts"', html)
                self.assertIn('Find my next step', html)
                self.assertIn(asset, html)
                self.assertIn("task20-live.css", html)
                self.assertIn("task15-flow.js", html)
                self.assertNotIn('class="choices"', html)
                self.assertNotIn('id="api-status"', html)
                self.assertNotIn("task20-concept.js", html)

    def test_single_reusable_modal_and_real_api(self):
        script=self.flowscript
        for fragment in ("task20-overlay", 'role","dialog"',
                         'aria-modal","true"', "function openModal",
                         "function closeModal", "event.key===\"Escape\"",
                         '"/api/intake"', '"/api/intake/confirm"', '"/api/guidance"',
                         "task20-primary", "task20-checklist", "task20-more",
                         "selectClaim(firstStep)"):
            self.assertIn(fragment,script)

    def test_scroll_and_safety_without_fabricating_contact(self):
        style=self.style
        for fragment in ("max-height:min(67dvh,650px)", "overflow-y:auto",
                         "max-height:calc(100dvh - 36px)", "prefers-reduced-motion"):
            self.assertIn(fragment,style)
        script=self.flowscript
        self.assertIn("await verifyResult(data,win.crypto)",script)
        self.assertIn("safeSource(record.url)",script)
        self.assertNotIn("admin@case.org.sg",script)
        self.assertNotIn("6277 5100",script)


if __name__ == "__main__":
    unittest.main()
