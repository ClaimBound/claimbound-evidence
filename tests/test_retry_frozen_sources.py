from pathlib import Path


def test_retry_preserves_original_attempt_and_exact_url() -> None:
    text = (Path(__file__).resolve().parents[1] / "scripts/retry_frozen_claim_sources.py").read_text()
    assert '"profile": "original-cached"' in text
    assert '"profile": "curl-browser-compatible"' in text
    assert "source_url" in text
    assert "status == 200" in text
