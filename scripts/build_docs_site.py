#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assemble the MkDocs source tree for the documentation site.

The site combines the hand-written pages in ``docs_site/`` with a fixed set of existing
repository documents. Links inside copied documents are rewritten: links to other copied
documents become site links, links to any other repository file become GitHub URLs.
Only documentation is published; there is no card browser here.

Usage: python scripts/build_docs_site.py [--out .docs_build]
Then:  mkdocs build --strict -d _site/docs
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/ClaimBound/claimbound-evidence"
RAW = "https://raw.githubusercontent.com/ClaimBound/claimbound-evidence/main"

# repository path -> file name in the site (flat)
COPIED = {
    "docs/CLAIMBOUND_IN_30_SECONDS.md": "CLAIMBOUND_IN_30_SECONDS.md",
    "docs/CLAIMBOUND_IN_5_MINUTES.md": "CLAIMBOUND_IN_5_MINUTES.md",
    "docs/START_WITHOUT_CODING.md": "START_WITHOUT_CODING.md",
    "docs/PLATFORM_SUPPORT.md": "PLATFORM_SUPPORT.md",
    "docs/GETTING_STARTED.md": "GETTING_STARTED.md",
    "docs/EVIDENCE_CARD.md": "EVIDENCE_CARD.md",
    "docs/RESULT_STATUS.md": "RESULT_STATUS.md",
    "docs/COMMON_MISREADINGS.md": "COMMON_MISREADINGS.md",
    "docs/INDEPENDENT_RERUN_WORKFLOW.md": "INDEPENDENT_RERUN_WORKFLOW.md",
    "docs/REVIEWER_PATH.md": "REVIEWER_PATH.md",
    "docs/GLOSSARY.md": "GLOSSARY.md",
    "docs/CLI.md": "CLI.md",
    "docs/PSEUDONYM_POLICY.md": "PSEUDONYM_POLICY.md",
    "docs/PLANNED_NOT_SHIPPED.md": "PLANNED_NOT_SHIPPED.md",
    "docs/ROADMAP_2026.md": "ROADMAP_2026.md",
    "CONTRIBUTING.md": "CONTRIBUTING.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "SECURITY.md": "SECURITY.md",
}
ASSETS = {
    "docs/assets/logo/claimbound-mark.svg": "assets/claimbound-mark.svg",
    "docs/assets/logo/claimbound-mark-32.png": "assets/favicon.png",
    "docs/assets/claimbound_workflow.svg": "assets/claimbound_workflow.svg",
}
IMAGE_SUFFIXES = {".svg", ".png", ".gif", ".jpg", ".jpeg"}
LINK = re.compile(r"(?<!\\)(\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")


def rewrite_links(text: str, source: str, root: Path = REPO_ROOT) -> tuple[str, list[str]]:
    """Rewrite relative links of a copied document; return the new text and unresolved links."""
    unresolved: list[str] = []
    source_dir = PurePosixPath(source).parent

    def replace(match: re.Match[str]) -> str:
        target = match.group(2)
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|//)", target, re.IGNORECASE):
            return match.group(0)
        path_part, _, fragment = target.partition("#")
        if not path_part:
            return match.group(0)
        resolved = PurePosixPath(*_normalise(source_dir / path_part))
        key = resolved.as_posix()
        suffix = f"#{fragment}" if fragment else ""
        if key in COPIED:
            new = COPIED[key] + suffix
        elif (root / key).exists():
            is_image = resolved.suffix.lower() in IMAGE_SUFFIXES
            if is_image:
                new = f"{RAW}/{key}"
            elif (root / key).is_dir():
                new = f"{GITHUB}/tree/main/{key}{suffix}"
            else:
                new = f"{GITHUB}/blob/main/{key}{suffix}"
        else:
            unresolved.append(f"{source}: {target}")
            return match.group(0)
        return f"{match.group(1)}{new}{match.group(3)}"

    return LINK.sub(replace, text), unresolved


def _normalise(path: PurePosixPath) -> list[str]:
    parts: list[str] = []
    for part in path.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return parts


def build(out: Path, root: Path = REPO_ROOT) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    unresolved: list[str] = []
    for page in sorted((root / "docs_site").glob("*.md")):
        shutil.copy(page, out / page.name)
    for source, name in COPIED.items():
        text = (root / source).read_text(encoding="utf-8")
        new_text, missing = rewrite_links(text, source, root)
        unresolved.extend(missing)
        (out / name).write_text(new_text, encoding="utf-8")
    for source, name in ASSETS.items():
        shutil.copy(root / source, out / name)
    return unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / ".docs_build")
    args = parser.parse_args()
    unresolved = build(args.out)
    for item in unresolved:
        print(f"unresolved link: {item}", file=sys.stderr)
    print(f"built {args.out}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
