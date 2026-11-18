# SPDX-License-Identifier: Apache-2.0
"""Directory store: ledger file, advisory lock, durable append, tail repair."""

from __future__ import annotations

import importlib
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .errors import EnvError

ENV_STORE = "PROTOCOLITH_STORE"
DEFAULT_STORE = ".protocolith"
LEDGER_NAME = "ledger.jsonl"
LOCK_NAME = "lock"

_lock = importlib.import_module("protocolith.core._lock_" + ("windows" if sys.platform == "win32" else "posix"))


def resolve_store(path: str | os.PathLike[str] | None) -> Store:
    """Pick the store directory: explicit path, then ``PROTOCOLITH_STORE``, then ``.protocolith``."""
    return Store(path or os.environ.get(ENV_STORE) or DEFAULT_STORE)


class Store:
    def __init__(self, path: str | os.PathLike[str], lock_timeout: float = 30.0) -> None:
        self.path = Path(path)
        self.lock_timeout = lock_timeout

    @property
    def ledger_path(self) -> Path:
        return self.path / LEDGER_NAME

    @property
    def lock_path(self) -> Path:
        return self.path / LOCK_NAME

    @property
    def anchors_dir(self) -> Path:
        return self.path / "anchors"

    @property
    def cards_dir(self) -> Path:
        return self.path / "cards"

    def read(self, *, missing_ok: bool) -> bytes:
        try:
            return self.ledger_path.read_bytes()
        except FileNotFoundError:
            if missing_ok:
                return b""
            raise EnvError("NO_LEDGER", f"no ledger at {self.ledger_path}") from None

    @contextmanager
    def locked(self, *, write: bool) -> Iterator[None]:
        """Hold the exclusive lock. A reader that cannot open the lock file reads without it."""
        if write:
            self.path.mkdir(parents=True, exist_ok=True)
        fd = self._open_lock(write)
        if fd is None:
            yield
            return
        try:
            self._acquire(fd)
            try:
                yield
            finally:
                _lock.unlock(fd)
        finally:
            os.close(fd)

    def _open_lock(self, write: bool) -> int | None:
        try:
            return os.open(self.lock_path, os.O_RDWR | (os.O_CREAT if write else 0), 0o644)
        except OSError:
            if write:
                raise
            return None

    def _acquire(self, fd: int) -> None:
        deadline = time.monotonic() + self.lock_timeout
        while not _lock.try_lock(fd):
            if time.monotonic() >= deadline:
                raise EnvError("LOCK_TIMEOUT", f"could not lock {self.lock_path} within {self.lock_timeout} s")
            time.sleep(0.01)

    def append_line(self, line: bytes) -> None:
        """Append one complete line: write, flush, fsync. Call with the lock held."""
        created = not self.ledger_path.exists()
        with open(self.ledger_path, "ab") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        if created:
            _lock.fsync_dir(str(self.path))

    def truncate(self, size: int) -> None:
        with open(self.ledger_path, "r+b") as handle:
            handle.truncate(size)
            handle.flush()
            os.fsync(handle.fileno())
