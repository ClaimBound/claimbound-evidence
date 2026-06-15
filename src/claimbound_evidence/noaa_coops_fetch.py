# SPDX-License-Identifier: Apache-2.0
"""Download NOAA CO-OPS D-131 payloads in API-compliant chunks.

NOAA's Data API limits many products (including hourly_height) to 365 days per
request. D-131 spans 2018-01-01..2024-12-31, so operators must fetch by year (or
smaller windows) and merge payloads locally outside the repository.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable


NOAA_COOPS_D131_STATIONS: tuple[str, ...] = ("8518750", "9414290", "8638610")
NOAA_COOPS_D131_BEGIN = date(2018, 1, 1)
NOAA_COOPS_D131_END = date(2024, 12, 31)
NOAA_COOPS_API_BASE = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
NOAA_COOPS_APPLICATION = "NOS.COOPS.TAC.WL"


@dataclass(frozen=True)
class NoaaCoopsFetchConfig:
    station: str
    product: str
    begin: date
    end: date
    datum: str = "MLLW"
    time_zone: str = "gmt"
    units: str = "metric"
    interval: str | None = None
    application: str = NOAA_COOPS_APPLICATION


def year_chunks(begin: date, end: date) -> list[tuple[date, date]]:
    if begin > end:
        raise ValueError("begin must be <= end")

    chunks: list[tuple[date, date]] = []
    for year in range(begin.year, end.year + 1):
        chunk_start = date(year, 1, 1) if year > begin.year else begin
        chunk_end = date(year, 12, 31) if year < end.year else end
        chunks.append((chunk_start, chunk_end))
    return chunks


def build_datagetter_url(config: NoaaCoopsFetchConfig, chunk_begin: date, chunk_end: date) -> str:
    params: dict[str, str] = {
        "product": config.product,
        "application": config.application,
        "begin_date": chunk_begin.strftime("%Y%m%d"),
        "end_date": chunk_end.strftime("%Y%m%d"),
        "datum": config.datum,
        "station": config.station,
        "time_zone": config.time_zone,
        "units": config.units,
        "format": "json",
    }
    if config.product == "predictions":
        params["interval"] = config.interval or "h"
    query = urllib.parse.urlencode(params)
    return f"{NOAA_COOPS_API_BASE}?{query}"


def merge_hourly_height_payloads(payloads: list[dict[str, object]]) -> dict[str, object]:
    if not payloads:
        raise ValueError("hourly_height payloads must not be empty")

    merged_data: list[object] = []
    metadata: object | None = None
    for payload in payloads:
        if "error" in payload:
            raise ValueError(str(payload["error"]))
        if metadata is None and "metadata" in payload:
            metadata = payload["metadata"]
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValueError("hourly_height payload missing data list")
        merged_data.extend(data)

    out: dict[str, object] = {"data": merged_data}
    if metadata is not None:
        out["metadata"] = metadata
    return out


def merge_predictions_payloads(payloads: list[dict[str, object]]) -> dict[str, object]:
    if not payloads:
        raise ValueError("predictions payloads must not be empty")

    merged_predictions: list[object] = []
    for payload in payloads:
        if "error" in payload:
            raise ValueError(str(payload["error"]))
        predictions = payload.get("predictions")
        if not isinstance(predictions, list):
            raise ValueError("predictions payload missing predictions list")
        merged_predictions.extend(predictions)

    return {"predictions": merged_predictions}


def merge_product_payloads(product: str, payloads: list[dict[str, object]]) -> dict[str, object]:
    if product == "hourly_height":
        return merge_hourly_height_payloads(payloads)
    if product == "predictions":
        return merge_predictions_payloads(payloads)
    raise ValueError(f"unsupported NOAA product {product!r}")


def default_fetch_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "ClaimBound-noaa-fetch/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NOAA HTTP {exc.code} for {url}: {detail}") from exc

    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"NOAA response is not a JSON object: {url}")
    return payload


def fetch_product_payload(
    config: NoaaCoopsFetchConfig,
    *,
    fetch_json: Callable[[str], dict[str, object]] = default_fetch_json,
) -> dict[str, object]:
    chunk_payloads: list[dict[str, object]] = []
    for chunk_begin, chunk_end in year_chunks(config.begin, config.end):
        url = build_datagetter_url(config, chunk_begin, chunk_end)
        chunk_payloads.append(fetch_json(url))
    return merge_product_payloads(config.product, chunk_payloads)


def write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def fetch_d131_station_payloads(
    station: str,
    out_dir: Path,
    *,
    begin: date = NOAA_COOPS_D131_BEGIN,
    end: date = NOAA_COOPS_D131_END,
    fetch_json: Callable[[str], dict[str, object]] = default_fetch_json,
) -> list[Path]:
    written: list[Path] = []
    for product, suffix in (("hourly_height", "observed"), ("predictions", "predictions")):
        payload = fetch_product_payload(
            NoaaCoopsFetchConfig(
                station=station,
                product=product,
                begin=begin,
                end=end,
            ),
            fetch_json=fetch_json,
        )
        written.append(write_json(out_dir / f"{station}_{suffix}.json", payload))
    return written


__all__ = [
    "NOAA_COOPS_API_BASE",
    "NOAA_COOPS_D131_BEGIN",
    "NOAA_COOPS_D131_END",
    "NOAA_COOPS_D131_STATIONS",
    "NoaaCoopsFetchConfig",
    "build_datagetter_url",
    "default_fetch_json",
    "fetch_d131_station_payloads",
    "fetch_product_payload",
    "merge_hourly_height_payloads",
    "merge_predictions_payloads",
    "merge_product_payloads",
    "write_json",
    "year_chunks",
]
