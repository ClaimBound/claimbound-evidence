# SPDX-License-Identifier: Apache-2.0
"""``capture``: a JSON fragment describing the environment and input files, for a record ``outcome``.

It reads only the files it is asked to hash (inside the current directory) and no environment variable values.
Nothing is executed.
"""

from __future__ import annotations

import hashlib
import platform
import sys
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path
from typing import Any

from .errors import InputError, io_guard

_CHUNK = 1 << 20


def _version() -> str:
    try:
        return metadata.version("protocolith")
    except metadata.PackageNotFoundError:  # running from a source tree that is not installed
        return "unknown"


def environment() -> dict[str, str]:
    return {
        "machine": platform.machine(),
        "platform": sys.platform,
        "protocolith": _version(),
        "python": platform.python_version(),
    }


def describe_file(name: str, base: Path) -> dict[str, Any]:
    """Relative path, size and sha256 of a regular file inside ``base`` (symbolic links are resolved first)."""
    with io_guard():
        root = base.resolve()
        path = (root / name).resolve()
        try:
            relative = path.relative_to(root)
        except ValueError:
            raise InputError("BAD_PATH", f"{name}: the file is outside the current directory") from None
        if not path.is_file():
            raise InputError("BAD_PATH", f"{name}: not an existing regular file")
        digest = hashlib.sha256()
        size = 0
        with open(path, "rb") as handle:
            while chunk := handle.read(_CHUNK):
                digest.update(chunk)
                size += len(chunk)
    return {"path": relative.as_posix(), "sha256": digest.hexdigest(), "size": size}


def capture(files: Iterable[str] = (), *, env: bool = False, base: Path | None = None) -> dict[str, Any]:
    """The fragment ``{"environment": ..., "inputs": [...]}``; the environment is included with ``env`` or when no file is named."""
    names = list(files)
    here = base or Path.cwd()
    fragment: dict[str, Any] = {"inputs": [describe_file(name, here) for name in names]}
    if env or not names:
        fragment["environment"] = environment()
    return fragment
