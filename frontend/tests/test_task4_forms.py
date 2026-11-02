"""Task 4 schema-driven forms: structural and contract checks only.

End-to-end browser interaction is tested by browser_task4.py separately.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
CASE_TYPES = ("rental_deposit", "consumer_complaint")
RESPONSES = {
    "NEED_CLARIFICATION": "need_clarification_response.json",
    "SUPPORTED_PATH": "supported_path_response.json",
    "REFER_TO_OFFICIAL": "refer_to_official_response.json",
    "ERROR": "error_response.json",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Task4FormsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (FRONTEND / "js" / "task4-forms.js").read_text(encoding="utf-8")
        cls.css = (FRONTEND / "css" / "task4-forms.css").read_text(encoding="utf-8")
        cls.html = (FRONTEND / "forms.html").read_text(encoding="utf-8")
        cls.map = read_json(FRONTEND / "mappings" / "task3_display_map.json")

    def test_both_dynamic_forms_use_exact_existing_schema_fields(self):
        self.assertEqual(set(CASE_TYPES), set(self.map) - {"action_card"})
        for case_type in CASE_TYPES:
            schema = read_json(FRONTEND / "schemas" / f"{case_type}_input.schema.json")
            Draft202012Validator.check_schema(schema)
            self.assertEqual(set(schema["properties"]), set(self.map[case_type]))
            self.assertEqual(len(schema["properties"]), 9)
            self.assertFalse(schema["additionalProperties"])

    def test_seven_action_card_sections_derive_from_existing_schema(self):
        schema = read_json(FRONTEND / "schemas" / "action_card.schema.json")
        Draft202012Validator.check_schema(schema)
        self.assertEqual(len(schema["properties"]), 7)
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertEqual(set(schema["properties"]), set(self.map["action_card"]))
        self.assertIn("Object.keys(fields)", self.js)

    def test_all_four_responses_still_follow_shared_contract(self):
        from shared.validate_contracts import validate
        for status, name in RESPONSES.items():
            with self.subTest(status=status):
                record = read_json(FRONTEND / "mocks" / name)
                self.assertEqual(record["status"], status)
                validate(record, "navigate_response")

    def test_form_payload_has_no_extra_fields(self):
        self.assertIn('api_version: "1.0", case_type: kind, answers', self.js)
        self.assertIn('Object.entries(schema.properties)', self.js)
        self.assertIn('["unknown", "Unknown"]', self.js)
        self.assertIn('["null", "Not provided (null)"]', self.js)
        self.assertIn('["omit", "Skip field"]', self.js)
        self.assertIn('raw === "false"', self.js)
        self.assertIn('answers[key] = "unknown"', self.js)
        self.assertIn('answers[key] = null', self.js)
        self.assertIn("!dateIsReal(raw)", self.js)
        self.assertIn("Number.isFinite(number)", self.js)
        self.assertIn("errors[0].control.focus()", self.js)

    def test_mock_transport_no_live_backend_or_hardcoded_rules(self):
        self.assertIn("async function mockNavigate(", self.js)
        self.assertNotIn('fetch("/api/navigate"', self.js)
        for forbidden in ("SCT_", "CEA_", "CASE_", "tenancy_duration_months:",
                          "claim_amount_sgd:", "supplier_registered_in_sg:"):
            self.assertNotIn(forbidden, self.js)
        self.assertIn('url.hostname.endsWith(".invalid")', self.js)
        self.assertIn('sourceVersion.startsWith("mock")', self.js)
        self.assertIn("Needs verification", self.js)

    def test_page_accessibility_and_mobile_layout(self):
        self.assertIn('id="case-form"', self.html)
        self.assertIn('id="case-type"', self.html)
        self.assertIn('id="mock-status"', self.html)
        self.assertIn('id="card-sections"', self.html)
        self.assertIn('id="form-summary"', self.html)
        self.assertIn('role="status"', self.html)
        self.assertIn('src="./js/task4-forms.js"', self.html)
        self.assertIn('href="./css/task4-forms.css"', self.html)
        self.assertIn("@media(max-width:560px)", self.css)
        self.assertIn("focus-visible", self.css)


if __name__ == "__main__":
    unittest.main()
