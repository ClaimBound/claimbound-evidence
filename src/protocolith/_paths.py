# SPDX-License-Identifier: Apache-2.0
"""Small path helpers shared by the command line modules."""

from __future__ import annotations

import tempfile
from pathlib import Path


def home_dir() -> Path:
    """The user's home directory, or the temporary directory when none can be determined (for example in a bare CI step)."""
    try:
        return Path.home()
    except (RuntimeError, KeyError):
        return Path(tempfile.gettempdir())
