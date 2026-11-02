"""Task 4 tests for schema-driven mock UI and API contract fixtures."""
import json
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
ROOT = FRONTEND.parent
SECTIONS = {"case_summary", "potential_channels", "conditions", "steps",
            "document_checklist", "unresolved_questions", "citations"}


def read(relative):
    return json.loads((FRONTEND / relative).read_text(encoding="utf-8"))


class Task4FormTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (FRONTEND / "js" / "task4-forms.js").read_text(encoding="utf-8")
        cls.html = (FRONTEND / "task4-forms.html").read_text(encoding="utf-8")

    def test_two_cases_use_existing_contract_fields(self):
        mapping = read("mappings/task3_display_map.json")
        for name in ("rental_deposit", "consumer_complaint"):
            schema = read("schemas/" + name + "_input.schema.json")
            self.assertEqual(set(schema["properties"]), set(mapping[name]))
            self.assertFalse(schema.get("required"))
            self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(mapping["action_card"]), SECTIONS)

    def test_all_four_mock_statuses_validate_against_shared_contract(self):
        from shared.validate_contracts import validate
        names = ("need_clarification", "supported_path", "refer_to_official", "error")
        states = set()
        for name in names:
            response = read("mocks/" + name + "_response.json")
            validate(response, "navigate_response")
            states.add(response["status"])
        self.assertEqual(states, {"NEED_CLARIFICATION", "SUPPORTED_PATH",
                                  "REFER_TO_OFFICIAL", "ERROR"})
        self.assertEqual(set(read("schemas/action_card.schema.json")["required"]), SECTIONS)

    def test_schema_generated_controls_and_answer_editing(self):
        self.assertIn('for(const [key,definition] of Object.entries(properties))', self.js)
        self.assertIn('select.addEventListener("change"', self.js)
        self.assertIn('details.addEventListener("input"', self.js)
        self.assertIn("answers[caseType]=next", self.js)
        self.assertIn('raw==="__unknown__"', self.js)
        self.assertIn('raw==="__null__"', self.js)
        self.assertIn('raw==="true"', self.js)
        self.assertIn('n<lower', self.js)
        self.assertIn('d.toISOString().slice(0,10)!==raw', self.js)
        self.assertIn('if(!collect(true))', self.js)

    def test_mock_api_and_evidence_guard(self):
        self.assertIn('async function mockNavigate', self.js)
        self.assertIn('JSON.stringify(request,null,2)', self.js)
        self.assertIn('response?.action_card?.[key]', self.js)
        self.assertIn("source_version.startsWith(\"mock\")", self.js)
        self.assertIn('url.hostname.endsWith(".invalid")', self.js)
        self.assertIn("Needs verification", self.js)
        for token in ("SCT_", "CEA_", "CASE-", "claim_amount_sgd",
                      "tenancy_duration_months", "https://www."):
            self.assertNotIn(token, self.js)

    def test_accessible_mobile_page_mounts_controls(self):
        for control in ("case-type", "mock-status", "dynamic-fields",
                        "submit", "validation", "card", "request-preview"):
            self.assertIn('id="' + control + '"', self.html)
        self.assertIn("@media(max-width:750px)", self.html)
        self.assertIn("aria-live", self.html)
        self.assertIn('src="./js/task4-forms.js"', self.html)


if __name__ == "__main__":
    unittest.main()
