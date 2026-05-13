from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_PRETRADE_READY_YAML


def test_research_allows_p1_ready_strategy() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)

    result = validate(ir, profile="research")

    assert result.ok


def test_pretrade_profile_accepts_explicit_risk_path() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)

    result = validate(ir, profile="pretrade")

    assert result.ok
