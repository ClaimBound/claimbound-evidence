#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Thin wrapper for `claimbound probe`."""

from __future__ import annotations

import sys

from claimbound_evidence.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["probe", *sys.argv[1:]]))
