# SPDX-License-Identifier: Apache-2.0
"""Protocolith: records, verifies and issues trial records.

The core modules use only the standard library. The NASA POWER runner names below are kept
for compatibility and load on first access, because that runner needs the optional
``runners`` extra (numpy).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from protocolith.nasa_power_prereg_runner import (
        NASA_POWER_PREREG_REPORT_SCHEMA,
        NasaPowerPreregConfig,
        evaluate_nasa_power_prereg,
    )

_LAZY = {
    "NASA_POWER_PREREG_REPORT_SCHEMA",
    "NasaPowerPreregConfig",
    "evaluate_nasa_power_prereg",
}

__all__ = [
    "NASA_POWER_PREREG_REPORT_SCHEMA",
    "NasaPowerPreregConfig",
    "evaluate_nasa_power_prereg",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        from protocolith import nasa_power_prereg_runner

        return getattr(nasa_power_prereg_runner, name)
    raise AttributeError(f"module 'protocolith' has no attribute {name!r}")
