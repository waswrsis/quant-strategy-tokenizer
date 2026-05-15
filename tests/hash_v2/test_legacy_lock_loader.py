from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, IR_VERSION
from quant_strategy_tokenizer.ir_v04.legacy import load_legacy_lock, load_legacy_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.qst_lock.builder import build_lock
from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes

ROOT = Path(__file__).resolve().parents[2]


def test_existing_p3_lock_loads_without_v2_only_fields() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    built = build_lock(ir)
    raw = built.lock.model_dump(mode="json")

    loaded = load_legacy_lock(raw)

    assert loaded.lock_version == "qst-lock/0.1"
    assert loaded.ir_version == IR_VERSION
    assert loaded.canonical_version == CANONICAL_VERSION
    assert not hasattr(loaded, "signature_hash")


def test_legacy_lock_loads_from_canonical_json_string() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    built = build_lock(ir)
    lock_bytes = canonical_lock_bytes(built.lock.model_dump(mode="json"))

    loaded = load_legacy_lock(lock_bytes.decode("utf-8"))

    assert loaded.strategy == "kdj_cross_basic"


def test_legacy_strategy_loads_without_upgrade() -> None:
    raw = json.loads(
        json.dumps(
            {
                "ir_version": "qst-ir/0.3",
                "canonical_version": "qst-canonical/0.1",
                "strategy": "legacy",
                "strategy_version": 1,
                "form": "surface",
                "externals": {},
                "recipes": [],
                "graph": [],
                "outputs": {},
            }
        )
    )

    loaded = load_legacy_strategy(raw)

    assert loaded.ir_version == "qst-ir/0.3"


def test_non_legacy_strategy_version_rejected() -> None:
    with pytest.raises(ValueError):
        load_legacy_strategy(
            {
                "ir_version": "qst-ir/0.4",
                "canonical_version": "qst-canonical/0.4",
                "strategy": "bad",
                "strategy_version": 1,
                "form": "surface",
                "externals": {},
                "recipes": [],
                "graph": [],
                "outputs": {},
            }
        )
