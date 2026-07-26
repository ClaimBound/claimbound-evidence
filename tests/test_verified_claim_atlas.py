import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "scripts/build_verified_claim_atlas.py"
    spec = importlib.util.spec_from_file_location("build_verified_claim_atlas", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_verified_claim_atlas_has_every_claim_and_category(tmp_path):
    builder = load_builder()
    output = tmp_path / "site"
    builder.build(output)
    payload = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert payload["maintainer"] == "NeoZorK"
    assert payload["claim_count"] == 7000
    assert payload["category_count"] == 100
    assert sum(payload["result_counts"].values()) == 7000
    assert payload["protocol_audit_conclusion"] == (
        "COMPLETE_CARD_SET_BUT_CURRENT_PROTOCOL_COMPLIANCE_NOT_ESTABLISHED"
    )
    assert all(item["dedicated_concrete_claim_under_test"] is None for item in payload["results"])
    assert all(item["adjudication_rule"] for item in payload["results"])
    assert all(item["evidence_locator"] for item in payload["results"])
    assert all(item["current_batch_manifest_compliance"] == "FAIL" for item in payload["results"])
    assert sum(bool(item["review_target_statement"]) for item in payload["results"]) == 4270
    assert sum(bool(item["card_report_metadata_mismatches"]) for item in payload["results"]) == 500
    assert len(list((output / "categories").glob("*/index.html"))) == 100
    home = (output / "index.html").read_text(encoding="utf-8")
    assert "PENDING_SOURCE_SELECTION" not in home
    assert "Not 7,000 captured public claims" in home
    category = (output / "categories/foundation-models/index.html").read_text(
        encoding="utf-8"
    )
    assert category.count('<article class="claim"') == 70
    assert "Exact preregistered audit question" in category
    assert "Dedicated concrete claim-under-test" in category
    assert "Card/report metadata agreement" in category
    assert "Frozen parameters" in category
    audit_page = (output / "audit/index.html").read_text(encoding="utf-8")
    assert "0 / 7000" in audit_page


def test_campaign_audit_exposes_known_protocol_failures():
    builder = load_builder()
    audit = builder.audit_campaign()
    checks = {item["id"]: item for item in audit["protocol_checks"]}
    assert audit["outcome_counts"] == {
        "PASSED_UNDER_PROTOCOL": 729,
        "INSUFFICIENT_COVERAGE": 4281,
        "NEGATIVE_RESULT_UNDER_PROTOCOL": 0,
        "BLOCKED_SOURCE": 1920,
        "SOURCE_DRIFT": 70,
    }
    assert audit["topic_source_analysis"]["fully_blocked_groups"] == 192
    assert audit["topic_source_analysis"]["accessible_adjudicated_groups"] == 501
    assert checks["source-role"]["status"] == "FAIL"
    assert checks["source-role"]["passed"] == 0
    assert checks["selection-provenance"]["status"] == "FAIL"
    assert checks["fetch-attempt-provenance"]["passed"] == 0
    assert checks["source-integrity-pass-evidence"]["total"] == 300
    assert checks["topic-url-diversity"]["passed"] == 68
    assert checks["executable-pass-reproduction"]["total"] == 96
    assert checks["reproducibility-pass-consistency"]["total"] == 23
    assert checks["report-file-integrity"]["passed"] == 7000
    assert checks["source-manifest-publication"]["passed"] == 15
