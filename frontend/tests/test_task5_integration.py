"""Task 5 integration: actual local HTTP to Flask through frontend-only proxy."""
from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from frontend.dev_proxy import FrontendHandler
from backend.app import create_app
from werkzeug.serving import make_server

FRONTEND = ROOT / "frontend"


class Task5IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = make_server("127.0.0.1", 0, create_app(), threaded=True)
        cls.backend_thread = threading.Thread(target=cls.backend.serve_forever, daemon=True)
        cls.backend_thread.start()
        backend_url = "http://127.0.0.1:" + str(cls.backend.server_port)
        handler = type("IsolatedHandler", (FrontendHandler,), {"backend_url": backend_url})
        cls.proxy = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.proxy_thread = threading.Thread(target=cls.proxy.serve_forever, daemon=True)
        cls.proxy_thread.start()
        cls.url = "http://127.0.0.1:" + str(cls.proxy.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.proxy.shutdown()
        cls.backend.shutdown()
        cls.proxy.server_close()
        cls.backend.server_close()
        cls.proxy_thread.join(timeout=3)
        cls.backend_thread.join(timeout=3)

    def request(self, case_type, answers):
        payload = {"api_version": "1.0", "case_type": case_type, "answers": answers}
        data = json.dumps(payload).encode("utf-8")
        req = Request(self.url + "/api/navigate", data=data, method="POST",
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=6) as res:
            self.assertEqual(res.status, 200)
            self.assertIn("application/json", res.headers["Content-Type"])
            return json.loads(res.read())

    def test_rental_real_http_clarification_then_referral(self):
        from shared.validate_contracts import validate
        missing = self.request("rental_deposit", {})
        validate(missing, "navigate_response")
        self.assertEqual(missing["status"], "NEED_CLARIFICATION")
        ids = {q["id"] for q in missing["questions"]}
        self.assertTrue({"dispute_with", "premises_type", "claim_amount_sgd"} <= ids)
        supplied = {"dispute_with": "landlord", "premises_type": "residential",
                    "claim_amount_sgd": 1200, "documents_available": "unknown"}
        final = self.request("rental_deposit", supplied)
        validate(final, "navigate_response")
        self.assertEqual(final["status"], "REFER_TO_OFFICIAL")
        self.assertIsNone(final["action_card"])
        self.assertEqual(final["evidence"], [])
        edit = self.request("rental_deposit", dict(supplied, claim_amount_sgd=800))
        self.assertEqual(edit["status"], "REFER_TO_OFFICIAL")

    def test_consumer_real_http_followup_edit_and_boundary(self):
        from shared.validate_contracts import validate
        missing = self.request("consumer_complaint", {})
        validate(missing, "navigate_response")
        self.assertEqual(missing["status"], "NEED_CLARIFICATION")
        ids = {q["id"] for q in missing["questions"]}
        self.assertTrue({"purchase_type", "purchase_purpose",
                         "supplier_registered_in_sg", "claim_amount_sgd"} <= ids)
        supplied = {"purchase_type": "goods", "purchase_purpose": "personal",
                    "supplier_registered_in_sg": True, "claim_amount_sgd": 75,
                    "resolution_attempted": False}
        final = self.request("consumer_complaint", supplied)
        validate(final, "navigate_response")
        self.assertEqual(final["status"], "REFER_TO_OFFICIAL")
        boundary = self.request("consumer_complaint", dict(supplied, purchase_purpose="business"))
        self.assertEqual(boundary["status"], "REFER_TO_OFFICIAL")
        self.assertTrue(boundary["warnings"])

    def test_proxy_serves_page_and_schema(self):
        for path, expected in (
            ("/task5-flow.html", b"/js/task5-flow.js"),
            ("/js/task5-flow.js", b'"/api/navigate"'),
            ("/schemas/rental_deposit_input.schema.json", b"claim_amount_sgd"),
        ):
            with self.subTest(path=path):
                with urlopen(self.url + path, timeout=6) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(expected, resp.read())

    def test_invalid_post_is_rejected_not_forwarded(self):
        req = Request(self.url + "/api/navigate", data=b"not json",
                      headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(HTTPError) as error:
            urlopen(req, timeout=6)
        self.assertEqual(error.exception.code, 400)

    def test_bad_legal_evidence_and_no_hardcoded_channels(self):
        script = (FRONTEND / "js/task5-flow.js").read_text(encoding="utf-8")
        page = (FRONTEND / "task5-flow.html").read_text(encoding="utf-8")
        self.assertIn('fetch("/api/navigate"', script)
        self.assertIn('response.action_card.citations.map(id => map.get(id))', script)
        self.assertIn('entry.review_status !== "verified"', script)
        self.assertIn('url.hostname.endsWith(".invalid")', script)
        self.assertIn('response.source_version.startsWith("mock")', script)
        self.assertIn('link.rel = "noopener noreferrer"', script)
        self.assertIn("function focusField", script)
        self.assertIn('state.drafts[kind]', script)
        self.assertIn("Needs verification", script)
        for forbidden in ("SCT_", "CEA_", "CASE-", "https://www.",
                          "tenancy_duration_months", "claim_amount_sgd"):
            self.assertNotIn(forbidden, script)
        self.assertIn('id="edit-answers"', page)
        self.assertIn('id="questions"', page)
        self.assertIn('id="card"', page)


if __name__ == "__main__":
    unittest.main()
