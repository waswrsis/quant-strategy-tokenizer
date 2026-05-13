"""Behavior contract runner for built-in token specs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from quant_strategy_tokenizer.core.output import normalize_token_output
from quant_strategy_tokenizer.tokens.registry import RegisteredToken, Registry, get_registry
from quant_strategy_tokenizer.tokens.spec import TokenSpec
from quant_strategy_tokenizer.types.decision import parse_decision
from quant_strategy_tokenizer.types.plan import parse_plan


@dataclass(frozen=True)
class ContractResult:
    """Single behavior contract outcome."""

    name: str
    passed: bool
    error: str | None = None


def _normalize_expected_value(value: Any) -> Any:
    if value is None:
        return np.nan
    if isinstance(value, str) and value.lower() == "nan":
        return np.nan
    if isinstance(value, list):
        return [_normalize_expected_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_expected_value(v) for k, v in value.items()}
    return value


def _series_from(value: Any) -> pd.Series:
    normalized = _normalize_expected_value(value)
    return pd.Series(normalized)


def _materialize(value: Any, type_ref: str) -> Any:
    if type_ref.startswith("TimeSeries"):
        return _series_from(value)
    if type_ref.startswith("Frame"):
        return pd.DataFrame(value)
    if type_ref == "Decision":
        return parse_decision(value)
    if type_ref == "Decision[]":
        if not isinstance(value, list):
            raise TypeError("Decision[] contract input must be a list")
        return [parse_decision(item) for item in value]
    if type_ref == "Plan":
        return parse_plan(value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        raw = value.model_dump(mode="json", exclude_none=True)
        if raw.get("evidence") == {}:
            raw.pop("evidence")
        return raw
    if isinstance(value, pd.Series):
        return value.to_numpy()
    if isinstance(value, dict):
        raw = {k: _plain(v) for k, v in value.items()}
        if raw.get("evidence") == {}:
            raw.pop("evidence")
        return raw
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _matches(actual: Any, expected: Any, tol: dict[str, Any]) -> bool:
    expected = _normalize_expected_value(expected)
    actual = _plain(actual)

    if isinstance(actual, np.ndarray) or isinstance(expected, list):
        try:
            actual_arr = np.asarray(actual, dtype=float)
            expected_arr = np.asarray(expected, dtype=float)
            if tol["kind"] == "absolute":
                return bool(
                    np.allclose(actual_arr, expected_arr, atol=tol["epsilon"], equal_nan=True)
                )
            if tol["kind"] == "relative":
                return bool(
                    np.allclose(actual_arr, expected_arr, rtol=tol["epsilon"], equal_nan=True)
                )
            return bool(np.array_equal(actual_arr, expected_arr, equal_nan=True))
        except (TypeError, ValueError):
            return bool(actual == expected)

    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            return False
        return all(_matches(actual[key], expected[key], tol) for key in actual)

    return bool(actual == expected)


def _resolve_registered(
    target: RegisteredToken | TokenSpec,
    registry: Registry | None = None,
) -> RegisteredToken:
    if isinstance(target, RegisteredToken):
        return target
    return (registry or get_registry()).get(target.id, target.version)


def run_contract(
    target: RegisteredToken | TokenSpec,
    contract: dict[str, Any],
    registry: Registry | None = None,
) -> ContractResult:
    """Run one token behavior contract."""

    registered = _resolve_registered(target, registry)
    spec = registered.spec
    name = str(contract["name"])
    try:
        raw_inputs = contract.get("inputs", {})
        inputs = {
            key: _materialize(raw_inputs[key], spec.inputs[key])
            for key in spec.inputs
            if key in raw_inputs
        }
        for key, value in raw_inputs.items():
            if key not in inputs:
                inputs[key] = _series_from(value) if isinstance(value, list) else value
        params = contract.get("params", {})
        output = normalize_token_output(registered.executor(**inputs, **params))

        expected_status = contract.get("expected_status", "ok")
        if output.status != expected_status:
            return ContractResult(
                name=name,
                passed=False,
                error=f"expected status {expected_status!r}, got {output.status!r}",
            )
        expected_reason = contract.get("expected_reason")
        if expected_reason is not None and output.unknown_reason != expected_reason:
            return ContractResult(
                name=name,
                passed=False,
                error=f"expected reason {expected_reason!r}, got {output.unknown_reason!r}",
            )

        expected_output = contract.get("expected_output")
        if expected_output is None:
            return ContractResult(name=name, passed=True)

        tol = contract.get("tolerance", {"kind": "absolute", "epsilon": 1e-9})
        for port, expected in expected_output.items():
            if port not in output.values:
                return ContractResult(name=name, passed=False, error=f"missing output port {port!r}")
            if not _matches(output.values[port], expected, tol):
                return ContractResult(
                    name=name,
                    passed=False,
                    error=f"output {port!r} mismatch: actual={_plain(output.values[port])!r} expected={expected!r}",
                )
        return ContractResult(name=name, passed=True)
    except Exception as exc:
        return ContractResult(name=name, passed=False, error=f"{type(exc).__name__}: {exc}")
