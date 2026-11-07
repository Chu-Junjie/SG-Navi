"""Task21 real local browser -> real Flask Action Plan 1.0; no intercepted replies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import unittest

ROOT=Path(__file__).resolve().parents[2]


class Task21BrowserTest(unittest.TestCase):
    def test_real_action_first_homepage_desktop_mobile_and_sources(self):
        node=shutil.which("node")
        browser=next((p for n in ("google-chrome","chromium","chromium-browser","msedge")
                      if (p:=shutil.which(n))),None)
        if os.name=="nt" and not browser:
            candidate=Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
            if candidate.exists():browser=str(candidate)
        if not node or not browser:self.skipTest("NOT RUN: Node.js and Chromium/Edge required")
        from integration.app import create_app
        from werkzeug.serving import make_server
        server=make_server("127.0.0.1",0,create_app(),threaded=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            process=subprocess.run(
                [node,str(ROOT/"frontend/tests/task21_browser_check.mjs"),
                 f"http://127.0.0.1:{server.server_port}/",browser],
                cwd=ROOT,capture_output=True,text=True,
                encoding="utf-8",errors="replace",timeout=300
            )
            report=json.loads((ROOT/"instance/task21-browser-local/report.json").read_text())
            self.assertEqual(process.returncode,0,report.get("errors") or process.stdout[-3000:]+process.stderr[-1500:])
            self.assertTrue(report["passed"],report.get("errors"))
            self.assertEqual(len(report["cases"]),2)
            self.assertTrue(all(c["passed"] for c in report["cases"]))
            self.assertEqual(len(report["screenshots"]),4)
        finally:server.shutdown();thread.join(timeout=5)


if __name__=="__main__":
    unittest.main()
