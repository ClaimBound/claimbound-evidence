#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run or block the EEA AQ D-001 manual-track readiness check."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Iterable


TRACK_ID = "EEA_AQ_D001"
SCHEMA = "claimbound_eea_aq_d001_manual_summary_v1"
API_BASE = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
DOWNLOAD_PAGE = "https://aqportal.discomap.eea.europa.eu/download-data/"
WEBAPP_URL = "https://eeadmz1-downloads-webapp.azurewebsites.net/"
SWAGGER_JSON_URL = f"{API_BASE}/swagger/v1/swagger.json"
POLLUTANT_PM10_URI = "http://dd.eionet.europa.eu/vocabulary/aq/pollutant/5"
EXPECTED_COUNTRIES = ("BE", "DE", "NL")
START_DATE = date(2018, 1, 1)
END_DATE = date(2024, 12, 31)
MIN_COVERAGE = 0.85


@dataclass(frozen=True)
class FileSummary:
    path: str
    rows: int
    columns: list[str]
    sampling_col: str | None
    country_col: str | None
    city_col: str | None
    pollutant_col: str | None
    start_col: str | None
    value_col: str | None
    unit_col: str | None
    aggregation_col: str | None
    read_error: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--operator", default="local operator")
    parser.add_argument("--access-date", default=datetime.now(UTC).date().isoformat())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--probe-eea-api",
        action="store_true",
        help="Probe the live EEA API for the fixed manual-track manifest boundary.",
    )
    group.add_argument(
        "--raw-dir",
        type=Path,
        help="Local-only directory containing CSV or parquet payload files.",
    )
    group.add_argument(
        "--blocked-reason",
        help="Write an explicit blocked-source summary without inspecting raw payloads.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.probe_eea_api:
        summary = build_api_probe_blocked_summary(
            operator=args.operator,
            access_date=args.access_date,
        )
    elif args.raw_dir:
        summary = build_summary_from_paths(
            sorted(_iter_payload_files(args.raw_dir)),
            operator=args.operator,
            access_date=args.access_date,
            source_probe=None,
        )
    else:
        summary = build_blocked_summary(
            block_reason=str(args.blocked_reason),
            operator=args.operator,
            access_date=args.access_date,
            source_probe=None,
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.report.as_posix())
    print(summary["result"]["result_status"])
    return 0


def build_api_probe_blocked_summary(*, operator: str, access_date: str) -> dict[str, Any]:
    probe = probe_eea_api()
    missing = [
        country
        for country, item in probe["by_country"].items()
        if item["download_summary_number_files"] > 0 and item["url_list_count"] == 0
    ]
    if missing:
        reason = (
            "The fixed EEA PM10 E1a daily source reported downloadable files for "
            f"{', '.join(missing)}, but the reproducible URL-list endpoint returned "
            "zero URLs for those countries. The PM10 coverage gate cannot be run "
            "fairly from a complete public manifest."
        )
    else:
        reason = (
            "The manual PM10 coverage gate still requires local raw payload files. "
            "No raw payload manifest was provided to this public run."
        )
    return build_blocked_summary(
        block_reason=reason,
        operator=operator,
        access_date=access_date,
        source_probe=probe,
    )


def probe_eea_api() -> dict[str, Any]:
    swagger = _fetch_json(SWAGGER_JSON_URL)
    paths = sorted(str(path) for path in swagger.get("paths", {}))
    combined_payload = _fixed_api_payload(list(EXPECTED_COUNTRIES))
    combined_summary = _post_json("/DownloadSummary", combined_payload)
    combined_urls = _post_csv_urls("/ParquetFile/urls", combined_payload)

    by_country: dict[str, Any] = {}
    for country in EXPECTED_COUNTRIES:
        payload = _fixed_api_payload([country])
        summary = _post_json("/DownloadSummary", payload)
        urls = _post_csv_urls("/ParquetFile/urls", payload)
        by_country[country] = {
            "download_summary_number_files": int(summary.get("numberFiles", 0)),
            "download_summary_size": int(summary.get("size", 0)),
            "url_list_count": len(urls),
        }

    return {
        "probe_type": "eea_api_manifest_probe",
        "api_base": API_BASE,
        "swagger_json_url": SWAGGER_JSON_URL,
        "swagger_paths_present": paths,
        "fixed_request": _fixed_scope(),
        "combined_download_summary": combined_summary,
        "combined_url_list_count": len(combined_urls),
        "combined_url_country_counts": _url_country_counts(combined_urls),
        "by_country": by_country,
        "raw_payload_committed": False,
        "raw_payload_policy": "No raw EEA parquet payloads or URL manifests are committed.",
    }


def build_summary_from_paths(
    paths: Iterable[Path],
    *,
    operator: str,
    access_date: str,
    source_probe: dict[str, Any] | None,
) -> dict[str, Any]:
    file_summaries: list[FileSummary] = []
    records: list[dict[str, Any]] = []
    for path in paths:
        loaded_records, summary = _read_payload_file(path)
        file_summaries.append(summary)
        records.extend(loaded_records)
    return build_summary_from_records(
        records,
        file_summaries=file_summaries,
        operator=operator,
        access_date=access_date,
        source_probe=source_probe,
    )


def build_summary_from_records(
    records: Iterable[dict[str, Any]],
    *,
    file_summaries: list[FileSummary],
    operator: str,
    access_date: str,
    source_probe: dict[str, Any] | None,
) -> dict[str, Any]:
    expected_days = (END_DATE - START_DATE).days + 1
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}

    for record in records:
        country = _country(record)
        sampling_point = str(record.get("samplingpoint", "")).strip()
        pollutant = str(record.get("pollutant", "")).strip()
        when = _parse_date(record.get("start"))
        value = record.get("value")
        if country not in EXPECTED_COUNTRIES:
            continue
        if not _is_pm10(pollutant):
            continue
        if not sampling_point or when is None or not (START_DATE <= when <= END_DATE):
            continue
        if value in {None, ""}:
            continue
        key = (country, str(record.get("city", "")).strip(), sampling_point)
        item = grouped.setdefault(
            key,
            {
                "country": country,
                "city": str(record.get("city", "")).strip(),
                "samplingpoint": sampling_point,
                "dates": set(),
                "row_count": 0,
                "unit_values": set(),
            },
        )
        item["dates"].add(when)
        item["row_count"] += 1
        unit = str(record.get("unit", "")).strip()
        if unit:
            item["unit_values"].add(unit)

    coverage_rows: list[dict[str, Any]] = []
    for item in grouped.values():
        dates = sorted(item["dates"])
        observed_days = len(dates)
        coverage_ratio = observed_days / expected_days
        coverage_rows.append(
            {
                "country": item["country"],
                "city": item["city"],
                "samplingpoint": item["samplingpoint"],
                "observed_days": observed_days,
                "row_count": item["row_count"],
                "first_date": dates[0].isoformat() if dates else "",
                "last_date": dates[-1].isoformat() if dates else "",
                "expected_days": expected_days,
                "coverage_ratio": round(coverage_ratio, 6),
                "eligible": coverage_ratio >= MIN_COVERAGE,
                "unit_values": sorted(item["unit_values"])[:5],
            }
        )
    coverage_rows.sort(key=lambda row: (row["country"], row["city"], row["samplingpoint"]))

    selected_rows: list[dict[str, Any]] = []
    by_country: dict[str, Any] = {}
    for country in EXPECTED_COUNTRIES:
        country_rows = [row for row in coverage_rows if row["country"] == country]
        eligible_rows = [row for row in country_rows if row["eligible"]]
        selected = eligible_rows[:5]
        selected_rows.extend(selected)
        by_country[country] = {
            "sampling_points_seen": len({row["samplingpoint"] for row in country_rows}),
            "eligible_sampling_points": len({row["samplingpoint"] for row in eligible_rows}),
            "selected_sampling_points": [row["samplingpoint"] for row in selected],
            "gate_passed": len(selected) >= 5,
        }

    if not coverage_rows:
        status = "BLOCKED_SOURCE"
        reason = "No usable PM10 daily records were parsed under the fixed manual protocol."
    elif all(item["gate_passed"] for item in by_country.values()):
        status = "PASSED_UNDER_PROTOCOL"
        reason = "All fixed countries have at least five eligible PM10 daily sampling points."
    else:
        status = "INSUFFICIENT_COVERAGE"
        reason = "At least one fixed country has fewer than five eligible PM10 daily sampling points."

    summary = _base_summary(operator=operator, access_date=access_date, source_probe=source_probe)
    summary.update(
        {
            "file_summaries": [_file_summary_dict(item) for item in file_summaries],
            "station_coverage": coverage_rows,
            "selected_sampling_points": selected_rows,
            "by_country": by_country,
            "result": {"result_status": status, "reason": reason},
        }
    )
    return summary


