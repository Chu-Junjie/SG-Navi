"""Task 10 continuation: additive Task 12/14 result and evidence UI adapter."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Task10EnrichedAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "frontend/task9-clarify.html").read_text(encoding="utf-8")
        cls.flow = (ROOT / "frontend/js/task9-clarify.js").read_text(encoding="utf-8")
        cls.adapter = (ROOT / "frontend/js/task10-guidance.js").read_text(encoding="utf-8")
        cls.config = (ROOT / "frontend/js/api-config.js").read_text(encoding="utf-8")

    def test_additive_real_api_wiring_and_legacy_fallback(self):
        self.assertIn('src="./js/task10-guidance.js"', self.page)
        self.assertIn('SGNaviApiConfig.resolve("/api/results/preview",win.location)', self.flow)
        self.assertIn('results_version:"0.1",confirmed:true', self.flow)
        self.assertIn('case_type:caseType,confirmed_answers:{...answers}', self.flow)
        self.assertIn('win.SGNaviTask10Guidance.render', self.flow)
        self.assertIn('win.SGNaviTask10?.render(payload,doc', self.flow)
        self.assertIn('SGNaviApiConfig.resolve("/api/navigate", win.location)', self.flow)
        self.assertIn('"/api/results/preview"', self.config)

    def test_truthful_sources_and_stale_result_invalidation(self):
        for name in ("verbatim_excerpt", "summary", "source_locator", "reviewed_at",
                     "source_version", "display_state", "verified_snapshot",
                     "evidence_ids", "claim_citations", "LIMITED_REFERRAL",
                     "GUIDANCE_ONLY", "Open Original Source"):
            self.assertIn(name, self.adapter)
        self.assertIn('state.pending?.abort()', self.flow)
        self.assertIn('revision !== state.revision', self.flow)
        self.assertIn('win.SGNaviTask10.clear(doc)', self.flow)
        self.assertIn('win.SGNaviTask10Guidance.clear(doc)', self.flow)
        for forbidden in ("innerHTML", "localStorage", "sessionStorage",
                          "eligibilityScore", "fakeScreenshot"):
            self.assertNotIn(forbidden, self.adapter)

    def test_javascript_unit_suite(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed in test environment")
        run = subprocess.run(
            [node, "--test", str(ROOT / "frontend/tests/test_task10_guidance.cjs")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=40, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stdout + "\n" + run.stderr)


if __name__ == "__main__":
    unittest.main()
