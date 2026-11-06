"""Task7 v1 compatibility and migrated Task20 root use the same approved API origin."""
import shutil
import subprocess
import unittest
from pathlib import Path

FRONTEND=Path(__file__).resolve().parents[1]

class Task7PublicConfigTests(unittest.TestCase):
    def test_public_frontend_references_config(self):
        home=(FRONTEND/"index.html").read_text(encoding="utf-8")
        form=(FRONTEND/"task5-flow.html").read_text(encoding="utf-8")
        flow=(FRONTEND/"js/task5-flow.js").read_text(encoding="utf-8")
        new=(FRONTEND/"js/task15-flow.js").read_text(encoding="utf-8")
        config=(FRONTEND/"js/api-config.js").read_text(encoding="utf-8")
        self.assertIn('src="./js/api-config.js"',home)
        self.assertIn('src="./js/api-config.js"',form)
        self.assertIn('SGNaviApiConfig.resolve("/api/navigate", window.location)',flow)
        self.assertIn('content="/api/health"',home)
        self.assertIn('SGNaviApiConfig.resolve(path,win.location)',new)
        self.assertIn('"/api/intake"',new)
        self.assertIn('"/api/guidance"',new)
        self.assertIn('const HTTPS_API_ORIGIN = "https://sg-navi-api-junjie.onrender.com";',config)
        self.assertNotIn("https://ACTUAL-",config)
        self.assertIn('"API not configured"',flow)

    @unittest.skipUnless(shutil.which("node"),"NOT RUN: Node.js unavailable")
    def test_api_configuration_node_safety_and_browser_script_syntax(self):
        for args in (
          ["node","--test","tests/test_api_config.cjs"],
          ["node","--check","tests/task7_public_pages_check.mjs"]
        ):
            with self.subTest(command=args):
                result=subprocess.run(args,cwd=FRONTEND,capture_output=True,text=True,
                        encoding="utf-8",errors="replace",timeout=22,check=False)
                self.assertEqual(result.returncode,0,(result.stdout or "")+(result.stderr or ""))

if __name__=="__main__":
    unittest.main()