def build_blocked_summary(
    *,
    block_reason: str,
    operator: str,
    access_date: str,
    source_probe: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = _base_summary(operator=operator, access_date=access_date, source_probe=source_probe)
    summary.update(
        {
            "block_reason": block_reason,
            "by_country": {},
            "file_summaries": [],
            "station_coverage": [],
            "selected_sampling_points": [],
            "result": {"result_status": "BLOCKED_SOURCE", "reason": block_reason},
        }
    )
    return summary


def _base_summary(*, operator: str, access_date: str, source_probe: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "track_id": TRACK_ID,
        "operator": operator,
        "access_date": access_date,
        "record_type": "source_audit",
        "claim_type": "manual_track_source_readiness",
        "source": {
            "name": "EEA Air Quality Download Service",
            "download_page": DOWNLOAD_PAGE,
            "web_application": WEBAPP_URL,
            "api_swagger_json": SWAGGER_JSON_URL,
            "raw_payload_committed": False,
        },
        "fixed_scope": _fixed_scope(),
        "source_probe": source_probe,
        "raw_payload_policy": "Raw EEA payload files stay outside the public repository.",
        "claim_boundary": (
            "EEA AQ D-001 reports only manual-track source-readiness and PM10 daily "
            "coverage status under the fixed protocol."
        ),
        "known_limitations": [
            "No air-quality forecasting claim is made.",
            "No health-impact claim is made.",
            "No deployment or production suitability claim is made.",
            "No raw EEA payload files are committed.",
        ],
    }


def _fixed_scope() -> dict[str, Any]:
    return {
        "dataset": "Primary validated data (E1a)",
        "dataset_code": 2,
        "pollutant": "PM10",
        "pollutant_uri": POLLUTANT_PM10_URI,
        "countries": list(EXPECTED_COUNTRIES),
        "period": f"{START_DATE.isoformat()}..{END_DATE.isoformat()}",
        "aggregation": "day",
        "coverage_gate": "at least 85 percent daily coverage per sampling point",
        "selection_rule": (
            "first five eligible sampling points per country after sorting by "
            "country code, city/locality if available, and sampling point ID"
        ),
    }


def _fixed_api_payload(countries: list[str]) -> dict[str, Any]:
    return {
        "countries": countries,
        "cities": [],
        "pollutants": [POLLUTANT_PM10_URI],
        "dataset": 2,
        "source": "Website",
        "method": None,
        "dateTimeStart": f"{START_DATE.isoformat()}T00:00:00.000Z",
        "dateTimeEnd": f"{END_DATE.isoformat()}T23:59:59.000Z",
        "aggregationType": "day",
        "email": None,
        "compress": True,
    }


def _iter_payload_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".csv", ".parquet"}:
            yield path


