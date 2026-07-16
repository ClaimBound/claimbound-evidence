from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from nasa_factory_data import BATCH_ISSUES, load_matrix  # noqa: E402


def _load_builder() -> ModuleType:
    path = REPO_ROOT / "scripts" / "build_nasa_factory_atlas.py"
    spec = importlib.util.spec_from_file_location("build_nasa_factory_atlas", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nasa_issue_matrices_cover_the_frozen_500_card_range() -> None:
    protocols: list[str] = []
    for issue_number in BATCH_ISSUES:
        matrix, payload = load_matrix(issue_number)
        assert len(matrix["cards"]) == 50
        assert json.loads(payload) == matrix
        protocols.extend(row["protocol_id"] for row in matrix["cards"])
    assert len(protocols) == len(set(protocols)) == 500
    assert protocols[0] == "NASA-ARTEMIS-01-D701"
    assert protocols[-1] == "NASA-EMIT-10-D1200"


def test_nasa_atlas_matches_registered_cards_and_static_outputs() -> None:
    builder = _load_builder()
    atlas = builder.collect_atlas()
    generated = json.loads(builder.DATA_JSON_PATH.read_text(encoding="utf-8"))
    assert generated == atlas
    assert atlas["card_count"] == 500
    assert atlas["mission_count"] == 50
    assert atlas["slot_count"] == 10
    assert atlas["result_counts"] == {
        "INSUFFICIENT_COVERAGE": 435,
        "PASSED_UNDER_PROTOCOL": 65,
    }
    assert all(
        (REPO_ROOT / row["evidence_path"]).is_file()
        and (REPO_ROOT / row["svg_path"]).is_file()
        for row in atlas["cards"]
    )
    ElementTree.parse(REPO_ROOT / "docs" / "assets" / "nasa_500_heatmap.svg")
    javascript = builder.DATA_JS_PATH.read_text(encoding="utf-8")
    assert javascript.startswith("window.NASA_ATLAS_DATA = ")
    assert "fetch(" not in (REPO_ROOT / "docs" / "nasa" / "atlas" / "atlas.js").read_text(encoding="utf-8")
