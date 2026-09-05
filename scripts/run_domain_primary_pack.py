#!/usr/bin/env python3
"""Run verify+register for all seven topic manifests of one CB7K domain."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True, help="e.g. DOM052")
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--skip-registry-validation", action="store_true")
    args = parser.parse_args()
    domain = args.domain.lower()
    source = args.source_file if args.source_file.is_absolute() else ROOT / args.source_file
    if not source.is_file():
        raise SystemExit(f"missing source file: {source}")
    for track in range(1, 8):
        manifest = ROOT / "artifacts" / f"cb7k_{domain}_t{track:02d}_primary_claims.json"
        if not manifest.is_file():
            raise SystemExit(f"missing manifest: {manifest}")
        verify = [
            sys.executable,
            str(ROOT / "scripts/verify_primary_public_claim_group.py"),
            str(manifest),
            "--source-file",
            str(source),
        ]
        register = [
            sys.executable,
            str(ROOT / "scripts/register_primary_public_claim_group.py"),
            str(manifest),
        ]
        if args.skip_registry_validation:
            register.append("--skip-registry-validation")
        print(f"VERIFY {manifest.name}", flush=True)
        subprocess.check_call(verify, cwd=ROOT)
        print(f"REGISTER {manifest.name}", flush=True)
        subprocess.check_call(register, cwd=ROOT)
    print(f"DONE: {args.domain} verify+register complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
