"""Local in-memory P0 Strategy IR executor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.core.errors import ErrorKind
from quant_strategy_tokenizer.core.output import (
    TokenOutput,
    jsonable_value,
    normalize_token_output,
    summarize_value,
)
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validate import ValidationFailure, validate
from quant_strategy_tokenizer.runtime.trace import Trace, TraceNode, write_trace
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry


class ExecutionResult(BaseModel):
    """Execution result with outputs and trace."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ok: bool
    outputs: dict[str, Any] = Field(default_factory=dict)
    trace: Trace
    error: str | None = None
    validation_failures: list[ValidationFailure] = Field(default_factory=list)


class UnresolvedReferenceError(KeyError):
    """Runtime graph input reference could not be resolved."""


def _looks_like_graph_ref(value: str) -> bool:
    return "." in value and not value.startswith("$")


def _resolve_external(ref: str, externals: dict[str, Any]) -> Any:
    pieces = ref.removeprefix("$externals.").split(".")
    if not pieces or pieces[0] not in externals:
        raise KeyError(f"Missing external {ref!r}")
    value = externals[pieces[0]]
    for part in pieces[1:]:
        if isinstance(value, pd.DataFrame):
            value = value[part]
        elif isinstance(value, dict):
            value = value[part]
        else:
            value = getattr(value, part)
    return value


def _resolve_value(value: Any, outputs: dict[str, Any], externals: dict[str, Any]) -> Any:
    if isinstance(value, str):
        if value.startswith("$externals."):
            return _resolve_external(value, externals)
        if value in outputs:
            return outputs[value]
        if _looks_like_graph_ref(value):
            raise UnresolvedReferenceError(f"Unresolved graph reference: {value!r}")
        return value
    if isinstance(value, list):
        return [_resolve_value(item, outputs, externals) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(item, outputs, externals) for key, item in value.items()}
    return value


def _empty_trace(ir: StrategyIR, instance_hash: str) -> Trace:
    return Trace(
        run_id="p0-local",
        strategy_instance_hash=instance_hash,
        ir_version=ir.ir_version,
        canonical_version=ir.canonical_version,
    )


def _add_trace_node(
    trace: Trace,
    *,
    node_id: str,
    token: str,
    token_version: int,
    behavior_version: int,
    output: TokenOutput,
) -> None:
    trace.nodes.append(
        TraceNode(
            id=node_id,
            token=token,
            token_version=token_version,
            behavior_version=behavior_version,
            status=output.status,
            output_summary={port: summarize_value(value) for port, value in output.values.items()},
            warnings=output.warnings,
            unknown_reason=output.unknown_reason,
            error_kind=output.error_kind,
        )
    )
    if output.status == "unknown":
        trace.unknown_count += 1
    if output.status == "error":
        trace.error_count += 1


def execute_strategy(
    ir: StrategyIR,
    externals: dict[str, Any],
    *,
    trace_path: str | Path | None = None,
    registry: Registry | None = None,
    profile: ProfileLiteral = "research",
) -> ExecutionResult:
    """Canonicalize, validate, and execute a Strategy IR."""

    canonical = canonicalize(ir)
    validation = validate(canonical, profile=profile)
    hashes = compute_hashes(canonical)
    trace = _empty_trace(canonical, hashes.instance_hash)
    if not validation.ok:
        return ExecutionResult(
            ok=False,
            trace=trace,
            error="validation_failed",
            validation_failures=validation.failures,
        )

    token_registry = registry or get_registry()
    node_outputs: dict[str, Any] = {}

    for node in canonical.graph:
        registered = token_registry.get(node.token, node.v)
        try:
            resolved_inputs = _resolve_value(node.inputs, node_outputs, externals)
            raw_output = registered.executor(**resolved_inputs, **node.params)
            output = normalize_token_output(raw_output)
        except UnresolvedReferenceError as exc:
            output = TokenOutput(
                status="error",
                error_kind=ErrorKind.missing_input.value,
                values={},
                warnings=[str(exc)],
            )
        except Exception as exc:
            output = TokenOutput(
                status="error",
                error_kind=ErrorKind.executor_exception.value,
                values={},
                warnings=[f"{type(exc).__name__}: {exc}"],
            )

        for port, value in output.values.items():
            node_outputs[f"{node.id}.{port}"] = value

        _add_trace_node(
            trace,
            node_id=node.id,
            token=node.token,
            token_version=node.v,
            behavior_version=registered.spec.behavior_version,
            output=output,
        )

        if output.status == "error":
            trace.outputs = {}
            if trace_path is not None:
                write_trace(trace, trace_path)
            return ExecutionResult(ok=False, trace=trace, error=output.error_kind or "executor_error")

    final_outputs = {
        port: _resolve_value(ref, node_outputs, externals)
        for port, ref in canonical.outputs.items()
    }
    trace.outputs = {port: jsonable_value(value) for port, value in final_outputs.items()}
    if trace_path is not None:
        write_trace(trace, trace_path)
    return ExecutionResult(ok=True, outputs=final_outputs, trace=trace)
