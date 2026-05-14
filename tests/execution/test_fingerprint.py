from __future__ import annotations

import math

import pytest

from quant_strategy_tokenizer.execution import canonical_params_bytes, compute_all_fingerprints
from quant_strategy_tokenizer.ir.model import GraphNode
from quant_strategy_tokenizer.provenance import ProvenanceTag


def test_same_token_params_different_external_input_has_different_fingerprint() -> None:
    graph = [
        GraphNode(
            id="btc_close",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.btc"},
        ),
        GraphNode(
            id="eth_close",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.eth"},
        ),
    ]

    fingerprints = compute_all_fingerprints(graph)

    assert fingerprints["btc_close"] != fingerprints["eth_close"]


def test_isomorphic_upstream_subgraphs_have_same_fingerprint() -> None:
    graph = [
        GraphNode(
            id="close_a",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.market"},
        ),
        GraphNode(
            id="max_a",
            token="window.max",
            params={"window": 3},
            inputs={"series": "close_a.value"},
        ),
        GraphNode(
            id="close_b",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.market"},
        ),
        GraphNode(
            id="max_b",
            token="window.max",
            params={"window": 3},
            inputs={"series": "close_b.value"},
        ),
    ]

    fingerprints = compute_all_fingerprints(graph)

    assert fingerprints["close_a"] == fingerprints["close_b"]
    assert fingerprints["max_a"] == fingerprints["max_b"]


def test_upstream_output_port_is_part_of_fingerprint_material() -> None:
    graph = [
        GraphNode(
            id="source",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.market"},
        ),
        GraphNode(
            id="use_value",
            token="math.add",
            inputs={"a": "source.value", "b": "$externals.other"},
        ),
        GraphNode(
            id="use_other",
            token="math.add",
            inputs={"a": "source.other", "b": "$externals.other"},
        ),
    ]

    fingerprints = compute_all_fingerprints(graph)

    assert fingerprints["use_value"] != fingerprints["use_other"]


def test_node_id_and_provenance_are_excluded_from_fingerprint() -> None:
    graph = [
        GraphNode(
            id="close_a",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.market"},
        ),
        GraphNode(
            id="close_b",
            token="data.column",
            params={"column": "close"},
            inputs={"frame": "$externals.market"},
            provenance=[ProvenanceTag(semantic_id="indicator.ewm", version=1)],
        ),
    ]

    fingerprints = compute_all_fingerprints(graph)

    assert fingerprints["close_a"] == fingerprints["close_b"]


@pytest.mark.parametrize(
    "params",
    [
        {"x": math.nan},
        {"x": math.inf},
        {"x": b"bytes"},
        {"x": (1, 2)},
        {"x": {"nested": {"too": {"deep": {"for": {"this": {"small": {"limit": {"x": 1}}}}}}}}},
    ],
)
def test_canonical_params_bytes_reject_invalid_values(params: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        canonical_params_bytes(params)


def test_canonical_params_bytes_are_stable() -> None:
    left = {"b": [2.0, 3.141592653589793], "a": {"z": 1, "m": True}}
    right = {"a": {"m": True, "z": 1}, "b": [2.0, 3.141592653589793]}

    assert canonical_params_bytes(left) == canonical_params_bytes(right)
