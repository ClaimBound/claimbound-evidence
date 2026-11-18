# SPDX-License-Identifier: Apache-2.0
"""Protocolith core: record, verify and issue trial records. Standard library only."""

from __future__ import annotations

from .anchor import AnchorReport, anchor_head, verify_anchors
from .atlas import build_atlas
from .canonical import CanonError, decode, encode, sha256_hex
from .clock import now_utc
from .errors import EnvError, InputError, ProtocolithError, VerificationFailed, Violation
from .ledger import MAX_ENTRY_BYTES, RESULT_STATUSES
from .capture import capture
from .disclosure import Policy, build_disclosure, load_policy, parse_policy, verify_disclosure, verify_reveal
from .ops import (
    claim_check,
    deviation,
    entries,
    freeze,
    head,
    init,
    issue,
    log,
    record,
    repair_truncate_partial_tail,
    show,
    summary,
    verify,
)
from .rules import Verdict, Verifier, scan
from .schema import schema_for
from .store import Store, resolve_store

__all__ = [
    "AnchorReport",
    "MAX_ENTRY_BYTES",
    "RESULT_STATUSES",
    "CanonError",
    "EnvError",
    "InputError",
    "ProtocolithError",
    "Policy",
    "Store",
    "Verdict",
    "VerificationFailed",
    "Verifier",
    "Violation",
    "anchor_head",
    "build_atlas",
    "build_disclosure",
    "capture",
    "claim_check",
    "decode",
    "deviation",
    "encode",
    "entries",
    "freeze",
    "head",
    "init",
    "issue",
    "load_policy",
    "log",
    "parse_policy",
    "now_utc",
    "record",
    "repair_truncate_partial_tail",
    "resolve_store",
    "scan",
    "schema_for",
    "show",
    "sha256_hex",
    "summary",
    "verify",
    "verify_anchors",
    "verify_disclosure",
    "verify_reveal",
]
