#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Write a translation template for the atlas: every UI key of ``atlas_i18n/en.json`` with an empty value.

Fill in the values (and ``_name``, the language's own name), save the file as ``<code>.json`` and pass its folder to
``protocolith atlas --i18n DIR``. Empty values fall back to English.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from protocolith.core.atlas import english_catalog  # noqa: E402


def build_template() -> dict[str, str]:
    return dict.fromkeys(english_catalog(), "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, metavar="FILE", help="Write here instead of standard output.")
    args = parser.parse_args(argv)
    text = json.dumps(build_template(), indent=2, ensure_ascii=False) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
