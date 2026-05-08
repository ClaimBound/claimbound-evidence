from __future__ import annotations

from claimbound_public_benchmarks.cli import build_parser, main


def test_cli_parser_has_public_workflow_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "new" in help_text
    assert "new-track" in help_text
    assert "demo" in help_text
    assert "run-root" in help_text
    assert "validate-all" in help_text


def test_validate_all_command_passes_for_committed_cards() -> None:
    assert main(["validate-all"]) == 0
