"""Task24 reviewed locale delivery: no publication without independent approval."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from backend.app import create_app
from backend.task24_delivery import (
    ATTESTATION, ChineseTranslationNotApproved, checked_review_attestation, reviewed_overlay)
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



@pytest.fixture
def missing_review_file(monkeypatch):
    """Simulate an absent approval file even after the real review is committed."""
    original_read_text = Path.read_text

    def read_text(path, *args, **kwargs):
        if path == ATTESTATION:
            raise FileNotFoundError(str(path))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

def test_default_no_review_attestation_blocks_public_translation(missing_review_file):
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


def test_feature_flag_alone_does_not_approve_translation(missing_review_file):
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


def test_reviewed_schema_is_distinct_and_strict(tmp_path):
    from jsonschema import Draft202012Validator, FormatChecker, ValidationError
    from backend.task24_delivery import REVIEWED_SCHEMA
    schema = json.loads(REVIEWED_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    catfile, approval = _files(tmp_path)
    response = reviewed_overlay(process_action_plan(REQUEST),
                                catalog_path=catfile, approval_path=approval)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(response)
    invalid = deepcopy(response)
    invalid["overlay_version"] = "task24-proposal-0.1"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)
    invalid = deepcopy(response)
    invalid["unreviewed_claim"] = "fabricated"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)
    invalid = deepcopy(response)
    invalid["display"]["question"] = {"field":"fabricated"}
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)


def test_source_traceability_has_real_profile_evidence_ids():
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "docs" / "task24-source-traceability.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    from rag.action_evidence import load_action_package
    package, _, _, _ = load_action_package()
    valid = {x["id"] for x in package["records"]}
    profiles = {p["id"] for p in package["profiles"]}
    assert len(data["source_backed_texts"]) >= 80
    assert data["review_status"] == "pending_review"
    assert data["reviewed_by"] is None
    for entry in data["source_backed_texts"]:
        assert entry["zh_hans"]
        for usage in entry["usages"]:
            assert usage["profile_id"] is None or usage["profile_id"] in profiles
            assert set(usage["evidence_ids"]) <= valid


def test_requested_copy_corrections_still_pending_review():
    from backend.task24_bilingual import CATALOG
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "Separate the pass event from the rental terms":
            "将工作准证状态变化与租约条款分开核查",
        "The signed agency agreement is a decisive document for choosing a contractual dispute route.":
            "已签署的房地产代理协议是判断应采用哪种合同争议处理渠道的重要文件。",
        "Monday to Friday, 9 am to 5 pm, excluding public holidays.":
            "周一至周五上午9时至下午5时，公共假期除外。",
    }
    for en, zh in expected.items():
        assert d["entries"][en] == {"zh_hans": zh, "review_status": "pending_review"}


# The following tests use a real temporary, internally consistent reviewer
# fixture, NOT a committed approval file or an assertion of Junjie's signoff.
# Patch only the local sidecar's file locations; all parsing, digest, schema
# and source-package version checks execute in the actual production logic.
def _call_reviewed_http(monkeypatch, app, catalog_path, approval_path, req=REQUEST):
    from functools import partial
    import backend.routes.task24 as endpoint
    from backend.task24_delivery import reviewed_overlay as real_overlay
    monkeypatch.setattr(
        endpoint, "reviewed_overlay",
        partial(real_overlay, catalog_path=catalog_path,
                approval_path=approval_path),
    )
    return app.test_client().post(
        "/api/action-plan/zh-hans-reviewed",
        json=req,
        headers={"Origin": "https://chu-junjie.github.io"},
    )


def test_http_200_with_valid_temporary_review_record(monkeypatch, tmp_path):
    from shared.validate_action_plan import validate_action_plan
    app = create_app()
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    catalog_file, approval_file = _files(tmp_path)
    response = _call_reviewed_http(monkeypatch, app, catalog_file, approval_file)
    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["overlay_version"] == "task24-reviewed-1.0"
    assert payload["translation_status"] == "approved_explanation"
    assert payload["is_official_translation"] is False
    assert payload["display"]["context_summary"]
    assert payload["reviewed_by"] == "Chu-Junjie"  # synthetic fixture only
    validate_action_plan(payload["canonical"], "response", request=REQUEST)
    assert payload["canonical"]["state"] == "CONFIRM"
    assert response.headers["Access-Control-Allow-Origin"] == "https://chu-junjie.github.io"


@pytest.mark.parametrize("change", [
    "wrong_reviewer", "wrong_status", "wrong_locale",
    "stale_source_version", "stale_catalog_version",
    "wrong_sha256", "changed_translation", "future_approval",
])
def test_http_503_for_mismatched_approval(monkeypatch, tmp_path, change):
    app = create_app()
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    catalog_file, approval_file = _files(tmp_path)
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    approval = json.loads(approval_file.read_text(encoding="utf-8"))
    if change == "wrong_reviewer":
        approval["approved_by"] = "not-Junjie"
    elif change == "wrong_status":
        approval["review_status"] = "pending_review"
    elif change == "wrong_locale":
        approval["locale"] = "en"
    elif change == "stale_source_version":
        approval["source_action_package_version"] = "action-kb-obsolete"
    elif change == "stale_catalog_version":
        approval["translation_catalog_version"] = "task24-obsolete"
    elif change == "wrong_sha256":
        approval["entries_sha256"] = "0" * 64
    elif change == "changed_translation":
        catalog["entries"]["You reported a dispute about purchased goods."]["zh_hans"] += " (changed)"
    elif change == "future_approval":
        approval["reviewed_at"] = "2099-01-01T00:00:00+00:00"
    catalog_file.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    approval_file.write_text(json.dumps(approval), encoding="utf-8")
    response = _call_reviewed_http(monkeypatch, app, catalog_file, approval_file)
    assert response.status_code == 503, (change, response.get_json())
    assert response.get_json()["error"] == "translation_not_approved"
    assert "display" not in response.get_json()


def test_english_http_unchanged_before_and_after_review(monkeypatch, tmp_path):
    app = create_app()
    client = app.test_client()
    original = client.post("/api/action-plan", json=REQUEST)
    assert original.status_code == 200
    english = original.get_json()
    assert english["state"] == "CONFIRM"
    assert "display" not in english
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    catalog_file, approval_file = _files(tmp_path)
    chinese = _call_reviewed_http(monkeypatch, app, catalog_file, approval_file)
    assert chinese.status_code == 200
    after = client.post("/api/action-plan", json=REQUEST)
    assert after.status_code == 200
    assert after.get_json() == english
    assert chinese.get_json()["canonical"] == english
