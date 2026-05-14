"""Agent-facing API wrappers."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.agent.promote import PromoteResult
from quant_strategy_tokenizer.agent.promote import promote as _promote
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as _explain_ir
from quant_strategy_tokenizer.detokenize.trace_explainer import explain_trace as _explain_trace
from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope, ProfileLiteral
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validate import ValidationResult
from quant_strategy_tokenizer.ir.validate import validate as _validate
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.provenance.spec import TagSpec
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.runtime.executor import ExecutionResult, execute_strategy
from quant_strategy_tokenizer.runtime.trace import Trace
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


def tagspec_get(semantic_id: str, version: int = 1) -> TagSpec | None:
    """Return a TagSpec by semantic id and version."""

    try:
        return get_tagspec_registry().get(semantic_id, version)
    except KeyError:
        return None


def validate(ir: StrategyIR | dict[str, Any], profile: ProfileLiteral = "research") -> ValidationResult:
    """Validate a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _validate(parsed, profile=profile)


def execute(
    ir: StrategyIR | dict[str, Any],
    externals: dict[str, Any],
    profile: ProfileLiteral = "research",
) -> ExecutionResult:
    """Execute a Strategy IR against externals."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return execute_strategy(parsed, externals, profile=profile)


def explain_ir(ir: StrategyIR | dict[str, Any], level: str = "L1") -> str:
    """Explain a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _explain_ir(parsed, level=level)


def explain_trace(trace: Trace | dict[str, Any], level: str = "human") -> str:
    """Explain an execution trace."""

    parsed = trace if isinstance(trace, Trace) else Trace.model_validate(trace)
    if level not in {"human", "agent", "raw"}:
        raise ValueError(f"Unsupported trace explain level: {level}")
    return _explain_trace(parsed, level=level)  # type: ignore[arg-type]


def promote(
    ir: StrategyIR | dict[str, Any],
    envelope: DeploymentEnvelope | dict[str, Any],
    target_profile: ProfileLiteral,
    approved_by: str | None = None,
) -> PromoteResult:
    """Promote a strategy envelope to a target profile."""

    parsed_ir = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    parsed_envelope = (
        envelope
        if isinstance(envelope, DeploymentEnvelope)
        else DeploymentEnvelope.model_validate(envelope)
    )
    return _promote(parsed_ir, parsed_envelope, target_profile, approved_by=approved_by)
