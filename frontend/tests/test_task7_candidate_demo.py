"""Task 7 candidate: actual Chromium page journeys, real Flask + RAG and screenshot evidence.

Test runs against the existing integration app; no intercepted API answers.
A missing browser/Node runtime reports explicit NOT RUN instead of PASS.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(ROOT))

class Task7CandidateBrowserDemos(unittest.TestCase):
    def test_both_real_candidate_journeys(self):
        node = shutil.which("node")
        browser = next((v for n in ("google-chrome","chromium","chromium-browser","microsoft-edge","msedge")
                        if (v := shutil.which(n))), None)
        if sys.platform == "win32" and not browser:
            browser = next((str(p) for p in [
                Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            ] if p.exists()), None)
        if not node or not browser:
            self.skipTest("NOT RUN: Node.js 22+ or Chromium/Chrome/Edge not installed")
        version = subprocess.run([node,"--version"],capture_output=True,text=True,
                                 encoding="utf-8",errors="replace",timeout=8,check=False)
        try:
            node_major = int(version.stdout.strip().lstrip("v").split(".")[0])
        except (ValueError, IndexError):
            node_major = 0
        if node_major < 22:
            self.skipTest("NOT RUN: Node.js 22+ needed for WebSocket CDP")
        from integration.app import create_app
        from werkzeug.serving import make_server
        webapp = make_server("127.0.0.1",0,create_app(),threaded=True)
        thread = threading.Thread(target=webapp.serve_forever,daemon=True)
        thread.start()
        try:
            env = os.environ.copy()
            env["SG_NAVI_TEST_SHA"] = env.get("GITHUB_SHA","local-unspecified")
            if env.get("GITHUB_ACTIONS") == "true":
                env["SG_NAVI_EXPORT_SCREENSHOTS"] = "1"
            cmd=[node,str(FRONTEND/"tests"/"task7_candidate_demo.mjs"),
                 "http://127.0.0.1:"+str(webapp.server_port),browser]
            done=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,
                                text=True,encoding="utf-8",errors="replace",timeout=160,check=False)
            # These are real screenshots and observed browser results. CI logs retain the
            # screenshot chunks to allow the owners to attach exact raw image bytes.
            print("\nTASK 7 CANDIDATE BROWSER EVIDENCE START")
            print(done.stdout)
            if done.stderr:
                print("Chromium stderr (last 2400 chars): "+done.stderr[-2400:])
            line=next((x.partition("SGNAVI_TASK7_JSON=")[2] for x in
                       done.stdout.splitlines() if x.startswith("SGNAVI_TASK7_JSON=")),None)
            self.assertIsNotNone(line,"Browser did not produce machine-readable results:\n"
                                 +done.stdout[-7000:]+done.stderr[-1500:])
            data=json.loads(line)
            self.assertEqual(data.get("scope"),"task7_candidate_real_browser")
            self.assertEqual(len(data.get("cases",[])),2,done.stdout[-8000:])
            for case in data["cases"]:
                failures=[x for x in case["steps"] if x["result"]!="PASS"]
                self.assertEqual(failures,[],case["case_type"]+": "+json.dumps(failures))
                self.assertTrue(case["passed"],case["case_type"])
                self.assertEqual(len(case["steps"]),9,case["case_type"])
            self.assertEqual(len(data.get("screenshots",[])),4,"Four browser screenshots required")
            self.assertEqual(data.get("javascript_exceptions"),0,"JavaScript exceptions")
            self.assertEqual(done.returncode,0,done.stdout[-15000:]+done.stderr[-2000:])
        finally:
            webapp.shutdown()
            webapp.server_close()
            thread.join(timeout=4)

if __name__=="__main__":
    unittest.main()
