from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from tests.ir.validator_helpers import (
    empty_recipe_registry,
    make_policy_registry,
    make_pretrade_ir,
    make_research_ir,
    make_token,
)


def test_pure_allowed_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", purity="pure"))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert result.ok, result.failures


def test_contextual_read_allowed_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", purity="contextual_read"))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert result.ok, result.failures


def test_external_read_rejected_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", purity="external_read"))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert not result.ok
    assert result.failures[0].kind == "purity_violation"


def test_external_write_rejected_in_research() -> None:
    registry = make_policy_registry(make_token("test.signal", purity="external_write"))

    result = validate(make_research_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="research")

    assert not result.ok
    assert result.failures[0].kind == "purity_violation"


def test_purity_violation_has_repair_hint() -> None:
    registry = make_policy_registry(make_token("test.signal", purity="external_read"))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert result.failures
    assert result.failures[0].repair_hint
    assert result.failures[0].repair_hint["kind"] == "replace_token_or_change_profile"
