# SPDX-License-Identifier: Apache-2.0
"""Cross-platform operator workflow orchestration for reruns and drift checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from claimbound_evidence.inspect import format_hash_lines, format_json_subset, hash_files, load_json, pick_fields
from claimbound_evidence.nasa_power_fetch import download_nasa_power_d103_points
from claimbound_evidence.nasa_power_prereg_runner import evaluate_nasa_power_prereg
from claimbound_evidence.noaa_coops_fetch import (
    NOAA_COOPS_D131_STATIONS,
    fetch_d131_station_payloads,
)
from claimbound_evidence.noaa_coops_prereg_runner import (
    build_negative_result_summary,
    evaluate_noaa_coops_prereg,
)
from claimbound_evidence.run_root import RunRootRequest, prepare_run_root


EEA_DRIFT_SUMMARY_KEYS = (
    "http_status",
    "final_url",
    "page_sha256",
    "rights_link_present",
    "direct_link_presence",
    "result_status",
)
EEA_DRIFT_COMPARE_KEYS = (
    "http_status",
    "final_url",
    "content_type",
    "page_sha256",
    "page_byte_size",
    "page_title",
    "rights_link_present",
    "direct_link_presence",
)


def _sha256_manifest(paths: list[Path]) -> str:
    import hashlib

    lines = []
    for path in sorted(paths, key=lambda item: item.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    payload = "\n".join(lines) + ("\n" if lines else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _gate_result_block(report: dict[str, Any]) -> dict[str, Any]:
    if "result" in report and isinstance(report["result"], dict):
        return report["result"]
    keys = (
        "source_audit_passed",
        "eligible_point_count",
        "eligible_windows",
        "overall_go_no_go",
        "result_status",
        "allowed_narrow_claim",
    )
    return {key: report[key] for key in keys if key in report}


def _print_compare(title: str, baseline: dict[str, Any], current: dict[str, Any]) -> None:
    print(f"=== {title} ===")
    print(format_json_subset(_gate_result_block(baseline)), end="")
    print("=== YOUR RUN ===")
    print(format_json_subset(_gate_result_block(current)), end="")


def resolve_or_create_run_dir(
    *,
    protocol_id: str,
    source_url: str,
    operator: str,
    root: Path,
    run_dir: Path | None,
) -> Path:
    if run_dir is not None:
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir.resolve()
    paths = prepare_run_root(
        RunRootRequest(
            protocol_id=protocol_id,
            operator=operator,
            source_url=source_url,
            root=root,
        )
    )
    return paths[0].resolve()


def rerun_nasa_d103(
    repo_root: Path,
    *,
    operator: str = "local operator",
    root: Path | None = None,
    run_dir: Path | None = None,
    baseline_path: Path | None = None,
) -> int:
    runs_root = root or Path.home() / "claimbound_runs"
    resolved_run_dir = resolve_or_create_run_dir(
        protocol_id="NASA_POWER_D103",
        source_url="https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        operator=operator,
        root=runs_root,
        run_dir=run_dir,
    )
    raw_dir = resolved_run_dir / "raw"
    reports_dir = resolved_run_dir / "reports"
    hashes_dir = resolved_run_dir / "hashes"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    hashes_dir.mkdir(parents=True, exist_ok=True)

    print(f"run_dir={resolved_run_dir.as_posix()}")
    downloaded = download_nasa_power_d103_points(raw_dir)
    hash_path = hashes_dir / "nasa_raw_sha256.txt"
    hash_path.write_text(format_hash_lines(hash_files(tuple(downloaded))), encoding="utf-8")
    print(f"hash_file={hash_path.as_posix()}")

    report_path = reports_dir / "nasa_power_d103_report.json"
    evaluation = evaluate_nasa_power_prereg(
        point_ids=["POWER_A", "POWER_B", "POWER_C"],
        json_paths=downloaded,
        pre_registration_doc_path=repo_root / "docs" / "protocols" / "NASA_POWER_D103_PREREG_CHARTER.md",
    )
    report_path.write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
    print(f"report={report_path.as_posix()}")

    baseline = load_json(
        baseline_path or repo_root / "artifacts" / "nasa_power_d103_real_run_summary.json"
    )
    _print_compare("BASELINE", baseline, evaluation)
    return 0


def rerun_noaa_d131(
    repo_root: Path,
    *,
    operator: str = "local operator",
    root: Path | None = None,
    run_dir: Path | None = None,
    baseline_path: Path | None = None,
) -> int:
    runs_root = root or Path.home() / "claimbound_runs"
    resolved_run_dir = resolve_or_create_run_dir(
        protocol_id="NOAA_COOPS_D131",
        source_url="https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
        operator=operator,
        root=runs_root,
        run_dir=run_dir,
    )
    raw_dir = resolved_run_dir / "raw"
    reports_dir = resolved_run_dir / "reports"
    hashes_dir = resolved_run_dir / "hashes"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    hashes_dir.mkdir(parents=True, exist_ok=True)

    print(f"run_dir={resolved_run_dir.as_posix()}")
    payload_paths: list[Path] = []
    for station in NOAA_COOPS_D131_STATIONS:
        payload_paths.extend(fetch_d131_station_payloads(station, raw_dir))
    hash_path = hashes_dir / "raw_sha256.txt"
    hash_path.write_text(format_hash_lines(hash_files(tuple(payload_paths))), encoding="utf-8")
    print(f"hash_file={hash_path.as_posix()}")

    observed = [raw_dir / f"{station}_observed.json" for station in NOAA_COOPS_D131_STATIONS]
    predictions = [raw_dir / f"{station}_predictions.json" for station in NOAA_COOPS_D131_STATIONS]
    manifest_sha = _sha256_manifest(observed + predictions)
    evaluation = evaluate_noaa_coops_prereg(
        station_ids=list(NOAA_COOPS_D131_STATIONS),
        observed_paths=observed,
        predictions_paths=predictions,
        pre_registration_doc_path=repo_root / "docs" / "protocols" / "NOAA_COOPS_D131_PREREG_CHARTER.md",
        external_payload_manifest_sha256=manifest_sha,
    )
    report_path = reports_dir / "noaa_coops_d131_report.json"
    summary_path = reports_dir / "noaa_coops_d131_summary.json"
    report_path.write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
    summary = build_negative_result_summary(evaluation, report_path=report_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"report={report_path.as_posix()}")
    print(f"summary={summary_path.as_posix()}")

    baseline = load_json(
        baseline_path or repo_root / "artifacts" / "noaa_coops_d131_negative_result_summary.json"
    )
    _print_compare("BASELINE GATE", baseline, summary)
    if "failed_gates" in summary:
        print("=== YOUR FAILED GATES ===")
        print(format_json_subset({"failed_gates": summary["failed_gates"]}), end="")
    return 0


def drift_eea_source_audit(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
    report_path: Path | None = None,
) -> int:
    baseline = baseline_path or repo_root / "artifacts" / "source_audit_d001_summary.json"
    report = report_path or repo_root / "artifacts" / "eea_source_audit_drift_check_summary.json"
    script = repo_root / "scripts" / "claimbound_run_eea_source_audit.py"
    report.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.call([sys.executable, str(script), "--report", str(report)], cwd=repo_root)
    if result != 0:
        return result

    baseline_data = load_json(baseline)
    print("=== BASELINE ===")
    print(format_json_subset(pick_fields(baseline_data, EEA_DRIFT_SUMMARY_KEYS)), end="")
    print("=== FRESH PROBE ===")
    fresh = load_json(report)
    print(format_json_subset(pick_fields(fresh, EEA_DRIFT_SUMMARY_KEYS)), end="")

    baseline_subset = pick_fields(load_json(baseline), EEA_DRIFT_COMPARE_KEYS)
    fresh_subset = pick_fields(fresh, EEA_DRIFT_COMPARE_KEYS)
    changed = [key for key in EEA_DRIFT_COMPARE_KEYS if baseline_subset.get(key) != fresh_subset.get(key)]
    print(f"changed_fields={','.join(changed) if changed else 'none'}")
    print(
        "note=source drift does not automatically invalidate the original card; "
        "record page_sha256 and marker fields in your issue comment."
    )
    return 0