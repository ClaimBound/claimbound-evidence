# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("packaging_render", REPO_ROOT / "packaging" / "render.py")
assert spec and spec.loader
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)

MACOS_ARM = render.PLATFORMS[0]
LINUX_INTEL = render.PLATFORMS[3]


def _wheel(name: str) -> dict:
    return {"url": f"https://files.example/{name}", "hash": "sha256:" + "0" * 64}


def test_pick_wheel_prefers_exact_interpreter_and_lowest_platform() -> None:
    package = {
        "wheels": [
            _wheel("x-1-cp313-cp313-macosx_14_0_arm64.whl"),
            _wheel("x-1-cp313-cp313-macosx_11_0_arm64.whl"),
            _wheel("x-1-cp311-abi3-macosx_11_0_arm64.whl"),
            _wheel("x-1-cp312-cp312-macosx_11_0_arm64.whl"),
            _wheel("x-1-py3-none-any.whl"),
        ]
    }
    picked = render.pick_wheel(package, "3.13", MACOS_ARM[2], MACOS_ARM[3])

    assert picked["url"].endswith("cp313-cp313-macosx_11_0_arm64.whl")


def test_pick_wheel_uses_abi3_and_pure_python_fallbacks_and_rejects_other_platforms() -> None:
    abi3 = {"wheels": [_wheel("c-1-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl")]}
    pure = {"wheels": [_wheel("p-1-py3-none-any.whl")]}
    windows_only = {"wheels": [_wheel("w-1-cp313-cp313-win_amd64.whl")]}
    too_new = {"wheels": [_wheel("n-1-cp314-abi3-manylinux_2_17_x86_64.whl")]}

    assert render.pick_wheel(abi3, "3.13", LINUX_INTEL[2], LINUX_INTEL[3])
    assert render.pick_wheel(pure, "3.13", MACOS_ARM[2], MACOS_ARM[3])
    assert render.pick_wheel(windows_only, "3.13", LINUX_INTEL[2], LINUX_INTEL[3]) is None
    assert render.pick_wheel(too_new, "3.13", LINUX_INTEL[2], LINUX_INTEL[3]) is None


def test_render_all_fills_templates_from_the_lock_file(tmp_path: Path) -> None:
    lock = render.load_lock(REPO_ROOT / "uv.lock")
    info = {
        "version": "9.9.9",
        "sdist_sha256": "a" * 64,
        "wheel_url": "https://files.example/claimbound_evidence-9.9.9-py3-none-any.whl",
        "wheel_sha256": "b" * 64,
    }
    conda, formula = render.render_all(info, lock, "3.13", tmp_path)

    recipe = conda.read_text(encoding="utf-8")
    ruby = formula.read_text(encoding="utf-8")
    assert 'version: "9.9.9"' in recipe
    assert "version: ${{ version }}" in recipe
    assert "sha256: " + "a" * 64 in recipe
    assert 'version "9.9.9"' in ruby
    assert 'sha256 "' + "b" * 64 + '"' in ruby
    for name in render.runtime_closure(lock):
        assert f'resource "{name}" do' in ruby
    for text in (recipe, ruby):
        assert "$" not in text.replace("${{", "")
        assert "$$" not in text
