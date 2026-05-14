"""P0 Strategy IR validator."""

from __future__ import annotations

from collections import Counter
from typing import Any

from quant_strategy_tokenizer.core.errors import ErrorKind
from quant_strategy_tokenizer.ir.canonicalize import _contains_refs, canonicalize
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, GraphNode, StrategyIR
from quant_strategy_tokenizer.ir.repair import (
    missing_input_hint,
    missing_risk_path_hint,
    missing_unknown_handling_hint,
    type_mismatch_hint,
)
from quant_strategy_tokenizer.ir.validation_result import ValidationFailure, ValidationResult
from quant_strategy_tokenizer.ir.validators.purity import validate_purity
from quant_strategy_tokenizer.ir.validators.temporal import validate_temporal
from quant_strategy_tokenizer.recipes.compiler import CycleError, MaxDepthError, compile_recipe
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import Registry, get_registry

__all__ = ["ValidationFailure", "ValidationResult", "validate"]


def _node_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        if not value.startswith("$"):
            refs.append(value)
    elif isinstance(value, list):
        for item in value:
            refs.extend(_node_refs(item))
    elif isinstance(value, dict):
        if value.get("kind") in {"accept", "reject", "block", "abstain", "unknown", "error"}:
            return refs
        for item in value.values():
            refs.extend(_node_refs(item))
    return refs


def _node_ref_ids(value: Any) -> list[str]:
    refs = _node_refs(value)
    ids: list[str] = []
    for ref in refs:
        ids.append(ref.split(".", 1)[0])
    return ids


def _normalize_single_ref(ref: str, output_types: dict[str, str]) -> str:
    if ref in output_types:
        return ref
    matches = [key for key in output_types if key.startswith(f"{ref}.")]
    if len(matches) == 1:
        return matches[0]
    return ref


def _external_type(ref: str, ir: StrategyIR) -> str | None:
    if not ref.startswith("$externals."):
        return None
    pieces = ref.removeprefix("$externals.").split(".")
    if not pieces or pieces[0] not in ir.externals:
        return None
    if len(pieces) > 1 and ir.externals[pieces[0]].type.startswith("Frame"):
        return "TimeSeries[float]"
    return ir.externals[pieces[0]].type


def _add_node_output_types(output_types: dict[str, str], node: GraphNode, registry: Registry) -> None:
    registered = registry.get(node.token, node.v)
    for port, type_ref in registered.spec.outputs.items():
        output_types[f"{node.id}.{port}"] = type_ref
    if len(registered.spec.outputs) == 1:
        only_type = next(iter(registered.spec.outputs.values()))
        output_types[node.id] = only_type


def _recipe_output_types(ir: StrategyIR, registry: Registry, recipe_registry: RecipeRegistry) -> dict[str, str]:
    output_types: dict[str, str] = {}
    for recipe_instance in ir.recipes:
        compiled = compile_recipe(
            recipe_id=recipe_instance.recipe,
            recipe_version=recipe_instance.version,
            instance_params=recipe_instance.params,
            instance_inputs=recipe_instance.inputs,
            instance_id=recipe_instance.id,
            registry=registry,
            recipe_registry=recipe_registry,
        )
        node_by_id = {node.id: node for node in compiled.nodes}
        for port, ref in compiled.outputs.items():
            node = node_by_id[ref.node_id]
            type_ref = registry.get(node.token, node.version).spec.outputs[ref.port]
            output_types[f"{recipe_instance.id}.{port}"] = type_ref
        if len(compiled.outputs) == 1:
            only_port = next(iter(compiled.outputs))
            output_types[recipe_instance.id] = output_types[f"{recipe_instance.id}.{only_port}"]
    return output_types


def _build_output_types(ir: StrategyIR, registry: Registry, recipe_registry: RecipeRegistry) -> dict[str, str]:
    output_types = _recipe_output_types(ir, registry, recipe_registry)
    for node in ir.graph:
        _add_node_output_types(output_types, node, registry)
    return output_types


def check_canonical_version_supported(ir: StrategyIR) -> list[ValidationFailure]:
    if ir.canonical_version != CANONICAL_VERSION:
        return [
            ValidationFailure(
                kind=ErrorKind.unsupported_canonical_version.value,
                message=(
                    f"canonical_version expected {CANONICAL_VERSION}, "
                    f"got {ir.canonical_version}"
                ),
            )
        ]
    return []


def check_unique_node_ids(ir: StrategyIR) -> list[ValidationFailure]:
    ids = [recipe.id for recipe in ir.recipes] + [node.id for node in ir.graph]
    counts = Counter(ids)
    return [
        ValidationFailure(
            kind=ErrorKind.duplicate_node_id.value,
            message=f"node id {node_id!r} appears {count} times",
            node_id=node_id,
        )
        for node_id, count in counts.items()
        if count > 1
    ]


def check_tokens_exist(ir: StrategyIR, registry: Registry) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for node in ir.graph:
        try:
            registry.get(node.token, node.v)
        except KeyError:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.token_not_found.value,
                    message=f"token {node.token}/v{node.v} not found",
                    node_id=node.id,
                )
            )
    return failures


