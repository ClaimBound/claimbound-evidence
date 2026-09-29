# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_reference_is_up_to_date() -> None:
    module = _load("gen_cli_reference")
    committed = (REPO_ROOT / "docs" / "CLI.md").read_text(encoding="utf-8")
    assert committed == module.build_reference(), "run: python scripts/gen_cli_reference.py"


def test_rewrite_links_maps_copied_docs_and_github_targets() -> None:
    module = _load("build_docs_site")
    text = (
        "[a](RESULT_STATUS.md#reproduction-levels) [b](../CONTRIBUTING.md) "
        "[c](external_verification/README.md) ![d](assets/claimbound_workflow.svg) "
        "[e](https://example.org/x) [f](#local)"
    )
    new, unresolved = module.rewrite_links(text, "docs/GETTING_STARTED.md")

    assert unresolved == []
    assert "[a](RESULT_STATUS.md#reproduction-levels)" in new
    assert "[b](CONTRIBUTING.md)" in new
    assert f"[c]({module.GITHUB}/blob/main/docs/external_verification/README.md)" in new
    assert f"![d]({module.RAW}/docs/assets/claimbound_workflow.svg)" in new
    assert "[e](https://example.org/x)" in new
    assert "[f](#local)" in new


def test_rewrite_links_reports_missing_targets() -> None:
    module = _load("build_docs_site")
    _, unresolved = module.rewrite_links("[x](does/not/exist.md)", "docs/GETTING_STARTED.md")

    assert unresolved == ["docs/GETTING_STARTED.md: does/not/exist.md"]


def test_docs_site_source_tree_builds_without_unresolved_links(tmp_path: Path) -> None:
    module = _load("build_docs_site")
    unresolved = module.build(tmp_path / "site_src")

    assert unresolved == []
    assert (tmp_path / "site_src" / "index.md").is_file()
    assert (tmp_path / "site_src" / "assets" / "claimbound-mark.svg").is_file()
