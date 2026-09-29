# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import date

from claimbound_evidence.nasa_power import NasaPowerMockConfig, _seed_from_config


def test_seed_is_derived_deterministically_when_not_given() -> None:
    config = NasaPowerMockConfig(point_id="POWER_A", start=date(2024, 1, 1), end=date(2024, 1, 10))
    same = NasaPowerMockConfig(point_id="POWER_A", start=date(2024, 1, 1), end=date(2024, 1, 10))
    other = NasaPowerMockConfig(point_id="POWER_B", start=date(2024, 1, 1), end=date(2024, 1, 10))

    assert _seed_from_config(config) == _seed_from_config(same)
    assert _seed_from_config(config) != _seed_from_config(other)


def test_explicit_seed_is_used_as_is() -> None:
    config = NasaPowerMockConfig(point_id="POWER_A", start=date(2024, 1, 1), end=date(2024, 1, 10), seed=7)

    assert _seed_from_config(config) == 7
