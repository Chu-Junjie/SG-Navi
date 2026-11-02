"""Task 5: read-only Backend -> RAG bridge, with explicit fail-closed checks.

A FOUND retrieval means that *source text exists*, not that a legal route applies.
No Task 3 rules are enabled; normal API responses never assert SUPPORTED_PATH.
"""
import logging
from urllib.parse import urlsplit

from jsonschema.exceptions import ValidationError

from rag.citations import CitationValidationError, validate_citations
from rag.repository import EvidenceRepository
from rag.retriever import retrieve_evidence
from shared.validate_contracts import validate

LOGGER = logging.getLogger(__name__)

# These are *research topics* drawn from checked Task 3 mappings, not activated
# eligibility rules. Their selection never depends on numeric/temporal thresholds.
TOPIC_CHECKS = {
    "rental_deposit": ("rental.premises_scope", "rental.claim_amount"),
    "consumer_complaint": ("consumer.personal_purpose", "consumer.supplier_registration"),
}


def rule_ids_for_context(case_type, configs):
    """Use only the existing disabled, linked checks; never invent a rule ID."""
    group = "rental" if case_type == "rental_deposit" else "consumer"
    candidates = {entry["check_id"]: entry for entry in configs[group]["checks"]}
    rule_ids = []
    for check_id in TOPIC_CHECKS[case_type]:
        check = candidates.get(check_id)
        if (not check or check["mapping_status"] != "linked"
                or check["runtime_enabled"] is not False or check["threshold"] is not None
                or not isinstance(check["rule_id"], str) or not check["evidence_ids"]):
            raise ValueError("Task 3 source mapping is unavailable or enabled unexpectedly")
        rule_ids.append(check["rule_id"])
    if len(set(rule_ids)) != len(rule_ids):
        raise ValueError("Duplicate rule IDs selected")
    validate({"case_type": case_type, "rule_ids": rule_ids, "facts": {}}, "retrieval_request")
    return rule_ids


def retrieve_checked(case_type, rule_ids, facts, *, expected_version):
    """Return (status, evidence) with no partial/unvalidated source records.

    Status is FOUND/NO_RESULTS/INVALID/ERROR. INVALID means a found response did
    not pass the authoritative citation or schema checks. Responses are copied
    directly from the RAG interface only after verification against *current*
    repository data and quarantine state.
    """
    try:
        repository = EvidenceRepository()
        result = retrieve_evidence(case_type, rule_ids, facts, repository=repository)
        validate(result, "retrieval_response")
        if set(result) != {"retrieval_status", "evidence"}:
            raise ValueError("RAG envelope fields differ from the contract")
        status, records = result["retrieval_status"], result["evidence"]
        if status not in {"FOUND", "NO_RESULTS", "ERROR"}:
            raise ValueError("Unexpected RAG status")
        if status in {"NO_RESULTS", "ERROR"}:
            if records:
                raise ValueError("Unsuccessful retrieval returned evidence")
            return status, []
        if not records or any(item["source_version"] != expected_version
                              or item["review_status"] != "verified" for item in records):
            return "INVALID", []
        validate_citations(
            case_type, rule_ids, records,
            [item["evidence_id"] for item in records],
            expected_source_version=expected_version,
            repository=repository,
        )
        return "FOUND", records
    except CitationValidationError:
        LOGGER.warning("Retrieved Evidence failed authoritative citation validation", exc_info=True)
        return "INVALID", []
    except (ValidationError, ValueError, TypeError, KeyError, OSError):
        LOGGER.warning("RAG result was malformed or could not be validated", exc_info=True)
        return "ERROR", []
    except Exception:
        LOGGER.exception("RAG retrieval service raised an unexpected exception")
        return "ERROR", []


def referral_source_context(records, *, expected_version):
    """Expose only the *entire* validated source list as research context.

    This is a second presentation guard after retrieve_checked() performed
    contract, canonical-source and quarantine checks. It cannot assert that a
    claimant is eligible and cannot create an Action Card or citations.
    """
    if not isinstance(records, list) or not records:
        return []
    output = []
    for item in records:
        if not isinstance(item, dict):
            return []
        try:
            validate(item, "evidence")
            url = urlsplit(item["url"])
            host = (url.hostname or "").lower()
            if (url.scheme != "https" or not host or url.username or url.password
                    or host in {"localhost", "127.0.0.1", "::1"}
                    or host.endswith((".invalid", ".test", ".example", ".localhost"))
                    or item["review_status"] != "verified"
                    or item["source_version"] != expected_version):
                return []
        except (TypeError, ValueError, KeyError, ValidationError):
            return []
        output.append(dict(item))
    if len({item["evidence_id"] for item in output}) != len(output):
        return []
    return output
