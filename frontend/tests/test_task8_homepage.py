"""Task8 problem-first input remains, with Task20's compact layout and real Task15 intake."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

class Task8HomepageTests(unittest.TestCase):
    def test_both_homepages_have_accessible_problem_first_entry(self):
        for path in (ROOT/"index.html",ROOT/"frontend/index.html"):
            with self.subTest(page=str(path)):
                html=path.read_text(encoding="utf-8")
                for required in (
                    'id="problem-form"','id="problem-text"','id="problem-submit"',
                    'type="submit" disabled>Find my next step',
                    'for="problem-text"','id="problem-review"',
                    'id="review-title" tabindex="-1"','id="review-back"',
                    'id="review-continue"','value="unsure"','value="other"',
                    'data-example-question=','maxlength="1200"',
                    'src="./','task15-flow.js','task20-live.css',
                    'For demonstration only','Not legal advice','made-up details',
                ):
                    self.assertIn(required,html)
                self.assertNotIn('id="api-status"',html)
                self.assertNotIn('class="choice-label">Open guided form',html)
                self.assertNotIn("EN / 中文",html)
    def test_assets_are_safely_scoped(self):
        public=(ROOT/"index.html").read_text(encoding="utf-8")
        local=(ROOT/"frontend/index.html").read_text(encoding="utf-8")
        for path in ("./frontend/css/task8-home.css","./frontend/js/task8-home.js"):
            self.assertIn(path,public)
        for path in ("./css/task8-home.css","./js/task8-home.js"):
            self.assertIn(path,local)
        for path in ("frontend/css/task20-live.css","frontend/js/task15-flow.js"):
            self.assertTrue((ROOT/path).is_file())
    def test_real_api_confirmation_does_not_persist_private_description(self):
        script=(ROOT/"frontend/js/task15-flow.js").read_text(encoding="utf-8")
        self.assertIn('await post("/api/intake"',script)
        self.assertIn('await post("/api/guidance"',script)
        self.assertNotIn("localStorage",script)
        self.assertNotIn("sessionStorage",script)
        self.assertNotIn("innerHTML",script)

if __name__=="__main__":
    unittest.main()
