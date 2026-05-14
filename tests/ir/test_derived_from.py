from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.execution.fingerprint import compute_all_fingerprints
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import DerivedFrom, StrategyIR
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"


def _lineage(parent_hash: str | None = None) -> DerivedFrom:
    return DerivedFrom(parent_instance_hash=parent_hash or "sha256:" + "0" * 64)


def test_loader_accepts_ir_03_and_031() -> None:
    ir = load_strategy_file(STRATEGY)
    raw = ir.model_dump(mode="json")
    raw["ir_version"] = "qst-ir/0.3.1"
    raw["derived_from"] = _lineage().model_dump(mode="json")

    parsed = StrategyIR.model_validate(raw)

    assert ir.ir_version == "qst-ir/0.3"
    assert parsed.ir_version == "qst-ir/0.3.1"
    assert parsed.derived_from is not None


def test_ir_03_rejects_derived_from() -> None:
    ir = load_strategy_file(STRATEGY)
    raw = ir.model_dump(mode="json")
    raw["derived_from"] = _lineage().model_dump(mode="json")

    with pytest.raises(ValidationError, match=r"qst-ir/0\.3 strategies cannot have derived_from"):
        StrategyIR.model_validate(raw)


def test_canonicalize_carries_derived_from_without_upgrading_parent() -> None:
    parent = load_strategy_file(STRATEGY)
    forked = agent.fork(parent, "kdj_variant")

    canonical = canonicalize(forked)

    assert parent.ir_version == "qst-ir/0.3"
    assert canonical.ir_version == "qst-ir/0.3.1"
    assert canonical.derived_from == forked.derived_from


def test_hash_ignores_derived_from() -> None:
    parent = load_strategy_file(STRATEGY)
    parent_hash = compute_hashes(parent).instance_hash
    raw = parent.model_dump(mode="json")
    raw["ir_version"] = "qst-ir/0.3.1"
    no_lineage = StrategyIR.model_validate(raw)
    raw["derived_from"] = _lineage(parent_hash).model_dump(mode="json")
    with_lineage = StrategyIR.model_validate(raw)

    assert compute_hashes(no_lineage) == compute_hashes(with_lineage)


def test_fingerprint_ignores_derived_from() -> None:
    parent = load_strategy_file(STRATEGY)
    parent_hash = compute_hashes(parent).instance_hash
    raw = parent.model_dump(mode="json")
    raw["ir_version"] = "qst-ir/0.3.1"
    no_lineage = canonicalize(StrategyIR.model_validate(raw))
    raw["derived_from"] = _lineage(parent_hash).model_dump(mode="json")
    with_lineage = canonicalize(StrategyIR.model_validate(raw))

    assert compute_all_fingerprints(no_lineage.graph) == compute_all_fingerprints(with_lineage.graph)
