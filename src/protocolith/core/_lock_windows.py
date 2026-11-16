# SPDX-License-Identifier: Apache-2.0
"""Windows advisory locking. Exercised on its own platform in CI, hence the pragmas."""

from __future__ import annotations  # pragma: no cover

import os  # pragma: no cover


def try_lock(fd: int) -> bool:  # pragma: no cover
    """Try to take an exclusive lock on the first byte without blocking."""
    import msvcrt

    os.lseek(fd, 0, os.SEEK_SET)
    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined, unused-ignore]
    except OSError:
        return False
    return True


def unlock(fd: int) -> None:  # pragma: no cover
    import msvcrt

    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined, unused-ignore]


def fsync_dir(path: str) -> None:  # pragma: no cover
    """Directories cannot be fsynced on Windows; nothing to do."""
