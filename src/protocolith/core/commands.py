# SPDX-License-Identifier: Apache-2.0
"""CLI glue for the core commands. Exit codes: 0 ok, 1 verification failed, 2 input, 3 environment."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ops
from .capture import capture
from .canonical import decode, encode
from .errors import InputError, ProtocolithError, hint_for, io_guard
from .ledger import ENTRY_TYPES, RESULT_STATUSES
from .mcp import serve
from .schema import NAMES, all_schemas, schema_for
from .store import Store, resolve_store


@dataclass
class Outcome:
    data: Any
    text: str
    code: int = 0
    errors: str = ""


def read_input(path: str) -> Any:
    """Read FILE as strict JSON (no duplicate keys, no floats)."""
    with io_guard():
        raw = Path(path).read_bytes()
    try:
        return decode(raw)
    except ProtocolithError as exc:
        raise InputError(exc.code, f"{path}: {exc.message}") from None


def _fail(args: argparse.Namespace, exc: ProtocolithError) -> int:
    print(f"protocolith: {exc.code}: {exc.message}", file=sys.stderr)
    for violation in exc.violations:
        print(f"  {violation.code} line {violation.seq}: {violation.message}", file=sys.stderr)
    for code in exc.codes():
        if (hint := hint_for(code)) is not None:
            print(f"  hint ({code}): {hint}", file=sys.stderr)
    if args.json:
        print(encode(exc.to_dict()).decode("utf-8"))
    return exc.exit_code


def _run(args: argparse.Namespace, work: Callable[[Store], Outcome]) -> int:
    try:
        outcome = work(resolve_store(args.store))
    except ProtocolithError as exc:
        return _fail(args, exc)
    if outcome.errors:
        print(outcome.errors, file=sys.stderr)
    print(encode(outcome.data).decode("utf-8") if args.json else outcome.text)
    return outcome.code


def _cmd_freeze(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        entry = ops.freeze(store, read_input(args.file), supersedes=args.supersedes)
        body = entry["body"]
        text = f"frozen {body['protocol_id']} {body['version']} seq={entry['seq']} hash={entry['hash']}"
        return Outcome(entry, text + f" protocol_sha256={body['protocol_sha256']}")

    return _run(args, work)


def _cmd_record(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        entry = ops.record(store, read_input(args.file))
        body = entry["body"]
        return Outcome(entry, f"recorded {body['run_id']} {body['status']} seq={entry['seq']} hash={entry['hash']}")

    return _run(args, work)


def _cmd_deviation(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        entry = ops.deviation(store, read_input(args.file))
        return Outcome(entry, f"deviation {entry['body']['kind']} seq={entry['seq']} hash={entry['hash']}")

    return _run(args, work)


def _cmd_verify_ledger(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        verdict = ops.verify(store, args.expect_head)
        if verdict.ok:
            head = f"head seq={verdict.head_seq} hash={verdict.head_hash}" if verdict.count else "empty"
            return Outcome(verdict.to_dict(), f"OK entries={verdict.count} {head}")
        lines = [f"{v.code} line {v.seq}: {v.message}" for v in verdict.violations]
        lines += [f"hint ({code}): {hint}" for code in verdict.codes if (hint := hint_for(code)) is not None]
        return Outcome(verdict.to_dict(), "FAILED: " + ", ".join(verdict.codes), 1, "\n".join(lines))

    return _run(args, work)


def _cmd_issue(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        result = ops.issue(store, args.seq, out=args.out)
        text = f"issued record seq={args.seq} card_sha256={result['entry']['body']['card_sha256']}"
        return Outcome(result, f"{text}\n{result['json_path']}\n{result['svg_path']}")

    return _run(args, work)


_SUMMARY: dict[str, Callable[[dict[str, Any]], str]] = {
    "freeze": lambda body: f"{body['protocol_id']} {body['version']}",
    "record": lambda body: f"{body['run_id']} {body['status']}",
    "deviation": lambda body: body["kind"],
    "issue": lambda body: f"record_seq={body['record_seq']}",
}


def _cmd_log(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        found = ops.log(store, protocol=args.protocol, type=args.type, status=args.status, tail=args.tail)
        lines = [f"{e['seq']} {e['type']} {e['ts']} {e['hash'][:12]} {_SUMMARY[e['type']](e['body'])}" for e in found]
        return Outcome(found, "\n".join(lines))

    return _run(args, work)


def _cmd_show(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        found = ops.show(store, args.seq)
        entry, context = found["entry"], found["protocol"]
        lines = [f"seq {entry['seq']} {entry['type']} {entry['ts']}", f"hash {entry['hash']}", f"prev {entry['prev']}"]
        lines.append(f"protocol {context['protocol_id']} {context['version']} (frozen at seq {context['freeze_seq']})")
        lines.append("points at: " + (", ".join(map(str, found["points_at"])) or "-"))
        lines.append("pointed at by: " + (", ".join(map(str, found["pointed_by"])) or "-"))
        lines.append("body: " + encode(entry["body"]).decode("utf-8"))
        return Outcome(found, "\n".join(lines))

    return _run(args, work)


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(len(header))]
    return [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in [header, *rows]
    ]


def _counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name} {count}" for name, count in counts.items()) or "none"


def _summary_text(found: dict[str, Any]) -> str:
    head = found["head"]
    state = "OK" if found["ok"] else "FAILED"
    where = f"head seq={head['seq']} hash={head['hash']}" if head["count"] else "empty"
    lines = [f"ledger {state}  entries={head['count']}  {where}", f"entries: {_counts(found['entries_by_type'])}"]
    lines.append(f"results: {_counts(found['records_by_status'])}")
    rows = [
        [
            row["protocol_id"],
            ",".join(row["versions"]),
            row["latest_version"],
            str(row["records"]),
            row["latest_status"] or "-",
            str(row["deviations"]),
            str(row["cards"]),
        ]
        for row in found["protocols"]
    ]
    if rows:
        lines += _table(["PROTOCOL", "VERSIONS", "LATEST", "RECORDS", "LATEST_STATUS", "DEVIATIONS", "CARDS"], rows)
    lines.append("problems: " + ("none" if not found["problems"] else str(len(found["problems"]))))
    lines += [f"  {p['code']} line {p['seq']}: {p['message']}" for p in found["problems"]]
    return "\n".join(lines)


def _cmd_summary(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        found = ops.summary(store, args.protocol)
        return Outcome(found, _summary_text(found), 0 if found["ok"] else 1)

    return _run(args, work)


def _cmd_init(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        found = ops.init(store)
        return Outcome(found, f"{'created' if found['created'] else 'exists'} {found['path']}")

    return _run(args, work)


def _cmd_capture(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        fragment = capture(args.file, env=args.env)
    except ProtocolithError as exc:
        return _fail(args, exc)
    print(encode(fragment).decode("utf-8"))
    return 0


def _cmd_schema(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    print(encode(all_schemas() if args.name == "all" else schema_for(args.name)).decode("utf-8"))
    return 0


def _cmd_head(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        found = ops.head(store)
        text = f"seq={found['seq']} hash={found['hash']}" if found["count"] else "empty"
        return Outcome(found, text)

    return _run(args, work)


def _cmd_repair(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    def work(store: Store) -> Outcome:
        removed = ops.repair_truncate_partial_tail(store)
        return Outcome({"ok": True, "removed_bytes": removed}, f"removed {removed} bytes of partial tail")

    return _run(args, work)


def _cmd_mcp(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    serve(resolve_store(args.store), sys.stdin.buffer, sys.stdout.buffer)
    return 0


def add_core_commands(subparsers: Any) -> None:
    """Register the ledger commands on the main parser (additive)."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", default=None, help="Store directory (env PROTOCOLITH_STORE, default .protocolith).")
    with_json = argparse.ArgumentParser(add_help=False, parents=[common])
    with_json.add_argument("--json", action="store_true", help="Print the result as canonical JSON.")

    def add(
        name: str, func: Callable[..., int], help_text: str, parent: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = subparsers.add_parser(
            name, parents=[parent], help=help_text, description=help_text
        )
        parser.set_defaults(func=func)
        return parser

    freeze = add("freeze", _cmd_freeze, "Freeze a protocol from a JSON file.", with_json)
    freeze.add_argument("file", metavar="FILE")
    freeze.add_argument(
        "--supersedes", default=None, metavar="SHA256", help="Hash of the protocol version this replaces."
    )
    add("record", _cmd_record, "Record a run outcome from a JSON file.", with_json).add_argument("file", metavar="FILE")
    add("deviation", _cmd_deviation, "Record a deviation from a JSON file.", with_json).add_argument(
        "file", metavar="FILE"
    )
    verify = add("verify-ledger", _cmd_verify_ledger, "Verify the ledger (rules R1 to R11).", with_json)
    verify.add_argument(
        "--expect-head",
        default=None,
        metavar="SEQ:HASH",
        help="Also require the entry at SEQ to have this hash (detects a removed tail); else HEAD_MISMATCH, exit 1.",
    )
    issue = add("issue", _cmd_issue, "Issue the evidence card of a record.", with_json)
    issue.add_argument("seq", type=int, metavar="SEQ")
    issue.add_argument("--out", default=None, metavar="DIR", help="Card directory (default <store>/cards).")
    log = add("log", _cmd_log, "List ledger entries, optionally filtered.", with_json)
    log.add_argument("--protocol", default=None, metavar="ID", help="Only entries of this protocol_id.")
    log.add_argument("--type", default=None, choices=ENTRY_TYPES, help="Only entries of this type.")
    log.add_argument(
        "--status", default=None, choices=sorted(RESULT_STATUSES), help="Only records with this result status."
    )
    log.add_argument("--tail", default=None, type=int, metavar="N", help="Keep only the last N matching entries.")
    add("show", _cmd_show, "Show one entry with its protocol context.", with_json).add_argument(
        "seq", type=int, metavar="SEQ"
    )
    summary = add("summary", _cmd_summary, "Verdict, head, counts and a per-protocol table in one call.", with_json)
    summary.add_argument("--protocol", default=None, metavar="ID", help="Only this protocol_id.")
    add("init", _cmd_init, "Create the store with an empty ledger (safe to repeat).", with_json)
    capture_parser = subparsers.add_parser(
        "capture",
        help="Print a JSON fragment (environment, input file hashes) for a record outcome.",
        description="Print a JSON fragment for the outcome object of a record: Python, platform, machine and "
        "protocolith version, and the relative path, size and sha256 of each --file (inside the current directory). "
        "Runs nothing and reads no environment values.",
    )
    capture_parser.set_defaults(func=_cmd_capture)
    capture_parser.add_argument("--json", action="store_true", help="Print errors as canonical JSON.")
    capture_parser.add_argument(
        "--file", action="append", default=[], metavar="PATH", help="File to hash; repeat for several."
    )
    capture_parser.add_argument(
        "--env", action="store_true", help="Include the environment (implied when no --file is given)."
    )
    schema_parser = subparsers.add_parser(
        "schema",
        help="Print the JSON Schema of an input body.",
        description="Print a JSON Schema (draft 2020-12) generated from the rules.",
    )
    schema_parser.set_defaults(func=_cmd_schema)
    schema_parser.add_argument(
        "name", nargs="?", default="all", choices=[*NAMES, "all"], help="Which schema (default all)."
    )
    add("head", _cmd_head, "Print the ledger head (last hash and seq).", with_json)
    repair = add("repair", _cmd_repair, "Repair a crash-damaged ledger.", with_json)
    repair.add_argument(
        "--truncate-partial-tail", action="store_true", required=True, help="Remove the partial last line."
    )
    add("mcp", _cmd_mcp, "Run the MCP server on stdio.", common)
