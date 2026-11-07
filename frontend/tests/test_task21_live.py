"""Task 21: public homepage loads the real Action Plan 1.0 integration."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"


class Task21LiveTests(unittest.TestCase):
    def test_both_homepages_load_real_action_plan_before_bootstrap(self):
        for path,prefix in [(ROOT/"index.html","./frontend/js/"),(FRONTEND/"index.html","./js/")]:
            with self.subTest(path=path):
                html=path.read_text(encoding="utf-8")
                self.assertIn(prefix+"task21-live.js",html)
                self.assertLess(html.index("task21-live.js"),html.index("task8-home.js"))
                self.assertIn("sg-skyline.webp",html)
        script=(FRONTEND/"js/task8-home.js").read_text(encoding="utf-8")
        self.assertIn("SGNaviTask21.init(doc, win)",script)
    def test_real_api_and_fail_closed_sources(self):
        app=(FRONTEND/"js/task21-live.js").read_text(encoding="utf-8")
        config=(FRONTEND/"js/api-config.js").read_text(encoding="utf-8")
        for expected in ('"/api/action-plan"','action_plan_version:"1.0"',
                         'operation,...payload','request_id!==request.request_id',
                         "revisionOf(data.context,cryptoApi)",'digest(e.quote,cryptoApi)',
                         'safeContact(c)','e.kind==="statute"',
                         'localStorage' if False else 'credentials:"omit"',
                         'e.key==="Escape"',"task20-overlay","task20-first-grid"):
            self.assertIn(expected,app+config)
        for forbidden in ("localStorage", "sessionStorage", "innerHTML",
                          "admin@case.org.sg", "6277 5100"):
            self.assertNotIn(forbidden,app)
    def test_node_security_and_contract(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node unavailable")
        for args in ([node,"--check",str(FRONTEND/"js/task21-live.js")],
                     [node,"--test",str(FRONTEND/"tests/test_task21_live.cjs")]):
            with self.subTest(args=args):
                x=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,
                                 encoding="utf-8",errors="replace",timeout=35)
                self.assertEqual(x.returncode,0,x.stdout+x.stderr)


if __name__=="__main__":
    unittest.main()
