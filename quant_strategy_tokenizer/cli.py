"""Typer CLI for QST P0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
import typer
import yaml

from quant_strategy_tokenizer.agent.promote import promote as promote_strategy
from quant_strategy_tokenizer.core.output import jsonable_value
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as explain_text
from quant_strategy_tokenizer.detokenize.trace_explainer import explain_trace as explain_trace_text
from quant_strategy_tokenizer.ir.canonicalize import canonicalize as canonicalize_ir
from quant_strategy_tokenizer.ir.compare import compare_ir
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json
from quant_strategy_tokenizer.ir.validate import validate as validate_ir
from quant_strategy_tokenizer.parse.yaml_loader import (
    load_strategy_file,
    load_strategy_file_with_envelope,
)
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from quant_strategy_tokenizer.runtime.trace import Trace
from quant_strategy_tokenizer.tokens._contract_runner import run_contract
from quant_strategy_tokenizer.tokens.registry import get_registry

app = typer.Typer(no_args_is_help=True)

P0_TOKEN_TRIPLES: tuple[tuple[str, int, int], ...] = (
    ("data.column", 1, 1),
    ("data.shift", 1, 1),
    ("window.max", 1, 1),
    ("window.min", 1, 1),
    ("smooth.linear_recursive", 1, 1),
    ("math.add", 1, 1),
    ("math.sub", 1, 1),
    ("math.mul", 1, 1),
    ("math.div", 1, 1),
    ("math.linear_combination", 1, 1),
    ("compare.gt", 1, 1),
    ("compare.le", 1, 1),
    ("logic.and", 1, 1),
    ("norm.range_position", 1, 1),
    ("decision.lift_bool", 1, 1),
    ("decision.reduce", 1, 1),
    ("plan.noop", 1, 1),
)
P0_RECIPE_PAIRS: tuple[tuple[str, int], ...] = (
    ("indicator.ewm", 1),
    ("indicator.rma", 1),
    ("indicator.kdj", 1),
    ("event.cross_above", 1),
)
PROFILE_VALUES = {"research", "paper", "pretrade", "production_guarded"}


def _echo_json(value: Any) -> None:
    typer.echo(json.dumps(jsonable_value(value), ensure_ascii=False, indent=2, default=str))


def _effective_profile(override: str | None, envelope_profile: ProfileLiteral) -> ProfileLiteral:
    raw_profile = override or envelope_profile
    if raw_profile not in PROFILE_VALUES:
        typer.echo(f"unsupported profile: {raw_profile}", err=True)
        raise typer.Exit(2)
    return cast(ProfileLiteral, raw_profile)


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
        "event.threshold_above": (
            {},
            {"series": "$externals.series", "threshold": "$externals.threshold"},
        ),
        "event.threshold_below": (
            {},
            {"series": "$externals.series", "threshold": "$externals.threshold"},
        ),
        "gate.elapsed_threshold": (
            {"field": "elapsed", "threshold": 10, "default": 0},
            {"state": "$externals.state"},
        ),
        "gate.cooldown": (
            {"field": "cooldown_elapsed", "threshold": 10, "default": 0},
            {"state": "$externals.state"},
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
        if len(tokens) != 25:
            typer.echo(f"expected 25 tokens, got {len(tokens)}", err=True)
            raise typer.Exit(1)
        if len(recipes) != 8:
            typer.echo(f"expected 8 recipes, got {len(recipes)}", err=True)
            raise typer.Exit(1)
        for token_id, version, behavior_version in P0_TOKEN_TRIPLES:
            spec = token_registry.get(token_id, version).spec
            if spec.behavior_version != behavior_version:
                typer.echo(
                    f"P0 token drift: {token_id}/v{version} expected bv{behavior_version}, "
                    f"got bv{spec.behavior_version}",
                    err=True,
                )
                raise typer.Exit(1)
        for recipe_id, version in P0_RECIPE_PAIRS:
            recipe_registry.get(recipe_id, version)
        for spec in tokens:
            for contract in spec.behavior_contract:
                result = run_contract(token_registry.get(spec.id, spec.version), contract)
                if not result.passed:
                    typer.echo(f"{spec.id}:{result.name}: {result.error}", err=True)
                    raise typer.Exit(1)
        for recipe in recipes:
            _compile_smoke_recipe(recipe.recipe)
        typer.echo("P0 frozen baseline:")
        typer.echo("  tokens: 17")
        typer.echo("  recipes: 4")
        typer.echo("  status: preserved")
        typer.echo("Current vocabulary:")
        typer.echo("  tokens: 25")
        typer.echo("  recipes: 8")
        typer.echo("25 tokens registered, all behavior_contracts pass")
        typer.echo("8 recipes registered, all compile")
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
def validate_cmd(
    path: Path,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
) -> None:
    """Validate a strategy YAML file."""

    ir, envelope = load_strategy_file_with_envelope(path)
    result = validate_ir(ir, profile=_effective_profile(profile, envelope.profile))
    if result.ok:
        typer.echo("valid")
        for warning in result.warnings:
            typer.echo(
                json.dumps(warning.model_dump(exclude_none=True), ensure_ascii=False),
                err=True,
            )
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
            typer.echo(f"  - {diff.path}: {diff.left} -> {diff.right}")
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
    profile: Annotated[str | None, typer.Option("--profile")] = None,
) -> None:
    """Execute a strategy YAML file against sample market CSV data."""

    ir, envelope = load_strategy_file_with_envelope(path)
    execution_profile = _effective_profile(profile, envelope.profile)
    result = execute_strategy(
        ir,
        {
            "market": _load_market_csv(market),
            "state": {
                "current_symbol": 1.0,
                "current_notional": 0.0,
                "elapsed": 0.0,
                "cooldown_elapsed": 0.0,
            },
            "sizing": 1.0,
        },
        trace_path=trace_path,
        profile=execution_profile,
    )
    if not result.ok:
        typer.echo(result.error or "execution failed", err=True)
        if result.validation_failures:
            for failure in result.validation_failures:
                typer.echo(json.dumps(failure.model_dump(exclude_none=True), ensure_ascii=False), err=True)
            raise typer.Exit(1)
        raise typer.Exit(4)
    _echo_json({"outputs": result.outputs, "trace": str(trace_path)})

@app.command("promote")
def promote_cmd(
    path: Path,
    to_profile: Annotated[ProfileLiteral, typer.Option("--to")],
    approved_by: Annotated[str | None, typer.Option("--approved-by")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Promote a strategy deployment envelope to a target profile."""

    ir, envelope = load_strategy_file_with_envelope(path)
    result = promote_strategy(ir, envelope, to_profile, approved_by=approved_by)
    if not result.ok:
        _echo_json(
            {
                "ok": False,
                "target_profile": to_profile,
                "strategy_instance_hash": envelope.strategy_instance_hash,
                "new_envelope": None,
                "validation_failures": [
                    failure.model_dump(mode="json", exclude_none=True)
                    for failure in result.new_validation_failures
                ],
            }
        )
        raise typer.Exit(1)

    assert result.new_envelope is not None
    if output is not None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError("Strategy YAML must contain a mapping")
        raw["_envelope"] = result.new_envelope.model_dump(mode="json", exclude_none=True)
        output.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    payload = {
        "ok": True,
        "target_profile": to_profile,
        "strategy_instance_hash": result.new_envelope.strategy_instance_hash,
        "new_envelope": result.new_envelope.model_dump(mode="json", exclude_none=True),
        "validation_failures": [],
        "diff": result.diff_from_previous,
    }
    if output is not None:
        payload["output"] = str(output)
    _echo_json(payload)


@app.command("explain-trace")
def explain_trace_cmd(
    trace_path: Path,
    level: Annotated[str, typer.Option("--level")] = "human",
) -> None:
    """Explain a trace JSON file."""

    if level not in {"human", "agent", "raw"}:
        typer.echo(f"unsupported level: {level}", err=True)
        raise typer.Exit(2)
    trace = Trace.model_validate_json(trace_path.read_text(encoding="utf-8"))
    typer.echo(explain_trace_text(trace, level=level))  # type: ignore[arg-type]


if __name__ == "__main__":
    app()
