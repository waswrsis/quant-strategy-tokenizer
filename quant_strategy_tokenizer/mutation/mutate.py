"""P2b-0 mutation engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import ExternalSpec, GraphNode, RecipeInstance, StrategyIR
from quant_strategy_tokenizer.mutation.ops import ChangeParam, InsertBefore, MutationOp
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry


class MutationError(ValueError):
    """Mutation could not be applied."""


class MutationResult(BaseModel):
    """Mutation result with before/after hash report."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ok: bool
    ir: StrategyIR | None = None
    before_hashes: dict[str, str]
    after_hashes: dict[str, str] | None = None
    op: dict[str, Any]
    error: str | None = None


def _find_graph_node(graph: list[GraphNode], node_id: str) -> tuple[int, GraphNode]:
    for index, node in enumerate(graph):
        if node.id == node_id:
            return index, node
    raise MutationError(f"Graph node {node_id!r} not found")


def _find_recipe_instance(recipes: list[RecipeInstance], node_id: str) -> tuple[int, RecipeInstance]:
    for index, recipe in enumerate(recipes):
        if recipe.id == node_id:
            return index, recipe
    raise MutationError(f"Recipe instance {node_id!r} not found")


def _apply_change_param(ir: StrategyIR, op: ChangeParam) -> StrategyIR:
    try:
        index, node = _find_graph_node(ir.graph, op.node_id)
        graph = list(ir.graph)
        graph[index] = node.model_copy(
            update={"params": {**node.params, op.param_name: op.new_value}}
        )
        return ir.model_copy(update={"graph": graph}, deep=True)
    except MutationError:
        index, recipe = _find_recipe_instance(ir.recipes, op.node_id)
        recipes = list(ir.recipes)
        recipes[index] = recipe.model_copy(
            update={"params": {**recipe.params, op.param_name: op.new_value}}
        )
        return ir.model_copy(update={"recipes": recipes}, deep=True)


def _single_output_port(node: GraphNode, registry: Registry) -> str:
    outputs = registry.get(node.token, node.v).spec.outputs
    if len(outputs) != 1:
        raise MutationError(
            f"Inserted node {node.id!r} must declare primary_output because "
            f"{node.token}/v{node.v} has outputs {sorted(outputs)}"
        )
    return next(iter(outputs))


def _build_insert_node(
    op: InsertBefore,
    original_upstream: Any,
    registry: Registry,
) -> tuple[GraphNode, str]:
    spec = dict(op.new_node_spec)
    node_id = spec.get("id")
    token = spec.get("token")
    if not isinstance(node_id, str) or not isinstance(token, str):
        raise MutationError("new_node_spec must include string id and token")
    version = int(spec.get("v", spec.get("token_version", 1)))
    primary_input = spec.get("primary_input", op.target_input_name)
    if not isinstance(primary_input, str):
        raise MutationError("primary_input must be a string")

    inputs = dict(spec.get("inputs", {}))
    inputs.pop(primary_input, None)
    inputs[primary_input] = original_upstream
    node = GraphNode(
        id=node_id,
        token=token,
        v=version,
        params=dict(spec.get("params", {})),
        inputs=inputs,
    )

    primary_output = spec.get("primary_output")
    if primary_output is None:
        primary_output = _single_output_port(node, registry)
    if not isinstance(primary_output, str):
        raise MutationError("primary_output must be a string")
    return node, primary_output


def _apply_insert_before(
    ir: StrategyIR,
    op: InsertBefore,
    registry: Registry,
) -> StrategyIR:
    target_index, target = _find_graph_node(ir.graph, op.target_node_id)
    if op.target_input_name not in target.inputs:
        raise MutationError(
            f"Target node {op.target_node_id!r} has no input {op.target_input_name!r}; "
            f"available inputs: {sorted(target.inputs)}"
        )
    graph_ids = {node.id for node in ir.graph}
    new_node, output_port = _build_insert_node(
        op,
        target.inputs[op.target_input_name],
        registry,
    )
    if new_node.id in graph_ids:
        raise MutationError(f"Inserted node id {new_node.id!r} already exists")

    target_inputs = {
        **target.inputs,
        op.target_input_name: f"{new_node.id}.{output_port}",
    }
    new_target = target.model_copy(update={"inputs": target_inputs})
    graph = list(ir.graph)
    graph[target_index] = new_target
    graph.insert(target_index, new_node)

    externals = dict(ir.externals)
    if new_node.token.startswith("risk.") and "state" not in externals:
        externals["state"] = ExternalSpec(type="State", required=True)

    return ir.model_copy(update={"graph": graph, "externals": externals}, deep=True)


def _apply_op(ir: StrategyIR, op: MutationOp, registry: Registry) -> StrategyIR:
    if isinstance(op, ChangeParam):
        return _apply_change_param(ir, op)
    if isinstance(op, InsertBefore):
        return _apply_insert_before(ir, op, registry)
    raise AssertionError(f"Unsupported mutation op: {op!r}")


def mutate_strategy(
    ir: StrategyIR,
    op: MutationOp,
    *,
    registry: Registry | None = None,
) -> MutationResult:
    """Apply one P2b-0 mutation op."""

    token_registry = registry or get_registry()
    before = compute_hashes(ir).as_dict()
    try:
        mutated = _apply_op(ir, op, token_registry)
    except MutationError as exc:
        return MutationResult(
            ok=False,
            ir=None,
            before_hashes=before,
            op=op.model_dump(mode="json"),
            error=str(exc),
        )
    return MutationResult(
        ok=True,
        ir=mutated,
        before_hashes=before,
        after_hashes=compute_hashes(mutated).as_dict(),
        op=op.model_dump(mode="json"),
    )
