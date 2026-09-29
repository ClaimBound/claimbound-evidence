#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate docs/CLI.md from the argparse definitions of the claimbound CLI.

Run ``python scripts/gen_cli_reference.py`` to rewrite the file, or with ``--check`` to
fail when it is out of date. The output does not depend on the terminal width or the
Python version, so it can be compared in CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from claimbound_evidence.cli import CHECKOUT_COMMANDS, build_parser  # noqa: E402

OUTPUT = REPO_ROOT / "docs" / "CLI.md"
HEADER = """# Command Reference

Generated from the CLI definitions by `scripts/gen_cli_reference.py`. Do not edit by hand.

Commands marked **needs a clone** use cards, registry or scripts that are not part of the
pip package; from a pip install they print how to clone the repository and exit with code 2.
All other commands work after `pip install claimbound-evidence`.
"""


def _choices(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def _subparsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    """Sub-commands by primary name; aliases share a parser and are skipped."""
    primary: dict[str, argparse.ArgumentParser] = {}
    seen: set[int] = set()
    for name, sub in _choices(parser).items():
        if id(sub) not in seen:
            seen.add(id(sub))
            primary[name] = sub
    return primary


def _aliases(parser: argparse.ArgumentParser, primary: argparse.ArgumentParser) -> list[str]:
    return [name for name, sub in _choices(parser).items() if sub is primary][1:]


def _argument_line(action: argparse.Action) -> str | None:
    if isinstance(action, (argparse._HelpAction, argparse._SubParsersAction, argparse._VersionAction)):
        return None
    if action.option_strings:
        label = ", ".join(action.option_strings)
        if action.nargs != 0 and action.metavar is None and action.dest:
            label += f" {action.dest.upper()}"
        elif action.metavar:
            label += f" {action.metavar}"
    else:
        label = action.dest
    notes: list[str] = []
    if action.option_strings and action.required:
        notes.append("required")
    if action.choices and not action.option_strings:
        notes.append("one of: " + ", ".join(f"`{c}`" for c in action.choices))
    elif action.choices:
        notes.append("choices: " + ", ".join(f"`{c}`" for c in action.choices))
    if action.nargs in ("+", "*"):
        notes.append("one or more values" if action.nargs == "+" else "zero or more values")
    if action.default not in (None, argparse.SUPPRESS, False, [], ()) and action.option_strings:
        default = action.default
        if isinstance(default, list):
            default = ", ".join(str(item) for item in default)
        elif isinstance(default, Path):
            for base, prefix in ((REPO_ROOT, Path()), (Path.home(), Path("~"))):
                if base in default.parents:
                    default = prefix / default.relative_to(base)
                    break
        notes.append(f"default: `{default}`")
    text = f"- `{label}`"
    if action.help:
        text += f" — {action.help}"
    if notes:
        text += f" ({'; '.join(notes)})"
    return text


def _render(parser: argparse.ArgumentParser, path: str, level: int, needs_clone: bool, out: list[str]) -> None:
    out.append(f"{'#' * level} `{path}`")
    out.append("")
    if needs_clone:
        out.append("**Needs a clone** of the repository.")
        out.append("")
    if parser.description:
        out.append(parser.description)
        out.append("")
    lines = [line for action in parser._actions if (line := _argument_line(action))]
    if lines:
        out.extend(lines)
        out.append("")
    for name, sub in _subparsers(parser).items():
        _render(sub, f"{path} {name}", level + 1, False, out)


def build_reference() -> str:
    root = build_parser()
    out = [HEADER]
    out.append("Global option: `--version` prints the installed version.")
    out.append("")
    for name, sub in _subparsers(root).items():
        aliases = _aliases(root, sub)
        title = f"claimbound {name}" + (f" (alias: {', '.join(aliases)})" if aliases else "")
        _render(sub, title, 2, name in CHECKOUT_COMMANDS, out)
    return "\n".join(out).rstrip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if docs/CLI.md is out of date")
    args = parser.parse_args()
    text = build_reference()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != text:
            print("docs/CLI.md is out of date; run: python scripts/gen_cli_reference.py", file=sys.stderr)
            return 1
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
