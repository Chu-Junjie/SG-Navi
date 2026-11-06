"""Run the actual JS protocol and safety tests through existing frontend CI."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class Task15JavaScriptTests(unittest.TestCase):
    def test_integrated_flow_protocol_and_source_integrity(self):
        node=shutil.which("node")
        if not node:self.skipTest("NOT RUN: Node unavailable")
        done=subprocess.run([node,"--test",str(ROOT/"frontend/tests/test_task15_flow.cjs")],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr)
