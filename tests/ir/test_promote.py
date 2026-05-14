from __future__ import annotations

import pytest

from quant_strategy_tokenizer.agent.promote import promote
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML, P1_PRETRADE_READY_YAML
from tests.ir.validator_helpers import (
    empty_recipe_registry,
    make_policy_registry,
    make_pretrade_ir,
    make_token,
)


def _envelope_for(ir_hash: str, profile: str = "research") -> DeploymentEnvelope:
    return DeploymentEnvelope(strategy_instance_hash=ir_hash, profile=profile)  # type: ignore[arg-type]


def test_promote_does_not_modify_strategy_ir() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)
    before = to_json(canonicalize(ir), indent=None)
    envelope = _envelope_for(compute_hashes(ir).instance_hash)

    result = promote(ir, envelope, "pretrade")

    after = to_json(canonicalize(ir), indent=None)
    assert result.ok
    assert after == before


def test_promote_changes_only_envelope_fields() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)
    envelope = _envelope_for(compute_hashes(ir).instance_hash, profile="research")

    result = promote(ir, envelope, "pretrade", approved_by="risk-review")

    assert result.ok
    assert result.new_envelope is not None
    assert result.new_envelope.strategy_instance_hash == envelope.strategy_instance_hash
    assert result.new_envelope.notes == envelope.notes
    assert result.new_envelope.profile == "pretrade"
    assert result.new_envelope.approved_by == "risk-review"
    assert result.new_envelope.approved_at is not None


def test_promote_invariant_three_layer_hash() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)
    before = compute_hashes(ir)
    envelope = _envelope_for(before.instance_hash)

    result = promote(ir, envelope, "pretrade")
    after = compute_hashes(ir)

    assert result.ok
    assert before == after


def test_promote_fails_without_risk_path() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)
    envelope = _envelope_for(compute_hashes(ir).instance_hash)

    result = promote(ir, envelope, "pretrade")

    assert not result.ok
    assert result.new_envelope is None
    assert any(failure.kind == "missing_risk_path" for failure in result.new_validation_failures)


def test_promote_rejects_future_data_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = make_policy_registry(
        make_token(
            "test.signal",
            temporal={
                "uses_future_data": True,
                "window_mode": "trailing",
                "output_available_at": "same_bar_close",
                "max_lookback": None,
            },
        )
    )
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_registry", lambda: registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_recipe_registry", empty_recipe_registry)
    ir = make_pretrade_ir()
    envelope = _envelope_for("sha256:" + "0" * 64)

    result = promote(ir, envelope, "pretrade")

    assert not result.ok
    assert any(failure.kind == "future_data_violation" for failure in result.new_validation_failures)


def test_promote_rejects_external_read_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = make_policy_registry(make_token("test.signal", purity="external_read"))
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_registry", lambda: registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_recipe_registry", empty_recipe_registry)
    ir = make_pretrade_ir()
    envelope = _envelope_for("sha256:" + "0" * 64)

    result = promote(ir, envelope, "pretrade")

    assert not result.ok
    assert any(failure.kind == "purity_violation" for failure in result.new_validation_failures)