def check_recipes_exist(ir: StrategyIR, recipe_registry: RecipeRegistry) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for recipe in ir.recipes:
        try:
            recipe_registry.get(recipe.recipe, recipe.version)
        except KeyError:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.recipe_not_found.value,
                    message=f"recipe {recipe.recipe}/v{recipe.version} not found",
                    node_id=recipe.id,
                )
            )
    return failures


def check_recipes_compilable(
    ir: StrategyIR,
    registry: Registry,
    recipe_registry: RecipeRegistry,
) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for recipe in ir.recipes:
        try:
            compile_recipe(
                recipe_id=recipe.recipe,
                recipe_version=recipe.version,
                instance_params=recipe.params,
                instance_inputs=recipe.inputs,
                instance_id=recipe.id,
                registry=registry,
                recipe_registry=recipe_registry,
            )
        except CycleError as exc:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.cycle_detected.value,
                    message=str(exc),
                    node_id=recipe.id,
                )
            )
        except MaxDepthError as exc:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.max_depth_exceeded.value,
                    message=str(exc),
                    node_id=recipe.id,
                )
            )
        except Exception as exc:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.recipe_not_found.value,
                    message=f"recipe {recipe.id!r} did not compile: {type(exc).__name__}: {exc}",
                    node_id=recipe.id,
                )
            )
    return failures


def check_no_cycles(ir: StrategyIR) -> list[ValidationFailure]:
    graph_ids = {node.id for node in ir.graph}
    incoming = {node.id: {ref.split(".", 1)[0] for ref in _contains_refs(node.inputs)} & graph_ids for node in ir.graph}
    remaining = set(graph_ids)
    while remaining:
        ready = {node_id for node_id in remaining if not (incoming[node_id] & remaining)}
        if not ready:
            return [
                ValidationFailure(
                    kind=ErrorKind.cycle_detected.value,
                    message="graph contains a cycle",
                )
            ]
        remaining -= ready
    return []


def check_params_schemas(ir: StrategyIR, registry: Registry) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for node in ir.graph:
        spec = registry.get(node.token, node.v).spec
        for param_name, schema in spec.params_schema.items():
            has_default = isinstance(schema, dict) and "default" in schema
            if param_name not in node.params and not has_default:
                failures.append(
                    ValidationFailure(
                        kind=ErrorKind.invalid_params.value,
                        message=f"node {node.id!r} missing required param {param_name!r}",
                        node_id=node.id,
                    )
                )
    return failures


def check_inputs_exist(
    ir: StrategyIR,
    registry: Registry,
    recipe_registry: RecipeRegistry,
) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    output_types = _build_output_types(ir, registry, recipe_registry)
    for node in ir.graph:
        spec = registry.get(node.token, node.v).spec
        if spec.inputs:
            for port in spec.inputs:
                if port not in node.inputs:
                    failures.append(
                        ValidationFailure(
                            kind=ErrorKind.missing_input.value,
                            message=f"node {node.id!r} missing input port {port!r}",
                            node_id=node.id,
                            repair_hint=missing_input_hint(sorted(output_types)),
                        )
                    )
        for ref in _node_refs(node.inputs):
            normalized = _normalize_single_ref(ref, output_types)
            if normalized in output_types or _external_type(ref, ir) is not None:
                continue
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.missing_input.value,
                    message=f"node {node.id!r} input reference {ref!r} has no source",
                    node_id=node.id,
                    repair_hint=missing_input_hint(sorted(output_types)),
                )
            )
    return failures


def check_basic_types(
    ir: StrategyIR,
    registry: Registry,
    recipe_registry: RecipeRegistry,
) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    output_types = _build_output_types(ir, registry, recipe_registry)

    for node in ir.graph:
        spec = registry.get(node.token, node.v).spec
        for port, expected_type in spec.inputs.items():
            if port not in node.inputs:
                continue
            raw_input = node.inputs[port]
            if expected_type == "Decision[]":
                items = raw_input if isinstance(raw_input, list) else [raw_input]
                for item in items:
                    if not isinstance(item, str):
                        continue
                    ref = _normalize_single_ref(item, output_types)
                    actual_type = output_types.get(ref) or _external_type(item, ir)
                    if actual_type != "Decision":
                        failures.append(
                            ValidationFailure(
                                kind=ErrorKind.type_mismatch.value,
                                message=(
                                    f"type_mismatch at node {node.id!r}: input port "
                                    f"'decisions' expects Decision[], got {actual_type}"
                                ),
                                node_id=node.id,
                                repair_hint=type_mismatch_hint(node.id, item),
                                details={"expected": "Decision[]", "actual": actual_type, "source": item},
                            )
                        )
                continue

            if isinstance(raw_input, str):
                ref = _normalize_single_ref(raw_input, output_types)
                actual_type = output_types.get(ref) or _external_type(raw_input, ir)
                if actual_type is not None and actual_type != expected_type:
                    failures.append(
                        ValidationFailure(
                            kind=ErrorKind.type_mismatch.value,
                            message=(
                                f"type_mismatch at node {node.id!r}: input port {port!r} "
                                f"expects {expected_type}, got {actual_type}"
                            ),
                            node_id=node.id,
                            repair_hint=type_mismatch_hint(node.id, raw_input)
                            if expected_type == "Decision"
                            else None,
                            details={"expected": expected_type, "actual": actual_type, "source": raw_input},
                        )
                    )
    return failures


