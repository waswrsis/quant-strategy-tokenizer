from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from tests.ir.validator_helpers import (
    empty_recipe_registry,
    make_policy_registry,
    make_pretrade_ir,
    make_research_ir,
    make_token,
)


def _temporal(
    *,
    uses_future_data: bool = False,
    window_mode: str = "trailing",
    output_available_at: str = "same_bar_close",
) -> dict[str, object]:
    return {
        "uses_future_data": uses_future_data,
        "window_mode": window_mode,
        "output_available_at": output_available_at,
        "max_lookback": None,
    }


def test_trailing_window_allowed_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", temporal=_temporal(window_mode="trailing")))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert result.ok, result.failures


def test_centered_window_rejected_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", temporal=_temporal(window_mode="centered")))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert not result.ok
    assert result.failures[0].kind == "unsafe_temporal_window"


def test_full_sample_rejected_in_pretrade() -> None:
    registry = make_policy_registry(make_token("test.signal", temporal=_temporal(window_mode="full_sample")))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert not result.ok
    assert result.failures[0].kind == "unsafe_temporal_window"


def test_unknown_temporal_rejected_in_pretrade() -> None:
    registry = make_policy_registry(
        make_token("test.signal", temporal=_temporal(window_mode="unknown", output_available_at="unknown"))
    )

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert not result.ok
    assert result.failures[0].kind == "unsafe_temporal_window"


def test_future_data_warning_in_research() -> None:
    registry = make_policy_registry(make_token("test.signal", temporal=_temporal(uses_future_data=True)))

    result = validate(make_research_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="research")

    assert result.ok
    assert result.warnings
    assert result.warnings[0].kind == "future_data_warning"


def test_temporal_failure_has_repair_hint() -> None:
    registry = make_policy_registry(make_token("test.signal", temporal=_temporal(uses_future_data=True)))

    result = validate(make_pretrade_ir(), registry=registry, recipe_registry=empty_recipe_registry(), profile="pretrade")

    assert result.failures
    assert result.failures[0].repair_hint
