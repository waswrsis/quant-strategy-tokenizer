from __future__ import annotations

from importlib.metadata import EntryPoint
from typing import Any

import pytest

from quant_strategy_tokenizer.adapters import discovery, loader
from quant_strategy_tokenizer.adapters.discovery import discover_adapters
from quant_strategy_tokenizer.adapters.loader import get_adapter


class LocalAdapter:
    pass


def adapter_factory() -> LocalAdapter:
    return LocalAdapter()


def _fake_entry_points(group: str | None = None, **_kwargs: Any) -> list[EntryPoint]:
    assert group == "quant_strategy_tokenizer.adapters"
    return [
        EntryPoint(
            name="zeta",
            value="tests.ports.test_adapter_discovery:adapter_factory",
            group="quant_strategy_tokenizer.adapters",
        ),
        EntryPoint(
            name="alpha",
            value="tests.ports.test_adapter_discovery:adapter_factory",
            group="quant_strategy_tokenizer.adapters",
        ),
    ]


def test_adapter_discovery_uses_local_entry_points_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(discovery.metadata, "entry_points", _fake_entry_points)

    descriptors = discover_adapters()

    assert [descriptor.adapter_id for descriptor in descriptors] == ["alpha", "zeta"]
    assert descriptors[0].module == "tests.ports.test_adapter_discovery"
    assert descriptors[0].object_ref == "adapter_factory"


def test_get_adapter_loads_local_entry_point_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loader.metadata, "entry_points", _fake_entry_points)

    adapter = get_adapter("alpha")

    assert type(adapter).__name__ == "LocalAdapter"


def test_get_adapter_missing_id_raises_key_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loader.metadata, "entry_points", _fake_entry_points)

    with pytest.raises(KeyError, match="not found"):
        get_adapter("missing")
