#!/usr/bin/env python3
"""Re-run the simulations and compare the output with the committed results.

Needs only Python 3 and numpy. Each file is reported as IDENTICAL (the same bytes; this is what the author's machine gives),
EQUAL (every number agrees within 1e-9; floating-point rounding differs between platforms and numpy builds, a difference of
the order of 1e-15 is normal) or DIFFERENT (a number differs by more than that). Exit code 0 unless a file is DIFFERENT.

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
TOLERANCE = 1e-9
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
            if sha256(out) == sha256(HERE / committed):
                print(f"{committed}: IDENTICAL  sha256 {sha256(out)[:16]}")
                continue
            a, b = flatten(json.loads(out.read_text())), flatten(json.loads((HERE / committed).read_text()))
            worst = max((abs(a[k] - b[k]) / max(1.0, abs(b[k])) for k in a if k in b), default=0.0)
            same_shape = a.keys() == b.keys()
            verdict = "EQUAL" if same_shape and worst <= TOLERANCE else "DIFFERENT"
            print(f"{committed}: {verdict}  largest relative difference {worst:.3e}")
            if verdict == "DIFFERENT":
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
