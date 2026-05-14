"""Metamorphic property checks for P2a-3."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.composition.contract import execute_recipe_instance


class MetamorphicResult(BaseModel):
    """One metamorphic property result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    passed: bool
    error: str | None = None


def _ewm(series: pd.Series, *, span: int = 9) -> pd.Series:
    output = execute_recipe_instance(
        "indicator.ewm",
        params={"span": span, "init": "first_value"},
        inputs={"series": series},
    )["value"]
    return pd.Series(output, dtype=float)


def _constant_fixed_point() -> bool:
    series = pd.Series([3.5] * 32, dtype=float)
    actual = _ewm(series, span=9)
    return bool(np.allclose(actual.to_numpy(), np.full(len(series), 3.5), atol=1e-9))


def _affine_shift() -> bool:
    series = pd.Series(np.linspace(-10.0, 12.0, 48), dtype=float)
    shift = 7.25
    base = _ewm(series, span=13)
    shifted = _ewm(series + shift, span=13)
    return bool(np.allclose(shifted.to_numpy(), base.to_numpy() + shift, atol=1e-9))


def _prefix_stability() -> bool:
    prefix = pd.Series(np.linspace(1.0, 20.0, 24), dtype=float)
    extended = pd.concat([prefix, pd.Series([-100.0, 50.0, 75.0], dtype=float)], ignore_index=True)
    prefix_output = _ewm(prefix, span=5)
    extended_output = _ewm(extended, span=5).iloc[: len(prefix)]
    return bool(np.allclose(prefix_output.to_numpy(), extended_output.to_numpy(), atol=1e-9))


_PROPERTIES: dict[str, Callable[[], bool]] = {
    "constant_fixed_point": _constant_fixed_point,
    "affine_shift": _affine_shift,
    "prefix_stability": _prefix_stability,
}


def run_metamorphic_property(name: str) -> MetamorphicResult:
    """Run one named metamorphic property."""

    if name not in _PROPERTIES:
        return MetamorphicResult(name=name, passed=False, error="unknown property")
    try:
        return MetamorphicResult(name=name, passed=_PROPERTIES[name]())
    except Exception as exc:
        return MetamorphicResult(name=name, passed=False, error=f"{type(exc).__name__}: {exc}")


def run_metamorphic_properties(names: list[str]) -> list[MetamorphicResult]:
    """Run named metamorphic properties."""

    return [run_metamorphic_property(name) for name in names]


def metamorphic_pass(names: list[str]) -> bool:
    """Return whether every named metamorphic property passes."""

    return bool(names) and all(result.passed for result in run_metamorphic_properties(names))
