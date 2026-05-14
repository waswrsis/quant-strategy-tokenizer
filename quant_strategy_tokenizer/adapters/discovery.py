"""Local entry-point adapter discovery."""

from __future__ import annotations

from importlib import metadata

from pydantic import BaseModel, ConfigDict, Field

ADAPTER_ENTRY_POINT_GROUP = "quant_strategy_tokenizer.adapters"


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

    descriptors: list[AdapterDescriptor] = []
    for entry_point in _entry_points():
        descriptors.append(
            AdapterDescriptor(
                adapter_id=entry_point.name,
                entry_point=entry_point.value,
                module=entry_point.module,
                object_ref=".".join(entry_point.attr.split(".")) if entry_point.attr else None,
            )
        )
    return sorted(descriptors, key=lambda item: item.adapter_id)
