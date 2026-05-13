"""P0 runtime trace models and writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quant_strategy_tokenizer.core.output import jsonable_value


class TraceNode(BaseModel):
    """One node execution record."""

    id: str
    token: str
    token_version: int
    behavior_version: int
    status: str
    output_summary: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    unknown_reason: str | None = None
    error_kind: str | None = None


class Trace(BaseModel):
    """P0 trace."""

    run_id: str
    strategy_instance_hash: str
    ir_version: str
    canonical_version: str
    nodes: list[TraceNode] = Field(default_factory=list)
    unknown_count: int = 0
    error_count: int = 0
    outputs: dict[str, Any] = Field(default_factory=dict)


def write_trace(trace: Trace, path: str | Path) -> None:
    """Write trace JSON to disk."""

    Path(path).write_text(
        json.dumps(jsonable_value(trace.model_dump()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
