from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy, load_strategy_file

ROOT = Path(__file__).resolve().parents[2]


def test_load_validate_canonicalize_hash_reference() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    assert validate(ir).ok
    canonical = canonicalize(ir)
    assert canonical.form == "canonical"
    assert canonical.recipes == []
    assert len(canonical.graph) == 13
    assert [node.id for node in canonical.graph] == [f"n{i}" for i in range(13)]
    hashes = compute_hashes(ir)
    assert hashes.graph_hash.startswith("sha256:")
    assert hashes.param_hash.startswith("sha256:")
    assert hashes.instance_hash.startswith("sha256:")


def test_external_refs_normalize() -> None:
    ir = load_strategy(
        """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: s
strategy_version: 1
form: surface
externals:
  market:
    type: Frame[OHLCV]
    required: true
graph: []
outputs: {}
recipes:
  - id: e
    recipe: indicator.ewm
    version: 1
    params: {span: 3}
    inputs: {series: market.close}
"""
    )
    assert ir.recipes[0].inputs["series"] == "$externals.market.close"


def test_broken_strategy_gets_repair_hint() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "broken_no_lift.qst.yaml")
    result = validate(ir)
    assert not result.ok
    failure = result.failures[0]
    assert failure.kind == "type_mismatch"
    assert failure.repair_hint is not None
