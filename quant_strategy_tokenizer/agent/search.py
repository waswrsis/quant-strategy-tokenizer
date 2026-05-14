"""Read-only P3b-0 search API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.agent.index_record import IndexKind, build_index


class SearchResult(BaseModel):
    """Public search result shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: IndexKind
    id: str
    version: int
    metadata: dict[str, Any] = Field(default_factory=dict)


def search(
    kind: IndexKind,
    *,
    domain: str | None = None,
    output_type: str | None = None,
    input_types: list[str] | None = None,
    state_tag: str | None = None,
    profile_allowed: str | None = None,
    uses_token: str | None = None,
    fully_verified_only: bool = False,
    lifecycle: list[str] | None = None,
    limit: int = 100,
) -> list[SearchResult]:
    """Search token, recipe, or TagSpec index records with field filters."""

    if limit < 0:
        raise ValueError("limit must be non-negative")

    records = build_index(kind)
    matches = [
        record
        for record in records
        if record.matches(
            domain=domain,
            output_type=output_type,
            input_types=input_types,
            state_tag=state_tag,
            profile_allowed=profile_allowed,
            uses_token=uses_token,
            fully_verified_only=fully_verified_only,
            lifecycle=lifecycle,
        )
    ]
    return [
        SearchResult(
            kind=record.kind,
            id=record.id,
            version=record.version,
            metadata=record.model_dump(mode="json"),
        )
        for record in matches[:limit]
    ]
