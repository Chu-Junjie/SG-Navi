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
            cwd=FRONTEND, capture_output=True, text=True, timeout=20, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

if __name__ == "__main__":
    unittest.main()
