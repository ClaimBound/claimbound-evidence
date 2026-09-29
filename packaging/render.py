#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Render the conda-forge recipe and the Homebrew formula for a PyPI release.

Nothing is submitted anywhere: the output goes to ``packaging/build/`` (git-ignored) and is
copied by hand into the conda-forge staged-recipes pull request or the Homebrew tap.

    python packaging/render.py --version 0.4.8 [--python 3.13]

Hashes for the release come from the PyPI JSON API, so the release must be published first.
Dependency wheels for Homebrew come from ``uv.lock`` of the checked-out commit.
"""

from __future__ import annotations

import argparse
import json
import re
import tomllib
import urllib.request
from pathlib import Path
from string import Template

PACKAGING = Path(__file__).resolve().parent
REPO_ROOT = PACKAGING.parent
PROJECT = "claimbound-evidence"
WHEEL_RE = re.compile(r"^(?P<dist>.+?)-(?P<ver>[^-]+)(?:-(?P<build>\d[^-]*))?-(?P<py>[^-]+)-(?P<abi>[^-]+)-(?P<plat>[^-]+)\.whl$")

# Homebrew platforms and how their wheel tags look
PLATFORMS = (
    ("macos", "arm64", ("macosx",), ("arm64", "universal2")),
    ("macos", "intel", ("macosx",), ("x86_64", "universal2")),
    ("linux", "arm64", ("manylinux",), ("aarch64",)),
    ("linux", "intel", ("manylinux",), ("x86_64",)),
)


def fetch_release(version: str) -> dict[str, str]:
    url = f"https://pypi.org/pypi/{PROJECT}/{version}/json"
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed https URL
        data = json.load(response)
    files = {item["packagetype"]: item for item in data["urls"]}
    return {
        "version": version,
        "sdist_sha256": files["sdist"]["digests"]["sha256"],
        "wheel_url": files["bdist_wheel"]["url"],
        "wheel_sha256": files["bdist_wheel"]["digests"]["sha256"],
    }


def load_lock(path: Path) -> dict[str, dict]:
    return {package["name"]: package for package in tomllib.loads(path.read_text(encoding="utf-8"))["package"]}


def runtime_closure(lock: dict[str, dict], root: str = PROJECT) -> list[str]:
    seen: list[str] = []

    def walk(name: str) -> None:
        if name in seen:
            return
        seen.append(name)
        for dep in lock[name].get("dependencies", []):
            walk(dep["name"])

    walk(root)
    return [name for name in seen if name != root]


def _version_key(tag: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", tag)) or (0,)


def wheel_score(filename: str, python: str, os_tags: tuple[str, ...], arches: tuple[str, ...]) -> tuple | None:
    """Return a sort key (lower is better) when the wheel fits, otherwise None."""
    match = WHEEL_RE.match(filename)
    if not match:
        return None
    minor = int(python.split(".")[1])
    py_tags = match["py"].split(".")
    abi = match["abi"]
    if f"cp3{minor}" in py_tags and abi in (f"cp3{minor}", "abi3"):
        interpreter_rank = 0
    elif any(re.fullmatch(r"cp3(\d+)", tag) and int(tag[3:]) <= minor for tag in py_tags) and abi == "abi3":
        interpreter_rank = 1
    elif any(tag in ("py3", "py2.py3") for tag in py_tags) and abi == "none":
        interpreter_rank = 2
    else:
        return None
    platforms = match["plat"].split(".")
    if platforms == ["any"]:
        return (interpreter_rank, (0,))
    best: tuple[int, ...] | None = None
    for platform in platforms:
        if any(platform.startswith(os_tag) for os_tag in os_tags) and any(platform.endswith(arch) for arch in arches):
            key = _version_key(platform)
            if best is None or key < best:
                best = key
    return None if best is None else (interpreter_rank, best)


def pick_wheel(package: dict, python: str, os_tags: tuple[str, ...], arches: tuple[str, ...]) -> dict | None:
    scored = []
    for wheel in package.get("wheels", []):
        filename = wheel["url"].rsplit("/", 1)[-1]
        score = wheel_score(filename, python, os_tags, arches)
        if score is not None:
            scored.append((score, filename, wheel))
    return min(scored, key=lambda item: (item[0], item[1]))[2] if scored else None


def supported_platforms(lock: dict[str, dict], python: str) -> list[tuple[str, str, tuple[str, ...], tuple[str, ...]]]:
    """Platforms for which every runtime dependency has a matching wheel."""
    names = runtime_closure(lock)
    return [
        platform
        for platform in PLATFORMS
        if all(pick_wheel(lock[name], python, platform[2], platform[3]) for name in names)
    ]


def render_resources(lock: dict[str, dict], python: str) -> str:
    """Ruby resource blocks; identical wheels for several platforms are merged into one block."""
    platforms = supported_platforms(lock, python)
    blocks: list[str] = []
    for name in runtime_closure(lock):
        package = lock[name]
        per_platform = {
            (os_name, arch): pick_wheel(package, python, os_tags, arches)
            for os_name, arch, os_tags, arches in platforms
        }
        unique = {wheel["url"] for wheel in per_platform.values()}
        if len(unique) == 1:
            blocks.append(_resource(name, next(iter(per_platform.values())), indent=2))
            continue
        lines = [f'  resource "{name}" do']
        for os_name in ("macos", "linux"):
            arches = [arch for (os_, arch) in per_platform if os_ == os_name]
            if not arches:
                continue
            lines.append(f"    on_{os_name} do")
            for arch in arches:
                wheel = per_platform[(os_name, arch)]
                lines += [
                    f"      on_{'arm' if arch == 'arm64' else 'intel'} do",
                    f'        url "{wheel["url"]}", using: :nounzip',
                    f'        sha256 "{wheel["hash"].removeprefix("sha256:")}"',
                    "      end",
                ]
            lines.append("    end")
        lines.append("  end")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_unsupported(lock: dict[str, dict], python: str) -> str:
    supported = {(os_name, arch) for os_name, arch, *_ in supported_platforms(lock, python)}
    checks = []
    for os_name, arch, *_ in PLATFORMS:
        if (os_name, arch) in supported:
            continue
        condition = f"OS.{'mac' if os_name == 'macos' else 'linux'}? && Hardware::CPU.{'intel' if arch == 'intel' else 'arm'}?"
        checks.append(f'    odie "claimbound-evidence: no dependency wheels for {os_name} {arch}" if {condition}')
    return "\n".join(checks)


def _resource(name: str, wheel: dict, indent: int) -> str:
    pad = " " * indent
    return "\n".join(
        [
            f'{pad}resource "{name}" do',
            f'{pad}  url "{wheel["url"]}", using: :nounzip',
            f'{pad}  sha256 "{wheel["hash"].removeprefix("sha256:")}"',
            f"{pad}end",
        ]
    )


def render_all(info: dict[str, str], lock: dict[str, dict], python: str, out: Path) -> list[Path]:
    (out / "conda-forge").mkdir(parents=True, exist_ok=True)
    (out / "homebrew").mkdir(parents=True, exist_ok=True)
    values = {
        **info,
        "python_formula": f"python@{python}",
        "python_bin": f"python{python}",
        "resources": render_resources(lock, python),
        "unsupported": render_unsupported(lock, python),
    }
    written = []
    for template, target in (
        (PACKAGING / "conda-forge" / "meta.yaml.tmpl", out / "conda-forge" / "meta.yaml"),
        (PACKAGING / "homebrew" / "claimbound-evidence.rb.tmpl", out / "homebrew" / "claimbound-evidence.rb"),
    ):
        target.write_text(Template(template.read_text(encoding="utf-8")).substitute(values), encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="published PyPI version, for example 0.4.8")
    parser.add_argument("--python", default="3.13", help="Homebrew Python formula minor version")
    parser.add_argument("--out", type=Path, default=PACKAGING / "build")
    args = parser.parse_args()
    lock = load_lock(REPO_ROOT / "uv.lock")
    for path in render_all(fetch_release(args.version), lock, args.python, args.out):
        print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