def check_unknown_handling_declared(ir: StrategyIR) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for node in ir.graph:
        if node.token == "decision.reduce" and "unknown_handling" not in node.params:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.missing_unknown_handling.value,
                    message=f"decision.reduce at node {node.id!r} must declare unknown_handling",
                    node_id=node.id,
                    repair_hint=missing_unknown_handling_hint(node.id),
                )
            )
    return failures


def _collect_ancestors(node_id: str, ir: StrategyIR) -> set[str]:
    visited: set[str] = set()
    queue = [node_id]
    deps = {node.id: _node_ref_ids(node.inputs) for node in ir.graph}
    while queue:
        current = queue.pop(0)
        for upstream in deps.get(current, []):
            if upstream not in visited:
                visited.add(upstream)
                queue.append(upstream)
    return visited


def check_profile_consistency(ir: StrategyIR, profile: ProfileLiteral) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if profile in {"pretrade", "production_guarded"}:
        for node in ir.graph:
            if node.token == "decision.reduce" and node.params.get("unknown_handling") == "treat_as_accept":
                failures.append(
                    ValidationFailure(
                        kind=ErrorKind.profile_violation.value,
                        message=(
                            f"decision.reduce at node {node.id!r} cannot use "
                            f"unknown_handling='treat_as_accept' in {profile} profile"
                        ),
                        node_id=node.id,
                        severity="error",
                    )
                )
    return failures


def check_risk_path(ir: StrategyIR, profile: ProfileLiteral) -> list[ValidationFailure]:
    if profile not in {"pretrade", "production_guarded"}:
        return []

    failures: list[ValidationFailure] = []
    nodes_by_id = {node.id: node for node in ir.graph}
    order_nodes = [node for node in ir.graph if node.token == "plan.order_intent"]
    if not order_nodes:
        plan_node = next((node for node in ir.graph if node.token.startswith("plan.")), None)
        failures.append(
            ValidationFailure(
                kind=ErrorKind.missing_risk_path.value,
                message=f"{profile} profile requires plan.order_intent with a risk.* ancestor",
                node_id=plan_node.id if plan_node is not None else None,
                severity="error",
                repair_hint=missing_risk_path_hint(plan_node.id if plan_node is not None else None),
            )
        )
        return failures

    for node in order_nodes:
        ancestors = _collect_ancestors(node.id, ir)
        risk_in_path = any(
            nodes_by_id[ancestor].token.startswith("risk.")
            for ancestor in ancestors
            if ancestor in nodes_by_id
        )
        if not risk_in_path:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.missing_risk_path.value,
                    message=(
                        f"plan.order_intent at {node.id!r} has no risk.* "
                        f"ancestor in {profile} profile"
                    ),
                    node_id=node.id,
                    severity="error",
                    repair_hint=missing_risk_path_hint(node.id),
                )
            )
    return failures


def validate(
    ir: StrategyIR,
    registry: Registry | None = None,
    recipe_registry: RecipeRegistry | None = None,
    profile: ProfileLiteral = "research",
) -> ValidationResult:
    """Run validator checks for a Strategy IR under a profile."""

    token_registry = registry or get_registry()
    recipes = recipe_registry or get_recipe_registry()
    failures: list[ValidationFailure] = []
    warnings: list[ValidationFailure] = []
    failures.extend(check_canonical_version_supported(ir))
    failures.extend(check_unique_node_ids(ir))
    failures.extend(check_tokens_exist(ir, token_registry))
    failures.extend(check_recipes_exist(ir, recipes))
    failures.extend(check_recipes_compilable(ir, token_registry, recipes))
    failures.extend(check_no_cycles(ir))
    failures.extend(check_params_schemas(ir, token_registry))
    failures.extend(check_inputs_exist(ir, token_registry, recipes))
    failures.extend(check_basic_types(ir, token_registry, recipes))
    failures.extend(check_unknown_handling_declared(ir))
    failures.extend(check_profile_consistency(ir, profile))
    failures.extend(check_risk_path(ir, profile))

    if not failures:
        policy_ir = ir if ir.form == "canonical" else canonicalize(ir, registry=token_registry, recipe_registry=recipes)
        failures.extend(validate_purity(policy_ir, profile, token_registry))
        temporal_failures, temporal_warnings = validate_temporal(policy_ir, profile, token_registry)
        failures.extend(temporal_failures)
        warnings.extend(temporal_warnings)

    return ValidationResult(failures=failures, warnings=warnings)
