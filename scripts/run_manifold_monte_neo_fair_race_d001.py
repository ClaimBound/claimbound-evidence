#!/usr/bin/env python3
"""Frozen runner: MANIFOLD_MONTE_NEO_FAIR_RACE_D001.

  uv run python scripts/run_manifold_monte_neo_fair_race_d001.py \\
    --out-dir artifacts/manifold_monte_neo_fair_race_d001
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from manifold_monte_neo_fair_race_peers import (
    manifold_type_a,
    manifold_type_b,
    manifold_type_c,
)


def _fingerprint() -> dict:
    chip = platform.processor()
    try:
        chip = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
    except Exception:  # noqa: BLE001
        pass
    return {
        "os": platform.platform(),
        "machine": platform.machine(),
        "chip": chip,
        "python": sys.version.split()[0],
        "cuda_peer_on_host": False if platform.machine() == "arm64" else "unknown",
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _bar_chart(path: Path, engines: list[str], vals: list[float], ylabel: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(engines, vals, color=["#2563eb", "#64748b"])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_charts(out: Path, summary: dict) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    engines = ["monte_neo", "manifoldbt"]
    paths = []
    p = out / "type_c_combos_per_s.png"
    _bar_chart(
        p,
        engines,
        [
            float(summary["type_c"]["monte_neo"].get("combos_per_s") or 0),
            float(summary["type_c"]["manifoldbt"].get("combos_per_s") or 0),
        ],
        "combos / s",
        "Type C sweep throughput (≤256, synthetic 50k bars)",
    )
    paths.append(p)
    p = out / "type_a_sims_per_s.png"
    _bar_chart(
        p,
        engines,
        [
            float(summary["type_a"]["monte_neo"].get("sims_per_s") or 0),
            float(summary["type_a"]["manifoldbt"].get("sims_per_s") or 0),
        ],
        "sims / s",
        "Type A return-path bootstrap (n=1000)",
    )
    paths.append(p)
    p = out / "type_b_scenarios_per_s.png"
    _bar_chart(
        p,
        engines,
        [
            float(summary["type_b"]["monte_neo"].get("scenarios_per_s") or 0),
            float(summary["type_b"]["manifoldbt"].get("scenarios_per_s") or 0),
        ],
        "scenarios / s",
        "Type B scenario / N-run throughput (n=1000)",
    )
    paths.append(p)
    return paths


def _markdown(summary: dict) -> str:
    c, a, b = summary["type_c"], summary["type_a"], summary["type_b"]
    return "\n".join(
        [
            "# MANIFOLD_MONTE_NEO_FAIR_RACE_D001 sanitized report",
            "",
            f"**result_status:** `{summary['result_status']}`",
            "",
            "## Hardware",
            "",
            "```json",
            json.dumps(summary["hardware"], indent=2),
            "```",
            "",
            "## Type C — sweep (gate)",
            "",
            "| engine | combos/s | ok |",
            "|---|---:|---|",
            f"| monte_neo | {c['monte_neo'].get('combos_per_s')} | {c['monte_neo'].get('ok')} |",
            f"| manifoldbt | {c['manifoldbt'].get('combos_per_s')} | {c['manifoldbt'].get('ok')} |",
            f"| gate_pass | | {c['gate_pass']} |",
            "",
            "## Type A — return-path bootstrap",
            "",
            "| engine | sims/s | ok |",
            "|---|---:|---|",
            f"| monte_neo | {a['monte_neo'].get('sims_per_s')} | {a['monte_neo'].get('ok')} |",
            f"| manifoldbt | {a['manifoldbt'].get('sims_per_s')} | {a['manifoldbt'].get('ok')} |",
            "",
            "## Type B — scenario / N-run",
            "",
            "| engine | scenarios/s | ok |",
            "|---|---:|---|",
            f"| monte_neo | {b['monte_neo'].get('scenarios_per_s')} | {b['monte_neo'].get('ok')} |",
            f"| manifoldbt | {b['manifoldbt'].get('scenarios_per_s')} | {b['manifoldbt'].get('ok')} |",
            "",
            "## Claim boundary",
            "",
            summary["claim_boundary"],
            "",
            "## Charts",
            "",
            "- `charts/type_c_combos_per_s.png`",
            "- `charts/type_a_sims_per_s.png`",
            "- `charts/type_b_scenarios_per_s.png`",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--bars", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Allow `scripts/` imports when run as uv run python scripts/...
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from monte_neo.fair_race import (
        return_path_bootstrap,
        run_type_b_scenarios,
        run_type_c_sweep,
        synthetic_ohlcv,
    )

    data = synthetic_ohlcv(args.bars, seed=args.seed)
    mn_c = run_type_c_sweep(n_bars=args.bars, combos=256, seed=args.seed)
    mn_c["combos_per_s"] = (
        float(mn_c["combos"]) / float(mn_c["elapsed_s"]) if mn_c.get("elapsed_s") else 0.0
    )
    mb_c = manifold_type_c(data, combos=256)
    rets = np.diff(np.log(data["close"].to_numpy(dtype=np.float64)))
    mn_a = return_path_bootstrap(rets, n_simulations=1000, seed=7)
    mb_a = manifold_type_a(data, n_sim=1000, seed=7)
    mn_b = run_type_b_scenarios(n_bars=args.bars, n_scenarios=1000, seed=args.seed)
    mb_b = manifold_type_b(data, n_scenarios=1000)

    type_c_pass = bool(
        mn_c.get("ok") and mb_c.get("ok") and mn_c["combos_per_s"] > mb_c["combos_per_s"]
    )
    type_a_pass = bool(mn_a.get("ok") and mb_a.get("ok"))
    overall = (
        "PASSED_UNDER_PROTOCOL"
        if (type_c_pass and type_a_pass)
        else "NEGATIVE_RESULT_UNDER_PROTOCOL"
    )

    summary = {
        "protocol_id": "MANIFOLD_MONTE_NEO_FAIR_RACE_D001",
        "protocol_version": "2026-09-12-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hardware": _fingerprint(),
        "pins": {
            "bars": args.bars,
            "seed": args.seed,
            "manifoldbt": mb_c.get("manifoldbt_version"),
        },
        "type_c": {"monte_neo": mn_c, "manifoldbt": mb_c, "gate_pass": type_c_pass},
        "type_a": {"monte_neo": mn_a, "manifoldbt": mb_a, "gate_pass": type_a_pass},
        "type_b": {"monte_neo": mn_b, "manifoldbt": mb_b},
        "result_status": overall,
        "claim_boundary": (
            "Under protocol MANIFOLD_MONTE_NEO_FAIR_RACE_D001 on recorded Apple Silicon "
            "hardware, comparing Monte-Neo (MIT) vs ManifoldBT Community CPU only. CUDA is "
            "not a peer. Type A/B/C are separate. Does not claim universal engine superiority."
        ),
    }
    charts = _write_charts(out_dir / "charts", summary)
    summary["charts"] = [c.name for c in charts]
    report = out_dir / "sanitized_report.json"
    report.write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    md = out_dir / "sanitized_report.md"
    md.write_text(_markdown(summary), encoding="utf-8")
    manifest = {
        "sanitized_report_json_sha256": _sha256_file(report),
        "sanitized_report_md_sha256": _sha256_file(md),
        "charts": {c.name: _sha256_file(c) for c in charts},
    }
    (out_dir / "raw_payload_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"result_status": overall, "out_dir": str(out_dir), **manifest}, indent=2))


if __name__ == "__main__":
    # Ensure sibling import works before main()
    _scripts = Path(__file__).resolve().parent
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    main()
