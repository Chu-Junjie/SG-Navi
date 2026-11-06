"""Bounded, deterministic query ranking over reviewed evidence; never eligibility.

Input is the output of backend.query_integration.prepare_confirmed_query.
The additive query contract is separate from the unchanged six-field v1 API.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from rag.citations import CitationValidationError, validate_citations
from rag.query_topics import ALIASES, CORE, TOPICS
from rag.repository import EvidenceRepository, RepositoryError
from rag.retriever import retrieve_evidence

ROOT = Path(__file__).resolve().parents[1]
QUERY_RAG_VERSION = "1.0"
MAX_RESULTS = 8  # Matches the backend adapter's maximum proposed rule count.
TOKEN = re.compile(r"[a-z]+")
SAFE_QUERY = re.compile(r"[a-zA-Z0-9 ,.!?'-]{1,300}")


def _tokens(value):
    return {ALIASES.get(word, word) for word in TOKEN.findall(value.lower())}


@lru_cache(maxsize=1)
def _validators():
    def deny_remote(uri):
        raise NoSuchResource(ref=uri)

    contract = json.loads((ROOT / "shared/query_retrieval_contract.json").read_text(encoding="utf-8"))
    registry = Registry(retrieve=deny_remote)
    schemas = [(contract["$id"], contract)]
    for case in ("rental_deposit", "consumer_complaint"):
        schema = json.loads((ROOT / f"frontend/schemas/{case}_input.schema.json").read_text(encoding="utf-8"))
        schemas.append((f"https://sg-navi.invalid/frontend/schemas/{case}_input.schema.json", schema))
    evidence = json.loads((ROOT / "shared/schemas/evidence_schema.json").read_text(encoding="utf-8"))
    schemas.append(("https://sg-navi.invalid/shared/schemas/evidence_schema.json", evidence))
    for uri, schema in schemas:
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(uri, Resource.from_contents(schema))
    return {name: Draft202012Validator({"$ref": contract["$id"] + "#/$defs/" + name},
                                      registry=registry, format_checker=FormatChecker())
            for name in ("prepared", "result")}


def validate_query_result(result):
    """Validate the additive internal query response without network resolution."""
    _validators()["result"].validate(result)


def _result(status, code, *, version=None, rules=None, evidence=None, reasons=None, missing=None):
    evidence = evidence or []
    result = {"query_rag_version": QUERY_RAG_VERSION, "context_only": True,
              "retrieval_status": status, "diagnostic_code": code,
              "source_version": version, "proposed_rule_ids": rules or [],
              "ranked_evidence_ids": [e["evidence_id"] for e in evidence],
              "evidence": evidence, "match_reasons": reasons or [],
              "missing_context_fields": missing or []}
    validate_query_result(result)
    return result


def _known(value):
    return value is not None and not (isinstance(value, str) and value.strip().lower() in ("", "unknown"))


def _normal(value):
    return value.strip().lower() if isinstance(value, str) else value


def _context(case, facts, terms):
    """Project boundaries only; optional query cannot create confirmed facts."""
    if case == "rental_deposit":
        premises = _normal(facts.get("premises_type"))
        if _known(premises) and premises != "residential":
            return None, "OUT_OF_SCOPE", []
        party = _normal(facts.get("dispute_with"))
        if party == "landlord":
            return "landlord", None, [k for k in ("premises_type",) if not _known(facts.get(k))]
        if party in ("agent", "agency", "property_agent"):
            conduct = {"conduct", "misconduct", "unlicensed", "complaint", "complain", "privacy", "anonymous", "anonymity", "disclosure", "chronology"}
            agreement = {"agreement", "contract", "commission", "mediation", "arbitration", "independent", "centre"}
            if terms & conduct and terms & agreement:
                return None, "INSUFFICIENT_CONTEXT", ["query"]
            if terms & conduct:
                return "agent_conduct", None, []
            if terms & agreement or _known(facts.get("agency_agreement_signed")):
                return "agent_contract", None, ["agency_agreement_signed"] if not _known(facts.get("agency_agreement_signed")) else []
            return None, "INSUFFICIENT_CONTEXT", ["query"]
        return None, "INSUFFICIENT_CONTEXT", ["dispute_with"]
    purpose = _normal(facts.get("purchase_purpose"))
    location = _normal(facts.get("supplier_location"))
    if (purpose == "business" or facts.get("supplier_registered_in_sg") is False
            or _known(location) and location not in ("singapore", "sg")):
        return None, "OUT_OF_SCOPE", []
    missing = [k for k in ("purchase_purpose", "purchase_type") if not _known(facts.get(k))]
    if missing:
        return None, "INSUFFICIENT_CONTEXT", missing
    if purpose != "personal" or _normal(facts.get("purchase_type")) not in ("goods", "services", "service"):
        return None, "OUT_OF_SCOPE", []
    return "consumer", None, ["supplier_registered_in_sg"] if not _known(facts.get("supplier_registered_in_sg")) else []


def retrieve_query_evidence(prepared, *, expected_source_version, mandatory_rule_ids=None,
                            max_results=8, repository=None):
    """Rank research context, then enforce complete canonical rule citations.

    No model, remote query, persistence or input logging. Limits count evidence
    and rules; a complete mapped group is never truncated. Invalid/stale/mixed
    evidence returns an empty response, never a partial verified result.
    """
    try:
        _validators()["prepared"].validate(prepared)
        if (not isinstance(expected_source_version, str) or not 1 <= len(expected_source_version) <= 128
                or type(max_results) is not int or not 1 <= max_results <= MAX_RESULTS):
            raise ValueError("Invalid version or result bound")
        mandatory = [] if mandatory_rule_ids is None else mandatory_rule_ids
        if (not isinstance(mandatory, list) or len(mandatory) > MAX_RESULTS
                or any(not isinstance(r, str) or not r.strip() for r in mandatory)
                or len(set(mandatory)) != len(mandatory)):
            raise ValueError("Invalid mandatory evidence group")
        facts = prepared["facts"]
        for value in facts.values():
            if isinstance(value, str) and (len(value) > 200 or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise ValueError("Invalid bounded fact")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Non-finite fact")
        query = prepared["query"]
        if query is not None and (any(ord(c) < 32 or ord(c) == 127 for c in query)
                                  or not SAFE_QUERY.fullmatch(query.strip())):
            raise ValueError("Invalid bounded English query")
    except (ValidationError, TypeError, ValueError):
        return _result("ERROR", "INVALID_INPUT")
    terms = _tokens(query or "")
    channel, error, missing = _context(prepared["case_type"], facts, terms)
    if error:
        return _result("NO_RESULTS", error, missing=missing)
    repo = repository or EvidenceRepository()
    try:
        bundle, _ = repo.snapshot()
        version = bundle["source_version"]
        if version != expected_source_version:
            return _result("NO_RESULTS", "STALE_VERSION", version=version)
        allowed = {r for r, (channels, _, _) in TOPICS.items() if channel in channels}
        if not set(mandatory) <= allowed:
            return _result("NO_RESULTS", "EVIDENCE_UNAVAILABLE", version=version)
        candidates = {}
        for rule_id in sorted(allowed):
            rule = bundle["rules"].get(rule_id)
            if rule is None or rule["runtime_enabled"] is not False:
                # Known topic indexes cannot authorize missing/activated rules.
                if rule_id in mandatory:
                    return _result("NO_RESULTS", "EVIDENCE_UNAVAILABLE", version=version)
                continue
            _, words, fields = TOPICS[rule_id]
            matched = sorted(terms & _tokens(words))
            field_hits = [key for key in fields if _known(facts.get(key))]
            core = rule_id in CORE[channel]
            # Nonempty irrelevant text does not return a generic publisher set.
            if query is not None and not matched and rule_id not in mandatory:
                continue
            if query is None and not (field_hits or core or rule_id in mandatory):
                continue
            passages = [bundle["passages"][eid] for eid in rule["evidence_ids"]]
            document_terms = _tokens(" ".join(p["text"] + " " + p["summary"] + " " + p["locator"] for p in passages))
            score = 4 * len(matched) + min(2, len(terms & document_terms)) + 2 * len(field_hits) + int(core)
            candidates[rule_id] = {"score": score, "fields": field_hits, "terms": matched,
                                   "mandatory": rule_id in mandatory}
        if not candidates:
            return _result("NO_RESULTS", "NO_MATCH", version=version, missing=missing)
        order = sorted(candidates, key=lambda r: (-candidates[r]["score"], r))
        selected = list(mandatory)
        selected_ids = {eid for r in selected for eid in bundle["rules"][r]["evidence_ids"]}
        if len(selected_ids) > max_results:
            return _result("NO_RESULTS", "LIMIT_COVERAGE", version=version)
        for rule_id in order:
            union = selected_ids | set(bundle["rules"][rule_id]["evidence_ids"])
            if rule_id not in selected and len(selected) < MAX_RESULTS and len(union) <= max_results:
                selected.append(rule_id)
                selected_ids = union
        selected.sort(key=lambda r: (-candidates[r]["score"], r))
        # The established exact-rule API is still the authority for complete
        # source coverage. Ranking cannot drop an invalid selected mapping.
        exact = retrieve_evidence(prepared["case_type"], selected, facts, repository=repo)
        if exact["retrieval_status"] != "FOUND":
            status = "ERROR" if exact["retrieval_status"] == "ERROR" else "NO_RESULTS"
            return _result(status, "EVIDENCE_UNAVAILABLE", version=version)
        evidence = exact["evidence"]
        if {e["evidence_id"] for e in evidence} != selected_ids:
            return _result("NO_RESULTS", "EVIDENCE_UNAVAILABLE", version=version)
        evidence.sort(key=lambda e: (-max(candidates[r]["score"] for r in e["rule_ids"]), e["evidence_id"]))
        ids = [e["evidence_id"] for e in evidence]
        validate_citations(prepared["case_type"], selected, evidence, ids,
                           expected_source_version=expected_source_version, repository=repo)
        reasons = [{"evidence_id": e["evidence_id"], "rule_ids": list(e["rule_ids"]),
                    "topics": sorted(e["rule_ids"]),
                    "matched_fields": sorted({f for r in e["rule_ids"] for f in candidates[r]["fields"]}),
                    "matched_terms": sorted({t for r in e["rule_ids"] for t in candidates[r]["terms"]}),
                    "mandatory": any(r in mandatory for r in e["rule_ids"]),
                    "locator": bundle["passages"][e["evidence_id"]]["locator"]} for e in evidence]
        return _result("FOUND", "MATCHED", version=version, rules=selected,
                       evidence=evidence, reasons=reasons, missing=missing)
    except CitationValidationError:
        return _result("NO_RESULTS", "EVIDENCE_UNAVAILABLE")
    except (RepositoryError, OSError, ValueError, KeyError, TypeError):
        return _result("ERROR", "SOURCE_UNAVAILABLE")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared", type=Path, help="Confirmed synthetic input file; never log a real dispute")
    parser.add_argument("--source-version", required=True)
    args = parser.parse_args(argv)
    try:
        prepared = json.loads(args.prepared.read_text(encoding="utf-8"))
        result = retrieve_query_evidence(prepared, expected_source_version=args.source_version)
    except (OSError, ValueError):
        result = _result("ERROR", "INVALID_INPUT")
    print(json.dumps(result, indent=2))
    return {"FOUND": 0, "NO_RESULTS": 1, "ERROR": 2}[result["retrieval_status"]]


if __name__ == "__main__":
    raise SystemExit(main())
