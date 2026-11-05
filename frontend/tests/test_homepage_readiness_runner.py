"""Exercise the actual two homepage scripts with real response payloads in Node."""
import shutil
import subprocess
import unittest
from pathlib import Path


class HomepageReadinessTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "NOT RUN: Node.js unavailable")
    def test_homepages_reject_unavailable_and_malformed_readiness(self):
        root = Path(__file__).resolve().parents[2]
        done = subprocess.run(
            ["node", "--test", "frontend/tests/test_homepage_readiness.cjs"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
