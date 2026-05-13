"""Agent-facing P0 API wrappers."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as _explain_ir
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validate import ValidationResult
from quant_strategy_tokenizer.ir.validate import validate as _validate
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.runtime.executor import ExecutionResult, execute_strategy
from quant_strategy_tokenizer.tokens.registry import get_registry


def vocabulary(layer: str | None = None) -> list[dict[str, Any]]:
    """Return serializable token specs."""

    registry = get_registry()
    specs = registry.list_tokens(layer=layer)  # type: ignore[arg-type]
    return [spec.model_dump(mode="json") for spec in specs]


def recipes(category: str | None = None) -> list[dict[str, Any]]:
    """Return serializable recipe specs."""

    registry = get_recipe_registry()
    return [spec.model_dump(mode="json") for spec in registry.list_recipes(category=category)]


def validate(ir: StrategyIR | dict[str, Any]) -> ValidationResult:
    """Validate a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _validate(parsed)


def execute(ir: StrategyIR | dict[str, Any], externals: dict[str, Any]) -> ExecutionResult:
    """Execute a Strategy IR against externals."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return execute_strategy(parsed, externals)


def explain_ir(ir: StrategyIR | dict[str, Any], level: str = "L1") -> str:
    """Explain a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _explain_ir(parsed, level=level)
