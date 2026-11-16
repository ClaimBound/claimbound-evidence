# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

import pytest

from protocolith.core import Store, freeze, record
from core_support import NOW, clock, protocol, record_body


@pytest.fixture(autouse=True)
def _fixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROTOCOLITH_NOW", raising=False)
    monkeypatch.delenv("PROTOCOLITH_STORE", raising=False)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "store")


@pytest.fixture
def recorded(store: Store) -> Store:
    """A store with one freeze (seq 0) and one record (seq 1)."""
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(), clock=clock(NOW))
    return store
