"""Provenance tag model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from types import MappingProxyType
from typing import Any, Literal

TagAttachedByLiteral = Literal["recipe_compiler", "trusted_generator", "user_authored"]
LegacyTagAttachedByLiteral = Literal["recipe_compiler", "trusted_generator", "user_authored", "spike_manual"]
ImmutableParamValue = (
    str
    | int
    | float
    | bool
    | None
    | tuple["ImmutableParamValue", ...]
    | Mapping[str, "ImmutableParamValue"]
)

MAX_PARAM_DEPTH = 8


def _round_float(value: float) -> float:
    return float(f"{value:.15g}")


def _canonicalize_param_value(value: Any, *, depth: int = 0) -> ImmutableParamValue:
    if depth > MAX_PARAM_DEPTH:
        raise ValueError(f"ProvenanceTag params exceed max depth {MAX_PARAM_DEPTH}")

    if value is None or isinstance(value, str) or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("ProvenanceTag params reject NaN and Infinity")
        return _round_float(value)
    if isinstance(value, bytes | bytearray):
        raise TypeError("ProvenanceTag params reject bytes")
    if isinstance(value, tuple):
        raise TypeError("ProvenanceTag params reject tuple; use list")
    if isinstance(value, list):
        return tuple(
            _canonicalize_param_value(item, depth=depth + 1)
            for item in value
        )
    if isinstance(value, Mapping):
        for key in value:
            if not isinstance(key, str):
                raise TypeError("ProvenanceTag params require string dict keys")
        return MappingProxyType(
            {
                key: _canonicalize_param_value(value[key], depth=depth + 1)
                for key in sorted(value)
            }
        )
    raise TypeError(f"Unsupported ProvenanceTag param value: {type(value).__name__}")


def canonicalize_params(params: Mapping[str, Any]) -> Mapping[str, ImmutableParamValue]:
    """Return immutable canonical params suitable for provenance metadata."""

    canonical = _canonicalize_param_value(params)
    if not isinstance(canonical, Mapping):
        raise TypeError("ProvenanceTag params must be a mapping")
    return canonical


@dataclass(frozen=True)
class TagAttachedBy:
    """Entity that attached a provenance tag."""

    type: TagAttachedByLiteral = "recipe_compiler"
    signed_by: str | None = None
    timestamp: datetime | None = None


def normalize_tag_attached_by(
    value: TagAttachedBy | LegacyTagAttachedByLiteral | Mapping[str, Any],
) -> TagAttachedBy:
    """Normalize P2a-0 string attachers to the P2a-1 structured form."""

    if isinstance(value, TagAttachedBy):
        return value
    if isinstance(value, str):
        tag_type = "recipe_compiler" if value == "spike_manual" else value
        return TagAttachedBy(type=tag_type)  # type: ignore[arg-type]
    if isinstance(value, Mapping):
        raw_type = value.get("type", "recipe_compiler")
        tag_type = "recipe_compiler" if raw_type == "spike_manual" else raw_type
        timestamp = value.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return TagAttachedBy(
            type=tag_type,  # type: ignore[arg-type]
            signed_by=value.get("signed_by"),
            timestamp=timestamp,
        )
    raise TypeError(f"Unsupported tag_attached_by value: {type(value).__name__}")


@dataclass(frozen=True)
class ProvenanceTag:
    """Provenance attached to a primitive node by a recipe compiler."""

    semantic_id: str
    version: int
    params: Mapping[str, Any] = field(default_factory=dict)
    role: str | None = None
    tag_attached_by: TagAttachedBy | LegacyTagAttachedByLiteral | Mapping[str, Any] = field(
        default_factory=TagAttachedBy
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", canonicalize_params(self.params))
        object.__setattr__(
            self,
            "tag_attached_by",
            normalize_tag_attached_by(self.tag_attached_by),
        )
