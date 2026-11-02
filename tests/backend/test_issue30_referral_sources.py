"""Issue #30: safe referral source context and negative cases."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from backend.app import create_app
from backend.rag_bridge import referral_source_context
from rag.import_knowledge_base import load_knowledge_base
from shared.validate_contracts import validate

RENTAL = {"dispute_with":"landlord","premises_type":"residential","claim_amount_sgd":123}
CONSUMER = {"purchase_type":"goods","purchase_purpose":"personal",
            "supplier_registered_in_sg":True,"claim_amount_sgd":123}

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", RENTAL), ("consumer_complaint", CONSUMER),
])
def test_referral_has_real_versioned_sources_but_no_legal_card(client,case,answers):
    response=client.post("/api/navigate",json={"api_version":"1.0","case_type":case,"answers":answers})
    assert response.status_code==200
    data=response.get_json()
    validate(data,"navigate_response")
    assert data["status"]=="REFER_TO_OFFICIAL"
    assert data["action_card"] is None
    assert data["evidence"]
    assert data["source_version"]==load_knowledge_base()["source_version"]
    assert all(x["url"].startswith("https://") and x["source_version"]==data["source_version"]
               and x["review_status"]=="verified" for x in data["evidence"])

@pytest.mark.parametrize("patch_value", [
    ("NO_RESULTS", []), ("INVALID", []), ("ERROR", []),
])
def test_retrieval_without_valid_sources_does_not_return_links(client,patch_value):
    with patch("backend.rules.engine.retrieve_checked",return_value=patch_value):
        response=client.post("/api/navigate",json={"api_version":"1.0","case_type":"rental_deposit","answers":RENTAL})
    data=response.get_json()
    validate(data,"navigate_response")
    assert data["evidence"]==[] and data["action_card"] is None

@pytest.mark.parametrize("change", [
    {"url":"https://example.invalid/test"},
    {"url":"http://www.judiciary.gov.sg/page"},
    {"source_version":"obsolete-version"},
    {"review_status":"quarantined"},
    {"url":"https://localhost/file"},
])
def test_source_presentation_fails_closed_on_invalid_metadata(change):
    version=load_knowledge_base()["source_version"]
    record={"evidence_id":"test","source_id":"test","rule_ids":["SCT_RESIDENTIAL_SCOPE"],
            "url":"https://www.judiciary.gov.sg/civil/cases-eligible-small-claim",
            "review_status":"verified","source_version":version}
    record.update(change)
    assert referral_source_context([record],expected_version=version)==[]

def test_duplicate_source_id_is_not_presented():
    version=load_knowledge_base()["source_version"]
    record={"evidence_id":"test","source_id":"test","rule_ids":["SCT_RESIDENTIAL_SCOPE"],
            "url":"https://www.judiciary.gov.sg/civil/cases-eligible-small-claim",
            "review_status":"verified","source_version":version}
    assert referral_source_context([record,deepcopy(record)],expected_version=version)==[]
