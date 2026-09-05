#!/usr/bin/env python3
"""Thin wrapper: build primary-source manifests for any CB7K domain inventory.

Delegates to build_first_700_primary_claim_manifests.py, which already accepts
--inventory and --domain. This entry point exists so domain packs do not depend
on the historical "first 700" script name.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build_first_700_primary_claim_manifests.py"


def main() -> int:
    sys.argv[0] = str(SCRIPT)
    runpy.run_path(str(SCRIPT), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