def _read_payload_file(path: Path) -> tuple[list[dict[str, Any]], FileSummary]:
    try:
        if path.suffix.lower() == ".csv":
            rows, columns = _read_csv_payload(path)
        elif path.suffix.lower() == ".parquet":
            rows, columns = _read_parquet_payload(path)
        else:
            rows, columns = [], []
    except Exception as exc:  # noqa: BLE001 - the report must preserve read blockers.
        return [], FileSummary(
            path=path.as_posix(),
            rows=0,
            columns=[],
            sampling_col=None,
            country_col=None,
            city_col=None,
            pollutant_col=None,
            start_col=None,
            value_col=None,
            unit_col=None,
            aggregation_col=None,
            read_error=repr(exc),
        )

    sampling_col = _find_col(columns, ("Samplingpoint", "SamplingPoint", "sampling point", "samplingpoint"))
    country_col = _find_col(columns, ("Country", "CountryCode", "country code", "country"))
    city_col = _find_col(columns, ("City", "Locality", "municipality", "city"))
    pollutant_col = _find_col(columns, ("Pollutant", "pollutant", "component", "parameter"))
    start_col = _find_col(columns, ("Start", "DatetimeBegin", "begin", "date", "time", "start"))
    value_col = _find_col(columns, ("Value", "Concentration", "result", "value"))
    unit_col = _find_col(columns, ("Unit", "unit"))
    aggregation_col = _find_col(columns, ("AggType", "aggregation", "type", "frequency"))

    normalized: list[dict[str, Any]] = []
    if sampling_col and pollutant_col and start_col and value_col:
        for row in rows:
            normalized.append(
                {
                    "samplingpoint": row.get(sampling_col),
                    "country": row.get(country_col) if country_col else None,
                    "city": row.get(city_col) if city_col else "",
                    "pollutant": row.get(pollutant_col),
                    "start": row.get(start_col),
                    "value": row.get(value_col),
                    "unit": row.get(unit_col) if unit_col else "",
                    "aggregation": row.get(aggregation_col) if aggregation_col else "",
                }
            )

    return normalized, FileSummary(
        path=path.as_posix(),
        rows=len(rows),
        columns=columns,
        sampling_col=sampling_col,
        country_col=country_col,
        city_col=city_col,
        pollutant_col=pollutant_col,
        start_col=start_col,
        value_col=value_col,
        unit_col=unit_col,
        aggregation_col=aggregation_col,
    )


