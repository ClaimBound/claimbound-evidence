# SPDX-License-Identifier: Apache-2.0
"""Injectable UTC clock with whole-second ISO timestamps."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, UTC

from .errors import InputError
from .ledger import is_ts

ENV_NOW = "PROTOCOLITH_NOW"
Clock = Callable[[], str]


def now_utc(clock: Clock | None = None) -> str:
    """The current timestamp: ``clock`` if given, else ``PROTOCOLITH_NOW``, else the system clock."""
    if clock is not None:
        value = clock()
    else:
        value = os.environ.get(ENV_NOW) or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not is_ts(value):
        raise InputError("BAD_CLOCK", f"timestamp must look like YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return value
