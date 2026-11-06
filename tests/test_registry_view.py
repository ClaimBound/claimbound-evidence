# SPDX-License-Identifier: Apache-2.0
"""Tests for the deterministic static registry views."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

from claimbound_evidence.registry import load_registry
from claimbound_evidence.registry_view import (
    INDEX_REL,
    RegistryViewError,
    build_views,
    build_views_from_registry,
    check_views,
    slug,
    validate_registry_strict,
)

ROOT = Path(__file__).resolve().parents[1]
VOID = {"meta", "br", "link", "input", "img", "hr"}


class _Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.captions = 0
        self.scoped_th = 0

    def handle_starttag(self, tag, attrs):
        if tag == "caption":
            self.captions += 1
        if tag == "th" and (("scope", "col") in attrs or ("scope", "row") in attrs):
            self.scoped_th += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            self.errors.append(tag)


def test_committed_views_are_current() -> None:
    """--check mode: fails if docs/registry/views is stale."""
    assert check_views(ROOT) == []


def test_check_cli_exit_code() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "claimbound_build_registry_view.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_regeneration_is_deterministic() -> None:
    registry = load_registry(ROOT / INDEX_REL)
    shuffled = copy.deepcopy(registry)
    shuffled["cards"].reverse()
    assert build_views_from_registry(registry, ROOT) == build_views_from_registry(shuffled, ROOT)


def test_html_is_wellformed_self_contained_and_accessible() -> None:
    text = (ROOT / "docs/registry/views/index.html").read_text(encoding="utf-8")
    parser = _Balance()
    parser.feed(text)
    parser.close()
    assert parser.errors == []
    assert parser.stack == []
    assert parser.captions == 1
    assert parser.scoped_th > 0
    assert "prefers-color-scheme" in text
    assert "<noscript" not in text and "src=" not in text.replace("sources", "")
    assert "http://" not in text and "https://" not in text


def test_every_entry_links_card_json_and_resolves() -> None:
    registry = load_registry(ROOT / INDEX_REL)
    html_text = (ROOT / "docs/registry/views/index.html").read_text(encoding="utf-8")
    views = ROOT / "docs/registry/views"
    for entry in registry["cards"][:200]:
        href = "../../" + entry["path"][len("docs/"):]
        assert f'href="{href}"' in html_text
        assert (views / href).resolve().is_file()


def test_mismatch_with_card_json_fails_loudly() -> None:
    registry = load_registry(ROOT / INDEX_REL)
    bad = copy.deepcopy(registry)
    bad["cards"] = bad["cards"][:1]
    bad["card_count"] = 1
    bad["cards"][0]["result_status"] = "PASSED_UNDER_PROTOCOL"
    with pytest.raises(RegistryViewError):
        validate_registry_strict(bad, ROOT)


def test_missing_card_path_fails_loudly(tmp_path: Path) -> None:
    registry = load_registry(ROOT / INDEX_REL)
    bad = copy.deepcopy(registry)
    bad["cards"] = bad["cards"][:1]
    bad["card_count"] = 1
    (tmp_path / "docs/registry").mkdir(parents=True)
    (tmp_path / INDEX_REL).write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(RegistryViewError):
        build_views(tmp_path)


def test_slug_is_stable() -> None:
    assert slug("ai-product-evidence") == "ai-product-evidence"
    assert slug("open_data") == "open-data"
