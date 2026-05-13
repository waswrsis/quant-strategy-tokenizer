"""Canonicalization for Strategy Content IR."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, GraphNode, StrategyIR
from quant_strategy_tokenizer.recipes.compiler import OutputRef, PrimitiveNode, compile_recipe
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry


def _round_float(value: float) -> float:
    return float(f"{value:.15g}")


def _canonical_value(value: Any) -> Any:
    if isinstance(value, float):
        return _round_float(value)
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _canonical_value(value[key]) for key in sorted(value)}
    return value


def _ref_parts(value: str) -> tuple[str, str] | None:
    if value.startswith("$"):
        return None
    if "." not in value:
        return None
    node_id, port = value.rsplit(".", 1)
    if not node_id or not port:
        return None
    return node_id, port


def _contains_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        parts = _ref_parts(value)
        if parts is not None:
            refs.append(parts[0])
    elif isinstance(value, list):
        for item in value:
            refs.extend(_contains_refs(item))
    elif isinstance(value, dict):
        for item in value.values():
            refs.extend(_contains_refs(item))
    return refs


def _rewrite_refs(value: Any, rename: dict[str, str]) -> Any:
    if isinstance(value, str):
        parts = _ref_parts(value)
        if parts is None:
            return value
        node_id, port = parts
        return f"{rename.get(node_id, node_id)}.{port}"
    if isinstance(value, list):
        return [_rewrite_refs(item, rename) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_refs(item, rename) for key, item in sorted(value.items())}
    return value


def _output_refs_for_node(node: PrimitiveNode, registry: Registry) -> dict[str, OutputRef]:
    registered = registry.get(node.token, node.version)
    return {port: OutputRef(node_id=node.id, port=port) for port in registered.spec.outputs}


def _add_resolver_entries(
    resolver: dict[str, OutputRef],
    node_id: str,
    outputs: dict[str, OutputRef],
) -> None:
    for port, ref in outputs.items():
        resolver[f"{node_id}.{port}"] = ref
    if len(outputs) == 1:
        resolver[node_id] = next(iter(outputs.values()))


def _resolve_ref_string(value: str, resolver: dict[str, OutputRef]) -> str:
    if value in resolver:
        return resolver[value].to_ref()
    return value


def _resolve_refs(value: Any, resolver: dict[str, OutputRef]) -> Any:
    if isinstance(value, str):
        return _resolve_ref_string(value, resolver)
    if isinstance(value, list):
        return [_resolve_refs(item, resolver) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_refs(item, resolver) for key, item in value.items()}
    return value


def _primitive_from_graph_node(node: GraphNode) -> PrimitiveNode:
    return PrimitiveNode(
        id=node.id,
        token=node.token,
        version=node.v,
        params=node.params,
        inputs=node.inputs,
    )


def _compute_reachable_ids(nodes: list[PrimitiveNode], output_refs: dict[str, str]) -> set[str]:
    node_by_id = {node.id: node for node in nodes}
    reachable: set[str] = set()
    stack: list[str] = []
    for ref in output_refs.values():
        parts = _ref_parts(ref)
        if parts is not None:
            stack.append(parts[0])

    while stack:
        node_id = stack.pop()
        if node_id in reachable or node_id not in node_by_id:
            continue
        reachable.add(node_id)
        stack.extend(_contains_refs(node_by_id[node_id].inputs))

    return reachable


def _topological_sort(nodes: list[PrimitiveNode]) -> list[PrimitiveNode]:
    node_by_id = {node.id: node for node in nodes}
    incoming: dict[str, set[str]] = {node.id: set() for node in nodes}
    outgoing: dict[str, set[str]] = defaultdict(set)

    for node in nodes:
        for dep in _contains_refs(node.inputs):
            if dep in node_by_id:
                incoming[node.id].add(dep)
                outgoing[dep].add(node.id)

    ready = deque(sorted(node_id for node_id, deps in incoming.items() if not deps))
    ordered: list[PrimitiveNode] = []
    while ready:
        node_id = ready.popleft()
        ordered.append(node_by_id[node_id])
        for dependent in sorted(outgoing[node_id]):
            incoming[dependent].discard(node_id)
            if not incoming[dependent]:
                ready.append(dependent)

    if len(ordered) != len(nodes):
        raise ValueError("Canonical graph contains a cycle")
    return ordered


def _finalize_node(node: PrimitiveNode, rename: dict[str, str]) -> GraphNode:
    return GraphNode(
        id=rename[node.id],
        token=node.token,
        v=node.version,
        params=_canonical_value(node.params),
        inputs=_canonical_value(_rewrite_refs(node.inputs, rename)),
    )


def canonicalize(
    ir: StrategyIR,
    registry: Registry | None = None,
    recipe_registry: RecipeRegistry | None = None,
) -> StrategyIR:
    """Canonicalize a surface Strategy IR."""

    if ir.form == "canonical":
        return ir

    token_registry = registry or get_registry()
    recipes = recipe_registry or get_recipe_registry()
    primitive_nodes: list[PrimitiveNode] = []
    resolver: dict[str, OutputRef] = {}

    for recipe_instance in ir.recipes:
        compiled = compile_recipe(
            recipe_id=recipe_instance.recipe,
            recipe_version=recipe_instance.version,
            instance_params=recipe_instance.params,
            instance_inputs=_resolve_refs(recipe_instance.inputs, resolver),
            instance_id=recipe_instance.id,
            registry=token_registry,
            recipe_registry=recipes,
        )
        primitive_nodes.extend(compiled.nodes)
        _add_resolver_entries(resolver, recipe_instance.id, compiled.outputs)

    direct_nodes = [_primitive_from_graph_node(node) for node in ir.graph]
    for node in direct_nodes:
        _add_resolver_entries(resolver, node.id, _output_refs_for_node(node, token_registry))

    resolved_direct_nodes = [
        PrimitiveNode(
            id=node.id,
            token=node.token,
            version=node.version,
            params=node.params,
            inputs=_resolve_refs(node.inputs, resolver),
        )
        for node in direct_nodes
    ]
    primitive_nodes.extend(resolved_direct_nodes)

    resolved_outputs = {
        port: _resolve_ref_string(target, resolver)
        for port, target in ir.outputs.items()
    }

    reachable = _compute_reachable_ids(primitive_nodes, resolved_outputs)
    alive_nodes = [node for node in primitive_nodes if node.id in reachable]
    sorted_nodes = _topological_sort(alive_nodes)
    rename = {node.id: f"n{i}" for i, node in enumerate(sorted_nodes)}

    final_nodes = [_finalize_node(node, rename) for node in sorted_nodes]
    final_outputs = {
        port: _rewrite_refs(target, rename)
        for port, target in sorted(resolved_outputs.items())
    }

    return StrategyIR(
        ir_version=ir.ir_version,
        canonical_version=CANONICAL_VERSION,
        strategy=ir.strategy,
        strategy_version=ir.strategy_version,
        form="canonical",
        externals=ir.externals,
        recipes=[],
        graph=final_nodes,
        outputs=final_outputs,
    )
