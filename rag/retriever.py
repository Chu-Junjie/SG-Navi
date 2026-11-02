"""Retrieve reviewed Evidence by Rule ID, without inferring legal rules from facts."""
import argparse
import json

from jsonschema.exceptions import ValidationError
from shared.validate_contracts import validate

from rag.repository import EvidenceRepository, RepositoryError
from rag.selection import EvidenceUnavailable, select_evidence


def _response(status, evidence=None):
    result = {"retrieval_status": status, "evidence": evidence or []}
    validate(result, "retrieval_response")
    return result


def retrieve_evidence(case_type, rule_ids, facts, *, repository=None):
    """Return FOUND, NO_RESULTS or ERROR in the existing two-field RAG envelope.

    All requested rules must be covered. Partial or rejected batches return no
    evidence. Facts are validated as an object and never mutated or used to guess
    applicability. Runtime rule activation remains the backend's responsibility.
    """
    try:
        validate({"case_type": case_type, "rule_ids": rule_ids, "facts": facts}, "retrieval_request")
    except (ValidationError, TypeError, ValueError):
        return _response("ERROR")
    if not rule_ids:
        return _response("NO_RESULTS")
    try:
        bundle, blocked = (repository or EvidenceRepository()).snapshot()
        evidence = select_evidence(bundle, blocked, case_type, rule_ids)
        return _response("FOUND", evidence)
    except EvidenceUnavailable:
        return _response("NO_RESULTS")
    except (RepositoryError, OSError, ValidationError):
        return _response("ERROR")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_type", choices=("rental_deposit", "consumer_complaint"))
    parser.add_argument("--rule-id", action="append", default=[])
    parser.add_argument("--directory", default=None)
    parser.add_argument("--state-file", default=None)
    args = parser.parse_args(argv)
    options = {key: value for key, value in {"directory": args.directory, "state_file": args.state_file}.items() if value is not None}
    try:
        result = retrieve_evidence(args.case_type, args.rule_id, {}, repository=EvidenceRepository(**options))
    except RepositoryError:
        result = _response("ERROR")
    print(json.dumps(result, indent=2))
    return {"FOUND": 0, "NO_RESULTS": 1, "ERROR": 2}[result["retrieval_status"]]


if __name__ == "__main__":
    raise SystemExit(main())
