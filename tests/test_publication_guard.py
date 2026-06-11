# SPDX-License-Identifier: Apache-2.0
"""Publication guard for the ClaimBound foreground repository."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = (
    "mq" + "l5",
    "meta" + "trader",
    "neozork_" + "q" + "wc" + "_api",
    "/users/" + "rostsh",
    "tr" + "ading",
    "gr" + "ant",
    "cu" + "rsoragent",
    "co-authored-by: cu" + "rsor",
    "made with cu" + "rsor",
    "cursor" + ".com",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "neozork",
    "server",
    "src." + "mq" + "l5",
    "scripts." + "mq" + "l5",
)

TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".json", ".yml", ".yaml"}
RAW_PAYLOAD_SUFFIXES = {".csv", ".parquet", ".zip", ".jsonl", ".env", ".key", ".pem"}
RAW_PAYLOAD_DIR_NAMES = {"raw", "payloads", "data"}


def _text_files() -> list[Path]:
    out: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in {".git", ".venv", ".pytest_cache", "__pycache__", "dist", "build"} for part in path.parts):
            continue
        if path.is_dir():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE", "NOTICE"}:
            out.append(path)
    return out


def test_no_forbidden_public_tokens_or_ru_text() -> None:
    cyrillic = re.compile(r"[\u0400-\u04FF]")
    violations: list[str] = []
    for path in _text_files():
        rel = path.relative_to(REPO_ROOT)
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for token in FORBIDDEN_PATTERNS:
            if rel.as_posix() == "LICENSE" and token == "gr" + "ant":
                continue
            if token in lower:
                violations.append(f"{rel}: forbidden token {token!r}")
        if "_" + "RU" in text:
            violations.append(f"{rel}: internal RU suffix reference")
        if cyrillic.search(text):
            violations.append(f"{rel}: Cyrillic text")
    assert violations == []


def test_python_imports_stay_inside_open_foreground() -> None:
    violations: list[str] = []
    for path in sorted((REPO_ROOT / "src").rglob("*.py")) + sorted((REPO_ROOT / "scripts").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
    assert violations == []


def test_no_raw_payload_files_or_dirs_are_committed() -> None:
    violations: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in {".git", ".venv", ".pytest_cache", "__pycache__", "dist", "build"} for part in path.parts):
            continue
        if path.is_dir():
            if path.name.lower() in RAW_PAYLOAD_DIR_NAMES:
                violations.append(f"{path.relative_to(REPO_ROOT)}: raw payload directory")
            continue
        if path.suffix.lower() in RAW_PAYLOAD_SUFFIXES:
            violations.append(f"{path.relative_to(REPO_ROOT)}: raw payload-like suffix")
    assert violations == []


def test_public_artifacts_have_claim_boundary_and_no_raw_payloads() -> None:
    violations: list[str] = []
    for path in sorted((REPO_ROOT / "artifacts").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "claim_boundary" not in data:
            violations.append(f"{path.relative_to(REPO_ROOT)}: missing claim_boundary")
        text = json.dumps(data, sort_keys=True).lower()
        if '"raw_payload_committed": true' in text:
            violations.append(f"{path.relative_to(REPO_ROOT)}: raw_payload_committed true")
    assert violations == []
