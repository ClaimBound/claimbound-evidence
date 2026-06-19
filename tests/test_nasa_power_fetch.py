# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

from claimbound_evidence.nasa_power import NASA_POWER_POINTS
from claimbound_evidence.nasa_power_fetch import (
    build_nasa_power_point_url,
    download_nasa_power_d103_points,
)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_build_nasa_power_point_url_contains_frozen_scope() -> None:
    built = build_nasa_power_point_url(NASA_POWER_POINTS["POWER_A"])
    assert "20150101" in built
    assert "20241231" in built
    assert "ALLSKY_SFC_SW_DWN" in built


def test_download_nasa_power_d103_points_writes_files(tmp_path: Path) -> None:
    def fake_opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        return _FakeResponse(b'{"mock": true}')

    paths = download_nasa_power_d103_points(tmp_path / "raw", opener=fake_opener)
    assert len(paths) == 3
    assert all(path.is_file() for path in paths)