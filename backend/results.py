"""Task 12 provisional, information-only result projection.

This is deliberately separate from the v1 legal Action Card and does not enable
any legal rules. Template prose is maintained by the RAG owner, not generated.
"""
import hashlib
import json
from urllib.parse import urlsplit

from rag.import_knowledge_base import current_reviews
from rag.repository import EvidenceRepository

RESULTS_VERSION = "0.1"
FIELDS = ("dispute_with", "premises_type", "tenancy_duration_months",
          "claim_amount_sgd", "relevant_event_date", "respondent_in_singapore",
          "agency_agreement_signed", "purchase_type", "purchase_purpose",
          "supplier_registered_in_sg", "supplier_location", "purchase_date",
          "resolution_attempted", "documents_available")
UNRESOLVED = {
    "rental_deposit": ("dispute_with", "premises_type", "tenancy_duration_months",
                       "claim_amount_sgd", "relevant_event_date",
                       "respondent_in_singapore"),
    "consumer_complaint": ("purchase_type", "purchase_purpose",
                           "supplier_registered_in_sg", "supplier_location",
                           "claim_amount_sgd", "purchase_date"),
}
LIMIT = ("This is research and preparation information, not an eligibility, "
         "filing, deadline or legal entitlement decision. Check official services.")

def _missing(value):
    return value is None or value == "unknown" or value == ""

def _scope(case_type, answers):
    if case_type == "rental_deposit":
        if str(answers.get("premises_type", "")).lower() in ("commercial", "industrial"):
            return False
        return True
    if str(answers.get("purchase_purpose", "")).lower() == "business":
        return False
    if answers.get("supplier_registered_in_sg") is False:
        return False
    location = answers.get("supplier_location")
    if isinstance(location, str) and location.strip() and location.lower().strip() not in (
            "singapore", "sg", "unknown"):
        return False
    return True

def _templates(case_type, answers, bundle):
    if case_type == "rental_deposit":
        party = str(answers.get("dispute_with") or "").lower()
        if party == "landlord":
            names = {"rental-sct-review"}
        elif party in ("agent", "agency", "property_agent"):
            # A property agent's conduct complaint and agency contract dispute
            # are not automatically interchangeable; no unconfirmed route.
            names = {"agency-contract-review"} if answers.get("agency_agreement_signed") is True else set()
        else:
            names = set()
    else:
        names = {"consumer-case-review", "consumer-sct-review"} if (
            str(answers.get("purchase_purpose", "")).lower() == "personal"
            and answers.get("supplier_registered_in_sg") is True) else set()
    return [bundle["templates"][name] for name in sorted(names)
            if name in bundle["templates"]
            and bundle["templates"][name]["review_status"] == "verified"]

def _checked_passage(evidence_id, case_type, bundle, blocked):
    p = bundle["passages"].get(evidence_id)
    if not p or p["source_id"] in blocked or p["review_status"] != "verified":
        return None
    source = bundle["sources"].get(p["source_id"])
    if not source or source["status"] != "verified" or case_type not in p["case_types"]:
        return None
    if p["source_version"] != bundle["source_version"] or source["version"] != bundle["source_version"]:
        return None
    if p["url"] != source["url"] or not p["text"].strip() or p["text_kind"] != "verbatim_excerpt":
        return None
    url = urlsplit(p["url"])
    if url.scheme != "https" or url.hostname not in (
            "www.judiciary.gov.sg", "www.cea.gov.sg", "www.case.org.sg"):
        return None
    if hashlib.sha256(p["text"].encode("utf-8")).hexdigest() != p["excerpt_sha256"]:
        return None
    reviews = current_reviews(source, bundle["review_log"])
    if not any(dict(zip(r["evidence_ids"].split(";"),
                        r["excerpt_sha256s"].split(";"))).get(evidence_id) == p["excerpt_sha256"]
               for r in reviews):
        return None
    return {
        "evidence_id": evidence_id, "source_id": p["source_id"],
        "rule_ids": list(p["rule_ids"]), "url": p["url"],
        "review_status": p["review_status"], "source_version": p["source_version"],
        "publisher": source["publisher"], "title": source["title"],
        "verbatim_excerpt": p["text"], "source_locator": p["locator"],
        "reviewed_at": source["reviewed_at"],
        "summary": p["summary"],  # Editorial, NEVER passed off as source quotation.
        "excerpt_sha256": p["excerpt_sha256"],
    }

def assemble(case_type, answers, *, repository=None):
    """Return limited conditional research guidance based on current checked state."""
    repository = repository or EvidenceRepository()
    bundle, blocked = repository.snapshot()
    version = bundle["source_version"]
    relevant = {key: answers[key] for key in FIELDS if key in answers}
    fingerprint = hashlib.sha256(json.dumps(
        [RESULTS_VERSION, version, case_type, relevant, sorted(blocked)],
        sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()[:24]
    missing = [name for name in UNRESOLVED[case_type]
               if name not in relevant or _missing(relevant[name])]
    response = {
        "results_version": RESULTS_VERSION, "result_id": fingerprint,
        "source_version": version, "guidance_status": "LIMITED_REFERRAL",
        "research_guidance": None, "display_evidence": [],
        "unresolved_fields": missing, "limitations": [LIMIT],
    }
    if not _scope(case_type, relevant):
        response["limitations"].append("This situation is outside the current SG Navi pilot scope.")
        return response
    selected = _templates(case_type, relevant, bundle)
    if not selected:
        response["limitations"].append(
            "Insufficient confirmed case details to select a source-backed research topic.")
        return response

    sections = {"potential_channels": [], "conditions": [], "steps": [],
                "document_checklist": []}
    evidence = {}
    dropped = False
    for template in selected:
        # One missing/unverified citation blocks the ENTIRE template; never
        # silently show an incomplete step or imply remaining citations suffice.
        ids = {id_ for section in ("conditions", "steps", "document_checklist", "limitations")
               for entry in template[section] for id_ in entry["evidence_ids"]}
        proofs = {id_: _checked_passage(id_, case_type, bundle, blocked) for id_ in ids}
        if not all(proofs.values()):
            dropped = True
            continue
        evidence.update(proofs)
        sections["potential_channels"].append({
            "text": template["channel"] + " (conditional official source to check; not eligibility)",
            "evidence_ids": sorted(ids),
        })
        for key in ("conditions", "steps", "document_checklist"):
            sections[key].extend({"text": item["text"], "evidence_ids": list(item["evidence_ids"])}
                                 for item in template[key])
        response["limitations"].extend(item["text"] for item in template["limitations"])
    if dropped:
        response["limitations"].append(
            "A source was missing, changed or quarantined; affected guidance was withheld.")
    if not sections["potential_channels"]:
        response["limitations"].append("No currently reviewable source-backed guidance is available.")
        return response
    # A fully reviewed excerpt supports research context, not legal eligibility.
    response["guidance_status"] = "GUIDANCE_ONLY"
    response["research_guidance"] = {
        "case_summary": "User-confirmed " + case_type.replace("_", " ") +
                        " scenario; facts have not been independently verified.",
        **sections,
        "unresolved_questions": [
            {"field": field, "text": "Confirm " + field.replace("_", " ") + "."}
            for field in missing],
        "citations": sorted(evidence),
    }
    response["display_evidence"] = [evidence[key] for key in sorted(evidence)]
    return response
