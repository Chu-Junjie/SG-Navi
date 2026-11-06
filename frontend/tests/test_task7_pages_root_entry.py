"""Task 7 v1 legacy forms remain available; Task20 publicly migrates to intake first."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class PublicPagesRootEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/"index.html").read_text(encoding="utf-8")
    def test_root_starts_real_intake_instead_of_old_card_navigation(self):
        self.assertIn('id="problem-submit"',self.html)
        self.assertIn('id="problem-text"',self.html)
        self.assertIn('src="./frontend/js/task15-flow.js"',self.html)
        self.assertNotIn('class="choices"',self.html)
        self.assertNotIn("Flow coming soon",self.html)
    def test_real_https_resolver_and_legacy_routes_still_exist(self):
        self.assertIn('<script src="./frontend/js/api-config.js"></script>',self.html)
        self.assertIn('content="/api/health"',self.html)
        script=(ROOT/"frontend/js/task15-flow.js").read_text(encoding="utf-8")
        self.assertIn('SGNaviApiConfig.resolve(path,win.location)',script)
        for route in ("/api/intake","/api/guidance"):
            self.assertIn(route,script)
    def test_relative_assets_and_both_existing_forms_are_available(self):
        for path in ("frontend/js/api-config.js", "frontend/task5-flow.html",
                     "frontend/task9-clarify.html",
                     "frontend/schemas/rental_deposit_input.schema.json",
                     "frontend/schemas/consumer_complaint_input.schema.json"):
            self.assertTrue((ROOT/path).is_file())

if __name__=="__main__":
    unittest.main()
