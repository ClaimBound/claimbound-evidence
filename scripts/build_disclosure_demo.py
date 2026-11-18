#!/usr/bin/env python3
"""Build examples/selective_disclosure/: a private notebook ledger, its visibility policy, the public disclosure and atlas.

Everything is synthetic and deterministic (fixed clock). The private ledger is built in a temporary directory and is NOT
committed; what is committed is what a researcher would publish: `policy.json`, `disclosure.jsonl` and `atlas.html`, plus the
anchor statement (`anchor.txt`) and one revealed entry (`revealed_entry.json`) so that the verification commands in the README
can be run as they are.

    python3 scripts/build_disclosure_demo.py          # needs protocolith importable (pip install -e . or PYTHONPATH=src)
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from protocolith.core import (
    Store,
    anchor_head,
    build_atlas,
    build_disclosure,
    deviation,
    entries,
    freeze,
    issue,
    load_policy,
    record,
    sha256_hex,
)
from protocolith.core.atlas import write_atlas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "selective_disclosure"
HASH = "c" * 64
CARD = {
    "operator": "demo operator",
    "official_source_name": "Synthetic notebook",
    "official_source_url": "https://example.org/notebook",
    "domain": "synthetic research",
    "claim_type": "source_audit",
    "access_date": "2026-11-09",
    "source_rights_note": "Synthetic data written for this demonstration.",
    "raw_payload_manifest": "No raw payload committed.",
    "sanitized_report_path": "examples/selective_disclosure/README.md",
    "sanitized_report_sha256": HASH,
    "git_commit": "none",
    "runner_command": "manual",
    "verification_count": 1,
    "verification_level": "SINGLE_OPERATOR",
    "execution_mode": "MANUAL_NO_AI",
    "ai_assistance": "not used",
    "manual_review": "Synthetic.",
    "known_limitations": ["Synthetic demonstration."],
    "baseline_control_summary": "Baseline: none.",
    "public_claim_text": "Synthetic demonstration claim.",
    "public_claim_verbatim_quote": "Synthetic demonstration claim.",
    "public_claim_source_url": "https://example.org/notebook",
    "public_claim_locator": "section 1, paragraph 2",
    "public_claim_captured_at": "2026-11-09",
    "public_claim_source_sha256": HASH,
}
FAMILIES = {
    "SWEEP_MOMENTUM": ("parameter sweep, 12 settings", "private exploratory work", 12),
    "SWEEP_SPREADS": ("parameter sweep, 8 settings", "private exploratory work", 8),
    "STUDY_ROBUSTNESS": ("robustness study", "published as a summary", 4),
    "PAPER_CLAIM": ("the claim in the paper", "published in full", 1),
}
STATUSES = ("NEGATIVE_RESULT_UNDER_PROTOCOL", "NEGATIVE_RESULT_UNDER_PROTOCOL", "PASSED_UNDER_PROTOCOL")


def tick(index: int) -> object:
    stamp = f"2026-11-{10 + index // 24:02d}T{index % 24:02d}:00:00Z"
    return lambda: stamp


def build_private(store: Store) -> None:
    """A notebook of 25 experiments across four protocols; most of them are not meant to be published."""
    step = 0
    for name, (question, _, runs) in FAMILIES.items():
        body = {"gate": f"{name}: gate fixed before the runs", "protocol_id": name, "question": question, "version": "1"}
        freeze(store, body, clock=tick(step))  # type: ignore[arg-type]
        step += 1
        for run in range(runs):
            status = "PASSED_UNDER_PROTOCOL" if name == "PAPER_CLAIM" else STATUSES[(run * 7 + len(name)) % 3]
            entry = {
                "protocol_sha256": sha256_hex(body),
                "run_id": f"run-{run + 1:02d}",
                "status": status,
                "outcome": {"setting": str(run + 1), "metric": f"0.{(run * 37) % 100:02d}"},
                "sources": [{"id": "results.csv", "sha256": HASH}],
                "reproduction_level": "not independently reproduced",
                "claim_boundary": f"{name}, setting {run + 1} only.",
                "deviations": [],
                "card": CARD,
            }
            record(store, entry, clock=tick(step))  # type: ignore[arg-type]
            step += 1
    deviation(
        store,
        {"protocol_sha256": sha256_hex({"gate": "STUDY_ROBUSTNESS: gate fixed before the runs", "protocol_id": "STUDY_ROBUSTNESS", "question": "robustness study", "version": "1"}), "kind": "note", "description": "one setting re-run after a crash"},
        clock=tick(step),  # type: ignore[arg-type]
    )
    issue(store, len(entries(store)) - 2, clock=tick(step + 1))  # type: ignore[arg-type]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT / "public", ignore_errors=True)
    (OUT / "public").mkdir(parents=True, exist_ok=True)
    policy_path = OUT / "policy.json"
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / ".protocolith")
        build_private(store)
        anchor_head(store, clock=tick(90), write_head=OUT / "public" / "anchor.txt")  # type: ignore[arg-type]
        policy = load_policy(policy_path)
        found = build_disclosure(store, policy)
        (OUT / "public" / "disclosure.jsonl").write_bytes(found.data)
        page = build_atlas(store=store, policy=policy, title="Synthetic notebook (published view)")
        write_atlas(page, OUT / "public" / "atlas.html")
        ledger = entries(store)
        revealed = next(e for e in ledger if e["type"] == "record" and e["body"]["run_id"] == "run-03" and 13 < e["seq"] < 22)
        (OUT / "public" / "revealed_entry.json").write_text(json.dumps(revealed, indent=1) + "\n", encoding="utf-8")
        print(f"entries={len(ledger)} counts={found.counts} head={found.head_hash}")
        print(f"revealed entry seq={revealed['seq']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
