# SPDX-License-Identifier: Apache-2.0
"""Offline tests for NASA POWER parser/materializer and CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from claimbound_evidence.nasa_power import (
    parse_nasa_power_json_file,
    solar_7d_mean_from_values,
)
from claimbound_evidence.nasa_power_parser import (
    parse_nasa_power_daily_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_power_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "Feature",
                "properties": {
                    "parameter": {
                        "ALLSKY_SFC_SW_DWN": {
                            "20240101": 1.0,
                            "20240102": 2.0,
                            "20240103": 3.0,
                            "20240104": -999.0,
                        },
                        "T2M": {
                            "20240101": 4.0,
                            "20240102": 5.0,
                            "20240103": 6.0,
                            "20240104": 7.0,
                        },
                        "WS10M": {
                            "20240101": 1.1,
                            "20240102": 1.2,
                            "20240103": 1.3,
                            "20240104": 1.4,
                        },
                        "PRECTOTCORR": {
                            "20240101": 0.0,
                            "20240102": 0.5,
                            "20240103": 0.1,
                            "20240104": 0.2,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def _load_cli_module():
    script_path = REPO_ROOT / "scripts" / "fetch_nasa_power.py"
    import importlib.util as ilu

    spec = ilu.spec_from_file_location("fetch_nasa_power_mod", script_path)
    assert spec is not None and spec.loader is not None
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_power_fixture(tmp_path: Path) -> None:
    src = tmp_path / "power.json"
    _write_power_fixture(src)
    days, values, summary = parse_nasa_power_daily_json(
        src,
        parameters=("ALLSKY_SFC_SW_DWN", "T2M", "WS10M", "PRECTOTCORR"),
    )
    assert [day.isoformat() for day in days] == [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
    ]
    assert values["ALLSKY_SFC_SW_DWN"].tolist() == [1.0, 2.0, 3.0]
    assert summary.rows == 3
    assert summary.skipped >= 1


def test_parse_power_json_file_and_solar_mean(tmp_path: Path) -> None:
    src = tmp_path / "power.json"
    _write_power_fixture(src)
    days, values, summary = parse_nasa_power_json_file(src)
    solar = solar_7d_mean_from_values(values)
    assert len(days) == 3
    assert summary["rows"] == 3
    assert solar.tolist() == pytest.approx([1.0, 1.5, 2.0])


def test_cli_help_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(sys, "argv", ["fetch_nasa_power.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        module.main()  # type: ignore[attr-defined]
    assert exc.value.code == 0


def test_cli_mock_mode_writes_csv_and_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_cli_module()
    out_csv = tmp_path / "mock.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_nasa_power.py",
            "--point",
            "POWER_A",
            "--mode",
            "mock",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-08",
            "--seed",
            "11",
            "--out",
            str(out_csv),
        ],
    )
    assert module.main() == 0  # type: ignore[attr-defined]
    assert out_csv.is_file()
    manifest = out_csv.with_suffix(".csv.manifest.json")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["source_mode"] == "mock"
    assert payload["rows"] == 7
    assert payload["point_location_redacted"] is True
    assert "latitude" not in payload
    assert "longitude" not in payload
    assert payload["raw_payload_committed"] is False
    assert "synthetic plumbing only" in payload["honest_boundary"]


def test_cli_json_file_mode_writes_csv_and_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_cli_module()
    src = tmp_path / "power.json"
    out_csv = tmp_path / "power.csv"
    _write_power_fixture(src)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_nasa_power.py",
            "--point",
            "POWER_A",
            "--mode",
            "nasa_power_json_file",
            "--json-path",
            str(src),
            "--out",
            str(out_csv),
        ],
    )
    assert module.main() == 0  # type: ignore[attr-defined]
    manifest = out_csv.with_suffix(".csv.manifest.json")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["source_mode"] == "nasa_power_json_file"
    assert payload["rows"] == 3
    assert payload["point_location_redacted"] is True
    assert "latitude" not in payload
    assert "longitude" not in payload
    assert "payload_basename" not in payload
    assert "payload_sha256" not in payload
    assert "source_file_sha256" not in payload


def test_cli_json_file_mode_requires_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_nasa_power.py",
            "--point",
            "POWER_A",
            "--mode",
            "nasa_power_json_file",
            "--out",
            str(tmp_path / "x.csv"),
        ],
    )
    with pytest.raises(ValueError):
        module.main()  # type: ignore[attr-defined]
