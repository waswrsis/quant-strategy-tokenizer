from __future__ import annotations

from quant_strategy_tokenizer.composition.metamorphic import (
    metamorphic_pass,
    run_metamorphic_properties,
    run_metamorphic_property,
)


def test_indicator_ewm_metamorphic_properties_pass() -> None:
    properties = ["constant_fixed_point", "affine_shift", "prefix_stability"]
    results = run_metamorphic_properties(properties)

    assert [result.name for result in results] == properties
    assert all(result.passed for result in results)
    assert metamorphic_pass(properties)


def test_unknown_metamorphic_property_fails() -> None:
    result = run_metamorphic_property("unknown_property")

    assert result.passed is False
    assert result.error == "unknown property"
