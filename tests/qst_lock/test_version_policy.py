from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.qst_lock import build_lock, verify_lock

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def test_strict_policy_passes() -> None:
    ir = load_strategy_file(STRATEGY)
    built = build_lock(ir)

    result = verify_lock(ir, built.lock, canonical_ir=built.canonical_ir)

    assert result.ok, result.failures


def test_same_minor_policy_is_unsupported() -> None:
    ir = load_strategy_file(STRATEGY)
    built = build_lock(ir, qst_version_policy="same_minor")

    result = verify_lock(ir, built.lock, canonical_ir=built.canonical_ir)

    assert not result.ok
    assert any(failure.kind == "qst_version_policy_unsupported" for failure in result.failures)
