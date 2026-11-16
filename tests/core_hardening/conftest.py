# SPDX-License-Identifier: Apache-2.0
"""Hypothesis profiles and a fixed environment for the hardening tests."""

from __future__ import annotations

import os

import pytest
from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=60,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
settings.register_profile(
    "deep",
    max_examples=2000,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "ci"))


@pytest.fixture(autouse=True)
def _fixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROTOCOLITH_NOW", raising=False)
    monkeypatch.delenv("PROTOCOLITH_STORE", raising=False)
