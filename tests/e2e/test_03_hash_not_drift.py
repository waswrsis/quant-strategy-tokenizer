from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]

P0_STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"

P0_HASHES = {
    "graph_hash": "sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947",
    "param_hash": "sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28",
    "instance_hash": "sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d",
}

P1_HASHES = {
    "graph_hash": "sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa",
    "param_hash": "sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321",
    "instance_hash": "sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3",
}


def test_p0_frozen_hashes_do_not_drift_after_wp1() -> None:
    hashes = compute_hashes(load_strategy_file(P0_STRATEGY))

    assert hashes.graph_hash == P0_HASHES["graph_hash"]
    assert hashes.param_hash == P0_HASHES["param_hash"]
    assert hashes.instance_hash == P0_HASHES["instance_hash"]


def test_p1_reference_hashes_do_not_drift_after_wp1() -> None:
    hashes = compute_hashes(load_strategy_file(P1_STRATEGY))

    assert hashes.graph_hash == P1_HASHES["graph_hash"]
    assert hashes.param_hash == P1_HASHES["param_hash"]
    assert hashes.instance_hash == P1_HASHES["instance_hash"]
