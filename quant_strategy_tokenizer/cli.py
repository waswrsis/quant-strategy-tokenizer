"""Typer CLI for QST P0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
import typer

from quant_strategy_tokenizer.core.output import jsonable_value
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as explain_text
from quant_strategy_tokenizer.ir.canonicalize import canonicalize as canonicalize_ir
from quant_strategy_tokenizer.ir.compare import compare_ir
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json
from quant_strategy_tokenizer.ir.validate import validate as validate_ir
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from quant_strategy_tokenizer.tokens._contract_runner import run_contract
from quant_strategy_tokenizer.tokens.registry import get_registry

app = typer.Typer(no_args_is_help=True)


def _echo_json(value: Any) -> None:
    typer.echo(json.dumps(jsonable_value(value), ensure_ascii=False, indent=2, default=str))


def _compile_smoke_recipe(recipe_id: str) -> None:
    smoke: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        "indicator.ewm": ({"span": 3}, {"series": "$externals.series"}),
        "indicator.rma": ({"alpha": 0.5}, {"series": "$externals.series"}),
        "indicator.kdj": (
            {"lookback": 9, "k_alpha": 0.3333333, "d_alpha": 0.3333333, "init": 50},
            {
                "high": "$externals.market.high",
                "low": "$externals.market.low",
                "close": "$externals.market.close",
            },
        ),
        "event.cross_above": (
            {},
            {"fast": "$externals.fast", "slow": "$externals.slow"},
        ),
    }
    params, inputs = smoke[recipe_id]
    compile_recipe(
        recipe_id=recipe_id,
        recipe_version=1,
        instance_params=params,
        instance_inputs=inputs,
        instance_id=recipe_id.replace(".", "_"),
        registry=get_registry(),
        recipe_registry=get_recipe_registry(),
    )


@app.command("vocabulary")
def vocabulary(check: bool = False, markdown: bool = False) -> None:
    """List or check built-in token and recipe vocabulary."""

    token_registry = get_registry()
    recipe_registry = get_recipe_registry()
    tokens = token_registry.list_tokens()
    recipes = recipe_registry.list_recipes()

    if check:
        if len(tokens) != 17:
            typer.echo(f"expected 17 tokens, got {len(tokens)}", err=True)
            raise typer.Exit(1)
        if len(recipes) != 4:
            typer.echo(f"expected 4 recipes, got {len(recipes)}", err=True)
            raise typer.Exit(1)
        for spec in tokens:
            for contract in spec.behavior_contract:
                result = run_contract(token_registry.get(spec.id, spec.version), contract)
                if not result.passed:
                    typer.echo(f"{spec.id}:{result.name}: {result.error}", err=True)
                    raise typer.Exit(1)
        for recipe in recipes:
            _compile_smoke_recipe(recipe.recipe)
        typer.echo("17 tokens registered, all behavior_contracts pass")
        typer.echo("4 recipes registered, all compile")
        return

    if markdown:
        typer.echo("| kind | id | version |")
        typer.echo("|---|---|---|")
        for spec in tokens:
            typer.echo(f"| token | {spec.id} | {spec.version} |")
        for recipe in recipes:
            typer.echo(f"| recipe | {recipe.recipe} | {recipe.version} |")
        return

    _echo_json(
        {
            "tokens": [spec.model_dump(mode="json") for spec in tokens],
            "recipes": [recipe.model_dump(mode="json") for recipe in recipes],
        }
    )


@app.command("validate")
def validate_cmd(path: Path) -> None:
    """Validate a strategy YAML file."""

    result = validate_ir(load_strategy_file(path))
    if result.ok:
        typer.echo("valid")
        return
    typer.echo("INVALID", err=True)
    for failure in result.failures:
        typer.echo(json.dumps(failure.model_dump(exclude_none=True), ensure_ascii=False), err=True)
    raise typer.Exit(1)


@app.command("canonicalize")
def canonicalize_cmd(path: Path) -> None:
    """Print canonical IR JSON."""

    typer.echo(to_json(canonicalize_ir(load_strategy_file(path))))


@app.command("hash")
def hash_cmd(path: Path) -> None:
    """Print P0 graph, param, and instance hashes."""

    hashes = compute_hashes(load_strategy_file(path))
    typer.echo(f"graph_hash:    {hashes.graph_hash}")
    typer.echo(f"param_hash:    {hashes.param_hash}")
    typer.echo(f"instance_hash: {hashes.instance_hash}")


@app.command("compare")
def compare_cmd(yaml_a: Path, yaml_b: Path) -> None:
    """Compare two strategy YAML files by P0 hash layers."""

    result = compare_ir(load_strategy_file(yaml_a), load_strategy_file(yaml_b))
    typer.echo("== Compare Report ==")
    typer.echo("")
    typer.echo("Structure:")
    typer.echo(f"  graph_hash {'identical' if result.graph_equal else 'different'}")
    typer.echo("")
    typer.echo("Parameters:")
    typer.echo(f"  param_hash {'identical' if result.param_equal else 'differs'}")
    if result.param_diffs:
        for diff in result.param_diffs:
            typer.echo(f"  - {diff.path}: {diff.left} → {diff.right}")
    typer.echo("")
    typer.echo("Instance:")
    typer.echo(f"  instance_hash {'identical' if result.instance_equal else 'differs'}")


@app.command("explain")
def explain_cmd(path: Path, level: str = "L1") -> None:
    """Print a human-readable strategy explanation."""

    typer.echo(explain_text(load_strategy_file(path), level=level))


def _load_market_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in ("timestamp", "ts", "time", "date"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
            frame = frame.set_index(column)
            break
    return frame


@app.command("execute")
def execute_cmd(
    path: Path,
    market: Annotated[Path, typer.Option("--market")],
    trace_path: Annotated[Path, typer.Option("--trace-path")] = Path("trace.json"),
) -> None:
    """Execute a strategy YAML file against sample market CSV data."""

    ir = load_strategy_file(path)
    result = execute_strategy(ir, {"market": _load_market_csv(market)}, trace_path=trace_path)
    if not result.ok:
        typer.echo(result.error or "execution failed", err=True)
        if result.validation_failures:
            for failure in result.validation_failures:
                typer.echo(json.dumps(failure.model_dump(exclude_none=True), ensure_ascii=False), err=True)
            raise typer.Exit(1)
        raise typer.Exit(4)
    _echo_json({"outputs": result.outputs, "trace": str(trace_path)})


if __name__ == "__main__":
    app()
