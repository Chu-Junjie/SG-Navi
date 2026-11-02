"""Run standalone referral-source JavaScript safety tests where Node is available."""
import shutil
import subprocess
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]

class ReferralSourceJavaScriptTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is not available in this Python CI")
    def test_node_source_validation_and_safe_rendering(self):
        result = subprocess.run(
            ["node", "--test", "tests/test_verified_sources.cjs"],
            cwd=FRONTEND, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20, check=False
        )
        diagnostics = (result.stdout or "") + "\n" + (result.stderr or "")
        self.assertEqual(result.returncode, 0, diagnostics)

if __name__ == "__main__":
    unittest.main()
