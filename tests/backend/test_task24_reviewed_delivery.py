"""Task24 reviewed locale delivery: no publication without independent approval."""
import hashlib
import json
from copy import deepcopy

import pytest

from backend.app import create_app
from backend.task24_delivery import (
    ChineseTranslationNotApproved, checked_review_attestation, reviewed_overlay)
from backend.task24_bilingual import CATALOG
from backend.action_plan_service import process_action_plan

REQUEST = {
    "action_plan_version": "1.0", "request_id": "task24-delivery-12345",
    "operation": "interpret",
    "description": "I bought a faulty product and want a refund.",
}


def _approval(catalog):
    return {
        "approval_version": "task24-reviewed-1.0",
        "translation_catalog_version": catalog["catalog_version"],
        "source_action_package_version": catalog["source_action_package_version"],
        "locale": "zh-Hans",
        "approved_by": "Chu-Junjie",
        "review_status": "approved",
        "reviewed_at": "2026-11-10T07:00:00+00:00",
        "entries_sha256": hashlib.sha256(json.dumps(
            catalog["entries"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest(),
    }


def _files(tmp_path):
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catfile = tmp_path / "catalog.json"
    approval = tmp_path / "approval.json"
    catfile.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    approval.write_text(json.dumps(_approval(catalog)), encoding="utf-8")
    return catfile, approval


def test_default_no_review_attestation_blocks_public_translation():
    canonical = process_action_plan(REQUEST)
    with pytest.raises(ChineseTranslationNotApproved):
        reviewed_overlay(canonical)


def test_reviewed_endpoint_404_default_and_canonical_unchanged():
    app = create_app()
    client = app.test_client()
    assert client.post("/api/action-plan/zh-hans-reviewed", json=REQUEST).status_code == 404
    response = client.post("/api/action-plan", json=REQUEST)
    assert response.status_code == 200
    assert response.get_json()["state"] == "CONFIRM"
    assert "display" not in response.get_json()


def test_feature_flag_alone_does_not_approve_translation():
    app = create_app()
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    c = app.test_client()
    result = c.post("/api/action-plan/zh-hans-reviewed", json=REQUEST)
    assert result.status_code == 503
    assert result.get_json()["error"] == "translation_not_approved"
    assert c.post("/api/action-plan/zh-hans-reviewed", json={
        **REQUEST, "action_plan_version": "2.0"}).status_code == 400


def test_attestation_allows_reviewed_copy_only_with_real_separate_signed_fixture(tmp_path):
    catfile, approval = _files(tmp_path)
    result = checked_review_attestation(catalog_path=catfile, approval_path=approval)
    assert result["approved_by"] == "Chu-Junjie"
    canonical = process_action_plan(REQUEST)
    original = deepcopy(canonical)
    sidecar = reviewed_overlay(canonical, catalog_path=catfile, approval_path=approval)
    assert sidecar["translation_status"] == "approved_explanation"
    assert sidecar["display"]["context_summary"]
    assert sidecar["canonical"] == original == canonical
    assert not sidecar["is_official_translation"]


@pytest.mark.parametrize("mutation", [
    lambda c, a: a.update(approved_by="other-person"),
    lambda c, a: a.update(review_status="pending_review"),
    lambda c, a: a.update(locale="en"),
    lambda c, a: a.update(reviewed_at="2030-01-01T00:00:00+00:00"),
    lambda c, a: a.update(entries_sha256="0"*64),
    lambda c, a: c["entries"]["You reported a dispute about purchased goods."].update(zh_hans="已修改但未审核"),
])
def test_forged_or_stale_approval_rejected(tmp_path, mutation):
    cfile, afile = _files(tmp_path)
    c = json.loads(cfile.read_text(encoding="utf-8"))
    a = json.loads(afile.read_text(encoding="utf-8"))
    mutation(c, a)
    cfile.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    afile.write_text(json.dumps(a), encoding="utf-8")
    with pytest.raises(ChineseTranslationNotApproved):
        checked_review_attestation(catalog_path=cfile, approval_path=afile)


def test_canonical_evidence_urls_and_values_preserved(tmp_path):
    catfile, approval = _files(tmp_path)
    req = {
        "action_plan_version": "1.0", "request_id": "task24-actual-12345",
        "operation": "plan", "confirmed": True,
        "context": {
            "case_type": "consumer_complaint", "issue_subtype": "restaurant_overcharge",
            "goal": "complain", "facts": {
                "merchant_location": "singapore", "purchase_purpose": "personal",
                "consumer_context": "local_consumer", "resolution_attempted": True,
            },
            "summary": "You reported a restaurant billing overcharge. You want to make a complaint.",
        },
    }
    canonical = process_action_plan(req)
    assert canonical["state"] == "READY"
    sidecar = reviewed_overlay(canonical, catalog_path=catfile, approval_path=approval)
    assert sidecar["canonical"]["plan"]["evidence"] == canonical["plan"]["evidence"]
    assert sidecar["canonical"]["plan"]["legal_basis"] == canonical["plan"]["legal_basis"]
    assert sidecar["canonical"]["revision"] == canonical["revision"]
    assert sidecar["display"]["plan"]["contacts"][0]["value"] == canonical["plan"]["contacts"][0]["value"]
