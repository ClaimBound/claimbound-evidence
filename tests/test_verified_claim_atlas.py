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
    payload = json.loads((output / "results.json").read_text())
    assert payload["maintainer"] == "NeoZorK"
    assert payload["claim_count"] == 7000
    assert payload["category_count"] == 100
    assert sum(payload["result_counts"].values()) == 7000
    assert len(list((output / "categories").glob("*/index.html"))) == 100
    assert "PENDING_SOURCE_SELECTION" not in (output / "index.html").read_text()
