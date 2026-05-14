"""Local entry-point adapter discovery."""

from __future__ import annotations

from importlib import metadata

from pydantic import BaseModel, ConfigDict, Field

ADAPTER_ENTRY_POINT_GROUP = "quant_strategy_tokenizer.adapters"

BUILTIN_ADAPTERS: dict[str, tuple[str, str, list[str]]] = {
    "mock-backtest": (
        "quant_strategy_tokenizer.adapters.mocks",
        "MockBacktestAdapter",
        ["backtest"],
    ),
    "mock-csv-market": (
        "quant_strategy_tokenizer.adapters.mocks",
        "CsvMarketAdapter",
        ["market_data", "csv"],
    ),
    "mock-execution": (
        "quant_strategy_tokenizer.adapters.mocks",
        "MockExecutionAdapter",
        ["execution"],
    ),
    "mock-experiment": (
        "quant_strategy_tokenizer.adapters.mocks",
        "MockExperimentAdapter",
        ["experiment"],
    ),
    "mock-parquet-market": (
        "quant_strategy_tokenizer.adapters.mocks",
        "ParquetMarketAdapter",
        ["market_data", "parquet"],
    ),
}


class AdapterDescriptor(BaseModel):
    """Public metadata for one locally installed adapter entry point."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_id: str
    entry_point: str
    module: str
    object_ref: str | None = None
    capabilities: list[str] = Field(default_factory=list)


def _entry_points() -> list[metadata.EntryPoint]:
    return list(metadata.entry_points(group=ADAPTER_ENTRY_POINT_GROUP))


def discover_adapters() -> list[AdapterDescriptor]:
    """Discover local qst adapter entry points without network access."""

    descriptors: dict[str, AdapterDescriptor] = {
        adapter_id: AdapterDescriptor(
            adapter_id=adapter_id,
            entry_point=f"{module}:{object_ref}",
            module=module,
            object_ref=object_ref,
            capabilities=capabilities,
        )
        for adapter_id, (module, object_ref, capabilities) in BUILTIN_ADAPTERS.items()
    }
    for entry_point in _entry_points():
        existing = descriptors.get(entry_point.name)
        descriptors[entry_point.name] = AdapterDescriptor(
            adapter_id=entry_point.name,
            entry_point=entry_point.value,
            module=entry_point.module,
            object_ref=".".join(entry_point.attr.split(".")) if entry_point.attr else None,
            capabilities=existing.capabilities if existing is not None else [],
        )
    return sorted(descriptors.values(), key=lambda item: item.adapter_id)
