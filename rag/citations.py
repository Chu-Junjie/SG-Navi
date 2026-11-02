"""Validate returned Evidence and Action Card citations against current sources."""
from jsonschema.exceptions import ValidationError
from shared.validate_contracts import validate

from rag.repository import EvidenceRepository, RepositoryError
from rag.selection import EvidenceUnavailable, select_evidence


class CitationValidationError(ValueError):
    """Evidence or citations do not match the current authoritative source bundle."""


class CitationValidator:
    def __init__(self, repository=None):
        self.repository = repository or EvidenceRepository()

    def validate(self, case_type, rule_ids, evidence, citations, *, expected_source_version=None):
        """Raise CitationValidationError; success returns None and changes no data."""
        try:
            validate({"case_type": case_type, "rule_ids": rule_ids, "facts": {}}, "retrieval_request")
            if not isinstance(evidence, list) or not evidence:
                raise CitationValidationError("At least one Evidence record is required")
            bundle, blocked = self.repository.snapshot()
            if expected_source_version is not None and expected_source_version != bundle["source_version"]:
                raise CitationValidationError("Requested source_version is not current")
            canonical = {item["evidence_id"]: item for item in select_evidence(bundle, blocked, case_type, rule_ids)}
            seen = set()
            for item in evidence:
                validate(item, "evidence")
                evidence_id = item["evidence_id"]
                if evidence_id in seen:
                    raise CitationValidationError("Duplicate Evidence ID")
                seen.add(evidence_id)
                expected = canonical.get(evidence_id)
                if expected is None:
                    raise CitationValidationError("Evidence does not belong to the requested rules")
                if (any(item[key] != expected[key] for key in ("source_id", "url", "review_status", "source_version"))
                        or set(item["rule_ids"]) != set(expected["rule_ids"])):
                    raise CitationValidationError("Evidence metadata or rule mapping differs from the source bundle")
            if seen != set(canonical):
                raise CitationValidationError("Evidence does not cover every requested mapping")
            if (not isinstance(citations, list) or not citations
                    or any(not isinstance(value, str) or not value.strip() for value in citations)):
                raise CitationValidationError("Citations must be a nonempty Evidence ID list")
            if len(citations) != len(set(citations)) or set(citations) != seen:
                raise CitationValidationError("Citations must name every supplied Evidence ID exactly once")
        except (ValidationError, EvidenceUnavailable, RepositoryError, OSError, TypeError) as error:
            raise CitationValidationError("Evidence could not be verified against current sources") from error


def validate_citations(case_type, rule_ids, evidence, citations, *, expected_source_version=None, repository=None):
    return CitationValidator(repository).validate(
        case_type, rule_ids, evidence, citations, expected_source_version=expected_source_version
    )
