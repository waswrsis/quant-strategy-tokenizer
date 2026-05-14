from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.provenance import ProvenanceTag

ROOT = Path(__file__).resolve().parents[2]
P0_STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"

EXPECTED_P0_GRAPH_HASH = "sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947"
EXPECTED_P0_PARAM_HASH = "sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28"
EXPECTED_P0_INSTANCE_HASH = "sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d"

EXPECTED_P1_GRAPH_HASH = "sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa"
EXPECTED_P1_PARAM_HASH = "sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321"
EXPECTED_P1_INSTANCE_HASH = "sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3"


def test_p0_frozen_hashes_remain_unchanged() -> None:
    hashes = compute_hashes(load_strategy_file(P0_STRATEGY))

    assert hashes.graph_hash == EXPECTED_P0_GRAPH_HASH
    assert hashes.param_hash == EXPECTED_P0_PARAM_HASH
    assert hashes.instance_hash == EXPECTED_P0_INSTANCE_HASH


def test_p1_core_hashes_remain_unchanged_after_ewm_provenance() -> None:
    hashes = compute_hashes(load_strategy_file(P1_STRATEGY))

    assert hashes.graph_hash == EXPECTED_P1_GRAPH_HASH
    assert hashes.param_hash == EXPECTED_P1_PARAM_HASH
    assert hashes.instance_hash == EXPECTED_P1_INSTANCE_HASH


def test_non_empty_provenance_does_not_affect_hash_material() -> None:
    canonical = canonicalize(load_strategy_file(P0_STRATEGY))
    tagged_graph = [
        node.model_copy(
            update={
                "provenance": [
                    ProvenanceTag(
                        "indicator.ewm",
                        1,
                        {"span": 9},
                        role="manual",
                        tag_attached_by="spike_manual",
                    )
                ]
            }
        )
        if index == 0
        else node
        for index, node in enumerate(canonical.graph)
    ]
    tagged = canonical.model_copy(update={"graph": tagged_graph})

    assert compute_hashes(tagged) == compute_hashes(canonical)
