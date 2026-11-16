#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Thin wrapper for `protocolith probe`."""

from __future__ import annotations

import sys

from protocolith.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["probe", *sys.argv[1:]]))
