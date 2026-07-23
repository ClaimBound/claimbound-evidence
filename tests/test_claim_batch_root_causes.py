from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_claim_batch_root_causes.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("claim_batch_root_causes", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cause_classification() -> None:
    module = load_module()
    assert module.blocked_cause(404) == "STALE_OR_INCORRECT_EXACT_URL"
    assert module.blocked_cause(403) == "ACCESS_POLICY_OR_ANTI_BOT"
    assert module.blocked_cause(0) == "TRANSPORT_FAILURE"
    assert module.insufficient_cause("") == "VERY_SHORT_OR_SHELL_EXTRACTION"
    assert module.insufficient_cause("x" * 1_000) == "SHORT_EXTRACT_REQUIRES_REVIEW"
    assert module.insufficient_cause("x" * 2_000) == "GATE_SPECIFIC_FACETS_MISSING"


def test_analysis_counts_unique_blocked_source_once(tmp_path: Path) -> None:
    module = load_module()
    report = {
        "issue_number": 999,
        "cards": [
            {
                "domain_code": "DOM001",
                "topic_index": 1,
                "topic": "forest loss",
                "gate": gate,
                "status": "BLOCKED_SOURCE",
                "http_status": 404,
                "source_url": "https://official.example/missing",
            }
            for gate in ("source-integrity", "time-boundary")
        ],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = module.analyze([report_path], str(tmp_path / "cache-{issue}"))
    assert result["blocked_source"]["cards"] == 2
    assert result["blocked_source"]["unique_sources"] == 1
    assert result["blocked_source"]["by_http_status_sources"] == {"404": 1}
