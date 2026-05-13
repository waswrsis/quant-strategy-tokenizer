from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML, P1_PRETRADE_READY_YAML


def test_pretrade_missing_risk_path_fails_with_hint() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)

    result = validate(ir, profile="pretrade")

    assert not result.ok
    failure = result.failures[0]
    assert failure.kind == "missing_risk_path"
    assert failure.repair_hint is not None
    assert "risk.position_cap" in str(failure.repair_hint)


def test_research_missing_risk_path_does_not_trigger() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)

    result = validate(ir, profile="research")

    assert result.ok


def test_pretrade_risk_path_uses_ancestors() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)

    result = validate(ir, profile="pretrade")

    assert result.ok
