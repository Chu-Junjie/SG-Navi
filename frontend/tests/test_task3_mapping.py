"""Task 3 mapping structure checks — source of truth is Task 2 schemas."""
import json
import unittest
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
CARD_KEYS = {"case_summary", "potential_channels", "conditions", "steps",
             "document_checklist", "unresolved_questions", "citations"}

def read(path):
    return json.loads((FRONTEND / path).read_text(encoding="utf-8"))

class Task3MappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = read("mappings/task3_display_map.json")
        cls.script = (FRONTEND / "js/task3-mapping.js").read_text(encoding="utf-8")
        cls.page = (FRONTEND / "task3-mapping.html").read_text(encoding="utf-8")

    def test_exact_case_fields(self):
        for kind in ("rental_deposit", "consumer_complaint"):
            schema = read(f"schemas/{kind}_input.schema.json")
            self.assertEqual(set(self.mapping[kind]), set(schema["properties"]))
            self.assertTrue(all(self.mapping[kind].values()))
        self.assertEqual(set(self.mapping), {"rental_deposit", "consumer_complaint", "action_card"})

    def test_seven_action_card_fields(self):
        self.assertEqual(set(self.mapping["action_card"]), CARD_KEYS)
        self.assertEqual(set(read("schemas/action_card.schema.json")["required"]), CARD_KEYS)

    def test_no_frontend_legal_routing(self):
        self.assertIn('"/api/navigate"', self.script)
        self.assertIn("response.action_card", self.script)
        self.assertIn("Needs verification", self.script)
        self.assertIn('value===false', self.script)
        self.assertIn('value===null', self.script)
        self.assertIn('value==="unknown"', self.script)
        for forbidden in ("SCT_", "CEA_", "CASE_", "claim_amount_sgd", "tenancy_duration_months"):
            self.assertNotIn(forbidden, self.script)
        self.assertIn('src="./js/task3-mapping.js"', self.page)

    def test_fixture_is_contract_compatible(self):
        from shared.validate_contracts import validate
        for kind in ("rental_deposit", "consumer_complaint"):
            request = read(f"mocks/{kind}_request.json")
            self.assertEqual(request["case_type"], kind)
            validate(request, "navigate_request")

if __name__ == "__main__":
    unittest.main()
