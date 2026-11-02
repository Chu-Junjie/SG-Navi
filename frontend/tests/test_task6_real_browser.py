"""Task 6 FE-01–08: run the existing real Flask integration origin in a Chromium browser.

Skip with a visible reason if a suitable local browser/Node runtime isn't installed.
The underlying Node script captures real POST /api/navigate; it does not mock responses.
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

class RealBrowserFE01to08(unittest.TestCase):
    def test_fe_01_to_08_chromium(self):
        node = shutil.which("node")
        browser = next((v for x in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "msedge")
                        if (v := shutil.which(x))), None)
        if sys.platform == "win32" and not browser:
            locations = (
                Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            )
            browser = next((str(x) for x in locations if x.is_file()), None)
        if not node or not browser:
            self.skipTest("NOT RUN: Node.js or Chromium/Chrome/Edge executable not found")
        version = subprocess.run([node, "--version"],capture_output=True,text=True,
                                 encoding="utf-8",errors="replace",timeout=8,check=False)
        try: major = int(version.stdout.strip().lstrip("v").split(".")[0])
        except (ValueError, IndexError): major = 0
        if major < 22:
            self.skipTest("NOT RUN: test runner needs Node.js 22+ global WebSocket")
        from integration.app import create_app
        from werkzeug.serving import make_server
        backend = make_server("127.0.0.1", 0, create_app(), threaded=True)
        worker = threading.Thread(target=backend.serve_forever,daemon=True)
        worker.start()
        try:
            url = "http://127.0.0.1:" + str(backend.server_port)
            result = subprocess.run(
                [node, str(FRONTEND / "tests" / "task6_fe_browser.mjs"), url, browser],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=135, check=False
            )
            data = None
            for pos in (i for i,c in enumerate(result.stdout) if c=="{"):
                try:
                    v = json.loads(result.stdout[pos:])
                    if v.get("scope")=="task6_fe_01_08_real_chromium":
                        data=v;break
                except (ValueError,AttributeError):pass
            diag=(result.stdout or "")[-12000:]+"\n"+(result.stderr or "")[-4000:]
            self.assertIsNotNone(data,"Browser did not return JSON results:\n"+diag)
            self.assertEqual(len(data["checks"]),8,diag)
            failures=[x for x in data["checks"] if x["result"]!="PASS"]
            self.assertEqual(result.returncode,0,"FE browser failures:\n"+json.dumps(failures,indent=2)+"\n"+diag)
            self.assertFalse(failures,diag)
            self.assertEqual(data.get("javascript_exceptions"),0,diag)
        finally:
            backend.shutdown()
            backend.server_close()
            worker.join(timeout=4)

if __name__=="__main__":
    unittest.main()
