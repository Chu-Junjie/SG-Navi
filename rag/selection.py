"""Exact evidence selection shared by retrieval and authoritative citation checks."""
from copy import deepcopy

from rag.import_knowledge_base import api_evidence


class EvidenceUnavailable(ValueError):
    """At least one requested rule lacks complete usable source evidence."""


def select_evidence(bundle, blocked, case_type, rule_ids):
    if not rule_ids:
        raise EvidenceUnavailable("No rule IDs requested")
    selected = {}
    for rule_id in rule_ids:
        rule = bundle["rules"].get(rule_id)
        if not rule or case_type not in rule["case_types"] or rule["review_status"] != "verified":
            raise EvidenceUnavailable("Requested rule has no verified mapping for this case")
        for evidence_id in rule["evidence_ids"]:
            passage = bundle["passages"].get(evidence_id)
            source = bundle["sources"].get(passage["source_id"]) if passage else None
            if (not passage or not source or passage["source_id"] in blocked
                    or case_type not in passage["case_types"]
                    or passage["review_status"] != "verified" or source["status"] != "verified"
                    or passage["source_version"] != bundle["source_version"]
                    or source["version"] != bundle["source_version"]
                    or passage["url"] != source["url"] or rule_id not in passage["rule_ids"]):
                raise EvidenceUnavailable("Requested rule has unavailable evidence")
            if evidence_id not in selected:
                selected[evidence_id] = deepcopy(api_evidence(passage))
                selected[evidence_id]["rule_ids"] = []
            selected[evidence_id]["rule_ids"].append(rule_id)
    return list(selected.values())
