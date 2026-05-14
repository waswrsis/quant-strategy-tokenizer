from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.composition import (
    GeneratorConstraintError,
    RecipeGeneratorDocument,
    expand_builtin_recipe,
    expand_generator,
    load_generator_file,
    recipe_to_stable_json,
)
from quant_strategy_tokenizer.recipes.schema import RecipeSpec

runner = CliRunner()


def _document_with_emit(emit: list[dict[str, object]]) -> RecipeGeneratorDocument:
    return RecipeGeneratorDocument.model_validate(
        {
            "recipe": {
                "id": "test.generated",
                "version": 1,
                "params_schema": {"count": {"type": "integer", "minimum": 0, "default": 1}},
                "inputs": {"series": "TimeSeries[float]"},
                "outputs": {"value": "node_0.value"},
                "generator": {"emit": emit},
            }
        }
    )


def test_builtin_dual_ema_generator_parses_and_expands_defaults() -> None:
    recipe = expand_builtin_recipe("signals.dual_ema_cross")

    assert isinstance(recipe, RecipeSpec)
    assert recipe.recipe == "signals.dual_ema_cross"
    assert recipe.version == 1
    assert [node.id for node in recipe.graph] == ["fast_ema", "slow_ema", "cross"]
    assert recipe.graph[0].params["span"] == 9
    assert recipe.graph[1].params["span"] == 21
    assert recipe.outputs == {
        "fast": "fast_ema.value",
        "slow": "slow_ema.value",
        "cross": "cross.cross",
    }


def test_builtin_dual_ema_generator_expands_explicit_params() -> None:
    recipe = expand_builtin_recipe(
        "signals.dual_ema_cross",
        {"fast_span": 5, "slow_span": 13, "init": "first_value"},
    )

    assert recipe.graph[0].params["span"] == 5
    assert recipe.graph[1].params["span"] == 13


def test_generator_expansion_is_deterministic() -> None:
    left = expand_builtin_recipe("signals.dual_ema_cross", {"fast_span": 9, "slow_span": 21})
    right = expand_builtin_recipe("signals.dual_ema_cross", {"slow_span": 21, "fast_span": 9})

    assert recipe_to_stable_json(left) == recipe_to_stable_json(right)


def test_generator_can_emit_generic_recipe_artifact() -> None:
    path = Path("quant_strategy_tokenizer/composition/generators/signals.dual_ema_cross.v1.yaml")
    document = load_generator_file(path)
    recipe = expand_generator(document, source_path=path, concrete_params=False)

    assert recipe.graph[0].params["span"] == "$params.fast_span"
    assert recipe.graph[1].params["span"] == "$params.slow_span"


def test_generated_graph_uses_only_existing_recipes() -> None:
    recipe = expand_builtin_recipe("signals.dual_ema_cross")

    assert {node.recipe for node in recipe.graph} == {
        "indicator.ewm",
        "event.cross_above",
    }
    assert all(node.token is None for node in recipe.graph)


def test_static_for_expands_and_enforces_loop_limit() -> None:
    document = _document_with_emit(
        [
            {
                "static_for": {"var": "i", "range": [0, "$params.count"]},
                "body": [
                    {
                        "id": "node_${i}",
                        "token": "data.shift",
                        "params": {"periods": "${i}"},
                        "inputs": {"series": "$inputs.series"},
                    }
                ],
            }
        ]
    )

    expanded = expand_generator(document, {"count": 3})
    assert [node.id for node in expanded.graph] == ["node_0", "node_1", "node_2"]

    with pytest.raises(GeneratorConstraintError):
        expand_generator(document, {"count": 1025})


def test_static_if_selects_deterministic_branch() -> None:
    document = _document_with_emit(
        [
            {
                "static_if": "$params.count > 1",
                "then": [{"id": "then_node", "token": "data.shift", "inputs": {"series": "$inputs.series"}}],
                "else": [{"id": "else_node", "token": "data.shift", "inputs": {"series": "$inputs.series"}}],
            }
        ]
    )

    assert expand_generator(document, {"count": 2}).graph[0].id == "then_node"
    assert expand_generator(document, {"count": 1}).graph[0].id == "else_node"


def test_include_rejects_absolute_path(tmp_path: Path) -> None:
    document = _document_with_emit([{"include": str(tmp_path / "macro.yaml")}])

    with pytest.raises(GeneratorConstraintError):
        expand_generator(document, source_path=tmp_path / "root.yaml")


def test_recursive_include_is_rejected(tmp_path: Path) -> None:
    macro = tmp_path / "macro.yaml"
    macro.write_text("emit:\n  - include: macro.yaml\n", encoding="utf-8")
    document = _document_with_emit([{"include": "macro.yaml"}])

    with pytest.raises(GeneratorConstraintError):
        expand_generator(document, source_path=tmp_path / "root.yaml")


def test_include_depth_limit_is_enforced(tmp_path: Path) -> None:
    for index in range(6):
        target = tmp_path / f"m{index}.yaml"
        if index == 5:
            target.write_text("- id: leaf\n  token: data.shift\n  inputs: {series: $inputs.series}\n", encoding="utf-8")
        else:
            target.write_text(f"emit:\n  - include: m{index + 1}.yaml\n", encoding="utf-8")
    document = _document_with_emit([{"include": "m0.yaml"}])

    with pytest.raises(GeneratorConstraintError):
        expand_generator(document, source_path=tmp_path / "root.yaml")


def test_expanded_node_limit_is_enforced() -> None:
    document = _document_with_emit(
        [
            {
                "id": f"node_{index}",
                "token": "data.shift",
                "inputs": {"series": "$inputs.series"},
            }
            for index in range(5001)
        ]
    )

    with pytest.raises(GeneratorConstraintError):
        expand_generator(document)


def test_nondeterministic_construct_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "recipe": {
                    "id": "bad",
                    "version": 1,
                    "inputs": {"series": "TimeSeries[float]"},
                    "outputs": {"value": "x.value"},
                    "generator": {"emit": [{"id": "x", "token": "data.shift", "random": True}]},
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GeneratorConstraintError):
        load_generator_file(path)


def test_qst_recipe_expand_writes_json_and_yaml(tmp_path: Path) -> None:
    json_output = tmp_path / "dual.json"
    yaml_output = tmp_path / "dual.yaml"

    json_result = runner.invoke(
        app,
        [
            "recipe",
            "expand",
            "signals.dual_ema_cross",
            "--params",
            '{"fast_span":9,"slow_span":21}',
            "--output",
            str(json_output),
        ],
    )
    yaml_result = runner.invoke(
        app,
        [
            "recipe",
            "expand",
            "signals.dual_ema_cross",
            "--params",
            '{"fast_span":5,"slow_span":13}',
            "--output",
            str(yaml_output),
        ],
    )

    assert json_result.exit_code == 0, json_result.output
    payload = json.loads(json_result.output)
    assert payload["ok"] is True
    assert payload["node_count"] == 3
    assert json.loads(json_output.read_text(encoding="utf-8"))["recipe"] == "signals.dual_ema_cross"
    assert yaml_result.exit_code == 0, yaml_result.output
    assert yaml.safe_load(yaml_output.read_text(encoding="utf-8"))["recipe"] == "signals.dual_ema_cross"


def test_qst_recipe_expand_invalid_params_exit_1(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "recipe",
            "expand",
            "signals.dual_ema_cross",
            "--params",
            '{"fast_span":0,"slow_span":21}',
            "--output",
            str(tmp_path / "bad.json"),
        ],
    )

    assert result.exit_code == 1
    assert '"ok": false' in result.output
