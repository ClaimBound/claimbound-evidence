#!/usr/bin/env python3
"""Re-run the simulations and compare the output with the committed results, byte for byte.

Needs only Python 3 and numpy. Exit code 0: identical. Exit code 1: different (numpy or platform may differ;
the script then prints the largest numeric difference so you can judge for yourself).

    python3 reproduce.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = (("code/phantom_mr_sim.py", "results.json"), ("code/other_hedges.py", "results_other.json"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(value: object, prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            out.update(flatten(item, f"{prefix}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(flatten(item, f"{prefix}/{index}"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        out[prefix] = float(value)
    return out


def main() -> int:
    exit_code = 0
    with tempfile.TemporaryDirectory() as tmp:
        for script, committed in JOBS:
            out = Path(tmp) / committed
            subprocess.run([sys.executable, "-W", "ignore::RuntimeWarning", str(HERE / script), "--out", str(out)], check=True, stdout=subprocess.DEVNULL)
            same = sha256(out) == sha256(HERE / committed)
            print(f"{committed}: {'IDENTICAL' if same else 'DIFFERENT'}  sha256 {sha256(out)[:16]}")
            if not same:
                exit_code = 1
                a, b = flatten(json.loads(out.read_text())), flatten(json.loads((HERE / committed).read_text()))
                worst = max((abs(a[k] - b[k]) for k in a if k in b), default=0.0)
                print(f"  largest numeric difference: {worst:.3e}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
