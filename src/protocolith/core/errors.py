# SPDX-License-Identifier: Apache-2.0
"""Error types shared by the core. Every error carries a stable machine code."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


# One-line advice per code, shown after the error. Codes without an entry have no hint.
HINTS: dict[str, str] = {
    "NO_LEDGER": "run `protocolith freeze FILE` (or `protocolith init`) to start a ledger, or check --store / PROTOCOLITH_STORE",
    "LOCK_TIMEOUT": "another protocolith process holds the store lock; wait for it to finish and retry",
    "HEAD_MISMATCH": "the ledger is not the one you anchored: an entry was removed or replaced; compare with your published head",
    "TRUNCATED_TAIL": "a write was interrupted; run `protocolith repair --truncate-partial-tail`",
    "NO_PARTIAL_TAIL": "nothing to repair: the last line is complete",
    "DUPLICATE_FREEZE": "a changed protocol needs a new `version`; freeze it with --supersedes HASH of the old one",
    "UNKNOWN_PROTOCOL": "freeze the protocol first and copy its protocol_sha256 into the entry",
    "BAD_STATUS": "use one of: PASSED_UNDER_PROTOCOL, NEGATIVE_RESULT_UNDER_PROTOCOL, BLOCKED_SOURCE, "
    "INSUFFICIENT_COVERAGE, SOURCE_DRIFT, REPRODUCED_OUTCOME",
    "MISSING_FIELD": "run `protocolith schema` to see the required fields",
    "BAD_ENTRY": "run `protocolith schema` to see the allowed fields; unknown keys are rejected",
    "DANGLING_REF": "refer only to an earlier entry of the right type (see `protocolith log`)",
    "TS_REGRESSION": "the clock is earlier than the last entry; fix the system time or PROTOCOLITH_NOW",
    "CARD_EXISTS": "a different card with this evidence_id is already there; use another --out directory",
    "CARD_CONFLICT": "remove the contradicting keys from the record `card` object",
    "CARD_INVALID": "fix the record `card` object; `protocolith validate-card` shows the validator output",
    "FLOAT_NOT_ALLOWED": 'write decimals as strings, for example "0.55"',
    "DUPLICATE_KEY": "an object repeats a key; remove the duplicate",
    "BAD_JSON": "the file is not valid JSON (a byte-order mark is also refused)",
    "BAD_PATH": "name an existing regular file inside the current directory",
    "IO_ERROR": "check that the path exists and is readable and writable",
}


def hint_for(code: str) -> str | None:
    return HINTS.get(code)


@dataclass(frozen=True)
class Violation:
    """One rule violation: the rule code, the ledger line index and a message."""

    code: str
    seq: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "seq": self.seq}


class ProtocolithError(Exception):
    exit_code = 2

    def __init__(self, code: str, message: str, violations: Sequence[Violation] = ()) -> None:
        # Messages may echo user text; keep them encodable as UTF-8 everywhere.
        self.message = message.encode("utf-8", "backslashreplace").decode("utf-8")
        self.code = code
        self.violations = tuple(violations)
        super().__init__(f"{code}: {self.message}")

    def codes(self) -> list[str]:
        found = {v.code for v in self.violations} or {self.code}
        return sorted(found)

    @property
    def hint(self) -> str | None:
        return hint_for(self.code)

    def to_dict(self) -> dict[str, Any]:
        error = {"code": self.code, "message": self.message}
        if self.hint is not None:
            error["hint"] = self.hint
        return {
            "codes": self.codes(),
            "error": error,
            "ok": False,
            "violations": [v.to_dict() for v in self.violations],
        }


class InputError(ProtocolithError):
    """Bad input or a rejected operation (CLI exit code 2)."""

    exit_code = 2


class EnvError(ProtocolithError):
    """I/O or environment problem (CLI exit code 3)."""

    exit_code = 3


class VerificationFailed(ProtocolithError):
    """The stored ledger does not verify (CLI exit code 1)."""

    exit_code = 1

    def __init__(self, violations: Sequence[Violation]) -> None:
        codes = ", ".join(sorted({v.code for v in violations}))
        super().__init__("VERIFICATION_FAILED", f"ledger does not verify: {codes}", violations)


@contextmanager
def io_guard() -> Iterator[None]:
    """Turn OSError (and a NUL in a path) into EnvError so no raw I/O error escapes the API."""
    try:
        yield
    except OSError as exc:
        raise EnvError("IO_ERROR", f"{type(exc).__name__}: {exc}") from exc
    except ValueError as exc:
        if "embedded null" not in str(exc):  # a NUL in a path is a ValueError, not an OSError
            raise
        raise EnvError("IO_ERROR", f"{type(exc).__name__}: {exc}") from exc
