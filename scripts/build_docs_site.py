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
GITHUB = "https://github.com/protocolith/protocolith"
RAW = "https://raw.githubusercontent.com/protocolith/protocolith/main"

# repository path -> file name in the site (flat)
COPIED = {
    "docs/PROTOCOLITH_IN_30_SECONDS.md": "PROTOCOLITH_IN_30_SECONDS.md",
    "docs/PROTOCOLITH_IN_5_MINUTES.md": "PROTOCOLITH_IN_5_MINUTES.md",
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
    # core documentation (flat names in the site; sources live in subfolders of docs/)
    "docs/getting-started/install.md": "getting-started-install.md",
    "docs/getting-started/first-record.md": "getting-started-first-record.md",
    "docs/getting-started/local-experiments.md": "getting-started-local-experiments.md",
    "docs/getting-started/ci.md": "getting-started-ci.md",
    "docs/concepts/protocol.md": "concepts-protocol.md",
    "docs/concepts/freeze.md": "concepts-freeze.md",
    "docs/concepts/ledger.md": "concepts-ledger.md",
    "docs/concepts/result-statuses.md": "concepts-result-statuses.md",
    "docs/concepts/canonical-json.md": "concepts-canonical-json.md",
    "docs/concepts/cards.md": "concepts-cards.md",
    "docs/guides/local-experiment-workflow.md": "guides-local-experiment-workflow.md",
    "docs/guides/headless-ci.md": "guides-headless-ci.md",
    "docs/guides/mcp.md": "guides-mcp.md",
    "docs/guides/ai-agent-mcp.md": "guides-ai-agent-mcp.md",
    "docs/guides/query-the-ledger.md": "guides-query-the-ledger.md",
    "docs/guides/python-api.md": "guides-python-api.md",
    "docs/guides/repair-and-crash-recovery.md": "guides-repair-and-crash-recovery.md",
    "docs/guides/anchoring-the-head.md": "guides-anchoring-the-head.md",
    "docs/guides/atlas.md": "guides-atlas.md",
    "docs/spec/CORE_SPEC.md": "spec-core.md",
    "docs/reference/error-codes.md": "reference-error-codes.md",
    "docs/reference/mcp.md": "reference-mcp.md",
    "docs/reference/python-api.md": "reference-python-api.md",
    "docs/reference/conformance-vectors.md": "reference-conformance-vectors.md",
    "docs/reference/file-formats.md": "reference-file-formats.md",
    "docs/reference/configuration.md": "reference-configuration.md",
    "docs/examples/README.md": "examples.md",
    "docs/examples/statuses-and-versions.md": "examples-statuses-and-versions.md",
    "docs/development/architecture.md": "development-architecture.md",
    "docs/development/testing.md": "development-testing.md",
    "docs/development/release-process.md": "development-release-process.md",
    "docs/project/roadmap.md": "project-roadmap.md",
    "docs/FAQ.md": "FAQ.md",
    "docs/RELATED_WORK_AND_INDEPENDENCE.md": "RELATED_WORK_AND_INDEPENDENCE.md",
    "docs/ARCHITECTURE.md": "ARCHITECTURE.md",
    "docs/archive/README.md": "archive.md",
    "GOVERNANCE.md": "GOVERNANCE.md",
    "CONTRIBUTING.md": "CONTRIBUTING.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "SECURITY.md": "SECURITY.md",
}
ASSETS = {
    "docs/assets/protocolith/logo-mark.svg": "assets/protocolith-mark.svg",
    "docs/assets/protocolith/favicon.svg": "assets/favicon.svg",
    "docs/assets/protocolith_workflow.svg": "assets/protocolith_workflow.svg",
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
        elif key.startswith("docs_site/") and (root / key).is_file():
            new = key.removeprefix("docs_site/") + suffix
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
