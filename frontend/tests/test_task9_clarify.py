"""Task 9 checks: new question route without removing compatibility form."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DynamicClarificationPageTests(unittest.TestCase):
    def test_guided_ui_is_frontend_owned(self):
        page = (ROOT / "frontend/task9-clarify.html").read_text(encoding="utf-8")
        for phrase in (
            'id="case-type"', 'id="question-area"', 'id="answer-form"',
            'id="question-back"', 'id="question-continue"', 'id="retry"',
            'id="confirmed-facts"', 'id="result"', 'id="change-problem"',
            'id="legacy-link"', 'href="./task5-flow.html"',
            'src="./js/task9-clarify.js"', 'src="./js/api-config.js"',
            'src="./js/verified-sources.js"', "Student demonstration",
            "Not legal advice",
        ):
            self.assertIn(phrase, page)

    def test_existing_task5_remains_available(self):
        self.assertTrue((ROOT / "frontend/task5-flow.html").exists())
        js = (ROOT / "frontend/js/task9-clarify.js").read_text(encoding="utf-8")
        for phrase in (
            'SGNaviApiConfig.resolve("/api/navigate", win.location)',
            'api_version:"1.0"', 'source_version',
            'state.pending?.abort()', 'state.revision', 'answerControls.replaceChildren()',
            'win.SGNaviVerifiedSources?.selectVerifiedSources',
            'win.SGNaviTask10?.render',
            'win.SGNaviTask10Guidance.render',
        ):
            self.assertIn(phrase, js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sessionStorage", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("eligibility_threshold", js)

    def test_task8_continues_into_task9_without_propagating_description(self):
        js = (ROOT / "frontend/js/task8-home.js").read_text(encoding="utf-8")
        self.assertIn('formPath.replace("task5-flow.html", "task9-clarify.html")', js)
        self.assertIn('win.location.assign(guidedPath + "?case_type=" + topic)', js)
        self.assertNotIn("encodeURIComponent(problem)", js)


if __name__ == "__main__":
    unittest.main()
