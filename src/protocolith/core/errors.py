# SPDX-License-Identifier: Apache-2.0
"""Error types shared by the core. Every error carries a stable machine code."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "codes": self.codes(),
            "error": {"code": self.code, "message": self.message},
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
    """Turn OSError into EnvError so no raw I/O error escapes the API."""
    try:
        yield
    except OSError as exc:
        raise EnvError("IO_ERROR", f"{type(exc).__name__}: {exc}") from exc
