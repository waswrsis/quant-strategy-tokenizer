"""Merkle fingerprints for canonical execution graphs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from math import isfinite
from typing import Any

from quant_strategy_tokenizer.ir.model import GraphNode
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry

MAX_PARAM_DEPTH = 8
FINGERPRINT_PREFIX = "fp_sha256:"


def _round_float(value: float) -> float:
    return float(f"{value:.15g}")


def _canonical_value(value: Any, *, depth: int = 0) -> Any:
    if depth > MAX_PARAM_DEPTH:
        raise ValueError(f"canonical params exceed max depth {MAX_PARAM_DEPTH}")
    if value is None or isinstance(value, str) or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("canonical params reject NaN and Infinity")
        return _round_float(value)
    if isinstance(value, bytes | bytearray):
        raise TypeError("canonical params reject bytes")
    if isinstance(value, tuple):
        raise TypeError("canonical params reject tuple; use list")
    if isinstance(value, list):
        return [_canonical_value(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        for key in value:
            if not isinstance(key, str):
                raise TypeError("canonical params require string dict keys")
        return {
            key: _canonical_value(value[key], depth=depth + 1)
            for key in sorted(value)
        }
    raise TypeError(f"Unsupported canonical param value: {type(value).__name__}")


def canonical_params_bytes(params: Mapping[str, Any]) -> bytes:
    """Return deterministic UTF-8 bytes for hash material."""

    return json.dumps(
        _canonical_value(params),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _ref_parts(value: str) -> tuple[str, str] | None:
    if value.startswith("$") or "." not in value:
        return None
    node_id, port = value.rsplit(".", 1)
    if not node_id or not port:
        return None
    return node_id, port


def _fingerprint_input_value(value: Any, fingerprints: dict[str, str]) -> Any:
    if isinstance(value, str):
        parts = _ref_parts(value)
        if parts is None:
            return {"kind": "external_or_literal", "value": value}
        node_id, port = parts
        upstream = fingerprints.get(node_id)
        if upstream is None:
            return {"kind": "unresolved_node_ref", "node_id": node_id, "port": port}
        return {"kind": "node_ref", "fingerprint": upstream, "port": port}
    if isinstance(value, list):
        return [_fingerprint_input_value(item, fingerprints) for item in value]
    if isinstance(value, dict):
        return {
            key: _fingerprint_input_value(value[key], fingerprints)
            for key in sorted(value)
        }
    return {"kind": "literal", "value": _canonical_value(value)}


def _node_fingerprint_material(
    node: GraphNode,
    fingerprints: dict[str, str],
    registry: Registry,
) -> dict[str, Any]:
    registered = registry.get(node.token, node.v)
    return {
        "token": node.token,
        "token_version": node.v,
        "behavior_version": registered.spec.behavior_version,
        "params": json.loads(canonical_params_bytes(node.params).decode("utf-8")),
        "inputs": {
            input_name: _fingerprint_input_value(node.inputs[input_name], fingerprints)
            for input_name in sorted(node.inputs)
        },
    }


def _hash_material(material: Mapping[str, Any]) -> str:
    raw = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return FINGERPRINT_PREFIX + hashlib.sha256(raw).hexdigest()


def compute_all_fingerprints(
    graph: list[GraphNode],
    *,
    registry: Registry | None = None,
) -> dict[str, str]:
    """Compute Merkle fingerprints for a canonical graph in graph order."""

    token_registry = registry or get_registry()
    fingerprints: dict[str, str] = {}
    for node in graph:
        fingerprints[node.id] = _hash_material(
            _node_fingerprint_material(node, fingerprints, token_registry)
        )
    return fingerprints
