"""P2b-0 mutation engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import ExternalSpec, GraphNode, RecipeInstance, StrategyIR
from quant_strategy_tokenizer.mutation.ops import (
    ChangeParam,
    InlineRecipe,
    InsertBefore,
    MutationOp,
    ReplaceToken,
)
from quant_strategy_tokenizer.recipes.compiler import PrimitiveNode, compile_recipe
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
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


def _rewrite_refs(value: Any, refs: dict[str, str]) -> Any:
    if isinstance(value, str):
        return refs.get(value, value)
    if isinstance(value, list):
        return [_rewrite_refs(item, refs) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_refs(item, refs) for key, item in value.items()}
    return value


def _collect_used_ports(value: Any, node_id: str, output_ports: set[str]) -> set[str]:
    used: set[str] = set()
    if isinstance(value, str):
        if len(output_ports) == 1 and value == node_id:
            used.add(next(iter(output_ports)))
        elif value.startswith(f"{node_id}."):
            port = value.removeprefix(f"{node_id}.")
            if port in output_ports:
                used.add(port)
        return used
    if isinstance(value, list):
        for item in value:
            used.update(_collect_used_ports(item, node_id, output_ports))
    if isinstance(value, dict):
        for item in value.values():
            used.update(_collect_used_ports(item, node_id, output_ports))
    return used


def _used_output_ports(ir: StrategyIR, node: GraphNode, registry: Registry) -> set[str]:
    output_ports = set(registry.get(node.token, node.v).spec.outputs)
    used: set[str] = set()
    candidates = [recipe.inputs for recipe in ir.recipes]
    candidates.extend(other.inputs for other in ir.graph)
    candidates.append(ir.outputs)
    for candidate in candidates:
        used.update(_collect_used_ports(candidate, node.id, output_ports))
    return used


def _required_params(params_schema: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    for name, schema in params_schema.items():
        if not isinstance(schema, dict) or "default" not in schema:
            required.add(name)
    return required


def _graph_node_from_primitive(node: PrimitiveNode) -> GraphNode:
    return GraphNode(
        id=node.id,
        token=node.token,
        v=node.version,
        params=node.params,
        inputs=node.inputs,
        provenance=node.provenance,
    )


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


def _apply_replace_token(
    ir: StrategyIR,
    op: ReplaceToken,
    registry: Registry,
) -> StrategyIR:
    index, node = _find_graph_node(ir.graph, op.node_id)
    old_spec = registry.get(node.token, node.v).spec
    new_spec = registry.get(op.new_token, op.new_version).spec

    for port in _used_output_ports(ir, node, registry):
        if port not in new_spec.outputs:
            raise MutationError(
                f"replacement token {op.new_token}/v{op.new_version} missing used output port {port!r}"
            )
        if new_spec.outputs[port] != old_spec.outputs[port]:
            raise MutationError(
                f"replacement output {port!r} type mismatch: "
                f"{old_spec.outputs[port]} -> {new_spec.outputs[port]}"
            )

    new_inputs: dict[str, Any] = {}
    for new_port, expected_type in new_spec.inputs.items():
        old_port = op.input_mapping.get(new_port, new_port)
        if old_port not in node.inputs:
            raise MutationError(
                f"replacement input {new_port!r} maps to missing old input {old_port!r}"
            )
        if old_port in old_spec.inputs and old_spec.inputs[old_port] != expected_type:
            raise MutationError(
                f"replacement input {new_port!r} type mismatch: "
                f"{old_spec.inputs[old_port]} -> {expected_type}"
            )
        new_inputs[new_port] = node.inputs[old_port]

    new_params = {
        key: value
        for key, value in node.params.items()
        if key in new_spec.params_schema
    }
    new_params.update(op.new_params)
    missing_params = _required_params(new_spec.params_schema) - set(new_params)
    if missing_params:
        raise MutationError(
            f"replacement token {op.new_token}/v{op.new_version} missing params {sorted(missing_params)}"
        )

    graph = list(ir.graph)
    graph[index] = GraphNode(
        id=node.id,
        token=op.new_token,
        v=op.new_version,
        params=new_params,
        inputs=new_inputs,
    )
    return ir.model_copy(update={"graph": graph}, deep=True)


def _apply_inline_recipe(
    ir: StrategyIR,
    op: InlineRecipe,
    registry: Registry,
    recipe_registry: RecipeRegistry,
) -> StrategyIR:
    recipe_index, recipe = _find_recipe_instance(ir.recipes, op.recipe_id)
    compiled = compile_recipe(
        recipe_id=recipe.recipe,
        recipe_version=recipe.version,
        instance_params=recipe.params,
        instance_inputs=recipe.inputs,
        instance_id=recipe.id,
        registry=registry,
        recipe_registry=recipe_registry,
    )
    existing_ids = {node.id for node in ir.graph}
    existing_ids.update(item.id for item in ir.recipes if item.id != recipe.id)
    new_nodes = [_graph_node_from_primitive(node) for node in compiled.nodes]
    duplicate_ids = existing_ids & {node.id for node in new_nodes}
    if duplicate_ids:
        raise MutationError(f"inlined recipe would create duplicate ids {sorted(duplicate_ids)}")

    ref_rewrites = {
        f"{recipe.id}.{port}": output_ref.to_ref()
        for port, output_ref in compiled.outputs.items()
    }
    if len(compiled.outputs) == 1:
        ref_rewrites[recipe.id] = next(iter(compiled.outputs.values())).to_ref()

    recipes = list(ir.recipes)
    recipes.pop(recipe_index)
    recipes = [
        item.model_copy(update={"inputs": _rewrite_refs(item.inputs, ref_rewrites)})
        for item in recipes
    ]
    graph = [
        node.model_copy(update={"inputs": _rewrite_refs(node.inputs, ref_rewrites)})
        for node in ir.graph
    ]
    outputs = {
        port: _rewrite_refs(target, ref_rewrites)
        for port, target in ir.outputs.items()
    }
    return ir.model_copy(
        update={
            "recipes": recipes,
            "graph": [*new_nodes, *graph],
            "outputs": outputs,
        },
        deep=True,
    )


def _apply_op(
    ir: StrategyIR,
    op: MutationOp,
    registry: Registry,
    recipe_registry: RecipeRegistry,
) -> StrategyIR:
    if isinstance(op, ChangeParam):
        return _apply_change_param(ir, op)
    if isinstance(op, InsertBefore):
        return _apply_insert_before(ir, op, registry)
    if isinstance(op, ReplaceToken):
        return _apply_replace_token(ir, op, registry)
    if isinstance(op, InlineRecipe):
        return _apply_inline_recipe(ir, op, registry, recipe_registry)
    raise AssertionError(f"Unsupported mutation op: {op!r}")


def _append_lineage_op(ir: StrategyIR, op: MutationOp) -> StrategyIR:
    if ir.derived_from is None:
        return ir
    derived_from = ir.derived_from.model_copy(
        update={
            "mutation_chain": [
                *ir.derived_from.mutation_chain,
                op.model_dump(mode="json"),
            ]
        }
    )
    return ir.model_copy(update={"derived_from": derived_from}, deep=True)


def mutate_strategy(
    ir: StrategyIR,
    op: MutationOp,
    *,
    registry: Registry | None = None,
    recipe_registry: RecipeRegistry | None = None,
) -> MutationResult:
    """Apply one P2b mutation op."""

    token_registry = registry or get_registry()
    recipes = recipe_registry or get_recipe_registry()
    before = compute_hashes(ir).as_dict()
    try:
        mutated = _append_lineage_op(_apply_op(ir, op, token_registry, recipes), op)
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
