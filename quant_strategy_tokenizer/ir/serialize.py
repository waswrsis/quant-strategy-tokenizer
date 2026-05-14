"""Strategy IR serialization helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any

from pydantic import BaseModel

from .model import StrategyIR


def _should_omit_item(key: object, value: Any) -> bool:
    return key == "provenance" and value == []


def to_plain(value: Any) -> Any:
    """Convert pydantic and nested values to plain JSON-compatible data."""

    if isinstance(value, BaseModel):
        return to_plain(value.model_dump(mode="python", exclude_none=True, warnings=False))
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_plain(field_value)
            for field in fields(value)
            if (field_value := getattr(value, field.name)) is not None
            and not _should_omit_item(field.name, field_value)
        }
    if isinstance(value, Mapping):
        return {
            str(k): to_plain(v)
            for k, v in value.items()
            if not _should_omit_item(k, v)
        }
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    if isinstance(value, tuple):
        return [to_plain(v) for v in value]
    return value


def to_json(ir: StrategyIR, *, indent: int | None = 2) -> str:
    """Serialize IR to stable JSON."""

    return json.dumps(to_plain(ir), ensure_ascii=False, indent=indent, sort_keys=True)
