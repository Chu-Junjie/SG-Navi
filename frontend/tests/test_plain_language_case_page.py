"""Regression checks for public-facing form copy; internal API contracts are unchanged."""
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]


class PlainLanguageCasePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (FRONTEND / "task5-flow.html").read_text(encoding="utf-8")
        cls.script = (FRONTEND / "js" / "task5-flow.js").read_text(encoding="utf-8")
        cls.sources = (FRONTEND / "js" / "verified-sources.js").read_text(encoding="utf-8")

    def test_form_uses_clear_labels_and_retains_necessary_disclaimer(self):
        for snippet in (
            "Explore your options", "Your results", "For demonstration only:",
            "not personal information", "does not decide whether you qualify",
            "Official websites to check", "not legal advice",
        ):
            self.assertIn(snippet.lower(), self.page.lower())
        for old in ("Task 5 · Live backend", "Development integration:",
                    "Backend response", "Request preview (synthetic input)",
                    "Verified Source Context"):
            self.assertNotIn(old, self.page)

    def test_internal_debug_values_are_not_visually_presented(self):
        self.assertIn('<span id="status" hidden>', self.page)
        self.assertIn('id="status-friendly"', self.page)
        self.assertIn('<div hidden aria-hidden="true"><pre id="request-preview"', self.page)
        self.assertIn('function setStatus(value)', self.script)
        self.assertIn('NEED_CLARIFICATION: "A few more details needed"', self.script)
        self.assertIn('REFER_TO_OFFICIAL: "Check official information"', self.script)
        self.assertIn('SGNaviApiConfig.resolve("/api/navigate", window.location)', self.script)

    def test_official_links_remain_safe_and_without_technical_metadata_in_copy(self):
        self.assertIn('SGNaviVerifiedSources.renderReferralSources', self.script)
        self.assertIn('link.rel = "noopener noreferrer"', self.sources)
        self.assertIn('Singapore Courts — view official website', self.sources)
        self.assertIn('Consumers Association of Singapore (CASE)', self.sources)
        self.assertNotIn('meta.textContent = "Evidence ID:', self.sources)
        self.assertNotIn('link.textContent = source.source_id', self.sources)


if __name__ == "__main__":
    unittest.main()
