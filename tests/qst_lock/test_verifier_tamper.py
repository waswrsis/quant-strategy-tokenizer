from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.provenance.verification_order import VerificationState
from quant_strategy_tokenizer.qst_lock import build_lock, verify_lock
from quant_strategy_tokenizer.qst_lock.schema import LockFile

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
ZERO_HASH = "sha256:" + ("0" * 64)


def _failure_kinds(lock: LockFile, *, canonical_ir: StrategyIR | None = None) -> set[str]:
    ir = load_strategy_file(STRATEGY)
    return {
        failure.kind
        for failure in verify_lock(ir, lock, canonical_ir=canonical_ir).failures
    }


def test_instance_hash_tamper_fails() -> None:
    built = build_lock(load_strategy_file(STRATEGY))
    tampered_hashes = built.lock.strategy_hashes.model_copy(
        update={"instance_hash": ZERO_HASH}
    )
    tampered = built.lock.model_copy(update={"strategy_hashes": tampered_hashes})

    assert "instance_hash_mismatch" in _failure_kinds(tampered, canonical_ir=built.canonical_ir)


def test_market_csv_tamper_fails(tmp_path: Path) -> None:
    ir = load_strategy_file(STRATEGY)
    built = build_lock(ir, market_path=MARKET)
    tampered_market = tmp_path / "market.csv"
    tampered_market.write_text(MARKET.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    result = verify_lock(
        ir,
        built.lock,
        canonical_ir=built.canonical_ir,
        market_path=tampered_market,
    )

    assert not result.ok
    assert any(failure.kind == "market_csv_hash_mismatch" for failure in result.failures)


def test_canonical_ir_tamper_fails() -> None:
    ir = load_strategy_file(STRATEGY)
    built = build_lock(ir)
    tampered_canonical = built.canonical_ir.model_copy(update={"strategy_version": 999})

    result = verify_lock(ir, built.lock, canonical_ir=tampered_canonical)

    assert not result.ok
    assert any(failure.kind == "canonical_ir_tampered" for failure in result.failures)


def test_surface_canonical_inconsistent_fails() -> None:
    original = load_strategy_file(STRATEGY)
    built = build_lock(original)
    changed = original.model_copy(update={"strategy_version": original.strategy_version + 1})

    result = verify_lock(changed, built.lock, canonical_ir=built.canonical_ir)

    assert not result.ok
    assert any(failure.kind == "surface_canonical_inconsistent" for failure in result.failures)


def test_qst_version_mismatch_fails() -> None:
    built = build_lock(load_strategy_file(STRATEGY))
    tampered = built.lock.model_copy(update={"qst_version": "999.0.0"})

    assert "qst_version_mismatch" in _failure_kinds(tampered, canonical_ir=built.canonical_ir)


def test_tagspec_verification_state_insufficient_fails(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    built = build_lock(load_strategy_file(STRATEGY))
    graph_hash = built.lock.tagspecs[0].graph_template_hash

    def minimal_state(_semantic_id: str, _version: int) -> tuple[VerificationState, str]:
        return "minimally_attached", graph_hash

    monkeypatch.setattr(
        "quant_strategy_tokenizer.qst_lock.verifier._current_tagspec_state",
        minimal_state,
    )

    assert (
        "tagspec_verification_state_insufficient"
        in _failure_kinds(built.lock, canonical_ir=built.canonical_ir)
    )
