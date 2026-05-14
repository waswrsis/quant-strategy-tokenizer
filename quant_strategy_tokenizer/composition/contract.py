"""Recipe contract runner for P2a-3 composition validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.core.output import TokenOutput, normalize_token_output
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry


class RecipeContractCase(BaseModel):
    """One recipe contract case."""

    model_config = ConfigDict(extra="forbid")

    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_outputs: dict[str, Any]
    tolerance: dict[str, Any] = Field(default_factory=lambda: {"kind": "absolute", "epsilon": 1e-9})


class RecipeContractSuite(BaseModel):
    """A declarative recipe contract suite."""

    model_config = ConfigDict(extra="forbid")

    recipe: str
    version: int = 1
    cases: list[RecipeContractCase]


class RecipeContractResult(BaseModel):
    """Recipe contract run result."""

    name: str
    passed: bool
    error: str | None = None


def load_contract_suite(path: str | Path) -> RecipeContractSuite:
    """Load a recipe contract suite from YAML."""

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("contract suite must contain a mapping")
    return RecipeContractSuite.model_validate(raw)


def _series_from(value: Any) -> pd.Series:
    return pd.Series([np.nan if item is None else item for item in value]) if isinstance(value, list) else value


def _materialize_input(value: Any, type_ref: str) -> Any:
    if type_ref.startswith("TimeSeries"):
        return _series_from(value)
    return value


def _resolve_value(value: Any, outputs: dict[str, Any]) -> Any:
    if isinstance(value, str) and value in outputs:
        return outputs[value]
    if isinstance(value, list):
        return [_resolve_value(item, outputs) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(item, outputs) for key, item in value.items()}
    return value


def execute_recipe_instance(
    recipe_id: str,
    *,
    recipe_version: int = 1,
    params: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
    registry: Registry | None = None,
    recipe_registry: RecipeRegistry | None = None,
) -> dict[str, Any]:
    """Execute a compiled recipe instance and return recipe outputs."""

    token_registry = registry or get_registry()
    recipes = recipe_registry or get_recipe_registry()
    recipe_spec = recipes.get(recipe_id, recipe_version)
    materialized_inputs = {
        key: _materialize_input((inputs or {})[key], type_ref)
        for key, type_ref in recipe_spec.inputs.items()
        if key in (inputs or {})
    }
    compiled = compile_recipe(
        recipe_id=recipe_id,
        recipe_version=recipe_version,
        instance_params=params or {},
        instance_inputs=materialized_inputs,
        instance_id="contract",
        registry=token_registry,
        recipe_registry=recipes,
    )

    outputs: dict[str, Any] = {}
    for node in compiled.nodes:
        registered = token_registry.get(node.token, node.version)
        resolved_inputs = _resolve_value(node.inputs, outputs)
        output = normalize_token_output(registered.executor(**resolved_inputs, **node.params))
        if output.status != "ok":
            raise RuntimeError(f"{node.id} returned status={output.status}")
        for port, value in output.values.items():
            outputs[f"{node.id}.{port}"] = value

    return {port: outputs[ref.to_ref()] for port, ref in compiled.outputs.items()}


def _plain(value: Any) -> Any:
    if isinstance(value, pd.Series):
        return value.to_numpy(dtype=float, na_value=np.nan)
    if isinstance(value, TokenOutput):
        return value.values
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _normalize_expected(value: Any) -> Any:
    if value is None:
        return np.nan
    if isinstance(value, str) and value.lower() == "nan":
        return np.nan
    if isinstance(value, list):
        return [_normalize_expected(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_expected(item) for key, item in value.items()}
    return value


def _matches(actual: Any, expected: Any, tolerance: dict[str, Any]) -> bool:
    actual = _plain(actual)
    expected = _normalize_expected(expected)
    try:
        actual_arr = np.asarray(actual, dtype=float)
        expected_arr = np.asarray(expected, dtype=float)
        if tolerance["kind"] == "relative":
            return bool(np.allclose(actual_arr, expected_arr, rtol=tolerance["epsilon"], equal_nan=True))
        return bool(np.allclose(actual_arr, expected_arr, atol=tolerance["epsilon"], equal_nan=True))
    except (TypeError, ValueError):
        return bool(actual == expected)


def run_contract_case(suite: RecipeContractSuite, case: RecipeContractCase) -> RecipeContractResult:
    """Run one recipe contract case."""

    try:
        outputs = execute_recipe_instance(
            suite.recipe,
            recipe_version=suite.version,
            params=case.params,
            inputs=case.inputs,
        )
        for port, expected in case.expected_outputs.items():
            if port not in outputs:
                return RecipeContractResult(name=case.name, passed=False, error=f"missing output {port!r}")
            if not _matches(outputs[port], expected, case.tolerance):
                return RecipeContractResult(
                    name=case.name,
                    passed=False,
                    error=f"output {port!r} mismatch",
                )
        return RecipeContractResult(name=case.name, passed=True)
    except Exception as exc:
        return RecipeContractResult(name=case.name, passed=False, error=f"{type(exc).__name__}: {exc}")


def run_contract_suite(path: str | Path) -> list[RecipeContractResult]:
    """Run all cases in a recipe contract suite."""

    suite = load_contract_suite(path)
    return [run_contract_case(suite, case) for case in suite.cases]


def contracts_pass(path: str | Path) -> bool:
    """Return whether every recipe contract passes."""

    return all(result.passed for result in run_contract_suite(path))
