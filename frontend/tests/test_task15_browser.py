"""Real local two-case integrated browser journey; no synthetic HTTP replies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import unittest

ROOT=Path(__file__).resolve().parents[2]

class Task15BrowserTest(unittest.TestCase):
    def test_real_problem_confirmation_questions_guidance_and_sources(self):
        node=shutil.which("node")
        browser=next((p for n in ("google-chrome","chromium","chromium-browser","msedge") if (p:=shutil.which(n))),None)
        if os.name=="nt" and not browser:
            p=Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
            if p.exists():browser=str(p)
        if not node or not browser:self.skipTest("NOT RUN: Node22+ and Chromium browser required")
        from integration.app import create_app
        from werkzeug.serving import make_server
        server=make_server("127.0.0.1",0,create_app(),threaded=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            # GitHub-hosted Chromium may occasionally fail to create DevToolsActivePort
            # before the test ever opens the app. Retry only that startup failure;
            # never retry real DOM/API assertion failures.
            for attempt in range(2):
                done=subprocess.run([node,str(ROOT/"frontend/tests/task15_browser_check.mjs"),f"http://127.0.0.1:{server.server_port}/",browser],cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
                trace=json.loads((ROOT/"instance/task15-browser-local/report.json").read_text())
                if done.returncode == 0 or "Browser debugger available" not in str(trace.get("error","")):
                    break
            self.assertEqual(done.returncode,0,done.stdout[-8000:]+done.stderr[-2000:])
            self.assertTrue(trace["passed"],trace.get("error"))
            self.assertEqual([len(c["steps"]) for c in trace["cases"]],[9,9])
            self.assertEqual(len(trace["edge_cases"]),5)
            self.assertTrue(all(c["passed"] for c in trace["edge_cases"]))
            self.assertEqual(trace["javascript_exceptions"],0)
            self.assertEqual(len(trace["screenshots"]),4)
        finally:server.shutdown();thread.join(timeout=5)
