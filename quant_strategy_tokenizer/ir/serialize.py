"""Strategy IR serialization helpers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from .model import StrategyIR


def to_plain(value: Any) -> Any:
    """Convert pydantic and nested values to plain JSON-compatible data."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    return value


def to_json(ir: StrategyIR, *, indent: int | None = 2) -> str:
    """Serialize IR to stable JSON."""

    return json.dumps(to_plain(ir), ensure_ascii=False, indent=indent, sort_keys=True)
