# SPDX-License-Identifier: Apache-2.0
"""JSON field extraction and file hashing for cross-platform operator workflows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object at top level")
    return data


def pick_fields(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    missing = [key for key in keys if key not in data]
    if missing:
        raise KeyError(f"missing keys: {', '.join(missing)}")
    return {key: data[key] for key in keys}


def format_json_subset(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_files(paths: tuple[Path, ...]) -> list[tuple[str, Path]]:
    lines: list[tuple[str, Path]] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        lines.append((sha256_file(path), path))
    return lines


def format_hash_lines(lines: list[tuple[str, Path]]) -> str:
    return "".join(f"{digest}  {path.as_posix()}\n" for digest, path in lines)