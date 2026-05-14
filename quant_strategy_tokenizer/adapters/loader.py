"""Load local adapter entry points."""

from __future__ import annotations

from importlib import import_module, metadata
from typing import Any

from quant_strategy_tokenizer.adapters.discovery import ADAPTER_ENTRY_POINT_GROUP, BUILTIN_ADAPTERS


def _entry_points() -> list[metadata.EntryPoint]:
    return list(metadata.entry_points(group=ADAPTER_ENTRY_POINT_GROUP))


def get_adapter(adapter_id: str) -> Any:
    """Load and instantiate a local adapter entry point by id."""

    for entry_point in _entry_points():
        if entry_point.name != adapter_id:
            continue
        loaded = entry_point.load()
        if callable(loaded):
            return loaded()
        return loaded
    if adapter_id in BUILTIN_ADAPTERS:
        module_name, object_ref, _capabilities = BUILTIN_ADAPTERS[adapter_id]
        loaded = getattr(import_module(module_name), object_ref)
        return loaded() if callable(loaded) else loaded
    raise KeyError(f"Adapter {adapter_id!r} not found")
