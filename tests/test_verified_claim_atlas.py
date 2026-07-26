import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "scripts/build_public_claim_atlas_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_claim_atlas_v2", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_public_claim_atlas_has_7000_distinct_claims(tmp_path):
    builder = load_builder()
    output = tmp_path / "site"
    builder.build(output)
    payload = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert payload["maintainer"] == "NeoZorK"
    assert payload["claim_count"] == 7000
    assert payload["distinct_statement_count"] == 7000
    assert payload["category_count"] == 100
    assert payload["result_counts"] == {"PASSED_UNDER_PROTOCOL": 7000}
    assert all(item["public_claim_text"] for item in payload["results"])
    assert all(item["public_claim_verbatim_quote"] for item in payload["results"])
    assert all(item["public_claim_locator"] for item in payload["results"])
    pages = list((output / "categories").glob("*/index.html"))
    assert len(pages) == 100
    assert all(page.read_text(encoding="utf-8").count('<article class="claim">') == 70 for page in pages)
    assert "7,000 / 7,000" in (output / "audit/index.html").read_text(encoding="utf-8")
