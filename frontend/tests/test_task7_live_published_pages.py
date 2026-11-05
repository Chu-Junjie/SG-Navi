"""Real Task 7 public-browser acceptance, opt-in only.

The named GitHub verification branch runs actual public Pages -> Render flow on
CI; this never fabricates data or substitutes local Flask. On other branches,
run manually with SG_NAVI_RUN_PUBLIC_PAGES=1. Save observed screenshots/logs.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
LIVE_BRANCH = "feat/task7-live-public-acceptance"
PUBLIC_URL = "https://chu-junjie.github.io/SG-Navi/"
API_URL = "https://sg-navi-api-junjie.onrender.com"

class Task7RealPublishedPagesTest(unittest.TestCase):
    def test_published_pages_rental_and_consumer(self):
        enabled = (os.getenv("SG_NAVI_RUN_PUBLIC_PAGES") == "1" or
                   os.getenv("GITHUB_HEAD_REF") == LIVE_BRANCH or
                   os.getenv("GITHUB_REF_NAME") == LIVE_BRANCH)
        if not enabled:
            self.skipTest("NOT RUN: opt-in external Pages test (set SG_NAVI_RUN_PUBLIC_PAGES=1)")
        node = shutil.which("node")
        chrome = next((p for n in (
            "google-chrome", "chromium", "chromium-browser", "microsoft-edge", "msedge"
        ) if (p := shutil.which(n))), None)
        if os.name == "nt" and not chrome:
            paths = [
                Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            ]
            chrome = next((str(p) for p in paths if p.is_file()), None)
        self.assertIsNotNone(node, "NOT RUN: Node.js 22+ unavailable; cannot count E2E PASS")
        self.assertIsNotNone(chrome, "NOT RUN: Chromium/Chrome/Edge unavailable; cannot count E2E PASS")
        version = subprocess.run(
            [node, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=10, check=False
        )
        try:
            major = int(version.stdout.strip().lstrip("v").split(".")[0])
        except (ValueError, IndexError):
            major = 0
        self.assertGreaterEqual(major, 22, "NOT RUN: Node.js 22+ needed for CDP WebSocket")

        env = os.environ.copy()
        env["SG_NAVI_EXPORT_SCREENSHOTS"] = "1"
        env["SG_NAVI_TEST_SHA"] = os.getenv("GITHUB_SHA", "manual-live-run")
        cmd = [node, str(FRONTEND / "tests" / "task7_public_pages_check.mjs"),
               PUBLIC_URL, chrome, API_URL]
        done = subprocess.run(
            cmd, cwd=ROOT, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=330, check=False
        )
        for line in done.stdout.splitlines():
            if (line.startswith("TASK7_PUBLIC_STEP ") or
                line.startswith("SGNAVI_PUBLIC_SHOT_") or
                line.startswith("SGNAVI_TASK7_PUBLIC_JSON=")):
                print(line, flush=True)
        if done.stderr:
            print("Browser stderr (last 2000):", done.stderr[-2000:], flush=True)
        reports = [line.split("SGNAVI_TASK7_PUBLIC_JSON=", 1)[1]
                   for line in done.stdout.splitlines()
                   if line.startswith("SGNAVI_TASK7_PUBLIC_JSON=")]
        self.assertTrue(reports, "No real browser trace; exit code " + str(done.returncode)
                        + "; tail " + done.stdout[-2800:] + done.stderr[-1000:])
        report = json.loads(reports[-1])
        self.assertEqual(report.get("scope"), "task7_public_pages_real_browser")
        self.assertEqual(report.get("pages_url"), PUBLIC_URL)
        self.assertEqual(report.get("api_origin"), API_URL)
        self.assertEqual(len(report.get("cases", [])), 2, json.dumps(report)[-4000:])
        errors = [{
            "case": case["case_type"],
            "failed_steps": [x for x in case.get("steps", []) if x.get("result") != "PASS"],
            "error": case.get("error"),
        } for case in report["cases"] if not case.get("passed")]
        self.assertFalse(errors, json.dumps(errors, indent=2)[-9000:])
        self.assertEqual([len(case["steps"]) for case in report["cases"]], [9, 9])
        self.assertEqual(len(report.get("screenshots", [])), 4, "Need four ACTUAL public JPEGs")
        self.assertEqual(report.get("javascript_exceptions"), 0)
        self.assertTrue(report.get("passed"), json.dumps(report)[-5000:])
        self.assertEqual(done.returncode, 0, done.stdout[-4500:] + done.stderr[-1000:])

if __name__ == "__main__":
    unittest.main()
