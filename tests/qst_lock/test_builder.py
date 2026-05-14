from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, IR_VERSION
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.qst_lock import build_lock
from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes
from quant_strategy_tokenizer.qst_lock.io import read_lock, write_lock

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def test_build_lock_is_deterministic(tmp_path: Path) -> None:
    ir = load_strategy_file(STRATEGY)

    first = build_lock(ir)
    second = build_lock(ir)

    first_bytes = canonical_lock_bytes(first.lock.model_dump(mode="json", exclude_none=True))
    second_bytes = canonical_lock_bytes(second.lock.model_dump(mode="json", exclude_none=True))
    assert first_bytes == second_bytes
    assert first.canonical_ir_bytes == second.canonical_ir_bytes

    lock_path = tmp_path / "qst.lock"
    write_lock(first.lock, lock_path)
    assert read_lock(lock_path) == first.lock


def test_build_lock_records_versions_and_dependencies() -> None:
    built = build_lock(load_strategy_file(STRATEGY))
    lock = built.lock

    assert lock.ir_version == IR_VERSION
    assert lock.canonical_version == CANONICAL_VERSION
    assert lock.strategy_hashes.instance_hash.startswith("sha256:")
    assert lock.canonical_ir_hash.startswith("sha256:")
    assert {token.id for token in lock.tokens} >= {
        "smooth.linear_recursive",
        "compare.gt",
        "decision.lift_bool",
        "plan.noop",
    }
    assert [(recipe.recipe, recipe.version) for recipe in lock.recipes] == [
        ("indicator.ewm", 1)
    ]
    assert [(spec.semantic_id, spec.version, spec.verification_state) for spec in lock.tagspecs] == [
        ("indicator.ewm", 1, "fully_verified")
    ]
