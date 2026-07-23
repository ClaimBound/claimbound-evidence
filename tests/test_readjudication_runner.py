from pathlib import Path


def test_readjudication_runner_updates_in_place() -> None:
    text = (Path(__file__).resolve().parents[1] / "scripts/readjudicate_claim_batch.py").read_text()
    assert 'registry["cards"].extend' not in text
    assert 'registry_by_protocol[row["claim_id"]]["result_status"]' in text
    assert "expected one existing card" in text
