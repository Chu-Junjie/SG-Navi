"""Task 10: conservative result viewer, existing Task 9/legacy compatibility."""
import unittest
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Task10ViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "frontend/task9-clarify.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "frontend/js/task9-clarify.js").read_text(encoding="utf-8")
        cls.viewer = (ROOT / "frontend/js/task10-results.js").read_text(encoding="utf-8")

    def test_accessible_results_and_compatibility(self):
        for phrase in (
            'id="task10-fact-summary"', 'id="task10-source-list"',
            'id="task10-evidence-viewer"', 'id="task10-evidence-details"',
            'id="task10-refine"', 'id="task10-retry"',
            'src="./js/task10-results.js"', 'href="./task5-flow.html"',
            'id="result-warnings"', 'id="result-title"',
        ):
            self.assertIn(phrase,self.html)
        self.assertIn("SGNaviTask10?.render",self.app)
        self.assertIn("SGNaviTask10.clear",self.app)
        self.assertIn("SGNaviVerifiedSources?.selectVerifiedSources",self.app)
        self.assertTrue((ROOT/"frontend/task5-flow.html").exists())

    def test_prohibit_manufactured_evidence_or_browser_persistence(self):
        for snippet in ("innerHTML","localStorage","sessionStorage","fakeScreenshot","eligibilityScore"):
            self.assertNotIn(snippet,self.viewer)
        for snippet in (
            'payload.api_version !== "1.0"',
            'payload.action_card !== null',
            'Review date","Not supplied by this API',
            'Exact official excerpt","Not supplied by this API',
            'rel = "noopener noreferrer"',
        ):
            self.assertIn(snippet,self.viewer)

    def test_node_suite(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable; browser/JS acceptance not established")
        test_file=ROOT/"frontend/tests/test_task10_results.cjs"
        run=subprocess.run(
            [node,"--test",str(test_file)],
            capture_output=True,text=True,encoding="utf-8",errors="replace",
            timeout=40,check=False,
        )
        self.assertEqual(run.returncode,0,run.stdout+"\n"+run.stderr)


if __name__=="__main__":
    unittest.main()
