"""Minimal provenance tag model for the P2a-0 spike."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Literal

TagAttachedByLiteral = Literal["recipe_compiler", "user_authored", "spike_manual"]
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
class ProvenanceTag:
    """Provenance attached to a primitive node by a recipe compiler."""

    semantic_id: str
    version: int
    params: Mapping[str, Any] = field(default_factory=dict)
    role: str | None = None
    tag_attached_by: TagAttachedByLiteral = "spike_manual"

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", canonicalize_params(self.params))
