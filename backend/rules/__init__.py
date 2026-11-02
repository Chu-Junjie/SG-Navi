"""Task 3 rule configuration validation. Never executes legal decisions."""
import json
from pathlib import Path
from rag.import_knowledge_base import load_knowledge_base

DIRECTORY = Path(__file__).resolve().parent
FILES = ("rental.json", "consumer.json", "boundary.json")
CASE_FILES = {
    "rental_deposit": "rental_deposit_input.schema.json",
    "consumer_complaint": "consumer_complaint_input.schema.json",
}
SCHEMA_DIR = DIRECTORY.parents[1] / "frontend" / "schemas"


class RuleConfigurationError(ValueError):
    """Reject unsafe or inconsistent rule configuration."""


def load_rule_configurations(directory=DIRECTORY, kb=None, schema_dir=SCHEMA_DIR):
    """Check all config links against the authoritative KB and existing input schemas.

    These are descriptive disabled rule skeletons, NOT live eligibility checks.
    """
    directory, schema_dir = Path(directory), Path(schema_dir)
    kb = load_knowledge_base() if kb is None else kb
    allowed_fields = {
        case: set(json.loads((schema_dir / name).read_text(encoding="utf-8"))["properties"])
        for case, name in CASE_FILES.items()
    }
    output = {}
    seen = set()
    for filename in FILES:
        doc = json.loads((directory / filename).read_text(encoding="utf-8"))
        category = filename.removesuffix(".json")
        if doc.get("category") != category or doc.get("source_version") != kb["source_version"]:
            raise RuleConfigurationError("category/source_version mismatch")
        if doc.get("unknown_policy") != "clarify_or_refer":
            raise RuleConfigurationError("unknown policy must preserve uncertain facts")
        checks = doc.get("checks")
        if not isinstance(checks, list) or not checks:
            raise RuleConfigurationError("checks must be a nonempty list")
        for check in checks:
            ident = check.get("check_id")
            cases = check.get("case_types")
            fields = check.get("input_fields")
            rid = check.get("rule_id")
            evidence = check.get("evidence_ids")
            if not isinstance(ident, str) or not ident.startswith(category + ".") or ident in seen:
                raise RuleConfigurationError("duplicate or invalid check_id")
            seen.add(ident)
            if not isinstance(cases, list) or not cases or len(cases) != len(set(cases)) or not set(cases) <= allowed_fields.keys():
                raise RuleConfigurationError("invalid case scope")
            if not isinstance(fields, list) or len(fields) != len(set(fields)) or any(not isinstance(f, str) for f in fields):
                raise RuleConfigurationError("invalid input fields")
            if any(not any(f in allowed_fields[case] for case in cases) for f in fields):
                raise RuleConfigurationError("field not declared for scoped case type")
            if check.get("runtime_enabled") is not False or check.get("threshold", "missing") is not None:
                raise RuleConfigurationError("Task 3 rules and thresholds must remain disabled")
            if not isinstance(check.get("notes"), str) or not check["notes"].strip():
                raise RuleConfigurationError("missing limitations")
            if rid is None:
                if check.get("mapping_status") != "unverified" or evidence != []:
                    raise RuleConfigurationError("unmapped checks cannot cite evidence")
                continue
            if check.get("mapping_status") != "linked":
                raise RuleConfigurationError("linked rule must declare linked status")
            source_rule = kb["rules"].get(rid)
            if source_rule is None or source_rule["runtime_enabled"] is not False:
                raise RuleConfigurationError("missing or unexpectedly active knowledge rule")
            if not set(cases) <= set(source_rule["case_types"]) or evidence != source_rule["evidence_ids"]:
                raise RuleConfigurationError("case scope or evidence ID mismatch")
            for eid in evidence:
                passage = kb["passages"].get(eid)
                source = kb["sources"].get(passage["source_id"]) if passage else None
                if not passage or not source or not passage.get("url") or passage["url"] != source["url"]:
                    raise RuleConfigurationError("Evidence ID cannot trace to source URL")
                if passage["source_version"] != kb["source_version"]:
                    raise RuleConfigurationError("evidence version mismatch")
                if passage["review_status"] != "verified" or source["status"] != "verified":
                    # Unverified evidence may remain in the KB but cannot be represented as a usable mapping.
                    raise RuleConfigurationError("unreviewed or quarantined evidence cannot be linked")
        output[category] = doc
    return output
