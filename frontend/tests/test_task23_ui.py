"""Task 23: bilingual shell, verified-source limits and in-memory process stepper."""
import ast
import json
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
                self.assertIn('id="problem-language-help" lang="zh-Hans" hidden',text)
                self.assertIn('placeholder="For example: My landlord',text)
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
        for phrase in ('lang="en"', "EN_ZH", 'setAttribute("lang","en")',
                       "task23Original", "No reviewed Chinese translation",
                       "setLanguage(next)", "sgnavi:languagechange"):
            # The html= attribute itself is in the homepage, not locale module.
            if phrase!='lang="en"': self.assertIn(phrase,script)
        self.assertIn("task23-dialog-translation-notice",script)
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

    def test_all_current_action_plan_question_copy_has_local_chinese(self):
        node=shutil.which("node")
        if not node: self.skipTest("Node.js unavailable")
        phrases=set()
        for relative,constructor in (("backend/scenario_understanding.py","_question"),
                                     ("backend/action_plan_service.py","_choice")):
            tree=ast.parse((ROOT/relative).read_text(encoding="utf-8"))
            for call in ast.walk(tree):
                if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!=constructor:
                    continue
                _,prompt,reason,options=map(ast.literal_eval,call.args)
                phrases.update((prompt,reason,*(label for _,label in options)))
        self.assertIn("Is this about goods or a service?",phrases)
        script='''const fs=require("node:fs"),locale=require("./frontend/js/task23-locale.js");
            console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,"utf8")).filter(text=>
              !/\\p{Script=Han}/u.test(locale.chineseCopy(text)||""))));'''
        run=subprocess.run([node,"-e",script],cwd=ROOT,input=json.dumps(sorted(phrases)),
                           capture_output=True,text=True,encoding="utf-8",timeout=20,check=True)
        self.assertEqual(json.loads(run.stdout),[])

    def test_corrected_selectors_preserve_backend_chinese_summary_coverage(self):
        node=shutil.which("node")
        if not node: self.skipTest("Node.js unavailable")
        from backend.scenario_understanding import interpret_scenario
        from backend.action_plan_service import process_action_plan
        from backend.task24_bilingual import preview_zh_hans
        contexts=[]
        for description in ("My landlord kept my rental deposit and I want a refund.",
                            "The restaurant charged me extra and refuses to refund it."):
            original=interpret_scenario(description)["context"]
            for goal in ("complain","seek_refund","prepare_claim","understand_options","contact_provider"):
                contexts.append({**original,"goal":goal})
        contexts.append({**contexts[0],"issue_subtype":"deposit_deduction"})
        contexts.append({**contexts[-2],"issue_subtype":"goods_dispute"})
        contexts.append({**contexts[0],"case_type":"consumer_complaint",
                         "issue_subtype":"unspecified","facts":{}})
        script='''const fs=require("node:fs"),ui=require("./frontend/js/task21-live.js");
            console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,"utf8")).map(context=>
              ({...context,summary:ui.summaryForContext(context)}))));'''
        run=subprocess.run([node,"-e",script],cwd=ROOT,input=json.dumps(contexts),
                           capture_output=True,text=True,encoding="utf-8",timeout=20,check=True)
        corrected=json.loads(run.stdout)
        for before,context in zip(contexts,corrected):
            with self.subTest(case=context["case_type"],goal=context["goal"],subtype=context["issue_subtype"]):
                self.assertEqual(context["facts"],before["facts"])
                response=process_action_plan({"action_plan_version":"1.0",
                    "request_id":"task23-corrected-selectors","operation":"plan",
                    "confirmed":True,"context":context})
                overlay=preview_zh_hans(response)
                self.assertEqual(overlay["missing_paths"],[])
                self.assertIsNotNone(overlay["display"]["context_summary"])

if __name__=="__main__":
    unittest.main()