def _read_csv_payload(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def _read_parquet_payload(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyarrow is required to inspect parquet payloads") from exc
    table = pq.read_table(path)
    rows = table.to_pylist()
    return rows, list(table.schema.names)


def _country(record: dict[str, Any]) -> str:
    explicit = str(record.get("country") or "").upper().strip()
    if explicit:
        return explicit[:2]
    sampling = str(record.get("samplingpoint") or "").upper()
    match = re.search(r"(?:^|[^A-Z])(BE|DE|NL)(?:[^A-Z]|$)", sampling)
    return match.group(1) if match else sampling[:2]


def _is_pm10(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"pm10", "5", POLLUTANT_PM10_URI.lower()}


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _find_col(columns: Iterable[str], names: Iterable[str]) -> str | None:
    columns = list(columns)
    lookup = {_norm_col(column): column for column in columns}
    for name in names:
        if _norm_col(name) in lookup:
            return lookup[_norm_col(name)]
    for column in columns:
        if any(_norm_col(name) in _norm_col(column) for name in names):
            return column
    return None


def _norm_col(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ClaimBound-EEA-manual-track/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _post(path, payload, accept="application/json")
    return json.loads(data.decode("utf-8"))


def _post_csv_urls(path: str, payload: dict[str, Any]) -> list[str]:
    try:
        data = _post(path, payload, accept="text/csv")
    except urllib.error.HTTPError:
        return []
    text = data.decode("utf-8-sig")
    if not text.strip():
        return []
    return [row["ParquetFileUrl"] for row in csv.DictReader(text.splitlines()) if row.get("ParquetFileUrl")]


def _post(path: str, payload: dict[str, Any], *, accept: str) -> bytes:
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": accept,
            "content-type": "application/json",
            "user-agent": "ClaimBound-EEA-manual-track/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _url_country_counts(urls: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for url in urls:
        match = re.search(r"/(BE|DE|NL)/", url)
        if match:
            counts[match.group(1)] += 1
    return dict(sorted(counts.items()))


def _file_summary_dict(summary: FileSummary) -> dict[str, Any]:
    return {
        "path": summary.path,
        "rows": summary.rows,
        "columns": summary.columns,
        "sampling_col": summary.sampling_col,
        "country_col": summary.country_col,
        "city_col": summary.city_col,
        "pollutant_col": summary.pollutant_col,
        "start_col": summary.start_col,
        "value_col": summary.value_col,
        "unit_col": summary.unit_col,
        "aggregation_col": summary.aggregation_col,
        "read_error": summary.read_error,
    }


if __name__ == "__main__":
    raise SystemExit(main())
