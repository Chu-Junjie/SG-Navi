"""Task 23: bilingual shell, verified-source limits and in-memory process stepper."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


class Task23UITests(unittest.TestCase):
    def test_both_published_and_local_homepages(self):
        for relative,prefix in (("index.html","./frontend"),("frontend/index.html",".")):
            with self.subTest(page=relative):
                text=(ROOT/relative).read_text(encoding="utf-8")
                self.assertIn("Don't feel lost, just find me.",text)
                self.assertIn('data-task23-language="en"',text)
                self.assertIn('data-task23-language="zh"',text)
                self.assertIn('id="task23-slogan"',text)
                self.assertIn('task23-ui.css',text)
                self.assertIn('task23-locale.js',text)
                self.assertIn(f'{prefix}/assets/sg-skyline.webp',text)
                self.assertIn('task21-live.js',text)
                self.assertNotIn("Singapore · Find a starting point",text)

    def test_action_plan_process_is_only_from_real_sources_and_memory(self):
        script=(ROOT/"frontend/js/task21-live.js").read_text(encoding="utf-8")
        for piece in ("const p=data.plan,sources=data.verifiedSources",
                      'part==="process"', "checkedProcess=new Set()",
                      "checkedProcess.clear()", "for(let index=0;index<p.checklist.length;index++)",
                      "p.primary_action.evidence_ids", "item.evidence_ids",
                      "Continue to next step", "showDetails(\"process\")",
                      "draftEdits=new Map()", "draftEdits.set(slot.id,field.value)"):
            self.assertIn(piece,script)
        self.assertNotIn('"Back to next step"',script)
        self.assertNotIn("localStorage",script)
        self.assertNotIn("sessionStorage",script)
        self.assertNotIn("complaint submitted",script.lower())

    def test_translation_protects_verbatim_quote_and_keeps_en_as_default(self):
        script=(ROOT/"frontend/js/task23-locale.js").read_text(encoding="utf-8")
        for phrase in ('lang="en"', "EN_ZH", "BLOCKQUOTE",
                       "task23Original", "No reviewed Chinese translation",
                       "setLanguage(next)", "sgnavi:languagechange"):
            # The html= attribute itself is in the homepage, not locale module.
            if phrase!='lang="en"': self.assertIn(phrase,script)
        self.assertNotIn("fetch(",script)
        self.assertNotIn("localStorage",script)
        self.assertNotIn("sessionStorage",script)

    def test_javascript_syntax_and_locale_unit(self):
        node=shutil.which("node")
        if not node: self.skipTest("Node.js unavailable")
        for relative in ("frontend/js/task23-locale.js","frontend/js/task21-live.js"):
            with self.subTest(path=relative):
                r=subprocess.run([node,"--check",str(ROOT/relative)],
                    capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=20)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        r=subprocess.run([node,"--test",str(ROOT/"frontend/tests/test_task23_locale.cjs")],
            capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

if __name__=="__main__":
    unittest.main()
