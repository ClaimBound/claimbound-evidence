# SPDX-License-Identifier: Apache-2.0
"""POSIX advisory locking. Exercised on its own platform in CI, hence the pragmas."""

from __future__ import annotations  # pragma: no cover

import fcntl  # pragma: no cover
import os  # pragma: no cover


def try_lock(fd: int) -> bool:  # pragma: no cover
    """Try to take an exclusive lock without blocking."""
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def unlock(fd: int) -> None:  # pragma: no cover
    fcntl.flock(fd, fcntl.LOCK_UN)


def fsync_dir(path: str) -> None:  # pragma: no cover
    """Make a newly created file name durable."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
