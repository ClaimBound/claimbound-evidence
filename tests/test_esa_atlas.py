from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_esa_factory_atlas.py"


def _load_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_esa_factory_atlas", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_atlas_matches_validated_sources() -> None:
    builder = _load_builder()
    expected = builder.collect_atlas()
    generated = json.loads(builder.DATA_JSON_PATH.read_text(encoding="utf-8"))

    assert generated == expected
    assert generated["card_count"] == 500
    assert generated["mission_count"] == 25
    assert generated["slot_count"] == 20
    assert generated["result_counts"] == {
        "INSUFFICIENT_COVERAGE": 10,
        "PASSED_UNDER_PROTOCOL": 490,
    }


def test_atlas_cards_resolve_to_committed_json_and_svg() -> None:
    atlas = json.loads(
        (REPO_ROOT / "docs" / "esa" / "atlas" / "atlas-data.json").read_text(
            encoding="utf-8"
        )
    )
    missions: dict[str, set[int]] = {}

    for card in atlas["cards"]:
        assert (REPO_ROOT / card["evidence_path"]).is_file()
        assert (REPO_ROOT / card["svg_path"]).is_file()
        missions.setdefault(card["mission"], set()).add(card["slot"])

    assert len(missions) == 25
    assert all(slots == set(range(1, 21)) for slots in missions.values())


def test_atlas_static_and_offline_outputs_are_well_formed() -> None:
    atlas_dir = REPO_ROOT / "docs" / "esa" / "atlas"
    data = json.loads((atlas_dir / "atlas-data.json").read_text(encoding="utf-8"))
    javascript = (atlas_dir / "atlas-data.js").read_text(encoding="utf-8")
    prefix = "window.ESA_ATLAS_DATA = "

    assert javascript.startswith(prefix)
    assert json.loads(javascript.removeprefix(prefix).removesuffix(";\n")) == data
    ElementTree.parse(REPO_ROOT / "docs" / "assets" / "esa_500_heatmap.svg")

    html = (atlas_dir / "index.html").read_text(encoding="utf-8")
    behavior = (atlas_dir / "atlas.js").read_text(encoding="utf-8")
    assert 'id="heatmap"' in html
    assert 'id="gaps-button"' in html
    assert 'id="detail-panel"' in html
    assert "fetch(" not in behavior
