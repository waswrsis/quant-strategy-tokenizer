"""Lightweight P0 IR comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR


@dataclass(frozen=True)
class ParamDiff:
    """One parameter value difference."""

    path: str
    left: Any
    right: Any


@dataclass(frozen=True)
class CompareResult:
    """Hash-level comparison result."""

    graph_equal: bool
    param_equal: bool
    instance_equal: bool
    param_diffs: list[ParamDiff]


def _diff_values(path: str, left: Any, right: Any) -> list[ParamDiff]:
    if isinstance(left, dict) and isinstance(right, dict):
        diffs: list[ParamDiff] = []
        for key in sorted(set(left) | set(right)):
            key_path = f"{path}.{key}" if path else str(key)
            diffs.extend(_diff_values(key_path, left.get(key), right.get(key)))
        return diffs
    if isinstance(left, list) and isinstance(right, list):
        diffs = []
        max_len = max(len(left), len(right))
        for index in range(max_len):
            item_path = f"{path}[{index}]"
            left_item = left[index] if index < len(left) else None
            right_item = right[index] if index < len(right) else None
            diffs.extend(_diff_values(item_path, left_item, right_item))
        return diffs
    if left != right:
        return [ParamDiff(path=path, left=left, right=right)]
    return []


def _surface_param_diffs(left: StrategyIR, right: StrategyIR) -> list[ParamDiff]:
    diffs: list[ParamDiff] = []
    left_recipes = {recipe.id: recipe for recipe in left.recipes}
    right_recipes = {recipe.id: recipe for recipe in right.recipes}
    for recipe_id in sorted(set(left_recipes) | set(right_recipes)):
        left_recipe = left_recipes.get(recipe_id)
        right_recipe = right_recipes.get(recipe_id)
        left_params = left_recipe.params if left_recipe is not None else None
        right_params = right_recipe.params if right_recipe is not None else None
        diffs.extend(_diff_values(f"recipes.{recipe_id}.params", left_params, right_params))

    left_nodes = {node.id: node for node in left.graph}
    right_nodes = {node.id: node for node in right.graph}
    for node_id in sorted(set(left_nodes) | set(right_nodes)):
        left_node = left_nodes.get(node_id)
        right_node = right_nodes.get(node_id)
        left_params = left_node.params if left_node is not None else None
        right_params = right_node.params if right_node is not None else None
        diffs.extend(_diff_values(f"graph.{node_id}.params", left_params, right_params))
    return diffs


def compare_ir(left: StrategyIR, right: StrategyIR) -> CompareResult:
    """Compare two Strategy IR instances by P0 hash layers."""

    left_hashes = compute_hashes(left)
    right_hashes = compute_hashes(right)
    return CompareResult(
        graph_equal=left_hashes.graph_hash == right_hashes.graph_hash,
        param_equal=left_hashes.param_hash == right_hashes.param_hash,
        instance_equal=left_hashes.instance_hash == right_hashes.instance_hash,
        param_diffs=_surface_param_diffs(left, right),
    )
