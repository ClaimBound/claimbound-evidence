#!/usr/bin/env python3
"""Build the evidence folder of this example: freeze, anchor, reproduce, record, anchor, verify.

Run it from anywhere; it needs `protocolith` (0.7.0 or later, for `anchor`) importable and numpy installed:

    python3 build_ledger.py            # writes ./evidence/ (refuses to overwrite an existing one)

The order is the point. The protocol is frozen and anchored BEFORE the results are re-computed, and the record is added
afterwards. This is a retrospective record: the study itself was run and written up before this protocol was frozen, so the
ledger proves what existed at the times it shows, not that the analysis was planned earlier. See README.md.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
SOURCES = (
    "results.json",
    "results_other.json",
    "code/phantom_mr_sim.py",
    "code/other_hedges.py",
    "code/mechanism_check.py",
    "code/make_figures.py",
)
RUNNER = "import sys; from protocolith.cli import main; sys.exit(main())"


def sha(path: str) -> str:
    return hashlib.sha256((HERE / path).read_bytes()).hexdigest()


def plith(*args: str) -> str:
    proc = subprocess.run([sys.executable, "-c", RUNNER, *args], cwd=EVIDENCE, capture_output=True, text=True, check=False)
    print("$ protocolith", " ".join(args))
    print((proc.stdout + proc.stderr).rstrip())
    if proc.returncode != 0:
        raise SystemExit(f"command failed with exit code {proc.returncode}")
    return proc.stdout


def main() -> int:
    if EVIDENCE.exists():
        raise SystemExit(f"{EVIDENCE} exists; remove it first (a ledger is append-only, this script never edits one)")
    EVIDENCE.mkdir()
    plith("init")
    frozen = plith("freeze", "../protocol.json")
    protocol_sha = re.search(r"protocol_sha256=([0-9a-f]{64})", frozen)
    if protocol_sha is None:
        raise SystemExit("freeze did not print a protocol hash")
    plith("anchor", "--write-head", "anchor-after-freeze.txt")
    reproduced = subprocess.run([sys.executable, str(HERE / "reproduce.py")], capture_output=True, text=True, check=False)
    print(reproduced.stdout.rstrip())
    if reproduced.returncode != 0:
        raise SystemExit("reproduction differs from the committed results; refusing to record a pass")
    sums = {name: sha(name) for name in SOURCES}
    claim = "Rolling-hedge spread books look profitable on independent random walks while the tradable P&L is near zero."
    record = {
        "protocol_sha256": protocol_sha.group(1),
        "run_id": "run-1",
        "status": "PASSED_UNDER_PROTOCOL",
        "outcome": json.loads((HERE / "outcome.json").read_text(encoding="utf-8")),
        "sources": [{"id": name, "sha256": digest} for name, digest in sums.items()],
        "reproduction_level": "not independently reproduced",
        "claim_boundary": "Simulated independent random walks only, seed 20261015, 400 paths of 5000 hourly bars. "
        "Says nothing about real markets or about any investment result.",
        "deviations": [],
        "card": {
            "operator": "Rostyslav Shcherbyna",
            "official_source_name": "Monte-Neo paper sources (phantom-mean-reversion)",
            "official_source_url": "https://github.com/NeoZorK/Monte-Neo",
            "domain": "quantitative research",
            "claim_type": "source_audit",
            "access_date": "2026-11-18",
            "source_rights_note": "Own simulation code and output, MIT licence in the source repository; no third-party data.",
            "raw_payload_manifest": "No raw payload; the simulation generates its own random walks.",
            "sanitized_report_path": "examples/phantom_mean_reversion/results.json",
            "sanitized_report_sha256": sums["results.json"],
            "git_commit": "none",
            "runner_command": "python3 reproduce.py",
            "verification_count": 2,
            "verification_level": "SINGLE_OPERATOR",
            "execution_mode": "AUTOMATED_AI_ASSISTED",
            "ai_assistance": "An AI assistant copied the files and wrote the protocol, the reproduce script and this record; the operator reviewed them.",
            "manual_review": "The operator compared the table in the preprint with results.json.",
            "known_limitations": ["Retrospective record: the study predates this frozen protocol.", "Single operator.", "Simulation only."],
            "baseline_control_summary": "Control: the tradable P&L series of the same paths, which holds the previous hedge.",
            "public_claim_text": claim,
            "public_claim_verbatim_quote": claim,
            "public_claim_source_url": "https://github.com/NeoZorK/Monte-Neo",
            "public_claim_locator": "paper/phantom-mean-reversion, Table 1",
            "public_claim_captured_at": "2026-11-18",
            "public_claim_source_sha256": sums["results.json"],
        },
    }
    (EVIDENCE / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    plith("record", "record.json")
    plith("issue", "1")
    plith("verify-ledger")
    plith("anchor", "--write-head", "anchor-after-record.txt")
    plith("verify-ledger", "--anchors")
    plith("claim-check", "--seq", "1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
