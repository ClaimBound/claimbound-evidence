# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from claimbound_evidence.noaa_coops_fetch import (
    build_datagetter_url,
    fetch_d131_station_payloads,
    merge_hourly_height_payloads,
    merge_predictions_payloads,
    year_chunks,
)


def test_year_chunks_for_d131_period() -> None:
    chunks = year_chunks(date(2018, 1, 1), date(2024, 12, 31))
    assert chunks[0] == (date(2018, 1, 1), date(2018, 12, 31))
    assert chunks[-1] == (date(2024, 1, 1), date(2024, 12, 31))
    assert len(chunks) == 7


def test_build_datagetter_url_includes_predictions_interval() -> None:
    from claimbound_evidence.noaa_coops_fetch import NoaaCoopsFetchConfig

    url = build_datagetter_url(
        NoaaCoopsFetchConfig(
            station="8518750",
            product="predictions",
            begin=date(2018, 1, 1),
            end=date(2018, 12, 31),
        ),
        date(2018, 1, 1),
        date(2018, 12, 31),
    )
    assert "interval=h" in url
    assert "product=predictions" in url


def test_merge_hourly_height_payloads_concatenates_data() -> None:
    merged = merge_hourly_height_payloads(
        [
            {"metadata": {"id": "8518750"}, "data": [{"t": "2018-01-01 00:00", "v": "1"}]},
            {"data": [{"t": "2019-01-01 00:00", "v": "2"}]},
        ]
    )
    assert merged["metadata"] == {"id": "8518750"}
    assert merged["data"] == [
        {"t": "2018-01-01 00:00", "v": "1"},
        {"t": "2019-01-01 00:00", "v": "2"},
    ]


def test_merge_predictions_payloads_concatenates_predictions() -> None:
    merged = merge_predictions_payloads(
        [
            {"predictions": [{"t": "2018-01-01 00:00", "v": "1"}]},
            {"predictions": [{"t": "2019-01-01 00:00", "v": "2"}]},
        ]
    )
    assert merged == {
        "predictions": [
            {"t": "2018-01-01 00:00", "v": "1"},
            {"t": "2019-01-01 00:00", "v": "2"},
        ]
    }


def test_fetch_d131_station_payloads_uses_yearly_chunks(tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_fetch(url: str) -> dict[str, object]:
        calls.append(url)
        if "product=hourly_height" in url:
            year = url.split("begin_date=")[1][:4]
            return {
                "metadata": {"id": "8518750"},
                "data": [{"t": f"{year}-01-01 00:00", "v": "1"}],
            }
        year = url.split("begin_date=")[1][:4]
        return {"predictions": [{"t": f"{year}-01-01 00:00", "v": "1"}]}

    paths = fetch_d131_station_payloads(
        "8518750",
        tmp_path,
        begin=date(2018, 1, 1),
        end=date(2019, 12, 31),
        fetch_json=fake_fetch,
    )

    assert len(paths) == 2
    observed = json.loads((tmp_path / "8518750_observed.json").read_text(encoding="utf-8"))
    predictions = json.loads((tmp_path / "8518750_predictions.json").read_text(encoding="utf-8"))
    assert len(observed["data"]) == 2
    assert len(predictions["predictions"]) == 2
    assert len(calls) == 4


def test_merge_hourly_height_raises_on_api_error() -> None:
    with pytest.raises(ValueError, match="Range Limit Exceeded"):
        merge_hourly_height_payloads([{"error": {"message": "Range Limit Exceeded"}}])
