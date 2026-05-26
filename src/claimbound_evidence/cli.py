# SPDX-License-Identifier: Apache-2.0
"""Small command-line helpers for ClaimBound public workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from claimbound_evidence.evidence_card import (
    load_evidence_card,
    validate_evidence_card,
)
from claimbound_evidence.family_ledger import (
    load_frontier_ledger,
    load_family_ledger,
    validate_frontier_ledger,
    validate_family_ledger,
)
from claimbound_evidence.registry import load_registry, validate_registry
from claimbound_evidence.run_root import RunRootRequest, prepare_run_root
from claimbound_evidence.scaffold import ScaffoldRequest, build_scaffold
from claimbound_evidence.tree_overlay import (
    load_tree_overlay,
    validate_tree_overlay,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEMO_ROOT = Path.home() / "claimbound_runs" / "claimbound_demo"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claimbound",
        description="ClaimBound helper commands for requests, scaffolds, demos and validation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser(
        "new",
        aliases=("new-track",),
        description="Create a draft track scaffold. Prompts interactively when run in a terminal.",
    )
    new_parser.add_argument("--source-url")
    new_parser.add_argument("--protocol-id")
    new_parser.add_argument("--domain")
    new_parser.add_argument("--track-type")
    new_parser.add_argument(
        "--execution-mode",
        choices=("MANUAL_NO_AI", "AUTOMATED_AI_ASSISTED"),
        default="MANUAL_NO_AI",
    )
    new_parser.add_argument("--out", type=Path)
    new_parser.add_argument("--source-name", default="Public source under review")
    new_parser.add_argument("--audience", default="public evidence operators")
    new_parser.set_defaults(func=_cmd_new)

    demo_parser = subparsers.add_parser(
        "demo",
        description="Run a small public demo helper.",
    )
    demo_parser.add_argument(
        "name",
        choices=("grok-source-audit", "eea-source-audit", "eea-manual-probe", "validate-all"),
    )
    demo_parser.add_argument("--report", type=Path)
    demo_parser.add_argument(
        "--demo-root",
        type=Path,
        default=DEFAULT_DEMO_ROOT,
        help="Local-only root for demo source clones and reports.",
    )
    demo_parser.add_argument(
        "--grok-repo-dir",
        type=Path,
        help="Existing local clone for xai-org/grok-prompts. Defaults to a local-only demo clone.",
    )
    demo_parser.set_defaults(func=_cmd_demo)

    validate_parser = subparsers.add_parser(
        "validate-all",
        description="Validate all public evidence cards and the registry.",
    )
    validate_parser.add_argument(
        "--cards-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "evidence_cards",
    )
    validate_parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "docs" / "registry" / "evidence_index.json",
    )
    validate_parser.add_argument(
        "--families-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "track_families",
        help="Directory containing optional *_FAMILY_LEDGER.json files.",
    )
    validate_parser.add_argument(
        "--frontiers-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "track_families",
        help="Directory containing optional *_FRONTIER.json files.",
    )
    validate_parser.add_argument(
        "--trees-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "track_families",
        help="Directory containing optional protocol v3 *_TREE.json files.",
    )
    validate_parser.set_defaults(func=_cmd_validate_all)

    family_parser = subparsers.add_parser(
        "validate-family",
        description="Validate one R&D family ledger JSON file.",
    )
    family_parser.add_argument("path", type=Path)
    family_parser.set_defaults(func=_cmd_validate_family)

    frontier_parser = subparsers.add_parser(
        "validate-frontier",
        description="Validate one R&D family frontier JSON file.",
    )
    frontier_parser.add_argument("path", type=Path)
    frontier_parser.add_argument(
        "--base-dir",
        type=Path,
        help="Optional base directory for context capsule and tombstone path checks.",
    )
    frontier_parser.set_defaults(func=_cmd_validate_frontier)

    tree_parser = subparsers.add_parser(
        "validate-tree",
        description="Validate one protocol v3 R&D tree overlay JSON file.",
    )
    tree_parser.add_argument("path", type=Path)
    tree_parser.set_defaults(func=_cmd_validate_tree)

    run_root_parser = subparsers.add_parser(
        "run-root",
        description="Create a local-only run root with standard raw/log/hash/report folders.",
    )
    run_root_parser.add_argument("--protocol-id", required=True)
    run_root_parser.add_argument("--source-url", required=True)
    run_root_parser.add_argument("--operator", default="local operator")
    run_root_parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / "claimbound_runs",
        help="Local-only parent directory. Defaults to ~/claimbound_runs.",
    )
    run_root_parser.set_defaults(func=_cmd_run_root)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args, parser) or 0)


def _cmd_new(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    source_url = _value_or_prompt(args.source_url, "Source URL", parser)
    protocol_id = _value_or_prompt(args.protocol_id, "Protocol ID", parser)
    domain = _value_or_prompt(args.domain, "Domain", parser)
    track_type = _value_or_prompt(args.track_type, "Track type", parser)
    out = args.out or _prompt_path("Output directory", parser)

    if not out.is_absolute():
        out = REPO_ROOT / out

    request = ScaffoldRequest(
        source_url=source_url,
        protocol_id=protocol_id,
        domain=domain,
        track_type=track_type,
        execution_mode=args.execution_mode,
        out_dir=out,
        source_name=args.source_name,
        audience=args.audience,
    )
    paths = build_scaffold(request, REPO_ROOT)
    for path in paths:
        print(path.relative_to(REPO_ROOT).as_posix())
    return 0


def _cmd_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    if args.name == "validate-all":
        validate_args = argparse.Namespace(
            cards_dir=REPO_ROOT / "docs" / "evidence_cards",
            registry=REPO_ROOT / "docs" / "registry" / "evidence_index.json",
            families_dir=REPO_ROOT / "docs" / "track_families",
            frontiers_dir=REPO_ROOT / "docs" / "track_families",
            trees_dir=REPO_ROOT / "docs" / "track_families",
        )
        return _cmd_validate_all(validate_args, build_parser())

    if args.name == "eea-source-audit":
        report = args.report or (args.demo_root / "reports" / "source_audit_d001_demo_summary.json")
        return _run_script("claimbound_run_eea_source_audit.py", "--report", str(report))

    if args.name == "eea-manual-probe":
        report = args.report or (args.demo_root / "reports" / "eea_aq_d001_manual_summary.json")
        return _run_script(
            "claimbound_run_eea_manual_track.py",
            "--probe-eea-api",
            "--report",
            str(report),
        )

    if args.name == "grok-source-audit":
        repo_dir = args.grok_repo_dir or args.demo_root / "sources" / "grok-prompts"
        _ensure_grok_clone(repo_dir)
        report = args.report or (args.demo_root / "reports" / "grok_prompts_source_audit_d001_demo_summary.json")
        return _run_script(
            "claimbound_run_grok_prompts_source_audit.py",
            "--repo-dir",
            str(repo_dir),
            "--report",
            str(report),
        )

    raise AssertionError(args.name)


def _cmd_validate_all(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    card_paths = sorted(args.cards_dir.glob("*.json"))
    violations: list[str] = []

    for card_path in card_paths:
        for violation in validate_evidence_card(load_evidence_card(card_path)):
            violations.append(f"{_display_path(card_path)}: {violation}")

    registry = load_registry(args.registry)
    for violation in validate_registry(registry, REPO_ROOT):
        violations.append(f"{_display_path(args.registry)}: {violation}")

    family_paths = sorted(args.families_dir.glob("*_FAMILY_LEDGER.json"))
    for family_path in family_paths:
        for violation in validate_family_ledger(load_family_ledger(family_path)):
            violations.append(f"{_display_path(family_path)}: {violation}")

    frontier_paths = sorted(args.frontiers_dir.glob("*_FRONTIER.json"))
    for frontier_path in frontier_paths:
        for violation in validate_frontier_ledger(
            load_frontier_ledger(frontier_path),
            frontier_path.parent,
        ):
            violations.append(f"{_display_path(frontier_path)}: {violation}")

    tree_paths = sorted(args.trees_dir.glob("*_TREE.json"))
    for tree_path in tree_paths:
        for violation in validate_tree_overlay(load_tree_overlay(tree_path)):
            violations.append(f"{_display_path(tree_path)}: {violation}")

    if violations:
        for violation in violations:
            print(f"violation: {violation}", file=sys.stderr)
        return 1

    print(f"valid_cards={len(card_paths)}")
    print(f"valid_registry={_display_path(args.registry)}")
    print(f"valid_family_ledgers={len(family_paths)}")
    print(f"valid_frontier_ledgers={len(frontier_paths)}")
    print(f"valid_tree_overlays={len(tree_paths)}")
    return 0


def _cmd_validate_family(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    path = args.path
    if not path.is_absolute():
        path = REPO_ROOT / path

    violations = validate_family_ledger(load_family_ledger(path))
    if violations:
        for violation in violations:
            print(f"violation: {_display_path(path)}: {violation}", file=sys.stderr)
        return 1

    print(f"valid_family_ledger={_display_path(path)}")
    return 0


def _cmd_validate_frontier(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    path = args.path
    if not path.is_absolute():
        path = REPO_ROOT / path
    base_dir = args.base_dir
    if base_dir is not None and not base_dir.is_absolute():
        base_dir = REPO_ROOT / base_dir

    violations = validate_frontier_ledger(load_frontier_ledger(path), base_dir or path.parent)
    if violations:
        for violation in violations:
            print(f"violation: {_display_path(path)}: {violation}", file=sys.stderr)
        return 1

    print(f"valid_frontier_ledger={_display_path(path)}")
    return 0


def _cmd_validate_tree(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    path = args.path
    if not path.is_absolute():
        path = REPO_ROOT / path

    violations = validate_tree_overlay(load_tree_overlay(path))
    if violations:
        for violation in violations:
            print(f"violation: {_display_path(path)}: {violation}", file=sys.stderr)
        return 1

    print(f"valid_tree_overlay={_display_path(path)}")
    return 0


def _cmd_run_root(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    del parser
    paths = prepare_run_root(
        RunRootRequest(
            protocol_id=args.protocol_id,
            operator=args.operator,
            source_url=args.source_url,
            root=args.root,
        )
    )
    for path in paths:
        print(path.as_posix())
    return 0


def _value_or_prompt(
    value: str | None, prompt: str, parser: argparse.ArgumentParser
) -> str:
    if value:
        return value
    if sys.stdin.isatty():
        entered = input(f"{prompt}: ").strip()
        if entered:
            return entered
    parser.error(f"--{prompt.lower().replace(' ', '-')} is required outside interactive mode")
    raise AssertionError("unreachable")


def _prompt_path(prompt: str, parser: argparse.ArgumentParser) -> Path:
    if sys.stdin.isatty():
        entered = input(f"{prompt}: ").strip()
        if entered:
            return Path(entered)
    parser.error("--out is required outside interactive mode")
    raise AssertionError("unreachable")


def _run_script(script_name: str, *args: str) -> int:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / script_name), *args]
    return subprocess.call(cmd, cwd=REPO_ROOT)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _ensure_grok_clone(repo_dir: Path) -> None:
    if (repo_dir / ".git").is_dir():
        return
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "git",
            "clone",
            "--depth=1",
            "https://github.com/xai-org/grok-prompts",
            str(repo_dir),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
