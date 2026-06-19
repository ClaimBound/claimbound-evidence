# SPDX-License-Identifier: Apache-2.0
"""Download frozen NASA POWER D-103 JSON payloads for operator reruns."""

from __future__ import annotations

import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from claimbound_evidence.nasa_power import NASA_POWER_PARAMETERS, NASA_POWER_POINTS, NasaPowerPoint


NASA_POWER_API_BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_D103_START = "20150101"
NASA_POWER_D103_END = "20241231"
DEFAULT_USER_AGENT = "ClaimBound-nasa-fetch/0.1"


def build_nasa_power_point_url(point: NasaPowerPoint) -> str:
    params = {
        "parameters": ",".join(NASA_POWER_PARAMETERS),
        "community": point.community,
        "longitude": str(point.longitude),
        "latitude": str(point.latitude),
        "start": NASA_POWER_D103_START,
        "end": NASA_POWER_D103_END,
        "format": "JSON",
    }
    return f"{NASA_POWER_API_BASE}?{urllib.parse.urlencode(params)}"


def download_nasa_power_point(
    point_id: str,
    out_path: Path,
    *,
    opener: Callable[..., object] | None = None,
) -> Path:
    point = NASA_POWER_POINTS[point_id]
    url = build_nasa_power_point_url(point)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    open_fn = opener or urllib.request.urlopen
    with open_fn(request, timeout=120) as response:
        payload = response.read()
    out_path.write_bytes(payload)
    return out_path


def download_nasa_power_d103_points(
    raw_dir: Path,
    *,
    opener: Callable[..., object] | None = None,
) -> list[Path]:
    paths: list[Path] = []
    for point_id in ("POWER_A", "POWER_B", "POWER_C"):
        paths.append(
            download_nasa_power_point(
                point_id,
                raw_dir / f"{point_id}.json",
                opener=opener,
            )
        )
    return paths