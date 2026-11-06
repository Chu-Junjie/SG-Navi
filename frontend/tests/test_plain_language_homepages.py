"""Visitor-facing copy checks for the new single-input public and local entries."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class PlainLanguageHomepagesTests(unittest.TestCase):
    def test_both_homepages_match_the_new_action_first_direction(self):
        for name in ("index.html","frontend/index.html"):
            with self.subTest(name=name):
                html=(ROOT/name).read_text(encoding="utf-8")
                for phrase in ("What happened?", "Find my next step",
                               "For demonstration only", "Not legal advice",
                               "Does not submit cases", "made-up details"):
                    self.assertIn(phrase.lower(),html.lower())
                for legacy in ("prototype","Backend API status","Health endpoint responded",
                               "Open guided form","Is the service available?"):
                    self.assertNotIn(legacy.lower(),html.lower())
                self.assertIn('id="problem-review"',html)
                self.assertIn('id="problem-submit"',html)
                self.assertNotIn('id="api-status"',html)


if __name__=="__main__":
    unittest.main()
