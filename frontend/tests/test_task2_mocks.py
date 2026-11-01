"""Task 2 frontend schemas and synthetic fixtures; never validates legal truth."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

FRONTEND = Path(__file__).resolve().parents[1]
ROOT = FRONTEND.parent
sys.path.insert(0, str(ROOT))

RENTAL_FIELDS = {
    "dispute_with", "premises_type", "tenancy_duration_months",
    "claim_amount_sgd", "relevant_event_date", "respondent_in_singapore",
    "agency_agreement_signed", "resolution_attempted", "documents_available",
}
CONSUMER_FIELDS = {
    "purchase_type", "purchase_purpose", "supplier_registered_in_sg",
    "supplier_location", "problem_type", "purchase_date", "claim_amount_sgd",
    "resolution_attempted", "documents_available",
}
CARD_FIELDS = {
    "case_summary", "potential_channels", "conditions", "steps",
    "document_checklist", "unresolved_questions", "citations",
}


def read(path):
    return json.loads((FRONTEND / path).read_text(encoding="utf-8"))


class FrontendTask2Tests(unittest.TestCase):
    def test_schema_fields_are_exactly_the_assigned_ones(self):
        for case, expected in (("rental_deposit", RENTAL_FIELDS), ("consumer_complaint", CONSUMER_FIELDS)):
            schema = read(f"schemas/{case}_input.schema.json")
            self.assertEqual(set(schema["properties"]), expected)
            self.assertIs(schema["additionalProperties"], False)
            Draft202012Validator.check_schema(schema)
        card = read("schemas/action_card.schema.json")
        self.assertEqual(set(card["properties"]), CARD_FIELDS)
        self.assertEqual(set(card["required"]), CARD_FIELDS)
        self.assertIs(card["additionalProperties"], False)
        Draft202012Validator.check_schema(card)

    def test_two_input_fixtures_and_null_unknown_false_handling(self):
        for case in ("rental_deposit", "consumer_complaint"):
            payload = read(f"mocks/{case}_request.json")
            self.assertEqual(set(payload), {"api_version", "case_type", "answers"})
            self.assertEqual(payload["api_version"], "1.0")
            self.assertEqual(payload["case_type"], case)
            schema = read(f"schemas/{case}_input.schema.json")
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            validator.validate(payload["answers"])
            self.assertIn(None, payload["answers"].values())
            self.assertIn("unknown", payload["answers"].values())
            self.assertIn(False, payload["answers"].values())
            for field in schema["properties"]:
                for val in (None, "unknown"):
                    validator.validate({field: val})
            with self.assertRaises(ValidationError):
                validator.validate({"invented_extra_field": True})

    def test_four_status_fixtures_are_exact_wire_shapes(self):
        all_statuses = set()
        for name in ("need_clarification", "supported_path", "refer_to_official", "error"):
            record = read(f"mocks/{name}_response.json")
            self.assertEqual(set(record), {"api_version", "rule_version", "source_version", "status", "questions", "action_card", "evidence", "warnings"})
            all_statuses.add(record["status"])
            if record["status"] == "NEED_CLARIFICATION":
                self.assertTrue(record["questions"])
                self.assertIsNone(record["action_card"])
            if record["status"] == "SUPPORTED_PATH":
                self.assertFalse(record["questions"])
                self.assertTrue(record["evidence"])
                self.assertTrue(all(e["review_status"] == "verified" for e in record["evidence"]))
                card = record["action_card"]
                self.assertEqual(set(card), CARD_FIELDS)
                Draft202012Validator(read("schemas/action_card.schema.json")).validate(card)
                self.assertTrue(all(c in {e["evidence_id"] for e in record["evidence"]} for c in card["citations"]))
                self.assertTrue(all(e["url"].startswith("https://example.invalid/") for e in record["evidence"]))
            if record["status"] in ("REFER_TO_OFFICIAL", "ERROR"):
                self.assertTrue(record["warnings"])
                self.assertFalse(record["questions"])
        self.assertEqual(all_statuses, {"NEED_CLARIFICATION", "SUPPORTED_PATH", "REFER_TO_OFFICIAL", "ERROR"})

    def test_shared_contract_if_available(self):
        try:
            from shared.validate_contracts import validate
        except ModuleNotFoundError:
            self.skipTest("Canonical shared contract not yet merged into main")
        for case in ("rental_deposit", "consumer_complaint"):
            validate(read(f"mocks/{case}_request.json"), "navigate_request")
        for name in ("need_clarification", "supported_path", "refer_to_official", "error"):
            validate(read(f"mocks/{name}_response.json"), "navigate_response")


if __name__ == "__main__":
    unittest.main()
