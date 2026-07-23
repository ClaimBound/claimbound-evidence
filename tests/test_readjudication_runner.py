from pathlib import Path
import importlib.util
import sys


def load_module():
    script = Path(__file__).resolve().parents[1] / "scripts/readjudicate_claim_batch.py"
    sys.path.insert(0, str(script.parent))
    spec = importlib.util.spec_from_file_location("readjudicate_claim_batch", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readjudication_runner_updates_in_place() -> None:
    text = (Path(__file__).resolve().parents[1] / "scripts/readjudicate_claim_batch.py").read_text()
    assert 'registry["cards"].extend' not in text
    assert 'registry_by_protocol[row["claim_id"]]["result_status"]' in text
    assert "expected one existing card" in text


def test_executable_gates_cannot_pass_on_keyword_locators_alone() -> None:
    text = (Path(__file__).resolve().parents[1] / "scripts/readjudicate_claim_batch.py").read_text()
    assert '"numerator-denominator"' in text
    assert '"method-version"' in text
    assert '"reproducibility"' in text
    assert 'reason_code = (' in text
    assert '"EXECUTION_ARTIFACT_MISSING"' in text


def test_source_integrity_requires_recorded_access_and_redirect_chain() -> None:
    module = load_module()
    source = {
        "source_url": "https://official.test/report",
        "final_url": "https://official.test/report",
        "sha256": "a" * 64,
    }
    assert module.missing_source_integrity_fields(source) == [
        "accessed-at-utc",
        "redirect-chain",
    ]
    source.update({"accessed_at_utc": "2026-07-23T12:00:00+00:00", "redirect_chain": []})
    assert module.missing_source_integrity_fields(source) == []
