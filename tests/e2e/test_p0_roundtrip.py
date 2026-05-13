from __future__ import annotations

import copy
from pathlib import Path

from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from tests.helpers import load_sample_market

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"


def test_p0_roundtrip() -> None:
    ir = load_strategy_file(STRATEGY)

    validation = validate(ir)
    assert validation.ok, validation.failures

    canonical = canonicalize(ir)
    assert canonical.form == "canonical"
    assert canonical.graph

    hashes = compute_hashes(canonical)
    assert hashes.graph_hash.startswith("sha256:")
    assert hashes.param_hash.startswith("sha256:")
    assert hashes.instance_hash.startswith("sha256:")

    market = load_sample_market(MARKET)
    result = execute_strategy(ir, {"market": market})

    assert result.ok, result.error
    assert result.trace.nodes
    assert "plan" in result.outputs
    assert "plan" in result.trace.outputs

    explanation = explain_ir(ir, level="L1")
    assert "KDJ" in explanation or "kdj" in explanation
    assert "cross" in explanation.lower()
    assert "noop" in explanation.lower()


def test_p0_hash_compare_lookback_change() -> None:
    ir_9 = load_strategy_file(STRATEGY)
    ir_14 = copy.deepcopy(ir_9)

    for recipe in ir_14.recipes:
        if recipe.id == "kdj":
            recipe.params["lookback"] = 14

    h9 = compute_hashes(canonicalize(ir_9))
    h14 = compute_hashes(canonicalize(ir_14))

    assert h9.graph_hash == h14.graph_hash
    assert h9.param_hash != h14.param_hash
    assert h9.instance_hash != h14.instance_hash
