"""Recursive JSON recipe compiler."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.recipes.schema import RecipeNode, RecipeSpec
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry

MAX_RECIPE_DEPTH = 16


class CycleError(ValueError):
    """Recipe recursion cycle detected."""


class MaxDepthError(ValueError):
    """Recipe nesting exceeded P0 max depth."""


@dataclass(frozen=True)
class OutputRef:
    """Reference to a primitive node output port."""

    node_id: str
    port: str

    def to_ref(self) -> str:
        return f"{self.node_id}.{self.port}"


@dataclass(frozen=True)
class PrimitiveNode:
    """Compiled primitive token node."""

    id: str
    token: str
    version: int
    params: dict[str, Any]
    inputs: dict[str, Any]


@dataclass(frozen=True)
class CompiledRecipe:
    """Recipe compiler result."""

    nodes: list[PrimitiveNode]
    outputs: dict[str, OutputRef]


def _defaults_from_schema(params_schema: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for key, schema in params_schema.items():
        if isinstance(schema, dict) and "default" in schema:
            defaults[key] = schema["default"]
    return defaults


def _merge_params(spec: RecipeSpec, instance_params: dict[str, Any]) -> dict[str, Any]:
    merged = _defaults_from_schema(spec.params_schema)
    merged.update(instance_params)
    return merged


def _safe_eval_arithmetic(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.USub,
        ast.UAdd,
        ast.Load,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"Unsupported compute expression: {expr}")
    value = eval(compile(tree, "<qst-compute>", "eval"), {"__builtins__": {}}, {})  # noqa: S307
    return float(value)


def _resolve_compute(expr: str, params: dict[str, Any]) -> float:
    body = expr.removeprefix("$compute:")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in params:
            raise KeyError(f"Missing recipe param {key!r} in compute expression")
        return str(params[key])

    resolved = re.sub(r"\$params\.([A-Za-z_][A-Za-z0-9_]*)", replace, body)
    return _safe_eval_arithmetic(resolved)


def _resolve_ref(value: str, local_outputs: dict[str, OutputRef]) -> str:
    if value in local_outputs:
        return local_outputs[value].to_ref()
    return value


def _resolve_value(
    value: Any,
    params: dict[str, Any],
    instance_inputs: dict[str, Any],
    local_outputs: dict[str, OutputRef],
) -> Any:
    if isinstance(value, str):
        if value.startswith("$compute:"):
            return _resolve_compute(value, params)
        if value.startswith("$params."):
            key = value.removeprefix("$params.")
            return params[key]
        if value.startswith("$inputs."):
            key = value.removeprefix("$inputs.")
            return instance_inputs[key]
        return _resolve_ref(value, local_outputs)
    if isinstance(value, list):
        return [_resolve_value(item, params, instance_inputs, local_outputs) for item in value]
    if isinstance(value, dict):
        return {
            key: _resolve_value(item, params, instance_inputs, local_outputs)
            for key, item in value.items()
        }
    return value


def _resolve_param_value(value: Any, params: dict[str, Any], instance_inputs: dict[str, Any]) -> Any:
    """Resolve recipe params without rewriting plain strings as graph refs."""

    if isinstance(value, str):
        if value.startswith("$compute:"):
            return _resolve_compute(value, params)
        if value.startswith("$params."):
            return params[value.removeprefix("$params.")]
        if value.startswith("$inputs."):
            return instance_inputs[value.removeprefix("$inputs.")]
        return value
    if isinstance(value, list):
        return [_resolve_param_value(item, params, instance_inputs) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_param_value(item, params, instance_inputs) for key, item in value.items()}
    return value


def _register_local_outputs(
    local_outputs: dict[str, OutputRef],
    node_id: str,
    output_refs: dict[str, OutputRef],
) -> None:
    for port, output_ref in output_refs.items():
        local_outputs[f"{node_id}.{port}"] = output_ref
    if len(output_refs) == 1:
        only_ref = next(iter(output_refs.values()))
        local_outputs[node_id] = only_ref


def _compile_token_node(
    node: RecipeNode,
    *,
    instance_id: str,
    params: dict[str, Any],
    instance_inputs: dict[str, Any],
    local_outputs: dict[str, OutputRef],
    registry: Registry,
) -> tuple[PrimitiveNode, dict[str, OutputRef]]:
    assert node.token is not None
    registered = registry.get(node.token, node.resolved_version)
    primitive_id = f"{instance_id}.{node.id}"
    resolved_params = _resolve_param_value(node.params, params, instance_inputs)
    resolved_inputs = _resolve_value(node.inputs, params, instance_inputs, local_outputs)
    primitive = PrimitiveNode(
        id=primitive_id,
        token=node.token,
        version=node.resolved_version,
        params=resolved_params,
        inputs=resolved_inputs,
    )
    outputs = {
        port: OutputRef(node_id=primitive_id, port=port)
        for port in registered.spec.outputs
    }
    return primitive, outputs


def compile_recipe(
    *,
    recipe_id: str,
    recipe_version: int,
    instance_params: dict[str, Any],
    instance_inputs: dict[str, Any],
    instance_id: str,
    registry: Registry | None = None,
    recipe_registry: RecipeRegistry | None = None,
    _stack: tuple[str, ...] = (),
    _depth: int = 0,
) -> CompiledRecipe:
    """Compile a recipe instance into primitive token nodes."""

    if _depth > MAX_RECIPE_DEPTH:
        raise MaxDepthError(f"Recipe nesting exceeded {MAX_RECIPE_DEPTH}")
    if recipe_id in _stack:
        cycle = " -> ".join((*_stack, recipe_id))
        raise CycleError(f"Recipe cycle detected: {cycle}")

    token_registry = registry or get_registry()
    recipes = recipe_registry or get_recipe_registry()
    spec = recipes.get(recipe_id, recipe_version)
    params = _merge_params(spec, instance_params)

    primitive_nodes: list[PrimitiveNode] = []
    local_outputs: dict[str, OutputRef] = {}
    stack = (*_stack, recipe_id)

    for node in spec.graph:
        if node.token is not None:
            primitive, node_outputs = _compile_token_node(
                node,
                instance_id=instance_id,
                params=params,
                instance_inputs=instance_inputs,
                local_outputs=local_outputs,
                registry=token_registry,
            )
            primitive_nodes.append(primitive)
            _register_local_outputs(local_outputs, node.id, node_outputs)
            continue

        assert node.recipe is not None
        nested_params = _resolve_param_value(node.params, params, instance_inputs)
        nested_inputs = _resolve_value(node.inputs, params, instance_inputs, local_outputs)
        compiled = compile_recipe(
            recipe_id=node.recipe,
            recipe_version=node.resolved_version,
            instance_params=nested_params,
            instance_inputs=nested_inputs,
            instance_id=f"{instance_id}.{node.id}",
            registry=token_registry,
            recipe_registry=recipes,
            _stack=stack,
            _depth=_depth + 1,
        )
        primitive_nodes.extend(compiled.nodes)
        _register_local_outputs(local_outputs, node.id, compiled.outputs)

    recipe_outputs: dict[str, OutputRef] = {}
    for port, ref in spec.outputs.items():
        resolved = _resolve_value(ref, params, instance_inputs, local_outputs)
        if not isinstance(resolved, str) or resolved not in {
            output_ref.to_ref() for output_ref in local_outputs.values()
        }:
            # The resolved string may already be a primitive ref from local_outputs.
            if isinstance(resolved, str) and "." in resolved:
                node_id, output_port = resolved.rsplit(".", 1)
                recipe_outputs[port] = OutputRef(node_id=node_id, port=output_port)
                continue
            raise KeyError(f"Recipe {recipe_id} output {port!r} could not resolve {ref!r}")
        node_id, output_port = resolved.rsplit(".", 1)
        recipe_outputs[port] = OutputRef(node_id=node_id, port=output_port)

    return CompiledRecipe(nodes=primitive_nodes, outputs=recipe_outputs)
